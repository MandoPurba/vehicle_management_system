from core.structures.bst import HistoryTree
from core.structures.dynamic_array import ParkingSlots
from core.structures.queue import WaitingQueue


def count_occupied(slots: ParkingSlots, i: int = 0) -> int:
    """Menghitung jumlah slot terisi secara rekursif."""
    # Base case: jika index mencapai kapasitas slot, berhenti
    if i >= slots.capacity:
        return 0

    # Cek apakah slot ke-i terisi, jika tidak maka None
    is_filled = 1 if slots.get(i) is not None else 0

    # Recursive case: tambahkan status slot saat ini dengan hasil rekursi index berikutnya
    return is_filled + count_occupied(slots, i + 1)


def show_statistics(slots: ParkingSlots, queue: WaitingQueue, history: HistoryTree) -> None:
    """Total slot, terisi, tersedia, jumlah queue, total dilayani (history.size)."""
    total_slots = slots.capacity
    occupied_slots = count_occupied(slots, 0)  # Memanggil fungsi rekursif
    available_slots = total_slots - occupied_slots
    queue_len = queue.size
    total_served = history.size  # Mengambil jumlah riwayat parkir yang selesai

    print("=== Statistik Smart Parking ===")
    print(f"Total Slot      : {total_slots}")
    print(f"Slot Terisi     : {occupied_slots}")
    print(f"Slot Tersedia   : {available_slots}")
    print(f"Jumlah Antrean  : {queue_len}")
    print(f"Total Dilayani  : {total_served}")
