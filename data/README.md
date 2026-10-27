# Data contoh

`sample_data.json` dipakai untuk mengisi sistem saat demo, lewat
`core.sample_data.load_sample_data()`.

| Kolom | Isi |
| --- | --- |
| `plate` | Plat nomor, unik |
| `owner` | Nama pemilik |
| `vtype` | `MOBIL` atau `MOTOR` |
| `initial_status` | Kondisi awal yang diinginkan: `PARKED`, `WAITING`, atau `REGISTERED` |

`vehicle_id` dibuat otomatis oleh `ParkingSystem.registrasi()` mengikuti
urutan pendaftaran (V001, V002, ...).

`initial_status` menjadi masukan loader. Loader memanggil `registrasi()`
lalu `check_in()` lewat API publik `ParkingSystem`, dan status akhir
ditentukan sistem itu sendiri: baris `PARKED` mengisi slot sampai habis,
sisanya otomatis masuk antrean.
Karena itu **urutan baris menentukan hasil** — baris `PARKED` harus
berada di atas baris `WAITING`.

Dengan `SLOT_CAPACITY = 5`, data contoh ini menghasilkan 5 slot terisi,
2 kendaraan mengantre, dan 1 kendaraan terdaftar tapi belum masuk.

## State berjalan

`state.json` menyimpan kondisi sistem saat aplikasi berjalan: kendaraan
terdaftar, isi slot, antrean, riwayat check-out, dan tumpukan undo.
Aplikasi menulis file ini setelah registrasi, check-in, check-out, undo,
muat data contoh, dan reset. File ini berada di `.gitignore`.

Isinya:

| Bagian | Isi |
| --- | --- |
| `vehicles` | Seluruh kendaraan terdaftar, berurutan, beserta status dan waktu masuk |
| `slots` | Penghuni `A01`–`A05`, id kendaraan atau `null` |
| `queue` | Id antrean dari depan ke belakang |
| `history` | Riwayat check-out dari yang paling lama |
| `undo` | Transaksi dari yang paling lama ke yang paling baru |

Saat file dimuat, daftar kendaraan dibangun lebih dulu. Indeks hash plat
dan id lalu menunjuk ke objek kendaraan yang sama, dan antrean serta slot
memakai objek itu juga.
