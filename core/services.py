from datetime import datetime

class ParkingSystem:
    """ Facede: atau satu pintu untuk seluruh structure data smart Parking."""

    def __init__(self, capacity: int = SLOT_CAPACITY) -> None:
        self.slots: ParkingSlots = ParkingSlots(capacity)
        self.vehicles: VehicleList = VehicleList()
        self.queue: WaitingQueue = WaitingQueue()
        self.undo: UndoStack = UndoStack()
        self.history: ParkingHistory = ParkingHistory()


    """ METHOD: Registrasi"""
    def registrasi(self, vehicle_id: str, plate: str, owner: str, vtype: VehicleType) -> Result[Vehicle]:
        if not all([vehicle_id, plate, owner, vtype]):
            return Result.fail("Semua field harus diisi")
        if self.vehicles.search(vehicle_id, by="id") or self.vehicles.search(plate, by="plate"):
            return Result.fail("Kendaraan sudah terdaftar")

        v = Vehicle(vehicle_id, plate, owner, vtype)
        self.vehicles.insert(v)
        return Result.success(f"{vehicle_id} sudah {v.status}", v)


    """ METHOD: Check-in """
    def check_in(self, vehicle_plate: str) -> Result[Vehicle]:
        v = self.vehicles.search(vehicle_plate, by="plate")
        if v is None:
            return Result.fail(f"Kendaraan dengan plat {vehicle_plate} tidak ditemukan")
        if v.status in ("PARKED", "WAITING"):
            return Result.fail(f"Kendaraan {v.vehicle_id} sudah {v.status}")

        idx = self.slots.find_available()
        if idx != -1:
            self.slots.assign(idx, v.vehicle_id)
            v.status, v.slot_index, v.entry_time = "PARKED", idx, datetime.now()
            self.undo.push(Transaction(tx_type="CHECK_IN", vehicle_id=v.vehicle_id, slot_index=idx))
            return Result.success(f"{vehicle_plate} parkir di {slot_code(idx)}", v)

        self.queue.enqueue(v)
        v.status = "WAITING"
        self.undo.push(Transaction(tx_type="ENQUEUE", vehicle_id=v.vehicle_id))
        return Result.success(f"{vehicle_plate} masuk antrean", v)


    """ METHOD: Check-out """
    def check_out(self, vehicle_plate: str) -> Result[Vehicle]:
        v = self.vehicles.search(vehicle_plate, by="plate")
        if v is None or v.status != "PARKED":
            return Result.fail(f"Kendaraan tidak sedang parkir")

        idx = v.slot_index
        self.slots.release(idx)
        record = HistoryRecord(v.vehicle_id, v.plate, slot_code(idx), v.entry_time, datetime.now())
        self.history.add(record)
        v.status, v.slot_index = "EXITED", None

        promoted_vehicle = None
        if not self.queue.is_empty():
            nxt = self.queue.dequeue()
            self.slots.assign(idx, nxt.vehicle_id)
            nxt.status, nxt.slot_index, nxt.entry_time = "PARKED", idx, datetime.now()
            promoted_vehicle = nxt

        self.undo.push(Transaction(
            tx_type="CHECK_OUT",
            vehicle_id=v.vehicle_id,
            slot_index=idx,
            promoted_id=promoted_vehicle.vehicle_id if promoted_vehicle else None
        ))
        msg = f"{vehicle_plate} keluar dari {slot_code(idx)}"
        if promoted_vehicle:
            msg += f", {promoted_vehicle.plate} naik dari antrean"
        return Result.success(msg, v)

    """ SEARCH """
    def search(self, key: str, by: SearchBy = "plate") -> Result[Vehicle]:
        v = self.vehicles.search(key, by)
        return Result.success("Ditemukan", v) if v else Result.fail("Kendaran tidak ditemukan")


    """ UNDO """
    def undo_last(self) -> Result[Transaction]:
        # Menggunakan self.undo, bukan global undo
        if self.undo.is_empty():
            return Result.fail("Tidak ada transaksi untuk dibatalkan")
        tx = self.undo.pop()
        v = self.vehicles.search(tx.vehicle_id, by="id")

        if tx.tx_type == "CHECK_IN":
            self.slots.release(tx.slot_index)
            v.status, v.slot_index, v.entry_time = "REGISTERED", None, None

        elif tx.tx_type == "ENQUEUE":
            self.queue.remove_rear()
            v.status = "REGISTERED"

        elif tx.tx_type == "CHECK_OUT":
            idx = tx.slot_index
            if tx.promoted_id:                                                      # Kembalikan ke depan antrian
                p = self.vehicles.search(tx.promoted_id, by="id")
                self.slots.release(idx)
                self.queue.push_front(p)
                p.status, p.slot_index, p.entry_time = "WAITING", None, None
            record = self.history.remove_last()
            self.slots.assign(idx, v.vehicle_id)
            v.status, v.slot_index = "PARKED", idx
            if record:
                v.entry_time = record.entry_time

        return Result.success(f"Undo {tx.tx_type}, {tx.vehicle_id}")

    """ View Slots """
    def show_slots(self) -> Result[list[tuple[str, Optional[str]]]]:
        slots = [(slot_code(i), self.slots.get(i)) for i in range(self.slots.capacity)]
        return Result.success("Status slot", slots)

    """ View Queue """
    def show_queue(self) -> Result[list[Vehicle]]:
        return Result.success("Antrean parkir", self.queue.display())

    """ View History """
    def show_history(self) -> Result[list[HistoryRecord]]:
        return Result.success("Riwayat parkir", self.history.display())

    """ Statistics """
    def statistics(self) -> Result[dict]:
        occupied = count_occupied(self.slots)
        stats = {
            "total_slots": self.slots.capacity,
            "occupied_slots": occupied,
            "available_slots": self.slots.capacity - occupied,
            "queue_len": self.queue.size,
            "total_served": self.history.size
        }
        return Result.success("Statistik berhasil ditampilkan", stats)
