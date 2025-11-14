# Sketchfab Cultural Heritage Data Collection

A research-focused Python toolkit for collecting cultural heritage 3D model metadata from Sketchfab via their official API. Designed for discourse analysis and scholarly examination of how modelers represent and describe cultural heritage in digital 3D spaces.

## Important: Start Here

**Use the Enhanced Scraper** (`sketchfab_scraper_enhanced.py`) for all data collection. It includes:
- Automatic rate limit handling with exponential backoff
- Progress checkpointing (resume interrupted collections)
- Transparent logging and statistics
- Smart retry logic

Sketchfab's API has undocumented rate limits. The enhanced scraper handles these gracefully. See [DEALING_WITH_RATE_LIMITS.md](DEALING_WITH_RATE_LIMITS.md) for detailed strategies.

## Quick Start

### Installation

```bash
git clone https://github.com/yourusername/km-sf.git
cd km-sf
pip install -r requirements.txt
```

### Recommended Workflow

```python
from sketchfab_scraper_enhanced import EnhancedSketchfabScraper

# Initialize with checkpointing and API token
scraper = EnhancedSketchfabScraper(
    api_token="your_token_here",  # Get at: https://sketchfab.com/settings/password
    rate_limit_delay=3.0,          # Conservative delay between requests
    max_retries=5,                 # Retry attempts on rate limits
    checkpoint_file="roman_collection.json"
)

# Collect data with automatic progress saving
try:
    results = scraper.search_models_with_checkpoints(
        query="roman",
        categories="cultural-heritage-history",
        max_results=1000,
        checkpoint_every=100  # Save progress every 100 models
    )

    # View statistics
    scraper.print_stats()

    # Results are standard model dictionaries - use with base scraper methods
    from sketchfab_scraper import SketchfabScraper
    base = SketchfabScraper()

    # Convert to DataFrame
    df = base.to_dataframe(results, comprehensive=True)

    # Export
    base.export_to_csv(df, "roman_models.csv")
    base.export_complete_data_to_json(results, "roman_models_complete.json")

except RateLimitError:
    print("Rate limited - progress saved in checkpoint file.")
    print("Wait 1-2 hours and run again to resume from checkpoint.")
```

### If Rate Limited (Resume Collection)

```python
# Load previous progress
previous_data = scraper.load_checkpoint("roman_collection.json")
print(f"Resuming from {len(previous_data)} models")

# Continue collecting where you left off
# The checkpoint file tracks what you've already collected
```

## What Data Is Available?

The API provides comprehensive metadata for each model:

### Core Model Information
- **Identification**: uid, name, description, uri, viewerUrl, embedUrl, slug
- **Metrics**: viewCount, likeCount, commentCount, downloadCount
- **Geometry**: faceCount, vertexCount, materialCount, textureCount
- **Media**: animationCount, soundCount
- **Dates**: publishedAt, createdAt, updatedAt, staffpickedAt
- **Flags**: isDownloadable, isProtected, isPublished, isAgeRestricted

### User & Author Data
- User profile: username, displayName, account type
- Avatar images
- Profile and URI links

### License Information
- License type: label, slug, fullName
- Requirements and restrictions
- License URL

### Technical Specifications
- PBR type: metalness, specular, or non-PBR
- Processing status: current state and errors
- Archive readiness: whether downloads are available
- Categories and tags
- Collections membership

### Archive Data (Per Format: gltf, glb, usdz, source)
- File size in bytes
- Face and vertex counts
- Texture count
- Texture maximum resolution

### Organization Data (For Institutional Models)
- Organization: uid, username, displayName
- Project affiliation
- Organization-specific tags
- Visibility settings

### Comments (When Requested)
- Comment text (plain and HTML)
- Comment authors
- Timestamps
- Thread structure (replies)

