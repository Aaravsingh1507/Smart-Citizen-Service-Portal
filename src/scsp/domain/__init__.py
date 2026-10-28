"""Domain models"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class ComplaintStatus(Enum):
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"

class JobState(Enum):
    PENDING = "PENDING"
    CLAIMED = "CLAIMED"
    PROCESSING = "PROCESSING"
    RETRY_WAIT = "RETRY_WAIT"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class Priority(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
