"""Algoritma pengurutan, ditulis sendiri tanpa list.sort()."""

from collections.abc import Callable
from typing import Any

from core.models import SortBy

KeyFunc = Callable[[Any], Any]


def _diri_sendiri(item: Any) -> Any:
    return item


def merge_sort(items: list, key: KeyFunc | None = None) -> list:
    """Urut dengan merge sort. O(n log n), stabil, hemat perbandingan."""
    ambil = key or _diri_sendiri
    if len(items) <= 1:
        return list(items)
    tengah = len(items) // 2
    kiri = merge_sort(items[:tengah], ambil)
    kanan = merge_sort(items[tengah:], ambil)
    return _merge(kiri, kanan, ambil)


def _merge(kiri: list, kanan: list, ambil: KeyFunc) -> list:
    """Gabungkan dua daftar terurut menjadi satu daftar terurut."""
    hasil: list = []
    i = j = 0
    while i < len(kiri) and j < len(kanan):
        # <= menjaga kestabilan: yang dari kiri menang kalau kuncinya seri.
        if ambil(kiri[i]) <= ambil(kanan[j]):
            hasil.append(kiri[i])
            i += 1
        else:
            hasil.append(kanan[j])
            j += 1
    hasil.extend(kiri[i:])
    hasil.extend(kanan[j:])
    return hasil


def insertion_sort(items: list, key: KeyFunc | None = None) -> list:
    """Urut dengan insertion sort. O(n^2), tapi O(n) kalau hampir terurut."""
    ambil = key or _diri_sendiri
    hasil = list(items)
    for i in range(1, len(hasil)):
        sekarang = hasil[i]
        j = i - 1
        while j >= 0 and ambil(hasil[j]) > ambil(sekarang):
            hasil[j + 1] = hasil[j]
            j -= 1
        hasil[j + 1] = sekarang
    return hasil


def bubble_sort(items: list, key: KeyFunc | None = None) -> list:
    """Urut dengan bubble sort. O(n^2), berhenti awal kalau sudah terurut."""
    ambil = key or _diri_sendiri
    hasil = list(items)
    for akhir in range(len(hasil) - 1, 0, -1):
        bertukar = False
        for i in range(akhir):
            if ambil(hasil[i]) > ambil(hasil[i + 1]):
                hasil[i], hasil[i + 1] = hasil[i + 1], hasil[i]
                bertukar = True
        if not bertukar:
            return hasil
    return hasil


def quick_sort(items: list, key: KeyFunc | None = None) -> list:
    """Urut dengan quick sort, pivot tengah. O(n log n) rata-rata."""
    ambil = key or _diri_sendiri
    hasil = list(items)
    # Tumpukan eksplisit, bukan rekursi: data terurut bisa membuat
    # kedalaman rekursinya sebesar n dan Python berhenti di ~1000.
    tumpukan = [(0, len(hasil) - 1)]
    while tumpukan:
        awal, akhir = tumpukan.pop()
        if awal >= akhir:
            continue
        batas = _partition(hasil, awal, akhir, ambil)
        tumpukan.append((awal, batas - 1))
        tumpukan.append((batas + 1, akhir))
    return hasil


def _partition(items: list, awal: int, akhir: int, ambil: KeyFunc) -> int:
    """Tata ulang items[awal:akhir+1] di sekitar pivot, kembalikan posisinya."""
    tengah = (awal + akhir) // 2
    items[tengah], items[akhir] = items[akhir], items[tengah]
    pivot = ambil(items[akhir])
    batas = awal
    for i in range(awal, akhir):
        if ambil(items[i]) < pivot:
            items[i], items[batas] = items[batas], items[i]
            batas += 1
    items[batas], items[akhir] = items[akhir], items[batas]
    return batas


SORT_KEYS: dict[str, KeyFunc] = {
    "entry_time": lambda r: r.entry_time,
    "exit_time": lambda r: r.exit_time,
    "duration": lambda r: r.duration,
    "cost": lambda r: r.cost,
    "plate": lambda r: r.plate,
}

ALGORITHMS: dict[str, Callable[[list, KeyFunc | None], list]] = {
    "merge": merge_sort,
    "quick": quick_sort,
    "insertion": insertion_sort,
    "bubble": bubble_sort,
}


def sort_history(
    records: list,
    by: SortBy = "entry_time",
    descending: bool = False,
    algorithm: str = "merge",
) -> list:
    """Urutkan riwayat parkir menurut waktu, durasi, biaya, atau plat."""
    fungsi = ALGORITHMS.get(algorithm, merge_sort)
    hasil = fungsi(records, key=SORT_KEYS[by])
    return hasil[::-1] if descending else hasil
