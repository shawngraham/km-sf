"""
Comprehensive test suite for Sketchfab Cultural Heritage Scraper

Run with: pytest test_sketchfab_scraper.py -v
Run with coverage: pytest test_sketchfab_scraper.py --cov=sketchfab_scraper
Run integration tests: pytest test_sketchfab_scraper.py -v -m integration
Skip integration tests: pytest test_sketchfab_scraper.py -v -m "not integration"
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import requests
from sketchfab_scraper import SketchfabScraper, quick_search


# Test Fixtures

@pytest.fixture
def scraper():
    """Create a scraper instance for testing."""
    return SketchfabScraper(rate_limit_delay=0.1)  # Fast for testing


@pytest.fixture
def scraper_with_token():
    """Create a scraper instance with API token."""
    return SketchfabScraper(api_token="test_token_123", rate_limit_delay=0.1)


@pytest.fixture
def mock_search_response():
    """Mock API response for search endpoint."""
    return {
        "results": [
            {
                "uid": "model1",
                "name": "Roman Temple",
                "description": "Ancient Roman temple reconstruction",
                "viewCount": 1000,
                "likeCount": 50,
                "commentCount": 10,
                "animationCount": 0,
                "publishedAt": "2024-01-01T00:00:00Z",
                "createdAt": "2024-01-01T00:00:00Z",
                "viewerUrl": "https://sketchfab.com/models/model1",
                "isDownloadable": True,
                "faceCount": 10000,
                "vertexCount": 15000,
                "user": {
                    "username": "testuser",
                    "displayName": "Test User",
                    "profileUrl": "https://sketchfab.com/testuser",
                    "account": "basic"
                },
                "license": {
                    "label": "CC Attribution",
                    "requirements": "attribution",
                    "slug": "by"
                },
                "categories": [
                    {"name": "Cultural Heritage & History", "slug": "cultural-heritage-history"}
                ],
                "tags": [
                    {"name": "roman"},
                    {"name": "ancient"},
                    {"name": "temple"}
                ],
                "thumbnails": {
                    "images": [
                        {"url": "https://example.com/thumb.jpg"}
                    ]
                }
            },
            {
                "uid": "model2",
                "name": "Ancient Pottery",
                "description": "Archaeological find from excavation",
                "viewCount": 500,
                "likeCount": 25,
                "commentCount": 5,
                "animationCount": 0,
                "publishedAt": "2024-01-02T00:00:00Z",
                "createdAt": "2024-01-02T00:00:00Z",
                "viewerUrl": "https://sketchfab.com/models/model2",
                "isDownloadable": False,
                "faceCount": 5000,
                "vertexCount": 7500,
                "user": {
                    "username": "testuser2",
                    "displayName": "Test User 2",
                    "profileUrl": "https://sketchfab.com/testuser2",
                    "account": "pro"
                },
                "license": {
                    "label": "CC Attribution-ShareAlike",
                    "requirements": "attribution, sharealike",
                    "slug": "by-sa"
                },
                "categories": [
                    {"name": "Cultural Heritage & History", "slug": "cultural-heritage-history"}
                ],
                "tags": [
                    {"name": "pottery"},
                    {"name": "archaeology"}
                ],
                "thumbnails": {
                    "images": [
                        {"url": "https://example.com/thumb2.jpg"}
                    ]
                }
            }
        ],
        "next": None,
        "previous": None,
        "cursors": {
            "next": None,
            "previous": None
        }
    }


@pytest.fixture
def mock_paginated_response():
    """Mock API response with pagination."""
    return {
        "page1": {
            "results": [{"uid": f"model{i}", "name": f"Model {i}"} for i in range(1, 11)],
            "next": "https://api.sketchfab.com/v3/search?cursor=page2"
        },
        "page2": {
            "results": [{"uid": f"model{i}", "name": f"Model {i}"} for i in range(11, 21)],
            "next": "https://api.sketchfab.com/v3/search?cursor=page3"
        },
        "page3": {
            "results": [{"uid": f"model{i}", "name": f"Model {i}"} for i in range(21, 26)],
            "next": None
        }
    }


@pytest.fixture
def mock_model_details():
    """Mock API response for model details."""
    return {
        "uid": "model1",
        "name": "Roman Temple",
        "description": "Detailed Roman temple model",
        "viewCount": 1000,
        "likeCount": 50
    }


# Unit Tests - Initialization

class TestInitialization:
    """Test scraper initialization."""

    def test_init_without_token(self):
        """Test initialization without API token."""
        scraper = SketchfabScraper()
        assert scraper.api_token is None
        assert scraper.rate_limit_delay == 1.0
        assert 'Authorization' not in scraper.session.headers

    def test_init_with_token(self):
        """Test initialization with API token."""
        scraper = SketchfabScraper(api_token="test_token")
        assert scraper.api_token == "test_token"
        assert scraper.session.headers['Authorization'] == "Token test_token"

    def test_init_custom_rate_limit(self):
        """Test initialization with custom rate limit."""
        scraper = SketchfabScraper(rate_limit_delay=2.5)
        assert scraper.rate_limit_delay == 2.5

    def test_user_agent_set(self, scraper):
        """Test that user agent is properly set."""
        assert 'User-Agent' in scraper.session.headers
        assert 'Sketchfab-Research-Tool' in scraper.session.headers['User-Agent']


# Unit Tests - Rate Limiting

class TestRateLimiting:
    """Test rate limiting functionality."""

    def test_rate_limiting_delay(self, scraper):
        """Test that rate limiting introduces proper delay."""
        scraper.rate_limit_delay = 0.2

        start_time = time.time()
        scraper._rate_limit()
        time.sleep(0.05)  # Simulate some work
        scraper._rate_limit()
        elapsed = time.time() - start_time

        # Should have delayed approximately 0.2 seconds
        assert elapsed >= 0.15  # Allow some tolerance

    def test_no_delay_on_first_request(self, scraper):
        """Test that first request has no delay."""
        scraper.last_request_time = 0
        start_time = time.time()
        scraper._rate_limit()
        elapsed = time.time() - start_time

        # First request should be immediate
        assert elapsed < 0.1


# Unit Tests - Search Parameters

class TestSearchParameters:
    """Test search parameter construction."""

    @patch.object(SketchfabScraper, '_paginate')
    def test_basic_search_params(self, mock_paginate, scraper):
        """Test basic search parameter construction."""
        mock_paginate.return_value = []

        scraper.search_models(query="roman")

        call_args = mock_paginate.call_args
        params = call_args[0][1]

        assert params['type'] == 'models'
        assert params['q'] == 'roman'
        assert params['sort_by'] == '-relevance'

    @patch.object(SketchfabScraper, '_paginate')
    def test_category_filter(self, mock_paginate, scraper):
        """Test category filtering."""
        mock_paginate.return_value = []

        scraper.search_models(categories='cultural-heritage-history')

        params = mock_paginate.call_args[0][1]
        assert params['categories'] == 'cultural-heritage-history'

    @patch.object(SketchfabScraper, '_paginate')
    def test_multiple_categories(self, mock_paginate, scraper):
        """Test multiple category filtering."""
        mock_paginate.return_value = []

        scraper.search_models(categories=['cultural-heritage-history', 'architecture'])

        params = mock_paginate.call_args[0][1]
        assert params['categories'] == 'cultural-heritage-history,architecture'

    @patch.object(SketchfabScraper, '_paginate')
    def test_tag_filter(self, mock_paginate, scraper):
        """Test tag filtering."""
        mock_paginate.return_value = []

        scraper.search_models(tags=['ancient', 'roman'])

        params = mock_paginate.call_args[0][1]
        assert params['tags'] == 'ancient,roman'

    @patch.object(SketchfabScraper, '_paginate')
    def test_license_filter(self, mock_paginate, scraper):
        """Test license filtering."""
        mock_paginate.return_value = []

        scraper.search_models(licenses=['by', 'cc0'])

        params = mock_paginate.call_args[0][1]
        assert params['licenses'] == 'by,cc0'

    @patch.object(SketchfabScraper, '_paginate')
    def test_boolean_filters(self, mock_paginate, scraper):
        """Test boolean filter parameters."""
        mock_paginate.return_value = []

        scraper.search_models(downloadable=True, animated=False)

        params = mock_paginate.call_args[0][1]
        assert params['downloadable'] == 'true'
        assert params['animated'] == 'false'

    @patch.object(SketchfabScraper, '_paginate')
    def test_face_count_filters(self, mock_paginate, scraper):
        """Test polygon count filtering."""
        mock_paginate.return_value = []

        scraper.search_models(min_face_count=1000, max_face_count=50000)

        params = mock_paginate.call_args[0][1]
        assert params['min_face_count'] == 1000
        assert params['max_face_count'] == 50000

    @patch.object(SketchfabScraper, '_paginate')
    def test_new_filter_parameters(self, mock_paginate, scraper):
        """Test newly added filter parameters."""
        mock_paginate.return_value = []

        scraper.search_models(
            staff_picked=True,
            rigged=True,
            sound=False,
            pbr=True
        )

        params = mock_paginate.call_args[0][1]
        assert params['staff_picked'] == 'true'
        assert params['rigged'] == 'true'
        assert params['sound'] == 'false'
        assert params['pbr'] == 'true'

    @patch.object(SketchfabScraper, '_paginate')
    def test_sort_by_parameter(self, mock_paginate, scraper):
        """Test sort_by parameter."""
        mock_paginate.return_value = []

        scraper.search_models(sort_by='-likeCount')

        params = mock_paginate.call_args[0][1]
        assert params['sort_by'] == '-likeCount'

    @patch.object(SketchfabScraper, '_paginate')
    def test_kwargs_passthrough(self, mock_paginate, scraper):
        """Test that additional kwargs are passed through."""
        mock_paginate.return_value = []

        scraper.search_models(user='testuser', custom_param='value')

        params = mock_paginate.call_args[0][1]
        assert params['user'] == 'testuser'
        assert params['custom_param'] == 'value'


# Unit Tests - API Requests

class TestAPIRequests:
    """Test API request handling."""

    @patch('requests.Session.get')
    def test_successful_request(self, mock_get, scraper):
        """Test successful API request."""
        mock_response = Mock()
        mock_response.json.return_value = {"results": []}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = scraper._make_request('/search', {'q': 'test'})

        assert result == {"results": []}
        mock_get.assert_called_once()

    @patch('requests.Session.get')
    def test_rate_limit_retry(self, mock_get, scraper):
        """Test automatic retry on rate limit error."""
        # First call returns 429, second succeeds
        mock_response_429 = Mock()
        mock_response_429.status_code = 429
        mock_response_429.raise_for_status.side_effect = requests.exceptions.HTTPError()

        mock_response_200 = Mock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {"results": []}

        mock_get.side_effect = [mock_response_429, mock_response_200]

        with patch('time.sleep'):  # Skip actual sleep
            result = scraper._make_request('/search')

        assert result == {"results": []}
        assert mock_get.call_count == 2

    @patch('requests.Session.get')
    def test_http_error_propagation(self, mock_get, scraper):
        """Test that HTTP errors are properly propagated."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_get.return_value = mock_response

        with pytest.raises(requests.exceptions.HTTPError):
            scraper._make_request('/invalid')

    @patch('requests.Session.get')
    def test_network_error(self, mock_get, scraper):
        """Test network error handling."""
        mock_get.side_effect = requests.exceptions.ConnectionError()

        with pytest.raises(requests.exceptions.RequestException):
            scraper._make_request('/search')


