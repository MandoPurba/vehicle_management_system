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

## Struktur data yang dipakai

Tiap fitur dipetakan ke satu struktur data:

| Struktur | Modul | Dipakai untuk |
| --- | --- | --- |
| Dynamic Array | `core/structures/dynamic_array.py` | `ParkingSlots` — slot parkir berindeks |
| Linked List | `core/structures/linked_list.py` | `VehicleList` — daftar kendaraan terdaftar |
| Queue | `core/structures/queue.py` | `WaitingQueue` — antrean saat parkir penuh (FIFO) |
| Stack | `core/structures/stack.py` | `UndoStack` — riwayat transaksi untuk undo (LIFO) |
| Hash Table | `core/structures/hash_table.py` | Pencarian kendaraan dalam O(1) |
| BST | `core/structures/bst.py` | `ParkingHistory` — riwayat terurut waktu |
| Heap | `core/structures/heap.py` | Prioritas antrean (mis. kendaraan prioritas) |
| Graph | `core/structures/graph.py` | Tata letak area parkir / pencarian rute slot |

## Struktur folder

```
vehicle_management_system/
├── app.py              # Entry point aplikasi
├── core/
│   ├── services.py     # ParkingSystem — facade seluruh operasi
│   ├── structures/     # Implementasi struktur data
│   └── algorithms/     # Algoritma sorting & searching
├── views/              # Tampilan / antarmuka CLI
├── data/               # Penyimpanan data
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
uv run app.py
```

`uv` otomatis membuat dan menyinkronkan `.venv`, jadi tidak perlu
mengaktifkan virtual environment secara manual.

Menjalankan test:

```bash
uv run pytest
```

## Status pengembangan

Proyek masih dalam pengerjaan:

- [x] Rancangan `ParkingSystem` beserta alur registrasi, check-in, check-out, dan undo
- [ ] Implementasi modul struktur data di `core/structures/` (masih kosong)
- [ ] Model data (`Vehicle`, `Transaction`, `HistoryRecord`, `Result`) dan konstanta `SLOT_CAPACITY`
- [ ] Antarmuka CLI di `views/`
- [ ] Persistensi data ke `data/`
- [ ] Unit test
