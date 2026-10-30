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
| Ubah jumlah slot | Memperbesar atau memperkecil parkiran saat aplikasi jalan |
| Reset | Mengosongkan seluruh state sistem, jumlah slot tetap |
| Data contoh | Mengisi sistem dari `data/sample_data.json` sekali klik |

## Struktur data yang dipakai

Tiap fitur dipetakan ke satu struktur data:

| Struktur | Modul | Dipakai untuk |
| --- | --- | --- |
| Dynamic Array | `core/structures/dynamic_array.py` | `ParkingSlots` — slot parkir berindeks (awalnya `SLOT_CAPACITY` = 5, bisa di-resize) |
| Linked List | `core/structures/linked_list.py` | `VehicleList` — daftar kendaraan terdaftar, dan `ParkingHistory` — riwayat parkir |
| Queue | `core/structures/queue.py` | `WaitingQueue` — antrean saat parkir penuh (FIFO) |
| Stack | `core/structures/stack.py` | `UndoStack` — riwayat transaksi untuk undo (LIFO) |
| Hash Table | `core/structures/hash_table.py` | Indeks pencarian plat dan id, rata-rata O(1) |
| BST | `core/structures/bst.py` | `BST` — binary search tree, dan `HistoryTree` — riwayat parkir terurut waktu keluar tanpa sorting |
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

Butuh Python 3.12 atau lebih baru. Ada dua cara, pilih salah satu.

**Tanpa uv** (cukup `pip`, cocok kalau uv belum terinstall):

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

`python app.py` mendeteksi bahwa dirinya belum jalan di bawah
`streamlit run`, lalu meluncurkan ulang dirinya sendiri lewat CLI
Streamlit. Jadi tidak perlu mengingat perintah `streamlit run`, dan
peringatan `missing ScriptRunContext` tidak muncul lagi. Argumen tambahan
tetap diteruskan, mis. `python app.py --server.port=8600`.

**Dengan uv:**

```bash
uv run streamlit run app.py
```

`uv` otomatis membuat dan menyinkronkan `.venv`, jadi tidak perlu
mengaktifkan virtual environment secara manual.

Aplikasi terbuka di `http://localhost:8501`.

`app.py` harus berada di root project: `streamlit run` menaruh direktori
skrip di `sys.path`, sehingga skrip yang ditempatkan langsung di `views/`
tidak bisa mengimpor `core`.

Tombol **Muat data contoh** di sidebar mengisi sistem dari
`data/sample_data.json`: 24 kendaraan, 5 langsung mengisi slot, 2
mengantre, dan 17 sisanya terdaftar tapi belum masuk. Pemuatan lewat API
publik `ParkingSystem` (`registrasi()` lalu `check_in()`), jadi state yang
terbentuk selalu sah. Lihat `data/README.md` untuk format kolomnya.

Panel **Jumlah slot** di sidebar mengubah kapasitas parkiran tanpa
mengulang dari nol:

- Diperbesar — slot baru muncul kosong, lalu langsung diisi kendaraan
  paling depan di antrean sampai antrean habis.
- Diperkecil — hanya boleh kalau slot yang dibuang sudah kosong. Kalau
  masih ada penghuninya, operasinya ditolak beserta kode slotnya, jadi
  tidak ada kendaraan yang hilang dari slot.
- Tumpukan undo dikosongkan tiap kali kapasitas berubah: transaksi di
  dalamnya menyimpan indeks slot, dan indeks itu bisa menunjuk slot yang
  sudah tidak ada lagi.

Setiap operasi yang mengubah state menulis `data/state.json`, termasuk
jumlah slotnya. Sesi berikutnya membaca file itu dan membangun ulang
indeks hash plat serta id. Tombol **Reset sistem** menulis snapshot
kosong dengan jumlah slot yang sedang dipakai.

Menjalankan test:

```bash
python -m pytest        # butuh `pip install pytest` dulu
uv run pytest           # kalau pakai uv
```

## Status pengembangan

Proyek masih dalam pengerjaan:

- [x] Model data (`Vehicle`, `Transaction`, `HistoryRecord`, `Result`) dan konstanta
- [x] `ParkingSystem`: registrasi, check-in, check-out, pencarian, undo, laporan
- [x] Ubah jumlah slot saat aplikasi jalan (`resize_slots()`)
- [x] Struktur data inti: dynamic array, linked list, queue, stack
- [x] Antarmuka Streamlit di `views/parking_ui.py`
- [x] Data contoh di `data/sample_data.json`
- [x] Persistensi state ke `data/state.json` (simpan & muat ulang)
- [x] Unit test di `tests/`

Rencana pengembangan lanjutan (file-nya sengaja masih kosong):

- [x] `bst.py` — `BST` dan `HistoryTree`, riwayat urut tanpa sorting. Belum dipasang
      di `ParkingSystem`; `ParkingHistory` versi linked list masih yang dipakai
- [x] `hash_table.py` — pencarian plat dan id rata-rata O(1). Pencarian nama pemilik memindai linked list, O(n)
- [ ] `heap.py` — antrean berprioritas
- [ ] `graph.py` — tata letak area parkir
- [ ] `core/algorithms/` — sorting & searching
