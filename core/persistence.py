"""Simpan dan muat seluruh state parkir ke data/state.json.

Hash table dan bentuk pohon riwayat tidak ditulis ke file. Saat muat,
indeks plat dan id dibangun ulang dari daftar kendaraan, objek yang sama
dipakai antrean serta slot, dan riwayat disisipkan ulang satu per satu ke
HistoryTree.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import cast

from core.models import (
    HistoryRecord,
    Transaction,
    TxType,
    Vehicle,
    VehicleStatus,
    VehicleType,
)
from core.services import ParkingSystem

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
STATE_PATH = DATA_DIR / "state.json"

_SNAPSHOT_KEYS = ("capacity", "vehicles", "slots", "queue", "history", "undo")


def _dump_time(moment: datetime | None) -> str | None:
    return None if moment is None else moment.isoformat()


def _load_time(value: object) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("Waktu harus berupa teks ISO atau null")
    return datetime.fromisoformat(value)


def _require_text(row: dict, field: str, label: str) -> str:
    value = row.get(field)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label}: kolom {field} kosong")
    return value


def snapshot(system: ParkingSystem) -> dict:
    """Salinan state yang aman ditulis ke JSON."""
    # Iterasi HistoryTree sudah in-order, jadi riwayatnya tertulis urut
    # waktu keluar dari yang paling lama tanpa perlu disortir.
    history: list[dict] = [
        {
            "vehicle_id": record.vehicle_id,
            "plate": record.plate,
            "slot_code": record.slot_code,
            "entry_time": _dump_time(record.entry_time),
            "exit_time": _dump_time(record.exit_time),
        }
        for record in system.history
    ]

    undo_oldest_first = reversed(list(system.undo))
    return {
        "capacity": system.slots.capacity,
        "vehicles": [
            {
                "vehicle_id": vehicle.vehicle_id,
                "plate": vehicle.plate,
                "owner": vehicle.owner,
                "vtype": vehicle.vtype,
                "status": vehicle.status,
                "entry_time": _dump_time(vehicle.entry_time),
                "slot_index": vehicle.slot_index,
            }
            for vehicle in system.vehicles
        ],
        "slots": [system.slots.get(index) for index in range(system.slots.capacity)],
        "queue": [vehicle.vehicle_id for vehicle in system.queue],
        "history": history,
        "undo": [
            {
                "tx_type": tx.tx_type,
                "vehicle_id": tx.vehicle_id,
                "slot_index": tx.slot_index,
                "time": _dump_time(tx.time),
                "promoted_id": tx.promoted_id,
            }
            for tx in undo_oldest_first
        ],
    }


def save_state(system: ParkingSystem, path: Path | str = STATE_PATH) -> None:
    """Tulis snapshot ke file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(snapshot(system), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def load_state(path: Path | str = STATE_PATH) -> ParkingSystem:
    """Bangun ParkingSystem baru dari file. Indeks hash diisi ulang."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"File state tidak ditemukan: {path}")

    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"{path.name} harus berisi objek JSON")
    missing = [key for key in _SNAPSHOT_KEYS if key not in raw]
    if missing:
        raise ValueError(f"{path.name}: kolom hilang {', '.join(missing)}")

    capacity = raw["capacity"]
    if not isinstance(capacity, int) or capacity < 1:
        raise ValueError(f"{path.name}: kapasitas tidak sah")

    vehicles = raw["vehicles"]
    slots = raw["slots"]
    queue = raw["queue"]
    history = raw["history"]
    undo = raw["undo"]
    if not all(isinstance(part, list) for part in (vehicles, slots, queue, history, undo)):
        raise ValueError(f"{path.name}: vehicles, slots, queue, history, dan undo harus daftar")
    if len(slots) != capacity:
        raise ValueError(f"{path.name}: jumlah slot tidak sama dengan kapasitas")

    system = ParkingSystem(capacity)
    for number, row in enumerate(vehicles, start=1):
        if not isinstance(row, dict):
            raise ValueError(f"{path.name} kendaraan {number}: baris tidak sah")
        vehicle = Vehicle(
            _require_text(row, "vehicle_id", f"kendaraan {number}"),
            _require_text(row, "plate", f"kendaraan {number}"),
            _require_text(row, "owner", f"kendaraan {number}"),
            cast(VehicleType, _require_text(row, "vtype", f"kendaraan {number}")),
            cast(VehicleStatus, _require_text(row, "status", f"kendaraan {number}")),
            _load_time(row.get("entry_time")),
            row.get("slot_index") if isinstance(row.get("slot_index"), int) else None,
        )
        if system.find(vehicle.plate) is not None or system.find(vehicle.vehicle_id, by="id"):
            raise ValueError(f"{path.name}: plat atau id {vehicle.vehicle_id} ganda")
        system.vehicles.insert(vehicle)
        system.index_vehicle(vehicle)

    for index, vehicle_id in enumerate(slots):
        if vehicle_id is None:
            continue
        if not isinstance(vehicle_id, str) or system.find(vehicle_id, by="id") is None:
            raise ValueError(f"{path.name}: penghuni slot {index} tidak dikenal")
        system.slots.assign(index, vehicle_id)

    for vehicle_id in queue:
        if not isinstance(vehicle_id, str):
            raise ValueError(f"{path.name}: antrean berisi id yang tidak sah")
        vehicle = system.find(vehicle_id, by="id")
        if vehicle is None:
            raise ValueError(f"{path.name}: antrean menyebut {vehicle_id} yang tidak terdaftar")
        system.queue.enqueue(vehicle)

    for number, row in enumerate(history, start=1):
        if not isinstance(row, dict):
            raise ValueError(f"{path.name} riwayat {number}: baris tidak sah")
        entry_time = _load_time(row.get("entry_time"))
        exit_time = _load_time(row.get("exit_time"))
        if entry_time is None or exit_time is None:
            raise ValueError(f"{path.name} riwayat {number}: waktu kosong")
        system.history.add(
            HistoryRecord(
                _require_text(row, "vehicle_id", f"riwayat {number}"),
                _require_text(row, "plate", f"riwayat {number}"),
                _require_text(row, "slot_code", f"riwayat {number}"),
                entry_time,
                exit_time,
            )
        )

    for number, row in enumerate(undo, start=1):
        if not isinstance(row, dict):
            raise ValueError(f"{path.name} undo {number}: baris tidak sah")
        moment = _load_time(row.get("time"))
        if moment is None:
            raise ValueError(f"{path.name} undo {number}: waktu kosong")
        slot_index = row.get("slot_index")
        promoted_id = row.get("promoted_id")
        system.undo.push(
            Transaction(
                cast(TxType, _require_text(row, "tx_type", f"undo {number}")),
                _require_text(row, "vehicle_id", f"undo {number}"),
                slot_index if isinstance(slot_index, int) else None,
                moment,
                promoted_id if isinstance(promoted_id, str) else None,
            )
        )

    return system
