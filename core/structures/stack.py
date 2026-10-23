from collections.abc import Iterator

from core.models import Transaction


class Node:
    """Satu simpul tumpukan."""

    def __init__(self, value: Transaction) -> None:
        self.value: Transaction = value
        self.next: Node | None = None


class UndoStack:
    """Tumpukan LIFO berisi transaksi, agar yang terakhir bisa dibatalkan.

    Push dan pop di kepala linked list, jadi keduanya O(1).
    """

    def __init__(self) -> None:
        self._top: Node | None = None
        self._size = 0

    @property
    def size(self) -> int:
        return self._size

    def __len__(self) -> int:
        return self._size

    def __iter__(self) -> Iterator[Transaction]:
        current = self._top
        while current is not None:
            yield current.value
            current = current.next

    def is_empty(self) -> bool:
        return self._top is None

    def push(self, transaction: Transaction) -> None:
        """Simpan transaksi di puncak. O(1)."""
        node = Node(transaction)
        node.next = self._top
        self._top = node
        self._size += 1

    def pop(self) -> Transaction | None:
        """Ambil transaksi terakhir. O(1)."""
        if self._top is None:
            return None
        node = self._top
        self._top = node.next
        self._size -= 1
        return node.value

    def peek(self) -> Transaction | None:
        """Lihat transaksi terakhir tanpa mengambilnya."""
        return self._top.value if self._top else None

    def display(self) -> list[Transaction]:
        """Isi tumpukan dari yang terbaru ke terlama."""
        return list(self)
