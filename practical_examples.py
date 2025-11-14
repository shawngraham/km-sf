#!/usr/bin/env python3
"""
Practical Examples: Sketchfab API Scraper

Demonstrates complete API data collection including:
- All 85+ model fields
- Comments extraction
- Texture resolution analysis
- PBR type identification
- Organization data
- Processing status tracking

Run with: python practical_examples.py
"""

from sketchfab_scraper import SketchfabScraper
import pandas as pd


def example_1_basic_search():
    """
    Example 1: Basic Search - Quick Model Discovery
    
    Speed: Fast (~5 seconds for 50 models)
    Fields: ~45 basic fields
    """
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Search")
    print("="*70)
    
    scraper = SketchfabScraper(rate_limit_delay=1.0)
    
    df = scraper.search_cultural_heritage(
        query="roman architecture",
        max_results=20,
        sort_by='-likeCount'
    )
    
    print(f"\nFound {len(df)} models")
    print("\nTop 5 by likes:")
    print(df[['name', 'user_username', 'viewCount', 'likeCount', 'faceCount']].head())
    
    print(f"\n Statistics:")
    print(f"  Average views: {df['viewCount'].mean():.0f}")
    print(f"  Average polygons: {df['faceCount'].mean():.0f}")
    print(f"  Downloadable: {df['isDownloadable'].sum()}")
    
    return df


def example_2_texture_resolution():
    """
    Example 2: Texture Resolution Analysis (NEW!)
    
    The textureMaxResolution field was missing from the original scraper.
    This is critical for download planning and quality assessment.
    """
    print("\n" + "="*70)
    print("EXAMPLE 2: Texture Resolution Analysis")
    print("="*70)
    
    scraper = SketchfabScraper(rate_limit_delay=1.0)
    
    df = scraper.search_cultural_heritage(
        query="3d scan museum",
        max_results=20,
        downloadable=True,
        archives_flavours=True  # CRITICAL: Gets texture resolution!
    )
    
    print(f"\nAnalyzed {len(df)} downloadable models")
    
    # Analyze GLTF archives
    gltf_models = df[df['archive_gltf_size'] > 0].copy()
    
    if len(gltf_models) > 0:
        print(f"\nGLTF Archive Analysis:")
        print(f"  Models with GLTF: {len(gltf_models)}")
        print(f"  Avg file size: {gltf_models['archive_gltf_size'].mean()/1e6:.1f} MB")
        print(f"  Avg texture resolution: {gltf_models['archive_gltf_textureMaxResolution'].mean():.0f}px")
        print(f"  Avg face count: {gltf_models['archive_gltf_faceCount'].mean():.0f}")
        
        print("\nResolution breakdown:")
        print(gltf_models['archive_gltf_textureMaxResolution'].value_counts().sort_index(ascending=False))
        
        # Quality tiers
        high_res = gltf_models['archive_gltf_textureMaxResolution'] >= 4096
        med_res = (gltf_models['archive_gltf_textureMaxResolution'] >= 2048) & \
                  (gltf_models['archive_gltf_textureMaxResolution'] < 4096)
        low_res = gltf_models['archive_gltf_textureMaxResolution'] < 2048
        
        print(f"\nQuality tiers:")
        print(f"  High (4K+): {high_res.sum()} models")
        print(f"  Medium (2K-4K): {med_res.sum()} models")
        print(f"  Low (<2K): {low_res.sum()} models")
    
    scraper.export_to_csv(df, 'texture_resolution_analysis.csv')
    print("\nSaved to: texture_resolution_analysis.csv")
    
    return df


def example_3_pbr_analysis():
    """
    Example 3: PBR Type Analysis (NEW!)
    
    The pbrType field identifies the PBR workflow used.
    Critical for technical compatibility analysis.
    """
    print("\n" + "="*70)
    print("EXAMPLE 3: PBR Type Analysis")
    print("="*70)
    
    scraper = SketchfabScraper(rate_limit_delay=1.0)
    
    # Get detailed data to access pbrType
    basic_models = scraper.search_cultural_heritage(
        query="3d scan",
        max_results=30
    )
    
    print(f"\nEnriching {len(basic_models)} models to get PBR type...")
    
    enriched = scraper.enrich_search_results(
        basic_models,
        include_full_details=True,
        include_comments=False,
        max_models=30
    )
    
    df = scraper.to_dataframe(enriched, comprehensive=True)
    
    print(f"\nPBR Workflow Distribution:")
    pbr_counts = df['pbrType'].value_counts(dropna=False)
    print(pbr_counts)
    
    print(f"\nBreakdown:")
    print(f"  Metalness/Roughness: {(df['pbrType'] == 'metalness').sum()}")
    print(f"  Specular/Glossiness: {(df['pbrType'] == 'specular').sum()}")
    print(f"  Non-PBR: {df['pbrType'].isna().sum()}")
    
    scraper.export_to_csv(df, 'pbr_analysis.csv')
    print("\nSaved to: pbr_analysis.csv")
    
    return df


