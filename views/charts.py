"""Palet dan penyiapan data untuk grafik dashboard."""

from collections import Counter
from datetime import datetime

import altair as alt
import pandas as pd

from core.models import PRIORITY_LABEL, HistoryRecord, Vehicle
from core.parking_map import BLOK, LABEL, slot_per_blok
from core.structures.dynamic_array import ParkingSlots

# Palet kategorikal, dipakai menurut urutan slot dan tidak pernah didaur.
SERIES = ("#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4")

STATUS_ORDER = ("REGISTERED", "PARKED", "WAITING", "EXITED")
STATUS_LABEL = {
    "REGISTERED": "Terdaftar",
    "PARKED": "Parkir",
    "WAITING": "Antre",
    "EXITED": "Keluar",
}


def okupansi_per_blok(slots: ParkingSlots) -> pd.DataFrame:
    """Jumlah slot terisi dan kosong di tiap blok parkir."""
    pembagian = slot_per_blok(slots.capacity)
    baris = []
    for nama in BLOK:
        indeks = pembagian[nama]
        terisi = sum(1 for i in indeks if slots.get(i) is not None)
        baris.append(
            {"Blok": LABEL[nama], "Terisi": terisi, "Kosong": len(indeks) - terisi}
        )
    return pd.DataFrame(baris).set_index("Blok")


def kendaraan_per_status(vehicles: list[Vehicle]) -> pd.DataFrame:
    """Jumlah kendaraan di tiap status."""
    jumlah = Counter(v.status for v in vehicles)
    return pd.DataFrame(
        {"Jumlah": [jumlah.get(s, 0) for s in STATUS_ORDER]},
        index=[STATUS_LABEL[s] for s in STATUS_ORDER],
    )


def antrean_per_prioritas(jumlah: dict[str, int]) -> pd.DataFrame:
    """Jumlah kendaraan mengantre di tiap level prioritas."""
    return pd.DataFrame(
        {"Mengantre": [jumlah.get(k, 0) for k in PRIORITY_LABEL]},
        index=[PRIORITY_LABEL[k] for k in PRIORITY_LABEL],
    )


def _jam_label(moment: datetime) -> str:
    return moment.strftime("%H:00")


def checkout_per_jam(records: list[HistoryRecord]) -> pd.DataFrame:
    """Banyaknya check-out per jam."""
    jumlah = Counter(_jam_label(r.exit_time) for r in records)
    jam = sorted(jumlah)
    return pd.DataFrame({"Check-out": [jumlah[j] for j in jam]}, index=jam)


def pendapatan_per_jam(records: list[HistoryRecord]) -> pd.DataFrame:
    """Total biaya parkir per jam check-out."""
    total: dict[str, int] = {}
    for r in records:
        kunci = _jam_label(r.exit_time)
        total[kunci] = total.get(kunci, 0) + r.cost
    jam = sorted(total)
    return pd.DataFrame({"Pendapatan (Rp)": [total[j] for j in jam]}, index=jam)


def durasi_per_kendaraan(records: list[HistoryRecord]) -> pd.DataFrame:
    """Lama parkir tiap catatan riwayat, dalam menit."""
    return pd.DataFrame(
        {"Menit": [r.duration_minutes for r in records]},
        index=[r.plate for r in records],
    )


def benchmark_frame(rows: list[dict], nilai: str = "per_operasi_us") -> pd.DataFrame:
    """Susun hasil benchmark jadi tabel n x struktur untuk grafik garis."""
    tersedia = [r for r in rows if r.get(nilai) is not None]
    if not tersedia:
        return pd.DataFrame()
    frame = pd.DataFrame(tersedia).pivot(index="n", columns="struktur", values=nilai)
    urutan = []
    for r in tersedia:
        if r["struktur"] not in urutan:
            urutan.append(r["struktur"])
    return frame[urutan]


# Nilai nol tidak punya logaritma, jadi diangkat ke lantai ini dulu.
LANTAI_LOG = 0.001


def benchmark_chart(
    rows: list[dict], nilai: str = "per_operasi_us", judul_y: str = "Mikrodetik per operasi"
) -> alt.Chart:
    """Grafik waktu eksekusi terhadap n, kedua sumbu logaritmik.

    Skala log dipakai karena rentangnya ribuan kali: di sumbu linear
    garis O(1) dan O(log n) rata menempel di dasar dan tidak terbaca.
    Di skala log tiap kelas kompleksitas jadi garis lurus dengan
    kemiringan berbeda.
    """
    tersedia = [r for r in rows if r.get(nilai) is not None]
    urutan: list[str] = []
    for r in tersedia:
        if r["struktur"] not in urutan:
            urutan.append(r["struktur"])

    frame = pd.DataFrame(
        [
            {
                "n": r["n"],
                "Struktur": r["struktur"],
                "Waktu": max(r[nilai], LANTAI_LOG),
                "Kompleksitas": r["kompleksitas"],
            }
            for r in tersedia
        ]
    )
    return (
        alt.Chart(frame)
        .mark_line(strokeWidth=2, point=alt.OverlayMarkDef(size=60, filled=True))
        .encode(
            x=alt.X(
                "n:Q",
                scale=alt.Scale(type="log"),
                title="Jumlah data (n, skala log)",
                axis=alt.Axis(grid=True, gridOpacity=0.25),
            ),
            y=alt.Y(
                "Waktu:Q",
                scale=alt.Scale(type="log"),
                title=f"{judul_y} (skala log)",
                axis=alt.Axis(grid=True, gridOpacity=0.25),
            ),
            color=alt.Color(
                "Struktur:N",
                scale=alt.Scale(domain=urutan, range=list(SERIES[: len(urutan)])),
                legend=alt.Legend(title="Struktur / algoritma"),
            ),
            tooltip=["Struktur", "Kompleksitas", "n", alt.Tooltip("Waktu:Q", format=".3f")],
        )
        .properties(height=340)
    )


def bucket_frame(sizes: list[int]) -> pd.DataFrame:
    """Panjang rantai tiap bucket hash table."""
    return pd.DataFrame({"Panjang rantai": sizes}, index=[str(i) for i in range(len(sizes))])
