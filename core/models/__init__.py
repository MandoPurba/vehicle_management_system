from datetime import timedelta
from math import ceil
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from core.structures.dynamic_array import ParkingSlots

# ---- Konstanta ----
VehicleStatus = Literal["REGISTERED", "PARKED", "WAITING", "EXITED"]
TxType = Literal["CHECK_IN", "ENQUEUE", "CHECK_OUT"]
SearchBy = Literal["id", "plate", "owner"]
VehicleType = Literal["MOTOR", "MOBIL"]
Priority = Literal["DISABILITAS", "DOSEN", "TAMU", "UMUM"]
SortBy = Literal["entry_time", "exit_time", "duration", "cost", "plate"]

SLOT_CAPACITY: int = 5  # A01-A05, kecil agar kondisi penuh mudah didemokan
MIN_SLOT_CAPACITY: int = 1  # satu slot pun masih sistem parkir yang sah
MAX_SLOT_CAPACITY: int = 60  # batas atas agar grid slot di UI tetap terbaca

# Angka kecil dilayani lebih dulu; dipakai MinHeap sebagai kunci.
PRIORITY_RANK: dict[str, int] = {
    "DISABILITAS": 0,
    "DOSEN": 1,
    "TAMU": 2,
    "UMUM": 3,
}
PRIORITY_LABEL: dict[str, str] = {
    "DISABILITAS": "Disabilitas",
    "DOSEN": "Dosen",
    "TAMU": "Tamu undangan",
    "UMUM": "Umum",
}
DEFAULT_PRIORITY: Priority = "UMUM"

# Tarif parkir kampus: nominal, dihitung proporsional per menit.
TARIF_PER_JAM: dict[str, int] = {"MOBIL": 2000, "MOTOR": 1000}
PEMBULATAN_RUPIAH: int = 100


def slot_code(idx: int) -> str:
    """0 -> 'A01', 4 -> 'A05'."""
    return f"A{idx + 1:02d}"


def priority_rank(priority: str) -> int:
    """Angka urutan layanan sebuah prioritas. Yang tidak dikenal jadi UMUM."""
    return PRIORITY_RANK.get(priority, PRIORITY_RANK[DEFAULT_PRIORITY])


def hitung_biaya(vtype: str, durasi: timedelta) -> int:
    """Biaya parkir kampus: proporsional per menit, bukan per jam penuh.

    Dibulatkan ke atas ke ratusan rupiah terdekat. Kendaraan yang keluar
    tanpa sempat parkir tidak ditagih.
    """
    menit = durasi.total_seconds() / 60
    if menit <= 0:
        return 0
    tarif = TARIF_PER_JAM.get(vtype, TARIF_PER_JAM["MOBIL"])
    kasar = tarif * menit / 60
    return max(PEMBULATAN_RUPIAH, ceil(kasar / PEMBULATAN_RUPIAH) * PEMBULATAN_RUPIAH)


def count_occupied(slots: "ParkingSlots") -> int:
    """Hitung slot terisi, lewat fungsi rekursif di core/algorithms."""
    # Impor di dalam fungsi: modul algoritma mengimpor modul ini juga.
    from core.algorithms.recursion import count_occupied_recursive

    return count_occupied_recursive(slots)


# ---- Model ----
# Diimpor di bawah konstanta: tiap model mengambil Literal di atas dari modul ini.
from core.models.history_record import HistoryRecord
from core.models.result import Result
from core.models.transaction import Transaction
from core.models.vehicle import Vehicle

__all__ = [
    "DEFAULT_PRIORITY",
    "MAX_SLOT_CAPACITY",
    "MIN_SLOT_CAPACITY",
    "PRIORITY_LABEL",
    "PRIORITY_RANK",
    "SLOT_CAPACITY",
    "PEMBULATAN_RUPIAH",
    "TARIF_PER_JAM",
    "HistoryRecord",
    "Priority",
    "Result",
    "SearchBy",
    "SortBy",
    "Transaction",
    "TxType",
    "Vehicle",
    "VehicleStatus",
    "VehicleType",
    "count_occupied",
    "hitung_biaya",
    "priority_rank",
    "slot_code",
]
