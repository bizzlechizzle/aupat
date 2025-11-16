#!/usr/bin/env python3
"""
Test script to extract and dump full video metadata.
This helps debug why drone videos aren't being detected.
"""

import json
import subprocess
import sys
from pathlib import Path

def extract_with_ffprobe_full(file_path: str) -> dict:
    """Extract ALL metadata using ffprobe."""
    try:
        # Get full metadata dump
        result = subprocess.run(
            [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                file_path
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            print(f"ffprobe failed: {result.stderr}", file=sys.stderr)
            return {}
    except FileNotFoundError:
        print("ERROR: ffprobe not found - install with: brew install ffmpeg or apt-get install ffmpeg", file=sys.stderr)
        return {}
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return {}

def extract_with_exiftool(file_path: str) -> dict:
    """Extract metadata using exiftool."""
    try:
        result = subprocess.run(
            ['exiftool', '-j', '-a', '-G', file_path],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data[0] if data else {}
        else:
            print(f"exiftool failed: {result.stderr}", file=sys.stderr)
            return {}
    except FileNotFoundError:
        print("ERROR: exiftool not found - install with: brew install exiftool or apt-get install exiftool", file=sys.stderr)
        return {}
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return {}

def analyze_for_drone_markers(metadata: dict, source: str = "unknown") -> None:
    """Analyze metadata for drone-related markers."""
    print(f"\n{'='*80}")
    print(f"DRONE DETECTION ANALYSIS ({source})")
    print(f"{'='*80}")

    drone_keywords = ['dji', 'drone', 'mavic', 'phantom', 'inspire', 'air', 'mini',
                      'autel', 'parrot', 'skydio', 'yuneec', 'hasselblad']

    # Flatten dict for searching
    def flatten_dict(d, parent_key='', sep='_'):
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        items.extend(flatten_dict(item, f"{new_key}[{i}]", sep=sep).items())
                    else:
                        items.append((f"{new_key}[{i}]", str(item)))
            else:
                items.append((new_key, str(v)))
        return dict(items)

    flat = flatten_dict(metadata)

    # Look for drone markers
    found_markers = []
    for key, value in flat.items():
        for keyword in drone_keywords:
            if keyword.lower() in str(key).lower() or keyword.lower() in str(value).lower():
                found_markers.append((key, value, keyword))

    if found_markers:
        print(f"✓ FOUND {len(found_markers)} DRONE MARKER(S):")
        for key, value, keyword in found_markers:
            print(f"  - {key}: {value} (matched: '{keyword}')")
    else:
        print("✗ NO DRONE MARKERS FOUND")

    # Check common make/model fields
    print(f"\nCOMMON MAKE/MODEL FIELDS:")
    make_fields = ['make', 'Make', 'manufacturer', 'Manufacturer', 'CompressorName']
    model_fields = ['model', 'Model', 'device', 'Device']

    for field in make_fields:
        if field in flat:
            print(f"  Make ({field}): {flat[field]}")
    for field in model_fields:
        if field in flat:
            print(f"  Model ({field}): {flat[field]}")

def main():
    """Test metadata extraction on Water Slide World videos."""
    video_dir = Path("/home/user/aupat/tempdata/testphotos/Water Slide World/Video - Originals/Video - Originals")

    if not video_dir.exists():
        print(f"ERROR: Directory not found: {video_dir}")
        return 1

    videos = list(video_dir.glob("*.MOV")) + list(video_dir.glob("*.mov"))

    if not videos:
        print(f"ERROR: No videos found in {video_dir}")
        return 1

    print("="*80)
    print("VIDEO METADATA DEEP DIVE - Water Slide World")
    print("="*80)
    print(f"Found {len(videos)} video(s)")

    for video in videos[:1]:  # Test first video
        print(f"\n{'='*80}")
        print(f"FILE: {video.name}")
        print(f"{'='*80}")

        # Try exiftool first
        print("\n" + "-"*80)
        print("EXIFTOOL METADATA DUMP")
        print("-"*80)
        exif_data = extract_with_exiftool(str(video))
        if exif_data:
            print(json.dumps(exif_data, indent=2))
            analyze_for_drone_markers(exif_data, "exiftool")

        # Try ffprobe
        print("\n" + "-"*80)
        print("FFPROBE METADATA DUMP")
        print("-"*80)
        ffprobe_data = extract_with_ffprobe_full(str(video))
        if ffprobe_data:
            print(json.dumps(ffprobe_data, indent=2))
            analyze_for_drone_markers(ffprobe_data, "ffprobe")

        # Current implementation check
        print("\n" + "-"*80)
        print("CURRENT IMPLEMENTATION (ffprobe with limited fields)")
        print("-"*80)
        result = subprocess.run(
            [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_entries', 'format_tags=make,Make,model,Model',
                '-show_format',
                str(video)
            ],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            current_impl = json.loads(result.stdout)
            print(json.dumps(current_impl, indent=2))
            tags = current_impl.get('format', {}).get('tags', {})
            make = tags.get('make', tags.get('Make', ''))
            model = tags.get('model', tags.get('Model', ''))
            print(f"\nExtracted Make: '{make}'")
            print(f"Extracted Model: '{model}'")
            if not make:
                print("⚠️  WARNING: Current implementation found NO make field!")
        else:
            print(f"ERROR: {result.stderr}")

    return 0

if __name__ == '__main__':
    sys.exit(main())