def example_4_comments_analysis():
    """
    Example 4: Community Engagement via Comments
    
    Analyzes comment patterns and user engagement.
    """
    print("\n" + "="*70)
    print("EXAMPLE 4: Comments Analysis")
    print("="*70)
    
    scraper = SketchfabScraper(rate_limit_delay=1.5)
    
    models = scraper.search_cultural_heritage(
        query="ancient egypt",
        max_results=10
    )
    
    print(f"\nAnalyzing comments from {len(models)} models...")
    
    all_comments = []
    
    for i, model in enumerate(models, 1):
        uid = model['uid']
        name = model['name']
        
        print(f"  {i}/{len(models)}: {name[:50]}...")
        
        comments = scraper.get_model_comments(uid)
        
        for comment in comments:
            comment['model_uid'] = uid
            comment['model_name'] = name
        
        all_comments.extend(comments)
    
    if all_comments:
        comments_df = scraper.comments_to_dataframe(all_comments)
        
        print(f"\n{'─'*70}")
        print("Comment Analysis:")
        print(f"{'─'*70}")
        print(f"Total comments: {len(comments_df)}")
        print(f"Unique commenters: {comments_df['author_username'].nunique()}")
        print(f"Average comment length: {comments_df['body'].str.len().mean():.0f} chars")
        
        print("\nMost active commenters:")
        print(comments_df['author_username'].value_counts().head(5))
        
        print("\nRecent comments:")
        recent = comments_df.sort_values('createdAt', ascending=False).head(3)
        for _, comment in recent.iterrows():
            print(f"\n  @{comment['author_username']} on {comment['createdAt'][:10]}:")
            print(f"  {comment['body'][:100]}...")
        
        scraper.export_to_csv(comments_df, 'comments_analysis.csv')
        print("\nSaved to: comments_analysis.csv")
        
        return comments_df
    else:
        print("\nNo comments found on these models.")
        return None


def example_5_organization_research():
    """
    Example 5: Organization & Institutional Analysis (NEW!)
    
    Analyzes models from organizations and their projects.
    """
    print("\n" + "="*70)
    print("EXAMPLE 5: Organization & Institutional Research")
    print("="*70)
    
    scraper = SketchfabScraper(rate_limit_delay=1.5)
    
    # Search for institutional models
    df = scraper.search_cultural_heritage(
        query="museum heritage",
        max_results=50
    )
    
    # Filter for organization models
    org_models = df[df['org_uid'].notna()].copy()
    
    print(f"\nFound {len(org_models)} organization models out of {len(df)} total")
    
    if len(org_models) > 0:
        print(f"\nTop Organizations:")
        print(org_models['org_displayName'].value_counts().head(10))
        
        print(f"\nOrganization Projects:")
        if 'org_project_name' in org_models.columns:
            projects = org_models[org_models['org_project_name'].notna()]
            if len(projects) > 0:
                print(projects.groupby(['org_displayName', 'org_project_name']).size())
        
        print(f"\nVisibility Settings:")
        if 'visibility' in org_models.columns:
            print(org_models['visibility'].value_counts())
        
        scraper.export_to_csv(org_models, 'organization_models.csv')
        print("\nSaved to: organization_models.csv")
        
        return org_models
    else:
        print("\nNo organization models found in this sample.")
        return None


