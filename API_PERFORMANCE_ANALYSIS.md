# AUPAT API Performance Analysis - Timeout Issues

## Summary
Analysis of 4 timing-out API endpoints identifies N+1 query problems, missing indexes, inefficient queries, and pagination issues.

---

## 1. /api/locations (GET)
**File:** `/home/user/aupat/scripts/api_routes_v012.py` (Lines 1272-1314)

### Issues Found:
- **No Pagination**: Returns ALL locations without limit
- **Full Table Scan**: `SELECT * FROM locations ORDER BY loc_name` scans entire table
- **Missing WHERE Clause**: No filtering capability from API

### Code:
```python
@api_v012.route('/locations', methods=['GET', 'POST'])
def locations_list_create():
    if request.method == 'GET':
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM locations ORDER BY loc_name")  # ← FULL TABLE SCAN
            rows = cursor.fetchall()
            conn.close()

            locations_list = [dict(row) for row in rows]
            return jsonify(locations_list), 200
```

### Root Causes:
1. No LIMIT clause - if database has 10,000+ locations, fetches all at once
2. `SELECT *` loads all columns including large fields
3. No indexing on loc_name helps only slightly since full scan happens
4. Inefficient for large datasets

### Performance Impact:
- **O(n)** complexity where n = total locations
- Memory usage grows linearly with total records
- Network payload includes all locations

### Recommendations:
1. Add pagination: `LIMIT ? OFFSET ?`
2. Add query parameters: `limit` (default 50, max 200) and `offset`
3. Use indexed columns in WHERE clause for filtering
4. Consider returning ID + name only for list view

---

## 2. /api/locations/autocomplete/sub_type (GET)
**File:** `/home/user/aupat/scripts/api_routes_v012.py` (Lines 1546-1613)

### Issues Found:
- **Inefficient GROUP BY**: Uses `LOWER()` function in GROUP BY
- **No Column-Specific Indexing**: Index on full location record, not on grouped columns
- **Multiple Database Calls**: Executes query for each autocomplete field

### Code:
```python
@api_v012.route('/locations/autocomplete/<field>', methods=['GET'])
def location_autocomplete(field):
    # For sub_type with optional type filter:
    if field == 'sub_type':
        type_filter = request.args.get('type')
        if type_filter:
            cursor.execute(f"""
                SELECT {field}, COUNT(*) as count
                FROM locations
                WHERE {field} IS NOT NULL
                AND {field} != ''
                AND type = ?
                GROUP BY LOWER({field})  # ← LOWER() IN GROUP BY - NOT INDEXED
                ORDER BY count DESC, {field} ASC
                LIMIT ?
            """, (type_filter.lower(), limit))
```

### Root Causes:
1. `GROUP BY LOWER({field})` is not indexed - forces full scan + grouping
2. `WHERE {field} != ''` and `{field} IS NOT NULL` not optimized
3. No composite index on (type, sub_type) for filtered queries
4. SQLite must evaluate LOWER() function for every row

### Performance Impact:
- **O(n)** full table scan even with small result limit
- LOWER() function called for every location row
- Repeated calls for autocomplete fields (type, sub_type, state, etc.)

### Recommendations:
1. Create index: `CREATE INDEX idx_locations_sub_type_lower ON locations(type, LOWER(sub_type))`
2. Normalize data to lowercase in database or app layer
3. Consider caching autocomplete results (rarely changes)
4. Add filtering to reduce scan: `WHERE sub_type IS NOT NULL`

---

## 3. /api/map/markers (GET)
**File:** `/home/user/aupat/scripts/api_maps.py` (Lines 127-219)

### Issues Found:
- **No Index on GPS Coordinates**: BETWEEN queries on (lat, lon) without proper index
- **No Bounding Box Index**: Even with `idx_locations_gps`, BETWEEN is O(n) for large ranges
- **Optional Bounds Parameter**: Without bounds, fetches all GPS locations without limit

### Code:
```python
@api_v012.route('/map/markers', methods=['GET'])
def get_map_markers():
    bounds = request.args.get('bounds')
    limit = request.args.get('limit', type=int)
    
    if bounds:
        min_lat, min_lon, max_lat, max_lon = map(float, bounds.split(','))
        if limit:
            cursor.execute("""
                SELECT loc_uuid, loc_name, lat, lon, type, state
                FROM locations
                WHERE lat IS NOT NULL AND lon IS NOT NULL
                AND lat BETWEEN ? AND ?  # ← BETWEEN on GPS without proper spatial index
                AND lon BETWEEN ? AND ?
                LIMIT ?
            """, (min_lat, max_lat, min_lon, max_lon, limit))
    else:
        cursor.execute("""
            SELECT loc_uuid, loc_name, lat, lon, type, state
            FROM locations
            WHERE lat IS NOT NULL AND lon IS NOT NULL  # ← FULL SCAN IF NO BOUNDS
        """)
```

### Root Causes:
1. SQLite doesn't have native spatial indexing (R-tree needs PRAGMA)
2. `idx_locations_gps` helps but BETWEEN still scans matching rows
3. No limit when bounds not provided = full scan of all locations
4. Large bounding box = scanning thousands of potential matches

### Performance Impact:
- **O(n)** in worst case (no bounds filter)
- **O(m)** where m = locations in bounding box (usually 10-30% of total)
- Network payload includes all markers even if invisible on map

### Database Schema Issue:
```python
# Current index (from db_migrate_v012.py, line 522)
"CREATE INDEX IF NOT EXISTS idx_locations_gps ON locations(lat, lon) WHERE lat IS NOT NULL"
```
This is a partial index but not optimized for BETWEEN queries.

