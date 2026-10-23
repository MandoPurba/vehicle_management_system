from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from core.structures.dynamic_array import ParkingSlots

# ---- Konstanta ----
VehicleStatus = Literal["REGISTERED", "PARKED", "WAITING", "EXITED"]
TxType = Literal["CHECK_IN", "ENQUEUE", "CHECK_OUT"]
SearchBy = Literal["id", "plate", "owner"]
VehicleType = Literal["MOTOR", "MOBIL"]

SLOT_CAPACITY: int = 5  # A01-A05, kecil agar kondisi penuh mudah didemokan

def slot_code(idx: int) -> str:
    """0 -> 'A01', 4 -> 'A05'."""
    return f"A{idx + 1:02d}"


def count_occupied(slots: "ParkingSlots") -> int:
    """Hitung berapa slot yang sedang terisi."""
    return sum(1 for i in range(slots.capacity) if slots.get(i) is not None)


# ---- Model ----
# Diimpor di bawah konstanta: tiap model mengambil Literal di atas dari modul ini.
from core.models.history_record import HistoryRecord
from core.models.result import Result
from core.models.transaction import Transaction
from core.models.vehicle import Vehicle

__all__ = [
    "SLOT_CAPACITY",
    "HistoryRecord",
    "Result",
    "SearchBy",
    "Transaction",
    "TxType",
    "Vehicle",
    "VehicleStatus",
    "VehicleType",
    "count_occupied",
    "slot_code",
]
