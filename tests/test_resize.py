from core.models import MAX_SLOT_CAPACITY
from core.services import ParkingSystem


def _isi(system: ParkingSystem, jumlah: int) -> None:
    """Daftarkan `jumlah` kendaraan lalu check-in semuanya."""
    for n in range(1, jumlah + 1):
        plat = f"B {n} XYZ"
        system.registrasi(plat, f"Pemilik {n}", "MOBIL")
        system.check_in(plat)


def test_memperbesar_menarik_kendaraan_dari_antrean() -> None:
    system = ParkingSystem(capacity=2)
    _isi(system, 5)
    assert system.queue.size == 3

    hasil = system.resize_slots(4)

    assert hasil.ok
    assert system.slots.capacity == 4
    assert system.queue.size == 1
    assert hasil.data is not None
    assert hasil.data["promoted"] == ["B 3 XYZ", "B 4 XYZ"]
    naik = system.find("B 3 XYZ")
    assert naik is not None
    assert naik.status == "PARKED"
    assert naik.slot_index == 2
    assert naik.entry_time is not None
    # Yang masih mengantre tetap di antrean, urutannya tidak diacak.
    assert [v.plate for v in system.queue] == ["B 5 XYZ"]


def test_memperbesar_saat_antrean_kosong_hanya_menambah_slot_kosong() -> None:
    system = ParkingSystem(capacity=2)
    _isi(system, 2)

    hasil = system.resize_slots(5)

    assert hasil.ok
    assert system.slots.capacity == 5
    assert hasil.data is not None
    assert hasil.data["promoted"] == []
    assert [system.slots.get(i) for i in range(5)] == [
        "V001",
        "V002",
        None,
        None,
        None,
    ]


def test_memperkecil_membuang_slot_ekor_yang_kosong() -> None:
    system = ParkingSystem(capacity=5)
    _isi(system, 2)

    hasil = system.resize_slots(2)

    assert hasil.ok
    assert system.slots.capacity == 2
    assert system.statistics().data == {
        "total_slots": 2,
        "occupied_slots": 2,
        "available_slots": 0,
        "queue_len": 0,
        "total_served": 0,
    }


def test_memperkecil_ditolak_kalau_slot_ekor_masih_terisi() -> None:
    system = ParkingSystem(capacity=4)
    _isi(system, 4)

    hasil = system.resize_slots(2)

    assert not hasil.ok
    assert "A03, A04" in hasil.message
    assert system.slots.capacity == 4


def test_memperkecil_setelah_penghuni_ekor_check_out() -> None:
    system = ParkingSystem(capacity=3)
    _isi(system, 3)
    system.check_out("B 3 XYZ")

    assert system.resize_slots(2).ok
    assert system.slots.capacity == 2


def test_resize_mengosongkan_undo_agar_indeks_slot_tidak_basi() -> None:
    system = ParkingSystem(capacity=3)
    _isi(system, 3)
    system.check_out("B 3 XYZ")  # transaksi CHECK_OUT menyimpan slot_index 2
    assert len(system.undo) > 0

    assert system.resize_slots(2).ok

    assert system.undo.is_empty()
    assert not system.undo_last().ok


def test_resize_menolak_angka_di_luar_batas() -> None:
    system = ParkingSystem(capacity=5)

    assert not system.resize_slots(0).ok
    assert not system.resize_slots(-3).ok
    assert not system.resize_slots(MAX_SLOT_CAPACITY + 1).ok
    assert not system.resize_slots(5).ok  # sama dengan kapasitas sekarang
    assert system.slots.capacity == 5
