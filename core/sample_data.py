"""Pemuat data contoh untuk mengisi sistem saat demo.

Membaca data/sample_data.json. Pemuatan selalu lewat API publik
ParkingSystem (registrasi lalu check_in), tidak pernah menyentuh struktur
data secara langsung, jadi invarian sistem tidak mungkin dilanggar dari sini.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import cast

from core.models import Priority, Result, VehicleType
from core.services import ParkingSystem

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DEFAULT_PATH = DATA_DIR / "sample_data.json"

REQUIRED_FIELDS = ("plate", "owner", "vtype", "initial_status")

# Jarak waktu masuk antar kendaraan yang diparkir, supaya durasi dan biaya
# di demo tidak semuanya nol.
JEDA_MASUK = timedelta(minutes=37)


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
                cast(Priority, row.get("priority") or "UMUM"),
            )
        )

    masuk: list[Result] = []
    for row in rows:
        if row["initial_status"].upper() != "REGISTERED":
            masuk.append(system.check_in(row["plate"]))
    results.extend(masuk)

    _sebar_waktu_masuk(masuk)
    return results


def _sebar_waktu_masuk(hasil: list[Result]) -> None:
    """Mundurkan entry_time kendaraan yang parkir, berjenjang.

    check_in selalu memberi waktu sekarang, jadi tanpa ini seluruh
    kendaraan demo berdurasi nol menit dan biayanya nol.
    """
    sekarang = datetime.now()
    terparkir = [r.data for r in hasil if r.ok and r.data is not None]
    for urutan, kendaraan in enumerate(reversed(terparkir), start=1):
        if kendaraan.entry_time is not None:
            kendaraan.entry_time = sekarang - JEDA_MASUK * urutan
