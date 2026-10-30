"""Antarmuka Streamlit untuk Smart Parking.

Lapisan ini hanya memanggil ParkingSystem lalu menampilkan isi Result.
Semua logika parkir tetap di core/services.py.
"""

from datetime import datetime
from typing import cast

import streamlit as st

from core.models import (
    MAX_SLOT_CAPACITY,
    MIN_SLOT_CAPACITY,
    SLOT_CAPACITY,
    HistoryRecord,
    Result,
    SearchBy,
    Vehicle,
    VehicleType,
    slot_code,
)
from core.persistence import STATE_PATH, load_state, save_state
from core.sample_data import load_sample_data
from core.services import ParkingSystem

VEHICLE_TYPES: tuple[VehicleType, ...] = ("MOBIL", "MOTOR")
SEARCH_LABELS: dict[str, str] = {
    "plate": "Plat nomor",
    "id": "ID kendaraan",
    "owner": "Pemilik",
}
STATUS_LABEL = {
    "REGISTERED": "Terdaftar",
    "PARKED": "Parkir",
    "WAITING": "Antre",
    "EXITED": "Keluar",
}
SLOTS_PER_ROW = 5


# ---- State & util ----

def _system() -> ParkingSystem:
    """ParkingSystem disimpan di session_state agar bertahan antar-rerun.

    Kalau data/state.json ada, sesi baru membacanya. Hash dibangun ulang
    dari daftar kendaraan di file itu.
    """
    if "system" not in st.session_state:
        if STATE_PATH.is_file():
            try:
                st.session_state.system = load_state()
            except (OSError, ValueError) as exc:
                st.session_state.system = ParkingSystem(SLOT_CAPACITY)
                st.session_state.flash = (False, f"State tidak bisa dimuat: {exc}")
        else:
            st.session_state.system = ParkingSystem(SLOT_CAPACITY)
    return st.session_state.system


def _apply(result: Result) -> None:
    """Simpan state ke file, simpan pesan hasil operasi, lalu muat ulang halaman."""
    system = st.session_state.get("system")
    if isinstance(system, ParkingSystem):
        save_state(system)
    st.session_state.flash = (result.ok, result.message)
    st.rerun()


def _render_flash() -> None:
    """Tampilkan pesan dari operasi sebelumnya, sekali saja."""
    flash = st.session_state.pop("flash", None)
    if flash is None:
        return
    ok, message = flash
    st.success(message) if ok else st.error(message)


def _clock(moment: datetime | None) -> str:
    return moment.strftime("%H:%M:%S") if moment else "-"


# ---- Panel tampilan ----

def _render_stats(system: ParkingSystem) -> None:
    stats = system.statistics().data or {}
    labels = [
        ("Total slot", "total_slots"),
        ("Terisi", "occupied_slots"),
        ("Kosong", "available_slots"),
        ("Mengantre", "queue_len"),
        ("Selesai dilayani", "total_served"),
    ]
    for col, (label, key) in zip(st.columns(len(labels)), labels, strict=True):
        col.metric(label, stats.get(key, 0))


def _render_slots(system: ParkingSystem) -> None:
    slots = system.show_slots().data or []
    for start in range(0, len(slots), SLOTS_PER_ROW):
        row = slots[start : start + SLOTS_PER_ROW]
        columns = st.columns(SLOTS_PER_ROW)
        for col, (code, occupant_id) in zip(columns, row, strict=False):
            with col.container(border=True):
                st.caption(code)
                if occupant_id is None:
                    st.markdown(":green[**Kosong**]")
                    st.caption("&nbsp;", unsafe_allow_html=True)
                    continue
                vehicle = system.find(occupant_id, by="id")
                st.markdown(f":red[**{vehicle.plate if vehicle else occupant_id}**]")
                st.caption(vehicle.owner if vehicle else "-")


