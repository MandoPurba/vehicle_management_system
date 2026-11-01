import json

import pytest

from core.sample_data import DEFAULT_PATH, load_sample_data, read_rows
from core.services import ParkingSystem


def test_baca_data_contoh_bawaan() -> None:
    rows = read_rows()

    assert len(rows) == 24
    assert all(r["plate"] and r["owner"] and r["vtype"] for r in rows)
    assert {r["vtype"] for r in rows} == {"MOBIL", "MOTOR"}
    assert len({r["plate"] for r in rows}) == len(rows)  # plat tidak boleh ganda


def test_urutan_baris_parked_sebelum_waiting() -> None:
    """Loader mengandalkan urutan: PARKED mengisi slot, sisanya mengantre."""
    peringkat = {"PARKED": 0, "WAITING": 1, "REGISTERED": 2}
    urutan = [peringkat[r["initial_status"]] for r in read_rows()]

    assert urutan == sorted(urutan)


def test_muat_mengisi_slot_antrean_dan_pendaftaran() -> None:
    system = ParkingSystem(capacity=5)

    hasil = load_sample_data(system)

    assert all(r.ok for r in hasil)
    assert system.vehicles.size == 24
    stats = system.statistics().data
    assert stats["occupied_slots"] == 5
    assert stats["queue_len"] == 2
    assert sum(1 for v in system.vehicles if v.status == "REGISTERED") == 17


def test_waktu_masuk_disebar_tidak_semuanya_sama() -> None:
    system = ParkingSystem(capacity=5)
    load_sample_data(system)

    waktu = [v.entry_time for v in system.vehicles if v.status == "PARKED"]

    assert len(waktu) == 5
    assert len(set(waktu)) == 5  # berjenjang, bukan serentak
    assert max(waktu) > min(waktu)


def test_muat_dua_kali_tidak_menggandakan() -> None:
    system = ParkingSystem(capacity=5)
    load_sample_data(system)

    kedua = load_sample_data(system)

    assert system.vehicles.size == 24
    assert not any(r.ok for r in kedua[:24])  # semua registrasi ditolak


def test_slot_lebih_banyak_membuat_antrean_kosong() -> None:
    system = ParkingSystem(capacity=20)
    load_sample_data(system)

    assert system.statistics().data["queue_len"] == 0
    assert system.statistics().data["occupied_slots"] == 7


def test_file_tidak_ada(tmp_path) -> None:
    with pytest.raises(FileNotFoundError):
        read_rows(tmp_path / "hilang.json")


def test_file_bukan_daftar_atau_kosong(tmp_path) -> None:
    kosong = tmp_path / "kosong.json"
    kosong.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="tidak boleh kosong"):
        read_rows(kosong)

    objek = tmp_path / "objek.json"
    objek.write_text('{"plate": "B 1 AAA"}', encoding="utf-8")
    with pytest.raises(ValueError):
        read_rows(objek)


def test_kolom_yang_kurang_disebut_beserta_nomor_barisnya(tmp_path) -> None:
    rusak = tmp_path / "rusak.json"
    rusak.write_text(
        json.dumps(
            [
                {"plate": "B 1 AAA", "owner": "Ani", "vtype": "MOBIL", "initial_status": "PARKED"},
                {"plate": "B 2 BBB", "owner": "", "vtype": "MOBIL", "initial_status": "PARKED"},
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="baris 2"):
        read_rows(rusak)


def test_prioritas_terbawa_dari_file() -> None:
    system = ParkingSystem(capacity=5)
    load_sample_data(system)

    prioritas = {v.priority for v in system.vehicles}

    assert prioritas == {"UMUM", "DOSEN", "TAMU", "DISABILITAS"}
    assert DEFAULT_PATH.name == "sample_data.json"
