# Sketchfab Cultural Heritage API Scraper

A polite, research-focused Python tool for retrieving cultural heritage 3D model data from the Sketchfab Data API v3. Designed for discourse analysis and scholarly examination of how modelers represent and describe cultural heritage in digital 3D spaces.

## 🎯 Purpose

This tool enables researchers to:
- Retrieve cultural heritage model metadata from Sketchfab
- Analyze discourse patterns in model descriptions and tags
- Study licensing practices in digital cultural heritage
- Examine engagement patterns with cultural heritage content
- Export data in tabular format (pandas DataFrame/CSV) for further analysis

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/km-sf.git
cd km-sf

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```python
from sketchfab_scraper import SketchfabScraper

# Initialize scraper
scraper = SketchfabScraper(rate_limit_delay=1.5)

# Search cultural heritage models
df = scraper.search_cultural_heritage(
    query="roman archaeology",
    max_results=100
)

# Export to CSV
scraper.export_to_csv(df, 'roman_models.csv')
```

### Quick Search

```python
from sketchfab_scraper import quick_search

# One-liner for immediate results
df = quick_search("ancient egypt", max_results=50)
print(df[['name', 'user_username', 'viewCount']].head())
```

## 📚 Features

### Core Functionality

- ✅ **Polite Rate Limiting**: Built-in delays between requests to respect API limits
- ✅ **Automatic Pagination**: Seamlessly retrieve large result sets
- ✅ **Authentication Support**: Optional API token for authenticated requests
- ✅ **Error Handling**: Automatic retry on rate limit errors (429)
- ✅ **Pandas Integration**: Direct conversion to DataFrames for analysis
- ✅ **Flexible Searching**: Multiple search parameters and filters
- ✅ **Data Export**: Easy CSV export for further analysis

### Search Parameters

The scraper supports comprehensive search filtering:

- **Query terms**: Free-text search across titles, descriptions, tags
- **Categories**: Filter by Sketchfab categories (e.g., 'cultural-heritage-history')
- **Tags**: Filter by specific tags
- **Licenses**: Filter by Creative Commons and other licenses
- **Downloadability**: Limit to downloadable models
- **Polygon count**: Filter by model complexity (min/max face count)
- **Animation**: Filter animated models
- **Sorting**: By relevance, likes, views, publication date, etc.

## 📖 Documentation

### API Token (Optional)

While many searches work without authentication, having an API token provides:
- Access to more data fields
- Higher rate limits
- Ability to access private models (if authorized)

**To get your API token:**
1. Log in to Sketchfab
2. Visit https://sketchfab.com/settings/password
3. Find your API token in the settings
4. Keep it private!

```python
scraper = SketchfabScraper(api_token="your_token_here")
```

### Search Examples

#### Basic Cultural Heritage Search

```python
# Search within cultural heritage category
df = scraper.search_cultural_heritage(
    query="medieval architecture",
    max_results=100
)
```

#### Advanced Filtering

```python
# Search with multiple filters
models = scraper.search_models(
    query="ancient pottery",
    categories='cultural-heritage-history',
    downloadable=True,
    licenses=['cc0', 'by', 'by-sa'],  # Open licenses only
    sort_by='-likeCount',  # Most liked first
    min_face_count=10000,  # Detailed models
    max_results=50
)

df = scraper.to_dataframe(models)
```

#### Search by User

```python
# Get all models from a specific creator
user_models = scraper.get_user_models("username", max_results=100)
df_user = scraper.to_dataframe(user_models)
```

#### Get Model Details

```python
# Get detailed information about a specific model
model_uid = "abc123xyz"  # Model UID from search results
details = scraper.get_model_details(model_uid)
```

### Data Fields

The scraper extracts and flattens the following fields:

**Basic Info:**
- `uid`: Unique model identifier
- `name`: Model name
- `description`: Model description
- `viewerUrl`: Link to model on Sketchfab

