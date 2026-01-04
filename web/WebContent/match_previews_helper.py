#!/usr/bin/env python3
"""
Match Preview Images with Catalog Data Helper
Automatically matches generated preview images to catalog entries and updates catalog-data.json
"""

import json
import re
from pathlib import Path
from difflib import SequenceMatcher

# Configuration
CATALOG_FILE = Path("/Users/olivia2/Documents/GitHub/guitar/web/WebContent/catalog-data.json")
PREVIEW_FOLDER = Path("/Users/olivia2/Documents/GitHub/guitar/web/WebContent/img/previews")
BACKUP_FILE = CATALOG_FILE.with_suffix('.json.backup')

# Manual mappings for known matches (catalog_id -> preview_filename)
MANUAL_MAPPINGS = {
    'swan-lake': 'Kuu_Gl_-_Swan_Lake_Theme_For_Guitar-preview.png',
    'swing-low-sweet-charioy': 'Sweet_Chariot_1-preview.png',
    'aria-excerpt-from-goldberg-variations': 'Bach_Goldberg_Aria_Solo_3_Sections-preview.png',
    'minuet-bwv-114': 'Bach_Minuet_8-preview.png',
    'fox-nfl-theme': 'NFL_Fox_theme_D_minor-preview.png',
    'triad-chord-worksheet': 'Triad_Chord_Worksheet-preview.png',
    'drowsy-maggie': 'Drowsy_Maggie_Guitar_7-preview.png',
    'canon-in-d': 'Canon_in_D_by_Johann_Pachelbel-preview.png',
    'moonlight-sonata-1st-movement': 'Moonlight_Sonata_sustain08-03-preview.png',
    'flow-my-tears': 'Flow_My_Tears_John_Dowland_2-preview.png',
    'd-egyptian-etude': 'D_Egyptian_Etude-preview.png',
    'lost-boy': 'Lost_Boy_4_3_23-preview.png',
    'in-the-hall-of-the-mountain-king-excerpt-from-peer-gynt---arranged-for-guitar': 'Mountain_King_6-preview.png',
    'guitar-chord-exercises---iterating-chords': '23_Left_Hand_Exercises_for_Guitar-preview.png',
    'movable-guitar-chords': 'Movable_Guitar_Chords-preview.png',
    'true-blue-bossa': 'Blue_bossa_4_pianobass_Combine08-03-preview.png',
    'cello-suite-3-mvt-ll-allemande': 'Cello_Suite_3_mvt_ll_Allemande-preview.png',
    'cello-suite-no-3-mvt-lll-courante': 'Cello_Suite_No_3_mvt_lll_Courante-preview.png',
    '5-scale-forms-for-guitar': '5_Scale_Forms_For_Guitar-preview.png',
    'f-minor-ab-major-bossa-nova-jazz': 'F_Minor_AB_Major_Bossa_Nova_Jazz-preview.png',
    'g-major-e-minor-irish-folk': 'G_Major_E_Minor_Irish_Folk-preview.png',
    'last-night': 'Last_Night_-_Morgan_Wallen-preview.png',
    'gnossienne-no-3-tablature-and-sheet-music': 'Gnossienne_3_Combine_02_01_23-preview.png',
    'study-no-2-d-dorian-mode': 'D_Dorian_1_Just_Melody_Version_2-preview.png',
    'study-no-6-no-7---major-and-minor-modes': 'Study_No_6_+_7_-_Streckfus-preview.png',
    'off-kilter-grit-120-bpm-a-minor': 'Off_KilterGrit_120_BPM_A_minor-preview.png',
    'movable-guitar-chords': 'Movable_Guitar_Chords-preview.png',
    'cello-suite-3-mvt-ll-allemande': 'Cello_Suite_3_mvt_ll_Allemande-preview.png',
    'cello-suite-no-3-mvt-lll-courante': 'Cello_Suite_No_3_mvt_lll_Courante-preview.png',
    '5-scale-forms-for-guitar': '5_Scale_Forms_For_Guitar-preview.png',
    'triad-chord-worksheet': 'Triad_Chord_Worksheet-preview.png',
    'g-major-e-minor-irish-folk': 'G_Major_E_Minor_Irish_Folk-preview.png',
    'off-kiltergrit-120-bpm-a-minor': 'Off_KilterGrit_120_BPM_A_minor-preview.png',
}

