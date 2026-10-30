"""Binary min-heap dan antrean tunggu berprioritas di atasnya."""

from collections.abc import Iterator
from typing import Any

from core.models import PRIORITY_LABEL, Vehicle, priority_rank
from core.structures.dynamic_array import DynamicArray


class MinHeap:
    """Binary min-heap: kunci terkecil selalu di akar.

    Disimpan sebagai array, anak dari indeks i ada di 2i+1 dan 2i+2, jadi
    tidak perlu pointer sama sekali. Push dan pop O(log n), peek O(1).
    """

    def __init__(self) -> None:
        self._array = DynamicArray()

    @property
    def size(self) -> int:
        return len(self._array)

    def __len__(self) -> int:
        return len(self._array)

    def is_empty(self) -> bool:
        return len(self._array) == 0

    def _entry(self, index: int) -> tuple[Any, Any]:
        return self._array.get(index)

    def _swap(self, i: int, j: int) -> None:
        awal, akhir = self._array.get(i), self._array.get(j)
        self._array.set(i, akhir)
        self._array.set(j, awal)

    def push(self, key: Any, value: Any) -> None:
        """Masukkan nilai dengan kunci urutannya. O(log n)."""
        self._array.append((key, value))
        self._sift_up(len(self._array) - 1)

    def pop(self) -> Any | None:
        """Keluarkan nilai berkunci terkecil. O(log n)."""
        if self.is_empty():
            return None
        akar = self._entry(0)
        terakhir = self._array.pop()
        if len(self._array) > 0:
            self._array.set(0, terakhir)
            self._sift_down(0)
        return akar[1]

    def peek(self) -> Any | None:
        """Lihat nilai berkunci terkecil tanpa mengeluarkannya. O(1)."""
        return None if self.is_empty() else self._entry(0)[1]

    def peek_key(self) -> Any | None:
        """Kunci terkecil yang sedang di akar."""
        return None if self.is_empty() else self._entry(0)[0]

    def remove_at(self, index: int) -> Any | None:
        """Buang entri pada indeks lalu perbaiki bentuk heap. O(log n)."""
        if not 0 <= index < len(self._array):
            return None
        terbuang = self._entry(index)
        terakhir = self._array.pop()
        if index < len(self._array):
            self._array.set(index, terakhir)
            self._sift_down(index)
            self._sift_up(index)
        return terbuang[1]

    def entries(self) -> list[tuple[Any, Any]]:
        """Seluruh pasangan (kunci, nilai) menurut tata letak array heap."""
        return [self._entry(i) for i in range(len(self._array))]

    def sorted_values(self) -> list[Any]:
        """Nilai menurut urutan kunci. O(n log n) karena menyalin heap."""
        salinan = MinHeap()
        for key, value in self.entries():
            salinan.push(key, value)
        hasil: list[Any] = []
        while not salinan.is_empty():
            hasil.append(salinan.pop())
        return hasil

    def _sift_up(self, index: int) -> None:
        """Naikkan entri selama kuncinya lebih kecil dari induknya."""
        while index > 0:
            induk = (index - 1) // 2
            if self._entry(index)[0] >= self._entry(induk)[0]:
                return
            self._swap(index, induk)
            index = induk

    def _sift_down(self, index: int) -> None:
        """Turunkan entri selama ada anak yang kuncinya lebih kecil."""
        n = len(self._array)
        while True:
            terkecil = index
            for anak in (2 * index + 1, 2 * index + 2):
                if anak < n and self._entry(anak)[0] < self._entry(terkecil)[0]:
                    terkecil = anak
            if terkecil == index:
                return
            self._swap(index, terkecil)
            index = terkecil


class PriorityWaitingQueue:
    """Antrean tunggu parkir yang melayani prioritas lebih dulu.

    Kuncinya `(rank, urutan)`: rank dari PRIORITY_RANK, urutan dari
    penghitung yang selalu naik. Bagian urutan itulah yang membuat
    kendaraan berprioritas sama tetap dilayani FIFO, karena heap sendiri
    tidak menjamin stabilitas.
    """

    def __init__(self) -> None:
        self._heap = MinHeap()
        self._next_seq = 0
        self._front_seq = 0

    @property
    def size(self) -> int:
        return self._heap.size

    def __len__(self) -> int:
        return self._heap.size

    def __iter__(self) -> Iterator[Vehicle]:
        """Kendaraan menurut urutan layanan, bukan tata letak heap."""
        return iter(self._heap.sorted_values())

    def is_empty(self) -> bool:
        return self._heap.is_empty()

    def enqueue(self, vehicle: Vehicle) -> None:
        """Masukkan kendaraan ke antrean sesuai prioritasnya."""
        self._heap.push((priority_rank(vehicle.priority), self._next_seq), vehicle)
        self._next_seq += 1

    def dequeue(self) -> Vehicle | None:
        """Keluarkan kendaraan yang paling berhak dilayani."""
        return self._heap.pop()

    def peek(self) -> Vehicle | None:
        """Lihat kendaraan terdepan tanpa mengeluarkannya."""
        return self._heap.peek()

    def requeue_front(self, vehicle: Vehicle) -> None:
        """Kembalikan kendaraan ke depan antrean. Dipakai undo check-out."""
        self._front_seq -= 1
        self._heap.push((priority_rank(vehicle.priority), self._front_seq), vehicle)

    def remove_vehicle(self, vehicle_id: str) -> Vehicle | None:
        """Cabut satu kendaraan dari antrean. Dipakai undo enqueue. O(n)."""
        for index, (_, kendaraan) in enumerate(self._heap.entries()):
            if kendaraan.vehicle_id == vehicle_id:
                return self._heap.remove_at(index)
        return None

    def remove_last_enqueued(self) -> Vehicle | None:
        """Cabut kendaraan yang paling terakhir masuk antrean. O(n)."""
        terakhir: tuple[int, Any] | None = None
        for index, (key, _) in enumerate(self._heap.entries()):
            if terakhir is None or key[1] > terakhir[1]:
                terakhir = (index, key[1])
        return None if terakhir is None else self._heap.remove_at(terakhir[0])

    def display(self) -> list[Vehicle]:
        """Isi antrean menurut urutan layanan."""
        return self._heap.sorted_values()

    def group_counts(self) -> dict[str, int]:
        """Jumlah kendaraan mengantre per level prioritas."""
        jumlah = {nama: 0 for nama in PRIORITY_LABEL}
        for kendaraan in self._heap.sorted_values():
            jumlah[kendaraan.priority] = jumlah.get(kendaraan.priority, 0) + 1
        return jumlah
