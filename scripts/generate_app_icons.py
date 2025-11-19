#!/usr/bin/env python3
"""
Generate app icons with "AU Archive" branding
Creates all required sizes for macOS, Windows, and Linux
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import sys

# Icon sizes needed for Electron apps
ICON_SIZES = [16, 24, 32, 48, 64, 128, 256, 512, 1024]

def create_icon_with_text(source_image_path: Path, output_dir: Path, text: str = "AU Archive"):
    """
    Create app icons in all required sizes with text overlay.

    Args:
        source_image_path: Path to the source high-res icon
        output_dir: Directory to save generated icons
        text: Text to add to the icon (default: "AU Archive")
    """
    print(f"Loading source image: {source_image_path}")

    # Load source image
    source = Image.open(source_image_path)

    # Convert to RGBA if not already
    if source.mode != 'RGBA':
        source = source.convert('RGBA')

    # Get original size
    orig_width, orig_height = source.size
    print(f"Original size: {orig_width}x{orig_height}")

    # Create a version with text for the larger sizes (256+)
    # For smaller sizes, text won't be readable so we'll use the icon without text

    # Create text overlay version (for larger icons)
    text_version = source.copy()
    draw = ImageDraw.Draw(text_version)

    # Try to use a nice font, fall back to default if not available
    try:
        # Use a bold font for better visibility
        font_size = int(orig_height * 0.15)  # 15% of icon height
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except:
        # Fallback to default font
        font = ImageFont.load_default()

    # Calculate text position (bottom center)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Position text at bottom with some padding
    x = (orig_width - text_width) // 2
    y = orig_height - text_height - int(orig_height * 0.08)  # 8% padding from bottom

    # Draw text with shadow for better visibility
    shadow_offset = int(font_size * 0.05)

    # Shadow (black with transparency)
    draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=(0, 0, 0, 180))

    # Main text (white)
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate all icon sizes
    for size in ICON_SIZES:
        print(f"Generating {size}x{size} icon...")

        # Use text version for larger sizes (128+), plain for smaller
        if size >= 128:
            base = text_version
        else:
            base = source

        # Resize with high-quality resampling
        resized = base.resize((size, size), Image.Resampling.LANCZOS)

        # Save as PNG
        output_path = output_dir / f"{size}x{size}.png"
        resized.save(output_path, 'PNG', optimize=True)
        print(f"  Saved: {output_path}")

    print(f"\nSuccessfully generated {len(ICON_SIZES)} icon sizes!")
    print(f"Output directory: {output_dir}")

    # Also save a master 1024x1024 version with text
    master_path = output_dir / "icon.png"
    text_version.resize((1024, 1024), Image.Resampling.LANCZOS).save(master_path, 'PNG', optimize=True)
    print(f"\nMaster icon saved: {master_path}")


def main():
    # Paths
    source_image = Path("/home/user/aupat/App Icon.png")
    output_dir = Path("/home/user/aupat/desktop/resources/icons")

    if not source_image.exists():
        print(f"Error: Source image not found: {source_image}")
        sys.exit(1)

    print("=" * 60)
    print("AU Archive Icon Generator")
    print("=" * 60)
    print()

    create_icon_with_text(source_image, output_dir)

    print()
    print("=" * 60)
    print("Done! Icons are ready for Electron app.")
    print("=" * 60)


if __name__ == '__main__':
    main()
