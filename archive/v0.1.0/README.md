# AUPAT v0.1.0/v0.1.1 Archive

This directory contains historical code and documentation from AUPAT v0.1.0 and v0.1.1.

## Archived: November 2025

**Reason for archival**: v0.1.2 introduced a complete architectural change:
- Old: Monolithic web interface with local file processing
- New: Microservices architecture (Docker Compose) with Immich + ArchiveBox integration

## Directory Structure

```
v0.1.0/
├── scripts/           # Old CLI pipeline scripts
├── docs/              # Old Logseq documentation
└── root_files/        # Old root-level utilities and web interface
```

## Old Architecture (v0.1.0/v0.1.1)

- **web_interface.py**: Flask web UI with embedded import pipeline
- **CLI Pipeline**: db_import.py -> db_organize.py -> db_folder.py -> db_ingest.py -> db_verify.py
- **Local Processing**: All metadata extraction and file management done locally
- **No External Services**: Self-contained Python application

## New Architecture (v0.1.2)

- **Docker Compose**: 6-service orchestration (AUPAT Core, Immich, ArchiveBox, PostgreSQL, Redis, ML)
- **Service Adapters**: Immich for photo storage, ArchiveBox for web archiving
- **REST API**: api_routes_v012.py provides endpoints for desktop app
- **Microservices Pattern**: Separation of concerns with external service integration

## Migration Notes

If you need to run old v0.1.0 code:

1. Copy scripts from archive/v0.1.0/scripts/ to a separate directory
2. Install old requirements (no Docker, no Immich/ArchiveBox dependencies)
3. Run setup.sh from archive/v0.1.0/root_files/
4. Use web_interface.py or CLI pipeline as documented in old README

**Not recommended for new deployments. Use v0.1.2 instead.**

## Reference Documentation

Old documentation preserved in archive/v0.1.0/docs/logseq/pages/:
- claude.md - AI collaboration guide
- claudecode.md - Development methodology
- db_*.md - Script specifications
- *_table.md - Database schemas

These docs describe the v0.1.0 architecture and are kept for historical reference only.
