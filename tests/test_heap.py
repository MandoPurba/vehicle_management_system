from core.models import Vehicle
from core.services import ParkingSystem
from core.structures.heap import MinHeap, PriorityWaitingQueue


def _kendaraan(plate: str, priority: str = "UMUM") -> Vehicle:
    return Vehicle(f"V-{plate}", plate, "x", "MOBIL", priority=priority)


def test_minheap_mengeluarkan_kunci_terkecil_lebih_dulu() -> None:
    heap = MinHeap()
    for kunci in (5, 3, 9, 1, 7, 2):
        heap.push(kunci, f"n{kunci}")

    assert heap.peek_key() == 1
    assert [heap.pop() for _ in range(6)] == ["n1", "n2", "n3", "n5", "n7", "n9"]
    assert heap.is_empty()
    assert heap.pop() is None


def test_minheap_menjaga_invarian_induk_lebih_kecil() -> None:
    heap = MinHeap()
    for kunci in range(20, 0, -1):
        heap.push(kunci, kunci)

    entri = heap.entries()
    for i in range(1, len(entri)):
        induk = (i - 1) // 2
        assert entri[induk][0] <= entri[i][0]


def test_minheap_remove_at_memperbaiki_bentuk() -> None:
    heap = MinHeap()
    for kunci in (5, 3, 9, 1, 7):
        heap.push(kunci, kunci)

    assert heap.remove_at(2) is not None
    assert heap.sorted_values() == sorted(heap.sorted_values())
    assert len(heap) == 4
    assert heap.remove_at(99) is None


def test_antrean_melayani_prioritas_lebih_dulu() -> None:
    queue = PriorityWaitingQueue()
    for plate, prio in [
        ("UMUM-1", "UMUM"),
        ("DOSEN-1", "DOSEN"),
        ("UMUM-2", "UMUM"),
        ("DIFABEL", "DISABILITAS"),
        ("TAMU-1", "TAMU"),
    ]:
        queue.enqueue(_kendaraan(plate, prio))

    assert [v.plate for v in queue] == [
        "DIFABEL", "DOSEN-1", "TAMU-1", "UMUM-1", "UMUM-2",
    ]
    assert queue.size == 5
    assert queue.group_counts()["UMUM"] == 2


def test_prioritas_sama_tetap_fifo() -> None:
    queue = PriorityWaitingQueue()
    for i in range(5):
        queue.enqueue(_kendaraan(f"UMUM-{i}"))

    assert [v.plate for v in queue] == [f"UMUM-{i}" for i in range(5)]
    assert queue.dequeue().plate == "UMUM-0"
    assert queue.dequeue().plate == "UMUM-1"


def test_requeue_front_mengembalikan_ke_depan() -> None:
    queue = PriorityWaitingQueue()
    for i in range(3):
        queue.enqueue(_kendaraan(f"UMUM-{i}"))
    terdepan = queue.dequeue()

    queue.requeue_front(terdepan)

    assert [v.plate for v in queue] == ["UMUM-0", "UMUM-1", "UMUM-2"]


def test_remove_vehicle_mencabut_yang_ditunjuk() -> None:
    queue = PriorityWaitingQueue()
    for plate, prio in [("DOSEN-1", "DOSEN"), ("UMUM-1", "UMUM"), ("UMUM-2", "UMUM")]:
        queue.enqueue(_kendaraan(plate, prio))

    assert queue.remove_vehicle("V-UMUM-1").plate == "UMUM-1"
    assert [v.plate for v in queue] == ["DOSEN-1", "UMUM-2"]
    assert queue.remove_vehicle("V-TIDAK-ADA") is None
    assert queue.remove_last_enqueued().plate == "UMUM-2"
    assert PriorityWaitingQueue().remove_last_enqueued() is None


def test_check_out_menaikkan_yang_paling_berprioritas() -> None:
    system = ParkingSystem(capacity=1)
    system.registrasi("B 1 AAA", "Ani", "MOBIL")
    system.check_in("B 1 AAA")
    for plat, prio in [("B 2 UMU", "UMUM"), ("B 3 DOS", "DOSEN"), ("B 4 DIS", "DISABILITAS")]:
        system.registrasi(plat, "x", "MOBIL", prio)
        system.check_in(plat)

    hasil = system.check_out("B 1 AAA")

    assert "B 4 DIS" in hasil.message
    naik = system.find("B 4 DIS")
    assert naik is not None and naik.status == "PARKED"
    assert [v.plate for v in system.queue] == ["B 3 DOS", "B 2 UMU"]


def test_undo_enqueue_mencabut_kendaraan_yang_benar() -> None:
    system = ParkingSystem(capacity=1)
    system.registrasi("B 1 AAA", "Ani", "MOBIL")
    system.check_in("B 1 AAA")
    system.registrasi("B 9 DOS", "D", "MOBIL", "DOSEN")
    system.check_in("B 9 DOS")
    system.registrasi("B 8 UMU", "U", "MOBIL", "UMUM")
    system.check_in("B 8 UMU")

    assert system.undo_last().ok

    # Yang dicabut harus yang terakhir masuk antrean, bukan yang paling belakang dilayani.
    assert [v.plate for v in system.queue] == ["B 9 DOS"]
    dicabut = system.find("B 8 UMU")
    assert dicabut is not None and dicabut.status == "REGISTERED"
