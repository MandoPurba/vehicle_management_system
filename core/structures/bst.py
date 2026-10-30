"""Binary search tree, dan riwayat parkir yang dibangun di atasnya.

Dua lapis, sama seperti `dynamic_array.py` (DynamicArray lalu ParkingSlots):

* `BST` — strukturnya sendiri. Tiap simpul menyimpan satu data; semua
  data di subpohon kiri kuncinya lebih kecil, semua yang di kanan lebih
  besar. Invarian itulah yang membuat pencarian hanya menyusuri satu
  jalur dari akar ke daun, O(h) dengan h = tinggi pohon.
* `HistoryTree` — pemakaiannya di Smart Parking: riwayat check-out yang
  terurut waktu keluar tanpa pernah memanggil sort.

Catatan penting soal tinggi pohon ada di docstring `BST.height()`.
"""

from collections.abc import Callable, Iterator
from datetime import datetime
from typing import Any

from core.models import HistoryRecord


class BSTNode:
    """Satu simpul BST: satu data dan dua anak."""

    def __init__(self, data: Any) -> None:
        self.data = data
        self.left: BSTNode | None = None
        self.right: BSTNode | None = None


class BST:
    """Binary search tree: kiri lebih kecil, kanan lebih besar.

    Urutan tidak diambil dari datanya langsung, tapi dari fungsi `key`.
    Jadi pohon yang sama bisa dipakai untuk apa pun asal kuncinya bisa
    dibandingkan dengan `<`. Tanpa `key`, datanya sendiri jadi kunci.

    Dua kunci yang sama tidak bisa hidup berdampingan: yang baru menimpa
    yang lama, sama seperti `HashTable.put()`.
    """

    def __init__(self, key: Callable[[Any], Any] | None = None) -> None:
        self.root: BSTNode | None = None
        self._key: Callable[[Any], Any] = key if key is not None else _diri_sendiri
        self._size = 0

    @property
    def size(self) -> int:
        return self._size

    def __len__(self) -> int:
        return self._size

    def __iter__(self) -> Iterator[Any]:
        """Jelajah in-order, jadi datanya keluar urut dari kecil ke besar."""
        yield from self._in_order(self.root)

    def is_empty(self) -> bool:
        return self.root is None

    # ---- Sisip ----

    def insert(self, data: Any) -> None:
        """Sisipkan data pada posisi yang menjaga invarian BST. O(h).

        Rekursif: tiap panggilan mengembalikan akar subpohon yang sudah
        diperbarui, lalu induknya memasang hasil itu sebagai anaknya.
        Pola "kembalikan akar subpohon" ini membuat penyisipan tidak
        perlu menyimpan pointer ke induk.
        """
        self.root = self._insert(self.root, data)

    def _insert(self, node: BSTNode | None, data: Any) -> BSTNode:
        if node is None:  # base case: ketemu tempat kosong
            self._size += 1
            return BSTNode(data)

        baru, lama = self._key(data), self._key(node.data)
        if baru < lama:
            node.left = self._insert(node.left, data)
        elif baru > lama:
            node.right = self._insert(node.right, data)
        else:
            node.data = data  # kunci sama: timpa, ukuran tidak berubah
        return node

    # ---- Cari ----

    def search(self, key: Any) -> Any | None:
        """Cari data berdasarkan kuncinya, None kalau tidak ada. O(h).

        Iteratif, bukan rekursif: tiap langkah membuang separuh sisa
        pohon, jadi tidak ada yang perlu diingat di stack pemanggilan.
        """
        node = self.root
        while node is not None:
            lama = self._key(node.data)
            if key == lama:
                return node.data
            node = node.left if key < lama else node.right
        return None

    def min(self) -> Any | None:
        """Data berkunci terkecil: terus ke kiri sampai habis. O(h)."""
        node = self.root
        if node is None:
            return None
        while node.left is not None:
            node = node.left
        return node.data

    def max(self) -> Any | None:
        """Data berkunci terbesar: terus ke kanan sampai habis. O(h)."""
        node = self.root
        if node is None:
            return None
        while node.right is not None:
            node = node.right
        return node.data

    def between(self, low: Any, high: Any) -> list[Any]:
        """Seluruh data dengan kunci di rentang [low, high], terurut. O(h + k).

        Inilah yang tidak bisa dilakukan linked list tanpa memindai semua
        simpul: begitu kunci sebuah simpul sudah di bawah `low`, seluruh
        subpohon kirinya pasti di bawah `low` juga, jadi tidak dikunjungi.
        """
        hasil: list[Any] = []
        self._between(self.root, low, high, hasil)
        return hasil

    def _between(self, node: BSTNode | None, low: Any, high: Any, hasil: list) -> None:
        if node is None:
            return
        kunci = self._key(node.data)
        if kunci > low:  # kiri masih mungkin berisi yang >= low
            self._between(node.left, low, high, hasil)
        if low <= kunci <= high:
            hasil.append(node.data)
        if kunci < high:  # kanan masih mungkin berisi yang <= high
            self._between(node.right, low, high, hasil)

    # ---- Hapus ----

    def remove(self, key: Any) -> Any | None:
        """Hapus data berkunci `key`, kembalikan yang terhapus. O(h).

        Tiga kasus klasik BST:

        1. Simpul daun — cukup dilepas.
        2. Satu anak — anaknya naik menggantikan posisinya.
        3. Dua anak — datanya ditimpa penerusnya (*successor*), yaitu
           kunci terkecil di subpohon kanan, lalu penerus itu yang
           dihapus dari subpohon kanan. Penerus dipilih karena dialah
           satu-satunya data yang boleh duduk di posisi itu tanpa
           merusak invarian: lebih besar dari seluruh kiri, lebih kecil
           dari sisa kanan.
        """
        terhapus = self.search(key)
        if terhapus is None:
            return None
        self.root = self._remove(self.root, key)
        self._size -= 1
        return terhapus

    def _remove(self, node: BSTNode | None, key: Any) -> BSTNode | None:
        if node is None:
            return None

        lama = self._key(node.data)
        if key < lama:
            node.left = self._remove(node.left, key)
            return node
        if key > lama:
            node.right = self._remove(node.right, key)
            return node

        # Ketemu. Kasus 1 dan 2 sekaligus: kalau satu sisi kosong,
        # sisi lain yang naik (None kalau dua-duanya kosong).
        if node.left is None:
            return node.right
        if node.right is None:
            return node.left

        # Kasus 3: ambil penerus dari subpohon kanan.
        penerus = node.right
        while penerus.left is not None:
            penerus = penerus.left
        node.data = penerus.data
        node.right = self._remove(node.right, self._key(penerus.data))
        return node

    def remove_max(self) -> Any | None:
        """Hapus data berkunci terbesar. O(h)."""
        terbesar = self.max()
        if terbesar is None:
            return None
        return self.remove(self._key(terbesar))

    # ---- Jelajah & bentuk pohon ----

    def in_order(self) -> list[Any]:
        """Seluruh data terurut kecil ke besar. O(n), tanpa sorting.

        Urutannya gratis dari bentuk pohonnya: kunjungi kiri, cetak
        simpulnya, lalu kanan.
        """
        return list(self)

    def _in_order(self, node: BSTNode | None) -> Iterator[Any]:
        if node is None:
            return
        yield from self._in_order(node.left)
        yield node.data
        yield from self._in_order(node.right)

    def pre_order(self) -> list[Any]:
        """Simpul dulu, baru anaknya. Urutan ini menyalin bentuk pohon.

        Menyisipkan ulang hasil pre-order ke pohon kosong menghasilkan
        pohon yang bentuknya persis sama — tidak berlaku untuk in-order.
        """
        hasil: list[Any] = []
        self._pre_order(self.root, hasil)
        return hasil

    def _pre_order(self, node: BSTNode | None, hasil: list) -> None:
        if node is None:
            return
        hasil.append(node.data)
        self._pre_order(node.left, hasil)
        self._pre_order(node.right, hasil)

    def height(self) -> int:
        """Jumlah simpul di jalur terpanjang dari akar. Pohon kosong = 0.

        Tinggi inilah yang menentukan biaya cari, sisip, dan hapus.
        Pohon seimbang memberi h ≈ log2(n); kalau data disisipkan dalam
        keadaan sudah terurut, tiap simpul baru selalu jatuh ke kanan
        dan pohonnya merosot menjadi rantai dengan h = n — persis
        secepat linked list, tidak lebih.

        BST ini tidak menyeimbangkan diri sendiri. Jadi untuk riwayat
        parkir yang memang lahir urut waktu, keuntungannya bukan di
        tinggi pohon, melainkan di `between()`: linked list harus
        memindai seluruh simpul untuk menjawab pertanyaan rentang waktu.
        """
        return self._height(self.root)

    def _height(self, node: BSTNode | None) -> int:
        if node is None:
            return 0
        return 1 + max(self._height(node.left), self._height(node.right))


