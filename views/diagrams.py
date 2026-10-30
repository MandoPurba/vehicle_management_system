"""Gambar struktur data sebagai diagram Mermaid."""

from core.parking_map import JALUR, LABEL
from core.structures.bst import BSTNode

# Warna mengikuti palet kategorikal di views/charts.py.
KELAS = """
    classDef gerbang fill:#2a78d6,stroke:#1f5aa3,color:#ffffff,stroke-width:2px
    classDef blok fill:#1baf7a,stroke:#13835b,color:#ffffff,stroke-width:2px
    classDef gedung fill:#eb6834,stroke:#b84d26,color:#ffffff,stroke-width:2px
    classDef jalur fill:#eda100,stroke:#b87d00,color:#1a1a19,stroke-width:3px
    classDef kosong fill:#f2f2f0,stroke:#b8b8b2,color:#52514e,stroke-dasharray:4 3
"""


def _aman(teks: str) -> str:
    """Kutip ganda memutus label Mermaid, jadi diganti petik tunggal."""
    return teks.replace('"', "'")


def peta_parkir(sorot: list[str] | None = None) -> str:
    """Diagram peta parkir: gerbang, blok, gedung, dan jarak tiap jalur.

    Simpul yang namanya ada di `sorot` diberi warna berbeda, dipakai
    untuk menandai jalur hasil Dijkstra.
    """
    sorot = sorot or []
    baris = ["graph LR"]
    for nama, label in LABEL.items():
        baris.append(f'    {nama}["{_aman(label)}"]')
    for dari, ke, jarak in JALUR:
        baris.append(f"    {dari} ---|{jarak} m| {ke}")

    gerbang, blok, gedung = [], [], []
    for nama in LABEL:
        if nama in sorot:
            continue
        if nama.startswith("GERBANG"):
            gerbang.append(nama)
        elif nama.startswith("BLOK"):
            blok.append(nama)
        else:
            gedung.append(nama)

    baris.append(KELAS)
    for kelas, anggota in (("gerbang", gerbang), ("blok", blok), ("gedung", gedung)):
        if anggota:
            baris.append(f"    class {','.join(anggota)} {kelas}")
    if sorot:
        baris.append(f"    class {','.join(sorot)} jalur")
    return "\n".join(baris)


def pohon_bst(root: BSTNode | None, label, batas: int = 31) -> str | None:
    """Diagram percabangan BST: anak kiri dan kanan tiap simpul.

    None kalau pohonnya kosong atau lebih besar dari `batas`, karena di
    atas itu gambarnya tidak lagi terbaca.
    """
    if root is None:
        return None

    simpul: list[tuple[str, BSTNode]] = []
    tumpukan: list[tuple[str, BSTNode]] = [("n0", root)]
    while tumpukan:
        nama, node = tumpukan.pop()
        simpul.append((nama, node))
        if len(simpul) > batas:
            return None
        if node.right is not None:
            tumpukan.append((f"{nama}r", node.right))
        if node.left is not None:
            tumpukan.append((f"{nama}l", node.left))

    baris = ["graph TD"]
    for nama, node in simpul:
        baris.append(f'    {nama}["{_aman(str(label(node.data)))}"]')

    kosong = 0
    for nama, node in simpul:
        for sisi, anak in (("L", node.left), ("R", node.right)):
            if anak is not None:
                baris.append(f"    {nama} -->|{sisi}| {nama}{sisi.lower()}")
            elif node.left is not None or node.right is not None:
                # Hanya digambar kalau simpulnya punya satu anak, supaya
                # terlihat cabang mana yang kosong.
                kosong += 1
                baris.append(f'    kosong{kosong}[" "]')
                baris.append(f"    {nama} -.->|{sisi}| kosong{kosong}")

    baris.append(KELAS)
    baris.append("    class n0 jalur")
    lain = [nama for nama, _ in simpul if nama != "n0"]
    if lain:
        baris.append(f"    class {','.join(lain)} blok")
    if kosong:
        baris.append(f"    class {','.join(f'kosong{i}' for i in range(1, kosong + 1))} kosong")
    return "\n".join(baris)
