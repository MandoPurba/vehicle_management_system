from core.models import Vehicle
from core.structures.queue import WaitingQueue


def _kendaraan(plate: str) -> Vehicle:
    return Vehicle(f"V-{plate}", plate, "Pemilik", "MOBIL")


def test_antrean_kosong() -> None:
    queue = WaitingQueue()

    assert queue.is_empty()
    assert queue.size == 0
    assert len(queue) == 0
    assert queue.peek() is None
    assert queue.dequeue() is None
    assert queue.remove_rear() is None
    assert queue.display() == []


def test_fifo_yang_pertama_masuk_pertama_keluar() -> None:
    queue = WaitingQueue()
    for i in range(1, 4):
        queue.enqueue(_kendaraan(f"B {i} AAA"))

    assert queue.size == 3
    assert queue.peek().plate == "B 1 AAA"
    assert [queue.dequeue().plate for _ in range(3)] == ["B 1 AAA", "B 2 AAA", "B 3 AAA"]
    assert queue.is_empty()


def test_peek_tidak_mengeluarkan_isi() -> None:
    queue = WaitingQueue()
    queue.enqueue(_kendaraan("B 1 AAA"))

    assert queue.peek().plate == "B 1 AAA"
    assert queue.peek().plate == "B 1 AAA"
    assert queue.size == 1


def test_push_front_menyalip_ke_depan() -> None:
    queue = WaitingQueue()
    queue.enqueue(_kendaraan("B 1 AAA"))
    queue.enqueue(_kendaraan("B 2 BBB"))

    queue.push_front(_kendaraan("B 9 ZZZ"))

    assert [v.plate for v in queue] == ["B 9 ZZZ", "B 1 AAA", "B 2 BBB"]
    assert queue.size == 3


def test_push_front_ke_antrean_kosong() -> None:
    queue = WaitingQueue()
    queue.push_front(_kendaraan("B 1 AAA"))

    assert queue.size == 1
    assert queue.peek().plate == "B 1 AAA"
    assert queue.dequeue().plate == "B 1 AAA"
    assert queue.is_empty()


def test_remove_rear_membuang_yang_paling_belakang() -> None:
    queue = WaitingQueue()
    for i in range(1, 4):
        queue.enqueue(_kendaraan(f"B {i} AAA"))

    assert queue.remove_rear().plate == "B 3 AAA"
    assert [v.plate for v in queue] == ["B 1 AAA", "B 2 AAA"]

    # Sampai menyisakan satu, lalu kosong.
    queue.remove_rear()
    assert queue.remove_rear().plate == "B 1 AAA"
    assert queue.is_empty()
    assert queue.peek() is None


def test_enqueue_lagi_setelah_antrean_habis() -> None:
    """Rear harus ikut direset saat antrean kosong, bukan menunjuk simpul lama."""
    queue = WaitingQueue()
    queue.enqueue(_kendaraan("B 1 AAA"))
    queue.dequeue()

    queue.enqueue(_kendaraan("B 2 BBB"))

    assert queue.size == 1
    assert [v.plate for v in queue] == ["B 2 BBB"]
