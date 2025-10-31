"""
Sketchfab Data API Scraper for Cultural Heritage Models - COMPLETE VERSION

This module provides a comprehensive API client for retrieving ALL available data
from Sketchfab's Data API v3, including comments and every documented field.

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
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SketchfabScraper:
    """
    A comprehensive API client for Sketchfab Data API v3.

    Captures ALL available fields from the API including:
    - Full model details
    - Comments
    - Organization data
    - Archive information with all formats
    - Processing status
    - All metadata fields
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
            'User-Agent': 'Sketchfab-Research-Tool/2.0 (Cultural Heritage Analysis)'
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
        archives_flavours: bool = False,
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
            archives_flavours: If true, returns all archive flavours sorted by texture resolution
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

        if archives_flavours:
            params['archives_flavours'] = 'true'

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
        This returns ALL available fields for a model.

        Args:
            model_uid: The unique identifier of the model

        Returns:
            Model details dictionary with all available fields
        """
        logger.info(f"Fetching details for model: {model_uid}")
        return self._make_request(f'/models/{model_uid}')

    def get_model_comments(self, model_uid: str, max_results: Optional[int] = None) -> List[Dict]:
        """
        Get comments for a specific model.

        Args:
            model_uid: The unique identifier of the model
            max_results: Maximum number of comments to retrieve (None = all)

        Returns:
            List of comment dictionaries
        """
        logger.info(f"Fetching comments for model: {model_uid}")
        params = {'model': model_uid}
        return self._paginate('/comments', params, max_results)

    def get_complete_model_data(self, model_uid: str, include_comments: bool = True) -> Dict:
        """
        Get complete model data including full details and optionally comments.

        Args:
            model_uid: The unique identifier of the model
            include_comments: Whether to include comments (default: True)

        Returns:
            Dictionary with 'model' and optionally 'comments' keys
        """
        logger.info(f"Fetching complete data for model: {model_uid}")
        
        result = {
            'model': self.get_model_details(model_uid)
        }
        
        if include_comments:
            result['comments'] = self.get_model_comments(model_uid)
            result['comment_count'] = len(result['comments'])
        
        return result

    def enrich_search_results(
        self,
        search_results: List[Dict],
        include_full_details: bool = True,
        include_comments: bool = True,
        max_models: Optional[int] = None
    ) -> List[Dict]:
        """
        Enrich basic search results with full model details and comments.

        WARNING: This can be slow for large result sets as it makes additional
        API calls for each model.

        Args:
            search_results: List of basic model data from search
            include_full_details: Fetch complete model details
            include_comments: Include comments for each model
            max_models: Maximum number of models to enrich (None = all)

        Returns:
            List of enriched model dictionaries
        """
        enriched_results = []
        models_to_process = search_results[:max_models] if max_models else search_results
        
        logger.info(f"Enriching {len(models_to_process)} models with additional data")
        
        for i, model in enumerate(models_to_process, 1):
            uid = model.get('uid')
            if not uid:
                logger.warning(f"Model {i} has no UID, skipping")
                enriched_results.append(model)
                continue
            
            logger.info(f"Enriching model {i}/{len(models_to_process)}: {uid}")
            
            try:
                if include_full_details or include_comments:
                    enriched_data = self.get_complete_model_data(
                        uid,
                        include_comments=include_comments
                    )
                    
                    # Merge the data
                    if include_full_details:
                        # Replace basic data with full details
                        model_data = enriched_data['model']
                    else:
                        # Keep basic data
                        model_data = model.copy()
                    
                    if include_comments:
                        model_data['comments'] = enriched_data.get('comments', [])
                        model_data['fetched_comment_count'] = enriched_data.get('comment_count', 0)
                    
                    enriched_results.append(model_data)
                else:
                    enriched_results.append(model)
                    
            except Exception as e:
                logger.error(f"Failed to enrich model {uid}: {e}")
                enriched_results.append(model)
        
        logger.info(f"Enrichment complete for {len(enriched_results)} models")
        return enriched_results

    def to_dataframe(self, models: List[Dict], flatten: bool = True, comprehensive: bool = True) -> pd.DataFrame:
        """
        Convert model data to a pandas DataFrame.

        Args:
            models: List of model dictionaries from API
            flatten: If True, flatten nested structures for easier analysis
            comprehensive: If True, include ALL available fields

        Returns:
            pandas DataFrame with model data
        """
        if not models:
            logger.warning("No models to convert to DataFrame")
            return pd.DataFrame()

        if not flatten:
            # Return raw data as DataFrame
            return pd.DataFrame(models)

        if comprehensive:
            return self._flatten_comprehensive(models)
        else:
            return self._flatten_basic(models)

    def _flatten_basic(self, models: List[Dict]) -> pd.DataFrame:
        """Basic flattening with core fields only."""
        flattened_data = []

        for model in models:
            flat_row = {}

            # Core identification
            flat_row['uid'] = model.get('uid', '')
            flat_row['name'] = model.get('name', '')
            flat_row['description'] = model.get('description', '')
            flat_row['uri'] = model.get('uri', '')
            flat_row['viewerUrl'] = model.get('viewerUrl', '')
            flat_row['embedUrl'] = model.get('embedUrl', '')

            # Counts and metrics
            flat_row['viewCount'] = model.get('viewCount', 0)
            flat_row['likeCount'] = model.get('likeCount', 0)
            flat_row['commentCount'] = model.get('commentCount', 0)
            flat_row['downloadCount'] = model.get('downloadCount', 0)
            flat_row['animationCount'] = model.get('animationCount', 0)
            flat_row['soundCount'] = model.get('soundCount', 0)
            flat_row['faceCount'] = model.get('faceCount', 0)
            flat_row['vertexCount'] = model.get('vertexCount', 0)

            # Dates
            flat_row['publishedAt'] = model.get('publishedAt', '')
            flat_row['createdAt'] = model.get('createdAt', '')

            # Flags
            flat_row['isDownloadable'] = model.get('isDownloadable', False)
            flat_row['isProtected'] = model.get('isProtected', False)

            # User
            if 'user' in model and isinstance(model['user'], dict):
                flat_row['user_username'] = model['user'].get('username', '')
                flat_row['user_displayName'] = model['user'].get('displayName', '')

            # License
            if 'license' in model:
                if isinstance(model['license'], dict):
                    flat_row['license_label'] = model['license'].get('label', '')
                    flat_row['license_slug'] = model['license'].get('slug', '')
                else:
                    flat_row['license'] = model['license']

            # Tags and categories
            if 'tags' in model and isinstance(model['tags'], list):
                flat_row['tags'] = ', '.join([t.get('name', t.get('slug', '')) for t in model['tags']])

            if 'categories' in model and isinstance(model['categories'], list):
                flat_row['categories'] = ', '.join([c.get('name', '') for c in model['categories']])

            flattened_data.append(flat_row)

        return pd.DataFrame(flattened_data)

    def _flatten_comprehensive(self, models: List[Dict]) -> pd.DataFrame:
        """
        Comprehensive flattening that captures ALL available fields from the Swagger API.
        """
        flattened_data = []

        for model in models:
            flat_row = {}

            # ==================== CORE IDENTIFICATION ====================
            flat_row['uid'] = model.get('uid', '')
            flat_row['name'] = model.get('name', '')
            flat_row['description'] = model.get('description', '')
            flat_row['uri'] = model.get('uri', '')
            flat_row['viewerUrl'] = model.get('viewerUrl', '')
            flat_row['embedUrl'] = model.get('embedUrl', '')
            flat_row['editorUrl'] = model.get('editorUrl', '')  # NEW: Editor URL
            flat_row['slug'] = model.get('slug', '')  # NEW: Model slug
            
            # ==================== COUNTS AND METRICS ====================
            flat_row['viewCount'] = model.get('viewCount', 0)
            flat_row['likeCount'] = model.get('likeCount', 0)
            flat_row['commentCount'] = model.get('commentCount', 0)
            flat_row['downloadCount'] = model.get('downloadCount', 0)
            flat_row['animationCount'] = model.get('animationCount', 0)
            flat_row['soundCount'] = model.get('soundCount', 0)
            
            # Geometry
            flat_row['faceCount'] = model.get('faceCount', 0)
            flat_row['vertexCount'] = model.get('vertexCount', 0)
            flat_row['materialCount'] = model.get('materialCount', 0)
            flat_row['textureCount'] = model.get('textureCount', 0)
            
            # ==================== DATES ====================
            flat_row['publishedAt'] = model.get('publishedAt', '')
            flat_row['createdAt'] = model.get('createdAt', '')
            flat_row['updatedAt'] = model.get('updatedAt', '')  # NEW: Last update
            flat_row['staffpickedAt'] = model.get('staffpickedAt', '')
            
            # ==================== FLAGS AND SETTINGS ====================
            flat_row['isDownloadable'] = model.get('isDownloadable', False)
            flat_row['isProtected'] = model.get('isProtected', False)
            flat_row['isPublished'] = model.get('isPublished', True)
            flat_row['isAgeRestricted'] = model.get('isAgeRestricted', False)
            flat_row['hasCommentsDisabled'] = model.get('hasCommentsDisabled', False)
            flat_row['isArchivesReady'] = model.get('isArchivesReady', False)  # NEW: Archives ready flag
            flat_row['isInspectable'] = model.get('isInspectable', False)  # NEW: Inspector enabled
            
            # ==================== NEW FIELDS FROM SWAGGER ====================
            flat_row['source'] = model.get('source', '')  # NEW: Source information
            flat_row['pbrType'] = model.get('pbrType', '')  # NEW: PBR type (metalness/specular)
            flat_row['price'] = model.get('price', 0)  # NEW: Store price
            flat_row['processingStatus'] = model.get('processingStatus', '')  # NEW: Processing status
            flat_row['downloadType'] = model.get('downloadType', '')  # NEW: Download type
            flat_row['visibility'] = model.get('visibility', '')  # NEW: Visibility setting
            
            # Status object (NEW)
            if 'status' in model and isinstance(model['status'], dict):
                flat_row['status_processing'] = model['status'].get('processing', '')
                flat_row['status_error'] = model['status'].get('error', '')
            
            # ==================== USER INFORMATION ====================
            if 'user' in model and isinstance(model['user'], dict):
                user = model['user']
                flat_row['user_uid'] = user.get('uid', '')
                flat_row['user_username'] = user.get('username', '')
                flat_row['user_displayName'] = user.get('displayName', '')
                flat_row['user_profileUrl'] = user.get('profileUrl', '')
                flat_row['user_account'] = user.get('account', '')
                flat_row['user_uri'] = user.get('uri', '')
                
                # User avatar
                if 'avatar' in user:
                    if isinstance(user['avatar'], dict):
                        avatar_images = user['avatar'].get('images', [])
                        if avatar_images:
                            flat_row['user_avatar_url'] = avatar_images[-1].get('url', '')
                    elif isinstance(user['avatar'], str):
                        flat_row['user_avatar_url'] = user['avatar']
            
            # ==================== ORGANIZATION INFORMATION (NEW) ====================
            if 'org' in model and isinstance(model['org'], dict):
                org = model['org']
                flat_row['org_uid'] = org.get('uid', '')
                flat_row['org_username'] = org.get('username', '')
                flat_row['org_displayName'] = org.get('displayName', '')
                flat_row['org_viewerUrl'] = org.get('viewerUrl', '')
                flat_row['org_commentCount'] = org.get('commentCount', 0)
                
                # Organization project
                if 'project' in org and isinstance(org['project'], dict):
                    flat_row['org_project_uid'] = org['project'].get('uid', '')
                    flat_row['org_project_name'] = org['project'].get('name', '')
            
            # ==================== LICENSE INFORMATION ====================
            if 'license' in model:
                if isinstance(model['license'], dict):
                    license_info = model['license']
                    flat_row['license_label'] = license_info.get('label', '')
                    flat_row['license_fullName'] = license_info.get('fullName', '')
                    flat_row['license_slug'] = license_info.get('slug', '')
                    flat_row['license_requirements'] = license_info.get('requirements', '')
                    flat_row['license_url'] = license_info.get('url', '')
                elif isinstance(model['license'], str):
                    flat_row['license'] = model['license']
            
            # ==================== CATEGORIES ====================
            if 'categories' in model:
                if isinstance(model['categories'], list):
                    flat_row['categories'] = ', '.join([cat.get('name', '') for cat in model['categories']])
                    flat_row['category_slugs'] = ', '.join([cat.get('slug', '') for cat in model['categories']])
                    flat_row['category_uids'] = ', '.join([cat.get('uid', '') for cat in model['categories']])
                    flat_row['category_count'] = len(model['categories'])
                elif isinstance(model['categories'], str):
                    flat_row['categories'] = model['categories']
            
            # ==================== TAGS ====================
            if 'tags' in model:
                if isinstance(model['tags'], list):
                    flat_row['tags'] = ', '.join([tag.get('name', tag.get('slug', '')) for tag in model['tags']])
                    flat_row['tag_slugs'] = ', '.join([tag.get('slug', '') for tag in model['tags']])
                    flat_row['tag_count'] = len(model['tags'])
                elif isinstance(model['tags'], str):
                    flat_row['tags'] = model['tags']
            
            # Organization tags (NEW)
            if 'orgTags' in model:
                if isinstance(model['orgTags'], list):
                    flat_row['orgTags'] = ', '.join(model['orgTags'])
                elif isinstance(model['orgTags'], str):
                    flat_row['orgTags'] = model['orgTags']
            
            # ==================== ARCHIVES (COMPLETE WITH ALL FIELDS) ====================
            if 'archives' in model and isinstance(model['archives'], dict):
                archives = model['archives']
                
                # Process each archive type: source, gltf, glb, usdz
                for archive_type in ['source', 'gltf', 'glb', 'usdz']:
                    if archive_type in archives and isinstance(archives[archive_type], dict):
                        archive_data = archives[archive_type]
                        flat_row[f'archive_{archive_type}_size'] = archive_data.get('size', 0)
                        flat_row[f'archive_{archive_type}_faceCount'] = archive_data.get('faceCount', 0)
                        flat_row[f'archive_{archive_type}_vertexCount'] = archive_data.get('vertexCount', 0)
                        flat_row[f'archive_{archive_type}_textureCount'] = archive_data.get('textureCount', 0)
                        flat_row[f'archive_{archive_type}_textureMaxResolution'] = archive_data.get('textureMaxResolution', 0)  # NEW
            
            # ==================== THUMBNAILS ====================
            if 'thumbnails' in model:
                if isinstance(model['thumbnails'], dict):
                    images = model['thumbnails'].get('images', [])
                    if images:
                        flat_row['thumbnail_url_small'] = images[0].get('url', '') if len(images) > 0 else ''
                        flat_row['thumbnail_url_medium'] = images[len(images)//2].get('url', '') if len(images) > 1 else ''
                        flat_row['thumbnail_url_large'] = images[-1].get('url', '') if images else ''
                        flat_row['thumbnail_count'] = len(images)
                elif isinstance(model['thumbnails'], str):
                    flat_row['thumbnails'] = model['thumbnails']
            
            # ==================== COLLECTIONS ====================
            if 'collections' in model and isinstance(model['collections'], list):
                flat_row['collection_count'] = len(model['collections'])
                flat_row['collections'] = ', '.join([col.get('name', '') for col in model['collections']])
                flat_row['collection_uids'] = ', '.join([col.get('uid', '') for col in model['collections']])
            
            # ==================== OPTIONS ====================
            if 'options' in model and isinstance(model['options'], dict):
                options = model['options']
                flat_row['options_shadeless'] = options.get('shadeless', False)
                flat_row['options_showBackground'] = options.get('showBackground', True)
                flat_row['options_backgroundColor'] = options.get('backgroundColor', '')
                flat_row['options_shading'] = options.get('shading', '')
            
            # ==================== COMMENTS (IF FETCHED) ====================
            if 'comments' in model:
                flat_row['has_fetched_comments'] = True
                flat_row['fetched_comment_count'] = model.get('fetched_comment_count', 
                                                              len(model['comments']) if isinstance(model['comments'], list) else 0)
            else:
                flat_row['has_fetched_comments'] = False
                flat_row['fetched_comment_count'] = 0
            
            flattened_data.append(flat_row)

        return pd.DataFrame(flattened_data)

    def comments_to_dataframe(self, comments: List[Dict]) -> pd.DataFrame:
        """
        Convert comments data to a pandas DataFrame.

        Args:
            comments: List of comment dictionaries

        Returns:
            pandas DataFrame with comment data
        """
        if not comments:
            logger.warning("No comments to convert to DataFrame")
            return pd.DataFrame()

        flattened_comments = []
        
        for comment in comments:
            flat_comment = {
                'uid': comment.get('uid', ''),
                'body': comment.get('body', ''),
                'createdAt': comment.get('createdAt', ''),
                'htmlBody': comment.get('htmlBody', ''),
                'parentUid': comment.get('parentUid', ''),
            }
            
            # Author information
            if 'author' in comment and isinstance(comment['author'], dict):
                author = comment['author']
                flat_comment['author_uid'] = author.get('uid', '')
                flat_comment['author_username'] = author.get('username', '')
                flat_comment['author_displayName'] = author.get('displayName', '')
                flat_comment['author_profileUrl'] = author.get('profileUrl', '')
            
            flattened_comments.append(flat_comment)
        
        return pd.DataFrame(flattened_comments)

    def search_cultural_heritage(
        self,
        query: str = "",
        max_results: Optional[int] = None,
        include_full_details: bool = False,
        include_comments: bool = False,
        **kwargs
    ) -> pd.DataFrame:
        """
        Convenience method to search cultural heritage models and return as DataFrame.

        Args:
            query: Additional search query (combined with cultural heritage category)
            max_results: Maximum number of results
            include_full_details: If True, fetch full details for each model (slower)
            include_comments: If True, also fetch comments (much slower)
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

        if include_full_details or include_comments:
            models = self.enrich_search_results(
                models,
                include_full_details=include_full_details,
                include_comments=include_comments
            )

        return self.to_dataframe(models, comprehensive=True)

    def export_to_csv(self, df: pd.DataFrame, filename: str):
        """
        Export DataFrame to CSV file.

        Args:
            df: pandas DataFrame
            filename: Output CSV filename
        """
        df.to_csv(filename, index=False, encoding='utf-8')
        logger.info(f"Data exported to {filename}")

    def export_complete_data_to_json(self, models: List[Dict], filename: str):
        """
        Export complete model data (including comments) to JSON file.

        Args:
            models: List of model dictionaries
            filename: Output JSON filename
        """
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(models, f, indent=2, ensure_ascii=False)
        logger.info(f"Complete data exported to {filename}")

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
    include_comments: bool = False,
    api_token: Optional[str] = None
) -> pd.DataFrame:
    """
    Quick search function for immediate results.

    Args:
        query: Search query
        cultural_heritage: If True, filter by cultural heritage category
        max_results: Maximum results to retrieve
        include_comments: If True, fetch comments for each model (slower)
        api_token: Optional API token

    Returns:
        pandas DataFrame with results
    """
    scraper = SketchfabScraper(api_token=api_token)

    if cultural_heritage:
        return scraper.search_cultural_heritage(
            query=query,
            max_results=max_results,
            include_comments=include_comments
        )
    else:
        models = scraper.search_models(query=query, max_results=max_results)
        if include_comments:
            models = scraper.enrich_search_results(
                models,
                include_full_details=False,
                include_comments=True
            )
        return scraper.to_dataframe(models)


