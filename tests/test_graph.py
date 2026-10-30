from core.parking_map import blok_untuk_slot, build_map, slot_per_blok, slot_terdekat
from core.services import ParkingSystem
from core.structures.graph import INFINITE, Graph


def _graf_kecil() -> Graph:
    g = Graph()
    g.add_edge("A", "B", 1)
    g.add_edge("B", "C", 1)
    g.add_edge("A", "C", 5)
    g.add_edge("C", "D", 2)
    return g


def test_bangun_graf_dan_ketetanggaan() -> None:
    g = _graf_kecil()

    assert g.node_count == 4
    assert g.edge_count == 4
    assert sorted(t for t, _ in g.neighbors("A")) == ["B", "C"]
    assert g.has_node("A") and not g.has_node("Z")


def test_node_tidak_terduplikasi() -> None:
    g = Graph()
    g.add_node("A", "GERBANG")
    g.add_node("A", "GERBANG")

    assert g.node_count == 1
    assert g.kind_of("A") == "GERBANG"


def test_bfs_dan_dfs_mengunjungi_semua_simpul() -> None:
    g = _graf_kecil()

    bfs, dfs = g.bfs("A"), g.dfs("A")

    assert sorted(bfs) == sorted(dfs) == ["A", "B", "C", "D"]
    assert bfs[0] == dfs[0] == "A"
    assert bfs.index("B") < bfs.index("D")  # melebar: tetangga langsung dulu
    assert g.bfs("Z") == [] and g.dfs("Z") == []


def test_dijkstra_memilih_jalur_termurah_bukan_terpendek_simpul() -> None:
    g = _graf_kecil()

    jalur, jarak = g.shortest_path("A", "C")

    # A-C langsung berbobot 5, lewat B hanya 2.
    assert jalur == ["A", "B", "C"]
    assert jarak == 2
    assert g.bfs_path("A", "C") == ["A", "C"]  # BFS tidak melihat bobot


def test_dijkstra_pada_simpul_terpisah() -> None:
    g = _graf_kecil()
    g.add_node("TERPISAH")

    jarak, _ = g.dijkstra("A")

    assert jarak["TERPISAH"] == INFINITE
    assert g.shortest_path("A", "TERPISAH") == ([], INFINITE)
    assert g.shortest_path("A", "Z") == ([], INFINITE)
    assert g.bfs_path("A", "A") == ["A"]


def test_peta_kampus_lengkap() -> None:
    g = build_map()

    assert g.node_count == 8
    assert g.edge_count == 10
    assert len(g.bfs("GERBANG_UTAMA")) == 8  # semua titik terjangkau
    jalur, jarak = g.shortest_path("GERBANG_UTAMA", "GD_PERPUS")
    assert jalur[0] == "GERBANG_UTAMA" and jalur[-1] == "GD_PERPUS"
    assert jarak == 245


def test_pembagian_slot_ke_blok_ikut_kapasitas() -> None:
    assert slot_per_blok(9) == {
        "BLOK_A": [0, 1, 2],
        "BLOK_B": [3, 4, 5],
        "BLOK_C": [6, 7, 8],
    }
    assert blok_untuk_slot(0, 9) == "BLOK_A"
    assert blok_untuk_slot(8, 9) == "BLOK_C"
    # Kapasitas kecil: semua slot masih harus dapat blok yang sah.
    for capacity in range(1, 13):
        for i in range(capacity):
            assert blok_untuk_slot(i, capacity) in slot_per_blok(capacity)


def test_slot_terdekat_pindah_blok_saat_blok_dekat_penuh() -> None:
    g = build_map()
    system = ParkingSystem(capacity=9)

    pertama = slot_terdekat(g, system.slots, "GERBANG_UTAMA")
    assert pertama["found"] and pertama["block"] == "BLOK_A"
    assert pertama["slot_code"] == "A01"

    for plat in ("B 1 A", "B 2 B", "B 3 C"):
        system.registrasi(plat, "x", "MOBIL")
        system.check_in(plat)

    kedua = slot_terdekat(g, system.slots, "GERBANG_UTAMA")
    assert kedua["found"] and kedua["block"] == "BLOK_B"
    assert kedua["distance"] > pertama["distance"]
    assert kedua["path"][0] == "GERBANG_UTAMA"


def test_slot_terdekat_saat_parkir_penuh() -> None:
    g = build_map()
    system = ParkingSystem(capacity=2)
    for plat in ("B 1 A", "B 2 B"):
        system.registrasi(plat, "x", "MOBIL")
        system.check_in(plat)

    hasil = slot_terdekat(g, system.slots, "GERBANG_UTAMA")

    assert not hasil["found"]
    assert "Tidak ada slot kosong" in hasil["message"]
