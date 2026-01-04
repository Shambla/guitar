#!/usr/bin/env python3
"""
PDF Preview Generator for ArrangeMe PDFs
Generates first-page previews with searchable, obvious filenames
Skips audio files and handles errors gracefully
"""

import os
import re
from pathlib import Path
from pdf2image import convert_from_path
from PIL import Image, ImageDraw, ImageFont

# Configuration
PDF_FOLDER = Path("/Users/olivia2/Desktop/ArrangeMe_PDFs")
PREVIEW_FOLDER = Path("/Users/olivia2/Documents/GitHub/guitar/web/WebContent/img/previews")
WATERMARK_TEXT = "PREVIEW"
WATERMARK_OPACITY = 180
WATERMARK_FONT_SIZE = 180
WATERMARK_COLOR = (60, 60, 60)
IMAGE_WIDTH = 800
QUALITY = 85

def create_preview_folder():
    """Create preview folder if it doesn't exist"""
    PREVIEW_FOLDER.mkdir(parents=True, exist_ok=True)
    print(f"✓ Preview folder ready: {PREVIEW_FOLDER}")

def clean_filename(pdf_name):
    """
    Create a searchable, obvious filename from PDF name
    Removes common suffixes, cleans up spacing, makes it grep-friendly
    """
    # Remove .pdf extension
    name = pdf_name.replace('.pdf', '')
    
    # Remove common suffixes that make filenames less searchable
    suffixes_to_remove = [
        ' - Full Score',
        ' (1)',
        ' (2)',
        ' copy',
        ' copy 2',
        ' copy 3',
        ' Rev',
        ' MASTER',
        ' Publishing',
        ' - 2024-',
        ' - 2025-',
        ' 2024-',
        ' 2025-',
        ' dup',
        ' fingerings',
        ' TAB',
        ' Lead sheet',
        ' Lead_sheet',
        ' with lyrics',
        ' with_lyrics',
        ' Harmony',
        ' HARMONY',
        ' Bass Clef',
        ' Student',
        ' SCROLLER',
        ' mscz',
        ' Sib',
        ' RL3',
        ' Compressed',
        ' ALL PDF',
        ' ~',
    ]
    
    for suffix in suffixes_to_remove:
        name = name.replace(suffix, '')
        name = name.replace(suffix.replace(' ', '_'), '')
    
    # Clean up multiple spaces and underscores
    name = re.sub(r'\s+', '_', name)
    name = re.sub(r'_+', '_', name)
    
    # Remove leading/trailing underscores and spaces
    name = name.strip('_').strip()
    
    # Keep it readable but searchable - don't lowercase everything
    # Just clean up the structure
    return name

def add_watermark(image_path, watermark_text=WATERMARK_TEXT, opacity=WATERMARK_OPACITY):
    """Add diagonal watermark to image"""
    try:
        img = Image.open(image_path).convert("RGBA")
        overlay = Image.new('RGBA', img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)
        
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", WATERMARK_FONT_SIZE)
        except:
            try:
                font = ImageFont.truetype("/Library/Fonts/Arial Bold.ttf", WATERMARK_FONT_SIZE)
            except:
                font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), watermark_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        width, height = img.size
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        draw.text((x, y), watermark_text, fill=(*WATERMARK_COLOR, opacity), font=font)
        overlay = overlay.rotate(45, expand=False)
        watermarked = Image.alpha_composite(img, overlay)
        watermarked = watermarked.convert("RGB")
        watermarked.save(image_path, "JPEG", quality=QUALITY)
        return True
    except Exception as e:
        print(f"  Error adding watermark: {e}")
        return False

def generate_preview(pdf_path):
    """Generate first-page preview from PDF with watermark"""
    try:
        # Create clean, searchable filename
        clean_name = clean_filename(pdf_path.name)
        output_path = PREVIEW_FOLDER / f"{clean_name}-preview.png"
        
        # Skip if preview already exists
        if output_path.exists():
            print(f"  ✓ Already exists: {clean_name}")
            return True
        
        print(f"  Processing: {pdf_path.name}")
        print(f"    → Will save as: {clean_name}-preview.png")
        
        # Convert first page of PDF to image
        images = convert_from_path(
            str(pdf_path),
            first_page=1,
            last_page=1,
            dpi=150
        )
        
        if not images:
            print(f"  ✗ Error: Could not convert PDF")
            return False
        
        img = images[0]
        aspect_ratio = img.height / img.width
        new_height = int(IMAGE_WIDTH * aspect_ratio)
        img = img.resize((IMAGE_WIDTH, new_height), Image.Resampling.LANCZOS)
        
        # Save temporarily
        img.save(output_path, "PNG")
        
        # Add watermark
        add_watermark(output_path)
        
        print(f"  ✓ Created: {output_path.name}")
        return True
        
    except Exception as e:
        print(f"  ✗ Error processing {pdf_path.name}: {e}")
        return False

def batch_generate_previews():
    """Generate previews for all PDFs in ArrangeMe_PDFs folder"""
    if not PDF_FOLDER.exists():
        print(f"Error: PDF folder not found: {PDF_FOLDER}")
        return
    
    # Get all PDF files (skip audio files)
    pdf_files = sorted([f for f in PDF_FOLDER.glob("*.pdf")], key=lambda p: p.name.lower())
    
    if not pdf_files:
        print(f"No PDF files found in {PDF_FOLDER}")
        return
    
    print(f"\n{'='*60}")
    print(f"ArrangeMe PDF Preview Generator")
    print(f"{'='*60}")
    print(f"Found {len(pdf_files)} PDF files")
    print(f"Output folder: {PREVIEW_FOLDER}")
    print(f"Generating previews...\n")
    
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for pdf_path in pdf_files:
        # Check if already exists (by clean name)
        clean_name = clean_filename(pdf_path.name)
        output_path = PREVIEW_FOLDER / f"{clean_name}-preview.png"
        
        if output_path.exists():
            skip_count += 1
            continue
            
        if generate_preview(pdf_path):
            success_count += 1
        else:
            error_count += 1
    
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  ✓ Successfully generated: {success_count}")
    print(f"  ⊘ Skipped (already exists): {skip_count}")
    print(f"  ✗ Errors: {error_count}")
    print(f"  Total processed: {success_count + skip_count + error_count}")
    print(f"{'='*60}")
    print(f"\n✓ Previews saved to: {PREVIEW_FOLDER}")
    print(f"\nTip: Use grep to search for previews:")
    print(f"  grep -i 'swan_lake' {PREVIEW_FOLDER}/*.png")
    print(f"  grep -i 'nocturne' {PREVIEW_FOLDER}/*.png")

if __name__ == "__main__":
    create_preview_folder()
    batch_generate_previews()
    print("\nDone!")

