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
