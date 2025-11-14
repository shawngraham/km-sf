#!/usr/bin/env python3
"""
Example: Using the Sketchfab Web Scraper

This script demonstrates how to use the web scraper to collect
metadata from Sketchfab search results pages.
"""

from sketchfab_web_scraper import SketchfabWebScraper
from datetime import datetime
import json


def example_basic_scrape():
    """
    Example 1: Basic web scraping of search results
    """
    print("=" * 70)
    print("EXAMPLE 1: Basic Web Scraping")
    print("=" * 70)

    # Initialize scraper with polite rate limiting
    scraper = SketchfabWebScraper(rate_limit_delay=2.0)

    # Scrape search results for "roman"
    print("\nScraping search results for 'roman'...")
    print("Limiting to 2 pages for demonstration purposes\n")

    models = scraper.scrape_search(
        query="roman",
        max_pages=2,  # Limit for testing
        max_models=None
    )

    print(f"\n✓ Collected {len(models)} models")

    # Show sample data
    if models:
        print("\nSample model data:")
        print("-" * 70)
        sample = models[0]
        print(f"Title: {sample.get('title', 'N/A')}")
        print(f"Author: {sample.get('author', 'N/A')}")
        print(f"URL: {sample.get('model_url', 'N/A')}")
        print(f"Description: {sample.get('description', 'N/A')[:100]}...")
        print(f"\nAll text fields collected: {len(sample.get('all_text', []))}")
        print("Text preview:", sample.get('all_text', [])[:5])

    # Save to JSON
    output_file = f"web_scrape_roman_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    scraper.save_to_json(models, output_file)

    print(f"\n✓ Data saved to: {output_file}")

    return models


def example_limited_models():
    """
    Example 2: Limit by number of models instead of pages
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Limit by Model Count")
    print("=" * 70)

    scraper = SketchfabWebScraper(rate_limit_delay=2.0)

    print("\nScraping up to 10 models about 'ancient egypt'...\n")

    models = scraper.scrape_search(
        query="ancient egypt",
        max_models=10  # Stop after collecting 10 models
    )

    print(f"\n✓ Collected {len(models)} models")

    # Analyze collected data
    if models:
        print("\nData Analysis:")
        print("-" * 70)

        # Count models with descriptions
        with_descriptions = sum(1 for m in models if m.get('description'))
        print(f"Models with descriptions: {with_descriptions}/{len(models)}")

        # Count models with stats
        with_stats = sum(1 for m in models if m.get('stats'))
        print(f"Models with statistics: {with_stats}/{len(models)}")

        # Show all authors
        authors = [m.get('author', 'Unknown') for m in models]
        unique_authors = len(set(authors))
        print(f"Unique authors: {unique_authors}")

    return models


def example_analyze_text():
    """
    Example 3: Analyze all collected text
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Text Analysis")
    print("=" * 70)

    scraper = SketchfabWebScraper(rate_limit_delay=2.0)

    print("\nScraping models about 'archaeological site'...\n")

    models = scraper.scrape_search(
        query="archaeological site",
        max_pages=1
    )

    print(f"\n✓ Collected {len(models)} models")

    if models:
        print("\nText Analysis:")
        print("-" * 70)

        # Aggregate all text
        all_text_pieces = []
        for model in models:
            all_text_pieces.extend(model.get('all_text', []))

        print(f"Total text pieces collected: {len(all_text_pieces)}")

        # Show some examples
        print("\nSample text pieces:")
        for i, text in enumerate(all_text_pieces[:10], 1):
            print(f"  {i}. {text[:60]}...")

        # Count total words
        total_words = sum(len(text.split()) for text in all_text_pieces)
        print(f"\nTotal words: {total_words}")
        print(f"Average words per model: {total_words / len(models):.1f}")

    return models


def example_save_and_load():
    """
    Example 4: Save and load scraped data
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Save and Load Data")
    print("=" * 70)

    scraper = SketchfabWebScraper(rate_limit_delay=2.0)

    # Use convenience method
    print("\nUsing convenience method scrape_and_save()...\n")

    output_file = "example_museum_models.json"

    models = scraper.scrape_and_save(
        query="museum",
        output_file=output_file,
        max_pages=1
    )

    print(f"\n✓ Collected and saved {len(models)} models")

    # Load it back
    print(f"\nLoading data from {output_file}...")
    with open(output_file, 'r', encoding='utf-8') as f:
        loaded_models = json.load(f)

    print(f"✓ Loaded {len(loaded_models)} models")

    # Verify data
    if loaded_models:
        print("\nData verification:")
        print(f"  First model title: {loaded_models[0].get('title', 'N/A')}")
        print(f"  Fields per model: {len(loaded_models[0])}")
        print(f"  Available fields: {list(loaded_models[0].keys())}")

    return loaded_models


def main():
    """Run all examples"""
    print("\n" + "═" * 70)
    print(" Sketchfab Web Scraper - Example Usage")
    print("═" * 70)

    print("\nThis script demonstrates the web scraper functionality.")
    print("It will make real HTTP requests to Sketchfab.")
    print("\nPlease use responsibly and respect rate limits!")

    print("\n⚠️  Note: Each example will take some time due to polite rate limiting.")

    response = input("\nRun examples? (y/n): ")

    if response.lower() != 'y':
        print("\nExiting. You can run individual examples by editing this file.")
        return

    try:
        # Run examples
        example_basic_scrape()
        example_limited_models()
        example_analyze_text()
        example_save_and_load()

        # Summary
        print("\n" + "═" * 70)
        print(" All Examples Complete!")
        print("═" * 70)

        print("\n✓ You now know how to:")
        print("  1. Scrape search results with pagination")
        print("  2. Limit by pages or model count")
        print("  3. Analyze collected text")
        print("  4. Save and load JSON data")

        print("\n💡 Next steps:")
        print("  - Combine with API scraper for comprehensive data")
        print("  - Analyze discourse patterns in descriptions")
        print("  - Compare web-visible data with API data")

    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user.")
    except Exception as e:
        print(f"\n\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
