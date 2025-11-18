# AUPAT Archive Directory

**DO NOT USE CODE FROM THIS DIRECTORY**

This directory contains archived code from previous versions of AUPAT. The code here is **not compatible** with the current version and is kept for **historical reference only**.

---

## Contents

### v0.1.0/
Legacy implementation of AUPAT from the initial version.

**Status:** DEPRECATED - Do not use
**Size:** ~526KB
**Last Updated:** Historical (before v0.1.2)

**Contents:**
- `scripts/` - 19 deprecated Python scripts
- `root_files/` - Old startup scripts and web interface
- `docs/logseq/` - Logseq knowledge base entries

**Important Notes:**
- This code is NOT imported by current AUPAT (v0.1.2+)
- Database schemas are incompatible
- File paths and structures have changed
- Many features have been rewritten

---

## Why Is This Here?

The archive directory serves as:

1. **Historical Reference** - Documentation of how the system evolved
2. **Learning Resource** - See what approaches were tried and abandoned
3. **Migration Context** - Understanding what changed between versions

---

## Current Version

For the current, supported version of AUPAT, see:

- `/home/user/aupat/` - Main project directory
- `README.md` - Project documentation
- `claude.md` - Development rules and processes
- `techguide.md` - Technical reference
- `lilbits.md` - Script documentation

---

## If You Need Old Code

If you truly need to reference or use old code:

1. **Check the current version first** - The feature may already exist in a better form
2. **Read the audit** - See CODEBASE_AUDIT_COMPLETE.md for current architecture
3. **Ask questions** - Consult todo.md for known gaps and planned features
4. **Don't copy directly** - If you need functionality, reimplement following current patterns

---

## Recommendations

**For New Development:**
- Follow patterns in current `scripts/` directory
- Use LILBITS principle (see claude.md)
- Check todo.md for planned work
- Read techguide.md for architecture

**For Bug Fixes:**
- Fix in current codebase only
- Do not backport to v0.1.0 (unsupported)

**For Questions:**
- See lilbits.md for script documentation
- See techguide.md for technical details
- See docs/dependency_map.md for file relationships

---

## Archival Policy

- Old versions are kept indefinitely for reference
- No maintenance or bug fixes will be made
- Code is read-only and should not be modified
- If you need something from here, reimplement it properly in the current version

---

## Version History

- **v0.1.0** - Initial implementation (archived)
- **v0.1.1** - Intermediate version (not archived)
- **v0.1.2** - Current stable version
- **v0.1.3** - Map improvements (migration available)
- **v0.1.4** - Import tracking (migration available)

See `docs/v0.1.2/` for current version documentation.

---

**Last Updated:** 2025-11-18
**Maintained By:** Project maintainers
**Status:** Read-only archive, no active maintenance
