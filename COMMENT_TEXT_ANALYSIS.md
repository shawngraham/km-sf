# Comment Extraction for Text Analysis

## Quick Start - Three Easy Methods

### Method 1: One-Line Solution (Easiest!)

```python
from sketchfab_scraper import SketchfabScraper

scraper = SketchfabScraper()

# Search and extract comments in one call
models_df, comments_df = scraper.search_and_extract_comments(
    query="roman architecture",
    max_results=50
)

# Now you have two DataFrames:
print(f"Models: {len(models_df)}")
print(f"Comments: {len(comments_df)}")

# Export for text analysis
comments_df.to_csv('comments_for_analysis.csv', index=False)
```

**Output DataFrame has these columns:**
- `model_uid` - Links back to the model
- `model_name` - Name of the model
- `body` - Comment text (THIS IS WHAT YOU ANALYZE!)
- `author_username` - Who wrote it
- `createdAt` - When it was written
- `uid` - Unique comment ID
- `htmlBody` - HTML version of comment
- `parentUid` - Parent comment (for replies)
- `author_*` - Full author details

### Method 2: Extract from Existing Enriched Data

If you already enriched your models:

```python
scraper = SketchfabScraper()

# Your existing code
df = scraper.search_cultural_heritage(
    "ancient egypt",
    max_results=50,
    include_comments=True
)

# But BEFORE that became a DataFrame, get the enriched models:
models = scraper.search_models(
    query="ancient egypt",
    categories='cultural-heritage-history',
    max_results=50
)

enriched = scraper.enrich_search_results(
    models,
    include_comments=True
)

# Now extract comments
comments_df = scraper.extract_comments_from_models(enriched)

# Export
comments_df.to_csv('comments.csv', index=False)
```

### Method 3: Add Extra Model Context

Include additional model fields with each comment:

```python
scraper = SketchfabScraper()

models = scraper.search_models(
    query="pompeii",
    categories='cultural-heritage-history',
    max_results=50
)

enriched = scraper.enrich_search_results(
    models,
    include_comments=True
)

# Extract comments WITH additional model context
comments_df = scraper.extract_comments_from_models(
    enriched,
    include_model_fields=[
        'viewCount',       # How popular is the model?
        'likeCount',       # How many likes?
        'faceCount',       # Model complexity
        'user.username',   # Model author (nested field)
        'publishedAt'      # When was model published?
    ]
)

# Now each comment has model context!
print(comments_df.columns.tolist())
# Includes: model_viewCount, model_likeCount, model_faceCount, etc.

comments_df.to_csv('comments_with_context.csv', index=False)
```

## Complete Workflow Example

```python
from sketchfab_scraper import SketchfabScraper
import pandas as pd

# Initialize
scraper = SketchfabScraper(rate_limit_delay=1.5)

# Search and extract comments
models_df, comments_df = scraper.search_and_extract_comments(
    query="roman temple",
    max_results=100,
    include_model_fields=['viewCount', 'likeCount', 'user.username']
)

print("="*70)
print("DATA COLLECTED")
print("="*70)
print(f"\nModels: {len(models_df)}")
print(f"Models with comments: {models_df['has_fetched_comments'].sum()}")
print(f"Total comments: {len(comments_df)}")
print(f"Unique commenters: {comments_df['author_username'].nunique()}")

# View sample
print("\nSample comments:")
print(comments_df[['model_name', 'author_username', 'body']].head())

# Export both
models_df.to_csv('models.csv', index=False)
comments_df.to_csv('comments_for_text_analysis.csv', index=False)

print("\nExported to:")
print("  - models.csv")
print("  - comments_for_text_analysis.csv")
```

## Text Analysis Ready Format

The `comments_df` DataFrame is ready for text analysis:

```python
# Basic text analysis
print("\nComment Statistics:")
print(f"  Average length: {comments_df['body'].str.len().mean():.0f} chars")
print(f"  Shortest: {comments_df['body'].str.len().min()}")
print(f"  Longest: {comments_df['body'].str.len().max()}")

# Most active commenters
print("\nTop commenters:")
print(comments_df['author_username'].value_counts().head(10))

# Comment frequency over time
comments_df['date'] = pd.to_datetime(comments_df['createdAt'])
comments_df['year_month'] = comments_df['date'].dt.to_period('M')
print("\nComments by month:")
print(comments_df['year_month'].value_counts().sort_index().tail(12))

# Model with most comments
print("\nModels with most comments:")
print(comments_df.groupby('model_name').size().sort_values(ascending=False).head(10))
```

## Integration with Text Analysis Tools

### Sentiment Analysis
```python
# Using VADER or TextBlob
from textblob import TextBlob

comments_df['sentiment'] = comments_df['body'].apply(
    lambda x: TextBlob(x).sentiment.polarity
)

print("Average sentiment:", comments_df['sentiment'].mean())

# Positive vs negative comments
positive = comments_df[comments_df['sentiment'] > 0.1]
negative = comments_df[comments_df['sentiment'] < -0.1]

print(f"Positive comments: {len(positive)}")
print(f"Negative comments: {len(negative)}")
```

