class HashNode[T]:
    """Satu simpul di rantai bucket."""

    def __init__(self, key: str, value: T) -> None:
        self.key = key
        self.value = value
        self.next: HashNode[T] | None = None


class HashTable[T]:
    """Tabel hash dengan chaining.

    Dua kunci berbeda boleh jatuh di bucket yang sama. Keduanya tetap
    disimpan di rantai bucket itu. Pencarian rata-rata O(1). Kalau semua
    kunci menabrak satu bucket, memindai rantai itu menjadi O(n).
    """

    def __init__(self, capacity: int = 16) -> None:
        self._capacity = max(1, capacity)
        self._buckets: list[HashNode[T] | None] = [None] * self._capacity
        self._size = 0

    def __len__(self) -> int:
        return self._size

    def _index(self, key: str) -> int:
        total = 0
        for char in key:
            total = (total * 31 + ord(char)) % self._capacity
        return total

    def put(self, key: str, value: T) -> None:
        """Simpan nilai pada kunci. Kunci yang sudah ada ditimpa. O(1) rata-rata."""
        index = self._index(key)
        current = self._buckets[index]
        while current is not None:
            if current.key == key:
                current.value = value
                return
            current = current.next
        node = HashNode(key, value)
        node.next = self._buckets[index]
        self._buckets[index] = node
        self._size += 1

    def get(self, key: str) -> T | None:
        """Ambil nilai, atau None kalau kunci tidak ada. O(1) rata-rata."""
        current = self._buckets[self._index(key)]
        while current is not None:
            if current.key == key:
                return current.value
            current = current.next
        return None

    def chain_length(self, key: str) -> int:
        """Jumlah simpul di bucket yang ditempati kunci ini."""
        current = self._buckets[self._index(key)]
        count = 0
        while current is not None:
            count += 1
            current = current.next
        return count
