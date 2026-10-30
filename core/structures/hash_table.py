class HashNode[T]:
    """Satu simpul di rantai bucket."""

    def __init__(self, key: str, value: T) -> None:
        self.key = key
        self.value = value
        self.next: HashNode[T] | None = None


MAX_LOAD_FACTOR = 0.75


class HashTable[T]:
    """Tabel hash dengan chaining.

    Dua kunci berbeda boleh jatuh di bucket yang sama; keduanya tetap
    disimpan di rantai bucket itu. Pencarian rata-rata O(1), tapi menjadi
    O(n) kalau semua kunci menabrak satu bucket. Supaya rantainya tidak
    memanjang, tabel digandakan begitu load factor melewati 0,75.
    """

    def __init__(self, capacity: int = 16, auto_rehash: bool = True) -> None:
        self._capacity = max(1, capacity)
        self._buckets: list[HashNode[T] | None] = [None] * self._capacity
        self._size = 0
        self._rehash_count = 0
        self._auto_rehash = auto_rehash  # False: rantai dibiarkan panjang

    def __len__(self) -> int:
        return self._size

    @property
    def capacity(self) -> int:
        """Jumlah bucket."""
        return self._capacity

    @property
    def size(self) -> int:
        return self._size

    @property
    def load_factor(self) -> float:
        """Rata-rata isi per bucket: jumlah kunci dibagi jumlah bucket."""
        return self._size / self._capacity

    @property
    def rehash_count(self) -> int:
        """Berapa kali tabel sudah digandakan."""
        return self._rehash_count

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
        if self._auto_rehash and self.load_factor > MAX_LOAD_FACTOR:
            self._rehash(self._capacity * 2)

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

    def items(self) -> list[tuple[str, T]]:
        """Seluruh pasangan kunci dan nilai, bucket demi bucket."""
        hasil: list[tuple[str, T]] = []
        for bucket in self._buckets:
            current = bucket
            while current is not None:
                hasil.append((current.key, current.value))
                current = current.next
        return hasil

    def bucket_sizes(self) -> list[int]:
        """Panjang rantai tiap bucket, berurutan indeks."""
        ukuran: list[int] = []
        for bucket in self._buckets:
            current = bucket
            panjang = 0
            while current is not None:
                panjang += 1
                current = current.next
            ukuran.append(panjang)
        return ukuran

    def stats(self) -> dict:
        """Ringkasan sebaran kunci: load factor, collision, rantai terpanjang."""
        ukuran = self.bucket_sizes()
        bertabrakan = [n for n in ukuran if n > 1]
        return {
            "size": self._size,
            "capacity": self._capacity,
            "load_factor": self.load_factor,
            "used_buckets": sum(1 for n in ukuran if n > 0),
            "empty_buckets": sum(1 for n in ukuran if n == 0),
            "collision_buckets": len(bertabrakan),
            "colliding_keys": sum(bertabrakan) - len(bertabrakan),
            "longest_chain": max(ukuran) if ukuran else 0,
            "rehash_count": self._rehash_count,
        }

    def _rehash(self, new_capacity: int) -> None:
        """Gandakan jumlah bucket lalu sebar ulang seluruh kunci."""
        lama = self.items()
        self._capacity = max(1, new_capacity)
        self._buckets = [None] * self._capacity
        self._size = 0
        self._rehash_count += 1
        for key, value in lama:
            index = self._index(key)
            node = HashNode(key, value)
            node.next = self._buckets[index]
            self._buckets[index] = node
            self._size += 1
