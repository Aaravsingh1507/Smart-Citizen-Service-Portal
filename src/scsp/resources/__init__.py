"""Resource manager with deadlock prevention"""
import threading
import time
from typing import List, Dict, Optional
from contextlib import contextmanager

class ResourceManager:
    def __init__(self, db_manager):
        self.db = db_manager
        self._global_lock = threading.RLock()
        # Resource ordering for deadlock prevention
        self.resource_order = {}
    
    def initialize_ordering(self):
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM resources ORDER BY id")
        for i, row in enumerate(cur.fetchall()):
            self.resource_order[row['id']] = i
    
    def acquire_resources(self, job_id: int, resource_requests: List[Dict], 
                         worker_id: str, timeout: float = 5.0) -> bool:
        """
        Acquire multiple resources with consistent ordering to prevent deadlock
        Release partially acquired resources on failure
        """
        with self._global_lock:
            # Sort by resource order for deadlock prevention
            sorted_requests = sorted(resource_requests, 
                                   key=lambda x: self.resource_order.get(x['resource_id'], 999))
            
            acquired = []
            try:
                with self.db.transaction() as conn:
                    cur = conn.cursor()
                    for req in sorted_requests:
                        res_id = req['resource_id']
                        qty = req.get('quantity', 1)
                        # Check availability
                        cur.execute("SELECT available, exclusive FROM resources WHERE id = ? FOR UPDATE", (res_id,))
                        res = cur.fetchone()
                        if not res or res['available'] < qty:
                            raise Exception(f"Resource {res_id} not available")
                        # Reserve
                        cur.execute("UPDATE resources SET available = available - ? WHERE id = ?", (qty, res_id))
                        cur.execute("""INSERT INTO resource_reservations 
                                      (job_id, resource_id, quantity, reserved_by, expires_at)
                                      VALUES (?,?,?,?, datetime('now', '+300 seconds'))""",
                                   (job_id, res_id, qty, worker_id))
                        acquired.append((res_id, qty))
                    return True
            except Exception as e:
                # Release partially acquired resources
                if acquired:
                    self._release_acquired(acquired)
                raise
    
    def _release_acquired(self, acquired: List):
        try:
            with self.db.transaction() as conn:
                cur = conn.cursor()
                for res_id, qty in acquired:
                    cur.execute("UPDATE resources SET available = available + ? WHERE id = ?", (qty, res_id))
        except:
            pass
    
    def release_resources(self, job_id: int):
        with self._global_lock:
            with self.db.transaction() as conn:
                cur = conn.cursor()
                # Get active reservations
                cur.execute("SELECT resource_id, quantity FROM resource_reservations WHERE job_id = ? AND status = 'ACTIVE'", (job_id,))
                reservations = cur.fetchall()
                for r in reservations:
                    cur.execute("UPDATE resources SET available = available + ? WHERE id = ?", (r['quantity'], r['resource_id']))
                cur.execute("UPDATE resource_reservations SET status='RELEASED', released_at=datetime('now') WHERE job_id = ? AND status='ACTIVE'", (job_id,))
    
    def release_expired_reservations(self):
        with self.db.transaction() as conn:
            cur = conn.cursor()
            cur.execute("""SELECT DISTINCT job_id FROM resource_reservations 
                          WHERE status='ACTIVE' AND expires_at < datetime('now')""")
            expired_jobs = [r['job_id'] for r in cur.fetchall()]
            for job_id in expired_jobs:
                self.release_resources(job_id)
            cur.execute("UPDATE resource_reservations SET status='EXPIRED' WHERE status='ACTIVE' AND expires_at < datetime('now')")
            return len(expired_jobs)
    
    def get_resource_status(self) -> List[Dict]:
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM resources")
        return [dict(row) for row in cur.fetchall()]
