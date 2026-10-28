"""Repository layer for data access"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

class ComplaintRepository:
    def __init__(self, db_manager):
        self.db = db_manager
    
    def create_citizen(self, name: str, phone: str = None, email: str = None, address: str = None) -> int:
        with self.db.transaction() as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO citizens (name, phone, email, address) VALUES (?,?,?,?)",
                       (name, phone, email, address))
            return cur.lastrowid
    
    def create_complaint(self, citizen_id: int, category: str, title: str, description: str, 
                        location: str = None, priority: str = 'MEDIUM') -> int:
        with self.db.transaction() as conn:
            cur = conn.cursor()
            cur.execute("""INSERT INTO complaints (citizen_id, category, title, description, location, priority)
                          VALUES (?,?,?,?,?,?)""", (citizen_id, category, title, description, location, priority))
            complaint_id = cur.lastrowid
            cur.execute("INSERT INTO complaint_status_history (complaint_id, old_status, new_status, changed_by) VALUES (?,?,?,?)",
                       (complaint_id, None, 'PENDING', 'SYSTEM'))
            return complaint_id
    
    def get_complaint(self, complaint_id: int) -> Optional[Dict]:
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM complaints WHERE id = ?", (complaint_id,))
        row = cur.fetchone()
        return dict(row) if row else None
    
    def list_complaints(self, limit: int = 100) -> List[Dict]:
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("""SELECT c.*, ci.name as citizen_name, d.name as department_name 
                      FROM complaints c 
                      LEFT JOIN citizens ci ON c.citizen_id = ci.id
                      LEFT JOIN departments d ON c.assigned_department_id = d.id
                      ORDER BY c.created_at DESC LIMIT ?""", (limit,))
        return [dict(row) for row in cur.fetchall()]
    
    def get_stats(self) -> Dict[str, int]:
        conn = self.db.get_connection()
        cur = conn.cursor()
        stats = {}
        for status in ['PENDING', 'PROCESSING', 'COMPLETED', 'FAILED']:
            cur.execute("SELECT COUNT(*) as cnt FROM complaints WHERE status = ?", (status,))
            stats[status.lower()] = cur.fetchone()['cnt']
        cur.execute("SELECT COUNT(*) as cnt FROM complaints")
        stats['total'] = cur.fetchone()['cnt']
        return stats

class JobRepository:
    def __init__(self, db_manager):
        self.db = db_manager
    
    def create_job(self, complaint_id: int, priority: str = 'MEDIUM') -> int:
        with self.db.transaction() as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO processing_jobs (complaint_id, priority, state) VALUES (?,?,?)",
                       (complaint_id, priority, 'PENDING'))
            return cur.lastrowid
    
    def claim_job(self, worker_id: str) -> Optional[Dict]:
        with self.db.transaction() as conn:
            cur = conn.cursor()
            # Atomic claim with optimistic locking
            cur.execute("""SELECT * FROM processing_jobs 
                          WHERE state IN ('PENDING','RETRY_WAIT') 
                          AND (lease_expires_at IS NULL OR lease_expires_at < datetime('now'))
                          ORDER BY 
                            CASE priority WHEN 'HIGH' THEN 1 WHEN 'MEDIUM' THEN 2 WHEN 'LOW' THEN 3 END,
                            created_at ASC LIMIT 1""")
            row = cur.fetchone()
            if not row:
                return None
            job = dict(row)
            # Try to claim
            cur.execute("""UPDATE processing_jobs 
                          SET state='CLAIMED', assigned_worker=?, claimed_at=datetime('now'),
                              lease_expires_at=datetime('now', '+300 seconds'),
                              attempt_count=attempt_count+1, version=version+1, updated_at=datetime('now')
                          WHERE id=? AND version=? AND state IN ('PENDING','RETRY_WAIT')""",
                       (worker_id, job['id'], job['version']))
            if cur.rowcount == 0:
                return None  # Lost race
            cur.execute("SELECT * FROM processing_jobs WHERE id = ?", (job['id'],))
            return dict(cur.fetchone())
    
    def get_pending_jobs(self) -> List[Dict]:
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM processing_jobs WHERE state IN ('PENDING','RETRY_WAIT') ORDER BY created_at")
        return [dict(row) for row in cur.fetchall()]
    
    def update_state(self, job_id: int, new_state: str, error: str = None) -> bool:
        with self.db.transaction() as conn:
            cur = conn.cursor()
            if new_state == 'PROCESSING':
                cur.execute("UPDATE processing_jobs SET state=?, started_at=datetime('now'), updated_at=datetime('now') WHERE id=?",
                           (new_state, job_id))
            elif new_state == 'COMPLETED':
                cur.execute("UPDATE processing_jobs SET state=?, completed_at=datetime('now'), updated_at=datetime('now') WHERE id=?",
                           (new_state, job_id))
            elif new_state == 'FAILED':
                cur.execute("UPDATE processing_jobs SET state=?, last_error=?, completed_at=datetime('now'), updated_at=datetime('now') WHERE id=?",
                           (new_state, error, job_id))
            else:
                cur.execute("UPDATE processing_jobs SET state=?, updated_at=datetime('now') WHERE id=?",
                           (new_state, job_id))
            return cur.rowcount > 0
    
    def recover_stale_jobs(self, timeout_seconds: int = 300) -> int:
        with self.db.transaction() as conn:
            cur = conn.cursor()
            cur.execute("""UPDATE processing_jobs 
                          SET state='RETRY_WAIT', assigned_worker=NULL, lease_expires_at=NULL, updated_at=datetime('now')
                          WHERE state IN ('CLAIMED','PROCESSING') 
                          AND lease_expires_at < datetime('now')""")
            return cur.rowcount