# Unit Tests - Pagination

class TestPagination:
    """Test pagination handling."""

    @patch.object(SketchfabScraper, '_make_request')
    def test_single_page(self, mock_request, scraper):
        """Test pagination with single page of results."""
        mock_request.return_value = {
            "results": [{"uid": "1"}, {"uid": "2"}],
            "next": None
        }

        results = scraper._paginate('/search', {})

        assert len(results) == 2
        assert mock_request.call_count == 1

    @patch.object(SketchfabScraper, '_make_request')
    @patch('requests.Session.get')
    def test_multiple_pages(self, mock_session_get, mock_request, scraper):
        """Test pagination across multiple pages."""
        # First page
        mock_request.return_value = {
            "results": [{"uid": "1"}, {"uid": "2"}],
            "next": "https://api.sketchfab.com/v3/search?page=2"
        }

        # Second page
        mock_response_page2 = Mock()
        mock_response_page2.json.return_value = {
            "results": [{"uid": "3"}, {"uid": "4"}],
            "next": None
        }
        mock_response_page2.status_code = 200
        mock_session_get.return_value = mock_response_page2

        results = scraper._paginate('/search', {})

        assert len(results) == 4
        assert results[0]['uid'] == "1"
        assert results[3]['uid'] == "4"

    @patch.object(SketchfabScraper, '_make_request')
    def test_max_results_limit(self, mock_request, scraper):
        """Test that max_results limits returned results."""
        mock_request.return_value = {
            "results": [{"uid": str(i)} for i in range(20)],
            "next": None
        }

        results = scraper._paginate('/search', {}, max_results=10)

        assert len(results) == 10


