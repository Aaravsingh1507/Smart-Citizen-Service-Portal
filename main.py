"""Main entry point"""
import sys
import logging
from pathlib import Path

# Setup logging
from scsp.configuration import config
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.log_dir / 'scsp.log'),
        logging.StreamHandler()
    ]
)

from scsp.database import DatabaseManager
from scsp.repositories import ComplaintRepository, JobRepository
from scsp.concurrency import WorkerPool
from scsp.resources import ResourceManager
from scsp.recovery import RecoveryService
from scsp.audit import AuditService
from scsp.reporting import ReportService
from scsp.services import ComplaintService, ComplaintProcessor
from scsp.process_supervisor import ProcessSupervisor
from scsp.ui import run_app

def main():
    try:
        logging.info("Starting Smart Citizen Service Portal")
        # Initialize components
        db = DatabaseManager(config.db_path)
        complaint_repo = ComplaintRepository(db)
        job_repo = JobRepository(db)
        audit_service = AuditService(db)
        resource_manager = ResourceManager(db)
        resource_manager.initialize_ordering()
        report_service = ReportService(db, config.export_dir)
        process_supervisor = ProcessSupervisor()
        
        # Create processor
        processor = ComplaintProcessor(db, job_repo, complaint_repo, resource_manager, audit_service)
        
        # Start worker pool
        worker_pool = WorkerPool(config.worker_count, processor.process_task, config.max_queue_size)
        worker_pool.start()
        
        # Create complaint service
        complaint_service = ComplaintService(db, complaint_repo, job_repo, audit_service, worker_pool)
        complaint_service.start_dispatcher()
        
        # Start recovery service
        recovery_service = RecoveryService(db, job_repo, resource_manager)
        recovery_service.start()
        
        services = {
            'db': db,
            'complaint_repo': complaint_repo,
            'job_repo': job_repo,
            'audit_service': audit_service,
            'resource_manager': resource_manager,
            'report_service': report_service,
            'process_supervisor': process_supervisor,
            'complaint_service': complaint_service,
            'worker_pool': worker_pool,
            'recovery_service': recovery_service
        }
        
        logging.info("All services initialized")
        # Run GUI
        run_app(services)
        
        # Cleanup
        complaint_service.stop_dispatcher()
        worker_pool.shutdown()
        recovery_service.stop()
        process_supervisor.cleanup_all()
        logging.info("Application shutdown complete")
        
    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=True)
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
