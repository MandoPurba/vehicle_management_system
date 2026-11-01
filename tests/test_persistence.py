from pathlib import Path

from core.persistence import load_state, save_state, snapshot
from core.services import ParkingSystem


def _isi(system: ParkingSystem) -> None:
    system.registrasi("B 1 AAA", "Ani", "MOBIL")
    system.registrasi("B 2 BBB", "Budi", "MOTOR")
    system.registrasi("B 3 CCC", "Cici", "MOBIL")
    system.check_in("B 1 AAA")
    system.check_in("B 2 BBB")
    system.check_in("B 3 CCC")
    system.check_out("B 1 AAA")


def test_simpan_muat_mengembalikan_slot_antrean_riwayat_dan_undo(tmp_path: Path) -> None:
    system = ParkingSystem(capacity=2)
    _isi(system)
    path = tmp_path / "state.json"

    save_state(system, path)
    restored = load_state(path)

    assert snapshot(restored) == snapshot(system)
    dari_hash = restored.by_plate.get("B 3 CCC")
    dari_list = restored.vehicles.search("B 3 CCC", by="plate")
    assert dari_hash is dari_list
    assert dari_hash is not None
    assert dari_hash.status == "PARKED"
    assert restored.by_id.get("V001") is not None
    assert restored.by_id.get("V001").status == "EXITED"


def test_muat_state_kosong(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    save_state(ParkingSystem(capacity=2), path)
    restored = load_state(path)

    assert restored.vehicles.is_empty()
    assert restored.queue.is_empty()
    assert restored.undo.is_empty()
    assert restored.slots.capacity == 2


# ---- Penolakan file state yang rusak ----

import json

import pytest

from core.persistence import STATE_PATH


def _state_sah(tmp_path: Path) -> tuple[Path, dict]:
    path = tmp_path / "state.json"
    save_state(ParkingSystem(capacity=2), path)
    return path, json.loads(path.read_text(encoding="utf-8"))


def _tulis(path: Path, isi) -> None:
    path.write_text(json.dumps(isi), encoding="utf-8")


def test_file_tidak_ada(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_state(tmp_path / "hilang.json")


def test_isi_bukan_objek(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    _tulis(path, ["bukan", "objek"])

    with pytest.raises(ValueError, match="objek JSON"):
        load_state(path)


def test_kolom_hilang_disebutkan(tmp_path: Path) -> None:
    path, isi = _state_sah(tmp_path)
    del isi["queue"]
    _tulis(path, isi)

    with pytest.raises(ValueError, match="queue"):
        load_state(path)


def test_kapasitas_tidak_sah(tmp_path: Path) -> None:
    path, isi = _state_sah(tmp_path)
    for kapasitas in (0, -1, "dua", None):
        isi["capacity"] = kapasitas
        _tulis(path, isi)
        with pytest.raises(ValueError, match="kapasitas"):
            load_state(path)


def test_jumlah_slot_tidak_cocok_dengan_kapasitas(tmp_path: Path) -> None:
    path, isi = _state_sah(tmp_path)
    isi["slots"] = [None]  # kapasitasnya 2
    _tulis(path, isi)

    with pytest.raises(ValueError, match="jumlah slot"):
        load_state(path)


def test_bagian_yang_seharusnya_daftar(tmp_path: Path) -> None:
    path, isi = _state_sah(tmp_path)
    isi["vehicles"] = {"bukan": "daftar"}
    _tulis(path, isi)

    with pytest.raises(ValueError, match="harus daftar"):
        load_state(path)


def test_kendaraan_dengan_kolom_kosong(tmp_path: Path) -> None:
    path, isi = _state_sah(tmp_path)
    isi["vehicles"] = [
        {"vehicle_id": "V001", "plate": "", "owner": "Ani", "vtype": "MOBIL", "status": "REGISTERED"}
    ]
    _tulis(path, isi)

    with pytest.raises(ValueError, match="plate"):
        load_state(path)


def test_plat_atau_id_ganda_ditolak(tmp_path: Path) -> None:
    path, isi = _state_sah(tmp_path)
    kendaraan = {
        "vehicle_id": "V001", "plate": "B 1 AAA", "owner": "Ani",
        "vtype": "MOBIL", "status": "REGISTERED", "entry_time": None, "slot_index": None,
    }
    isi["vehicles"] = [kendaraan, dict(kendaraan)]
    _tulis(path, isi)

    with pytest.raises(ValueError, match="ganda"):
        load_state(path)


def test_penghuni_slot_yang_tidak_terdaftar(tmp_path: Path) -> None:
    path, isi = _state_sah(tmp_path)
    isi["slots"] = ["V999", None]
    _tulis(path, isi)

    with pytest.raises(ValueError, match="penghuni slot"):
        load_state(path)


def test_antrean_menyebut_id_asing(tmp_path: Path) -> None:
    path, isi = _state_sah(tmp_path)
    isi["queue"] = ["V999"]
    _tulis(path, isi)

    with pytest.raises(ValueError, match="tidak terdaftar"):
        load_state(path)

    isi["queue"] = [123]
    _tulis(path, isi)
    with pytest.raises(ValueError, match="tidak sah"):
        load_state(path)


def test_riwayat_tanpa_waktu(tmp_path: Path) -> None:
    path, isi = _state_sah(tmp_path)
    isi["history"] = [
        {"vehicle_id": "V001", "plate": "B 1 AAA", "slot_code": "A01",
         "entry_time": None, "exit_time": None}
    ]
    _tulis(path, isi)

    with pytest.raises(ValueError, match="waktu kosong"):
        load_state(path)


def test_waktu_bukan_teks_iso(tmp_path: Path) -> None:
    path, isi = _state_sah(tmp_path)
    isi["vehicles"] = [
        {"vehicle_id": "V001", "plate": "B 1 AAA", "owner": "Ani", "vtype": "MOBIL",
         "status": "PARKED", "entry_time": 12345, "slot_index": 0}
    ]
    _tulis(path, isi)

    with pytest.raises(ValueError, match="teks ISO"):
        load_state(path)


def test_undo_tanpa_waktu(tmp_path: Path) -> None:
    path, isi = _state_sah(tmp_path)
    isi["undo"] = [{"tx_type": "CHECK_IN", "vehicle_id": "V001", "time": None}]
    _tulis(path, isi)

    with pytest.raises(ValueError, match="waktu kosong"):
        load_state(path)


def test_lokasi_state_bisa_dipindah_lewat_env() -> None:
    """Dipakai saat jalan di container agar state tinggal di volume."""
    assert STATE_PATH.name == "state.json"


def test_simpan_membuat_direktori_induk(tmp_path: Path) -> None:
    path = tmp_path / "dalam" / "sekali" / "state.json"

    save_state(ParkingSystem(capacity=1), path)

    assert path.is_file()
    assert load_state(path).slots.capacity == 1
