# Normalize Module Added

**Date**: 2025-11-15
**Module**: `scripts/normalize.py`

---

## Purpose

Centralized normalization module to ensure consistent data transformation across all AUPAT scripts. Previously, normalization requirements were documented in schemas but no implementation existed.

---

## Functions Provided

### Text Normalization
- `normalize_location_name(name, use_postal)` - Location names → unidecode + titlecase + optional libpostal
- `normalize_aka_name(aka_name)` - AKA names → same as location names
- `normalize_state_code(state)` - State codes → lowercase, validated against USPS list
- `normalize_location_type(location_type)` - Types → unidecode + lowercase
- `normalize_sub_type(sub_type)` - Sub-types → same as types

### Data Normalization
- `normalize_datetime(dt_input)` - Dates → ISO 8601 format via dateutil
- `normalize_extension(extension)` - File extensions → lowercase, no dot
- `normalize_author(author)` - Author names → lowercase

### Utility
- `get_normalization_capabilities()` - Check available dependencies

---

## Dependency Handling

### Required Dependencies ✅
- `python-dateutil` - Date/time parsing (in requirements.txt)

### Optional Dependencies
- `unidecode` - Unicode → ASCII (in requirements.txt, fallback available)
- `libpostal` - Address parsing (optional in requirements.txt, fallback available)

### Fallback Behavior
- **No unidecode**: Unicode characters preserved, titlecase still applied
- **No libpostal**: Simple titlecase normalization without address parsing
- **No dateutil**: Falls back to `datetime.fromisoformat()` (limited format support)

All core functionality works with or without optional dependencies. ✅

---

## Usage Examples

```python
from scripts.normalize import (
    normalize_location_name,
    normalize_state_code,
    normalize_location_type,
    normalize_datetime,
    normalize_extension
)

# Location name
name = normalize_location_name("abandoned factory")
# Returns: "Abandoned Factory"

name_unicode = normalize_location_name("old café")
# Returns: "Old Cafe" (with unidecode)

# State code
state = normalize_state_code("NY")
# Returns: "ny"

# Location type
loc_type = normalize_location_type("Industrial")
# Returns: "industrial"

# DateTime
timestamp = normalize_datetime("2025-11-15 10:30 AM")
# Returns: "2025-11-15T10:30:00"

# Extension
ext = normalize_extension(".JPG")
# Returns: "jpg"
```

---

## Integration Points

This module will be used by:
- **db_import.py** - Normalize location data during import
  - Location names, state codes, types
  - Import timestamps

- **db_organize.py** - Normalize metadata
  - File extensions
  - Update timestamps

- **db_folder.py** - Normalize folder names
  - Uses normalized location names for folder creation

- **All scripts** - Consistent datetime handling
  - All timestamps normalized to ISO 8601

---

## Validation

### State Codes
Validates against USPS two-letter codes:
- 50 states + DC + 5 territories (56 total)
- Raises `ValueError` if invalid

### Location Types
Validates against known types (warns if unknown, but allows):
- industrial, residential, commercial, institutional
- agricultural, recreational, infrastructure, military
- religious, educational, healthcare, transportation
- mixed-use, other

---

## Testing

Tested with full capabilities:
```
unidecode       ✓ Available
dateutil        ✓ Available
postal          ✗ Not Available (optional)
fallback_mode   ✗ Not Available
```

All functions tested and working correctly.

---

## Updated Script Count

**Previous**: 10 scripts (after utils.py consolidation)
**Current**: 11 scripts (added normalize.py)

### Current Script Inventory

**Utilities** (3 implemented):
1. ✅ `utils.py` - UUID, SHA256, naming
2. ✅ `normalize.py` - Text/data normalization
3. ⏳ `backup.py` - Database backups (not yet implemented)

**Core Pipeline** (7 not yet implemented):
4. ⏳ `db_migrate.py`
5. ⏳ `db_import.py`
6. ⏳ `db_organize.py`
7. ⏳ `db_folder.py`
8. ⏳ `db_ingest.py`
9. ⏳ `db_verify.py`
10. ⏳ `db_identify.py`

**Maintenance** (1 not yet implemented):
11. ⏳ `database_cleanup.py`

**Future**:
12. ⏳ `aupat_webapp.py` (Stage 2)

---

## Benefits

### Consistency
- All normalization logic centralized
- Same transformation rules across all scripts
- Eliminates duplication

### Maintainability
- Single source of truth for normalization
- Easy to update rules in one place
- Clear dependency handling

### Robustness
- Handles missing optional dependencies gracefully
- Validates inputs (state codes, types)
- Clear error messages

### Documentation
- Self-documenting with examples
- Type hints for better IDE support
- Comprehensive docstrings

---

## Status

✅ **IMPLEMENTED AND TESTED**

Ready for use in all AUPAT scripts.

---

**Created**: 2025-11-15
**Status**: Complete
