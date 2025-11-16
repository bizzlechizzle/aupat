#!/usr/bin/env python3
"""
Test script to verify drone detection fix.
"""

import json
import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from db_organize import extract_video_metadata, categorize_hardware, load_camera_hardware

def test_drone_detection():
    """Test drone detection on Water Slide World videos."""
    video_dir = Path("/home/user/aupat/tempdata/testphotos/Water Slide World/Video - Originals/Video - Originals")

    if not video_dir.exists():
        print(f"ERROR: Directory not found: {video_dir}")
        return 1

    videos = list(video_dir.glob("*.MOV")) + list(video_dir.glob("*.mov"))

    if not videos:
        print(f"ERROR: No videos found in {video_dir}")
        return 1

    print("="*80)
    print("DRONE DETECTION TEST - Water Slide World")
    print("="*80)

    hardware_rules = load_camera_hardware()

    for video in videos:
        print(f"\n{'='*80}")
        print(f"Testing: {video.name}")
        print(f"{'='*80}")

        # Extract metadata using updated function
        metadata = extract_video_metadata(str(video))

        # Replicate the logic from organize_videos
        format_tags = metadata.get('format', {}).get('tags', {})
        make = format_tags.get('make', format_tags.get('Make', ''))
        model = format_tags.get('model', format_tags.get('Model', ''))

        print(f"\n1. Format tags:")
        print(f"   Make: '{make}'")
        print(f"   Model: '{model}'")

        # Check stream tags
        if not make and metadata.get('streams'):
            print(f"\n2. Checking stream tags...")
            for i, stream in enumerate(metadata['streams']):
                stream_tags = stream.get('tags', {})
                handler_name = stream_tags.get('handler_name', '')
                encoder = stream_tags.get('encoder', '')

                print(f"   Stream {i}:")
                print(f"     handler_name: '{handler_name}'")
                print(f"     encoder: '{encoder}'")

                if 'DJI' in handler_name.upper() or 'DJI' in encoder.upper():
                    make = 'DJI'
                    print(f"     DETECTED DJI from stream metadata!")
                    break

                if not make:
                    make = stream_tags.get('make', stream_tags.get('Make', ''))
                    model = stream_tags.get('model', stream_tags.get('Model', ''))
                    if make:
                        print(f"     Found make/model in stream tags: make='{make}', model='{model}'")
                        break

        print(f"\n3. Final extracted metadata:")
        print(f"   Make: '{make}'")
        print(f"   Model: '{model}'")

        # Categorize
        category = categorize_hardware(make, model, hardware_rules)

        print(f"\n4. Hardware categorization:")
        print(f"   Category: {category}")
        print(f"   Is drone: {'YES' if category == 'drone' else 'NO'}")

        if category == 'drone':
            print(f"\n{'='*80}")
            print("SUCCESS: Drone video correctly detected!")
            print(f"{'='*80}")
        else:
            print(f"\n{'='*80}")
            print("FAILURE: Drone video NOT detected!")
            print(f"{'='*80}")
            return 1

    print(f"\n{'='*80}")
    print("ALL TESTS PASSED!")
    print(f"{'='*80}")
    return 0

if __name__ == '__main__':
    sys.exit(test_drone_detection())