# Unit Tests - Data Conversion

class TestDataConversion:
    """Test data conversion to pandas DataFrames."""

    def test_to_dataframe_basic(self, scraper, mock_search_response):
        """Test basic conversion to DataFrame."""
        models = mock_search_response['results']
        df = scraper.to_dataframe(models, flatten=False)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert 'uid' in df.columns
        assert 'name' in df.columns

    def test_to_dataframe_flattened(self, scraper, mock_search_response):
        """Test flattened DataFrame conversion."""
        models = mock_search_response['results']
        df = scraper.to_dataframe(models, flatten=True)

        assert isinstance(df, pd.DataFrame)
        assert 'user_username' in df.columns
        assert 'license_label' in df.columns
        assert 'categories' in df.columns
        assert df.loc[0, 'user_username'] == 'testuser'

    def test_to_dataframe_empty(self, scraper):
        """Test DataFrame conversion with empty input."""
        df = scraper.to_dataframe([])

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_flatten_categories(self, scraper, mock_search_response):
        """Test that categories are properly flattened."""
        models = mock_search_response['results']
        df = scraper.to_dataframe(models, flatten=True)

        assert 'Cultural Heritage & History' in df.loc[0, 'categories']

    def test_flatten_tags(self, scraper, mock_search_response):
        """Test that tags are properly flattened."""
        models = mock_search_response['results']
        df = scraper.to_dataframe(models, flatten=True)

        assert 'roman' in df.loc[0, 'tags']
        assert 'ancient' in df.loc[0, 'tags']


