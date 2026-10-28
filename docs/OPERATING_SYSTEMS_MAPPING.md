# Operating Systems Mapping

This document maps each required OS concept to its actual implementation.

| OS Concept | Implementation Details | Source Files | Tests |
|------------|------------------------|--------------|-------|
| **Process/Task Lifecycle** | State machine: PENDING→CLAIMED→PROCESSING→COMPLETED, plus RETRY_WAIT, FAILED, CANCELLED. Persistent in DB. | `repositories/__init__.py` (JobRepository), `domain/__init__.py` | test_basic.py |
| **Multithreading** | Bounded thread pool (configurable), Worker threads, daemon threads, graceful shutdown | `concurrency/__init__.py` (WorkerPool, Worker) | Implicit in operation |
| **Producer-Consumer** | Producers: complaint submission/dispatcher. Consumers: worker threads. Bounded Queue + SQLite | `services/__init__.py`, `concurrency/__init__.py` | test_basic.py |
| **Synchronization** | threading.RLock, threading.Lock, DB transactions, optimistic locking (version column), row-level locking | Throughout all modules | test_basic.py |
| **Priority Scheduling** | Priority levels HIGH/MEDIUM/LOW, SQL ORDER BY priority then created_at, dispatcher logic | `repositories/__init__.py` claim_job() | Manual testing |
| **Deadlock Prevention** | Consistent global resource ordering by resource_id, acquire in sorted order, release partial on failure | `resources/__init__.py` acquire_resources() | test_basic.py |
| **Fault Recovery** | Lease expiry (300s), stale job detection, retry with limits, recovery service thread, resource expiration cleanup | `recovery/__init__.py`, `repositories/__init__.py` recover_stale_jobs() | Manual testing |
| **Resource Management** | Capacity tracking, ACTIVE reservations, availability updates in transactions, release on completion/failure/expiry | `resources/__init__.py` | test_basic.py |
| **OS Process Management** | subprocess.Popen (shell=False), stdin/stdout/stderr capture, timeouts, terminate/kill, cleanup, real PID | `process_supervisor/__init__.py` | Manual testing |
| **File Management** | pathlib.Path, atomic replacement (replace()), CSV writing, path validation concepts, cleanup | `reporting/__init__.py` | Manual testing |

**Note:** Application-level jobs are distinct from OS processes. Normal processing uses threads; only report generation uses separate OS process.