### Recommendations:
1. Require bounds parameter (don't allow full scan)
2. Increase hard limit: `min(limit, 200)` per request
3. Cluster locations by zoom level in frontend
4. Add R-tree spatial index for PostgreSQL later
5. Cache grid-based results (10x10 degree grid)

---

## 4. /api/bookmarks (GET)
**File:** `/home/user/aupat/scripts/api_routes_bookmarks.py` (Lines 180-297)

### Issues Found:
- **N+1 Pattern**: Executes separate count query for pagination
- **Repeated Filter Queries**: Builds same WHERE clause twice (once for data, once for count)
- **LIKE Query Without Indexing**: Full-text search on title/description/URL without indexes
- **Missing Bookmark Indexes**: No indexes on folder, loc_uuid, or search columns

### Code:
```python
@bookmarks_bp.route('/api/bookmarks', methods=['GET'])
def list_bookmarks():
    # Build query for data
    query = "SELECT * FROM bookmarks WHERE 1=1"
    params = []
    
    if search:
        query += " AND (title LIKE ? OR description LIKE ? OR url LIKE ?)"  # ← NO INDEX ON THESE
        search_pattern = f"%{search}%"
        params.extend([search_pattern, search_pattern, search_pattern])
    
    query += f" ORDER BY {order_clause} LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    # SEPARATE count query - N+1 PATTERN
    count_query = "SELECT COUNT(*) as total FROM bookmarks WHERE 1=1"
    count_params = []
    
    # Rebuild WHERE clause AGAIN  ← DUPLICATE LOGIC
    if folder:
        count_query += " AND folder = ?"
        count_params.append(folder)
    # ... repeat for loc_uuid, search, etc.
    
    cursor.execute(count_query, count_params)  # ← SECOND DATABASE CALL
    total = cursor.fetchone()['total']
```

### Root Causes:
1. **N+1 Query Problem**: Two separate database calls per request
   - One for paginated results
   - One for total count (needed for pagination UI)
2. **No Text Index**: LIKE searches force full table scan
3. **No Index on Foreign Keys**: `loc_uuid` filter has no index
4. **No Index on folder**: Category filtering unindexed

### Missing Indexes:
```sql
-- Should exist but are NOT created in db_migrate_v012.py:
CREATE INDEX idx_bookmarks_folder ON bookmarks(folder);
CREATE INDEX idx_bookmarks_loc_uuid ON bookmarks(loc_uuid);
CREATE INDEX idx_bookmarks_title ON bookmarks(title);
-- Not practical: CREATE INDEX idx_bookmarks_url ON bookmarks(url);
```

### Performance Impact:
- **2 queries per request** instead of 1
- **O(n) full scan** for LIKE searches
- Slower pagination on large datasets (100,000+ bookmarks)
- Network round trips doubled

### Database Issue:
Bookmarks table has no indexes in schema (db_migrate_v012.py doesn't create them).

### Recommendations:
1. **Combine queries**: Use `COUNT(*) OVER () as total` window function (SQLite 3.25+)
   ```sql
   SELECT *, COUNT(*) OVER () as total FROM bookmarks ... LIMIT ? OFFSET ?
   ```
2. **Add indexes**:
   ```sql
   CREATE INDEX idx_bookmarks_folder ON bookmarks(folder);
   CREATE INDEX idx_bookmarks_loc_uuid ON bookmarks(loc_uuid);
   CREATE INDEX idx_bookmarks_visit_count ON bookmarks(visit_count DESC);
   ```
3. **Use FTS5** for search: `CREATE VIRTUAL TABLE bookmarks_fts USING fts5(title, description, url)`
4. **Limit search**: Require min 2-3 characters before searching

---

## Summary Table

| Endpoint | Issue | Severity | Root Cause | Fix |
|----------|-------|----------|-----------|-----|
| `/api/locations` | No pagination | HIGH | `SELECT *` without LIMIT | Add LIMIT/OFFSET |
| `/api/locations/autocomplete/sub_type` | Full table scan + LOWER() in GROUP BY | HIGH | No expression index | Create expression index |
| `/api/map/markers` | No required bounds, BETWEEN unoptimized | HIGH | Optional bounds, spatial scan | Require bounds, limit results |
| `/api/bookmarks` | N+1 query + no search indexes | MEDIUM | Two separate queries + LIKE | Use window function, create FTS5 |

---

## Quick Wins (Priority Order)

### 1. Add pagination to /api/locations (15 min)
```python
limit = min(int(request.args.get('limit', 50)), 200)
offset = int(request.args.get('offset', 0))
cursor.execute("SELECT * FROM locations ORDER BY loc_name LIMIT ? OFFSET ?", (limit, offset))
```

### 2. Create missing indexes (5 min)
```sql
CREATE INDEX idx_bookmarks_folder ON bookmarks(folder);
CREATE INDEX idx_bookmarks_loc_uuid ON bookmarks(loc_uuid);
CREATE INDEX idx_locations_sub_type ON locations(sub_type) WHERE sub_type IS NOT NULL;
CREATE INDEX idx_locations_type_sub_type ON locations(type, sub_type);
```

### 3. Combine N+1 queries in bookmarks (10 min)
```python
# SQLite 3.25+
cursor.execute("""
    SELECT *, COUNT(*) OVER () as total FROM bookmarks 
    WHERE ... LIMIT ? OFFSET ?
""")
```

### 4. Require bounds in map/markers (5 min)
```python
if not bounds:
    return jsonify({'error': 'bounds parameter required'}), 400
```

---

## Database Optimization Checklist
- [ ] Add pagination to /api/locations
- [ ] Create missing indexes on bookmarks table  
- [ ] Add composite index (type, sub_type)
- [ ] Require bounds parameter in /api/map/markers
- [ ] Replace N+1 count query with OVER window function
- [ ] Monitor slow queries with PRAGMA log_metrics
- [ ] Consider FTS5 for bookmark search

