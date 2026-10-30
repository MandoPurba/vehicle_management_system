"""Algoritma pencarian, termasuk binary search pada data terurut."""

from collections.abc import Callable
from typing import Any

from core.algorithms.sorting import SORT_KEYS, sort_history
from core.models import SortBy

KeyFunc = Callable[[Any], Any]


def _diri_sendiri(item: Any) -> Any:
    return item


def linear_search(items: list, target: Any, key: KeyFunc | None = None) -> int:
    """Indeks pertama yang kuncinya sama dengan target, -1 kalau tidak ada. O(n)."""
    ambil = key or _diri_sendiri
    for i, item in enumerate(items):
        if ambil(item) == target:
            return i
    return -1


def binary_search(items: list, target: Any, key: KeyFunc | None = None) -> int:
    """Indeks target pada data yang SUDAH terurut naik, -1 kalau tidak ada. O(log n).

    Tiap langkah membuang separuh sisa data. Kalau datanya belum terurut
    hasilnya tidak bisa dipercaya.
    """
    ambil = key or _diri_sendiri
    rendah, tinggi = 0, len(items) - 1
    while rendah <= tinggi:
        tengah = (rendah + tinggi) // 2
        nilai = ambil(items[tengah])
        if nilai == target:
            return tengah
        if nilai < target:
            rendah = tengah + 1
        else:
            tinggi = tengah - 1
    return -1


def binary_search_first(items: list, target: Any, key: KeyFunc | None = None) -> int:
    """Indeks kemunculan PERTAMA target pada data terurut. O(log n)."""
    ambil = key or _diri_sendiri
    rendah, tinggi, ketemu = 0, len(items) - 1, -1
    while rendah <= tinggi:
        tengah = (rendah + tinggi) // 2
        nilai = ambil(items[tengah])
        if nilai == target:
            ketemu = tengah
            tinggi = tengah - 1  # masih mungkin ada yang lebih kiri
        elif nilai < target:
            rendah = tengah + 1
        else:
            tinggi = tengah - 1
    return ketemu


def lower_bound(items: list, target: Any, key: KeyFunc | None = None) -> int:
    """Indeks pertama yang kuncinya >= target pada data terurut. O(log n)."""
    ambil = key or _diri_sendiri
    rendah, tinggi = 0, len(items)
    while rendah < tinggi:
        tengah = (rendah + tinggi) // 2
        if ambil(items[tengah]) < target:
            rendah = tengah + 1
        else:
            tinggi = tengah
    return rendah


def search_history(records: list, by: SortBy, target: Any) -> dict:
    """Cari satu catatan riwayat lewat binary search pada data terurut.

    Riwayatnya diurutkan dulu menurut `by`, karena binary search hanya
    sah pada data terurut. Hasilnya menyertakan jumlah langkah kedua
    metode supaya bedanya bisa dibandingkan.
    """
    terurut = sort_history(records, by=by)
    ambil = SORT_KEYS[by]

    indeks = binary_search_first(terurut, target, ambil)
    langkah_binary = 0
    n = len(terurut)
    while n > 0:
        n //= 2
        langkah_binary += 1

    return {
        "sorted": terurut,
        "index": indeks,
        "record": terurut[indeks] if indeks >= 0 else None,
        "linear_index": linear_search(terurut, target, ambil),
        "binary_steps": langkah_binary,
        "linear_steps": len(terurut),
    }
