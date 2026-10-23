"""Pemuat data contoh untuk mengisi sistem saat demo.

Membaca data/sample_data.json. Pemuatan selalu lewat API publik
ParkingSystem (registrasi lalu check_in), tidak pernah menyentuh struktur
data secara langsung, jadi invarian sistem tidak mungkin dilanggar dari sini.
"""

import json
from pathlib import Path
from typing import cast

from core.models import Result, VehicleType
from core.services import ParkingSystem

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DEFAULT_PATH = DATA_DIR / "sample_data.json"

REQUIRED_FIELDS = ("plate", "owner", "vtype", "initial_status")


def read_rows(path: Path | str = DEFAULT_PATH) -> list[dict[str, str]]:
    """Baca baris data contoh dari file JSON.

    Raises:
        FileNotFoundError: file tidak ada.
        ValueError: isinya bukan daftar, kosong, atau ada kolom yang kurang.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File data contoh tidak ditemukan: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    rows: list[dict[str, str]] = data if isinstance(data, list) else []
    if not rows:
        raise ValueError(f"{path.name} harus berisi daftar baris dan tidak boleh kosong")

    for number, row in enumerate(rows, start=1):
        missing = [field for field in REQUIRED_FIELDS if not row.get(field)]
        if missing:
            raise ValueError(f"{path.name} baris {number}: kolom kosong {', '.join(missing)}")

    return rows


def load_sample_data(
    system: ParkingSystem, path: Path | str = DEFAULT_PATH
) -> list[Result]:
    """Isi `system` dengan data contoh, kembalikan Result tiap operasi.

    Dua tahap: semua kendaraan didaftarkan dulu, lalu yang `initial_status`
    bukan REGISTERED di-check-in sesuai urutan baris. Slot terisi sampai
    habis, sisanya masuk antrean dengan sendirinya.

    Operasi yang gagal (misalnya data contoh dimuat dua kali) tidak
    dilempar sebagai exception, cukup ikut terkumpul di hasil agar
    pemanggil bisa melaporkan berapa yang benar-benar berhasil.
    """
    rows = read_rows(path)
    results: list[Result] = []

    for row in rows:
        results.append(
            system.registrasi(
                row["plate"],
                row["owner"],
                cast(VehicleType, row["vtype"]),
            )
        )

    for row in rows:
        if row["initial_status"].upper() != "REGISTERED":
            results.append(system.check_in(row["plate"]))

    return results
