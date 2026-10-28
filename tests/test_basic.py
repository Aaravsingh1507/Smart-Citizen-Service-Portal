import unittest
import os
import tempfile
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from scsp.database import DatabaseManager
from scsp.repositories import ComplaintRepository, JobRepository
from scsp.resources import ResourceManager

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.tmpfile.close()
        self.db = DatabaseManager(Path(self.tmpfile.name))
        self.complaint_repo = ComplaintRepository(self.db)
        self.job_repo = JobRepository(self.db)
    
    def tearDown(self):
        try:
            os.unlink(self.tmpfile.name)
        except:
            pass
    
    def test_create_complaint(self):
        citizen_id = self.complaint_repo.create_citizen("Test User", "1234567890")
        self.assertIsInstance(citizen_id, int)
        complaint_id = self.complaint_repo.create_complaint(citizen_id, "Water supply", "Leak", "Pipe leak")
        self.assertIsInstance(complaint_id, int)
        job_id = self.job_repo.create_job(complaint_id)
        self.assertIsInstance(job_id, int)
    
    def test_foreign_keys_enabled(self):
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("PRAGMA foreign_keys")
        self.assertEqual(cur.fetchone()[0], 1)
    
    def test_claim_job_atomic(self):
        citizen_id = self.complaint_repo.create_citizen("Test", "123")
        complaint_id = self.complaint_repo.create_complaint(citizen_id, "Roads", "Pothole", "Big pothole")
        job_id = self.job_repo.create_job(complaint_id)
        job = self.job_repo.claim_job("worker1")
        self.assertIsNotNone(job)
        self.assertEqual(job['id'], job_id)

class TestResources(unittest.TestCase):
    def setUp(self):
        self.tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.tmpfile.close()
        self.db = DatabaseManager(Path(self.tmpfile.name))
        self.rm = ResourceManager(self.db)
        self.rm.initialize_ordering()
    
    def tearDown(self):
        try:
            os.unlink(self.tmpfile.name)
        except:
            pass
    
    def test_resource_initialization(self):
        status = self.rm.get_resource_status()
        self.assertGreater(len(status), 0)

if __name__ == '__main__':
    unittest.main()
