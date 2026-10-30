"""Binary search tree, serta riwayat parkir dan daftar kendaraan di atasnya.

Semua operasi di sini iteratif. Versi rekursifnya lebih ringkas, tapi
kedalaman rekursinya sebesar tinggi pohon, dan pohon ini bisa merosot
menjadi rantai sepanjang n kalau datanya masuk dalam keadaan terurut —
di atas ~1000 catatan Python berhenti dengan RecursionError.
"""

from collections.abc import Callable, Iterator
from datetime import datetime
from typing import Any, Literal

from core.models import HistoryRecord, Vehicle


class BSTNode:
    """Satu simpul BST: satu data dan dua anak."""

    def __init__(self, data: Any) -> None:
        self.data = data
        self.left: BSTNode | None = None
        self.right: BSTNode | None = None


class BST:
    """Binary search tree: kiri lebih kecil, kanan lebih besar.

    Urutan diambil dari fungsi `key`, bukan dari datanya langsung, jadi
    pohon ini bisa dipakai untuk apa pun asal kuncinya bisa dibandingkan.
    Kunci yang sama ditimpa, seperti `HashTable.put()`.
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
        return iter(self.in_order())

    def is_empty(self) -> bool:
        return self.root is None

    def key_of(self, data: Any) -> Any:
        """Kunci urutan sebuah data menurut pohon ini."""
        return self._key(data)

    # ---- Sisip & cari ----

    def insert(self, data: Any) -> None:
        """Sisipkan data pada posisi yang menjaga invarian BST. O(h)."""
        baru = self._key(data)
        if self.root is None:
            self.root = BSTNode(data)
            self._size += 1
            return

        node = self.root
        while True:
            lama = self._key(node.data)
            if baru < lama:
                if node.left is None:
                    node.left = BSTNode(data)
                    self._size += 1
                    return
                node = node.left
            elif baru > lama:
                if node.right is None:
                    node.right = BSTNode(data)
                    self._size += 1
                    return
                node = node.right
            else:
                node.data = data
                return

    def search(self, key: Any) -> Any | None:
        """Cari data berdasarkan kuncinya, None kalau tidak ada. O(h)."""
        node = self.root
        while node is not None:
            lama = self._key(node.data)
            if key == lama:
                return node.data
            node = node.left if key < lama else node.right
        return None

    def min(self) -> Any | None:
        """Data berkunci terkecil. O(h)."""
        node = self.root
        if node is None:
            return None
        while node.left is not None:
            node = node.left
        return node.data

    def max(self) -> Any | None:
        """Data berkunci terbesar. O(h)."""
        node = self.root
        if node is None:
            return None
        while node.right is not None:
            node = node.right
        return node.data

    def between(self, low: Any, high: Any) -> list[Any]:
        """Data dengan kunci di rentang [low, high], terurut. O(h + k).

        Subpohon yang seluruh kuncinya di luar rentang tidak dikunjungi;
        inilah yang tidak bisa dilakukan linked list.
        """
        hasil: list[Any] = []
        tumpukan: list[BSTNode] = []
        node = self.root
        while node is not None or tumpukan:
            while node is not None:
                if self._key(node.data) < low:
                    node = node.right  # simpul dan kiri-nya pasti di bawah low
                else:
                    tumpukan.append(node)
                    node = node.left
            if not tumpukan:
                break
            node = tumpukan.pop()
            if self._key(node.data) > high:
                break  # in-order menanjak, sisanya pasti di atas high
            hasil.append(node.data)
            node = node.right
        return hasil

    # ---- Hapus ----

    def remove(self, key: Any) -> Any | None:
        """Hapus data berkunci `key`, kembalikan yang terhapus. O(h).

        Tiga kasus: daun dilepas, satu anak naik menggantikan, dan dua
        anak digantikan penerus (kunci terkecil di subpohon kanan).
        """
        induk: BSTNode | None = None
        node = self.root
        while node is not None and self._key(node.data) != key:
            induk = node
            node = node.left if key < self._key(node.data) else node.right
        if node is None:
            return None

        terhapus = node.data

        if node.left is not None and node.right is not None:
            induk_penerus = node
            penerus = node.right
            while penerus.left is not None:
                induk_penerus = penerus
                penerus = penerus.left
            node.data = penerus.data
            induk, node = induk_penerus, penerus

        anak = node.left if node.left is not None else node.right
        if induk is None:
            self.root = anak
        elif induk.left is node:
            induk.left = anak
        else:
            induk.right = anak

        self._size -= 1
        return terhapus

    def remove_max(self) -> Any | None:
        """Hapus data berkunci terbesar. O(h)."""
        terbesar = self.max()
        if terbesar is None:
            return None
        return self.remove(self._key(terbesar))

    # ---- Jelajah ----

    def in_order(self) -> list[Any]:
        """Kiri, simpul, kanan. Hasilnya terurut kecil ke besar."""
        hasil: list[Any] = []
        tumpukan: list[BSTNode] = []
        node = self.root
        while node is not None or tumpukan:
            while node is not None:
                tumpukan.append(node)
                node = node.left
            node = tumpukan.pop()
            hasil.append(node.data)
            node = node.right
        return hasil

    def pre_order(self) -> list[Any]:
        """Simpul, kiri, kanan. Urutan ini menyalin bentuk pohon."""
        if self.root is None:
            return []
        hasil: list[Any] = []
        tumpukan: list[BSTNode] = [self.root]
        while tumpukan:
            node = tumpukan.pop()
            hasil.append(node.data)
            if node.right is not None:
                tumpukan.append(node.right)
            if node.left is not None:
                tumpukan.append(node.left)
        return hasil

    def post_order(self) -> list[Any]:
        """Kiri, kanan, simpul. Anak selalu keluar sebelum induknya."""
        if self.root is None:
            return []
        hasil: list[Any] = []
        tumpukan: list[BSTNode] = [self.root]
        while tumpukan:
            node = tumpukan.pop()
            hasil.append(node.data)
            if node.left is not None:
                tumpukan.append(node.left)
            if node.right is not None:
                tumpukan.append(node.right)
        hasil.reverse()
        return hasil

    def level_order(self) -> list[Any]:
        """Jelajah per tingkat, dari akar ke bawah."""
        if self.root is None:
            return []
        hasil: list[Any] = []
        antrean: list[BSTNode] = [self.root]
        i = 0
        while i < len(antrean):
            node = antrean[i]
            i += 1
            hasil.append(node.data)
            if node.left is not None:
                antrean.append(node.left)
            if node.right is not None:
                antrean.append(node.right)
        return hasil

    def height(self) -> int:
        """Jumlah simpul di jalur terpanjang dari akar. Pohon kosong = 0.

        Tinggi inilah yang menentukan biaya cari, sisip, dan hapus. Pohon
        seimbang memberi h ≈ log2(n), sedangkan data yang masuk dalam
        keadaan terurut membuat h = n — secepat linked list, tidak lebih.
        BST ini tidak menyeimbangkan diri sendiri.
        """
        if self.root is None:
            return 0
        tertinggi = 0
        tumpukan: list[tuple[BSTNode, int]] = [(self.root, 1)]
        while tumpukan:
            node, dalam = tumpukan.pop()
            tertinggi = max(tertinggi, dalam)
            if node.left is not None:
                tumpukan.append((node.left, dalam + 1))
            if node.right is not None:
                tumpukan.append((node.right, dalam + 1))
        return tertinggi


def _diri_sendiri(data: Any) -> Any:
    """Fungsi kunci bawaan: datanya dibandingkan apa adanya."""
    return data


class HistoryTree:
    """Riwayat parkir berbasis BST, terurut waktu keluar.

    Kuncinya `(exit_time, vehicle_id)`; tanpa `vehicle_id` dua check-out
    pada waktu yang sama akan saling menimpa.
    """

    def __init__(self) -> None:
        self._tree = BST(key=self._key)

    @staticmethod
    def _key(record: HistoryRecord) -> tuple[datetime, str]:
        return (record.exit_time, record.vehicle_id)

    @property
    def size(self) -> int:
        return self._tree.size

    @property
    def root(self) -> BSTNode | None:
        """Akar pohon, untuk menggambar bentuknya."""
        return self._tree.root

    def __len__(self) -> int:
        return self._tree.size

    def __iter__(self) -> Iterator[HistoryRecord]:
        return iter(self._tree.in_order())

    def is_empty(self) -> bool:
        return self._tree.is_empty()

    def add(self, record: HistoryRecord) -> None:
        """Catat satu check-out. O(h)."""
        self._tree.insert(record)

    def remove_last(self) -> HistoryRecord | None:
        """Hapus catatan terbaru. Dipakai undo check-out. O(h)."""
        return self._tree.remove_max()

    def first(self) -> HistoryRecord | None:
        """Check-out paling lama. O(h)."""
        return self._tree.min()

    def last(self) -> HistoryRecord | None:
        """Check-out paling baru. O(h)."""
        return self._tree.max()

    def between(self, start: datetime, end: datetime) -> list[HistoryRecord]:
        """Riwayat yang keluar antara `start` dan `end`, terurut. O(h + k)."""
        return self._tree.between((start, ""), (end, "￿"))

    def search(self, exit_time: datetime, vehicle_id: str) -> HistoryRecord | None:
        """Cari satu catatan dari waktu keluar dan id kendaraannya. O(h)."""
        return self._tree.search((exit_time, vehicle_id))

    def height(self) -> int:
        """Tinggi pohon. Lihat `BST.height()`."""
        return self._tree.height()

    def display(self) -> list[HistoryRecord]:
        """Seluruh riwayat, lama ke baru."""
        return self._tree.in_order()


OrderBy = Literal["plate", "id"]


class VehicleTree:
    """Kendaraan terdaftar yang terurut nomor polisi atau ID."""

    def __init__(self, order_by: OrderBy = "plate") -> None:
        self.order_by: OrderBy = order_by
        self._tree = BST(key=self._key_for(order_by))

    @staticmethod
    def _key_for(order_by: OrderBy) -> Callable[[Vehicle], str]:
        return (lambda v: v.plate) if order_by == "plate" else (lambda v: v.vehicle_id)

    @property
    def size(self) -> int:
        return self._tree.size

    @property
    def root(self) -> BSTNode | None:
        """Akar pohon, untuk menggambar bentuknya."""
        return self._tree.root

    def __len__(self) -> int:
        return self._tree.size

    def __iter__(self) -> Iterator[Vehicle]:
        return iter(self._tree.in_order())

    def is_empty(self) -> bool:
        return self._tree.is_empty()

    def add(self, vehicle: Vehicle) -> None:
        """Masukkan kendaraan ke pohon. O(h)."""
        self._tree.insert(vehicle)

    def remove(self, key: str) -> Vehicle | None:
        """Keluarkan kendaraan berdasarkan kunci urutannya. O(h)."""
        return self._tree.remove(key)

    def search(self, key: str) -> Vehicle | None:
        """Cari kendaraan lewat pohon, bukan lewat hash. O(h)."""
        return self._tree.search(key)

    def between(self, low: str, high: str) -> list[Vehicle]:
        """Kendaraan dengan kunci di rentang [low, high]. O(h + k)."""
        return self._tree.between(low, high)

    def in_order(self) -> list[Vehicle]:
        """Terurut naik — inilah daftar kendaraan terurut."""
        return self._tree.in_order()

    def pre_order(self) -> list[Vehicle]:
        return self._tree.pre_order()

    def post_order(self) -> list[Vehicle]:
        return self._tree.post_order()

    def level_order(self) -> list[Vehicle]:
        return self._tree.level_order()

    def height(self) -> int:
        return self._tree.height()

    def traversals(self) -> dict[str, list[Vehicle]]:
        """Ketiga traversal sekaligus, untuk ditampilkan berdampingan."""
        return {
            "inorder": self.in_order(),
            "preorder": self.pre_order(),
            "postorder": self.post_order(),
        }
