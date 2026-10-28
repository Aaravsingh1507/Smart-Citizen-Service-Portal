"""Benchmark utility for performance testing"""
import time
import random
from typing import Dict

class Benchmark:
    def __init__(self, services):
        self.services = services
    
    def run_benchmark(self, num_jobs: int = 50, worker_count: int = 4, 
                     priority_dist: Dict = None, processing_delay: float = 0.1) -> Dict:
        if priority_dist is None:
            priority_dist = {'HIGH': 0.2, 'MEDIUM': 0.5, 'LOW': 0.3}
        
        complaint_service = self.services['complaint_service']
        start_time = time.time()
        submitted = []
        
        # Submit jobs
        for i in range(num_jobs):
            r = random.random()
            if r < priority_dist['HIGH']:
                priority = 'HIGH'
            elif r < priority_dist['HIGH'] + priority_dist['MEDIUM']:
                priority = 'MEDIUM'
            else:
                priority = 'LOW'
            try:
                cid = complaint_service.submit_complaint(
                    f"Test User {i}", f"123456{i%10:04d}", 
                    "General municipal services", f"Test Complaint {i}",
                    f"Test description {i}", "Test Location", priority
                )
                submitted.append(cid)
            except Exception as e:
                pass
        
        submit_time = time.time()
        # Wait for processing
        time.sleep(num_jobs * processing_delay / worker_count + 5)
        end_time = time.time()
        
        stats = complaint_service.get_dashboard_stats()
        ws = complaint_service.get_worker_status()
        
        return {
            'submitted_jobs': len(submitted),
            'completed_jobs': stats.get('completed', 0),
            'failed_jobs': stats.get('failed', 0),
            'pending_jobs': stats.get('pending', 0),
            'total_elapsed': end_time - start_time,
            'throughput': stats.get('completed', 0) / (end_time - start_time) if (end_time - start_time) > 0 else 0,
            'workers': worker_count,
            'workers_status': ws,
            'synthetic_test_data': True
        }
