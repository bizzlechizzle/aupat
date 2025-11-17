#!/usr/bin/env python3
"""
Test script for map import API
"""

import json
import requests
from pathlib import Path

# Read test CSV file
csv_path = Path(__file__).parent / 'test_map_import.csv'
with open(csv_path, 'r') as f:
    csv_content = f.read()

print("Testing Map Import API")
print("=" * 50)

# Test 1: Parse CSV
print("\n1. Testing CSV parsing...")
response = requests.post(
    'http://localhost:5000/api/maps/parse',
    json={
        'filename': 'test_map.csv',
        'format': 'csv',
        'content': csv_content
    }
)

if response.status_code == 200:
    data = response.json()
    print(f"✓ Parsed successfully!")
    print(f"  - Valid locations: {data['statistics']['valid_locations']}")
    print(f"  - With GPS: {data['statistics']['with_gps']}")
    print(f"  - Errors: {len(data['errors'])}")

    if data['locations']:
        print(f"\n  First location: {data['locations'][0]['name']}")

    # Test 2: Check duplicates
    print("\n2. Testing duplicate detection...")
    dup_response = requests.post(
        'http://localhost:5000/api/maps/check-duplicates',
        json={'locations': data['locations']}
    )

    if dup_response.status_code == 200:
        dup_data = dup_response.json()
        print(f"✓ Checked {dup_data['statistics']['total_checked']} locations")
        print(f"  - Duplicates found: {dup_data['statistics']['with_duplicates']}")

    # Test 3: Import in reference mode
    print("\n3. Testing import (reference mode)...")
    import_response = requests.post(
        'http://localhost:5000/api/maps/import',
        json={
            'filename': 'test_map.csv',
            'format': 'csv',
            'mode': 'reference',
            'content': csv_content,
            'description': 'Test import - Abandoned locations',
            'skip_duplicates': True
        }
    )

    if import_response.status_code == 200:
        import_data = import_response.json()
        print(f"✓ Import completed!")
        print(f"  - Map ID: {import_data['map_id']}")
        print(f"  - Imported: {import_data['statistics']['imported']}")
        print(f"  - Skipped: {import_data['statistics']['skipped']}")

        # Test 4: Search reference maps
        print("\n4. Testing reference map search...")
        search_response = requests.get(
            'http://localhost:5000/api/maps/search',
            params={'q': 'Old Mill', 'state': 'AZ', 'limit': 5}
        )

        if search_response.status_code == 200:
            search_data = search_response.json()
            print(f"✓ Search returned {search_data['count']} matches")
            if search_data['matches']:
                match = search_data['matches'][0]
                print(f"  - Best match: {match['name']} (score: {match['match_score']:.2f})")

        # Test 5: List imported maps
        print("\n5. Testing list imported maps...")
        list_response = requests.get('http://localhost:5000/api/maps/list')

        if list_response.status_code == 200:
            list_data = list_response.json()
            print(f"✓ Found {list_data['total']} imported map(s)")
            if list_data['maps']:
                print(f"  - Latest: {list_data['maps'][0]['filename']}")

    else:
        print(f"✗ Import failed: {import_response.status_code}")
        print(f"  Error: {import_response.json().get('error')}")

else:
    print(f"✗ Parse failed: {response.status_code}")
    print(f"  Error: {response.json().get('error')}")

print("\n" + "=" * 50)
print("Test complete!")
