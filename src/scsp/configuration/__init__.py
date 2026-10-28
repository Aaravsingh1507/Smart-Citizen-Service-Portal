"""Configuration for Smart Citizen Service Portal"""
import os
from pathlib import Path
from dataclasses import dataclass

def get_app_data_dir() -> Path:
    """Get application data directory (writable, not absolute machine-specific in docs)"""
    if os.name == 'nt':
        base = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local'))
    else:
        base = Path.home() / '.local' / 'share'
    app_dir = base / 'SmartCitizenServicePortal'
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir

@dataclass
class Config:
    app_name: str = "Smart Citizen Service Portal"
    version: str = "1.0.0"
    db_path: Path = get_app_data_dir() / "scsp.db"
    log_dir: Path = get_app_data_dir() / "logs"
    export_dir: Path = get_app_data_dir() / "exports"
    worker_count: int = 4
    max_queue_size: int = 1000
    lease_timeout_seconds: int = 300
    max_retry_attempts: int = 5
    retry_backoff_base: float = 2.0
    resource_lock_timeout: float = 5.0
    
    def __post_init__(self):
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.export_dir.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def load(cls):
        return cls()

config = Config.load()
