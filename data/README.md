# Data contoh

`sample_data.json` dipakai untuk mengisi sistem saat demo, lewat
`core.sample_data.load_sample_data()`.

| Kolom | Isi |
| --- | --- |
| `plate` | Plat nomor, unik |
| `owner` | Nama pemilik |
| `vtype` | `MOBIL` atau `MOTOR` |
| `initial_status` | Kondisi awal yang diinginkan: `PARKED`, `WAITING`, atau `REGISTERED` |

`vehicle_id` tidak ada di file ini: ID dibuat otomatis oleh
`ParkingSystem.registrasi()` mengikuti urutan pendaftaran (V001, V002, ...).

`initial_status` bukan nilai yang ditulis langsung ke objek `Vehicle`.
Loader hanya memanggil `registrasi()` lalu `check_in()` lewat API publik
`ParkingSystem`, jadi status akhir ditentukan sistem itu sendiri: baris
`PARKED` mengisi slot sampai habis, sisanya otomatis masuk antrean.
Karena itu **urutan baris menentukan hasil** — baris `PARKED` harus
berada di atas baris `WAITING`.

Dengan `SLOT_CAPACITY = 5`, data contoh ini menghasilkan 5 slot terisi,
2 kendaraan mengantre, dan 1 kendaraan terdaftar tapi belum masuk.
