from core.models import Transaction
from core.services import ParkingSystem
from core.structures.stack import UndoStack


def _transaksi(vehicle_id: str) -> Transaction:
    return Transaction(tx_type="CHECK_IN", vehicle_id=vehicle_id, slot_index=0)


def test_tumpukan_kosong() -> None:
    stack = UndoStack()

    assert stack.is_empty()
    assert stack.size == 0
    assert len(stack) == 0
    assert stack.pop() is None
    assert stack.peek() is None
    assert stack.display() == []


def test_lifo_yang_terakhir_masuk_pertama_keluar() -> None:
    stack = UndoStack()
    for i in range(1, 4):
        stack.push(_transaksi(f"V00{i}"))

    assert stack.size == 3
    assert stack.peek().vehicle_id == "V003"
    assert [stack.pop().vehicle_id for _ in range(3)] == ["V003", "V002", "V001"]
    assert stack.is_empty()


def test_peek_tidak_mengambil() -> None:
    stack = UndoStack()
    stack.push(_transaksi("V001"))

    assert stack.peek().vehicle_id == "V001"
    assert stack.peek().vehicle_id == "V001"
    assert stack.size == 1


def test_display_dari_terbaru_ke_terlama() -> None:
    stack = UndoStack()
    for i in range(1, 4):
        stack.push(_transaksi(f"V00{i}"))

    assert [t.vehicle_id for t in stack.display()] == ["V003", "V002", "V001"]


def test_clear_mengosongkan_seluruhnya() -> None:
    stack = UndoStack()
    for i in range(1, 4):
        stack.push(_transaksi(f"V00{i}"))

    stack.clear()

    assert stack.is_empty()
    assert stack.size == 0
    assert stack.pop() is None


def test_undo_sistem_mengikuti_urutan_lifo() -> None:
    system = ParkingSystem(capacity=3)
    for plat in ("B 1 AAA", "B 2 BBB"):
        system.registrasi(plat, "x", "MOBIL")
        system.check_in(plat)

    # Transaksi terakhir adalah check-in B 2 BBB, jadi itu yang dibatalkan.
    assert system.undo_last().ok
    assert system.find("B 2 BBB").status == "REGISTERED"
    assert system.find("B 1 AAA").status == "PARKED"

    assert system.undo_last().ok
    assert system.find("B 1 AAA").status == "REGISTERED"
    assert not system.undo_last().ok  # tumpukan sudah habis
