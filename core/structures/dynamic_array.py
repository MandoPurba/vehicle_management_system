

class DynamicArray:
    """Array dinamis: buffer berkapasitas tetap yang digandakan saat penuh.

    Hanya menyimpan panjang logis (size) dan kapasitas fisik (capacity),
    persis seperti cara list bekerja di balik layar.
    """

    def __init__(self, capacity: int = 4) -> None:
        self._capacity = max(1, capacity)
        self._size = 0
        self._buffer = self._make_buffer(self._capacity)

    @staticmethod
    def _make_buffer(n: int) -> list:
        """Alokasi buffer kosong sebesar n."""
        return [None] * n

    def __len__(self) -> int:
        return self._size

    @property
    def capacity(self) -> int:
        return self._capacity

    def _resize(self, new_capacity: int) -> None:
        """Pindahkan isi ke buffer baru yang lebih besar."""
        new_buffer = self._make_buffer(new_capacity)
        for i in range(self._size):
            new_buffer[i] = self._buffer[i]
        self._buffer = new_buffer
        self._capacity = new_capacity

    def append(self, value) -> None:
        """Tambah elemen di akhir. Amortized O(1)."""
        if self._size == self._capacity:
            self._resize(self._capacity * 2)
        self._buffer[self._size] = value
        self._size += 1

    def get(self, index: int):
        """Ambil elemen pada indeks. O(1)."""
        if not 0 <= index < self._size:
            raise IndexError(f"Indeks {index} di luar jangkauan")
        return self._buffer[index]

    def set(self, index: int, value) -> None:
        """Ganti elemen pada indeks. O(1)."""
        if not 0 <= index < self._size:
            raise IndexError(f"Indeks {index} di luar jangkauan")
        self._buffer[index] = value

    def pop(self):
        """Buang elemen terakhir, kembalikan isinya. O(1).

        Buffer fisik tidak dikecilkan, hanya panjang logisnya yang turun,
        sama seperti list Python. Slot yang dilepas dikosongkan supaya
        tidak menahan referensi ke objek yang sudah dibuang.
        """
        if self._size == 0:
            raise IndexError("Array kosong")
        self._size -= 1
        value = self._buffer[self._size]
        self._buffer[self._size] = None
        return value


class ParkingSlots:
    """Slot parkir berindeks tetap. Tiap slot berisi vehicle_id atau None.

    Dibangun di atas DynamicArray; kapasitas diisi penuh dengan None
    sejak awal karena jumlah slot parkir fisik tidak berubah.
    """

    def __init__(self, capacity: int) -> None:
        self._array = DynamicArray(capacity)
        for _ in range(capacity):
            self._array.append(None)

    @property
    def capacity(self) -> int:
        """Jumlah slot parkir."""
        return len(self._array)

    def get(self, index: int) -> str | None:
        """vehicle_id penghuni slot, atau None kalau kosong."""
        return self._array.get(index)

    def find_available(self) -> int:
        """Indeks slot kosong pertama, atau -1 kalau penuh. O(n)."""
        for i in range(self.capacity):
            if self._array.get(i) is None:
                return i
        return -1

    def assign(self, index: int, vehicle_id: str) -> None:
        """Isi slot dengan kendaraan."""
        self._array.set(index, vehicle_id)

    def release(self, index: int) -> None:
        """Kosongkan slot."""
        self._array.set(index, None)

    def resize(self, new_capacity: int) -> None:
        """Ubah jumlah slot parkir.

        Diperbesar: slot baru ditambahkan di ekor dalam keadaan kosong.
        Diperkecil: slot di ekor dibuang. Pemanggil yang memastikan slot
        itu sudah kosong, di sini tidak ada pemeriksaan penghuni.
        """
        if new_capacity < 1:
            raise ValueError("Jumlah slot minimal 1")
        while self.capacity < new_capacity:
            self._array.append(None)
        while self.capacity > new_capacity:
            self._array.pop()

    def is_full(self) -> bool:
        return self.find_available() == -1
