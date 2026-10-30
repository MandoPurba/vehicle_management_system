"""Antarmuka Streamlit untuk Smart Parking.

Lapisan ini hanya memanggil ParkingSystem lalu menampilkan isi Result.
Semua logika parkir tetap di core/.
"""

from datetime import datetime, time, timedelta
from time import perf_counter
from typing import cast

import streamlit as st

from core.algorithms.recursion import max_duration_recursive, sum_costs_recursive
from core.algorithms.searching import search_history
from core.algorithms.sorting import sort_history
from core.benchmark import UKURAN, run_benchmark
from core.models import (
    MAX_SLOT_CAPACITY,
    MIN_SLOT_CAPACITY,
    PRIORITY_LABEL,
    SLOT_CAPACITY,
    TARIF_PER_JAM,
    HistoryRecord,
    Priority,
    Result,
    SearchBy,
    SortBy,
    Vehicle,
    VehicleType,
    slot_code,
)
from core.parking_map import GEDUNG, GERBANG, LABEL, build_map, slot_terdekat
from core.persistence import STATE_PATH, load_state, save_state
from core.sample_data import load_sample_data
from core.services import ParkingSystem
from core.structures.bst import OrderBy
from views import charts, diagrams

VEHICLE_TYPES: tuple[VehicleType, ...] = ("MOBIL", "MOTOR")
PRIORITIES: tuple[Priority, ...] = ("UMUM", "DOSEN", "TAMU", "DISABILITAS")
SEARCH_LABELS: dict[str, str] = {
    "plate": "Plat nomor",
    "id": "ID kendaraan",
    "owner": "Pemilik",
}
SORT_LABELS: dict[str, str] = {
    "entry_time": "Waktu masuk",
    "exit_time": "Waktu keluar",
    "duration": "Durasi parkir",
    "cost": "Biaya",
    "plate": "Plat nomor",
}
ALGO_LABELS: dict[str, str] = {
    "merge": "Merge Sort — O(n log n) stabil",
    "quick": "Quick Sort — O(n log n) rata-rata",
    "insertion": "Insertion Sort — O(n²)",
    "bubble": "Bubble Sort — O(n²)",
}
STATUS_LABEL = charts.STATUS_LABEL
SLOTS_PER_ROW = 5


# ---- State & util ----

def _system() -> ParkingSystem:
    """ParkingSystem di session_state agar bertahan antar-rerun."""
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


def _map():
    """Graf peta parkir, dibangun sekali per sesi."""
    if "map" not in st.session_state:
        st.session_state.map = build_map()
    return st.session_state.map


def _apply(result: Result) -> None:
    """Simpan state, simpan pesan hasil operasi, lalu muat ulang halaman."""
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


def _rupiah(nilai: float) -> str:
    return f"Rp {int(nilai):,}".replace(",", ".")


