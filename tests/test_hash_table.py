from core.models import Vehicle
from core.services import ParkingSystem
from core.structures.hash_table import HashTable


def test_dua_kunci_berbeda_tetap_ditemukan_di_bucket_yang_sama() -> None:
    table: HashTable[Vehicle] = HashTable(capacity=1)
    pertama = Vehicle("V001", "B 1234 ABC", "Ani", "MOBIL")
    kedua = Vehicle("V002", "D 9999 XYZ", "Budi", "MOTOR")

    table.put(pertama.plate, pertama)
    table.put(kedua.plate, kedua)

    assert table.chain_length(pertama.plate) == 2
    assert table.get("B 1234 ABC") is pertama
    assert table.get("D 9999 XYZ") is kedua


def test_hash_mengembalikan_objek_yang_sama_dengan_daftar() -> None:
    system = ParkingSystem()
    system.registrasi("B 1234 ABC", "Budi", "MOBIL")

    dari_hash = system.by_plate.get("B 1234 ABC")
    dari_list = system.vehicles.search("B 1234 ABC", by="plate")

    assert dari_hash is dari_list
    system.check_in("B 1234 ABC")
    assert dari_hash is not None
    assert dari_hash.status == "PARKED"
    assert dari_hash.slot_index == 0


def test_pencarian_plat_dan_id_lewat_hash_pemilik_tetap_pertama() -> None:
    system = ParkingSystem()
    system.registrasi("B 1 AAA", "Budi", "MOBIL")
    system.registrasi("B 2 BBB", "Budi", "MOTOR")

    plat = system.search("B 2 BBB")
    identitas = system.search("V001", by="id")
    pemilik = system.search("Budi", by="owner")

    assert plat.ok and plat.data is not None and plat.data.owner == "Budi"
    assert identitas.ok and identitas.data is not None and identitas.data.plate == "B 1 AAA"
    assert pemilik.ok and pemilik.data is not None and pemilik.data.plate == "B 1 AAA"
    assert system.search("Z 000 ZZZ").ok is False
