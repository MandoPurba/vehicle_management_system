from datetime import datetime, timedelta

from core.models import HistoryRecord
from core.structures.bst import BST, HistoryTree

AWAL = datetime(2026, 10, 30, 8, 0, 0)


def _catatan(menit: int, vehicle_id: str = "V001") -> HistoryRecord:
    """Satu HistoryRecord yang keluar pada menit ke-`menit`."""
    masuk = AWAL + timedelta(minutes=menit)
    return HistoryRecord(vehicle_id, f"B {menit} XYZ", "A01", masuk, masuk + timedelta(minutes=30))


# ---- BST sebagai struktur ----

def test_in_order_mengurutkan_tanpa_sorting() -> None:
    tree = BST()
    for angka in (50, 30, 70, 20, 40, 60, 80):
        tree.insert(angka)

    assert tree.in_order() == [20, 30, 40, 50, 60, 70, 80]
    assert len(tree) == 7
    assert tree.min() == 20
    assert tree.max() == 80


def test_invarian_kiri_kecil_kanan_besar() -> None:
    tree = BST()
    for angka in (50, 30, 70, 20, 40):
        tree.insert(angka)

    assert tree.root is not None
    assert tree.root.data == 50
    assert tree.root.left is not None and tree.root.left.data == 30
    assert tree.root.right is not None and tree.root.right.data == 70
    assert tree.root.left.left is not None and tree.root.left.left.data == 20
    assert tree.root.left.right is not None and tree.root.left.right.data == 40


def test_search_menemukan_yang_ada_dan_menolak_yang_tidak() -> None:
    tree = BST()
    for angka in (50, 30, 70):
        tree.insert(angka)

    assert tree.search(30) == 30
    assert tree.search(70) == 70
    assert tree.search(99) is None
    assert BST().search(1) is None


def test_kunci_sama_ditimpa_bukan_digandakan() -> None:
    tree = BST(key=lambda pasangan: pasangan[0])
    tree.insert(("a", 1))
    tree.insert(("b", 2))
    tree.insert(("a", 99))

    assert len(tree) == 2
    assert tree.search("a") == ("a", 99)


def test_hapus_daun_satu_anak_dan_dua_anak() -> None:
    def pohon() -> BST:
        tree = BST()
        for angka in (50, 30, 70, 20, 40, 60, 80, 65):
            tree.insert(angka)
        return tree

    # Kasus 1: daun.
    tree = pohon()
    assert tree.remove(20) == 20
    assert tree.in_order() == [30, 40, 50, 60, 65, 70, 80]
    assert len(tree) == 7

    # Kasus 2: satu anak (60 hanya punya anak kanan 65).
    tree = pohon()
    assert tree.remove(60) == 60
    assert tree.in_order() == [20, 30, 40, 50, 65, 70, 80]

    # Kasus 3: dua anak. 70 digantikan penerusnya, 80.
    tree = pohon()
    assert tree.remove(70) == 70
    assert tree.in_order() == [20, 30, 40, 50, 60, 65, 80]
    assert tree.root is not None and tree.root.right is not None
    assert tree.root.right.data == 80

    # Kasus 3 pada akar.
    tree = pohon()
    assert tree.remove(50) == 50
    assert tree.in_order() == [20, 30, 40, 60, 65, 70, 80]
    assert tree.root is not None and tree.root.data == 60


def test_hapus_kunci_yang_tidak_ada_tidak_mengubah_apa_pun() -> None:
    tree = BST()
    for angka in (50, 30, 70):
        tree.insert(angka)

    assert tree.remove(99) is None
    assert tree.in_order() == [30, 50, 70]
    assert len(tree) == 3


def test_hapus_sampai_kosong() -> None:
    tree = BST()
    for angka in (50, 30, 70):
        tree.insert(angka)
    for angka in (50, 30, 70):
        tree.remove(angka)

    assert tree.is_empty()
    assert tree.root is None
    assert len(tree) == 0
    assert tree.height() == 0
    assert tree.remove_max() is None


def test_between_hanya_mengembalikan_rentangnya() -> None:
    tree = BST()
    for angka in (50, 30, 70, 20, 40, 60, 80):
        tree.insert(angka)

    assert tree.between(35, 65) == [40, 50, 60]
    assert tree.between(20, 80) == [20, 30, 40, 50, 60, 70, 80]
    assert tree.between(81, 90) == []
    assert tree.between(40, 40) == [40]


