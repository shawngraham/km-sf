#!/usr/bin/env python3
"""
Sketchfab Web Scraper using Beautiful Soup

This script complements the API-based scraper by directly scraping
Sketchfab search result pages to collect metadata that might not be
available through the API.

Uses Beautiful Soup to:
- Navigate through paginated search results
- Extract model metadata from each search result page
- Collect all descriptive text from model cards
- Save data to JSON format

Author: SG w/ Claude Assistance
Date: 2025-11-14
"""

import time
import json
import logging
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse
from datetime import datetime

import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SketchfabWebScraper:
    """
    Web scraper for Sketchfab search results using Beautiful Soup.

    This scraper collects metadata directly from the HTML of search result pages,
    complementing the API-based approach with any additional information
    visible on the web interface.
    """

    BASE_URL = "https://sketchfab.com"

    def __init__(self, rate_limit_delay: float = 2.0, user_agent: Optional[str] = None):
        """
        Initialize the web scraper.

        Args:
            rate_limit_delay: Delay in seconds between requests (default: 2.0)
                            Be respectful to the server!
            user_agent: Custom user agent string (optional)
        """
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0
        self.session = requests.Session()

        # Set up headers
        if user_agent:
            self.session.headers.update({'User-Agent': user_agent})
        else:
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
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

    def _make_request(self, url: str) -> Optional[BeautifulSoup]:
        """
        Make a rate-limited request and return BeautifulSoup object.

        Args:
            url: URL to fetch

        Returns:
            BeautifulSoup object or None if request fails
        """
        self._rate_limit()

        try:
            logger.info(f"Fetching: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            return BeautifulSoup(response.content, 'html.parser')

        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                logger.error("Rate limit exceeded (429). Waiting 60 seconds...")
                time.sleep(60)
                # Retry once
                try:
                    response = self.session.get(url, timeout=30)
                    response.raise_for_status()
                    return BeautifulSoup(response.content, 'html.parser')
                except Exception as retry_error:
                    logger.error(f"Retry failed: {retry_error}")
                    return None
            else:
                logger.error(f"HTTP Error {response.status_code}: {e}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return None

    def _extract_model_data(self, item_div) -> Dict:
        """
        Extract all available data from a model card div.

        Args:
            item_div: BeautifulSoup div element with class 'c-grid__item item'

        Returns:
            Dictionary with extracted model data
        """
        model_data = {
            'scraped_at': datetime.now().isoformat(),
            'title': '',
            'author': '',
            'author_url': '',
            'model_url': '',
            'thumbnail_url': '',
            'description': '',
            'stats': {},
            'metadata': {},
            'all_text': []  # Collect ALL text from the card
        }

        try:
            # Extract title and link
            title_link = item_div.find('a', class_='item-name')
            if title_link:
                model_data['title'] = title_link.get_text(strip=True)
                model_data['model_url'] = urljoin(self.BASE_URL, title_link.get('href', ''))
                model_data['all_text'].append(model_data['title'])

            # Extract author information
            author_link = item_div.find('a', class_='item-author')
            if not author_link:
                # Try alternative selectors
                author_link = item_div.find('a', {'data-test': 'model-author'})

            if author_link:
                model_data['author'] = author_link.get_text(strip=True)
                model_data['author_url'] = urljoin(self.BASE_URL, author_link.get('href', ''))
                model_data['all_text'].append(model_data['author'])

            # Extract thumbnail
            img = item_div.find('img')
            if img:
                model_data['thumbnail_url'] = img.get('src', '') or img.get('data-src', '')

            # Extract description/snippet if present
            description = item_div.find('p', class_='item-description')
            if not description:
                description = item_div.find('div', class_='item-description')

            if description:
                model_data['description'] = description.get_text(strip=True)
                model_data['all_text'].append(model_data['description'])

            # Extract statistics (views, likes, etc.)
            stats_container = item_div.find('div', class_='item-stats')
            if not stats_container:
                stats_container = item_div.find('ul', class_='item-stats')

            if stats_container:
                # Look for various stat elements
                stat_elements = stats_container.find_all(['span', 'li', 'div'])
                for stat in stat_elements:
                    stat_text = stat.get_text(strip=True)
                    if stat_text:
                        model_data['all_text'].append(stat_text)

                        # Try to parse specific stats
                        if 'view' in stat_text.lower():
                            model_data['stats']['views'] = stat_text
                        elif 'like' in stat_text.lower():
                            model_data['stats']['likes'] = stat_text
                        elif 'comment' in stat_text.lower():
                            model_data['stats']['comments'] = stat_text

            # Extract any badges or tags
            badges = item_div.find_all(['span', 'div'], class_=lambda x: x and ('badge' in x or 'tag' in x))
            for badge in badges:
                badge_text = badge.get_text(strip=True)
                if badge_text:
                    model_data['all_text'].append(badge_text)
                    if 'badges' not in model_data['metadata']:
                        model_data['metadata']['badges'] = []
                    model_data['metadata']['badges'].append(badge_text)

            # Extract license information if visible
            license_elem = item_div.find(lambda tag: tag.name in ['span', 'div', 'a'] and
                                        ('license' in tag.get('class', []) if tag.get('class') else False))
            if license_elem:
                license_text = license_elem.get_text(strip=True)
                model_data['metadata']['license'] = license_text
                model_data['all_text'].append(license_text)

            # Extract data attributes (often contain useful IDs)
            for attr in ['data-model-id', 'data-uid', 'data-model-uid']:
                if item_div.has_attr(attr):
                    model_data['metadata'][attr] = item_div[attr]

            # Collect ALL remaining text from the item
            all_strings = item_div.stripped_strings
            for string in all_strings:
                if string not in model_data['all_text']:
                    model_data['all_text'].append(string)

        except Exception as e:
            logger.error(f"Error extracting model data: {e}")

        return model_data

    def _get_next_page_url(self, soup: BeautifulSoup, current_url: str) -> Optional[str]:
        """
        Find the URL for the next page of results.

        Args:
            soup: BeautifulSoup object of current page
            current_url: URL of current page

        Returns:
            URL of next page or None if no next page
        """
        # Look for next page link
        next_link = soup.find('a', class_='next')
        if not next_link:
            next_link = soup.find('a', {'rel': 'next'})
        if not next_link:
            next_link = soup.find('a', string=lambda text: text and 'next' in text.lower())

        if next_link and next_link.get('href'):
            return urljoin(self.BASE_URL, next_link['href'])

        # Alternative: Look for pagination and construct URL
        # Parse current URL to increment cursor or page parameter
        parsed = urlparse(current_url)
        query_params = parse_qs(parsed.query)

        # Check if there's a cursor parameter (Sketchfab uses cursor-based pagination)
        if 'cursor' in query_params:
            # We need to find the next cursor from the page
            # Look for pagination data in script tags or data attributes
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and 'cursor' in script.string:
                    # This would require parsing JSON from script tags
                    # For now, we'll rely on the next link
                    pass

        return None

    def scrape_search(
        self,
        query: str,
        search_type: str = 'models',
        max_pages: Optional[int] = None,
        max_models: Optional[int] = None
    ) -> List[Dict]:
        """
        Scrape Sketchfab search results.

        Args:
            query: Search query string
            search_type: Type of search (default: 'models')
            max_pages: Maximum number of pages to scrape (None = all)
            max_models: Maximum number of models to collect (None = all)

        Returns:
            List of dictionaries containing model data
        """
        # Construct initial search URL
        search_url = f"{self.BASE_URL}/search"
        params = {
            'q': query,
            'type': search_type
        }

        # Build URL with parameters
        parsed = urlparse(search_url)
        query_string = urlencode(params)
        url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            query_string,
            parsed.fragment
        ))

        all_models = []
        page_count = 0

        logger.info(f"Starting search scrape for query: '{query}'")
        logger.info(f"Initial URL: {url}")

        while url:
            page_count += 1

            if max_pages and page_count > max_pages:
                logger.info(f"Reached max_pages limit: {max_pages}")
                break

            logger.info(f"Scraping page {page_count}...")

            # Fetch page
            soup = self._make_request(url)
            if not soup:
                logger.error("Failed to fetch page, stopping")
                break

            # Find all model items
            model_items = soup.find_all('div', class_='c-grid__item item')

            # Also try alternative class names in case they change
            if not model_items:
                model_items = soup.find_all('div', class_=lambda x: x and 'grid__item' in x)

            if not model_items:
                logger.warning(f"No model items found on page {page_count}")
                logger.info("Page structure might have changed. Saving HTML for inspection...")

                # Save HTML for debugging
                debug_filename = f"debug_page_{page_count}_{int(time.time())}.html"
                with open(debug_filename, 'w', encoding='utf-8') as f:
                    f.write(soup.prettify())
                logger.info(f"HTML saved to {debug_filename}")

                # Try to find any divs that might be model cards
                logger.info("Attempting to find model cards with alternative selectors...")

                # Look for article tags (common for cards)
                model_items = soup.find_all('article')
                if not model_items:
                    # Look for divs with data-model attributes
                    model_items = soup.find_all('div', attrs={'data-model-id': True})
                if not model_items:
                    # Look for links to /models/
                    model_links = soup.find_all('a', href=lambda x: x and '/models/' in x)
                    # Get parent containers
                    model_items = [link.find_parent(['div', 'article', 'li']) for link in model_links]
                    model_items = [item for item in model_items if item]

                if model_items:
                    logger.info(f"Found {len(model_items)} items with alternative selectors")
                else:
                    logger.error("Could not find any model items. Breaking.")
                    break

            logger.info(f"Found {len(model_items)} models on page {page_count}")

            # Extract data from each model
            for item in model_items:
                model_data = self._extract_model_data(item)
                all_models.append(model_data)

                # Check if we've reached max_models
                if max_models and len(all_models) >= max_models:
                    logger.info(f"Reached max_models limit: {max_models}")
                    return all_models

            logger.info(f"Total models collected: {len(all_models)}")

            # Find next page
            url = self._get_next_page_url(soup, url)

            if not url:
                logger.info("No next page found, scraping complete")
                break

        logger.info(f"Scraping complete. Collected {len(all_models)} models from {page_count} pages")
        return all_models

    def save_to_json(self, data: List[Dict], filename: str):
        """
        Save scraped data to JSON file.

        Args:
            data: List of model dictionaries
            filename: Output filename
        """
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Data saved to {filename}")
        logger.info(f"Total models: {len(data)}")

    def scrape_and_save(
        self,
        query: str,
        output_file: str,
        max_pages: Optional[int] = None,
        max_models: Optional[int] = None
    ):
        """
        Convenience method to scrape and save in one call.

        Args:
            query: Search query
            output_file: Output JSON filename
            max_pages: Maximum pages to scrape
            max_models: Maximum models to collect
        """
        models = self.scrape_search(query, max_pages=max_pages, max_models=max_models)
        self.save_to_json(models, output_file)
        return models


