"""
Sketchfab Data API Scraper for Cultural Heritage Models

This module provides a polite API client for retrieving cultural heritage model data
from Sketchfab's Data API v3. It includes rate limiting, pagination handling, and
pandas DataFrame conversion for data analysis.

Author: Research Tool
Date: 2025-10-31
API Documentation: https://docs.sketchfab.com/data-api/v3/
"""

import time
import requests
import pandas as pd
from typing import Dict, List, Optional, Union
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SketchfabScraper:
    """
    A polite API client for Sketchfab Data API v3.

    This client implements rate limiting, pagination, and data conversion
    to facilitate cultural heritage research.
    """

    BASE_URL = "https://api.sketchfab.com/v3"

    def __init__(self, api_token: Optional[str] = None, rate_limit_delay: float = 1.0):
        """
        Initialize the Sketchfab API scraper.

        Args:
            api_token: Optional API token for authenticated requests.
                      Get yours at: https://sketchfab.com/settings/password
            rate_limit_delay: Delay in seconds between requests (default: 1.0)
                            Increase this if you encounter rate limiting (429 errors)
        """
        self.api_token = api_token
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0
        self.session = requests.Session()

        # Set up headers
        self.session.headers.update({
            'User-Agent': 'Sketchfab-Research-Tool/1.0 (Cultural Heritage Analysis)'
        })

        if self.api_token:
            self.session.headers.update({
                'Authorization': f'Token {self.api_token}'
            })

    def _rate_limit(self):
        """Implement polite rate limiting between requests."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_request
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        Make a rate-limited request to the Sketchfab API.

        Args:
            endpoint: API endpoint (e.g., '/search')
            params: Query parameters

        Returns:
            JSON response as dictionary

        Raises:
            requests.exceptions.HTTPError: If the request fails
        """
        self._rate_limit()

        url = f"{self.BASE_URL}{endpoint}"

        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                logger.error("Rate limit exceeded (429). Consider increasing rate_limit_delay.")
                logger.info(f"Waiting 60 seconds before retrying...")
                time.sleep(60)
                # Retry once
                response = self.session.get(url, params=params)
                response.raise_for_status()
                return response.json()
            else:
                logger.error(f"HTTP Error {response.status_code}: {e}")
                raise

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise

    def search_models(
        self,
        query: str = "",
        categories: Optional[Union[str, List[str]]] = None,
        tags: Optional[Union[str, List[str]]] = None,
        licenses: Optional[List[str]] = None,
        downloadable: Optional[bool] = None,
        animated: Optional[bool] = None,
        max_face_count: Optional[int] = None,
        min_face_count: Optional[int] = None,
        sort_by: str = '-relevance',
        max_results: Optional[int] = None,
        **kwargs
    ) -> List[Dict]:
        """
        Search for models on Sketchfab.

        Args:
            query: Search query string (e.g., "roman temple", "ancient pottery")
            categories: Category slug(s) - e.g., 'cultural-heritage-history'
            tags: Tag(s) to filter by
            licenses: List of license codes to filter by
                     (e.g., ['by', 'by-sa', 'by-nd', 'by-nc', 'by-nc-sa', 'by-nc-nd', 'cc0'])
            downloadable: Filter by downloadable models only
            animated: Filter by animated models
            max_face_count: Maximum face/polygon count
            min_face_count: Minimum face/polygon count
            sort_by: Sort order. Options:
                    '-relevance' (default), '-likeCount', '-viewCount',
                    '-publishedAt', 'publishedAt', '-createdAt', 'createdAt'
            max_results: Maximum number of results to retrieve (None = all available)
            **kwargs: Additional search parameters

        Returns:
            List of model dictionaries
        """
        params = {
            'type': 'models',
            'sort_by': sort_by
        }

        if query:
            params['q'] = query

        if categories:
            if isinstance(categories, list):
                params['categories'] = ','.join(categories)
            else:
                params['categories'] = categories

        if tags:
            if isinstance(tags, list):
                params['tags'] = ','.join(tags)
            else:
                params['tags'] = tags

        if licenses:
            params['licenses'] = ','.join(licenses)

        if downloadable is not None:
            params['downloadable'] = str(downloadable).lower()

        if animated is not None:
            params['animated'] = str(animated).lower()

        if max_face_count:
            params['max_face_count'] = max_face_count

        if min_face_count:
            params['min_face_count'] = min_face_count

        # Add any additional parameters
        params.update(kwargs)

        return self._paginate('/search', params, max_results)

    def _paginate(self, endpoint: str, params: Dict, max_results: Optional[int] = None) -> List[Dict]:
        """
        Handle pagination for API requests.

        Args:
            endpoint: API endpoint
            params: Query parameters
            max_results: Maximum number of results to retrieve

        Returns:
            List of all results across pages
        """
        all_results = []
        next_url = None
        total_fetched = 0

        logger.info(f"Starting pagination for endpoint: {endpoint}")

        while True:
            # Make request
            if next_url:
                # Extract path and params from next_url
                self._rate_limit()
                response = self.session.get(next_url)
                response.raise_for_status()
                data = response.json()
            else:
                data = self._make_request(endpoint, params)

            # Extract results
            results = data.get('results', [])
            all_results.extend(results)
            total_fetched += len(results)

            logger.info(f"Fetched {len(results)} results (Total: {total_fetched})")

            # Check if we've reached max_results
            if max_results and total_fetched >= max_results:
                all_results = all_results[:max_results]
                logger.info(f"Reached max_results limit: {max_results}")
                break

            # Check for next page
            next_url = data.get('next')
            if not next_url:
                logger.info("No more pages available")
                break

        logger.info(f"Pagination complete. Total results: {len(all_results)}")
        return all_results

    def get_model_details(self, model_uid: str) -> Dict:
        """
        Get detailed information about a specific model.

        Args:
            model_uid: The unique identifier of the model

        Returns:
            Model details dictionary
        """
        logger.info(f"Fetching details for model: {model_uid}")
        return self._make_request(f'/models/{model_uid}')

    def to_dataframe(self, models: List[Dict], flatten: bool = True) -> pd.DataFrame:
        """
        Convert model data to a pandas DataFrame.

        Args:
            models: List of model dictionaries from API
            flatten: If True, flatten nested structures for easier analysis

        Returns:
            pandas DataFrame with model data
        """
        if not models:
            logger.warning("No models to convert to DataFrame")
            return pd.DataFrame()

        df = pd.DataFrame(models)

        if flatten:
            df = self._flatten_dataframe(df)

        return df

    def _flatten_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Flatten nested structures in the DataFrame for easier analysis.

        Args:
            df: Input DataFrame

        Returns:
            Flattened DataFrame
        """
        flattened_data = []

        for _, row in df.iterrows():
            flat_row = {}

            # Basic fields
            flat_row['uid'] = row.get('uid', '')
            flat_row['name'] = row.get('name', '')
            flat_row['description'] = row.get('description', '')
            flat_row['viewCount'] = row.get('viewCount', 0)
            flat_row['likeCount'] = row.get('likeCount', 0)
            flat_row['commentCount'] = row.get('commentCount', 0)
            flat_row['animationCount'] = row.get('animationCount', 0)
            flat_row['publishedAt'] = row.get('publishedAt', '')
            flat_row['createdAt'] = row.get('createdAt', '')
            flat_row['viewerUrl'] = row.get('viewerUrl', '')
            flat_row['isDownloadable'] = row.get('isDownloadable', False)

            # User information
            if 'user' in row and isinstance(row['user'], dict):
                flat_row['user_username'] = row['user'].get('username', '')
                flat_row['user_displayName'] = row['user'].get('displayName', '')
                flat_row['user_profileUrl'] = row['user'].get('profileUrl', '')
                flat_row['user_account'] = row['user'].get('account', '')

            # License information
            if 'license' in row and isinstance(row['license'], dict):
                flat_row['license_label'] = row['license'].get('label', '')
                flat_row['license_requirements'] = row['license'].get('requirements', '')
                flat_row['license_slug'] = row['license'].get('slug', '')

            # Categories
            if 'categories' in row and isinstance(row['categories'], list):
                flat_row['categories'] = ', '.join([cat.get('name', '') for cat in row['categories']])
                flat_row['category_slugs'] = ', '.join([cat.get('slug', '') for cat in row['categories']])

            # Tags
            if 'tags' in row and isinstance(row['tags'], list):
                flat_row['tags'] = ', '.join([tag.get('name', '') for tag in row['tags']])

            # Face/polygon count
            flat_row['faceCount'] = row.get('faceCount', 0)
            flat_row['vertexCount'] = row.get('vertexCount', 0)

            # Thumbnails
            if 'thumbnails' in row and isinstance(row['thumbnails'], dict):
                images = row['thumbnails'].get('images', [])
                if images:
                    # Get the largest thumbnail
                    flat_row['thumbnail_url'] = images[-1].get('url', '')

            flattened_data.append(flat_row)

        return pd.DataFrame(flattened_data)

    def search_cultural_heritage(
        self,
        query: str = "",
        max_results: Optional[int] = None,
        **kwargs
    ) -> pd.DataFrame:
        """
        Convenience method to search cultural heritage models and return as DataFrame.

        Args:
            query: Additional search query (combined with cultural heritage category)
            max_results: Maximum number of results
            **kwargs: Additional search parameters

        Returns:
            pandas DataFrame with cultural heritage model data
        """
        logger.info(f"Searching cultural heritage models with query: '{query}'")

        models = self.search_models(
            query=query,
            categories='cultural-heritage-history',
            max_results=max_results,
            **kwargs
        )

        return self.to_dataframe(models)

    def export_to_csv(self, df: pd.DataFrame, filename: str):
        """
        Export DataFrame to CSV file.

        Args:
            df: pandas DataFrame
            filename: Output CSV filename
        """
        df.to_csv(filename, index=False, encoding='utf-8')
        logger.info(f"Data exported to {filename}")

    def get_user_models(self, username: str, max_results: Optional[int] = None) -> List[Dict]:
        """
        Get all models by a specific user.

        Args:
            username: Sketchfab username
            max_results: Maximum number of results

        Returns:
            List of model dictionaries
        """
        logger.info(f"Fetching models for user: {username}")

        params = {
            'type': 'models',
            'user': username
        }

        return self._paginate('/search', params, max_results)


# Convenience functions for quick usage

def quick_search(
    query: str,
    cultural_heritage: bool = True,
    max_results: int = 100,
    api_token: Optional[str] = None
) -> pd.DataFrame:
    """
    Quick search function for immediate results.

    Args:
        query: Search query
        cultural_heritage: If True, filter by cultural heritage category
        max_results: Maximum results to retrieve
        api_token: Optional API token

    Returns:
        pandas DataFrame with results
    """
    scraper = SketchfabScraper(api_token=api_token)

    if cultural_heritage:
        return scraper.search_cultural_heritage(query=query, max_results=max_results)
    else:
        models = scraper.search_models(query=query, max_results=max_results)
        return scraper.to_dataframe(models)


if __name__ == "__main__":
    # Example usage
    print("Sketchfab Cultural Heritage Scraper")
    print("=" * 50)

    # Initialize scraper (no token needed for public searches)
    scraper = SketchfabScraper(rate_limit_delay=1.5)

    # Search for cultural heritage models
    print("\nSearching for Roman archaeology models...")
    df = scraper.search_cultural_heritage(
        query="roman",
        max_results=10
    )

    print(f"\nFound {len(df)} models")
    print("\nSample data:")
    print(df[['name', 'user_username', 'viewCount', 'likeCount', 'tags']].head())

    # Export to CSV
    scraper.export_to_csv(df, 'cultural_heritage_models.csv')