def test_tinggi_pohon_seimbang_dan_yang_merosot() -> None:
    seimbang = BST()
    for angka in (50, 30, 70, 20, 40, 60, 80):
        seimbang.insert(angka)
    assert seimbang.height() == 3  # 7 simpul, log2(7) dibulatkan ke atas

    # Data yang sudah terurut membuat tiap simpul jatuh ke kanan terus:
    # pohonnya jadi rantai, tinggi = jumlah simpul.
    merosot = BST()
    for angka in range(1, 8):
        merosot.insert(angka)
    assert merosot.height() == 7
    assert merosot.in_order() == [1, 2, 3, 4, 5, 6, 7]


def test_pre_order_menyalin_bentuk_pohon() -> None:
    tree = BST()
    for angka in (50, 30, 70, 20, 40):
        tree.insert(angka)

    salinan = BST()
    for angka in tree.pre_order():
        salinan.insert(angka)

    assert salinan.pre_order() == tree.pre_order()
    assert salinan.height() == tree.height()


# ---- HistoryTree sebagai riwayat parkir ----

def test_riwayat_terurut_waktu_meski_dicatat_acak() -> None:
    history = HistoryTree()
    for menit in (30, 10, 50, 20, 40):
        history.add(_catatan(menit))

    plat = [r.plate for r in history.display()]
    assert plat == ["B 10 XYZ", "B 20 XYZ", "B 30 XYZ", "B 40 XYZ", "B 50 XYZ"]
    assert history.size == 5
    assert list(history) == history.display()


def test_remove_last_membuang_catatan_terbaru() -> None:
    history = HistoryTree()
    for menit in (10, 30, 20):
        history.add(_catatan(menit))

    terbuang = history.remove_last()

    assert terbuang is not None and terbuang.plate == "B 30 XYZ"
    assert [r.plate for r in history] == ["B 10 XYZ", "B 20 XYZ"]
    assert history.size == 2
    assert HistoryTree().remove_last() is None


def test_waktu_keluar_sama_tidak_saling_menimpa() -> None:
    history = HistoryTree()
    bersamaan = _catatan(10, "V001")
    kembar = HistoryRecord(
        "V002", "B 999 ZZZ", "A02", bersamaan.entry_time, bersamaan.exit_time
    )

    history.add(bersamaan)
    history.add(kembar)

    assert history.size == 2
    assert {r.vehicle_id for r in history} == {"V001", "V002"}


def test_between_menjaring_rentang_waktu() -> None:
    history = HistoryTree()
    for menit in (0, 10, 20, 30, 40):
        history.add(_catatan(menit, f"V{menit:03d}"))

    # Catatan menit ke-m keluar pada AWAL + m + 30 menit.
    hasil = history.between(AWAL + timedelta(minutes=40), AWAL + timedelta(minutes=60))

    assert [r.plate for r in hasil] == ["B 10 XYZ", "B 20 XYZ", "B 30 XYZ"]
    assert history.between(AWAL, AWAL + timedelta(minutes=5)) == []


def test_first_last_dan_search() -> None:
    history = HistoryTree()
    for menit in (20, 10, 30):
        history.add(_catatan(menit, f"V{menit:03d}"))

    pertama = history.first()
    terakhir = history.last()

    assert pertama is not None and pertama.plate == "B 10 XYZ"
    assert terakhir is not None and terakhir.plate == "B 30 XYZ"
    assert history.search(terakhir.exit_time, "V030") is terakhir
    assert history.search(terakhir.exit_time, "V999") is None


def test_antarmuka_sama_dengan_parking_history() -> None:
    """HistoryTree harus bisa menggantikan ParkingHistory di ParkingSystem."""
    from core.structures.linked_list import ParkingHistory

    dipakai_parking_system = ("add", "remove_last", "size", "display")
    for nama in dipakai_parking_system:
        assert hasattr(ParkingHistory(), nama)
        assert hasattr(HistoryTree(), nama)


# ---- HistoryTree terpasang di ParkingSystem ----

def test_show_history_mengembalikan_daftar_bukan_none() -> None:
    """ParkingHistory.display() mencetak ke stdout dan mengembalikan None,
    sehingga show_history().data selalu None. HistoryTree memperbaikinya."""
    from core.services import ParkingSystem

    system = ParkingSystem(capacity=2)
    for plat in ("B 1 AAA", "B 2 BBB"):
        system.registrasi(plat, "Ani", "MOBIL")
        system.check_in(plat)
    system.check_out("B 1 AAA")

    hasil = system.show_history()

    assert hasil.ok
    assert hasil.data is not None
    assert [r.plate for r in hasil.data] == ["B 1 AAA"]


