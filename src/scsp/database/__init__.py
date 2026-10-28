"""Database schema and connection management"""
import sqlite3
import threading
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager

class DatabaseManager:
    _lock = threading.RLock()
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._local = threading.local()
        self._init_schema()
    
    def get_connection(self):
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            conn = sqlite3.connect(str(self.db_path), timeout=30.0, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA busy_timeout = 30000")
            self._local.conn = conn
        return self._local.conn
    
    @contextmanager
    def transaction(self):
        conn = self.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    
    def _init_schema(self):
        with self.transaction() as conn:
            cur = conn.cursor()
            # Schema versioning
            cur.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Citizens
            cur.execute("""
                CREATE TABLE IF NOT EXISTS citizens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone TEXT,
                    email TEXT,
                    address TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Departments
            cur.execute("""
                CREATE TABLE IF NOT EXISTS departments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    capacity INTEGER DEFAULT 10,
                    active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Complaints
            cur.execute("""
                CREATE TABLE IF NOT EXISTS complaints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    citizen_id INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    location TEXT,
                    priority TEXT DEFAULT 'MEDIUM' CHECK(priority IN ('LOW','MEDIUM','HIGH')),
                    status TEXT DEFAULT 'PENDING' CHECK(status IN ('PENDING','ASSIGNED','PROCESSING','COMPLETED','CANCELLED','REJECTED')),
                    assigned_department_id INTEGER,
                    assigned_to TEXT,
                    version INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (citizen_id) REFERENCES citizens(id),
                    FOREIGN KEY (assigned_department_id) REFERENCES departments(id)
                )
            """)
            # Processing jobs
            cur.execute("""
                CREATE TABLE IF NOT EXISTS processing_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    complaint_id INTEGER NOT NULL UNIQUE,
                    state TEXT DEFAULT 'PENDING' CHECK(state IN ('PENDING','CLAIMED','PROCESSING','RETRY_WAIT','COMPLETED','FAILED','CANCELLED')),
                    assigned_worker TEXT,
                    priority TEXT DEFAULT 'MEDIUM' CHECK(priority IN ('LOW','MEDIUM','HIGH')),
                    attempt_count INTEGER DEFAULT 0,
                    max_attempts INTEGER DEFAULT 5,
                    last_error TEXT,
                    lease_expires_at TIMESTAMP,
                    claimed_at TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    version INTEGER DEFAULT 1,
                    FOREIGN KEY (complaint_id) REFERENCES complaints(id)
                )
            """)
            # Resources
            cur.execute("""
                CREATE TABLE IF NOT EXISTS resources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    type TEXT NOT NULL,
                    total_capacity INTEGER NOT NULL,
                    available INTEGER NOT NULL,
                    exclusive INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Resource reservations
            cur.execute("""
                CREATE TABLE IF NOT EXISTS resource_reservations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL,
                    resource_id INTEGER NOT NULL,
                    quantity INTEGER DEFAULT 1,
                    reserved_by TEXT,
                    reserved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    released_at TIMESTAMP,
                    expires_at TIMESTAMP,
                    status TEXT DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE','RELEASED','EXPIRED')),
                    FOREIGN KEY (job_id) REFERENCES processing_jobs(id),
                    FOREIGN KEY (resource_id) REFERENCES resources(id)
                )
            """)
            # Complaint status history
            cur.execute("""
                CREATE TABLE IF NOT EXISTS complaint_status_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    complaint_id INTEGER NOT NULL,
                    old_status TEXT,
                    new_status TEXT NOT NULL,
                    changed_by TEXT,
                    reason TEXT,
                    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (complaint_id) REFERENCES complaints(id)
                )
            """)
            # Audit events
            cur.execute("""
                CREATE TABLE IF NOT EXISTS audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    entity_type TEXT,
                    entity_id INTEGER,
                    actor TEXT,
                    details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Processing attempts
            cur.execute("""
                CREATE TABLE IF NOT EXISTS processing_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL,
                    worker_id TEXT,
                    attempt_number INTEGER,
                    status TEXT,
                    error_message TEXT,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ended_at TIMESTAMP,
                    duration_ms INTEGER,
                    FOREIGN KEY (job_id) REFERENCES processing_jobs(id)
                )
            """)
            # Application settings
            cur.execute("""
                CREATE TABLE IF NOT EXISTS application_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Indexes
            cur.execute("CREATE INDEX IF NOT EXISTS idx_jobs_state ON processing_jobs(state)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_jobs_priority ON processing_jobs(priority)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_complaints_status ON complaints(status)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_complaints_citizen ON complaints(citizen_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_events(created_at)")
            # Insert initial data
            cur.execute("INSERT OR IGNORE INTO schema_version (version) VALUES (1)")
            cur.execute("INSERT OR IGNORE INTO departments (name, description) VALUES ('Water Supply','Water and pipeline issues')")
            cur.execute("INSERT OR IGNORE INTO departments (name, description) VALUES ('Electricity','Power supply issues')")
            cur.execute("INSERT OR IGNORE INTO departments (name, description) VALUES ('Roads','Road maintenance and repairs')")
            cur.execute("INSERT OR IGNORE INTO departments (name, description) VALUES ('Sanitation','Sanitation and hygiene')")
            cur.execute("INSERT OR IGNORE INTO departments (name, description) VALUES ('Waste Collection','Garbage collection')")
            cur.execute("INSERT OR IGNORE INTO departments (name, description) VALUES ('Drainage','Drainage systems')")
            cur.execute("INSERT OR IGNORE INTO departments (name, description) VALUES ('Streetlights','Public lighting')")
            cur.execute("INSERT OR IGNORE INTO resources (name, type, total_capacity, available) VALUES ('Repair Vehicle','vehicle',5,5)")
            cur.execute("INSERT OR IGNORE INTO resources (name, type, total_capacity, available) VALUES ('Technician','personnel',10,10)")
            cur.execute("INSERT OR IGNORE INTO resources (name, type, total_capacity, available) VALUES ('Equipment Kit','equipment',8,8)")
