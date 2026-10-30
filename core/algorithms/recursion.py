"""Perhitungan statistik yang dikerjakan secara rekursif."""

from core.structures.dynamic_array import ParkingSlots


def count_occupied_recursive(slots: ParkingSlots, i: int = 0) -> int:
    """Jumlah slot terisi, dihitung rekursif dari indeks `i`."""
    if i >= slots.capacity:  # base case
        return 0
    terisi = 1 if slots.get(i) is not None else 0
    return terisi + count_occupied_recursive(slots, i + 1)


def sum_costs_recursive(records: list, lo: int = 0, hi: int | None = None) -> int:
    """Total biaya seluruh riwayat, dijumlahkan dengan membagi rentang dua.

    Tiap langkah mengerjakan separuh kiri dan separuh kanan, jadi kedalaman
    call stack O(log n). Seribu dua ratus riwayat tetap di bawah batas rekursi Python.
    """
    if hi is None:
        hi = len(records)
    if hi - lo <= 0:  # base case: kosong
        return 0
    if hi - lo == 1:  # base case: satu elemen
        return records[lo].cost
    mid = (lo + hi) // 2
    return sum_costs_recursive(records, lo, mid) + sum_costs_recursive(records, mid, hi)


def max_duration_recursive(records: list, i: int = 0) -> int:
    """Durasi parkir terlama dalam menit, dicari rekursif."""
    if i >= len(records):  # base case
        return 0
    return max(records[i].duration_minutes, max_duration_recursive(records, i + 1))
