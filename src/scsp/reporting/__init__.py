"""Reporting service with CSV export"""
import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, List

class ReportService:
    def __init__(self, db_manager, export_dir: Path):
        self.db = db_manager
        self.export_dir = export_dir
    
    def export_complaints_csv(self, filename: str = None) -> Path:
        if filename is None:
            filename = f"complaints_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = self.export_dir / filename
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("""SELECT c.id, ci.name, ci.phone, c.category, c.title, c.status, 
                      c.priority, d.name as department, c.created_at, c.updated_at
                      FROM complaints c 
                      LEFT JOIN citizens ci ON c.citizen_id = ci.id
                      LEFT JOIN departments d ON c.assigned_department_id = d.id
                      ORDER BY c.created_at""")
        rows = cur.fetchall()
        # Atomic write
        tmp_path = filepath.with_suffix('.tmp')
        with open(tmp_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ID', 'Citizen', 'Phone', 'Category', 'Title', 'Status', 
                           'Priority', 'Department', 'Created', 'Updated'])
            for row in rows:
                writer.writerow([row['id'], row['name'], row['phone'], row['category'],
                               row['title'], row['status'], row['priority'], 
                               row['department'], row['created_at'], row['updated_at']])
        tmp_path.replace(filepath)  # Atomic replace on Windows
        return filepath
    
    def generate_summary_report(self) -> Dict:
        conn = self.db.get_connection()
        cur = conn.cursor()
        report = {}
        cur.execute("SELECT COUNT(*) as cnt FROM complaints")
        report['total_complaints'] = cur.fetchone()['cnt']
        cur.execute("SELECT status, COUNT(*) as cnt FROM complaints GROUP BY status")
        report['by_status'] = {r['status']: r['cnt'] for r in cur.fetchall()}
        cur.execute("SELECT category, COUNT(*) as cnt FROM complaints GROUP BY category")
        report['by_category'] = {r['category']: r['cnt'] for r in cur.fetchall()}
        cur.execute("SELECT COUNT(*) as cnt FROM processing_jobs WHERE state='COMPLETED'")
        report['jobs_completed'] = cur.fetchone()['cnt']
        cur.execute("SELECT COUNT(*) as cnt FROM processing_jobs WHERE state='FAILED'")
        report['jobs_failed'] = cur.fetchone()['cnt']
        return report
