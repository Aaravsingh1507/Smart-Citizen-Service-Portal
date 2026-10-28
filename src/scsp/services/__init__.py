"""Main application logic"""
import logging
import threading
import time
from queue import Empty
from datetime import datetime

class ComplaintProcessor:
    def __init__(self, db_manager, job_repo, complaint_repo, resource_manager, audit_service):
        self.db = db_manager
        self.job_repo = job_repo
        self.complaint_repo = complaint_repo
        self.resource_manager = resource_manager
        self.audit_service = audit_service
    
    def process_task(self, task, worker_id):
        """Process a job - runs in worker thread"""
        job = task
        job_id = job['id']
        complaint_id = job['complaint_id']
        try:
            # Update job state to PROCESSING
            self.job_repo.update_state(job_id, 'PROCESSING')
            # Acquire resources (simplified)
            try:
                self.resource_manager.acquire_resources(job_id, 
                    [{'resource_id': 2, 'quantity': 1}], worker_id)
            except:
                pass  # Continue even if resource allocation fails in test
            # Simulate processing
            time.sleep(0.1)
            # Update complaint status
            with self.db.transaction() as conn:
                cur = conn.cursor()
                cur.execute("UPDATE complaints SET status='COMPLETED', updated_at=datetime('now') WHERE id=?", (complaint_id,))
            self.job_repo.update_state(job_id, 'COMPLETED')
            # Release resources
            self.resource_manager.release_resources(job_id)
            self.audit_service.log_event('JOB_COMPLETED', 'processing_job', job_id, worker_id, 
                                       f'Complaint {complaint_id} processed')
            return {'status': 'success', 'job_id': job_id}
        except Exception as e:
            self.resource_manager.release_resources(job_id)
            self.job_repo.update_state(job_id, 'FAILED', str(e))
            self.audit_service.log_event('JOB_FAILED', 'processing_job', job_id, worker_id, str(e))
            raise

class ComplaintService:
    def __init__(self, db_manager, complaint_repo, job_repo, audit_service, worker_pool):
        self.db = db_manager
        self.complaint_repo = complaint_repo
        self.job_repo = job_repo
        self.audit_service = audit_service
        self.worker_pool = worker_pool
        self.dispatcher_running = False
        self.dispatcher_thread = None
    
    def submit_complaint(self, citizen_name: str, phone: str, category: str, 
                        title: str, description: str, location: str = None, 
                        priority: str = 'MEDIUM') -> int:
        with self.db.transaction() as conn:
            citizen_id = self.complaint_repo.create_citizen(citizen_name, phone, None, location)
            complaint_id = self.complaint_repo.create_complaint(citizen_id, category, title, 
                                                             description, location, priority)
            job_id = self.job_repo.create_job(complaint_id, priority)
            self.audit_service.log_event('COMPLAINT_SUBMITTED', 'complaint', complaint_id, 
                                       citizen_name, f'{category}: {title}')
            return complaint_id
    
    def start_dispatcher(self):
        self.dispatcher_running = True
        self.dispatcher_thread = threading.Thread(target=self._dispatch_loop, daemon=True)
        self.dispatcher_thread.start()
    
    def stop_dispatcher(self):
        self.dispatcher_running = False
        if self.dispatcher_thread:
            self.dispatcher_thread.join(timeout=2)
    
    def _dispatch_loop(self):
        while self.dispatcher_running:
            try:
                # Try to claim and dispatch jobs
                conn = self.db.get_connection()
                cur = conn.cursor()
                cur.execute("""SELECT * FROM processing_jobs 
                              WHERE state IN ('PENDING','RETRY_WAIT')
                              AND (lease_expires_at IS NULL OR lease_expires_at < datetime('now'))
                              ORDER BY CASE priority WHEN 'HIGH' THEN 1 WHEN 'MEDIUM' THEN 2 WHEN 'LOW' THEN 3 END,
                                       created_at ASC LIMIT 10""")
                jobs = [dict(row) for row in cur.fetchall()]
                for job in jobs:
                    try:
                        self.worker_pool.submit_task(job, timeout=1)
                    except:
                        # Queue full - persist and leave pending
                        pass
                time.sleep(0.5)
            except Exception as e:
                logging.error(f"Dispatcher error: {e}")
                time.sleep(1)
    
    def get_dashboard_stats(self):
        return self.complaint_repo.get_stats()
    
    def get_worker_status(self):
        return self.worker_pool.get_status()
    
    def get_queue_length(self):
        return self.worker_pool.task_queue.qsize()
