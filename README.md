# Smart Citizen Service Portal (SCSP)

A Fault-Tolerant, Concurrent Citizen Service Management Application implementing genuine Operating Systems concepts.

## Features

- **Citizen Complaint Management**: Register, track, and manage municipal service complaints
- **Multi-threaded Worker Pool**: Configurable bounded worker pool for concurrent processing
- **Producer-Consumer Architecture**: Queue-based job dispatch with database persistence
- **Priority Scheduling**: HIGH/MEDIUM/LOW priority with aging mechanism
- **Resource Management**: Deadlock prevention using consistent resource ordering
- **Fault Recovery**: Stale job detection, retry with backoff, lease expiry
- **Process Supervision**: Real OS process management using subprocess
- **Audit Logging**: Complete audit trail of all operations
- **CSV Export**: Report generation with atomic file operations
- **Desktop GUI**: Tkinter-based interface with real-time updates

## Operating Systems Concepts Implemented

| Concept | Implementation | Location |
|---------|---------------|----------|
| Process/Task Lifecycle | PENDING→CLAIMED→PROCESSING→COMPLETED with FAILED/RETRY_WAIT/CANCELLED | `src/scsp/repositories/__init__.py` |
| Multithreading | Configurable worker pool with threading.Thread | `src/scsp/concurrency/__init__.py` |
| Producer-Consumer | Bounded Queue + SQLite persistence | `src/scsp/services/__init__.py`, `src/scsp/concurrency/__init__.py` |
| Synchronization | threading.Lock/RLock, DB transactions, optimistic locking | Throughout |
| Priority Scheduling | Priority-based dispatch with deterministic ordering | `src/scsp/repositories/__init__.py` |
| Deadlock Prevention | Consistent resource ordering, release on failure | `src/scsp/resources/__init__.py` |
| Fault Recovery | Stale lease detection, retry limits, recovery service | `src/scsp/recovery/__init__.py` |
| Resource Management | Capacity tracking, reservations, expiration | `src/scsp/resources/__init__.py` |
| OS Process Management | subprocess.Popen with lifecycle monitoring | `src/scsp/process_supervisor/__init__.py` |
| File Management | pathlib, atomic writes, safe paths | `src/scsp/reporting/__init__.py` |

## Requirements

- Python 3.12 or later
- Windows/Linux/macOS (tested on Windows)
- No external dependencies required (uses only standard library)

## Quick Start

### Windows
1. Double-click `run.bat` or run in terminal: `run.bat`
2. The GUI will launch

### Manual
```bash
cd Smart-Citizen-Service-Portal
set PYTHONPATH=src
python main.py
```

## Running Tests
```bash
test.bat
# or
python -m pytest tests/ -v
```

## Database

Database stored in OS-appropriate app data directory:
- Windows: `%LOCALAPPDATA%\SmartCitizenServicePortal\scsp.db`
- Linux: `~/.local/share/SmartCitizenServicePortal/scsp.db`

## Architecture

- `src/scsp/ui/` - Tkinter GUI (separate from logic)
- `src/scsp/services/` - Business logic
- `src/scsp/repositories/` - Data access
- `src/scsp/database/` - Schema and connections
- `src/scsp/concurrency/` - Threading/worker pool
- `src/scsp/resources/` - Resource management
- `src/scsp/recovery/` - Fault recovery
- `src/scsp/process_supervisor/` - OS process management
- `src/scsp/audit/` - Audit logging
- `src/scsp/reporting/` - Reports and CSV export

## Notes

- Jobs persist in SQLite - survive application crashes
- Queue full does not discard jobs - persisted to DB
- Resource allocation uses deadlock prevention
- All DB operations use transactions with foreign keys enabled
- GUI updates only from main thread using `after()`
