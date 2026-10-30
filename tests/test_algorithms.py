import random
from datetime import datetime, timedelta

from core.algorithms.recursion import (
    count_occupied_recursive,
    max_duration_recursive,
    sum_costs_recursive,
)
from core.algorithms.searching import (
    binary_search,
    binary_search_first,
    linear_search,
    lower_bound,
    search_history,
)
from core.algorithms.sorting import (
    bubble_sort,
    insertion_sort,
    merge_sort,
    quick_sort,
    sort_history,
)
from core.models import HistoryRecord, hitung_biaya
from core.services import ParkingSystem

AWAL = datetime(2026, 10, 30, 8, 0, 0)


def _riwayat() -> list[HistoryRecord]:
    return [
        HistoryRecord("V001", "B 3 CCC", "A03", AWAL, AWAL + timedelta(hours=3), "MOBIL"),
        HistoryRecord("V002", "B 1 AAA", "A01", AWAL + timedelta(hours=1), AWAL + timedelta(hours=2), "MOTOR"),
        HistoryRecord("V003", "B 2 BBB", "A02", AWAL - timedelta(hours=1), AWAL + timedelta(hours=5), "MOBIL"),
    ]


def test_semua_sorting_memberi_hasil_yang_sama() -> None:
    random.seed(3)
    data = [random.randint(0, 999) for _ in range(300)]
    benar = sorted(data)

    for fungsi in (merge_sort, insertion_sort, bubble_sort, quick_sort):
        assert fungsi(data) == benar, fungsi.__name__
        assert data[:3] == data[:3]  # masukan tidak diubah


def test_sorting_pada_kasus_tepi() -> None:
    for fungsi in (merge_sort, insertion_sort, bubble_sort, quick_sort):
        assert fungsi([]) == []
        assert fungsi([1]) == [1]
        assert fungsi([2, 2, 2]) == [2, 2, 2]
        assert fungsi([3, 2, 1]) == [1, 2, 3]


def test_merge_sort_stabil() -> None:
    data = [("a", 1), ("b", 1), ("c", 0)]

    assert merge_sort(data, key=lambda p: p[1]) == [("c", 0), ("a", 1), ("b", 1)]


def test_quick_sort_tahan_data_terurut() -> None:
    # Pivot buruk pada data terurut dulu berarti kedalaman rekursi n.
    urut = list(range(20_000))

    assert quick_sort(urut) == urut


def test_binary_search_pada_data_terurut() -> None:
    data = list(range(0, 200, 2))

    assert binary_search(data, 100) == 50
    assert binary_search(data, 101) == -1
    assert binary_search([], 1) == -1
    assert linear_search(data, 100) == binary_search(data, 100)


def test_binary_search_first_dan_lower_bound() -> None:
    data = [1, 2, 2, 2, 5, 8]

    assert binary_search_first(data, 2) == 1
    assert lower_bound(data, 2) == 1
    assert lower_bound(data, 3) == 4
    assert lower_bound(data, 100) == len(data)


def test_urut_riwayat_menurut_waktu_durasi_dan_biaya() -> None:
    riwayat = _riwayat()

    assert [r.plate for r in sort_history(riwayat, "entry_time")] == ["B 2 BBB", "B 3 CCC", "B 1 AAA"]
    assert [r.plate for r in sort_history(riwayat, "duration")] == ["B 1 AAA", "B 3 CCC", "B 2 BBB"]
    assert [r.plate for r in sort_history(riwayat, "cost")] == ["B 1 AAA", "B 3 CCC", "B 2 BBB"]
    assert [r.plate for r in sort_history(riwayat, "plate")] == ["B 1 AAA", "B 2 BBB", "B 3 CCC"]
    menurun = sort_history(riwayat, "cost", descending=True)
    assert menurun[0].plate == "B 2 BBB"
    for algo in ("merge", "quick", "insertion", "bubble"):
        assert [r.plate for r in sort_history(riwayat, "cost", algorithm=algo)] == [
            "B 1 AAA",
            "B 3 CCC",
            "B 2 BBB",
        ]


def test_cari_riwayat_lewat_binary_search() -> None:
    riwayat = _riwayat()

    hasil = search_history(riwayat, "plate", "B 2 BBB")

    assert hasil["record"] is not None
    assert hasil["record"].plate == "B 2 BBB"
    assert hasil["index"] == hasil["linear_index"]
    assert hasil["binary_steps"] < hasil["linear_steps"]
    assert search_history(riwayat, "plate", "Z 9 ZZZ")["record"] is None


def test_biaya_kampus_proporsional_per_menit() -> None:
    # Tarif kampus: MOBIL 2.000/jam, MOTOR 1.000/jam, per menit.
    assert hitung_biaya("MOBIL", timedelta(hours=1)) == 2000
    assert hitung_biaya("MOBIL", timedelta(minutes=30)) == 1000
    assert hitung_biaya("MOTOR", timedelta(hours=1)) == 1000
    assert hitung_biaya("MOTOR", timedelta(hours=8)) == 8000
    # Dibulatkan ke atas ke ratusan, jadi sebentar pun tetap kena Rp 100.
    assert hitung_biaya("MOBIL", timedelta(minutes=1)) == 100
    assert hitung_biaya("MOBIL", timedelta(seconds=5)) == 100
    # Keluar tanpa sempat parkir tidak ditagih.
    assert hitung_biaya("MOBIL", timedelta(0)) == 0
    assert hitung_biaya("MOTOR", timedelta(0)) == 0
    # Dua kali lebih lama berarti dua kali lebih mahal, tanpa lompatan per jam.
    assert hitung_biaya("MOBIL", timedelta(hours=2)) == 2 * hitung_biaya("MOBIL", timedelta(hours=1))


def test_fungsi_rekursif_dipakai_statistik_sistem() -> None:
    system = ParkingSystem(capacity=4)
    for plat in ("B 1 AAA", "B 2 BBB"):
        system.registrasi(plat, "x", "MOBIL")
        system.check_in(plat)

    assert count_occupied_recursive(system.slots) == 2
    assert system.statistics().data["occupied_slots"] == 2

    riwayat = _riwayat()
    assert sum_costs_recursive(riwayat) == sum(r.cost for r in riwayat)
    assert max_duration_recursive(riwayat) == 360
    assert sum_costs_recursive([]) == 0
    assert max_duration_recursive([]) == 0
