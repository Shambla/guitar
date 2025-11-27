#!/usr/bin/env python3
"""
PDF Preview Generator with Watermark
Generates first-page previews of sheet music PDFs with "PREVIEW" watermark

Requirements:
    pip install pdf2image Pillow

Note: Also requires poppler-utils:
    macOS: brew install poppler
    Ubuntu/Debian: sudo apt-get install poppler-utils
"""

import os
from pathlib import Path
from pdf2image import convert_from_path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

# Configuration
PDF_FOLDER = Path("pdfs")  # Folder containing your PDF files
PREVIEW_FOLDER = Path("previews")  # Output folder for previews
WATERMARK_TEXT = "PREVIEW"
WATERMARK_OPACITY = 128  # 0-255 (128 = 50% transparent)
IMAGE_WIDTH = 800  # Width of output preview images
QUALITY = 85  # JPEG quality (1-100)

def create_preview_folder():
    """Create preview folder if it doesn't exist"""
    PREVIEW_FOLDER.mkdir(exist_ok=True)
    print(f"✓ Preview folder ready: {PREVIEW_FOLDER}")

def add_watermark(image_path, watermark_text=WATERMARK_TEXT, opacity=WATERMARK_OPACITY):
    """Add diagonal watermark to image"""
    try:
        # Open image
        img = Image.open(image_path).convert("RGBA")
        
        # Create transparent overlay for watermark
        overlay = Image.new('RGBA', img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Try to load a bold font, fallback to default
        try:
            # Adjust font path for your system
            font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 120)
        except:
            try:
                font = ImageFont.truetype("/Library/Fonts/Arial Bold.ttf", 120)
            except:
                print("  Warning: Could not load custom font, using default")
                font = ImageFont.load_default()
        
        # Get text size
        bbox = draw.textbbox((0, 0), watermark_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Calculate position (centered, rotated diagonally)
        width, height = img.size
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        # Draw watermark with transparency
        draw.text((x, y), watermark_text, fill=(200, 200, 200, opacity), font=font)
        
        # Rotate overlay
        overlay = overlay.rotate(45, expand=False)
        
        # Composite watermark onto image
        watermarked = Image.alpha_composite(img, overlay)
        
        # Convert back to RGB for saving as JPEG
        watermarked = watermarked.convert("RGB")
        
        # Save
        watermarked.save(image_path, "JPEG", quality=QUALITY)
        return True
    except Exception as e:
        print(f"  Error adding watermark: {e}")
        return False

def generate_preview(pdf_path, output_name=None):
    """Generate first-page preview from PDF with watermark"""
    try:
        # Get output filename
        if output_name is None:
            output_name = pdf_path.stem
        
        output_path = PREVIEW_FOLDER / f"{output_name}-preview.png"
        
        # Skip if preview already exists
        if output_path.exists():
            print(f"  Skipping (already exists): {output_name}")
            return True
        
        print(f"  Processing: {pdf_path.name}")
        
        # Convert first page of PDF to image
        images = convert_from_path(
            str(pdf_path),
            first_page=1,
            last_page=1,
            dpi=150  # Good quality for web display
        )
        
        if not images:
            print(f"  Error: Could not convert PDF")
            return False
        
        # Get first page
        img = images[0]
        
        # Resize to standard width while maintaining aspect ratio
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
    """Generate previews for all PDFs in folder"""
    # Check if PDF folder exists
    if not PDF_FOLDER.exists():
        print(f"Error: PDF folder not found: {PDF_FOLDER}")
        print(f"Please create the folder and add your PDF files.")
        return
    
    # Get all PDF files
    pdf_files = list(PDF_FOLDER.glob("*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {PDF_FOLDER}")
        return
    
    print(f"\nFound {len(pdf_files)} PDF files")
    print(f"Generating previews...\n")
    
    # Process each PDF
    success_count = 0
    for pdf_path in pdf_files:
        if generate_preview(pdf_path):
            success_count += 1
    
    print(f"\n✓ Generated {success_count}/{len(pdf_files)} previews")
    print(f"✓ Previews saved to: {PREVIEW_FOLDER.absolute()}")

def generate_single_preview(pdf_filename, output_name=None):
    """Generate preview for a single PDF file"""
    pdf_path = PDF_FOLDER / pdf_filename
    
    if not pdf_path.exists():
        print(f"Error: PDF not found: {pdf_path}")
        return False
    
    return generate_preview(pdf_path, output_name)

if __name__ == "__main__":
    import sys
    
    # Create preview folder
    create_preview_folder()
    
    # Check command line arguments
    if len(sys.argv) > 1:
        # Single file mode
        pdf_filename = sys.argv[1]
        output_name = sys.argv[2] if len(sys.argv) > 2 else None
        print(f"\nGenerating preview for: {pdf_filename}")
        generate_single_preview(pdf_filename, output_name)
    else:
        # Batch mode
        batch_generate_previews()
    
    print("\nDone! Upload the preview images to your website's 'previews' folder.")

