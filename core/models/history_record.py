from dataclasses import dataclass
from datetime import datetime, timedelta

from core.models import VehicleType, hitung_biaya


@dataclass
class HistoryRecord:
    """Satu entri di HistoryTree (dibuat saat check-out)."""
    vehicle_id: str
    plate: str
    slot_code: str
    entry_time: datetime
    exit_time: datetime
    vtype: VehicleType = "MOBIL"

    @property
    def duration(self) -> timedelta:
        """Lama kendaraan parkir."""
        return self.exit_time - self.entry_time

    @property
    def duration_minutes(self) -> int:
        """Lama parkir dalam menit, dibulatkan ke bawah."""
        return int(self.duration.total_seconds() // 60)

    @property
    def cost(self) -> int:
        """Biaya parkir menurut tipe kendaraan dan lama parkir."""
        return hitung_biaya(self.vtype, self.duration)
