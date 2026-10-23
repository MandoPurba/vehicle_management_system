from dataclasses import dataclass
from datetime import datetime


@dataclass
class HistoryRecord:
    """Satu entri di ParkingHistory (dibuat saat check-out)."""
    vehicle_id: str
    plate: str
    slot_code: str
    entry_time: datetime
    exit_time: datetime
