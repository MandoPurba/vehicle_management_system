from datetime import datetime, timedelta

from core.models import HistoryRecord, Vehicle
from core.structures.linked_list import ParkingHistory, VehicleList

AWAL = datetime(2026, 11, 1, 8, 0)


def _kendaraan(plate: str, owner: str = "Pemilik") -> Vehicle:
    return Vehicle(f"V-{plate}", plate, owner, "MOBIL")


def _catatan(menit: int) -> HistoryRecord:
    masuk = AWAL + timedelta(minutes=menit)
    return HistoryRecord(f"V{menit}", f"B {menit} XYZ", "A01", masuk, masuk + timedelta(hours=1))


# ---- VehicleList ----

def test_daftar_kosong() -> None:
    daftar = VehicleList()

    assert daftar.is_empty()
    assert daftar.size == 0
    assert len(daftar) == 0
    assert daftar.display() == []
    assert daftar.search("B 1 AAA") is None
    assert daftar.remove("V-apa pun") is None


def test_sisip_menjaga_urutan_masuk() -> None:
    daftar = VehicleList()
    for plat in ("B 3 CCC", "B 1 AAA", "B 2 BBB"):
        daftar.insert(_kendaraan(plat))

    assert [v.plate for v in daftar] == ["B 3 CCC", "B 1 AAA", "B 2 BBB"]
    assert daftar.size == 3


def test_cari_berdasarkan_plat_id_dan_pemilik() -> None:
    daftar = VehicleList()
    daftar.insert(_kendaraan("B 1 AAA", "Ani"))
    daftar.insert(_kendaraan("B 2 BBB", "Budi"))

    assert daftar.search("B 2 BBB", by="plate").owner == "Budi"
    assert daftar.search("V-B 1 AAA", by="id").plate == "B 1 AAA"
    assert daftar.search("Budi", by="owner").plate == "B 2 BBB"
    assert daftar.search("Tidak Ada", by="owner") is None


def test_hapus_dari_kepala_tengah_dan_ekor() -> None:
    def daftar_bertiga() -> VehicleList:
        d = VehicleList()
        for plat in ("B 1 AAA", "B 2 BBB", "B 3 CCC"):
            d.insert(_kendaraan(plat))
        return d

    kepala = daftar_bertiga()
    assert kepala.remove("V-B 1 AAA").plate == "B 1 AAA"
    assert [v.plate for v in kepala] == ["B 2 BBB", "B 3 CCC"]

    tengah = daftar_bertiga()
    assert tengah.remove("V-B 2 BBB").plate == "B 2 BBB"
    assert [v.plate for v in tengah] == ["B 1 AAA", "B 3 CCC"]

    ekor = daftar_bertiga()
    assert ekor.remove("V-B 3 CCC").plate == "B 3 CCC"
    assert [v.plate for v in ekor] == ["B 1 AAA", "B 2 BBB"]
    # Tail harus ikut mundur, jadi sisipan berikutnya tetap di akhir.
    ekor.insert(_kendaraan("B 9 ZZZ"))
    assert [v.plate for v in ekor] == ["B 1 AAA", "B 2 BBB", "B 9 ZZZ"]
    assert ekor.size == 3


def test_hapus_sampai_kosong_lalu_sisip_lagi() -> None:
    daftar = VehicleList()
    daftar.insert(_kendaraan("B 1 AAA"))
    daftar.remove("V-B 1 AAA")

    assert daftar.is_empty()
    daftar.insert(_kendaraan("B 2 BBB"))
    assert [v.plate for v in daftar] == ["B 2 BBB"]


# ---- ParkingHistory (versi linked list, pembanding HistoryTree) ----

def test_riwayat_linked_list_kosong() -> None:
    riwayat = ParkingHistory()

    assert riwayat.size == 0
    assert riwayat.head is None
    assert riwayat.remove_last() is None


def test_riwayat_linked_list_menambah_di_ekor() -> None:
    riwayat = ParkingHistory()
    for menit in (10, 20, 30):
        riwayat.add(_catatan(menit))

    assert riwayat.size == 3
    assert riwayat.head.data.plate == "B 10 XYZ"
    assert riwayat.tail.data.plate == "B 30 XYZ"


def test_riwayat_linked_list_remove_last() -> None:
    riwayat = ParkingHistory()
    for menit in (10, 20):
        riwayat.add(_catatan(menit))

    assert riwayat.remove_last().plate == "B 20 XYZ"
    assert riwayat.size == 1
    assert riwayat.tail.data.plate == "B 10 XYZ"

    assert riwayat.remove_last().plate == "B 10 XYZ"
    assert riwayat.size == 0
    assert riwayat.head is None and riwayat.tail is None


def test_riwayat_linked_list_display_mencetak(capsys) -> None:
    riwayat = ParkingHistory()
    assert riwayat.display() is None
    assert "kosong" in capsys.readouterr().out

    riwayat.add(_catatan(10))
    riwayat.display()
    keluaran = capsys.readouterr().out
    assert "B 10 XYZ" in keluaran
    assert "A01" in keluaran
