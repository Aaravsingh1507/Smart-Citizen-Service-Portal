"""Recovery service"""
import threading
import time
from datetime import datetime, timedelta

class RecoveryService:
    def __init__(self, db_manager, job_repo, resource_manager):
        self.db = db_manager
        self.job_repo = job_repo
        self.resource_manager = resource_manager
        self.running = False
        self.thread = None
    
    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._recovery_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
    
    def _recovery_loop(self):
        while self.running:
            try:
                self.recover_stale()
                self.release_expired_resources()
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                pass
    
    def recover_stale(self):
        count = self.job_repo.recover_stale_jobs(timeout_seconds=300)
        if count > 0:
            self._log_audit('RECOVERY', f'Recovered {count} stale jobs')
        return count
    
    def release_expired_resources(self):
        count = self.resource_manager.release_expired_reservations()
        if count > 0:
            self._log_audit('RESOURCE_RELEASE', f'Released expired reservations for {count} jobs')
        return count
    
    def _log_audit(self, event_type: str, details: str):
        try:
            with self.db.transaction() as conn:
                cur = conn.cursor()
                cur.execute("INSERT INTO audit_events (event_type, details, actor) VALUES (?,?,?)",
                           (event_type, details, 'RECOVERY_SERVICE'))
        except:
            pass
    
    def manual_recover_job(self, job_id: int):
        with self.db.transaction() as conn:
            cur = conn.cursor()
            cur.execute("SELECT attempt_count, max_attempts FROM processing_jobs WHERE id = ?", (job_id,))
            row = cur.fetchone()
            if not row:
                return False
            if row['attempt_count'] >= row['max_attempts']:
                cur.execute("UPDATE processing_jobs SET state='FAILED', updated_at=datetime('now') WHERE id = ?", (job_id,))
            else:
                cur.execute("UPDATE processing_jobs SET state='RETRY_WAIT', assigned_worker=NULL, lease_expires_at=NULL, updated_at=datetime('now') WHERE id = ?", (job_id,))
            return True