def example_6_complete_dataset():
    """
    Example 6: Complete Dataset with ALL Fields
    
    Creates a comprehensive dataset with every available field.
    This is the slowest operation but provides complete data.
    """
    print("\n" + "="*70)
    print("EXAMPLE 6: Complete Dataset with ALL 85+ Fields")
    print("="*70)
    
    scraper = SketchfabScraper(rate_limit_delay=2.0)  # Conservative
    
    print("\nSearching for models...")
    df = scraper.search_cultural_heritage(
        query="archaeological site",
        max_results=10,
        archives_flavours=True
    )
    
    print(f"Found {len(df)} models")
    print(f"Current fields: {len(df.columns)}")
    
    print("\nEnriching with full details and comments...")
    enriched = scraper.enrich_search_results(
        df.to_dict('records'),
        include_full_details=True,
        include_comments=True,
        max_models=10
    )
    
    complete_df = scraper.to_dataframe(enriched, comprehensive=True)
    
    print(f"\nComplete dataset created:")
    print(f"  Models: {len(complete_df)}")
    print(f"  Fields: {len(complete_df.columns)}")
    print(f"  With comments: {complete_df['has_fetched_comments'].sum()}")
    
    print(f"\nField categories:")
    print(f"  Core: uid, name, description, dates, etc.")
    print(f"  Metrics: views, likes, comments, downloads")
    print(f"  Geometry: faces, vertices, materials, textures")
    print(f"  User: username, account, avatar")
    print(f"  License: type, requirements, URL")
    print(f"  Archives: size, resolution, formats")
    print(f"  Technical: PBR type, processing status")
    print(f"  Organization: org, projects, visibility")
    print(f"  Comments: fetched count, has comments")
    
    # Save both formats
    scraper.export_to_csv(complete_df, 'complete_dataset.csv')
    scraper.export_complete_data_to_json(enriched, 'complete_dataset.json')

    print("\nSaved to:")
    print("  - complete_dataset.csv (tabular)")
    print("  - complete_dataset.json (nested, preserves all structures)")
    
    return complete_df


def example_7_processing_status():
    """
    Example 7: Processing Status Analysis (NEW!)
    
    Tracks model processing states and archive readiness.
    """
    print("\n" + "="*70)
    print("EXAMPLE 7: Processing Status Analysis")
    print("="*70)
    
    scraper = SketchfabScraper(rate_limit_delay=1.0)
    
    basic_models = scraper.search_cultural_heritage(
        query="reconstruction",
        max_results=20
    )
    
    print(f"\nChecking processing status for {len(basic_models)} models...")
    
    enriched = scraper.enrich_search_results(
        basic_models,
        include_full_details=True,
        include_comments=False,
        max_models=20
    )
    
    df = scraper.to_dataframe(enriched, comprehensive=True)
    
    print(f"\nArchive Readiness:")
    if 'isArchivesReady' in df.columns:
        ready = df['isArchivesReady'].sum()
        print(f"  Archives ready: {ready}/{len(df)}")
    
    print(f"\nProcessing Status:")
    if 'processingStatus' in df.columns:
        print(df['processingStatus'].value_counts())
    
    print(f"\nDownloadable Models:")
    downloadable = df['isDownloadable'].sum()
    print(f"  {downloadable}/{len(df)} models are downloadable")
    
    return df


def main():
    """Run examples"""
    
    print("\n" + "═"*70)
    print(" Sketchfab API Scraper - Practical Examples")
    print("═"*70)
    print("\nDemonstrates complete API data collection:")
    print("  1. Basic Search")
    print("  2. Texture Resolution Analysis (NEW!)")
    print("  3. PBR Type Analysis (NEW!)")
    print("  4. Comments Analysis")
    print("  5. Organization Research (NEW!)")
    print("  6. Complete Dataset (ALL 85+ fields)")
    print("  7. Processing Status Analysis (NEW!)")

    print("\nNote: Examples 2-7 require additional API calls and will be slower.")
    
    response = input("\nRun all examples? (y/n): ")
    
    if response.lower() != 'y':
        print("\nExiting. Edit this file to run specific examples.")
        return
    
    results = {}
    
    try:
        # Fast example
        results['basic'] = example_1_basic_search()
        
        # New field examples
        results['texture'] = example_2_texture_resolution()
        results['pbr'] = example_3_pbr_analysis()
        
        # Comments
        results['comments'] = example_4_comments_analysis()
        
        # Organization data
        results['org'] = example_5_organization_research()
        
        # Processing status
        results['status'] = example_7_processing_status()
        
        # Ask before slowest example
        print("\n" + "─"*70)
        response = input("\nRun Example 6 (Complete Dataset)? This is the slowest. (y/n): ")
        
        if response.lower() == 'y':
            results['complete'] = example_6_complete_dataset()
        
        # Summary
        print("\n" + "═"*70)
        print(" All Examples Complete!")
        print("═"*70)
        print("\nGenerated files:")
        print("  - texture_resolution_analysis.csv")
        print("  - pbr_analysis.csv")
        print("  - comments_analysis.csv")
        print("  - organization_models.csv")
        
        if 'complete' in results:
            print("  - complete_dataset.csv")
            print("  - complete_dataset.json")

        print("\nYou now have comprehensive Sketchfab data!")
        print("Adapt these examples for your research needs.")
        
    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user.")
    except Exception as e:
        print(f"\n\nError running examples: {e}")
        raise


if __name__ == "__main__":
    main()
