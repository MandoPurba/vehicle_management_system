# Vehicle Management System

Sistem manajemen parkir kendaraan (*Smart Parking*) yang dibangun di atas
struktur data yang diimplementasikan sendiri dari nol — tanpa memakai
`list`/`dict` bawaan Python sebagai struktur inti. Proyek mata kuliah
Struktur Data (DS01).

## Fitur

### Dari UTS

| Fitur | Keterangan |
| --- | --- |
| Registrasi | Mendaftarkan kendaraan baru (ID, plat, pemilik, tipe, prioritas) |
| Check-in | Menempatkan kendaraan ke slot kosong, atau masuk antrean bila penuh |
| Check-out | Mengosongkan slot, mencatat riwayat, lalu menaikkan kendaraan dari antrean |
| Pencarian | Mencari kendaraan berdasarkan plat, ID, atau pemilik |
| Undo | Membatalkan transaksi terakhir (check-in / antre / check-out) |
| Laporan | Status slot, isi antrean, riwayat parkir, dan statistik |
| Statistik rekursif | `count_occupied_recursive`, `sum_costs_recursive`, `max_duration_recursive` |
| Ubah jumlah slot | Memperbesar atau memperkecil parkiran saat aplikasi jalan |
| Reset | Mengosongkan seluruh state sistem, jumlah slot tetap |
| Data contoh | Mengisi sistem dari `data/sample_data.json` sekali klik |

### Tambahan UAS

| No | Fitur | Materi | Di mana |
| --- | --- | --- | --- |
| 1 | Pencarian cepat nomor polisi | Hash Table | `core/structures/hash_table.py`; tab **Struktur data** menampilkan load factor, collision, dan rehash |
| 2 | Daftar kendaraan terurut | BST | `core/structures/bst.py` (`VehicleTree`); tab **Kendaraan (BST)** menampilkan inorder, preorder, postorder, dan gambar percabangannya |
| 3 | Parkir prioritas | Heap | `core/structures/heap.py`; empat level prioritas (disabilitas, dosen, tamu, umum) di tab **Antrean** |
| 4 | Peta area parkir dan rute | Graph | `core/structures/graph.py` + `core/parking_map.py`; tab **Slot & peta** menampilkan slot kosong terdekat dari gerbang/gedung beserta gambar petanya |
| 5 | Pengurutan riwayat parkir | Sorting & Searching | `core/algorithms/sorting.py` dan `searching.py`; tab **Riwayat** mengurutkan menurut waktu, durasi, atau biaya lalu binary search di atasnya |
| 6 | Dashboard statistik | Recursion + visualisasi | tab **Dashboard**: kartu ringkasan, lima grafik, dan tiga angka yang dihitung rekursif |
| 7 | Halaman benchmark | Analisis kompleksitas | `core/benchmark.py`; tab **Benchmark** mengukur n = 1.000 / 10.000 / 100.000 |

## Struktur data yang dipakai

Tiap fitur dipetakan ke satu struktur data:

| Struktur | Modul | Dipakai untuk |
| --- | --- | --- |
| Dynamic Array | `core/structures/dynamic_array.py` | `ParkingSlots` — slot parkir berindeks, bisa di-resize. Juga jadi penyimpan `MinHeap` |
| Linked List | `core/structures/linked_list.py` | `VehicleList` — daftar kendaraan terdaftar. `ParkingHistory` tinggal sebagai pembanding |
| Queue | `core/structures/queue.py` | `WaitingQueue` — antrean FIFO, kini jadi pembanding `PriorityWaitingQueue` |
| Stack | `core/structures/stack.py` | `UndoStack` — riwayat transaksi untuk undo (LIFO) |
| Hash Table | `core/structures/hash_table.py` | Indeks plat dan id rata-rata O(1), chaining + rehash di load factor 0,75. Juga jadi adjacency list `Graph` |
| BST | `core/structures/bst.py` | `HistoryTree` — riwayat urut waktu, dan `VehicleTree` — kendaraan urut plat/ID |
| Heap | `core/structures/heap.py` | `MinHeap` dan `PriorityWaitingQueue` — antrean berprioritas. `MinHeap` juga dipakai Dijkstra |
| Graph | `core/structures/graph.py` | Peta gerbang, blok parkir, dan gedung: BFS, DFS, dan Dijkstra |
| Sorting | `core/algorithms/sorting.py` | Merge, insertion, bubble, dan quick sort untuk riwayat parkir |
| Searching | `core/algorithms/searching.py` | Binary search dan linear search pada riwayat terurut |
| Recursion | `core/algorithms/recursion.py` | Tiga perhitungan statistik tanpa loop |

## Struktur folder

