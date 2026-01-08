#!/usr/bin/env python3
"""
Quick script to update tags on the last 10 videos (newest first).
Uses the SEO tag generation from youtube_api.py.
"""
import sys
import os

# Add current directory to path to import youtube_api
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from youtube_api import (
    run_seo_tag_plan_from_backup,
    apply_seo_tag_plan,
    get_authenticated_service,
    json
)

BACKUP_FILE = "youtube_backup_20251227_032322.json"
LIMIT = 10

def main():
    print("=" * 60)
    print("🔖 TAG UPDATE: Last 10 Videos (Newest First)")
    print("=" * 60)
    print()
    
    # Step 1: Generate tag plan for all videos (will be sorted newest-first)
    print("Step 1: Generating SEO tag plan...")
    plan_file = run_seo_tag_plan_from_backup(
        backup_file=BACKUP_FILE,
        oldest_first=False  # newest first
    )
    
    # Step 2: Limit the plan to last 10 videos
    print(f"\nStep 2: Limiting plan to {LIMIT} newest videos...")
    with open(plan_file, "r", encoding="utf-8") as f:
        plan = json.load(f)
    
    # Videos are already sorted newest-first, so take first LIMIT
    plan["videos"] = plan["videos"][:LIMIT]
    plan["total_videos"] = len(plan["videos"])
    plan["limit_applied"] = LIMIT
    
    # Save the limited plan
    limited_plan_file = plan_file.replace(".json", f"_last{LIMIT}.json")
    with open(limited_plan_file, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Created limited plan: {limited_plan_file}")
    print(f"  Total videos in plan: {len(plan['videos'])}")
    print()
    
    # Show preview of what will be updated
    print("Preview of tag updates:")
    print("-" * 60)
    for i, v in enumerate(plan["videos"][:3], 1):
        print(f"{i}. {v['title'][:50]}...")
        print(f"   Current: {len(v['current_tags'])} tags")
        print(f"   New:     {len(v['new_tags'])} tags")
        if v['current_tags']:
            print(f"   Current tags (sample): {', '.join(v['current_tags'][:3])}...")
        if v['new_tags']:
            print(f"   New tags (sample): {', '.join(v['new_tags'][:5])}...")
        print()
    
    if len(plan["videos"]) > 3:
        print(f"... and {len(plan['videos']) - 3} more videos\n")
    
    # Step 3: Confirm and apply
    print("=" * 60)
    print("Ready to apply tag updates.")
    print("=" * 60)
    print("\nAuthenticating and applying updates...")
    print()
    
    service = get_authenticated_service()
    results = apply_seo_tag_plan(
        service=service,
        plan_file=limited_plan_file,
        dry_run=False,
        batch_size=10,
        delay_seconds=2.0,
        skip_already_successful=True,
    )
    
    successful = sum(1 for v in results.values() if v)
    total = len(results)
    
    print()
    print("=" * 60)
    print(f"📊 FINAL RESULTS: {successful}/{total} videos updated successfully")
    print("=" * 60)

if __name__ == "__main__":
    main()

