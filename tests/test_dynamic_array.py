import pytest

from core.models import slot_code
from core.structures.dynamic_array import DynamicArray, ParkingSlots


# ---- DynamicArray ----

def test_array_kosong() -> None:
    arr = DynamicArray()

    assert len(arr) == 0
    assert arr.capacity >= 1
    with pytest.raises(IndexError, match="Array kosong"):
        arr.pop()


def test_buffer_digandakan_saat_penuh() -> None:
    arr = DynamicArray(capacity=2)
    awal = arr.capacity

    for i in range(5):
        arr.append(i)

    assert len(arr) == 5
    assert arr.capacity > awal  # digandakan, bukan gagal
    assert [arr.get(i) for i in range(5)] == [0, 1, 2, 3, 4]


def test_kapasitas_minimal_satu() -> None:
    assert DynamicArray(capacity=0).capacity == 1
    assert DynamicArray(capacity=-5).capacity == 1


def test_get_dan_set_di_luar_jangkauan_ditolak() -> None:
    arr = DynamicArray(capacity=4)
    arr.append("a")

    assert arr.get(0) == "a"
    arr.set(0, "b")
    assert arr.get(0) == "b"

    # Indeks 1 masih di dalam buffer fisik, tapi di luar panjang logis.
    for salah in (1, 2, -1, 99):
        with pytest.raises(IndexError, match="di luar jangkauan"):
            arr.get(salah)
        with pytest.raises(IndexError, match="di luar jangkauan"):
            arr.set(salah, "x")


def test_pop_menurunkan_panjang_logis_bukan_kapasitas() -> None:
    arr = DynamicArray(capacity=4)
    for huruf in "abc":
        arr.append(huruf)
    kapasitas = arr.capacity

    assert arr.pop() == "c"
    assert len(arr) == 2
    assert arr.capacity == kapasitas  # buffer fisik tidak dikecilkan
    with pytest.raises(IndexError):
        arr.get(2)  # slot yang dilepas tidak bisa dibaca lagi


def test_pop_sampai_kosong_lalu_append_lagi() -> None:
    arr = DynamicArray(capacity=2)
    arr.append("a")
    arr.pop()

    arr.append("b")

    assert len(arr) == 1
    assert arr.get(0) == "b"


# ---- ParkingSlots ----

def test_slot_mulai_kosong_semua() -> None:
    slots = ParkingSlots(3)

    assert slots.capacity == 3
    assert [slots.get(i) for i in range(3)] == [None, None, None]
    assert slots.find_available() == 0
    assert not slots.is_full()


def test_isi_dan_kosongkan_slot() -> None:
    slots = ParkingSlots(2)

    slots.assign(0, "V001")
    assert slots.get(0) == "V001"
    assert slots.find_available() == 1

    slots.assign(1, "V002")
    assert slots.is_full()
    assert slots.find_available() == -1

    slots.release(0)
    assert slots.get(0) is None
    assert slots.find_available() == 0
    assert not slots.is_full()


def test_find_available_memberi_slot_kosong_pertama() -> None:
    slots = ParkingSlots(4)
    for i in (0, 1, 2, 3):
        slots.assign(i, f"V00{i}")
    slots.release(2)

    assert slots.find_available() == 2


def test_resize_memperbesar_dan_memperkecil() -> None:
    slots = ParkingSlots(2)
    slots.assign(0, "V001")

    slots.resize(5)
    assert slots.capacity == 5
    assert slots.get(0) == "V001"  # penghuni lama tidak hilang
    assert [slots.get(i) for i in range(1, 5)] == [None] * 4

    slots.resize(1)
    assert slots.capacity == 1
    assert slots.get(0) == "V001"
    with pytest.raises(IndexError):
        slots.get(1)


def test_resize_menolak_kapasitas_nol_atau_negatif() -> None:
    slots = ParkingSlots(3)

    for salah in (0, -1):
        with pytest.raises(ValueError, match="minimal 1"):
            slots.resize(salah)
    assert slots.capacity == 3


def test_kode_slot_mengikuti_indeks() -> None:
    assert slot_code(0) == "A01"
    assert slot_code(4) == "A05"
    assert slot_code(99) == "A100"
