"""Worker pool with threading - Multithreading concept"""
import threading
import time
import uuid
from queue import Queue, Empty, Full
from typing import Callable, Optional
import logging

class Worker:
    def __init__(self, worker_id: str, task_queue: Queue, result_queue: Queue, 
                 stop_event: threading.Event, processor: Callable):
        self.worker_id = worker_id
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.stop_event = stop_event
        self.processor = processor
        self.thread = threading.Thread(target=self._run, name=f"Worker-{worker_id}", daemon=True)
        self.status = "IDLE"
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.current_task = None
        
    def start(self):
        self.thread.start()
    
    def stop(self):
        self.stop_event.set()
    
    def join(self, timeout=None):
        self.thread.join(timeout)
    
    def _run(self):
        while not self.stop_event.is_set():
            try:
                task = self.task_queue.get(timeout=1)
                if task is None:  # Poison pill
                    self.task_queue.task_done()
                    break
                self.status = "BUSY"
                self.current_task = task
                try:
                    result = self.processor(task, self.worker_id)
                    self.tasks_completed += 1
                    self.result_queue.put(('SUCCESS', task, result))
                except Exception as e:
                    self.tasks_failed += 1
                    self.result_queue.put(('ERROR', task, e))
                finally:
                    self.status = "IDLE"
                    self.current_task = None
                    self.task_queue.task_done()
            except Empty:
                continue
            except Exception as e:
                logging.error(f"Worker {self.worker_id} error: {e}")
                self.status = "IDLE"

class WorkerPool:
    def __init__(self, num_workers: int, processor: Callable, max_queue_size: int = 1000):
        self.num_workers = num_workers
        self.processor = processor
        self.task_queue = Queue(maxsize=max_queue_size)
        self.result_queue = Queue()
        self.stop_event = threading.Event()
        self.workers = []
        self.lock = threading.RLock()
        self.total_submitted = 0
        self.total_completed = 0
        
    def start(self):
        with self.lock:
            for i in range(self.num_workers):
                worker_id = str(uuid.uuid4())[:8]
                worker = Worker(worker_id, self.task_queue, self.result_queue, 
                               self.stop_event, self.processor)
                self.workers.append(worker)
                worker.start()
        logging.info(f"Started {self.num_workers} worker threads")
    
    def submit_task(self, task, timeout=None):
        """Submit task - never silently discard, wait if needed"""
        try:
            self.task_queue.put(task, timeout=timeout)
            self.total_submitted += 1
            return True
        except Full:
            # Don't discard - caller should persist to DB
            raise
    
    def get_result(self, timeout=None):
        try:
            return self.result_queue.get(timeout=timeout)
        except Empty:
            return None
    
    def get_status(self):
        with self.lock:
            return {
                'workers': [{'id': w.worker_id, 'status': w.status, 
                           'completed': w.tasks_completed, 'failed': w.tasks_failed}
                          for w in self.workers],
                'queue_size': self.task_queue.qsize(),
                'queue_max': self.task_queue.maxsize,
                'total_submitted': self.total_submitted,
                'total_completed': self.total_completed
            }
    
    def shutdown(self, timeout=5):
        logging.info("Shutting down worker pool...")
        # Send poison pills
        for _ in self.workers:
            try:
                self.task_queue.put(None, timeout=1)
            except:
                pass
        self.stop_event.set()
        for worker in self.workers:
            worker.join(timeout=timeout)
        logging.info("Worker pool shut down")
    
    def is_alive(self):
        return any(w.thread.is_alive() for w in self.workers)