### Topic Modeling
```python
# Using sklearn or gensim
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation

# Prepare text
texts = comments_df['body'].tolist()

# TF-IDF
vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
X = vectorizer.fit_transform(texts)

# LDA topic modeling
lda = LatentDirichletAllocation(n_components=5, random_state=42)
topics = lda.fit_transform(X)

# Add topic to DataFrame
comments_df['primary_topic'] = topics.argmax(axis=1)
```

### Word Cloud
```python
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# All comments as one text
all_text = ' '.join(comments_df['body'].tolist())

# Generate word cloud
wordcloud = WordCloud(width=800, height=400, background_color='white').generate(all_text)

plt.figure(figsize=(12, 6))
plt.imshow(wordcloud, interpolation='bilinear')
plt.axis('off')
plt.title('Comment Word Cloud')
plt.savefig('comment_wordcloud.png')
```

## Advanced: Retrieve Comments for Specific Models

If you only want comments from certain models:

```python
# Get models of interest
models_df = scraper.search_cultural_heritage("pompeii", max_results=100)

# Filter to high-engagement models
high_engagement = models_df[models_df['commentCount'] > 5]

print(f"High-engagement models: {len(high_engagement)}")

# Get comments for these specific models
all_comments = []
for _, model in high_engagement.iterrows():
    uid = model['uid']
    name = model['name']
    
    comments = scraper.get_model_comments(uid)
    
    for comment in comments:
        comment['model_uid'] = uid
        comment['model_name'] = name
        comment['model_viewCount'] = model['viewCount']
        comment['model_likeCount'] = model['likeCount']
    
    all_comments.extend(comments)

comments_df = scraper.comments_to_dataframe(all_comments)
```

## Working with Existing Data

If you already have a DataFrame with `has_fetched_comments`:

```python
# You already have this
df = scraper.search_cultural_heritage("roman", max_results=50, include_comments=True)

# Get UIDs of models with comments
model_uids = df[df['has_fetched_comments'] == True]['uid'].tolist()

# Re-fetch comments (quick since you know which ones have comments)
all_comments = []
for uid in model_uids:
    model_name = df[df['uid'] == uid]['name'].values[0]
    
    comments = scraper.get_model_comments(uid)
    
    for comment in comments:
        comment['model_uid'] = uid
        comment['model_name'] = model_name
    
    all_comments.extend(comments)

comments_df = scraper.comments_to_dataframe(all_comments)
comments_df.to_csv('comments.csv', index=False)
```

## CSV Output Format

The exported CSV has this structure:

| Column | Type | Description |
|--------|------|-------------|
| `model_uid` | string | Model unique ID (for joining) |
| `model_name` | string | Model name |
| `body` | string | **Comment text - analyze this!** |
| `author_username` | string | Commenter username |
| `author_displayName` | string | Commenter display name |
| `createdAt` | datetime | Comment timestamp |
| `uid` | string | Comment unique ID |
| `parentUid` | string | Parent comment (for thread analysis) |
| `htmlBody` | string | HTML formatted comment |
| `author_uid` | string | Author unique ID |
| `author_profileUrl` | string | Author profile link |

Plus any additional `model_*` fields you requested.

## Best Practices

1. **Use Method 1** (`search_and_extract_comments`) for simplicity
2. **Include model fields** to understand comment context
3. **Export to CSV** for analysis in Excel, R, Python, etc.
4. **Handle missing data** - not all models have comments
5. **Rate limiting** - Use appropriate delays for large datasets
6. **Filter before fetching** - Only get comments for relevant models

## Common Analyses

### Engagement Analysis
```python
# Which models generate most discussion?
engagement = comments_df.groupby(['model_uid', 'model_name']).agg({
    'body': 'count',
    'author_username': 'nunique'
}).rename(columns={'body': 'comment_count', 'author_username': 'unique_commenters'})

print(engagement.sort_values('comment_count', ascending=False).head())
```

### Temporal Analysis
```python
# How do comments change over time?
comments_df['date'] = pd.to_datetime(comments_df['createdAt'])
comments_df['hour'] = comments_df['date'].dt.hour
comments_df['day_of_week'] = comments_df['date'].dt.day_name()

print("Comments by hour of day:")
print(comments_df['hour'].value_counts().sort_index())
```

### User Analysis
```python
# Who are the power users?
power_users = comments_df.groupby('author_username').agg({
    'body': 'count',
    'model_uid': 'nunique'
}).rename(columns={'body': 'total_comments', 'model_uid': 'models_commented_on'})

print(power_users.sort_values('total_comments', ascending=False).head())
```

## Performance Notes

- **Basic search**: ~1 second per 24 models
- **With comments**: +1-3 seconds per model with comments
- **For 50 models**: ~2-5 minutes if 20 have comments
- **Recommendation**: Start with max_results=20 to test


## Quick Reference

```python
# One-liner to get comments ready for analysis
models_df, comments_df = scraper.search_and_extract_comments(
    "roman temple", 
    max_results=50
)

# Export
comments_df.to_csv('comments.csv', index=False)

# Analyze
print(comments_df['body'])  # This is what you analyze!
```
