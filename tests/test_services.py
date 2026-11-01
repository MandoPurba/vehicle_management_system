"""Jalur gagal dan aturan ParkingSystem, bukan hanya jalur yang mulus."""

from core.services import ParkingSystem


def _sistem_terisi(capacity: int = 2) -> ParkingSystem:
    system = ParkingSystem(capacity=capacity)
    system.registrasi("B 1 AAA", "Ani", "MOBIL")
    system.registrasi("B 2 BBB", "Budi", "MOTOR")
    return system


# ---- Registrasi ----

def test_registrasi_menolak_plat_yang_sudah_terdaftar() -> None:
    system = ParkingSystem()
    pertama = system.registrasi("B 1 AAA", "Ani", "MOBIL")

    kedua = system.registrasi("B 1 AAA", "Orang Lain", "MOTOR")

    assert pertama.ok
    assert not kedua.ok
    assert "sudah terdaftar" in kedua.message
    assert system.vehicles.size == 1  # tidak ada data ganda yang masuk
    assert system.find("B 1 AAA").owner == "Ani"


def test_registrasi_menolak_field_kosong() -> None:
    system = ParkingSystem()

    assert not system.registrasi("", "Ani", "MOBIL").ok
    assert not system.registrasi("B 1 AAA", "", "MOBIL").ok
    assert not system.registrasi("B 1 AAA", "Ani", "").ok
    assert system.vehicles.is_empty()
    assert system.registrasi("", "", "").message == "Semua field harus diisi"


def test_id_kendaraan_berurutan_dan_terindeks() -> None:
    system = ParkingSystem()
    for plat in ("B 1 AAA", "B 2 BBB", "B 3 CCC"):
        system.registrasi(plat, "x", "MOBIL")

    assert [v.vehicle_id for v in system.vehicles] == ["V001", "V002", "V003"]
    # Objek yang sama harus ada di ketiga indeks.
    kendaraan = system.find("B 2 BBB")
    assert system.find("V002", by="id") is kendaraan
    assert system.vehicle_tree.search("B 2 BBB") is kendaraan


# ---- Check-in ----

def test_check_in_menolak_plat_tak_dikenal() -> None:
    system = ParkingSystem()

    hasil = system.check_in("Z 999 ZZZ")

    assert not hasil.ok
    assert "tidak ditemukan" in hasil.message


def test_check_in_dua_kali_ditolak() -> None:
    system = _sistem_terisi()
    system.check_in("B 1 AAA")

    hasil = system.check_in("B 1 AAA")

    assert not hasil.ok
    assert "sudah PARKED" in hasil.message


def test_kendaraan_yang_mengantre_tidak_bisa_check_in_lagi() -> None:
    system = ParkingSystem(capacity=1)
    system.registrasi("B 1 AAA", "Ani", "MOBIL")
    system.registrasi("B 2 BBB", "Budi", "MOBIL")
    system.check_in("B 1 AAA")
    system.check_in("B 2 BBB")  # masuk antrean

    hasil = system.check_in("B 2 BBB")

    assert not hasil.ok
    assert "sudah WAITING" in hasil.message
    assert system.queue.size == 1


def test_kendaraan_yang_sudah_keluar_boleh_masuk_lagi() -> None:
    system = _sistem_terisi()
    system.check_in("B 1 AAA")
    system.check_out("B 1 AAA")

    hasil = system.check_in("B 1 AAA")

    assert hasil.ok
    assert system.find("B 1 AAA").status == "PARKED"


# ---- Check-out ----

def test_check_out_menolak_yang_tidak_sedang_parkir() -> None:
    system = _sistem_terisi()

    assert not system.check_out("B 1 AAA").ok  # baru terdaftar
    assert not system.check_out("Z 999 ZZZ").ok  # tidak ada
    assert system.check_out("B 1 AAA").message == "Kendaraan tidak sedang parkir"


def test_check_out_mengosongkan_slot_dan_mencatat_riwayat() -> None:
    system = _sistem_terisi()
    system.check_in("B 1 AAA")

    hasil = system.check_out("B 1 AAA")

    assert hasil.ok
    assert system.slots.get(0) is None
    assert system.find("B 1 AAA").status == "EXITED"
    assert system.find("B 1 AAA").slot_index is None
    assert system.history.size == 1
    assert system.history.last().plate == "B 1 AAA"


# ---- Pencarian ----

def test_search_tiga_kunci_dan_yang_tidak_ketemu() -> None:
    system = _sistem_terisi()

    assert system.search("B 1 AAA").ok
    assert system.search("V002", by="id").data.plate == "B 2 BBB"
    assert system.search("Budi", by="owner").data.plate == "B 2 BBB"

    gagal = system.search("Z 999 ZZZ")
    assert not gagal.ok
    assert gagal.data is None


# ---- Undo ----

def test_undo_pada_sistem_kosong() -> None:
    hasil = ParkingSystem().undo_last()

    assert not hasil.ok
    assert "Tidak ada transaksi" in hasil.message


def test_undo_check_out_mengembalikan_kendaraan_ke_slotnya() -> None:
    system = _sistem_terisi()
    system.check_in("B 1 AAA")
    masuk = system.find("B 1 AAA").entry_time
    system.check_out("B 1 AAA")

    assert system.undo_last().ok

    kendaraan = system.find("B 1 AAA")
    assert kendaraan.status == "PARKED"
    assert kendaraan.slot_index == 0
    assert kendaraan.entry_time == masuk  # waktu masuk asli dipulihkan
    assert system.history.size == 0
    assert system.slots.get(0) == kendaraan.vehicle_id


def test_undo_check_in_mengosongkan_slot_lagi() -> None:
    system = _sistem_terisi()
    system.check_in("B 1 AAA")

    assert system.undo_last().ok

    kendaraan = system.find("B 1 AAA")
    assert kendaraan.status == "REGISTERED"
    assert kendaraan.slot_index is None
    assert kendaraan.entry_time is None
    assert system.slots.get(0) is None


# ---- Laporan ----

def test_statistik_mengikuti_keadaan_sistem() -> None:
    system = ParkingSystem(capacity=2)
    for plat in ("B 1 AAA", "B 2 BBB", "B 3 CCC"):
        system.registrasi(plat, "x", "MOBIL")
        system.check_in(plat)
    system.check_out("B 1 AAA")

    stats = system.statistics().data

    assert stats["total_slots"] == 2
    assert stats["occupied_slots"] == 2  # B 3 CCC naik dari antrean
    assert stats["available_slots"] == 0
    assert stats["queue_len"] == 0
    assert stats["total_served"] == 1


def test_show_slots_dan_show_queue_kosong() -> None:
    system = ParkingSystem(capacity=2)

    slots = system.show_slots().data
    assert slots == [("A01", None), ("A02", None)]
    assert system.show_queue().data == []
    assert system.show_history().data == []
