from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class TransactionStatus(Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

@dataclass
class UPITransaction:
    transaction_id: str
    user_id: str
    amount: float
    upi_id: str
    status: TransactionStatus
    created_at: datetime = datetime.utcnow()