def similarity(a, b):
    """Calculate similarity ratio between two strings"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def normalize_string(s):
    """Normalize string for matching - remove common words, punctuation, etc."""
    s = s.lower()
    # Remove common words that don't help matching
    common_words = ['arr', 'arrangement', 'arranged', 'for', 'guitar', 'the', 'a', 'an', 'and', 'or', 'but']
    words = re.split(r'[\s_\-]+', s)
    words = [w for w in words if w and w not in common_words]
    return ' '.join(words)

def extract_key_terms(title, composer=""):
    """Extract key matching terms from title and composer"""
    full_text = f"{title} {composer}".lower()
    
    # Remove common suffixes
    full_text = re.sub(r'\s*\(arr[^)]*\)', '', full_text)
    full_text = re.sub(r'\s*-?\s*full\s*score', '', full_text)
    full_text = re.sub(r'\s*-\s*', ' ', full_text)
    
    # Extract meaningful words (3+ chars, not numbers only)
    words = re.findall(r'\b[a-z]{3,}\b', full_text)
    
    # Prioritize composer names and key musical terms
    important_terms = []
    for word in words:
        if len(word) >= 4:  # Longer words are more distinctive
            important_terms.append(word)
    
    return set(important_terms)

def match_preview_to_catalog(preview_name, catalog_entry):
    """Calculate match score between preview filename and catalog entry"""
    title = catalog_entry.get('title', '')
    composer = catalog_entry.get('composer', '')
    entry_id = catalog_entry.get('id', '')
    
    # Normalize preview name (remove -preview.png)
    preview_base = preview_name.replace('-preview.png', '').replace('.png', '')
    
    # Remove common suffixes from preview name for better matching
    preview_clean = preview_base
    for suffix in ['_4', '_6', '_7', '_8', '_1', '_2', '_3', '_master', '_guitar', '_version']:
        if preview_clean.endswith(suffix):
            preview_clean = preview_clean[:-len(suffix)]
    
    # Strategy 1: Direct title match
    title_normalized = normalize_string(title)
    preview_normalized = normalize_string(preview_clean)
    title_score = similarity(title_normalized, preview_normalized)
    
    # Strategy 2: Key terms matching (more flexible)
    catalog_terms = extract_key_terms(title, composer)
    preview_terms = extract_key_terms(preview_clean)
    
    if catalog_terms and preview_terms:
        common_terms = catalog_terms.intersection(preview_terms)
        term_score = len(common_terms) / max(len(catalog_terms), len(preview_terms), 1)
    else:
        term_score = 0
    
    # Strategy 3: ID-based matching (if ID contains key words)
    id_score = 0
    if entry_id:
        id_normalized = normalize_string(entry_id.replace('-', ' '))
        id_score = similarity(id_normalized, preview_normalized)
    
    # Strategy 4: Partial word matching (check if key words from title appear in preview)
    title_words = set(re.findall(r'\b[a-z]{4,}\b', title.lower()))
    preview_words = set(re.findall(r'\b[a-z]{4,}\b', preview_clean.lower()))
    if title_words and preview_words:
        matching_words = title_words.intersection(preview_words)
        word_score = len(matching_words) / max(len(title_words), len(preview_words), 1)
    else:
        word_score = 0
    
    # Strategy 5: Check for composer name in preview
    composer_score = 0
    if composer:
        composer_lower = composer.lower()
        if composer_lower in preview_clean.lower():
            composer_score = 0.8
    
    # Combined score (weighted, more lenient)
    combined_score = (title_score * 0.35) + (term_score * 0.25) + (id_score * 0.15) + (word_score * 0.15) + (composer_score * 0.10)
    
    return combined_score, {
        'title_score': title_score,
        'term_score': term_score,
        'id_score': id_score,
        'word_score': word_score,
        'composer_score': composer_score,
        'combined': combined_score
    }

def find_best_matches(catalog_data, preview_files):
    """Find best matches between catalog entries and preview files"""
    matches = []
    used_previews = set()
    
    # First pass: Manual mappings (highest priority)
    for entry in catalog_data:
        if entry.get('preview_image'):  # Skip if already has preview
            continue
        
        entry_id = entry.get('id', '')
        if entry_id in MANUAL_MAPPINGS:
            preview_file = MANUAL_MAPPINGS[entry_id]
            if preview_file in preview_files:
                matches.append({
                    'entry': entry,
                    'preview': preview_file,
                    'score': 1.0,  # Perfect match
                    'details': {'method': 'manual_mapping'}
                })
                used_previews.add(preview_file)
    
    # Second pass: High confidence matches (>0.5 similarity)
    for entry in catalog_data:
        if entry.get('preview_image'):  # Skip if already has preview
            continue
            
        best_match = None
        best_score = 0
        best_details = None
        
        for preview_file in preview_files:
            if preview_file in used_previews:
                continue
                
            score, details = match_preview_to_catalog(preview_file, entry)
            
            if score > best_score and score > 0.5:  # Lower threshold for more matches
                best_score = score
                best_match = preview_file
                best_details = details
        
        if best_match:
            matches.append({
                'entry': entry,
                'preview': best_match,
                'score': best_score,
                'details': best_details
            })
            used_previews.add(best_match)
    
    # Second pass: Medium confidence matches (0.5-0.7) for remaining entries
    for entry in catalog_data:
        if entry.get('preview_image'):  # Skip if already has preview
            continue
        
        # Check if already matched in first pass
        already_matched = any(m['entry']['id'] == entry['id'] for m in matches)
        if already_matched:
            continue
        
        best_match = None
        best_score = 0
        best_details = None
        
        for preview_file in preview_files:
            if preview_file in used_previews:
                continue
                
            score, details = match_preview_to_catalog(preview_file, entry)
            
            if score > best_score and 0.4 <= score < 0.5:  # Lower confidence matches
                best_score = score
                best_match = preview_file
                best_details = details
        
        if best_match:
            matches.append({
                'entry': entry,
                'preview': best_match,
                'score': best_score,
                'details': best_details
            })
            used_previews.add(best_match)
    
    return matches

def update_catalog_with_previews(catalog_data, matches):
    """Update catalog entries with preview_image paths"""
    updated_count = 0
    
    # Create a lookup for matches
    match_lookup = {m['entry']['id']: m for m in matches}
    
    for entry in catalog_data:
        if entry['id'] in match_lookup:
            match = match_lookup[entry['id']]
            preview_path = f"img/previews/{match['preview']}"
            entry['preview_image'] = preview_path
            updated_count += 1
    
    return updated_count

def main():
    print("=" * 70)
    print("Preview Image Matcher for Catalog Data")
    print("=" * 70)
    
    # Load catalog data
    print(f"\n1. Loading catalog data from: {CATALOG_FILE}")
    try:
        with open(CATALOG_FILE, 'r', encoding='utf-8') as f:
            catalog_data = json.load(f)
        print(f"   ✓ Loaded {len(catalog_data)} catalog entries")
    except Exception as e:
        print(f"   ✗ Error loading catalog: {e}")
        return
    
    # Get preview files
    print(f"\n2. Scanning preview images from: {PREVIEW_FOLDER}")
    if not PREVIEW_FOLDER.exists():
        print(f"   ✗ Preview folder not found: {PREVIEW_FOLDER}")
        return
    
    preview_files = sorted([f.name for f in PREVIEW_FOLDER.glob("*.png")])
    print(f"   ✓ Found {len(preview_files)} preview images")
    
    # Count entries without previews
    entries_without_previews = [e for e in catalog_data if not e.get('preview_image')]
    print(f"   ✓ Found {len(entries_without_previews)} entries without preview images")
    
    # Find matches
    print(f"\n3. Matching previews to catalog entries...")
    matches = find_best_matches(catalog_data, preview_files)
    print(f"   ✓ Found {len(matches)} potential matches")
    
    # Show matches
    print(f"\n4. Match Results:")
    print(f"{'='*70}")
    print(f"{'Title':<40} {'Preview File':<35} {'Score':<6}")
    print(f"{'-'*70}")
    
    # Sort by score (highest first)
    matches_sorted = sorted(matches, key=lambda x: x['score'], reverse=True)
    
    for match in matches_sorted[:50]:  # Show top 50
        title = match['entry']['title'][:38]
        preview = match['preview'][:33]
        score = f"{match['score']:.2f}"
        print(f"{title:<40} {preview:<35} {score:<6}")
    
    if len(matches) > 50:
        print(f"\n   ... and {len(matches) - 50} more matches")
    
    # Show unmatched entries
    matched_ids = {m['entry']['id'] for m in matches}
    unmatched = [e for e in entries_without_previews if e['id'] not in matched_ids]
    
    if unmatched:
        print(f"\n5. Unmatched Entries ({len(unmatched)}):")
        print(f"{'='*70}")
        for entry in unmatched[:20]:  # Show first 20
            print(f"   - {entry['title']} (ID: {entry['id']})")
        if len(unmatched) > 20:
            print(f"   ... and {len(unmatched) - 20} more")
    
    # Ask for confirmation
    print(f"\n6. Ready to update catalog-data.json")
    print(f"   - Will create backup: {BACKUP_FILE}")
    print(f"   - Will update {len(matches)} entries with preview images")
    
    # Create backup
    print(f"\n7. Creating backup...")
    try:
        with open(CATALOG_FILE, 'r', encoding='utf-8') as f:
            backup_data = f.read()
        with open(BACKUP_FILE, 'w', encoding='utf-8') as f:
            f.write(backup_data)
        print(f"   ✓ Backup created: {BACKUP_FILE}")
    except Exception as e:
        print(f"   ✗ Error creating backup: {e}")
        return
    
    # Update catalog
    print(f"\n8. Updating catalog-data.json...")
    updated_count = update_catalog_with_previews(catalog_data, matches)
    
    # Save updated catalog
    try:
        with open(CATALOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(catalog_data, f, indent=2, ensure_ascii=False)
        print(f"   ✓ Updated {updated_count} entries")
        print(f"   ✓ Saved to: {CATALOG_FILE}")
    except Exception as e:
        print(f"   ✗ Error saving catalog: {e}")
        return
    
    print(f"\n{'='*70}")
    print("Summary:")
    print(f"  ✓ Matched: {len(matches)} entries")
    print(f"  ⊘ Unmatched: {len(unmatched)} entries")
    print(f"  📁 Backup saved: {BACKUP_FILE}")
    print(f"{'='*70}")
    print("\nDone! Review the updated catalog-data.json and verify matches.")

if __name__ == "__main__":
    main()