# Unit Tests - Helper Methods

class TestHelperMethods:
    """Test helper methods."""

    @patch.object(SketchfabScraper, 'search_models')
    def test_search_cultural_heritage(self, mock_search, scraper):
        """Test cultural heritage convenience method."""
        mock_search.return_value = []

        scraper.search_cultural_heritage(query="roman", max_results=50)

        mock_search.assert_called_once()
        call_args = mock_search.call_args
        assert call_args[1]['query'] == 'roman'
        assert call_args[1]['categories'] == 'cultural-heritage-history'
        assert call_args[1]['max_results'] == 50

    @patch.object(SketchfabScraper, '_make_request')
    def test_get_model_details(self, mock_request, scraper, mock_model_details):
        """Test get_model_details method."""
        mock_request.return_value = mock_model_details

        result = scraper.get_model_details("model1")

        assert result == mock_model_details
        mock_request.assert_called_with('/models/model1')

    @patch.object(SketchfabScraper, '_paginate')
    def test_get_user_models(self, mock_paginate, scraper):
        """Test get_user_models method."""
        mock_paginate.return_value = []

        scraper.get_user_models("testuser", max_results=100)

        mock_paginate.assert_called_once()
        params = mock_paginate.call_args[0][1]
        assert params['type'] == 'models'
        assert params['user'] == 'testuser'

    def test_export_to_csv(self, scraper, tmp_path):
        """Test CSV export functionality."""
        df = pd.DataFrame({
            'uid': ['1', '2'],
            'name': ['Model 1', 'Model 2']
        })

        csv_file = tmp_path / "test.csv"
        scraper.export_to_csv(df, str(csv_file))

        assert csv_file.exists()

        # Read back and verify
        df_read = pd.read_csv(csv_file)
        assert len(df_read) == 2
        assert list(df_read.columns) == ['uid', 'name']


# Unit Tests - Quick Search Function

class TestQuickSearch:
    """Test quick_search convenience function."""

    @patch('sketchfab_scraper.SketchfabScraper')
    def test_quick_search_cultural_heritage(self, mock_scraper_class):
        """Test quick_search with cultural heritage filter."""
        mock_instance = Mock()
        mock_instance.search_cultural_heritage.return_value = pd.DataFrame()
        mock_scraper_class.return_value = mock_instance

        result = quick_search("roman", cultural_heritage=True, max_results=50)

        assert isinstance(result, pd.DataFrame)
        mock_instance.search_cultural_heritage.assert_called_once()

    @patch('sketchfab_scraper.SketchfabScraper')
    def test_quick_search_general(self, mock_scraper_class):
        """Test quick_search without cultural heritage filter."""
        mock_instance = Mock()
        mock_instance.search_models.return_value = []
        mock_instance.to_dataframe.return_value = pd.DataFrame()
        mock_scraper_class.return_value = mock_instance

        result = quick_search("car", cultural_heritage=False, max_results=50)

        assert isinstance(result, pd.DataFrame)
        mock_instance.search_models.assert_called_once()


# Integration Tests (require actual API access)

@pytest.mark.integration
class TestIntegration:
    """Integration tests that require actual API access."""

    def test_real_search(self):
        """Test real API search (requires network)."""
        scraper = SketchfabScraper(rate_limit_delay=2.0)

        results = scraper.search_models(
            query="test",
            max_results=5
        )

        assert isinstance(results, list)
        # API might return 0-5 results depending on what's available

    def test_real_cultural_heritage_search(self):
        """Test real cultural heritage search (requires network)."""
        scraper = SketchfabScraper(rate_limit_delay=2.0)

        df = scraper.search_cultural_heritage(
            query="roman",
            max_results=5
        )

        assert isinstance(df, pd.DataFrame)
        if len(df) > 0:
            assert 'name' in df.columns
            assert 'uid' in df.columns


# Test Markers and Configuration

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