**Engagement:**
- `viewCount`: Number of views
- `likeCount`: Number of likes
- `commentCount`: Number of comments

**User Info:**
- `user_username`: Creator's username
- `user_displayName`: Creator's display name
- `user_profileUrl`: Link to creator's profile
- `user_account`: Account type

**Technical:**
- `faceCount`: Number of polygons/faces
- `vertexCount`: Number of vertices
- `animationCount`: Number of animations
- `isDownloadable`: Whether model can be downloaded

**Metadata:**
- `publishedAt`: Publication date
- `createdAt`: Creation date
- `categories`: Categories (comma-separated)
- `tags`: Tags (comma-separated)
- `license_label`: License name
- `license_slug`: License identifier
- `license_requirements`: License requirements

### Rate Limiting

The scraper implements polite rate limiting:

```python
# Adjust delay between requests (seconds)
scraper = SketchfabScraper(rate_limit_delay=2.0)  # 2 seconds between requests
```

If you encounter 429 errors (rate limit exceeded):
1. Increase the `rate_limit_delay` parameter
2. The scraper will automatically wait 60 seconds and retry once
3. Consider reducing `max_results` or batching requests

## 🔬 Google Colab Usage

The included Jupyter notebook (`sketchfab_heritage_analysis.ipynb`) is designed for Google Colab and includes:

- Complete setup instructions
- Example searches and data collection
- Data visualization examples
- Discourse analysis techniques
- Text analysis (word clouds, keyword analysis)
- Export examples

**To use in Colab:**

1. Upload `sketchfab_heritage_analysis.ipynb` to Google Colab
2. Upload `sketchfab_scraper.py` to the Colab session
3. Run the cells sequentially

Alternatively, clone from GitHub in Colab:

```python
!git clone https://github.com/yourusername/km-sf.git
import sys
sys.path.append('/content/km-sf')
from sketchfab_scraper import SketchfabScraper
```

## 📊 Example Analyses

### Discourse Theme Analysis

```python
# Analyze discourse themes in descriptions
discourse_keywords = {
    'preservation': ['preserv', 'conserv', 'restor'],
    'authenticity': ['authentic', 'original', 'genuine'],
    'education': ['educat', 'learn', 'teach', 'research'],
    'technology': ['scan', 'photogrammetry', 'laser', 'digital']
}

for theme, keywords in discourse_keywords.items():
    count = df['description'].str.contains('|'.join(keywords), case=False).sum()
    print(f"{theme}: {count} models ({count/len(df)*100:.1f}%)")
```

### Tag Analysis

```python
# Most common tags
all_tags = df['tags'].str.split(', ').explode()
tag_counts = all_tags.value_counts().head(20)
print(tag_counts)

# Word cloud
from wordcloud import WordCloud
wordcloud = WordCloud(width=800, height=400).generate(' '.join(all_tags.dropna()))
plt.imshow(wordcloud)
plt.axis('off')
plt.show()
```

### License Distribution

```python
# Analyze licensing practices
license_dist = df['license_label'].value_counts()
license_dist.plot(kind='bar')
plt.title('License Distribution in Cultural Heritage Models')
plt.show()
```

### Creator Analysis

```python
# Most prolific creators
top_creators = df['user_username'].value_counts().head(10)
print("Top 10 Most Prolific Creators:")
print(top_creators)
```

## ⚠️ Ethical Considerations

### Responsible Use

- **Respect Terms of Service**: Use data in accordance with Sketchfab's ToS
- **Rate Limiting**: Always use polite rate limiting to avoid overloading servers
- **Attribution**: Cite creators when using models or data in publications
- **Privacy**: Consider privacy implications when analyzing user data
- **Research Ethics**: Follow your institution's research ethics guidelines

### Data Citation

When publishing research using this tool:

```
Data retrieved from Sketchfab via the Sketchfab Data API v3
(https://docs.sketchfab.com/data-api/v3/index.html)
Retrieved on [DATE] using km-sf scraper (https://github.com/yourusername/km-sf)
```

