from core.parking_map import JALUR, LABEL
from core.services import ParkingSystem
from views.diagrams import peta_parkir, pohon_bst


def test_peta_memuat_semua_simpul_dan_jarak() -> None:
    teks = peta_parkir()

    assert teks.startswith("graph LR")
    for nama, label in LABEL.items():
        assert f'{nama}["{label}"]' in teks
    for dari, ke, jarak in JALUR:
        assert f"{dari} ---|{jarak} m| {ke}" in teks


def test_peta_menyorot_jalur_terpilih() -> None:
    teks = peta_parkir(sorot=["GERBANG_UTAMA", "BLOK_A"])

    assert "class GERBANG_UTAMA,BLOK_A jalur" in teks
    # Yang disorot tidak boleh ikut kelas warna asalnya.
    assert "GERBANG_UTAMA" not in teks.split("class ")[-2].split("\n")[0]


def test_pohon_bst_menggambar_cabang_kiri_dan_kanan() -> None:
    system = ParkingSystem()
    for plat in ("D 9 ZZZ", "B 1 AAA", "F 5 MMM"):
        system.registrasi(plat, "x", "MOBIL")

    teks = pohon_bst(system.vehicle_tree.root, lambda v: v.plate)

    assert teks is not None
    assert teks.startswith("graph TD")
    assert 'n0["D 9 ZZZ"]' in teks
    assert "n0 -->|L| n0l" in teks
    assert "n0 -->|R| n0r" in teks


def test_pohon_bst_menandai_cabang_kosong_pada_simpul_satu_anak() -> None:
    system = ParkingSystem()
    for plat in ("B 1 AAA", "C 2 BBB"):  # rantai ke kanan
        system.registrasi(plat, "x", "MOBIL")

    teks = pohon_bst(system.vehicle_tree.root, lambda v: v.plate)

    assert teks is not None
    assert "-.->|L|" in teks  # cabang kiri akar kosong, digambar putus-putus


def test_pohon_bst_kosong_dan_terlalu_besar() -> None:
    assert pohon_bst(None, lambda v: v) is None

    system = ParkingSystem()
    for i in range(40):
        system.registrasi(f"B {i:03d} XYZ", "x", "MOBIL")

    # Di atas batas, gambarnya tidak terbaca jadi sengaja tidak dibuat.
    assert pohon_bst(system.vehicle_tree.root, lambda v: v.plate, batas=31) is None
    assert pohon_bst(system.vehicle_tree.root, lambda v: v.plate, batas=100) is not None


def test_label_diagram_aman_dari_kutip_ganda() -> None:
    system = ParkingSystem()
    system.registrasi('B 1 "X"', "x", "MOBIL")

    teks = pohon_bst(system.vehicle_tree.root, lambda v: v.plate)

    assert teks is not None
    assert '"B 1 \'X\'"' in teks  # kutip ganda diganti petik tunggal
