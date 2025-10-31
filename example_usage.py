#!/usr/bin/env python3
"""
Example Usage of Sketchfab Cultural Heritage Scraper

This script demonstrates basic usage patterns for retrieving
and analyzing cultural heritage models from Sketchfab.

Run this script to see example output:
    python example_usage.py
"""

from sketchfab_scraper import SketchfabScraper, quick_search
import pandas as pd


def example_1_basic_search():
    """Example 1: Basic cultural heritage search"""
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Cultural Heritage Search")
    print("="*70)

    # Quick search using convenience function
    df = quick_search("roman temple", cultural_heritage=True, max_results=10)

    print(f"\nFound {len(df)} Roman temple models")
    print("\nTop 5 results:")
    print(df[['name', 'user_username', 'viewCount', 'likeCount']].head())


def example_2_advanced_search():
    """Example 2: Advanced search with filters"""
    print("\n" + "="*70)
    print("EXAMPLE 2: Advanced Search with Filters")
    print("="*70)

    # Initialize scraper
    scraper = SketchfabScraper(rate_limit_delay=1.5)

    # Advanced search with multiple filters
    models = scraper.search_models(
        query="ancient pottery",
        categories='cultural-heritage-history',
        downloadable=True,
        sort_by='-likeCount',
        max_results=10
    )

    df = scraper.to_dataframe(models)

    print(f"\nFound {len(df)} downloadable ancient pottery models")
    print("\nMost liked models:")
    print(df[['name', 'likeCount', 'isDownloadable', 'license_label']].head())


def example_3_discourse_analysis():
    """Example 3: Discourse analysis on descriptions"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Discourse Analysis")
    print("="*70)

    scraper = SketchfabScraper(rate_limit_delay=1.5)

    # Search for archaeology models
    df = scraper.search_cultural_heritage(
        query="archaeology",
        max_results=50
    )

    print(f"\nAnalyzing {len(df)} archaeology models...")

    # Analyze discourse themes
    discourse_keywords = {
        'preservation': ['preserv', 'conserv', 'restor', 'protect'],
        'authenticity': ['authentic', 'original', 'genuine', 'real'],
        'education': ['educat', 'learn', 'teach', 'research', 'study'],
        'technology': ['scan', 'photogrammetry', 'laser', 'digital', '3d']
    }

    print("\nDiscourse themes in model descriptions:")
    descriptions = df['description'].fillna('').str.lower()

    for theme, keywords in discourse_keywords.items():
        count = descriptions.str.contains('|'.join(keywords), regex=True).sum()
        percentage = (count / len(df)) * 100
        print(f"  {theme:15s}: {count:3d} models ({percentage:5.1f}%)")


def example_4_tag_analysis():
    """Example 4: Tag analysis"""
    print("\n" + "="*70)
    print("EXAMPLE 4: Tag Analysis")
    print("="*70)

    scraper = SketchfabScraper(rate_limit_delay=1.5)

    # Search for heritage models
    df = scraper.search_cultural_heritage(
        query="heritage",
        max_results=50
    )

    # Analyze tags
    all_tags = df['tags'].str.split(', ').explode()
    tag_counts = all_tags.value_counts().head(15)

    print(f"\nTop 15 tags in {len(df)} heritage models:")
    print(tag_counts.to_string())


def example_5_export_data():
    """Example 5: Export data to CSV"""
    print("\n" + "="*70)
    print("EXAMPLE 5: Export Data")
    print("="*70)

    scraper = SketchfabScraper(rate_limit_delay=1.5)

    # Search for medieval models
    df = scraper.search_cultural_heritage(
        query="medieval",
        max_results=25
    )

    # Export to CSV
    filename = 'example_medieval_models.csv'
    scraper.export_to_csv(df, filename)

    print(f"\nExported {len(df)} models to '{filename}'")
    print("\nColumns in exported file:")
    print(", ".join(df.columns.tolist()))


def example_6_license_analysis():
    """Example 6: License distribution analysis"""
    print("\n" + "="*70)
    print("EXAMPLE 6: License Analysis")
    print("="*70)

    scraper = SketchfabScraper(rate_limit_delay=1.5)

    # Search for cultural heritage models
    df = scraper.search_cultural_heritage(
        query="ancient",
        max_results=50
    )

    # Analyze licenses
    license_dist = df['license_label'].value_counts()

    print(f"\nLicense distribution in {len(df)} ancient models:")
    print(license_dist.to_string())

    # Count open licenses
    open_licenses = ['CC Attribution', 'CC Attribution-ShareAlike',
                    'CC0 (Public Domain)']
    open_count = df['license_label'].isin(open_licenses).sum()
    open_percentage = (open_count / len(df)) * 100

    print(f"\nOpen licenses: {open_count} models ({open_percentage:.1f}%)")


def example_7_time_analysis():
    """Example 7: Temporal analysis of publications"""
    print("\n" + "="*70)
    print("EXAMPLE 7: Temporal Analysis")
    print("="*70)

    scraper = SketchfabScraper(rate_limit_delay=1.5)

    # Search for cultural heritage models
    df = scraper.search_cultural_heritage(
        query="",  # All cultural heritage
        max_results=100,
        sort_by='-publishedAt'  # Most recent first
    )

    # Convert to datetime
    df['publishedAt'] = pd.to_datetime(df['publishedAt'])
    df['year'] = df['publishedAt'].dt.year

    # Count by year
    yearly_counts = df['year'].value_counts().sort_index()

    print(f"\nCultural heritage models by year (last {len(df)} models):")
    print(yearly_counts.to_string())


def main():
    """Run all examples"""
    print("\n" + "="*70)
    print("SKETCHFAB CULTURAL HERITAGE SCRAPER - EXAMPLE USAGE")
    print("="*70)
    print("\nThis script demonstrates various usage patterns.")
    print("Note: API requests are rate-limited for polite scraping.")
    print("This may take a few minutes to complete...\n")

    try:
        example_1_basic_search()
        example_2_advanced_search()
        example_3_discourse_analysis()
        example_4_tag_analysis()
        example_5_export_data()
        example_6_license_analysis()
        example_7_time_analysis()

        print("\n" + "="*70)
        print("All examples completed successfully!")
        print("="*70)
        print("\nNext steps:")
        print("  1. Modify these examples for your research needs")
        print("  2. Use the Jupyter notebook for interactive analysis")
        print("  3. Check the README for more advanced usage patterns")
        print()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("  1. Check your internet connection")
        print("  2. Verify Sketchfab API is accessible")
        print("  3. Try increasing rate_limit_delay if getting 429 errors")
        print("  4. Consider using an API token for higher limits")


if __name__ == "__main__":
    main()
