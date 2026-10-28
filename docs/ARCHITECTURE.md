# Architecture Documentation

## System Overview
Smart Citizen Service Portal is a fault-tolerant, concurrent desktop application using Tkinter, SQLite, threading, and multiprocessing concepts.

## Layered Architecture
1. **UI Layer** (`ui/`) - Tkinter GUI, main thread only for widgets
2. **Service Layer** (`services/`) - Business logic, orchestration
3. **Repository Layer** (`repositories/`) - Data access abstraction
4. **Domain Layer** (`domain/`) - Models and enums
5. **Infrastructure** - Database, concurrency, resources, recovery

## Concurrency Model
- Main thread: GUI event loop
- Worker threads: Process jobs from queue
- Dispatcher thread: Claims jobs from DB and dispatches
- Recovery thread: Monitors for stale jobs
- All communication thread-safe via locks/queues

## Data Persistence
SQLite with WAL mode, foreign keys enabled, transactions for atomicity.
