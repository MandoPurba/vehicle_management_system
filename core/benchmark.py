"""Pengukuran waktu eksekusi struktur data dan algoritma pada n bertingkat."""

import random
from time import perf_counter

from core.algorithms.searching import binary_search, linear_search
from core.algorithms.sorting import insertion_sort, merge_sort, quick_sort
from core.models import Vehicle
from core.structures.bst import BST
from core.structures.dynamic_array import DynamicArray
from core.structures.hash_table import HashTable
from core.structures.heap import MinHeap
from core.structures.linked_list import VehicleList

UKURAN: tuple[int, ...] = (1_000, 10_000, 100_000)

# Batas n untuk algoritma O(n^2). Di n = 100.000 bubble/insertion sort butuh
# sekitar 10^10 perbandingan, jadi sengaja dilewati, bukan dijalankan.
BATAS_KUADRATIK = 10_000

# Operasi O(n) hanya diukur beberapa kali lalu dirata-rata, supaya satu
# baris benchmark tidak menghabiskan waktu lebih lama dari seluruh halaman.
PROBE_CEPAT = 1_000
PROBE_LAMBAT = 20


def _plates(n: int) -> list[str]:
    return [f"B {i:06d} XYZ" for i in range(n)]


def _ukur(fn, ulang: int = 1) -> float:
    """Waktu rata-rata sekali jalan `fn`, dalam detik."""
    awal = perf_counter()
    for _ in range(ulang):
        fn()
    return (perf_counter() - awal) / ulang


def _baris(operasi: str, struktur: str, kompleksitas: str, n: int, detik: float | None) -> dict:
    return {
        "operasi": operasi,
        "struktur": struktur,
        "kompleksitas": kompleksitas,
        "n": n,
        "detik": detik,
        "per_operasi_us": None if detik is None else detik * 1_000_000,
    }


def benchmark_sisip(n: int) -> list[dict]:
    """Waktu memasukkan n data ke tiap struktur."""
    plates = _plates(n)
    teracak = plates[:]
    random.shuffle(teracak)
    hasil = []

    def hash_put() -> None:
        tabel: HashTable[int] = HashTable()
        for i, p in enumerate(plates):
            tabel.put(p, i)

    def bst_acak() -> None:
        pohon = BST()
        for p in teracak:
            pohon.insert(p)

    def array_append() -> None:
        arr = DynamicArray()
        for p in plates:
            arr.append(p)

    def list_insert() -> None:
        daftar = VehicleList()
        for i, p in enumerate(plates):
            daftar.insert(Vehicle(f"V{i}", p, "x", "MOBIL"))

    def heap_push() -> None:
        heap = MinHeap()
        for i, p in enumerate(teracak):
            heap.push(p, i)

    hasil.append(_baris(f"Sisip {n:,} data", "Hash Table", "O(1) amortized", n, _ukur(hash_put)))
    hasil.append(_baris(f"Sisip {n:,} data", "BST (data teracak)", "O(n log n)", n, _ukur(bst_acak)))
    hasil.append(_baris(f"Sisip {n:,} data", "Dynamic Array", "O(1) amortized", n, _ukur(array_append)))
    hasil.append(_baris(f"Sisip {n:,} data", "Linked List", "O(1) di tail", n, _ukur(list_insert)))
    hasil.append(_baris(f"Sisip {n:,} data", "Min Heap", "O(log n)", n, _ukur(heap_push)))
    return hasil


def benchmark_cari(n: int) -> list[dict]:
    """Waktu rata-rata satu pencarian pada tiap struktur."""
    plates = _plates(n)
    teracak = plates[:]
    random.shuffle(teracak)
    random.seed(7)
    target_cepat = [random.choice(plates) for _ in range(PROBE_CEPAT)]
    target_lambat = [random.choice(plates) for _ in range(PROBE_LAMBAT)]

    tabel: HashTable[int] = HashTable()
    for i, p in enumerate(plates):
        tabel.put(p, i)

    pohon = BST()
    for p in teracak:
        pohon.insert(p)

    daftar = VehicleList()
    for i, p in enumerate(plates):
        daftar.insert(Vehicle(f"V{i}", p, "x", "MOBIL"))

    terurut = plates  # _plates sudah terurut naik

    return [
        _baris("Cari 1 plat", "Hash Table", "O(1)", n,
               _ukur(lambda: [tabel.get(t) for t in target_cepat]) / PROBE_CEPAT),
        _baris("Cari 1 plat", "BST", "O(log n)", n,
               _ukur(lambda: [pohon.search(t) for t in target_cepat]) / PROBE_CEPAT),
        _baris("Cari 1 plat", "Binary Search", "O(log n)", n,
               _ukur(lambda: [binary_search(terurut, t) for t in target_cepat]) / PROBE_CEPAT),
        _baris("Cari 1 plat", "Linear Search", "O(n)", n,
               _ukur(lambda: [linear_search(terurut, t) for t in target_lambat]) / PROBE_LAMBAT),
        _baris("Cari 1 plat", "Linked List", "O(n)", n,
               _ukur(lambda: [daftar.search(t) for t in target_lambat]) / PROBE_LAMBAT),
    ]


def benchmark_urut(n: int) -> list[dict]:
    """Waktu mengurutkan n data. Algoritma O(n^2) dilewati di n besar."""
    random.seed(11)
    data = [random.randint(0, n * 10) for _ in range(n)]
    hasil = [
        _baris(f"Urut {n:,} data", "Merge Sort", "O(n log n)", n, _ukur(lambda: merge_sort(data))),
        _baris(f"Urut {n:,} data", "Quick Sort", "O(n log n)", n, _ukur(lambda: quick_sort(data))),
    ]
    if n <= BATAS_KUADRATIK:
        hasil.append(
            _baris(f"Urut {n:,} data", "Insertion Sort", "O(n^2)", n,
                   _ukur(lambda: insertion_sort(data)))
        )
    else:
        hasil.append(_baris(f"Urut {n:,} data", "Insertion Sort", "O(n^2)", n, None))
    return hasil


def benchmark_bentuk_bst(n: int) -> list[dict]:
    """Bandingkan BST yang seimbang dengan yang merosot jadi rantai."""
    plates = _plates(min(n, 5_000))
    m = len(plates)
    teracak = plates[:]
    random.shuffle(teracak)

    acak = BST()
    awal = perf_counter()
    for p in teracak:
        acak.insert(p)
    detik_acak = perf_counter() - awal

    urut = BST()
    awal = perf_counter()
    for p in plates:
        urut.insert(p)
    detik_urut = perf_counter() - awal

    return [
        {"n": m, "kondisi": "Data teracak", "tinggi": acak.height(),
         "detik": detik_acak, "kompleksitas": "O(n log n)"},
        {"n": m, "kondisi": "Data sudah terurut", "tinggi": urut.height(),
         "detik": detik_urut, "kompleksitas": "O(n^2) — pohon jadi rantai"},
    ]


def run_benchmark(sizes: tuple[int, ...] = UKURAN) -> dict:
    """Jalankan seluruh pengukuran untuk tiap n."""
    sisip: list[dict] = []
    cari: list[dict] = []
    urut: list[dict] = []
    for n in sizes:
        sisip.extend(benchmark_sisip(n))
        cari.extend(benchmark_cari(n))
        urut.extend(benchmark_urut(n))
    return {
        "sizes": list(sizes),
        "sisip": sisip,
        "cari": cari,
        "urut": urut,
        "bentuk_bst": benchmark_bentuk_bst(max(sizes)),
        "batas_kuadratik": BATAS_KUADRATIK,
    }
