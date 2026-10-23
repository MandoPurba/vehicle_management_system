from dataclasses import dataclass
from datetime import datetime

from core.models import VehicleStatus, VehicleType


@dataclass
class Vehicle:
    vehicle_id: str
    plate: str
    owner: str
    vtype: VehicleType
    status: VehicleStatus = "REGISTERED"
    entry_time: datetime | None = None
    slot_index: int | None = None  # None = tidak sedang parkir
