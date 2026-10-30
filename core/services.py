from datetime import datetime

from core.models import (
    DEFAULT_PRIORITY,
    MAX_SLOT_CAPACITY,
    MIN_SLOT_CAPACITY,
    SLOT_CAPACITY,
    HistoryRecord,
    Priority,
    Result,
    SearchBy,
    Transaction,
    Vehicle,
    VehicleType,
    count_occupied,
    slot_code,
)
from core.structures.bst import HistoryTree, OrderBy, VehicleTree
from core.structures.dynamic_array import ParkingSlots
from core.structures.hash_table import HashTable
from core.structures.heap import PriorityWaitingQueue
from core.structures.linked_list import VehicleList
from core.structures.stack import UndoStack


class ParkingSystem:
    """Facede: atau satu pintu untuk seluruh structure data smart Parking."""

    def __init__(self, capacity: int = SLOT_CAPACITY) -> None:
        self.slots: ParkingSlots = ParkingSlots(capacity)
        self.vehicles: VehicleList = VehicleList()
        self.by_plate: HashTable[Vehicle] = HashTable()
        self.by_id: HashTable[Vehicle] = HashTable()
        self.queue: PriorityWaitingQueue = PriorityWaitingQueue()
        self.undo: UndoStack = UndoStack()
        self.history: HistoryTree = HistoryTree()
        self.vehicle_tree: VehicleTree = VehicleTree("plate")

    def index_vehicle(self, vehicle: Vehicle) -> None:
        """Catat objek yang sama di indeks plat, indeks id, dan pohon urut."""
        self.by_plate.put(vehicle.plate, vehicle)
        self.by_id.put(vehicle.vehicle_id, vehicle)
        self.vehicle_tree.add(vehicle)

    def find(self, key: str, by: SearchBy = "plate") -> Vehicle | None:
        """Cari plat atau id lewat hash. Nama pemilik tetap dipindai di list."""
        if by == "plate":
            return self.by_plate.get(key)
        if by == "id":
            return self.by_id.get(key)
        return self.vehicles.search(key, by="owner")

    """ METHOD: Registrasi"""

    def registrasi(
        self,
        plate: str,
        owner: str,
        vtype: VehicleType,
        priority: Priority = DEFAULT_PRIORITY,
    ) -> Result[Vehicle]:
        if not all([plate, owner, vtype]):
            return Result.fail("Semua field harus diisi")
        if self.find(plate, by="plate"):
            return Result.fail("Kendaraan sudah terdaftar")

        vehicle_id = f"V{self.vehicles.size + 1:03d}"

        v = Vehicle(vehicle_id, plate, owner, vtype, priority=priority)
        self.vehicles.insert(v)
        self.index_vehicle(v)
        return Result.success(f"{plate} sudah {v.status}", v)

    """ METHOD: Check-in """

    def check_in(self, vehicle_plate: str) -> Result[Vehicle]:
        v = self.find(vehicle_plate, by="plate")
        if v is None:
            return Result.fail(f"Kendaraan dengan plat {vehicle_plate} tidak ditemukan")
        if v.status in ("PARKED", "WAITING"):
            return Result.fail(f"Kendaraan {v.vehicle_id} sudah {v.status}")

        idx = self.slots.find_available()
        if idx != -1:
            self.slots.assign(idx, v.vehicle_id)
            v.status, v.slot_index, v.entry_time = "PARKED", idx, datetime.now()
            self.undo.push(
                Transaction(tx_type="CHECK_IN", vehicle_id=v.vehicle_id, slot_index=idx)
            )
            return Result.success(f"{vehicle_plate} parkir di {slot_code(idx)}", v)

        self.queue.enqueue(v)
        v.status = "WAITING"
        self.undo.push(Transaction(tx_type="ENQUEUE", vehicle_id=v.vehicle_id))
        posisi = self.queue.display().index(v) + 1
        return Result.success(
            f"{vehicle_plate} masuk antrean prioritas {v.priority}, urutan {posisi}", v
        )

    """ METHOD: Check-out """

    def check_out(self, vehicle_plate: str) -> Result[Vehicle]:
        v = self.find(vehicle_plate, by="plate")
        if v is None or v.status != "PARKED":
            return Result.fail("Kendaraan tidak sedang parkir")

        if v.slot_index is None or v.entry_time is None:
            return Result.fail(f"Data parkir {vehicle_plate} tidak lengkap")

        idx = v.slot_index
        self.slots.release(idx)
        record = HistoryRecord(
            v.vehicle_id, v.plate, slot_code(idx), v.entry_time, datetime.now(), v.vtype
        )
        self.history.add(record)
        v.status, v.slot_index = "EXITED", None

        promoted_vehicle = None
        if not self.queue.is_empty():
            nxt = self.queue.dequeue()
            if nxt is not None:
                self.slots.assign(idx, nxt.vehicle_id)
                nxt.status, nxt.slot_index, nxt.entry_time = (
                    "PARKED",
                    idx,
                    datetime.now(),
                )
                promoted_vehicle = nxt

        self.undo.push(
            Transaction(
                tx_type="CHECK_OUT",
                vehicle_id=v.vehicle_id,
                slot_index=idx,
                promoted_id=promoted_vehicle.vehicle_id if promoted_vehicle else None,
            )
        )
        msg = f"{vehicle_plate} keluar dari {slot_code(idx)}"
        if promoted_vehicle:
            msg += f", {promoted_vehicle.plate} naik dari antrean"
        return Result.success(msg, v)

    """ METHOD: Ubah jumlah slot """

    def resize_slots(self, new_capacity: int) -> Result[dict]:
        """Ubah jumlah slot parkir tanpa kehilangan kendaraan yang terdaftar.

        Diperbesar: slot baru langsung diisi kendaraan paling depan di
        antrean, sampai antrean habis atau slot baru penuh.
        Diperkecil: ditolak kalau slot yang akan dibuang masih ada
        penghuninya, jadi tidak ada kendaraan yang hilang dari slot.

        Tumpukan undo dikosongkan: transaksi di dalamnya menyimpan indeks
        slot, dan indeks itu bisa menunjuk slot yang sudah tidak ada lagi
        setelah kapasitas berubah.
        """
        if new_capacity < MIN_SLOT_CAPACITY:
            return Result.fail(f"Jumlah slot minimal {MIN_SLOT_CAPACITY}")
        if new_capacity > MAX_SLOT_CAPACITY:
            return Result.fail(f"Jumlah slot maksimal {MAX_SLOT_CAPACITY}")

        old_capacity = self.slots.capacity
        if new_capacity == old_capacity:
            return Result.fail(f"Jumlah slot sudah {old_capacity}")

        if new_capacity < old_capacity:
            terisi = [
                slot_code(i)
                for i in range(new_capacity, old_capacity)
                if self.slots.get(i) is not None
            ]
            if terisi:
                # Pesannya cuma menyebut beberapa slot pertama; kalau yang
                # terisi banyak, daftar lengkapnya malah tidak terbaca.
                disebut = ", ".join(terisi[:5])
                if len(terisi) > 5:
                    disebut += f", dan {len(terisi) - 5} slot lain"
                return Result.fail(
                    f"Slot {disebut} masih terisi, check-out dulu "
                    f"sebelum mengurangi jumlah slot"
                )

        self.slots.resize(new_capacity)
        self.undo.clear()
        promoted = self._fill_from_queue()

        msg = f"Jumlah slot {old_capacity} menjadi {new_capacity}"
        if promoted:
            msg += f", {len(promoted)} kendaraan naik dari antrean"
        return Result.success(
            msg,
            {
                "capacity": new_capacity,
                "previous_capacity": old_capacity,
                "promoted": [v.plate for v in promoted],
            },
        )

    def _fill_from_queue(self) -> list[Vehicle]:
        """Isi setiap slot kosong dengan kendaraan terdepan di antrean."""
        promoted: list[Vehicle] = []
        while not self.queue.is_empty():
            idx = self.slots.find_available()
            if idx == -1:
                break
            v = self.queue.dequeue()
            if v is None:
                break
            self.slots.assign(idx, v.vehicle_id)
            v.status, v.slot_index, v.entry_time = "PARKED", idx, datetime.now()
            promoted.append(v)
        return promoted

    """ SEARCH """

    def search(self, key: str, by: SearchBy = "plate") -> Result[Vehicle]:
        v = self.find(key, by)
        return (
            Result.success("Ditemukan", v)
            if v
            else Result.fail("Kendaran tidak ditemukan")
        )

    """ UNDO """

    def undo_last(self) -> Result[Transaction]:
        # Menggunakan self.undo, bukan global undo
        if self.undo.is_empty():
            return Result.fail("Tidak ada transaksi untuk dibatalkan")
        tx = self.undo.pop()
        if tx is None:
            return Result.fail("Tidak ada transaksi untuk dibatalkan")

        v = self.find(tx.vehicle_id, by="id")
        if v is None:
            return Result.fail(f"Kendaraan {tx.vehicle_id} tidak ditemukan")

        if tx.tx_type == "CHECK_IN":
            if tx.slot_index is not None:
                self.slots.release(tx.slot_index)
            v.status, v.slot_index, v.entry_time = "REGISTERED", None, None

        elif tx.tx_type == "ENQUEUE":
            self.queue.remove_vehicle(v.vehicle_id)
            v.status = "REGISTERED"

        elif tx.tx_type == "CHECK_OUT":
            idx = tx.slot_index
            if idx is None:
                return Result.fail(f"Transaksi {tx.tx_type} tidak menyimpan slot")

            if tx.promoted_id:  # Kembalikan ke depan antrian
                p = self.find(tx.promoted_id, by="id")
                self.slots.release(idx)
                if p is not None:
                    self.queue.requeue_front(p)
                    p.status, p.slot_index, p.entry_time = "WAITING", None, None
            record = self.history.remove_last()
            self.slots.assign(idx, v.vehicle_id)
            v.status, v.slot_index = "PARKED", idx
            if record:
                v.entry_time = record.entry_time

        return Result.success(f"Undo {tx.tx_type}, {tx.vehicle_id}")

    """ BST: daftar kendaraan terurut """

    def sorted_vehicles(self, order_by: OrderBy = "plate") -> Result[list[Vehicle]]:
        """Kendaraan terurut nomor polisi atau ID, lewat in-order BST."""
        pohon = self.vehicle_tree if order_by == self.vehicle_tree.order_by else None
        if pohon is None:
            pohon = VehicleTree(order_by)
            for kendaraan in self.vehicles:
                pohon.add(kendaraan)
        return Result.success(f"Kendaraan terurut {order_by}", pohon.in_order())

    def vehicle_traversals(self, order_by: OrderBy = "plate") -> Result[dict]:
        """Hasil traversal inorder, preorder, dan postorder beserta tinggi pohon."""
        pohon = self.vehicle_tree
        if order_by != pohon.order_by:
            pohon = VehicleTree(order_by)
            for kendaraan in self.vehicles:
                pohon.add(kendaraan)
        hasil = pohon.traversals()
        return Result.success(
            f"Traversal BST kendaraan ({order_by})",
            {**hasil, "height": pohon.height(), "size": pohon.size, "order_by": order_by},
        )

    """ Hash table: sebaran kunci """

    def hash_stats(self) -> Result[dict]:
        """Load factor dan statistik collision kedua indeks hash."""
        return Result.success(
            "Statistik hash table",
            {"by_plate": self.by_plate.stats(), "by_id": self.by_id.stats()},
        )

    """ View Slots """

    def show_slots(self) -> Result[list[tuple[str, str | None]]]:
        slots = [(slot_code(i), self.slots.get(i)) for i in range(self.slots.capacity)]
        return Result.success("Status slot", slots)

    """ View Queue """

    def show_queue(self) -> Result[list[Vehicle]]:
        return Result.success("Antrean parkir", self.queue.display())

    """ View History """

    def show_history(self) -> Result[list[HistoryRecord]]:
        """Riwayat check-out, lama ke baru. Urutannya datang dari in-order BST."""
        return Result.success("Riwayat parkir", self.history.display())

    """ Statistics """

    def statistics(self) -> Result[dict]:
        occupied = count_occupied(self.slots)
        stats = {
            "total_slots": self.slots.capacity,
            "occupied_slots": occupied,
            "available_slots": self.slots.capacity - occupied,
            "queue_len": self.queue.size,
            "total_served": self.history.size,
        }
        return Result.success("Statistik berhasil ditampilkan", stats)
