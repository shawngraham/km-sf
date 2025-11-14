#!/usr/bin/env python3
"""
Field Discovery Test - Shows ALL available fields from the API

This script demonstrates:
1. Which fields come from basic search
2. Which fields require full details enrichment
3. Which fields are conditional (only when data exists)
4. How to access comments (separate endpoint)
"""

from sketchfab_scraper import SketchfabScraper
import pandas as pd

def test_basic_search():
    """Test 1: Basic search - what fields are available?"""
    print("\n" + "="*70)
    print("TEST 1: Basic Search Fields")
    print("="*70)
    
    scraper = SketchfabScraper(rate_limit_delay=1.0)
    
    df = scraper.search_cultural_heritage("roman", max_results=5)
    
    print(f"\nBasic search returned {len(df.columns)} fields:")
    print(df.columns.tolist())
    
    # Check for key field categories
    print(f"\n Field Categories Present:")
    print(f"  Core fields: YES")
    print(f"  User fields: {'YES' if 'user_username' in df.columns else 'NO'}")
    print(f"  License fields: {'YES' if 'license_label' in df.columns else 'NO'}")
    print(f"  Archive fields: {'YES' if 'archive_gltf_size' in df.columns else 'NO'}")
    print(f"  Org fields: {'YES' if 'org_uid' in df.columns else 'NO'}")
    print(f"  Comments: {'YES' if 'has_fetched_comments' in df.columns else 'NO (separate endpoint)'}")
    
    return df


def test_with_enrichment():
    """Test 2: Search with full details enrichment"""
    print("\n" + "="*70)
    print("TEST 2: Search with Full Details Enrichment")
    print("="*70)
    
    scraper = SketchfabScraper(rate_limit_delay=1.5)
    
    df = scraper.search_cultural_heritage(
        "roman temple",
        max_results=3,
        include_full_details=True  # This fetches full details for each model
    )
    
    print(f"\nEnriched search returned {len(df.columns)} fields:")
    print(df.columns.tolist())
    
    print(f"\nField Categories Present:")
    print(f"  Core fields: YES")
    print(f"  User fields: {'YES' if 'user_username' in df.columns else 'NO'}")
    print(f"  License fields: {'YES' if 'license_label' in df.columns else 'NO'}")
    print(f"  Archive fields: {'YES' if 'archive_gltf_size' in df.columns else 'NO'}")
    print(f"  Status fields: {'YES' if 'status_processing' in df.columns else 'NO'}")
    print(f"  Options fields: {'YES' if 'options_shadeless' in df.columns else 'NO'}")
    print(f"  Collection fields: {'YES' if 'collection_count' in df.columns else 'NO'}")
    
    return df


def test_comments_separate():
    """Test 3: Comments are accessed separately"""
    print("\n" + "="*70)
    print("TEST 3: Comments (Separate Endpoint)")
    print("="*70)
    
    scraper = SketchfabScraper(rate_limit_delay=1.5)
    
    # First get a model
    df = scraper.search_cultural_heritage("ancient egypt", max_results=1)
    
    if len(df) > 0:
        model_uid = df.iloc[0]['uid']
        model_name = df.iloc[0]['name']
        
        print(f"\nFetching comments for: {model_name}")
        print(f"Model UID: {model_uid}")
        
        # Get comments separately
        comments = scraper.get_model_comments(model_uid)
        
        print(f"\nFound {len(comments)} comments")
        
        if comments:
            # Convert to DataFrame
            comments_df = scraper.comments_to_dataframe(comments)
            
            print(f"\nComment fields:")
            print(comments_df.columns.tolist())
            
            print(f"\nSample comment:")
            if len(comments_df) > 0:
                sample = comments_df.iloc[0]
                print(f"  Author: {sample['author_username']}")
                print(f"  Date: {sample['createdAt']}")
                print(f"  Text: {sample['body'][:100]}...")
            
            return comments_df
        else:
            print("  No comments found on this model.")
    else:
        print("No models found.")
    
    return None


def test_with_comments_enrichment():
    """Test 4: Auto-enrich with comments"""
    print("\n" + "="*70)
    print("TEST 4: Auto-Enrichment with Comments")
    print("="*70)
    
    scraper = SketchfabScraper(rate_limit_delay=2.0)
    
    print("\nSearching and enriching with comments...")
    print("(This is slow - fetches details + comments for each model)")
    
    df = scraper.search_cultural_heritage(
        "pompeii",
        max_results=2,
        include_full_details=True,
        include_comments=True  # This adds comments!
    )
    
    print(f"\nFully enriched DataFrame has {len(df.columns)} fields:")
    
    # Check for comment-related fields
    has_comment_fields = 'has_fetched_comments' in df.columns
    
    print(f"\nComment fields added: {'YES' if has_comment_fields else 'NO'}")
    
    if has_comment_fields:
        print(f"\nComment summary:")
        print(f"  Models with comments: {df['has_fetched_comments'].sum()}")
        print(f"  Total comments fetched: {df['fetched_comment_count'].sum()}")
        
        # Show which models have comments
        models_with_comments = df[df['has_fetched_comments']]
        for _, model in models_with_comments.iterrows():
            print(f"    - {model['name']}: {model['fetched_comment_count']} comments")
    
    return df


