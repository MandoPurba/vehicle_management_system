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

Isinya 24 baris: 5 `PARKED`, 2 `WAITING`, dan 17 `REGISTERED`. Dengan
`SLOT_CAPACITY = 5`, hasilnya 5 slot terisi, 2 kendaraan mengantre, dan 17
kendaraan terdaftar tapi belum masuk. Mayoritas `REGISTERED` disengaja:
kendaraannya jadi bahan untuk mencoba check-in satu-satu, dan untuk
melihat efek **Jumlah slot** di sidebar — perbesar slotnya, lalu check-in
sisa kendaraan sampai antrean terbentuk lagi.

## State berjalan

`state.json` menyimpan kondisi sistem saat aplikasi berjalan: kendaraan
terdaftar, isi slot, antrean, riwayat check-out, dan tumpukan undo.
Aplikasi menulis file ini setelah registrasi, check-in, check-out, undo,
ubah jumlah slot, muat data contoh, dan reset. File ini berada di
`.gitignore`.

Isinya:

| Bagian | Isi |
| --- | --- |
| `vehicles` | Seluruh kendaraan terdaftar, berurutan, beserta status dan waktu masuk |
| `capacity` | Jumlah slot parkir saat disimpan, bisa diubah dari sidebar |
| `slots` | Penghuni `A01`–`A0n`, id kendaraan atau `null`, sebanyak `capacity` |
| `queue` | Id antrean dari depan ke belakang |
| `history` | Riwayat check-out dari yang paling lama |
| `undo` | Transaksi dari yang paling lama ke yang paling baru |

Saat file dimuat, daftar kendaraan dibangun lebih dulu. Indeks hash plat
dan id lalu menunjuk ke objek kendaraan yang sama, dan antrean serta slot
memakai objek itu juga.
