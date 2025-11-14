# Dealing with Sketchfab's Opaque Rate Limits

Sketchfab's API has rate limits that are not well-documented. This guide helps you work around them effectively.

## The Problem

- Rate limits are **not publicly documented**
- Limits vary based on authentication status
- No clear indication of when you'll be allowed to request again
- Can get rate limited (429 errors) seemingly randomly
- Makes large-scale data collection difficult

## Solutions Implemented

### 1. Enhanced Scraper (`sketchfab_scraper_enhanced.py`)

**New features:**
- **Exponential backoff**: Automatically increases wait time after rate limits
- **Response header inspection**: Looks for rate limit info in responses
- **Progress checkpointing**: Saves your progress so you can resume
- **Transparent logging**: Shows exactly what's happening
- **Request statistics**: Track success/failure rates

### 2. Strategies for Large Collections

#### Strategy A: Use Conservative Delays
```python
from sketchfab_scraper_enhanced import EnhancedSketchfabScraper

# Start with longer delays
scraper = EnhancedSketchfabScraper(
    rate_limit_delay=3.0,  # 3 seconds between requests
    max_retries=5
)
```

**Adjust based on results:**
- If you rarely hit rate limits → reduce to 2.0s
- If you frequently hit rate limits → increase to 5.0s or more

#### Strategy B: Checkpoint and Resume
```python
scraper = EnhancedSketchfabScraper(
    rate_limit_delay=2.0,
    checkpoint_file="my_search.json"
)

try:
    results = scraper.search_models_with_checkpoints(
        query="roman",
        max_results=1000,
        checkpoint_every=100  # Save every 100 models
    )
except RateLimitError:
    print("Hit rate limit - checkpoint saved!")
    # Wait 1 hour, then resume from checkpoint
```

**Resume from checkpoint:**
```python
# Load previous progress
previous_data = scraper.load_checkpoint("my_search.json")
print(f"Resuming from {len(previous_data)} models")

# Continue collecting...
```

#### Strategy C: Collect in Batches

Instead of one massive collection, break it into smaller batches:

```python
queries = ["roman architecture", "roman sculpture", "roman coins", "roman pottery"]

for query in queries:
    print(f"\nCollecting: {query}")
    scraper = EnhancedSketchfabScraper(rate_limit_delay=3.0)

    try:
        results = scraper.search_models_with_checkpoints(
            query=query,
            categories="cultural-heritage-history",
            max_results=200,
            checkpoint_every=50
        )

        scraper.print_stats()

        # Save this batch
        with open(f"{query.replace(' ', '_')}.json", 'w') as f:
            json.dump(results, f)

        # Rest between batches
        print("Resting 5 minutes before next batch...")
        time.sleep(300)

    except RateLimitError:
        print(f"Rate limited on '{query}' - saved checkpoint")
        print("Resume this query later")
        continue
```

#### Strategy D: Use API Token

If you're not using one already, get an API token - authenticated requests often have higher limits.

```python
scraper = EnhancedSketchfabScraper(
    api_token="your_token_here",
    rate_limit_delay=2.0
)
```

Get token at: https://sketchfab.com/settings/password

#### Strategy E: Monitor and Adapt

Use the statistics to understand your rate limits:

```python
scraper = EnhancedSketchfabScraper(rate_limit_delay=2.0)

# After some requests
scraper.print_stats()

# Output:
# Total requests:    150
# Successful:        148
# Rate limited:      2
# Success rate:      98.7%
```

**If rate limited frequently (>5%):**
- Increase `rate_limit_delay`
- Reduce `max_results` per run
- Add longer rests between batches

**If rarely rate limited (<1%):**
- You can try reducing `rate_limit_delay` slightly
- Still use checkpoints as insurance

### 3. Example: Large-Scale Collection

Collecting 5000 models safely:

```python
from sketchfab_scraper_enhanced import EnhancedSketchfabScraper
import time
import json

def collect_large_dataset(query, target_count=5000):
    """Collect large dataset with rate limit handling."""

    scraper = EnhancedSketchfabScraper(
        api_token="your_token_here",  # USE TOKEN!
        rate_limit_delay=3.0,  # Conservative
        max_retries=5,
        checkpoint_file=f"checkpoint_{query.replace(' ', '_')}.json"
    )

    print(f"Collecting up to {target_count} models for: {query}")
    print("Using checkpointing - can resume if interrupted")
    print("=" * 70)

    try:
        # Try to load previous progress
        existing = scraper.load_checkpoint(scraper.checkpoint_file)
        if existing:
            print(f"Resuming from checkpoint: {len(existing)} models")
            remaining = target_count - len(existing)
        else:
            remaining = target_count

        # Collect data
        results = scraper.search_models_with_checkpoints(
            query=query,
            categories="cultural-heritage-history",
            max_results=remaining,
            checkpoint_every=100
        )

        # Merge with existing if resuming
        if existing:
            # Deduplicate by UID
            existing_uids = {m['uid'] for m in existing}
            new_results = [m for m in results if m['uid'] not in existing_uids]
            results = existing + new_results

        print(f"\nSUCCESS: Collected {len(results)} models")

        # Save final dataset
        final_path = f"final_{query.replace(' ', '_')}_{len(results)}_models.json"
        with open(final_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"Saved to: {final_path}")

        # Print statistics
        scraper.print_stats()

        return results

    except RateLimitError as e:
        print(f"\nRate limited: {e}")
        print("\nWhat to do:")
        print("1. Wait 1-2 hours")
        print("2. Run this script again (will resume from checkpoint)")
        print("3. Or increase rate_limit_delay and try again")
        scraper.print_stats()
        return None

    except KeyboardInterrupt:
        print("\n\nInterrupted - Progress saved in checkpoint")
        scraper.print_stats()
        return None

# Usage
if __name__ == "__main__":
    results = collect_large_dataset("roman", target_count=5000)

    if results:
        print(f"\nCollection complete!")
    else:
        print(f"\nPaused - resume later")
```

## Recommended Workflow

1. **Start conservative**: `rate_limit_delay=3.0`
2. **Use checkpointing**: Always set `checkpoint_file`
3. **Collect in batches**: Don't try to get 10,000 models at once
4. **Monitor statistics**: Check success rate
5. **Adjust as needed**: Increase delay if rate limited often
6. **Be patient**: Large collections may take hours/days

## Understanding Rate Limits

Based on community experience:

| Auth Status | Rough Limit | Per |
|-------------|-------------|-----|
| No token | ~60-100 | hour |
| With token | ~300-500 | hour |
| *Unofficial estimates* | | |

These are **estimates** - actual limits vary and change.

## Signs You're Being Rate Limited

- Getting 429 errors frequently
- Requests taking longer than usual
- Empty responses or timeouts
- Success rate below 90%

## What NOT to Do

- Do NOT set `rate_limit_delay` below 1.0s
- Do NOT disable retries
- Do NOT ignore checkpoints
- Do NOT try to parallelize requests
- Do NOT use multiple API tokens (likely ToS violation)

## What TO Do

- DO use the enhanced scraper
- DO start with conservative delays (3s+)
- DO always use checkpointing
- DO monitor statistics
- DO be patient
- DO use an API token
- DO collect during off-peak hours if possible

## Questions?

Check the logs! The enhanced scraper logs everything to:
- Console (INFO level)
- `sketchfab_scraper.log` file (DEBUG level)

Look for patterns in when rate limits occur.
