from collections.abc import Iterator
from typing import ClassVar

from core.models import HistoryRecord, SearchBy, Vehicle


class Node:
    """Satu simpul linked list."""

    def __init__(self, value: Vehicle) -> None:
        self.value: Vehicle = value
        self.next: Node | None = None


class VehicleList:
    """Singly linked list berisi seluruh kendaraan terdaftar.

    Menyimpan tail agar penyisipan di akhir tetap O(1).
    """

    _FIELDS: ClassVar[dict[str, str]] = {
        "id": "vehicle_id",
        "plate": "plate",
        "owner": "owner",
    }

    def __init__(self) -> None:
        self._head: Node | None = None
        self._tail: Node | None = None
        self._size = 0

    @property
    def size(self) -> int:
        return self._size

    def __len__(self) -> int:
        return self._size

    def __iter__(self) -> Iterator[Vehicle]:
        current = self._head
        while current is not None:
            yield current.value
            current = current.next

    def is_empty(self) -> bool:
        return self._head is None

    def insert(self, vehicle: Vehicle) -> None:
        """Sisipkan kendaraan di akhir daftar. O(1)."""
        node = Node(vehicle)
        if self._tail is None:
            self._head = self._tail = node
        else:
            self._tail.next = node
            self._tail = node
        self._size += 1

    def search(self, key: str, by: SearchBy = "plate") -> Vehicle | None:
        """Cari kendaraan berdasarkan plat, id, atau pemilik. O(n)."""
        for vehicle in self:
            found = getattr(vehicle, self._FIELDS[by])
            if found == key:
                return vehicle
        return None

    def remove(self, vehicle_id: str) -> Vehicle | None:
        """Hapus kendaraan berdasarkan id, kembalikan yang terhapus. O(n)."""
        previous: Node | None = None
        current = self._head
        while current is not None:
            if current.value.vehicle_id == vehicle_id:
                if previous is None:
                    self._head = current.next
                else:
                    previous.next = current.next
                if current is self._tail:
                    self._tail = previous
                self._size -= 1
                return current.value
            previous, current = current, current.next
        return None

    def display(self) -> list[Vehicle]:
        """Seluruh kendaraan dalam urutan penyisipan."""
        return list(self)


class HistoryNode:
    def __init__(self, data: HistoryRecord) -> None:
        self.data: HistoryRecord = data
        self.next: HistoryNode | None = None


class ParkingHistory:
    def __init__(self) -> None:
        self.head: HistoryNode | None = None
        self.tail: HistoryNode | None = None
        self.size: int = 0

    def add(self, record: HistoryRecord) -> None:
        """Tambah di tail."""
        node = HistoryNode(record)
        if self.head is None or self.tail is None:
            self.head = self.tail = node
        else:
            self.tail.next = node
            self.tail = node
        self.size += 1

    def remove_last(self) -> HistoryRecord | None:
        """Hapus dan kembalikan node terakhir. O(n)."""
        if self.head is None or self.tail is None:
            return None

        record = self.tail.data

        if self.head is self.tail:
            self.head = self.tail = None
        else:
            current = self.head
            while current.next is not None and current.next is not self.tail:
                current = current.next
            current.next = None
            self.tail = current

        self.size -= 1
        return record

    def display(self) -> None:
        """Tampilkan riwayar dari yng paling lma"""
        if self.head is None:
            print("Riwayat parkir kosong")
            return
        current = self.head
        no = 1
        while current is not None:
            r = current.data
            print(
                f"{no}. {r.vehicle_id} | {r.plate} | {r.slot_code} | "
                f"{r.entry_time:%H:%M} - {r.exit_time:%H:%M}"
            )
            current = current.next
            no += 1
