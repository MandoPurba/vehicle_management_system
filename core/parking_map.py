"""Peta area parkir kampus: gerbang, blok parkir, dan gedung tujuan."""

from core.models import slot_code
from core.structures.dynamic_array import ParkingSlots
from core.structures.graph import INFINITE, Graph

GERBANG = ("GERBANG_UTAMA", "GERBANG_TIMUR")
BLOK = ("BLOK_A", "BLOK_B", "BLOK_C")
GEDUNG = ("GD_REKTORAT", "GD_FTI", "GD_PERPUS")

LABEL: dict[str, str] = {
    "GERBANG_UTAMA": "Gerbang Utama",
    "GERBANG_TIMUR": "Gerbang Timur",
    "BLOK_A": "Blok A",
    "BLOK_B": "Blok B",
    "BLOK_C": "Blok C",
    "GD_REKTORAT": "Gedung Rektorat",
    "GD_FTI": "Gedung FTI",
    "GD_PERPUS": "Perpustakaan",
}

# (dari, ke, jarak meter)
JALUR: tuple[tuple[str, str, int], ...] = (
    ("GERBANG_UTAMA", "BLOK_A", 50),
    ("GERBANG_UTAMA", "BLOK_B", 120),
    ("BLOK_A", "BLOK_B", 60),
    ("BLOK_B", "BLOK_C", 70),
    ("GERBANG_TIMUR", "BLOK_C", 40),
    ("BLOK_A", "GD_REKTORAT", 80),
    ("BLOK_B", "GD_FTI", 55),
    ("BLOK_C", "GD_PERPUS", 65),
    ("GD_REKTORAT", "GD_FTI", 90),
    ("GERBANG_TIMUR", "GD_PERPUS", 100),
)


def build_map() -> Graph:
    """Bangun graf peta parkir kampus."""
    graph = Graph()
    for nama in GERBANG:
        graph.add_node(nama, "GERBANG")
    for nama in BLOK:
        graph.add_node(nama, "BLOK")
    for nama in GEDUNG:
        graph.add_node(nama, "GEDUNG")
    for dari, ke, jarak in JALUR:
        graph.add_edge(dari, ke, jarak)
    return graph


def blok_untuk_slot(index: int, capacity: int) -> str:
    """Blok yang menampung slot ke-`index`.

    Slot dibagi rata ke tiga blok secara berurutan, jadi pembagiannya
    ikut menyesuaikan ketika jumlah slot diubah.
    """
    if capacity <= 0:
        return BLOK[0]
    per_blok = max(1, -(-capacity // len(BLOK)))  # pembulatan ke atas
    return BLOK[min(index // per_blok, len(BLOK) - 1)]


def slot_per_blok(capacity: int) -> dict[str, list[int]]:
    """Daftar indeks slot untuk tiap blok."""
    hasil: dict[str, list[int]] = {nama: [] for nama in BLOK}
    for index in range(capacity):
        hasil[blok_untuk_slot(index, capacity)].append(index)
    return hasil


def slot_kosong_per_blok(slots: ParkingSlots) -> dict[str, list[int]]:
    """Indeks slot kosong untuk tiap blok."""
    hasil: dict[str, list[int]] = {nama: [] for nama in BLOK}
    for index in range(slots.capacity):
        if slots.get(index) is None:
            hasil[blok_untuk_slot(index, slots.capacity)].append(index)
    return hasil


def slot_terdekat(graph: Graph, slots: ParkingSlots, dari: str) -> dict:
    """Slot kosong terdekat dari sebuah gerbang atau gedung.

    Jarak tiap blok dihitung sekali dengan Dijkstra, lalu blok yang punya
    slot kosong dan jaraknya terkecil yang dipilih.
    """
    jarak, _ = graph.dijkstra(dari)
    kosong = slot_kosong_per_blok(slots)

    terbaik: tuple[float, str, int] | None = None
    for nama in BLOK:
        if not kosong[nama]:
            continue
        d = jarak.get(nama, INFINITE)
        if d == INFINITE:
            continue
        calon = (d, nama, kosong[nama][0])
        if terbaik is None or calon[0] < terbaik[0]:
            terbaik = calon

    if terbaik is None:
        return {
            "found": False,
            "from": dari,
            "message": "Tidak ada slot kosong yang bisa dicapai dari titik ini",
        }

    d, blok, index = terbaik
    jalur, total = graph.shortest_path(dari, blok)
    return {
        "found": True,
        "from": dari,
        "block": blok,
        "slot_index": index,
        "slot_code": slot_code(index),
        "distance": int(d),
        "path": jalur,
        "path_distance": int(total),
        "free_in_block": len(kosong[blok]),
        "message": (
            f"{slot_code(index)} di {LABEL[blok]}, {int(d)} m dari {LABEL.get(dari, dari)}"
        ),
    }