```
vehicle_management_system/
├── app.py              # Entry point Streamlit
├── core/
│   ├── services.py     # ParkingSystem — facade seluruh operasi
│   ├── persistence.py  # Simpan & muat state ke data/state.json
│   ├── sample_data.py  # Pemuat data contoh dari data/sample_data.json
│   ├── parking_map.py  # Peta kampus & pencarian slot terdekat
│   ├── benchmark.py    # Pengukuran waktu eksekusi
│   ├── models/         # Vehicle, Transaction, HistoryRecord, Result, konstanta
│   ├── structures/     # Implementasi struktur data
│   └── algorithms/     # Recursion, sorting, searching
├── views/
│   ├── parking_ui.py   # Antarmuka Streamlit, delapan tab
│   ├── charts.py       # Palet & penyiapan data grafik
│   └── diagrams.py     # Diagram Mermaid peta dan pohon BST
├── data/
│   └── sample_data.json  # Data contoh untuk demo
├── tests/              # Unit test
└── pyproject.toml
```

Inti logika ada di `ParkingSystem` (`core/services.py`), sebuah *facade*
yang menjadi satu pintu ke semua struktur data di atas. Setiap method
mengembalikan objek `Result` berisi status berhasil/gagal beserta pesannya,
jadi lapisan `views/` tidak perlu menangani exception.

### Catatan desain

**Semua operasi BST iteratif.** Versi rekursifnya lebih ringkas, tapi
kedalaman rekursinya sebesar tinggi pohon. Riwayat parkir lahir urut
waktu sehingga pohonnya merosot menjadi rantai, dan di atas ~1000
catatan Python berhenti dengan `RecursionError`. Diukur: 5.000 data
terurut memberi tinggi pohon 5.000, sedangkan 100.000 data teracak
hanya 41.

**Antrean prioritas berkunci `(rank, nomor urut)`.** Heap sendiri tidak
menjamin stabilitas, jadi tanpa nomor urut itu kendaraan berprioritas
sama bisa saling menyalip. Undo enqueue mencabut kendaraan yang
ditunjuk, bukan yang paling belakang, karena heap tidak punya
"belakang".

**Tarif parkir kampus proporsional per menit**, dibulatkan ke ratusan
rupiah, dan kendaraan yang keluar tanpa sempat parkir tidak ditagih.
Bukan tarif per jam penuh seperti parkir umum.

**Rehash hash table bisa dimatikan** lewat `HashTable(auto_rehash=False)`.
Dipakai test dan demo collision: dengan rehash menyala, rantai tabrakan
otomatis bubar sehingga collision-nya justru tidak bisa ditunjukkan.

**Isi tab dihitung lazy** lewat `st.tabs(on_change="rerun")`. Tanpa itu
Dijkstra, traversal BST, dan statistik hash ikut jalan setiap rerun
meski tabnya tidak dibuka.

### Riwayat parkir memakai BST

`ParkingSystem.history` adalah `HistoryTree`, binary search tree berkunci
`(exit_time, vehicle_id)`. `vehicle_id` ada di kunci untuk memutus seri:
dua check-out bisa tercatat pada waktu yang sama, dan kalau kuncinya
hanya `exit_time`, catatan yang satu akan menimpa yang lain.

Yang didapat dari BST:

- Jelajah in-order mengeluarkan riwayat urut waktu keluar tanpa pernah
  memanggil sort, jadi `data/state.json` dan tabel di UI langsung urut.
- `between(start, end)` menjawab pertanyaan rentang waktu tanpa memindai
  seluruh catatan — subpohon yang kuncinya di luar rentang tidak
  dikunjungi. Ini yang tidak bisa dilakukan linked list.
- `remove_last()` membuang simpul paling kanan, dipakai undo check-out.

Satu hal yang perlu diakui: `BST` di sini tidak menyeimbangkan diri, dan
riwayat parkir lahir urut waktu. Tiap catatan baru selalu jatuh ke kanan,
jadi pohonnya merosot menjadi rantai — diukur dengan 7 catatan, tingginya
7, sama saja dengan linked list. Keuntungan BST di proyek ini ada di
`between()` dan pada riwayat yang disisipkan tidak berurutan, bukan pada
tinggi pohon. Penyeimbangan (AVL/red-black) adalah langkah lanjutannya.

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
- [x] Antarmuka Streamlit delapan tab di `views/parking_ui.py`
- [x] Data contoh di `data/sample_data.json`
- [x] Persistensi state ke `data/state.json` (simpan & muat ulang)
- [x] Unit test di `tests/` (75 test)

Fitur wajib UAS:

- [x] `hash_table.py` — plat dan id rata-rata O(1), load factor dan collision ditampilkan
- [x] `bst.py` — `HistoryTree` dan `VehicleTree`, ketiga traversal, gambar percabangan
- [x] `heap.py` — `MinHeap` dan antrean empat level prioritas
- [x] `graph.py` — peta kampus, BFS, DFS, Dijkstra, slot kosong terdekat
- [x] `core/algorithms/` — sorting, binary search, dan rekursi
- [x] `benchmark.py` — perbandingan waktu eksekusi pada n bertingkat

Belum dikerjakan:

- [ ] Penyeimbangan pohon (AVL / red-black) supaya riwayat tidak merosot jadi rantai