def _diri_sendiri(data: Any) -> Any:
    """Fungsi kunci bawaan: datanya dibandingkan apa adanya."""
    return data


class HistoryTree:
    """Riwayat parkir berbasis BST, terurut waktu keluar.

    Kuncinya pasangan `(exit_time, vehicle_id)`, bukan `exit_time` saja:
    dua check-out bisa tercatat pada mikrodetik yang sama, dan kalau
    kuncinya seri yang satu akan menimpa yang lain. `vehicle_id` memutus
    seri itu, dan urutan waktunya tetap yang menentukan karena elemen
    pertama tuple dibandingkan lebih dulu.

    Inilah riwayat yang dipakai `ParkingSystem.history`. Antarmukanya
    sengaja sama dengan `ParkingHistory` versi linked list (`add`,
    `remove_last`, `size`, `display`) sehingga pertukarannya tidak
    mengubah satu pun pemanggilan di `ParkingSystem`, ditambah
    `between()` untuk pertanyaan rentang waktu.
    """

    def __init__(self) -> None:
        self._tree = BST(key=self._key)

    @staticmethod
    def _key(record: HistoryRecord) -> tuple[datetime, str]:
        return (record.exit_time, record.vehicle_id)

    @property
    def size(self) -> int:
        return self._tree.size

    def __len__(self) -> int:
        return self._tree.size

    def __iter__(self) -> Iterator[HistoryRecord]:
        """Riwayat dari yang paling lama ke yang paling baru."""
        return iter(self._tree)

    def is_empty(self) -> bool:
        return self._tree.is_empty()

    def add(self, record: HistoryRecord) -> None:
        """Catat satu check-out. O(h)."""
        self._tree.insert(record)

    def remove_last(self) -> HistoryRecord | None:
        """Hapus catatan terbaru, yaitu simpul paling kanan. O(h).

        Dipakai undo check-out: kendaraannya dikembalikan ke slot, jadi
        riwayat keluarnya harus ikut dibatalkan.
        """
        return self._tree.remove_max()

    def first(self) -> HistoryRecord | None:
        """Check-out paling lama. O(h)."""
        return self._tree.min()

    def last(self) -> HistoryRecord | None:
        """Check-out paling baru. O(h)."""
        return self._tree.max()

    def between(self, start: datetime, end: datetime) -> list[HistoryRecord]:
        """Riwayat yang keluar antara `start` dan `end`, terurut. O(h + k).

        Batas bawah memakai `vehicle_id` kosong dan batas atas memakai
        karakter besar, supaya seluruh kendaraan pada detik batas ikut
        terjaring berapa pun id-nya.
        """
        return self._tree.between((start, ""), (end, "￿"))

    def search(self, exit_time: datetime, vehicle_id: str) -> HistoryRecord | None:
        """Cari satu catatan dari waktu keluar dan id kendaraannya. O(h)."""
        return self._tree.search((exit_time, vehicle_id))

    def height(self) -> int:
        """Tinggi pohon. Lihat `BST.height()` soal pohon yang merosot."""
        return self._tree.height()

    def display(self) -> list[HistoryRecord]:
        """Seluruh riwayat, lama ke baru.

        Beda dari `ParkingHistory.display()` yang mencetak ke stdout dan
        mengembalikan None: di sini daftarnya dikembalikan, jadi bisa
        langsung dipakai `ParkingSystem.show_history()` dan tabel di
        `views/`.
        """
        return self._tree.in_order()
