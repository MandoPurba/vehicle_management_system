"""Perhitungan statistik yang dikerjakan secara rekursif."""

from core.structures.dynamic_array import ParkingSlots


def count_occupied_recursive(slots: ParkingSlots, i: int = 0) -> int:
    """Jumlah slot terisi, dihitung rekursif dari indeks `i`."""
    if i >= slots.capacity:  # base case
        return 0
    terisi = 1 if slots.get(i) is not None else 0
    return terisi + count_occupied_recursive(slots, i + 1)


def max_duration_recursive(records: list, lo: int = 0, hi: int | None = None) -> int:
    """Durasi parkir terlama dalam menit, dicari dengan membagi rentang dua.

    Tiap langkah mengerjakan separuh kiri dan separuh kanan, jadi kedalaman
    call stack-nya O(log n), bukan O(n). Ribuan riwayat tetap di bawah batas
    rekursi Python.
    """
    if hi is None:
        hi = len(records)
    if hi - lo <= 0:  # base case: rentang kosong
        return 0
    if hi - lo == 1:  # base case: satu elemen
        return records[lo].duration_minutes
    mid = (lo + hi) // 2
    return max(
        max_duration_recursive(records, lo, mid),
        max_duration_recursive(records, mid, hi),
    )
