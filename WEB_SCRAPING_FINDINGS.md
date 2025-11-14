# Web Scraping Findings for Sketchfab

## Issue Discovered

When attempting to scrape Sketchfab search results pages directly, the server returns:
- **HTTP Status: 403 Forbidden**
- **Response: "Access denied"**

## What This Means

Sketchfab is actively blocking web scraping attempts. This is likely because:

1. **Bot Detection**: They detect automated requests even with standard browser User-Agent headers
2. **Rate Limiting/Protection**: Cloudflare or similar service protecting their site
3. **Terms of Service**: They want users to use their official API instead

## Implications

### Why the Web Scraper Doesn't Work
- The HTML page is never returned, so BeautifulSoup has nothing to parse
- No amount of adjusting selectors will help - we're blocked at the HTTP level
- This is by design on Sketchfab's side

### Potential Workarounds (Not Recommended)

1. **Browser Automation (Selenium/Playwright)**
   - Could potentially bypass detection
   - Much slower (needs full browser)
   - High resource usage
   - **Likely violates Sketchfab's Terms of Service**

2. **Rotating Proxies/IPs**
   - Could evade IP-based blocking
   - Expensive and complex
   - **Definitely violates Terms of Service**

3. **Reverse Engineering JavaScript API Calls**
   - Find the internal API endpoints the website uses
   - Would require inspecting browser network requests
   - **May violate Terms of Service**
   - Endpoints likely change without notice

## Recommended Approach

### Use the Official API (Already Implemented!)

**You already have a comprehensive API scraper** (`sketchfab_scraper.py`) that:
- ✅ Works perfectly and is officially supported
- ✅ Collects 85+ fields of structured data
- ✅ Includes pagination, comments, all metadata
- ✅ Respects rate limits properly
- ✅ Complies with Sketchfab's Terms of Service
- ✅ More reliable and maintainable

**The API provides MORE data than web scraping would:**
- Complete model metadata
- User information
- License details
- Archive information with texture resolutions
- Organization data
- Comments
- Processing status
- And much more!

## What About Descriptive Text?

The API already provides all the descriptive text you need:
- `description` field - Full model description
- `name` field - Model title
- `tags` - All tags with names
- `categories` - Category names
- `comments` - All comment text
- `user.displayName` - Creator names
- `license.label` - License descriptions

## Conclusion

**Recommendation: Remove the web scraper and use only the API scraper.**

The web scraper:
- Doesn't work (403 blocked)
- Would violate Terms of Service to circumvent
- Provides less data than the API
- Is slower and less reliable
- Requires more maintenance

The API scraper:
- Already implemented and working
- Officially supported
- More comprehensive data
- Faster and more reliable
- ToS compliant

## Next Steps

1. **Focus on API scraper** - It already does everything you need
2. **Use comprehensive mode** - `include_full_details=True` and `include_comments=True`
3. **Export to JSON** - `export_complete_data_to_json()` preserves all text
4. **Text analysis** - Extract `description`, `tags`, `comments` fields for discourse analysis

## Example: Collecting All Descriptive Text via API

```python
from sketchfab_scraper import SketchfabScraper

scraper = SketchfabScraper(rate_limit_delay=1.5)

# Search and get complete data
models = scraper.search_models(
    query="roman",
    categories="cultural-heritage-history",
    max_results=1000
)

# Enrich with full details and comments
enriched = scraper.enrich_search_results(
    models,
    include_full_details=True,
    include_comments=True
)

# Save complete JSON with all text
scraper.export_complete_data_to_json(enriched, "roman_complete_data.json")

# Each model now has:
# - model['description'] - full description text
# - model['name'] - title
# - model['tags'] - list of tag objects with names
# - model['comments'] - list of all comments with text
# - model['user']['displayName'] - creator name
# And 80+ other fields!
```

This gives you **everything** for discourse analysis, and it's the proper way to use Sketchfab's platform.
