from collections.abc import Iterator

from core.models import Vehicle


class Node:
    """Satu simpul antrean."""

    def __init__(self, value: Vehicle) -> None:
        self.value: Vehicle = value
        self.next: Node | None = None


class WaitingQueue:
    """Antrean FIFO kendaraan yang menunggu slot kosong.

    Menyimpan front dan rear supaya enqueue dan dequeue sama-sama O(1).
    """

    def __init__(self) -> None:
        self._front: Node | None = None
        self._rear: Node | None = None
        self._size = 0

    @property
    def size(self) -> int:
        return self._size

    def __len__(self) -> int:
        return self._size

    def __iter__(self) -> Iterator[Vehicle]:
        current = self._front
        while current is not None:
            yield current.value
            current = current.next

    def is_empty(self) -> bool:
        return self._front is None

    def enqueue(self, vehicle: Vehicle) -> None:
        """Masuk ke belakang antrean. O(1)."""
        node = Node(vehicle)
        if self._rear is None:
            self._front = self._rear = node
        else:
            self._rear.next = node
            self._rear = node
        self._size += 1

    def dequeue(self) -> Vehicle | None:
        """Keluarkan kendaraan paling depan. O(1)."""
        if self._front is None:
            return None
        node = self._front
        self._front = node.next
        if self._front is None:
            self._rear = None
        self._size -= 1
        return node.value

    def push_front(self, vehicle: Vehicle) -> None:
        """Sisipkan di depan antrean. Dipakai undo check-out. O(1)."""
        node = Node(vehicle)
        node.next = self._front
        self._front = node
        if self._rear is None:
            self._rear = node
        self._size += 1

    def remove_rear(self) -> Vehicle | None:
        """Buang kendaraan paling belakang. Dipakai undo enqueue. O(n)."""
        if self._rear is None:
            return None

        removed = self._rear
        if self._front is self._rear:
            self._front = self._rear = None
        else:
            current = self._front
            while current is not None and current.next is not self._rear:
                current = current.next
            if current is not None:
                current.next = None
                self._rear = current
        self._size -= 1
        return removed.value

    def peek(self) -> Vehicle | None:
        """Lihat kendaraan terdepan tanpa mengeluarkannya."""
        return self._front.value if self._front else None

    def display(self) -> list[Vehicle]:
        """Isi antrean dari depan ke belakang."""
        return list(self)
