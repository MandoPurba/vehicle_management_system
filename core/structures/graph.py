"""Graf berbobot dengan adjacency list, BFS, DFS, dan Dijkstra."""

from core.structures.hash_table import HashTable
from core.structures.heap import MinHeap

INFINITE = float("inf")


class Graph:
    """Graf tak berarah berbobot. Ketetanggaan disimpan di HashTable.

    Adjacency list dipilih karena peta parkir jarang terhubung penuh:
    memorinya O(V + E), bukan O(V^2) seperti matriks ketetanggaan.
    """

    def __init__(self) -> None:
        self._adjacency: HashTable[list[tuple[str, int]]] = HashTable()
        self._kind: HashTable[str] = HashTable()
        self._nodes: list[str] = []

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    @property
    def edge_count(self) -> int:
        return sum(len(self.neighbors(n)) for n in self._nodes) // 2

    def _tetangga(self, name: str) -> list[tuple[str, int]]:
        """Daftar tetangga yang tersimpan, dibuat kalau simpulnya baru."""
        tersimpan = self._adjacency.get(name)
        if tersimpan is None:
            tersimpan = []
            self._adjacency.put(name, tersimpan)
            self._nodes.append(name)
        return tersimpan

    def add_node(self, name: str, kind: str = "NODE") -> None:
        """Tambah simpul. Memanggil ulang nama yang sama tidak menduplikasi."""
        self._tetangga(name)
        self._kind.put(name, kind)

    def add_edge(self, a: str, b: str, weight: int) -> None:
        """Hubungkan dua simpul dua arah dengan bobot jarak."""
        self.add_node(a)
        self.add_node(b)
        self._tetangga(a).append((b, weight))
        self._tetangga(b).append((a, weight))

    def nodes(self, kind: str | None = None) -> list[str]:
        """Nama simpul, bisa disaring menurut jenisnya."""
        if kind is None:
            return list(self._nodes)
        return [n for n in self._nodes if self._kind.get(n) == kind]

    def kind_of(self, name: str) -> str | None:
        """Jenis sebuah simpul."""
        return self._kind.get(name)

    def neighbors(self, name: str) -> list[tuple[str, int]]:
        """Tetangga sebuah simpul beserta bobotnya, kosong kalau tidak ada."""
        return self._adjacency.get(name) or []

    def has_node(self, name: str) -> bool:
        return self._adjacency.get(name) is not None

    def bfs(self, start: str) -> list[str]:
        """Urutan kunjungan melebar dari `start`. O(V + E)."""
        if not self.has_node(start):
            return []
        terkunjungi = {start}
        antrean = [start]
        hasil: list[str] = []
        i = 0
        while i < len(antrean):
            node = antrean[i]
            i += 1
            hasil.append(node)
            for tetangga, _ in self.neighbors(node):
                if tetangga not in terkunjungi:
                    terkunjungi.add(tetangga)
                    antrean.append(tetangga)
        return hasil

    def dfs(self, start: str) -> list[str]:
        """Urutan kunjungan mendalam dari `start`. O(V + E)."""
        if not self.has_node(start):
            return []
        terkunjungi: set[str] = set()
        tumpukan = [start]
        hasil: list[str] = []
        while tumpukan:
            node = tumpukan.pop()
            if node in terkunjungi:
                continue
            terkunjungi.add(node)
            hasil.append(node)
            for tetangga, _ in reversed(self.neighbors(node)):
                if tetangga not in terkunjungi:
                    tumpukan.append(tetangga)
        return hasil

    def bfs_path(self, start: str, goal: str) -> list[str]:
        """Jalur dengan simpul tersedikit, bobot diabaikan. O(V + E)."""
        if not (self.has_node(start) and self.has_node(goal)):
            return []
        if start == goal:
            return [start]
        sebelum: dict[str, str] = {start: start}
        antrean = [start]
        i = 0
        while i < len(antrean):
            node = antrean[i]
            i += 1
            for tetangga, _ in self.neighbors(node):
                if tetangga in sebelum:
                    continue
                sebelum[tetangga] = node
                if tetangga == goal:
                    return _rangkai(sebelum, start, goal)
                antrean.append(tetangga)
        return []

    def dijkstra(self, start: str) -> tuple[dict[str, float], dict[str, str]]:
        """Jarak terpendek dari `start` ke semua simpul. O((V + E) log V).

        Simpul berikutnya diambil dari MinHeap, jadi yang jaraknya paling
        kecil selalu diproses lebih dulu.
        """
        jarak: dict[str, float] = {n: INFINITE for n in self._nodes}
        sebelum: dict[str, str] = {}
        if not self.has_node(start):
            return jarak, sebelum

        jarak[start] = 0
        selesai: set[str] = set()
        heap = MinHeap()
        heap.push(0, start)

        while not heap.is_empty():
            node = heap.pop()
            if node is None:  # hanya terjadi kalau heap kosong
                break
            if node in selesai:
                continue
            selesai.add(node)
            for tetangga, bobot in self.neighbors(node):
                calon = jarak[node] + bobot
                if calon < jarak[tetangga]:
                    jarak[tetangga] = calon
                    sebelum[tetangga] = node
                    heap.push(calon, tetangga)
        return jarak, sebelum

    def shortest_path(self, start: str, goal: str) -> tuple[list[str], float]:
        """Jalur terpendek menurut bobot, beserta total jaraknya."""
        if not (self.has_node(start) and self.has_node(goal)):
            return [], INFINITE
        jarak, sebelum = self.dijkstra(start)
        if jarak.get(goal, INFINITE) == INFINITE:
            return [], INFINITE
        sebelum[start] = start
        return _rangkai(sebelum, start, goal), jarak[goal]


def _rangkai(sebelum: dict[str, str], start: str, goal: str) -> list[str]:
    """Susun jalur dari peta pendahulu, dibaca mundur dari tujuan."""
    jalur = [goal]
    while jalur[-1] != start:
        jalur.append(sebelum[jalur[-1]])
    jalur.reverse()
    return jalur