def test_actual_model_details():
    """Test 5: Direct model details call"""
    print("\n" + "="*70)
    print("TEST 5: Direct Model Details Call")
    print("="*70)
    
    scraper = SketchfabScraper(rate_limit_delay=1.0)
    
    # Get a model
    df = scraper.search_cultural_heritage("roman", max_results=1)
    
    if len(df) > 0:
        model_uid = df.iloc[0]['uid']
        model_name = df.iloc[0]['name']
        
        print(f"\nFetching full details for: {model_name}")
        
        # Get raw model details (not flattened)
        model_details = scraper.get_model_details(model_uid)
        
        print(f"\nRaw API response has these top-level keys:")
        print(list(model_details.keys()))
        
        print(f"\nNested objects:")
        for key, value in model_details.items():
            if isinstance(value, dict):
                print(f"  {key}: {list(value.keys())[:5]}...")
            elif isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                print(f"  {key}: array of {len(value)} objects")
        
        return model_details
    
    return None


def test_conditional_fields():
    """Test 6: Which fields are conditional?"""
    print("\n" + "="*70)
    print("TEST 6: Conditional Fields Analysis")
    print("="*70)
    
    scraper = SketchfabScraper(rate_limit_delay=1.5)
    
    df = scraper.search_cultural_heritage(
        "heritage",
        max_results=20,
        include_full_details=True
    )
    
    print(f"\nAnalyzing {len(df)} models for field presence...")
    
    # Check conditional fields
    conditional_checks = {
        'License': 'license_label',
        'Organization': 'org_uid',
        'Collections': 'collection_count',
        'Options': 'options_shadeless',
        'Status': 'status_processing',
        'Staff Picked': 'staffpickedAt',
        'Price': 'price',
        'GLTF Archive': 'archive_gltf_size',
        'Source Archive': 'archive_source_size',
    }
    
    print(f"\nField presence analysis:")
    for field_name, column_name in conditional_checks.items():
        if column_name in df.columns:
            non_null = df[column_name].notna().sum()
            pct = (non_null / len(df)) * 100
            print(f"  {field_name:20s}: {non_null:2d}/{len(df)} models ({pct:.0f}%) have this field")
        else:
            print(f"  {field_name:20s}: Column not present")
    
    return df


def main():
    """Run all tests"""
    print("\n" + "═"*70)
    print(" COMPREHENSIVE FIELD DISCOVERY TEST")
    print("═"*70)
    print("\nThis script will show you:")
    print("  1. What fields come from basic search")
    print("  2. What fields need enrichment")
    print("  3. How to access comments (separate endpoint)")
    print("  4. Which fields are conditional")
    
    input("\nPress Enter to start tests...")
    
    try:
        # Run tests
        print("\n" + "─"*70)
        basic_df = test_basic_search()
        
        print("\n" + "─"*70)
        enriched_df = test_with_enrichment()
        
        print("\n" + "─"*70)
        comments_df = test_comments_separate()
        
        print("\n" + "─"*70)
        model_details = test_actual_model_details()
        
        print("\n" + "─"*70)
        conditional_df = test_conditional_fields()
        
        # Ask about expensive test
        print("\n" + "─"*70)
        response = input("\nRun Test 4 (auto-enrichment with comments)? This is slow. (y/n): ")
        
        if response.lower() == 'y':
            enriched_with_comments_df = test_with_comments_enrichment()
        
        # Summary
        print("\n" + "═"*70)
        print(" SUMMARY")
        print("═"*70)
        print("\nKey Findings:")
        print("  • Comments are accessed via SEPARATE endpoint")
        print("  • Basic search gives ~45 fields")
        print("  • Full enrichment gives 85+ fields")
        print("  • Many fields are conditional (only when data exists)")
        print("  • License, org, collections, options require specific data")
        print("\nTo get ALL fields:")
        print("  1. Use include_full_details=True for model fields")
        print("  2. Use include_comments=True for comments")
        print("  3. Or use get_model_comments(uid) separately")
        
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user.")
    except Exception as e:
        print(f"\n\nError during tests: {e}")
        raise


if __name__ == "__main__":
    main()
