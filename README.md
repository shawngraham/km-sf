# Sketchfab Cultural Heritage API Scraper

A polite, research-focused Python tool for retrieving cultural heritage 3D model data from the Sketchfab Data API v3. Designed for discourse analysis and scholarly examination of how modelers represent and describe cultural heritage in digital 3D spaces.

## Purpose

This tool enables researchers to:
- Retrieve cultural heritage model metadata from Sketchfab
- Analyze discourse patterns in model descriptions and tags
- Study licensing practices in digital cultural heritage
- Examine engagement patterns with cultural heritage content
- Export data in tabular format (pandas DataFrame/CSV) for further analysis

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/km-sf.git
cd km-sf

# Install dependencies if you are running on your own machine with eg jupyter;
# if you don't want to use jupyter, comment those lines out of requirements.txt first
pip install -r requirements.txt
```

### Basic Usage

```python
from sketchfab_scraper import SketchfabScraper

# Initialize
scraper = SketchfabScraper()

# Search cultural heritage models
df = scraper.search_cultural_heritage("roman temple", max_results=50)

# View results
print(df[['name', 'user_username', 'viewCount', 'faceCount', 'license_label']])
```

### Get Comments

```python
# Get comments for a model
comments = scraper.get_model_comments(model_uid='abc123')

# Convert to DataFrame
comments_df = scraper.comments_to_dataframe(comments)
```

### Get Complete Data

```python
# Full details + comments for one model
complete_data = scraper.get_complete_model_data(
    model_uid='abc123',
    include_comments=True
)

# Search with auto-enrichment
df = scraper.search_cultural_heritage(
    query="ancient egypt",
    max_results=20,
    include_full_details=True,  # Get ALL 85+ fields
    include_comments=True       # Include comments too
)
```

## What Data Is Available?

### Core Model Information (Always Available)
- Identification: uid, name, description, uri, viewerUrl, embedUrl
- Metrics: viewCount, likeCount, commentCount, downloadCount
- Geometry: faceCount, vertexCount, materialCount, textureCount
- Media: animationCount, soundCount
- Dates: publishedAt, createdAt, updatedAt, staffpickedAt
- Flags: isDownloadable, isProtected, isPublished, isAgeRestricted

### User & Author Data
- User profile: username, displayName, account type
- Avatar images
- Profile and URI links

### License Information
- License type: label, slug, fullName
- Requirements and restrictions
- License URL

### Technical Specifications
- **PBR type**: metalness, specular, or non-PBR
- **Processing status**: current state and errors
- **Archive readiness**: whether downloads are available
- Categories and tags
- Collections membership

### Archive Data (Per Format: gltf, glb, usdz, source)
- File size in bytes
- Face and vertex counts
- Texture count
- **Texture maximum resolution** ← Critical new field!

### Organization Data (For Institutional Models)
- Organization: uid, username, displayName
- Project affiliation
- Organization-specific tags
- Visibility settings
- Download types

### Comments (When Requested)
- Comment text (plain and HTML)
- Comment authors
- Timestamps
- Thread structure (replies)

## Common Use Cases

### 1. Quick Model Discovery
```python
df = scraper.search_cultural_heritage("archaeology", max_results=100)
```

### 2. Download Planning (with Texture Resolution)
```python
df = scraper.search_cultural_heritage(
    "museum scan",
    max_results=50,
    downloadable=True,
    archives_flavours=True  # Get texture resolution!
)

# Analyze texture quality
print(df[['name', 'archive_gltf_textureMaxResolution', 'archive_gltf_size']])
```

### 3. PBR Workflow Analysis
```python
df = scraper.search_cultural_heritage("3d scan", max_results=200)
pbr_breakdown = df['pbrType'].value_counts()
print(pbr_breakdown)
```

### 4. Community Engagement Study
```python
models = scraper.search_models("roman architecture", max_results=20)

all_comments = []
for model in models:
    comments = scraper.get_model_comments(model['uid'])
    for comment in comments:
        comment['model_name'] = model['name']
    all_comments.extend(comments)

comments_df = scraper.comments_to_dataframe(all_comments)
```

### 5. Organizational Research
```python
df = scraper.search_cultural_heritage("heritage")
org_models = df[df['org_uid'].notna()]
print(f"Institutional models: {len(org_models)}")
print(org_models.groupby('org_displayName').size())
```

This scraper should capture **ALL** fields documented in the [Swagger API](https://docs.sketchfab.com/data-api/v3/index.html),

## API Token (Optional)

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




**Maintainer**: Research Team
**Status**: Active Development
