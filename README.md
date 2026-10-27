# Vehicle Management System

Sistem manajemen parkir kendaraan (*Smart Parking*) yang dibangun di atas
struktur data yang diimplementasikan sendiri dari nol — tanpa memakai
`list`/`dict` bawaan Python sebagai struktur inti. Proyek mata kuliah
Struktur Data (DS01).

## Fitur

| Fitur | Keterangan |
| --- | --- |
| Registrasi | Mendaftarkan kendaraan baru (ID, plat, pemilik, tipe) |
| Check-in | Menempatkan kendaraan ke slot kosong, atau masuk antrean bila penuh |
| Check-out | Mengosongkan slot, mencatat riwayat, lalu menaikkan kendaraan dari antrean |
| Pencarian | Mencari kendaraan berdasarkan plat atau ID |
| Undo | Membatalkan transaksi terakhir (check-in / antre / check-out) |
| Laporan | Status slot, isi antrean, riwayat parkir, dan statistik |
| Reset | Mengosongkan seluruh state sistem |
| Data contoh | Mengisi sistem dari `data/sample_data.json` sekali klik |

## Struktur data yang dipakai

Tiap fitur dipetakan ke satu struktur data:

| Struktur | Modul | Dipakai untuk |
| --- | --- | --- |
| Dynamic Array | `core/structures/dynamic_array.py` | `ParkingSlots` — slot parkir berindeks (`SLOT_CAPACITY` = 5) |
| Linked List | `core/structures/linked_list.py` | `VehicleList` — daftar kendaraan terdaftar, dan `ParkingHistory` — riwayat parkir |
| Queue | `core/structures/queue.py` | `WaitingQueue` — antrean saat parkir penuh (FIFO) |
| Stack | `core/structures/stack.py` | `UndoStack` — riwayat transaksi untuk undo (LIFO) |
| Hash Table | `core/structures/hash_table.py` | Indeks pencarian plat dan id, rata-rata O(1) |
| BST | `core/structures/bst.py` | *(rencana)* `ParkingHistory` terurut waktu, menggantikan versi linked list |
| Heap | `core/structures/heap.py` | Prioritas antrean (mis. kendaraan prioritas) |
| Graph | `core/structures/graph.py` | Tata letak area parkir / pencarian rute slot |

## Struktur folder

```
vehicle_management_system/
├── app.py              # Entry point Streamlit
├── core/
│   ├── services.py     # ParkingSystem — facade seluruh operasi
│   ├── sample_data.py  # Pemuat data contoh dari data/sample_data.json
│   ├── models/         # Vehicle, Transaction, HistoryRecord, Result, konstanta
│   ├── structures/     # Implementasi struktur data
│   └── algorithms/     # Algoritma sorting & searching
├── views/
│   └── parking_ui.py   # Antarmuka Streamlit
├── data/
│   └── sample_data.json  # Data contoh untuk demo
├── tests/              # Unit test
└── pyproject.toml
```

Inti logika ada di `ParkingSystem` (`core/services.py`), sebuah *facade*
yang menjadi satu pintu ke semua struktur data di atas. Setiap method
mengembalikan objek `Result` berisi status berhasil/gagal beserta pesannya,
jadi lapisan `views/` tidak perlu menangani exception.

## Menjalankan

Proyek ini memakai [uv](https://docs.astral.sh/uv/) sebagai manajer
dependensi. Butuh Python 3.12 atau lebih baru.

```bash
uv run streamlit run app.py
```

`uv` otomatis membuat dan menyinkronkan `.venv`, jadi tidak perlu
mengaktifkan virtual environment secara manual. Aplikasi terbuka di
`http://localhost:8501`.

`app.py` harus berada di root project: `streamlit run` menaruh direktori
skrip di `sys.path`, sehingga skrip yang ditempatkan langsung di `views/`
tidak bisa mengimpor `core`.

Tombol **Muat data contoh** di sidebar mengisi sistem dari
`data/sample_data.json`: 5 slot terisi, 2 kendaraan mengantre, 1 terdaftar
tapi belum masuk. Pemuatan lewat API publik `ParkingSystem`
(`registrasi()` lalu `check_in()`), jadi state yang terbentuk selalu sah.
Lihat `data/README.md` untuk format kolomnya.

Setiap operasi yang mengubah state menulis `data/state.json`. Sesi
berikutnya membaca file itu dan membangun ulang indeks hash plat serta
id. `data/sample_data.json` dipakai tombol **Muat data contoh**. Tombol
**Reset sistem** menulis snapshot kosong. Tombol **Muat ulang dari file**
menarik snapshot terakhir ke sesi yang sedang berjalan.

Menjalankan test:

```bash
uv run pytest
```

## Status pengembangan

Proyek masih dalam pengerjaan:

- [x] Model data (`Vehicle`, `Transaction`, `HistoryRecord`, `Result`) dan konstanta
- [x] `ParkingSystem`: registrasi, check-in, check-out, pencarian, undo, laporan
- [x] Struktur data inti: dynamic array, linked list, queue, stack
- [x] Antarmuka Streamlit di `views/parking_ui.py`
- [x] Data contoh di `data/sample_data.json`
- [x] Persistensi state ke `data/state.json` (simpan & muat ulang)
- [x] Unit test di `tests/`

Rencana pengembangan lanjutan (file-nya sengaja masih kosong):

- [ ] `bst.py` — `ParkingHistory` berbasis BST, riwayat urut tanpa sorting
- [x] `hash_table.py` — pencarian plat dan id rata-rata O(1). Pencarian nama pemilik memindai linked list, O(n)
- [ ] `heap.py` — antrean berprioritas
- [-] `graph.py` — tata letak area parkir
- [ ] `core/algorithms/` — sorting & searching
