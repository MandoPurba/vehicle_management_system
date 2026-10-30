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