def _render_queue(system: ParkingSystem) -> None:
    queue = system.show_queue().data or []
    if not queue:
        st.caption("Antrean kosong.")
        return
    st.dataframe(
        [
            {"Urutan": i, "Plat": v.plate, "Pemilik": v.owner, "Tipe": v.vtype}
            for i, v in enumerate(queue, start=1)
        ],
        hide_index=True,
        width="stretch",
    )


def _render_history(system: ParkingSystem) -> None:
    # show_history() mengembalikan hasil in-order HistoryTree: urut waktu
    # keluar dari yang paling lama. Tabel ini membalikkannya supaya
    # check-out terbaru ada di baris atas.
    records: list[HistoryRecord] = system.show_history().data or []
    if not records:
        st.caption("Belum ada riwayat parkir.")
        return
    st.dataframe(
        [
            {
                "Plat": r.plate,
                "Slot": r.slot_code,
                "Masuk": _clock(r.entry_time),
                "Keluar": _clock(r.exit_time),
            }
            for r in reversed(records)
        ],
        hide_index=True,
        width="stretch",
    )


def _render_vehicles(system: ParkingSystem) -> None:
    vehicles = system.vehicles.display()
    if not vehicles:
        st.caption("Belum ada kendaraan terdaftar.")
        return
    st.dataframe(
        [
            {
                "ID": v.vehicle_id,
                "Plat": v.plate,
                "Pemilik": v.owner,
                "Tipe": v.vtype,
                "Status": STATUS_LABEL.get(v.status, v.status),
                "Slot": slot_code(v.slot_index) if v.slot_index is not None else "-",
            }
            for v in vehicles
        ],
        hide_index=True,
        width="stretch",
    )


# ---- Formulir ----

def _form_registrasi(system: ParkingSystem) -> None:
    with st.form("registrasi", clear_on_submit=True):
        # vehicle_id = st.text_input("ID kendaraan", placeholder="V001", key="reg_id")
        plate = st.text_input("Plat nomor", placeholder="B 1234 ABC", key="reg_plate")
        owner = st.text_input("Nama pemilik", placeholder="Budi Santoso", key="reg_owner")
        vtype = st.selectbox("Tipe kendaraan", VEHICLE_TYPES, key="reg_type")
        if st.form_submit_button("Daftarkan", type="primary"):
            _apply(
                system.registrasi(
                    plate.strip(),
                    owner.strip(),
                    cast(VehicleType, vtype),
                )
            )


def _pick_vehicle(system: ParkingSystem, statuses: tuple[str, ...], key: str) -> str | None:
    """Selectbox kendaraan yang statusnya cocok. None kalau tidak ada."""
    options: dict[str, str] = {
        f"{v.plate} — {v.owner}": v.plate
        for v in system.vehicles.display()
        if v.status in statuses
    }
    if not options:
        return None
    return options[st.selectbox("Kendaraan", list(options), key=key)]


def _form_check_in(system: ParkingSystem) -> None:
    with st.form("check_in"):
        plate = _pick_vehicle(system, ("REGISTERED", "EXITED"), "pick_in")
        if plate is None:
            st.info("Tidak ada kendaraan yang siap masuk. Daftarkan dulu di tab Registrasi.")
        if st.form_submit_button("Check-in", type="primary", disabled=plate is None) and plate:
            _apply(system.check_in(plate))


def _form_check_out(system: ParkingSystem) -> None:
    with st.form("check_out"):
        plate = _pick_vehicle(system, ("PARKED",), "pick_out")
        if plate is None:
            st.info("Tidak ada kendaraan yang sedang parkir.")
        if st.form_submit_button("Check-out", type="primary", disabled=plate is None) and plate:
            _apply(system.check_out(plate))