def main():
    """Example usage"""
    print("Sketchfab Web Scraper")
    print("=" * 70)

    # Initialize scraper
    scraper = SketchfabWebScraper(rate_limit_delay=2.0)

    # Example: Scrape Roman models
    query = "roman"
    output_file = f"sketchfab_web_scrape_{query}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    print(f"\nScraping Sketchfab for: '{query}'")
    print(f"Output file: {output_file}")
    print(f"Rate limit: {scraper.rate_limit_delay} seconds between requests")
    print("\nStarting in 3 seconds...")
    time.sleep(3)

    # Scrape (limit to 3 pages for testing)
    models = scraper.scrape_search(
        query=query,
        max_pages=3,  # Remove or increase for production use
        max_models=None
    )

    # Save results
    scraper.save_to_json(models, output_file)

    # Print summary
    print("\n" + "=" * 70)
    print("SCRAPING COMPLETE")
    print("=" * 70)
    print(f"\nTotal models collected: {len(models)}")

    if models:
        print("\nSample model data:")
        print(f"Title: {models[0].get('title', 'N/A')}")
        print(f"Author: {models[0].get('author', 'N/A')}")
        print(f"URL: {models[0].get('model_url', 'N/A')}")
        print(f"All text fields: {len(models[0].get('all_text', []))}")

    print(f"\nData saved to: {output_file}")


if __name__ == "__main__":
    main()
