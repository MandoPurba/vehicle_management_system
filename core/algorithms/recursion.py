"""Perhitungan statistik yang dikerjakan secara rekursif."""

from core.structures.dynamic_array import ParkingSlots


def count_occupied_recursive(slots: ParkingSlots, i: int = 0) -> int:
    """Jumlah slot terisi, dihitung rekursif dari indeks `i`."""
    if i >= slots.capacity:  # base case
        return 0
    terisi = 1 if slots.get(i) is not None else 0
    return terisi + count_occupied_recursive(slots, i + 1)


def sum_costs_recursive(records: list, i: int = 0) -> int:
    """Total biaya seluruh riwayat, dijumlahkan rekursif."""
    if i >= len(records):  # base case
        return 0
    return records[i].cost + sum_costs_recursive(records, i + 1)


def max_duration_recursive(records: list, i: int = 0) -> int:
    """Durasi parkir terlama dalam menit, dicari rekursif."""
    if i >= len(records):  # base case
        return 0
    return max(records[i].duration_minutes, max_duration_recursive(records, i + 1))
