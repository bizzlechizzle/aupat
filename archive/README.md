# AUPAT Archive Directory

**This directory tracks historical versions of AUPAT**

As of 2025-11-18, the archive directory structure has been cleaned up to reduce repository size and eliminate developer confusion.

---

## Contents

### v0.1.0/ (REMOVED - Available in Git History)

Legacy implementation of AUPAT from the initial version has been **removed from the repository** to keep the codebase clean and focused.

**Status:** ARCHIVED - Removed from repository
**Size:** ~526KB (60 files)
**Removed:** 2025-11-18
**Last Commit:** See git history before this date

**Original Contents:**
- `scripts/` - 19 deprecated Python scripts
- `root_files/` - Old startup scripts and web interface
- `docs/logseq/` - Logseq knowledge base entries

**Why Removed:**
- Code was never imported by current AUPAT (v0.1.2+)
- Database schemas incompatible with current version
- File paths and structures completely changed
- All features have been rewritten
- Caused confusion for developers
- Git history preserves everything if needed

---

## Accessing Historical Code

If you need to reference v0.1.0 code for any reason:

**Option 1: View in Git History**
```bash
# Find the last commit before removal
git log --all --full-history -- "archive/v0.1.0/"

# Checkout the historical code
git checkout <commit-hash> -- archive/v0.1.0/

# View specific file from history
git show <commit-hash>:archive/v0.1.0/scripts/db_import.py
```

**Option 2: View on GitHub**
Navigate to the repository before the cleanup commit and browse the archive directory.

---

## Why Is This Approach Better?

**Benefits of Removal:**
1. **Reduced Repository Size** - 526KB smaller
2. **Eliminated Confusion** - No dead code to stumble upon
3. **Clear Codebase** - Only current, supported code visible
4. **Git History Preserves Everything** - Nothing is lost
5. **Follows Best Practices** - Dead code should not live in main branch

**Git History as Archive:**
- Git is designed for this exact use case
- Historical code is always accessible
- No maintenance burden
- No separate repository needed
- Complete commit history preserved

---

## Current Version

For the current, supported version of AUPAT, see:

- `/home/user/aupat/` - Main project directory
- `README.md` - Project documentation
- `claude.md` - Development rules and processes
- `techguide.md` - Technical reference
- `lilbits.md` - Script documentation
- `CODEBASE_AUDIT_COMPLETE.md` - Architecture overview

---

## Recommendations

**For New Development:**
- Follow patterns in current `scripts/` directory
- Use LILBITS principle (see claude.md)
- Check todo.md for planned work
- Read techguide.md for architecture

**If You Need Old Code:**
1. **Check the current version first** - The feature may already exist in a better form
2. **Read the audit** - See CODEBASE_AUDIT_COMPLETE.md for current architecture
3. **Don't copy directly** - If you need functionality, reimplement following current patterns
4. **Use git history** - Retrieve historical code if absolutely necessary

---

## Future Archival Policy

- Dead code will be removed from the repository
- Git history serves as the permanent archive
- No separate archive repositories will be created
- README.md will document what was removed and when
- Historical code always accessible via `git checkout`

---

## Version History

- **v0.1.0** - Initial implementation (archived, removed 2025-11-18)
- **v0.1.1** - Intermediate version (not separately archived)
- **v0.1.2** - Current stable version
- **v0.1.3** - Map improvements (migration available)
- **v0.1.4** - Import tracking (migration available)

See `docs/v0.1.2/` for current version documentation.

---

**Last Updated:** 2025-11-18
**Maintained By:** Project maintainers
**Status:** Active - Documents archival policy