Individual models should be cited with:
- Model name
- Creator name
- Sketchfab URL
- License information
- Access date

## 🔧 Technical Details

### Dependencies

- `requests`: HTTP library for API calls
- `pandas`: Data manipulation and analysis
- `matplotlib`: Plotting and visualization (optional)
- `seaborn`: Statistical visualization (optional)
- `wordcloud`: Word cloud generation (optional)

### API Endpoints

The scraper uses the following Sketchfab API v3 endpoints:

- `/v3/search`: Search for models
- `/v3/models/{uid}`: Get model details

### Error Handling

The scraper handles:
- HTTP errors with informative messages
- Rate limiting (429 errors) with automatic retry
- Network timeouts and connection errors
- Empty result sets

## 🧪 Testing

The project includes a comprehensive test suite using pytest.

### Running Tests

```bash
# Run all unit tests (skip integration tests that require network)
pytest test_sketchfab_scraper.py -v -m "not integration"

# Run all tests including integration tests
pytest test_sketchfab_scraper.py -v

# Run with coverage report
pytest test_sketchfab_scraper.py --cov=sketchfab_scraper --cov-report=html

# Run specific test class
pytest test_sketchfab_scraper.py::TestSearchParameters -v

# Run specific test
pytest test_sketchfab_scraper.py::TestSearchParameters::test_category_filter -v
```

### Test Coverage

The test suite includes:
- **Initialization tests**: API token handling, rate limiting setup
- **Rate limiting tests**: Delay verification, polite scraping behavior
- **Search parameter tests**: All search filters and combinations
- **API request tests**: Success, errors, retries, rate limiting
- **Pagination tests**: Single page, multiple pages, max_results
- **Data conversion tests**: DataFrame creation, flattening, field extraction
- **Helper method tests**: Convenience functions, CSV export
- **Integration tests**: Real API calls (marked with `@pytest.mark.integration`)

### Test Organization

Tests are organized into classes by functionality:
- `TestInitialization`: Scraper setup and configuration
- `TestRateLimiting`: Rate limiting behavior
- `TestSearchParameters`: Search parameter construction
- `TestAPIRequests`: HTTP request handling
- `TestPagination`: Multi-page result handling
- `TestDataConversion`: pandas DataFrame conversion
- `TestHelperMethods`: Utility functions
- `TestQuickSearch`: Convenience functions
- `TestIntegration`: Real API integration tests

## 📝 Project Structure

```
km-sf/
├── sketchfab_scraper.py               # Main scraper module
├── sketchfab_heritage_analysis.ipynb  # Google Colab notebook
├── example_usage.py                   # Standalone example script
├── test_sketchfab_scraper.py          # Comprehensive test suite
├── requirements.txt                   # Python dependencies
├── pytest.ini                         # Pytest configuration
├── README.md                          # This file
└── examples/                          # Example scripts (future)
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This tool is provided for research purposes. Please respect:
- Sketchfab's Terms of Service
- Individual model licenses
- Creator attribution requirements
- Research ethics guidelines

## 🔗 Resources

- **Sketchfab Data API Documentation**: https://docs.sketchfab.com/data-api/v3/index.html
- **Sketchfab Developer Portal**: https://sketchfab.com/developers
- **Cultural Heritage Category**: https://sketchfab.com/3d-models/cultural-heritage-history
- **API Token Settings**: https://sketchfab.com/settings/password

## 📧 Contact

For questions, issues, or research collaborations, please:
- Open an issue on GitHub
- Contact the repository maintainer

## 🙏 Acknowledgments

- Sketchfab for providing the API and hosting cultural heritage models
- The cultural heritage 3D modeling community
- Contributors to this project

---

**Version**: 1.0.0
**Last Updated**: October 2025
**Maintainer**: Research Team
**Status**: Active Development