**Total: 85+ fields per model** - See [Sketchfab API documentation](https://docs.sketchfab.com/data-api/v3/index.html)

## Available Scrapers

### 1. Enhanced Scraper (RECOMMENDED)

**File**: `sketchfab_scraper_enhanced.py`

**Use for**: All data collection, especially large-scale

**Features**:
- Exponential backoff on rate limits
- Progress checkpointing and resume capability
- Response header inspection for rate limit info
- Request statistics tracking
- Detailed logging (console + file)
- Custom RateLimitError exception

**When to use**: Always, for any collection larger than 50 models

### 2. Base Scraper

**File**: `sketchfab_scraper.py`

**Use for**:
- Data processing and conversion (to DataFrame, CSV, JSON)
- Accessing all the comprehensive field extraction logic
- Small collections where rate limits are unlikely

**Features**:
- Comprehensive field extraction (85+ fields)
- DataFrame conversion with flattening
- Comment extraction and analysis
- Search with filters (categories, tags, licenses, downloadable, etc.)
- User model lookup

**When to use**:
- For data processing after collection
- Quick small queries (< 50 models)
- When you need the DataFrame conversion utilities

### Typical Usage Pattern

```python
from sketchfab_scraper_enhanced import EnhancedSketchfabScraper
from sketchfab_scraper import SketchfabScraper

# 1. Collect data with enhanced scraper
enhanced = EnhancedSketchfabScraper(
    api_token="your_token",
    rate_limit_delay=3.0,
    checkpoint_file="data.json"
)

results = enhanced.search_models_with_checkpoints(
    query="archaeological site",
    categories="cultural-heritage-history",
    max_results=500
)

# 2. Process with base scraper utilities
base = SketchfabScraper()
df = base.to_dataframe(results, comprehensive=True)
base.export_to_csv(df, "archaeological_sites.csv")
```

## Common Research Tasks

### Task 1: Collect Large Dataset

```python
from sketchfab_scraper_enhanced import EnhancedSketchfabScraper

scraper = EnhancedSketchfabScraper(
    api_token="your_token",
    rate_limit_delay=3.0,
    checkpoint_file="large_collection.json"
)

# Collect in batches to manage rate limits
queries = ["roman architecture", "roman sculpture", "roman pottery"]

for query in queries:
    print(f"\nCollecting: {query}")
    results = scraper.search_models_with_checkpoints(
        query=query,
        categories="cultural-heritage-history",
        max_results=500,
        checkpoint_every=100
    )

    # Save each batch
    with open(f"{query.replace(' ', '_')}.json", 'w') as f:
        json.dump(results, f)

    # Rest between batches
    time.sleep(300)  # 5 minute rest
```

### Task 2: Analyze Descriptions and Tags

```python
from sketchfab_scraper import SketchfabScraper

# Load collected data
with open("roman_architecture.json", 'r') as f:
    models = json.load(f)

base = SketchfabScraper()
df = base.to_dataframe(models, comprehensive=True)

# Extract all descriptive text
descriptions = df['description'].dropna()
tags = df['tags'].dropna()

# Analyze
print(f"Total descriptions: {len(descriptions)}")
print(f"Average description length: {descriptions.str.len().mean():.0f} characters")
print(f"Most common tags: {tags.str.split(', ').explode().value_counts().head(10)}")
```

### Task 3: Collect Comments for Discourse Analysis

```python
from sketchfab_scraper_enhanced import EnhancedSketchfabScraper
from sketchfab_scraper import SketchfabScraper

# First collect models
enhanced = EnhancedSketchfabScraper(api_token="your_token", rate_limit_delay=3.0)
models = enhanced.search_models_with_checkpoints(
    query="museum scan",
    max_results=100
)

# Then enrich with comments using base scraper
base = SketchfabScraper(api_token="your_token", rate_limit_delay=3.0)
enriched = base.enrich_search_results(
    models,
    include_full_details=True,
    include_comments=True
)

# Extract all comments
comments_df = base.extract_comments_from_models(
    enriched,
    include_model_fields=['user_username', 'viewCount', 'likeCount']
)

print(f"Total comments: {len(comments_df)}")
print(f"Unique commenters: {comments_df['author_username'].nunique()}")
```

### Task 4: Filter by License

```python
from sketchfab_scraper_enhanced import EnhancedSketchfabScraper

scraper = EnhancedSketchfabScraper(api_token="your_token", rate_limit_delay=3.0)

# Collect only CC0 and CC-BY models
results = scraper.search_models_with_checkpoints(
    query="archaeological",
    categories="cultural-heritage-history",
    licenses=['cc0', 'by'],  # CC0 and CC-BY only
    downloadable=True,
    max_results=500
)
```

### Task 5: Analyze Texture Quality

```python
from sketchfab_scraper_enhanced import EnhancedSketchfabScraper
from sketchfab_scraper import SketchfabScraper

enhanced = EnhancedSketchfabScraper(api_token="your_token", rate_limit_delay=3.0)

# Search with archive info
from sketchfab_scraper import SketchfabScraper
base = SketchfabScraper(api_token="your_token", rate_limit_delay=3.0)

models = base.search_models(
    query="3d scan",
    categories="cultural-heritage-history",
    downloadable=True,
    archives_flavours=True,  # Important: gets texture resolution
    max_results=200
)

df = base.to_dataframe(models, comprehensive=True)

# Analyze texture quality
print(f"Models with 4K+ textures: {(df['archive_gltf_textureMaxResolution'] >= 4096).sum()}")
print(f"Average texture resolution: {df['archive_gltf_textureMaxResolution'].mean():.0f}px")
print(f"\nResolution distribution:")
print(df['archive_gltf_textureMaxResolution'].value_counts().sort_index())
```

## Rate Limit Management

Sketchfab's API has undocumented rate limits that vary by:
- Authentication status (with/without token)
- Time of day
- Overall API load

**Estimated limits** (unofficial):
- Without token: ~60-100 requests/hour
- With token: ~300-500 requests/hour

### Best Practices

1. **Always use an API token** - Get one at https://sketchfab.com/settings/password
2. **Start with conservative delays** - Use `rate_limit_delay=3.0` or higher
3. **Enable checkpointing** - Always set a `checkpoint_file`
4. **Collect in batches** - Don't try to get 10,000 models in one run
5. **Monitor statistics** - Check `scraper.print_stats()` to see success rate
6. **Be patient** - Large collections may take hours or days

### If You Get Rate Limited

The enhanced scraper will:
1. Automatically retry with exponential backoff (2s, 4s, 8s, 16s, 32s, etc.)
2. Save your progress to the checkpoint file
3. Raise a `RateLimitError` after max retries

When this happens:
1. Wait 1-2 hours
2. Run your script again - it will resume from the checkpoint
3. Consider increasing `rate_limit_delay` for the next run

**See [DEALING_WITH_RATE_LIMITS.md](DEALING_WITH_RATE_LIMITS.md) for detailed strategies and examples.**

## Why Not Web Scraping?

**Direct web scraping of Sketchfab search pages does not work.**

When we attempted to scrape search result pages with Beautiful Soup, Sketchfab returns:
- HTTP Status: 403 Forbidden
- Response: "Access denied"

This is because:
1. **Bot detection**: They detect and block automated requests
2. **Terms of Service**: They want users to use the official API
3. **Protection**: Likely using Cloudflare or similar service

**The API is superior anyway**:
- More comprehensive data (85+ fields vs. limited HTML)
- Structured and reliable
- Officially supported
- More maintainable
- Includes data not visible on web pages

## API Token

While some searches work without authentication, using an API token provides:
- Higher rate limits (~300-500/hour vs ~60-100/hour)
- Access to more data fields
- Ability to access private models (if authorized)
- Better API behavior

**To get your API token**:
1. Log in to Sketchfab
2. Visit https://sketchfab.com/settings/password
3. Find your API token in the settings
4. Keep it private - don't commit it to git

## Files in This Repository

### Scrapers
- `sketchfab_scraper_enhanced.py` - **RECOMMENDED** - Enhanced scraper with rate limit handling
- `sketchfab_scraper.py` - Base scraper with comprehensive field extraction
- `practical_examples.py` - Usage examples for base scraper
- `test_all_fields.py` - Field discovery and testing

### Documentation
- `README.md` - This file
- `DEALING_WITH_RATE_LIMITS.md` - Comprehensive rate limit strategies
- `WEB_SCRAPING_FINDINGS.md` - Technical explanation of why web scraping doesn't work
- `COMMENT_TEXT_ANALYSIS.md` - Guide for analyzing comment text

### Configuration
- `requirements.txt` - Python dependencies
- `.gitignore` - Git ignore rules (includes scraped data files)

## Logging

The enhanced scraper logs to:
- **Console**: INFO level messages
- **File**: `sketchfab_scraper.log` with DEBUG level details

Check the log file to:
- See detailed request information
- Understand rate limit patterns
- Debug issues
- Track progress over time

## Example: Complete Research Workflow

```python
import json
import time
from sketchfab_scraper_enhanced import EnhancedSketchfabScraper, RateLimitError
from sketchfab_scraper import SketchfabScraper

# Phase 1: Data Collection
print("Phase 1: Collecting model metadata...")

enhanced = EnhancedSketchfabScraper(
    api_token="your_token_here",
    rate_limit_delay=3.0,
    checkpoint_file="research_data.json"
)

try:
    models = enhanced.search_models_with_checkpoints(
        query="roman imperial",
        categories="cultural-heritage-history",
        max_results=1000,
        checkpoint_every=100
    )

    enhanced.print_stats()

except RateLimitError as e:
    print(f"Rate limited: {e}")
    print("Resume later by running this script again")
    exit(1)

# Phase 2: Enrich with Comments
print("\nPhase 2: Collecting comments...")

base = SketchfabScraper(api_token="your_token_here", rate_limit_delay=3.0)

enriched = base.enrich_search_results(
    models[:50],  # Start with first 50 models
    include_full_details=True,
    include_comments=True
)

# Phase 3: Data Processing
print("\nPhase 3: Processing and exporting...")

# Create comprehensive DataFrame
df = base.to_dataframe(enriched, comprehensive=True)

# Extract comments
comments_df = base.extract_comments_from_models(
    enriched,
    include_model_fields=['user_username', 'viewCount', 'categories']
)

# Export everything
base.export_to_csv(df, "models_analysis.csv")
base.export_complete_data_to_json(enriched, "models_complete.json")

if len(comments_df) > 0:
    base.export_to_csv(comments_df, "comments_analysis.csv")

# Phase 4: Analysis
print("\nPhase 4: Quick analysis...")

print(f"\nCollection Summary:")
print(f"  Total models: {len(df)}")
print(f"  Total comments: {len(comments_df)}")
print(f"  Unique creators: {df['user_username'].nunique()}")
print(f"  Date range: {df['publishedAt'].min()} to {df['publishedAt'].max()}")

print(f"\nLicensing:")
print(df['license_label'].value_counts())

print(f"\nEngagement:")
print(f"  Total views: {df['viewCount'].sum():,}")
print(f"  Total likes: {df['likeCount'].sum():,}")
print(f"  Average views per model: {df['viewCount'].mean():.0f}")

print(f"\nMost common tags:")
print(df['tags'].str.split(', ').explode().value_counts().head(10))

print("\nData collection complete!")
```

## Contributing

This is a research tool. Contributions welcome:
- Better rate limit handling strategies
- Additional analysis utilities
- Documentation improvements
- Bug fixes

## License

[Add your license here]

## Citation

If you use this tool in your research, please cite:

[Add citation information]

## Support

For issues or questions:
- Check the documentation files (especially DEALING_WITH_RATE_LIMITS.md)
- Review the log file (`sketchfab_scraper.log`)
- Check the Sketchfab API documentation: https://docs.sketchfab.com/data-api/v3/

## Maintainer

Research Team

**Status**: Active Development