def _form_search(system: ParkingSystem) -> None:
    with st.form("cari"):
        by = st.radio(
            "Cari berdasarkan",
            list(SEARCH_LABELS),
            format_func=lambda k: SEARCH_LABELS[k],
            horizontal=True,
            key="search_by",
        )
        key = st.text_input("Kata kunci", key="search_key")
        submitted = st.form_submit_button("Cari")

    if not submitted:
        return
    result = system.search(key.strip(), by=cast(SearchBy, by))
    if not result.ok or result.data is None:
        st.error(result.message)
        return
    found: Vehicle = result.data
    st.success(result.message)
    detail = st.columns(3)
    detail[0].metric("Plat", found.plate)
    detail[1].metric("Status", STATUS_LABEL.get(found.status, found.status))
    detail[2].metric(
        "Slot", slot_code(found.slot_index) if found.slot_index is not None else "-"
    )
    st.caption(f"ID {found.vehicle_id} · {found.owner} · {found.vtype} · masuk {_clock(found.entry_time)}")


def _form_resize(system: ParkingSystem) -> None:
    """Ubah jumlah slot parkir.

    Dalam st.form supaya angkanya bisa diutak-atik dulu tanpa memicu
    rerun, dan parkiran baru berubah saat tombol ditekan.
    """
    with st.form("resize"):
        st.subheader("Jumlah slot")
        capacity = st.number_input(
            "Slot parkir",
            min_value=MIN_SLOT_CAPACITY,
            max_value=MAX_SLOT_CAPACITY,
            value=system.slots.capacity,
            step=1,
            key="resize_capacity",
            help=(
                "Slot tambahan langsung dipakai kendaraan yang mengantre. "
                "Untuk mengurangi slot, slot di ekor harus kosong dulu."
            ),
        )
        if st.form_submit_button("Terapkan", width="stretch"):
            _apply(system.resize_slots(int(capacity)))


def _render_sidebar(system: ParkingSystem) -> None:
    with st.sidebar:
        st.header("Kontrol")
        if st.button("Undo transaksi terakhir", key="undo", width="stretch"):
            _apply(system.undo_last())
        if st.button("Reset sistem", key="reset", width="stretch"):
            # Jumlah slot ikut terbawa: kapasitas adalah bentuk parkirannya,
            # bukan data yang dibuang bersama kendaraan.
            st.session_state.system = ParkingSystem(system.slots.capacity)
            _apply(Result.success("Sistem direset"))

        if st.button("Muat data contoh", key="load_sample", width="stretch"):
            try:
                results = load_sample_data(system)
            except (OSError, ValueError) as exc:
                _apply(Result.fail(f"Gagal memuat data contoh: {exc}"))
            else:
                berhasil = sum(1 for r in results if r.ok)
                _apply(
                    Result.success(f"Data contoh dimuat, {berhasil} operasi berhasil")
                    if berhasil
                    else Result.fail("Data contoh sudah dimuat sebelumnya")
                )

        st.divider()
        _form_resize(system)

        st.divider()
        st.caption(
            f"Kapasitas {system.slots.capacity} slot · "
            f"{len(system.undo)} transaksi bisa di-undo"
        )


# ---- Entry point ----

def main() -> None:
    st.set_page_config(page_title="Smart Parking", layout="wide")
    system = _system()

    st.title("Smart Parking")
    st.caption("Sistem manajemen parkir berbasis struktur data — Struktur Data DS01")

    _render_sidebar(system)
    _render_flash()
    _render_stats(system)

    st.subheader("Status slot")
    _render_slots(system)

    st.divider()
    left, right = st.columns([3, 2])

    with left:
        st.subheader("Operasi")
        tabs = st.tabs(["Registrasi", "Check-in", "Check-out", "Cari"])
        with tabs[0]:
            _form_registrasi(system)
        with tabs[1]:
            _form_check_in(system)
        with tabs[2]:
            _form_check_out(system)
        with tabs[3]:
            _form_search(system)

    with right:
        st.subheader("Antrean")
        _render_queue(system)
        st.subheader("Riwayat parkir")
        _render_history(system)

    st.divider()
    st.subheader("Kendaraan terdaftar")
    _render_vehicles(system)
