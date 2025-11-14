#!/usr/bin/env python3
"""
Enhanced Sketchfab API Scraper with Better Rate Limit Handling

This enhanced version addresses opaque rate limiting issues with:
- Exponential backoff on rate limit errors
- Response header inspection for rate limit info
- Progress checkpointing (resume interrupted scrapes)
- More transparent logging
- Conservative defaults

Author: SG w/ Claude Assistance
Date: 2025-11-14
"""

import time
import requests
import json
import os
from typing import Dict, List, Optional, Union
from datetime import datetime
import logging

# Configure logging with more detail
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('sketchfab_scraper.log')
    ]
)
logger = logging.getLogger(__name__)


class RateLimitError(Exception):
    """Custom exception for rate limit issues"""
    pass


class EnhancedSketchfabScraper:
    """
    Enhanced API client with better rate limit handling.

    Improvements over base scraper:
    - Exponential backoff (not just one retry)
    - Response header inspection
    - Progress checkpointing
    - More transparent logging
    - Adaptive rate limiting
    """

    BASE_URL = "https://api.sketchfab.com/v3"

    def __init__(
        self,
        api_token: Optional[str] = None,
        rate_limit_delay: float = 2.0,
        max_retries: int = 5,
        checkpoint_file: Optional[str] = None
    ):
        """
        Initialize the enhanced scraper.

        Args:
            api_token: Optional API token
            rate_limit_delay: Initial delay between requests (default: 2.0s)
            max_retries: Maximum retry attempts on rate limit (default: 5)
            checkpoint_file: File to save progress for resuming
        """
        self.api_token = api_token
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        self.checkpoint_file = checkpoint_file
        self.last_request_time = 0
        self.session = requests.Session()

        # Track rate limit info
        self.rate_limit_info = {
            'limit': None,
            'remaining': None,
            'reset': None,
            'retry_after': None
        }

        # Request statistics
        self.stats = {
            'total_requests': 0,
            'rate_limited': 0,
            'errors': 0,
            'successful': 0
        }

        # Set up headers
        self.session.headers.update({
            'User-Agent': 'Sketchfab-Research-Tool/3.0 (Cultural Heritage Analysis)'
        })

        if self.api_token:
            self.session.headers.update({
                'Authorization': f'Token {self.api_token}'
            })
            logger.info("Initialized with API token (authenticated)")
        else:
            logger.info("Initialized without API token (unauthenticated)")

        logger.info(f"Rate limit delay: {self.rate_limit_delay}s")
        logger.info(f"Max retries on rate limit: {self.max_retries}")

    def _update_rate_limit_info(self, response: requests.Response):
        """Extract rate limit information from response headers."""
        headers = response.headers

        # Common rate limit header names
        limit_headers = {
            'limit': ['X-RateLimit-Limit', 'RateLimit-Limit'],
            'remaining': ['X-RateLimit-Remaining', 'RateLimit-Remaining'],
            'reset': ['X-RateLimit-Reset', 'RateLimit-Reset'],
            'retry_after': ['Retry-After', 'X-RateLimit-Retry-After']
        }

        for key, possible_headers in limit_headers.items():
            for header in possible_headers:
                if header in headers:
                    self.rate_limit_info[key] = headers[header]
                    break

        # Log if we found rate limit info
        if any(self.rate_limit_info.values()):
            logger.debug(f"Rate limit info: {self.rate_limit_info}")

    def _adaptive_sleep(self, retry_count: int = 0):
        """
        Adaptive sleep with exponential backoff.

        Args:
            retry_count: Current retry attempt (0 = first attempt)
        """
        if retry_count == 0:
            # Normal rate limiting
            sleep_time = self.rate_limit_delay
        else:
            # Exponential backoff: 2^retry * base_delay
            # With jitter to avoid thundering herd
            import random
            backoff = (2 ** retry_count) * self.rate_limit_delay
            jitter = random.uniform(0, 0.1 * backoff)
            sleep_time = backoff + jitter
            sleep_time = min(sleep_time, 300)  # Cap at 5 minutes

        logger.info(f"Waiting {sleep_time:.2f}s before next request (retry: {retry_count})")
        time.sleep(sleep_time)

    def _rate_limit(self):
        """Implement polite rate limiting between requests."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_request
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        retry_count: int = 0
    ) -> Dict:
        """
        Make a rate-limited request with exponential backoff.

        Args:
            endpoint: API endpoint
            params: Query parameters
            retry_count: Current retry attempt

        Returns:
            JSON response as dictionary

        Raises:
            RateLimitError: If rate limited after all retries
            requests.exceptions.HTTPError: For other HTTP errors
        """
        self._rate_limit()

        url = f"{self.BASE_URL}{endpoint}"
        self.stats['total_requests'] += 1

        try:
            logger.debug(f"Request {self.stats['total_requests']}: {endpoint}")
            response = self.session.get(url, params=params, timeout=30)

            # Update rate limit info from headers
            self._update_rate_limit_info(response)

            # Log remaining requests if available
            if self.rate_limit_info['remaining']:
                logger.debug(f"Rate limit remaining: {self.rate_limit_info['remaining']}")

            response.raise_for_status()
            self.stats['successful'] += 1
            return response.json()

        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                # Rate limited
                self.stats['rate_limited'] += 1
                logger.warning(f"Rate limit hit (429) - Attempt {retry_count + 1}/{self.max_retries}")

                # Check for Retry-After header
                retry_after = response.headers.get('Retry-After')
                if retry_after:
                    wait_time = int(retry_after)
                    logger.info(f"Server says Retry-After: {wait_time}s")
                    time.sleep(wait_time)

                if retry_count < self.max_retries:
                    logger.info(f"Retrying with exponential backoff...")
                    self._adaptive_sleep(retry_count + 1)
                    return self._make_request(endpoint, params, retry_count + 1)
                else:
                    logger.error(f"Max retries ({self.max_retries}) exceeded")
                    raise RateLimitError(
                        f"Rate limited after {self.max_retries} retries. "
                        f"Consider: 1) Increasing rate_limit_delay, "
                        f"2) Using API token if not already, "
                        f"3) Waiting before resuming"
                    )

            elif response.status_code == 403:
                logger.error("403 Forbidden - Check API token or permissions")
                self.stats['errors'] += 1
                raise

            elif response.status_code >= 500:
                # Server error - retry with backoff
                logger.warning(f"Server error {response.status_code}")
                if retry_count < 3:  # Fewer retries for server errors
                    self._adaptive_sleep(retry_count + 1)
                    return self._make_request(endpoint, params, retry_count + 1)
                raise

            else:
                logger.error(f"HTTP Error {response.status_code}: {e}")
                self.stats['errors'] += 1
                raise

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            self.stats['errors'] += 1
            raise

    def save_checkpoint(self, data: List[Dict], checkpoint_name: str = "checkpoint"):
        """
        Save progress checkpoint.

        Args:
            data: Current data to save
            checkpoint_name: Name for checkpoint file
        """
        if not self.checkpoint_file:
            checkpoint_path = f"{checkpoint_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        else:
            checkpoint_path = self.checkpoint_file

        checkpoint = {
            'timestamp': datetime.now().isoformat(),
            'stats': self.stats,
            'data': data,
            'count': len(data)
        }

        with open(checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(checkpoint, f, indent=2, ensure_ascii=False)

        logger.info(f"✓ Checkpoint saved: {checkpoint_path} ({len(data)} items)")
        return checkpoint_path

    def load_checkpoint(self, checkpoint_path: str) -> List[Dict]:
        """
        Load from checkpoint file.

        Args:
            checkpoint_path: Path to checkpoint file

        Returns:
            List of previously saved data
        """
        if not os.path.exists(checkpoint_path):
            logger.warning(f"Checkpoint file not found: {checkpoint_path}")
            return []

        with open(checkpoint_path, 'r', encoding='utf-8') as f:
            checkpoint = json.load(f)

        logger.info(f"✓ Loaded checkpoint: {len(checkpoint.get('data', []))} items")
        logger.info(f"  From: {checkpoint.get('timestamp')}")

        return checkpoint.get('data', [])

    def search_models_with_checkpoints(
        self,
        query: str = "",
        categories: Optional[Union[str, List[str]]] = None,
        max_results: Optional[int] = None,
        checkpoint_every: int = 100,
        **kwargs
    ) -> List[Dict]:
        """
        Search models with automatic checkpointing.

        Args:
            query: Search query
            categories: Categories to filter
            max_results: Max results to fetch
            checkpoint_every: Save checkpoint every N results
            **kwargs: Additional search parameters

        Returns:
            List of model dictionaries
        """
        from sketchfab_scraper import SketchfabScraper

        # Create a temporary base scraper to use its search logic
        base = SketchfabScraper(api_token=self.api_token, rate_limit_delay=self.rate_limit_delay)

        # Override its _make_request with ours
        base._make_request = self._make_request

        logger.info(f"Starting search with checkpointing (every {checkpoint_every} results)")

        try:
            results = base.search_models(
                query=query,
                categories=categories,
                max_results=max_results,
                **kwargs
            )

            # Final checkpoint
            if results:
                self.save_checkpoint(results, f"final_search_{query.replace(' ', '_')}")

            return results

        except (RateLimitError, KeyboardInterrupt) as e:
            logger.warning(f"Search interrupted: {e}")
            logger.info("Partial results saved in checkpoint")
            raise

    def print_stats(self):
        """Print request statistics."""
        print("\n" + "=" * 70)
        print("API Request Statistics")
        print("=" * 70)
        print(f"Total requests:    {self.stats['total_requests']}")
        print(f"Successful:        {self.stats['successful']}")
        print(f"Rate limited:      {self.stats['rate_limited']}")
        print(f"Errors:            {self.stats['errors']}")

        if self.stats['total_requests'] > 0:
            success_rate = (self.stats['successful'] / self.stats['total_requests']) * 100
            print(f"Success rate:      {success_rate:.1f}%")

        if self.rate_limit_info['remaining']:
            print(f"\nRate limit remaining: {self.rate_limit_info['remaining']}")

        print("=" * 70)


def main():
    """Example usage"""
    print("Enhanced Sketchfab Scraper with Better Rate Limit Handling")
    print("=" * 70)

    # Initialize with conservative settings
    scraper = EnhancedSketchfabScraper(
        rate_limit_delay=3.0,  # More conservative
        max_retries=5,
        checkpoint_file="search_checkpoint.json"
    )

    try:
        # Search with checkpointing
        results = scraper.search_models_with_checkpoints(
            query="roman",
            categories="cultural-heritage-history",
            max_results=50,
            checkpoint_every=25
        )

        print(f"\n✓ Collected {len(results)} models")

        # Print statistics
        scraper.print_stats()

    except RateLimitError as e:
        print(f"\n✗ Rate limit error: {e}")
        print("Resume by loading the checkpoint and continuing")
        scraper.print_stats()

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        print("Progress saved in checkpoint file")
        scraper.print_stats()


if __name__ == "__main__":
    main()