def _ribuan(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def _records(system: ParkingSystem) -> list[HistoryRecord]:
    return system.show_history().data or []


# ---- Halaman: Dashboard ----

def _render_dashboard(system: ParkingSystem) -> None:
    stats = system.statistics().data or {}
    records = _records(system)

    labels = [
        ("Total slot", "total_slots"),
        ("Terisi", "occupied_slots"),
        ("Kosong", "available_slots"),
        ("Mengantre", "queue_len"),
        ("Selesai dilayani", "total_served"),
    ]
    for col, (label, key) in zip(st.columns(len(labels)), labels, strict=True):
        col.metric(label, stats.get(key, 0))

    rekursif = st.columns(3)
    rekursif[0].metric("Slot terisi", stats.get("occupied_slots", 0))
    rekursif[1].metric("Total pendapatan", _rupiah(sum_costs_recursive(records)))
    rekursif[2].metric("Durasi terlama", f"{max_duration_recursive(records)} menit")
    st.caption(
        "Tiga angka di atas dihitung tanpa loop oleh `count_occupied_recursive`, "
        "`sum_costs_recursive`, dan `max_duration_recursive` di "
        "`core/algorithms/recursion.py`."
    )

    st.divider()
    kiri, kanan = st.columns(2)

    with kiri:
        st.subheader("Okupansi per blok")
        data = charts.okupansi_per_blok(system.slots)
        st.bar_chart(data, color=list(charts.SERIES[:2]))
        st.dataframe(data, width="stretch")

    with kanan:
        st.subheader("Kendaraan per status")
        data = charts.kendaraan_per_status(system.vehicles.display())
        st.bar_chart(data, color=charts.SERIES[0])
        st.dataframe(data.T, width="stretch")

    if not records:
        st.info("Grafik check-out dan pendapatan muncul setelah ada kendaraan keluar.")
        return

    st.divider()
    kiri, kanan = st.columns(2)
    with kiri:
        st.subheader("Check-out per jam")
        st.line_chart(charts.checkout_per_jam(records), color=charts.SERIES[0])
    with kanan:
        st.subheader("Pendapatan per jam")
        # Dipisah dari grafik di sebelah: satu grafik satu sumbu, skala
        # rupiah tidak boleh ditumpuk dengan skala jumlah kendaraan.
        st.line_chart(charts.pendapatan_per_jam(records), color=charts.SERIES[1])

    st.subheader("Durasi parkir per kendaraan")
    st.bar_chart(charts.durasi_per_kendaraan(records), color=charts.SERIES[2])


# ---- Halaman: Operasi ----

def _form_registrasi(system: ParkingSystem) -> None:
    with st.form("registrasi", clear_on_submit=True):
        plate = st.text_input("Plat nomor", placeholder="B 1234 ABC", key="reg_plate")
        owner = st.text_input("Nama pemilik", placeholder="Budi Santoso", key="reg_owner")
        vtype = st.selectbox("Tipe kendaraan", VEHICLE_TYPES, key="reg_type")
        priority = st.selectbox(
            "Prioritas",
            PRIORITIES,
            format_func=lambda k: PRIORITY_LABEL[k],
            key="reg_priority",
            help="Menentukan urutan dilayani saat parkir penuh.",
        )
        if st.form_submit_button("Daftarkan", type="primary"):
            _apply(
                system.registrasi(
                    plate.strip(),
                    owner.strip(),
                    cast(VehicleType, vtype),
                    cast(Priority, priority),
                )
            )


def _pick_vehicle(system: ParkingSystem, statuses: tuple[str, ...], key: str) -> str | None:
    """Selectbox kendaraan yang statusnya cocok. None kalau tidak ada."""
    options: dict[str, str] = {
        f"{v.plate} — {v.owner} ({PRIORITY_LABEL.get(v.priority, v.priority)})": v.plate
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
    st.caption(
        "Tarif parkir kampus: "
        + ", ".join(f"{t} {_rupiah(h)}/jam" for t, h in TARIF_PER_JAM.items())
        + " — dihitung proporsional per menit, dibulatkan ke ratusan. "
        "Keluar tanpa sempat parkir tidak ditagih."
    )


def _form_search(system: ParkingSystem) -> None:
    with st.form("cari"):
        by = st.segmented_control(
            "Cari berdasarkan",
            list(SEARCH_LABELS),
            format_func=lambda k: SEARCH_LABELS[k],
            default="plate",
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
    detail = st.columns(4)
    detail[0].metric("Plat", found.plate)
    detail[1].metric("Status", STATUS_LABEL.get(found.status, found.status))
    detail[2].metric(
        "Slot", slot_code(found.slot_index) if found.slot_index is not None else "-"
    )
    detail[3].metric("Prioritas", PRIORITY_LABEL.get(found.priority, found.priority))
    st.caption(
        f"ID {found.vehicle_id} · {found.owner} · {found.vtype} · masuk {_clock(found.entry_time)}"
    )
    if by == "plate":
        st.caption(
            "Ditemukan lewat hash table, rantai bucket sepanjang "
            f"{system.by_plate.chain_length(found.plate)} simpul."
        )
    elif by == "owner":
        st.caption("Nama pemilik tidak diindeks, jadi linked list dipindai O(n).")


def _render_operasi(system: ParkingSystem) -> None:
    tabs = st.tabs(["Registrasi", "Check-in", "Check-out", "Cari"])
    with tabs[0]:
        _form_registrasi(system)
    with tabs[1]:
        _form_check_in(system)
    with tabs[2]:
        _form_check_out(system)
    with tabs[3]:
        _form_search(system)


# ---- Halaman: Slot & peta ----

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


def _render_slot_dan_peta(system: ParkingSystem) -> None:
    st.subheader("Status slot")
    _render_slots(system)
    st.divider()
    _render_peta(system)


def _render_peta(system: ParkingSystem) -> None:
    graph = _map()

    dari = st.selectbox(
        "Cari slot terdekat dari",
        [*GERBANG, *GEDUNG],
        format_func=lambda k: LABEL[k],
        key="map_from",
    )
    hasil = slot_terdekat(graph, system.slots, dari)
    if hasil["found"]:
        kolom = st.columns(3)
        kolom[0].metric("Slot terdekat", hasil["slot_code"])
        kolom[1].metric("Blok", LABEL[hasil["block"]])
        kolom[2].metric("Jarak", f"{hasil['distance']} m")
        st.success(" → ".join(LABEL[n] for n in hasil["path"]))
        st.caption(f"{hasil['free_in_block']} slot kosong di blok itu.")
    else:
        st.warning(hasil["message"])

    st.divider()
    st.subheader("Peta area parkir")
    st.caption(
        "Biru gerbang, hijau blok parkir, jingga gedung tujuan. Angka pada "
        "garis adalah jarak dalam meter, dan kuning menandai jalur terpilih."
    )
    st.mermaid_chart(
        diagrams.peta_parkir(sorot=hasil.get("path") if hasil["found"] else None),
        alt="Peta area parkir kampus: dua gerbang, tiga blok parkir, dan tiga gedung, terhubung jalur berjarak",
    )

    st.divider()
    st.subheader("Penjelajahan graf")
    kiri, kanan = st.columns(2)
    with kiri:
        awal = st.selectbox(
            "Mulai dari", graph.nodes(), format_func=lambda k: LABEL[k], key="graph_start"
        )
        st.caption("BFS — melebar, tetangga terdekat lebih dulu")
        st.code(" → ".join(LABEL[n] for n in graph.bfs(awal)), language=None)
        st.caption("DFS — mendalam, satu cabang sampai habis")
        st.code(" → ".join(LABEL[n] for n in graph.dfs(awal)), language=None)
    with kanan:
        tujuan = st.selectbox(
            "Menuju", graph.nodes(), format_func=lambda k: LABEL[k], key="graph_goal"
        )
        jalur, jarak = graph.shortest_path(awal, tujuan)
        hop = graph.bfs_path(awal, tujuan)
        if jalur:
            st.caption("Dijkstra — jarak terpendek menurut bobot")
            st.code(f"{' → '.join(LABEL[n] for n in jalur)}  =  {int(jarak)} m", language=None)
            st.caption("BFS — simpul tersedikit, bobot diabaikan")
            st.code(" → ".join(LABEL[n] for n in hop), language=None)
            if jalur != hop:
                st.info("Kedua jalur beda: yang paling sedikit simpul belum tentu terpendek.")
        else:
            st.warning("Tidak ada jalur antara dua titik itu.")

    if jalur:
        st.caption(f"Jalur Dijkstra {LABEL[awal]} ke {LABEL[tujuan]} disorot kuning:")
        st.mermaid_chart(
            diagrams.peta_parkir(sorot=jalur),
            alt=f"Peta parkir dengan jalur terpendek dari {LABEL[awal]} ke {LABEL[tujuan]} disorot",
        )

    st.caption(f"Peta: {graph.node_count} simpul, {graph.edge_count} jalur.")


def _form_resize(system: ParkingSystem) -> None:
    """Ubah jumlah slot parkir."""
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


# ---- Halaman: Antrean ----

def _render_queue(system: ParkingSystem) -> None:
    queue = system.show_queue().data or []
    jumlah = system.queue.group_counts()

    kolom = st.columns(len(PRIORITY_LABEL))
    for col, (kunci, label) in zip(kolom, PRIORITY_LABEL.items(), strict=True):
        col.metric(label, jumlah.get(kunci, 0))

    if not queue:
        st.caption("Antrean kosong.")
    else:
        st.dataframe(
            [
                {
                    "Urutan": i,
                    "Plat": v.plate,
                    "Pemilik": v.owner,
                    "Tipe": v.vtype,
                    "Prioritas": PRIORITY_LABEL.get(v.priority, v.priority),
                }
                for i, v in enumerate(queue, start=1)
            ],
            hide_index=True,
            width="stretch",
        )
        st.caption(
            "Urutan datang dari MinHeap berkunci (rank prioritas, nomor urut). "
            "Nomor urut itu yang menjaga kendaraan berprioritas sama tetap FIFO."
        )

    st.bar_chart(charts.antrean_per_prioritas(jumlah), color=charts.SERIES[0])


# ---- Halaman: Kendaraan (BST) ----

def _render_vehicles(system: ParkingSystem) -> None:
    order_by = st.segmented_control(
        "Urutkan pohon berdasarkan",
        ("plate", "id"),
        format_func=lambda k: "Nomor polisi" if k == "plate" else "ID kendaraan",
        default="plate",
        key="tree_order",
    )
    hasil = system.vehicle_traversals(cast(OrderBy, order_by)).data or {}
    if not hasil.get("size"):
        st.caption("Belum ada kendaraan terdaftar.")
        return

    kolom = st.columns(2)
    kolom[0].metric("Simpul di pohon", hasil["size"])
    kolom[1].metric("Tinggi pohon", hasil["height"])

    st.subheader("Daftar kendaraan terurut")
    st.caption("Hasil traversal inorder — terurut tanpa memanggil sort.")
    st.dataframe(
        [
            {
                "ID": v.vehicle_id,
                "Plat": v.plate,
                "Pemilik": v.owner,
                "Tipe": v.vtype,
                "Prioritas": PRIORITY_LABEL.get(v.priority, v.priority),
                "Status": STATUS_LABEL.get(v.status, v.status),
                "Slot": slot_code(v.slot_index) if v.slot_index is not None else "-",
            }
            for v in hasil["inorder"]
        ],
        hide_index=True,
        width="stretch",
    )

    kunci = (lambda v: v.plate) if order_by == "plate" else (lambda v: v.vehicle_id)

    st.subheader("Percabangan pohon")
    gambar = diagrams.pohon_bst(system.vehicle_tree.root, kunci) if order_by == "plate" else None
    if order_by != "plate":
        st.caption(
            "Gambar pohon hanya untuk urutan nomor polisi, karena pohon itulah "
            "yang benar-benar disimpan sistem. Urutan ID dibangun sesaat."
        )
    elif gambar is None:
        st.caption(
            f"Pohonnya {hasil['size']} simpul — terlalu besar untuk digambar "
            "supaya tetap terbaca. Muat ulang dengan kendaraan lebih sedikit "
            "untuk melihat percabangannya."
        )
    else:
        st.caption(
            "L anak kiri (lebih kecil), R anak kanan (lebih besar). Kuning akar, "
            "kotak putus-putus cabang yang kosong."
        )
        st.mermaid_chart(gambar, alt="Diagram percabangan binary search tree kendaraan")

    st.subheader("Tiga traversal")
    penjelasan = {
        "inorder": "Kiri → simpul → kanan. Selalu terurut.",
        "preorder": "Simpul → kiri → kanan. Menyalin bentuk pohon.",
        "postorder": "Kiri → kanan → simpul. Anak sebelum induk.",
    }
    for col, nama in zip(st.columns(3), ("inorder", "preorder", "postorder"), strict=True):
        with col:
            st.markdown(f"**{nama}**")
            st.caption(penjelasan[nama])
            st.code("\n".join(kunci(v) for v in hasil[nama]), language=None)


# ---- Halaman: Riwayat ----

def _render_history(system: ParkingSystem) -> None:
    records = _records(system)
    if not records:
        st.caption("Belum ada riwayat parkir.")
        return

    kolom = st.columns([2, 2, 1, 1])
    by = kolom[0].selectbox(
        "Urutkan berdasarkan",
        list(SORT_LABELS),
        format_func=lambda k: SORT_LABELS[k],
        key="hist_sort",
    )
    algo = kolom[1].selectbox(
        "Algoritma pengurutan",
        list(ALGO_LABELS),
        format_func=lambda k: ALGO_LABELS[k],
        key="hist_algo",
    )
    turun = kolom[2].toggle("Menurun", key="hist_desc")
    kolom[3].metric("Catatan", len(records))

    t0 = perf_counter()
    terurut = sort_history(records, by=cast(SortBy, by), descending=turun, algorithm=algo)
    durasi_ms = (perf_counter() - t0) * 1000
    st.caption(
        f"Diurutkan dengan **{ALGO_LABELS[algo]}** di `core/algorithms/sorting.py` "
        f"dalam **{durasi_ms:.3f} ms**."
    )
    st.dataframe(
        [
            {
                "Plat": r.plate,
                "Tipe": r.vtype,
                "Slot": r.slot_code,
                "Masuk": _clock(r.entry_time),
                "Keluar": _clock(r.exit_time),
                "Durasi (menit)": r.duration_minutes,
                "Biaya": _rupiah(r.cost),
            }
            for r in terurut
        ],
        hide_index=True,
        width="stretch",
    )

    st.divider()
    st.subheader("Query rentang waktu keluar (HistoryTree.between)")
    st.caption(
        "Memangkas cabang BST riwayat di luar rentang waktu keluar `[start, end]` "
        "tanpa memindai seluruh simpul."
    )
    waktu_keluar = [r.exit_time for r in records]
    min_dt, max_dt = min(waktu_keluar), max(waktu_keluar)
    kolom_r = st.columns(2)
    t_mulai = kolom_r[0].time_input(
        "Dari jam keluar",
        value=time(min_dt.hour, min_dt.minute),
        key="hist_range_start",
    )
    t_akhir = kolom_r[1].time_input(
        "Sampai jam keluar",
        value=time(max_dt.hour, min(59, max_dt.minute + 1)),
        key="hist_range_end",
    )
    dt_mulai = datetime.combine(min_dt.date(), t_mulai)
    dt_akhir = datetime.combine(max_dt.date(), t_akhir).replace(second=59, microsecond=999999)
    hasil_rentang = system.history.between(dt_mulai, dt_akhir)
    st.caption(
        f"Ditemukan **{len(hasil_rentang)}** dari {len(records)} catatan pada rentang "
        f"`{dt_mulai.strftime('%H:%M:%S')}` – `{dt_akhir.strftime('%H:%M:%S')}`."
    )
    if hasil_rentang:
        st.dataframe(
            [
                {
                    "ID": r.vehicle_id,
                    "Plat": r.plate,
                    "Slot": r.slot_code,
                    "Keluar": _clock(r.exit_time),
                    "Durasi (menit)": r.duration_minutes,
                    "Biaya": _rupiah(r.cost),
                }
                for r in hasil_rentang
            ],
            hide_index=True,
            width="stretch",
        )

    st.divider()
    st.subheader("Binary search pada riwayat terurut")
    with st.form("cari_riwayat"):
        kolom = st.columns([1, 2])
        cari_by = kolom[0].selectbox(
            "Kunci",
            ("plate", "cost", "duration"),
            format_func=lambda k: SORT_LABELS[k],
            key="bs_key",
        )
        nilai_teks = kolom[1].text_input(
            "Nilai yang dicari",
            key="bs_value",
            help="Plat apa adanya, biaya dalam rupiah, durasi dalam menit.",
        )
        submitted = st.form_submit_button("Cari")

    if not submitted:
        return
    target: str | int | timedelta
    try:
        if cari_by == "plate":
            target = nilai_teks.strip()
        elif cari_by == "cost":
            target = int(nilai_teks)
        else:
            target = timedelta(minutes=int(nilai_teks))
    except ValueError:
        st.error("Nilai harus berupa angka.")
        return

    hasil = search_history(records, cast(SortBy, cari_by), target)
    if hasil["record"] is None:
        st.error(f"Tidak ada catatan dengan {SORT_LABELS[cari_by].lower()} itu.")
    else:
        r = hasil["record"]
        st.success(
            f"Ketemu di indeks {hasil['index']}: {r.plate}, "
            f"{r.duration_minutes} menit, {_rupiah(r.cost)}"
        )
    st.caption(
        f"Binary search memeriksa sekitar {hasil['binary_steps']} data, "
        f"linear search sampai {hasil['linear_steps']}. Binary search hanya "
        "sah karena datanya sudah diurutkan lebih dulu."
    )


# ---- Halaman: Struktur data ----

def _render_struktur(system: ParkingSystem) -> None:
    stats = system.hash_stats().data or {}
    for nama, judul in (("by_plate", "Indeks nomor polisi"), ("by_id", "Indeks ID")):
        s = stats.get(nama, {})
        st.subheader(judul)
        kolom = st.columns(5)
        kolom[0].metric("Kunci", s.get("size", 0))
        kolom[1].metric("Bucket", s.get("capacity", 0))
        kolom[2].metric("Load factor", f"{s.get('load_factor', 0):.3f}")
        kolom[3].metric("Bucket bertabrakan", s.get("collision_buckets", 0))
        kolom[4].metric("Rantai terpanjang", s.get("longest_chain", 0))
        st.caption(
            f"{s.get('used_buckets', 0)} bucket terpakai, "
            f"{s.get('empty_buckets', 0)} kosong, "
            f"{s.get('colliding_keys', 0)} kunci menumpuk, "
            f"sudah {s.get('rehash_count', 0)} kali rehash. "
            "Collision ditangani dengan chaining, dan tabel digandakan "
            "otomatis begitu load factor melewati 0,75."
        )
        tabel = system.by_plate if nama == "by_plate" else system.by_id
        st.bar_chart(charts.bucket_frame(tabel.bucket_sizes()), color=charts.SERIES[0])
        st.divider()

    st.subheader("Tinggi pohon")
    kolom = st.columns(3)
    kolom[0].metric("BST kendaraan", system.vehicle_tree.height())
    kolom[1].metric("Simpul kendaraan", system.vehicle_tree.size)
    kolom[2].metric("BST riwayat", system.history.height())
    st.caption(
        "Riwayat masuk urut waktu, jadi pohonnya merosot menjadi rantai "
        "setinggi jumlah catatan. BST di proyek ini tidak menyeimbangkan "
        "diri; keuntungannya di traversal terurut dan query rentang, bukan "
        "di tinggi pohon."
    )

    st.divider()
    st.subheader("Isi tumpukan UndoStack (LIFO)")
    tumpukan = system.undo.display()
    puncak = system.undo.peek()
    kolom_u = st.columns(3)
    kolom_u[0].metric("Ukuran stack", len(tumpukan))
    kolom_u[1].metric("Transaksi puncak (TOP)", puncak.tx_type if puncak else "-")
    kolom_u[2].metric("Kendaraan puncak", puncak.vehicle_id if puncak else "-")
    st.caption(
        "`UndoStack` menyimpan transaksi dalam singly linked list di kepala (`_top`), "
        "sehingga `push`, `pop`, dan `peek` berjalan O(1)."
    )
    if tumpukan:
        st.dataframe(
            [
                {
                    "Posisi": "TOP (0)" if i == 0 else str(i),
                    "Tipe transaksi": tx.tx_type,
                    "ID kendaraan": tx.vehicle_id,
                    "Slot": slot_code(tx.slot_index) if tx.slot_index is not None else "-",
                    "Promosi antrean": tx.promoted_id or "-",
                    "Waktu": _clock(tx.time),
                }
                for i, tx in enumerate(tumpukan)
            ],
            hide_index=True,
            width="stretch",
        )
    else:
        st.caption("Tumpukan undo kosong.")

    st.divider()
    st.subheader("Rantai VehicleList (Singly Linked List)")
    rantai = system.vehicles.display()
    st.caption(
        f"`VehicleList` menyimpan **{len(rantai)}** kendaraan terdaftar dalam "
        "singly linked list (`_head` → `next` → ... → `None`)."
    )
    if rantai:
        st.code(
            " → ".join(f"[{v.id} | {v.plate} | {STATUS_LABEL[v.status]}]" for v in rantai)
            + " → None",
            language=None,
        )


# ---- Halaman: Benchmark ----

def _render_benchmark() -> None:
    st.caption(
        "Mengukur waktu eksekusi struktur dan algoritma pada n = "
        + "; ".join(_ribuan(n) for n in UKURAN)
        + ". Sekali jalan sekitar 3 detik."
    )
    if st.button("Jalankan benchmark", type="primary", key="run_bench"):
        with st.spinner("Mengukur..."):
            st.session_state.bench = run_benchmark()

    hasil = st.session_state.get("bench")
    if hasil is None:
        st.info("Tekan tombol di atas untuk mulai mengukur.")
        return

    st.subheader("Pencarian satu data")
    st.caption("Waktu rata-rata satu operasi pencarian, dalam mikrodetik.")
    st.altair_chart(
        charts.benchmark_chart(hasil["cari"]),
        alt="Grafik log-log waktu pencarian terhadap jumlah data untuk tiap struktur",
    )
    st.dataframe(
        charts.benchmark_frame(hasil["cari"]).style.format("{:.3f}"),
        width="stretch",
        alt="Tabel waktu pencarian per struktur dan jumlah data",
    )
    st.caption(
        "Hash table, BST, dan binary search hampir rata saat n naik 100 kali, "
        "sedangkan linear search dan linked list naik sebanding n. Itulah beda "
        "O(1) dan O(log n) melawan O(n)."
    )

    st.divider()
    st.subheader("Menyisipkan n data")
    st.altair_chart(
        charts.benchmark_chart(hasil["sisip"], "detik", "Detik untuk n data"),
        alt="Grafik log-log waktu penyisipan n data untuk tiap struktur",
    )
    st.dataframe(
        charts.benchmark_frame(hasil["sisip"], "detik").style.format("{:.6f}"),
        width="stretch",
        alt="Tabel waktu penyisipan per struktur dan jumlah data",
    )

    st.divider()
    st.subheader("Mengurutkan n data")
    st.altair_chart(
        charts.benchmark_chart(hasil["urut"], "detik", "Detik untuk n data"),
        alt="Grafik log-log waktu pengurutan n data untuk tiap algoritma",
    )
    st.dataframe(
        charts.benchmark_frame(hasil["urut"], "detik").style.format("{:.6f}"),
        width="stretch",
        alt="Tabel waktu pengurutan per algoritma dan jumlah data",
    )
    st.caption(
        f"Insertion sort sengaja dilewati di atas n = {_ribuan(hasil['batas_kuadratik'])}: "
        "O(n²) pada 100.000 data butuh sekitar 10 miliar perbandingan."
    )

    st.divider()
    st.subheader("Bentuk BST menentukan biayanya")
    st.dataframe(
        [
            {
                "Kondisi data": r["kondisi"],
                "n": r["n"],
                "Tinggi pohon": r["tinggi"],
                "Waktu sisip (detik)": round(r["detik"], 4),
                "Kompleksitas": r["kompleksitas"],
            }
            for r in hasil["bentuk_bst"]
        ],
        hide_index=True,
        width="stretch",
    )
    st.caption(
        "Data yang sudah terurut membuat tiap simpul jatuh ke kanan, pohonnya "
        "berubah jadi rantai, dan menyisipkan n data menjadi O(n²)."
    )


# ---- Sidebar ----

def _render_sidebar(system: ParkingSystem) -> None:
    with st.sidebar:
        st.header("Kontrol")
        if st.button("Undo transaksi terakhir", key="undo", width="stretch"):
            _apply(system.undo_last())
        if st.button("Reset sistem", key="reset", width="stretch"):
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

    # on_change="rerun" membuat hanya tab terbuka yang dihitung. Tanpa itu
    # Dijkstra, traversal, dan statistik hash ikut jalan tiap rerun.
    halaman = st.tabs(
        [
            "Dashboard",
            "Operasi",
            "Slot & peta",
            "Antrean",
            "Kendaraan (BST)",
            "Riwayat",
            "Struktur data",
            "Benchmark",
        ],
        key="halaman",
        on_change="rerun",
    )

    def isi(index: int, render) -> None:
        if not halaman[index].open:
            return
        with halaman[index]:
            render()

    isi(0, lambda: _render_dashboard(system))
    isi(1, lambda: _render_operasi(system))
    isi(2, lambda: _render_slot_dan_peta(system))
    isi(3, lambda: _render_queue(system))
    isi(4, lambda: _render_vehicles(system))
    isi(5, lambda: _render_history(system))
    isi(6, lambda: _render_struktur(system))
    isi(7, _render_benchmark)