if __name__ == "__main__":
    # Example usage demonstrating all features
    print("Sketchfab Cultural Heritage Scraper - COMPLETE VERSION")
    print("=" * 70)

    # Initialize scraper
    scraper = SketchfabScraper(rate_limit_delay=1.5)

    # Example 1: Basic search
    print("\n[Example 1] Basic search for Roman models...")
    df = scraper.search_cultural_heritage(
        query="roman",
        max_results=5
    )
    print(f"Found {len(df)} models")
    print("\nAvailable columns (first 20):")
    print(df.columns.tolist()[:20])

    # Example 2: Get comments for a model
    if len(df) > 0:
        test_uid = df.iloc[0]['uid']
        print(f"\n[Example 2] Fetching comments for model: {test_uid}")
        comments = scraper.get_model_comments(test_uid)
        print(f"Found {len(comments)} comments")

    # Example 3: Get complete data for a model
    if len(df) > 0:
        test_uid = df.iloc[0]['uid']
        print(f"\n[Example 3] Getting complete data for: {test_uid}")
        complete_data = scraper.get_complete_model_data(test_uid, include_comments=True)
        print(f"Available fields in model: {list(complete_data['model'].keys())[:15]}...")
        print(f"Comments count: {complete_data.get('comment_count', 0)}")

    # Export
    scraper.export_to_csv(df, 'cultural_heritage_models.csv')
    print("\n✓ Data saved to: cultural_heritage_models.csv")
