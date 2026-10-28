"""Audit service"""
from typing import List, Dict
from datetime import datetime

class AuditService:
    def __init__(self, db_manager):
        self.db = db_manager
    
    def log_event(self, event_type: str, entity_type: str = None, entity_id: int = None, 
                  actor: str = 'SYSTEM', details: str = None):
        try:
            with self.db.transaction() as conn:
                cur = conn.cursor()
                cur.execute("""INSERT INTO audit_events (event_type, entity_type, entity_id, actor, details)
                              VALUES (?,?,?,?,?)""", (event_type, entity_type, entity_id, actor, details))
        except Exception as e:
            pass
    
    def get_events(self, limit: int = 100) -> List[Dict]:
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM audit_events ORDER BY created_at DESC LIMIT ?", (limit,))
        return [dict(row) for row in cur.fetchall()]
    
    def get_events_by_entity(self, entity_type: str, entity_id: int) -> List[Dict]:
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM audit_events WHERE entity_type=? AND entity_id=? ORDER BY created_at",
                   (entity_type, entity_id))
        return [dict(row) for row in cur.fetchall()]