def test_riwayat_sistem_urut_waktu_dan_undo_membuang_yang_terbaru() -> None:
    from core.services import ParkingSystem

    system = ParkingSystem(capacity=3)
    for plat in ("B 1 AAA", "B 2 BBB", "B 3 CCC"):
        system.registrasi(plat, "Ani", "MOBIL")
        system.check_in(plat)
    system.check_out("B 1 AAA")
    system.check_out("B 2 BBB")
    system.check_out("B 3 CCC")

    assert [r.plate for r in system.history] == ["B 1 AAA", "B 2 BBB", "B 3 CCC"]
    assert system.statistics().data is not None
    assert system.statistics().data["total_served"] == 3

    assert system.undo_last().ok  # undo check-out B 3 CCC

    assert [r.plate for r in system.history] == ["B 1 AAA", "B 2 BBB"]
    kembali = system.find("B 3 CCC")
    assert kembali is not None and kembali.status == "PARKED"


def test_riwayat_bertahan_lewat_simpan_muat(tmp_path) -> None:
    from core.persistence import load_state, save_state
    from core.services import ParkingSystem

    system = ParkingSystem(capacity=2)
    for plat in ("B 1 AAA", "B 2 BBB"):
        system.registrasi(plat, "Ani", "MOBIL")
        system.check_in(plat)
    system.check_out("B 1 AAA")
    system.check_out("B 2 BBB")

    path = tmp_path / "state.json"
    save_state(system, path)
    dimuat = load_state(path)

    assert [r.plate for r in dimuat.history] == ["B 1 AAA", "B 2 BBB"]
    assert dimuat.history.size == 2
    assert isinstance(dimuat.history.display(), list)


# ---- Traversal lengkap & VehicleTree ----

def test_postorder_mengeluarkan_anak_sebelum_induk() -> None:
    tree = BST()
    for angka in (50, 30, 70, 20, 40, 60, 80):
        tree.insert(angka)

    assert tree.post_order() == [20, 40, 30, 60, 80, 70, 50]
    assert tree.pre_order() == [50, 30, 20, 40, 70, 60, 80]
    assert tree.in_order() == [20, 30, 40, 50, 60, 70, 80]
    assert tree.level_order() == [50, 30, 70, 20, 40, 60, 80]
    assert tree.post_order()[-1] == 50  # akar selalu terakhir
    assert BST().post_order() == []


def test_traversal_iteratif_tahan_pohon_rantai() -> None:
    """Versi rekursif patah di sini karena batas ~1000 frame Python."""
    rantai = BST()
    for i in range(3_000):
        rantai.insert(i)

    assert rantai.height() == 3_000
    assert rantai.in_order() == list(range(3_000))
    assert rantai.pre_order()[0] == 0
    assert rantai.post_order()[-1] == 0
    assert rantai.remove(1_500) == 1_500
    assert len(rantai) == 2_999


def test_vehicle_tree_urut_plat_dan_id() -> None:
    from core.models import Vehicle
    from core.structures.bst import VehicleTree

    kendaraan = [
        Vehicle("V003", "B 1 AAA", "Ani", "MOBIL"),
        Vehicle("V001", "D 9 ZZZ", "Budi", "MOTOR"),
        Vehicle("V002", "C 5 MMM", "Cici", "MOBIL"),
    ]

    per_plat = VehicleTree("plate")
    per_id = VehicleTree("id")
    for v in kendaraan:
        per_plat.add(v)
        per_id.add(v)

    assert [v.plate for v in per_plat.in_order()] == ["B 1 AAA", "C 5 MMM", "D 9 ZZZ"]
    assert [v.vehicle_id for v in per_id.in_order()] == ["V001", "V002", "V003"]
    assert per_plat.search("C 5 MMM") is kendaraan[2]
    assert per_plat.search("Z 0 ZZZ") is None
    assert per_plat.size == 3

    traversal = per_plat.traversals()
    assert set(traversal) == {"inorder", "preorder", "postorder"}
    assert len(traversal["postorder"]) == 3
    assert per_plat.remove("C 5 MMM") is kendaraan[2]
    assert per_plat.size == 2


def test_pohon_kendaraan_terisi_dari_registrasi() -> None:
    from core.services import ParkingSystem

    system = ParkingSystem()
    for plat in ("D 9 ZZZ", "B 1 AAA", "C 5 MMM"):
        system.registrasi(plat, "x", "MOBIL")

    hasil = system.sorted_vehicles("plate")
    assert [v.plate for v in hasil.data] == ["B 1 AAA", "C 5 MMM", "D 9 ZZZ"]

    traversal = system.vehicle_traversals("id").data
    assert [v.vehicle_id for v in traversal["inorder"]] == ["V001", "V002", "V003"]
    assert traversal["height"] >= 1
    assert traversal["order_by"] == "id"
