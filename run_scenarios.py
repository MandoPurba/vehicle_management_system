"""Runner skenario fungsional dan teknis untuk Smart Parking (UAS Data Structure).

Mengeksekusi skenario 1-24 secara otomatis dan mencetak tabel hasil PASS/FAIL.
"""

from datetime import datetime, timedelta
import sys

from core.algorithms.recursion import count_occupied_recursive, sum_costs_recursive
from core.benchmark import run_benchmark
from core.models import HistoryRecord, Priority, VehicleType
from core.parking_map import build_map, slot_terdekat
from core.services import ParkingSystem
from core.structures.bst import VehicleTree
from core.structures.graph import Graph
from core.structures.hash_table import HashTable


def run_all() -> list[tuple[int, str, str, str, str]]:
    results = []

    # System reset
    system = ParkingSystem(capacity=5)

    # 1. Registrasi data valid
    r1 = system.registrasi("B 1001 AA", "Andi", "MOBIL", "UMUM")
    v1 = system.by_plate.get("B 1001 AA")
    status1 = "PASS" if r1.ok and v1 and v1.vehicle_id == "V001" and v1.status == "REGISTERED" else "FAIL"
    results.append((1, "Fungsional", "Registrasi data valid", "ID V001, REGISTERED", status1))

    # 2. Registrasi plat duplikat
    r2 = system.registrasi("B 1001 AA", "Budi", "MOBIL", "UMUM")
    status2 = "PASS" if not r2.ok and "sudah terdaftar" in r2.message.lower() else "FAIL"
    results.append((2, "Fungsional", "Registrasi plat duplikat", "Ditolak: sudah terdaftar", status2))

    # 3. Registrasi field kosong
    r3 = system.registrasi("", "Andi", "MOBIL", "UMUM")
    status3 = "PASS" if not r3.ok and "semua field" in r3.message.lower() else "FAIL"
    results.append((3, "Fungsional", "Registrasi field kosong", "Ditolak: semua field harus diisi", status3))

    # Daftarkan kendaraan tambahan untuk skenario berikutnya
    system.registrasi("B 1002 AB", "Budi", "MOBIL", "UMUM")
    system.registrasi("B 1003 AC", "Citra", "MOTOR", "UMUM")
    system.registrasi("B 1004 AD", "Dewi", "MOBIL", "UMUM")
    system.registrasi("B 1005 AE", "Eko", "MOTOR", "UMUM")

    # 4. Check-in sampai penuh (5 kendaraan)
    for plat in ("B 1001 AA", "B 1002 AB", "B 1003 AC", "B 1004 AD", "B 1005 AE"):
        system.check_in(plat)
    stats4 = system.statistics().data or {}
    status4 = "PASS" if stats4.get("occupied_slots") == 5 and stats4.get("available_slots") == 0 else "FAIL"
    results.append((4, "Dynamic Array", "Check-in sampai penuh (5 slot)", "A01-A05 terisi, sisa 0", status4))

    # 5. Check-in kendaraan sedang parkir
    r5 = system.check_in("B 1001 AA")
    status5 = "PASS" if not r5.ok and "sudah parkir" in r5.message.lower() else "FAIL"
    results.append((5, "Fungsional", "Check-in kendaraan sedang parkir", "Ditolak: sudah parkir", status5))

    # 6. Check-in belum terdaftar
    r6 = system.check_in("Z 9 Z")
    status6 = "PASS" if not r6.ok and "tidak ditemukan" in r6.message.lower() else "FAIL"
    results.append((6, "Fungsional", "Check-in belum terdaftar", "Ditolak: tidak ditemukan", status6))

    # Registrasi untuk antrean prioritas
    system.registrasi("B 2001 UM", "Fajar", "MOBIL", "UMUM")
    system.registrasi("B 2002 DS", "Pak Dosen", "MOBIL", "DOSEN")
    system.registrasi("B 2003 DB", "Ibu Difabel", "MOBIL", "DISABILITAS")

    # 7. Antrean prioritas saat penuh
    system.check_in("B 2001 UM")
    system.check_in("B 2002 DS")
    system.check_in("B 2003 DB")
    q_items = system.queue.display()
    q_plates = [v.plate for v in q_items]
    status7 = "PASS" if q_plates == ["B 2003 DB", "B 2002 DS", "B 2001 UM"] else "FAIL"
    results.append((7, "Min Heap", "Antrean prioritas (DISABILITAS > DOSEN > UMUM)", "DISABILITAS, DOSEN, UMUM", status7))

    # 8. Check-out dengan promosi antrean
    r8 = system.check_out("B 1002 AB")
    promoted = system.by_plate.get("B 2003 DB")
    status8 = "PASS" if r8.ok and promoted and promoted.status == "PARKED" and promoted.slot_index == 1 else "FAIL"
    results.append((8, "Min Heap", "Check-out dengan promosi prioritas", "B 2003 DB naik ke A02", status8))

    # 9. Pencarian data ada
    s_plate = system.search("plate", "B 1001 AA")
    s_owner = system.search("owner", "Andi")
    status9 = "PASS" if s_plate.ok and s_owner.ok else "FAIL"
    results.append((9, "Hash Table", "Pencarian plat dan pemilik (ada)", "Ditemukan", status9))

    # 10. Pencarian data tidak ada
    s_none = system.search("plate", "ZZ 9999 XX")
    status10 = "PASS" if not s_none.ok else "FAIL"
    results.append((10, "Hash Table", "Pencarian plat (tidak ada)", "Ditolak: tidak ditemukan", status10))

    # 11. Statistik sistem
    st11 = system.statistics().data or {}
    status11 = "PASS" if st11.get("occupied_slots") == 5 and st11.get("queue_length") == 2 and st11.get("served_count") == 1 else "FAIL"
    results.append((11, "Fungsional", "Statistik sistem setelah skenario 8", "terisi 5, antre 2, riwayat 1", status11))

    # 12. Undo check-out (LIFO)
    u12 = system.undo_last()
    v_asal = system.by_plate.get("B 1002 AB")
    v_prom = system.by_plate.get("B 2003 DB")
    hist_len = len(system.history.display())
    status12 = "PASS" if u12.ok and v_asal.status == "PARKED" and v_asal.slot_index == 1 and v_prom.status == "WAITING" and hist_len == 0 else "FAIL"
    results.append((12, "UndoStack", "Undo check-out (kembalikan asal & demote)", "Asal parkir lagi, promosi antre lagi", status12))

    # 13. Undo enqueue
    u13 = system.undo_last()
    v_last_q = system.by_plate.get("B 2003 DB")
    status13 = "PASS" if u13.ok and v_last_q.status == "REGISTERED" else "FAIL"
    results.append((13, "UndoStack", "Undo enqueue", "Kendaraan terakhir antre dibatalkan", status13))

    # 14. Undo sampai stack kosong
    while not system.undo.is_empty():
        system.undo_last()
    u14 = system.undo_last()
    status14 = "PASS" if not u14.ok and "tidak ada transaksi" in u14.message.lower() else "FAIL"
    results.append((14, "UndoStack", "Undo saat stack kosong", "Ditolak: tidak ada transaksi", status14))

    # 15. Recursion slot kosong
    sys_empty = ParkingSystem(capacity=5)
    rec15 = count_occupied_recursive(sys_empty.slots)
    status15 = "PASS" if rec15 == 0 else "FAIL"
    results.append((15, "Recursion", "Hitung slot terisi rekursif (kosong)", "count_occupied = 0", status15))

    # 16. Persistence simpan & muat
    from core.persistence import load_state, save_state
    save_state(system)
    sys_loaded = load_state()
    status16 = "PASS" if sys_loaded.slots.capacity == system.slots.capacity and len(sys_loaded.vehicles.display()) == len(system.vehicles.display()) else "FAIL"
    results.append((16, "Persistence", "Simpan dan muat state.json", "Kapasitas & kendaraan identik", status16))

    # 17. Resize slot (memperbesar)
    sys_res = ParkingSystem(capacity=2)
    sys_res.registrasi("B 1 A", "A", "MOBIL", "UMUM")
    sys_res.registrasi("B 2 B", "B", "MOBIL", "UMUM")
    sys_res.registrasi("B 3 C", "C", "MOBIL", "UMUM")
    sys_res.check_in("B 1 A")
    sys_res.check_in("B 2 B")
    sys_res.check_in("B 3 C")  # antre
    res17 = sys_res.resize_slots(4)
    v_c = sys_res.by_plate.get("B 3 C")
    status17 = "PASS" if res17.ok and sys_res.slots.capacity == 4 and v_c.status == "PARKED" else "FAIL"
    results.append((17, "Dynamic Array", "Memperbesar kapasitas slot (2 -> 4)", "Kapasitas 4, antrean naik ke slot baru", status17))

    # 18. Resize slot (memperkecil slot terisi)
    res18 = sys_res.resize_slots(2)  # slot indeks 2 terisi oleh B 3 C
    status18 = "PASS" if not res18.ok and "masih terisi" in res18.message.lower() else "FAIL"
    results.append((18, "Dynamic Array", "Memperkecil slot terisi (ditolak)", "Ditolak: slot ekor masih terisi", status18))

    # 19. Recursion pada 1.200 riwayat (Batas kedalaman rekursi Python)
    awal = datetime(2026, 10, 31, 8, 0, 0)
    records_1200 = [
        HistoryRecord(f"V{i:04d}", f"B {i} XX", "A01", awal, awal + timedelta(hours=1), "MOBIL")
        for i in range(1200)
    ]
    try:
        sum_costs_recursive(records_1200)
        status19 = "PASS"
    except RecursionError:
        status19 = "FAIL (RecursionError)"
    except Exception as e:
        status19 = f"FAIL ({type(e).__name__})"
    results.append((19, "Recursion", "Recursion pada 1.200 riwayat", "Total biaya tanpa batas recursion", status19))

    # 20. Hash Table Collision handling
    ht = HashTable(capacity=1, auto_rehash=False)
    ht.put("kunci1", "val1")
    ht.put("kunci2", "val2")
    ht.put("kunci3", "val3")
    stats_ht = ht.stats()
    status20 = "PASS" if stats_ht["collision_buckets"] > 0 and ht.get("kunci1") == "val1" and ht.get("kunci2") == "val2" else "FAIL"
    results.append((20, "Hash Table", "Collision handling (chaining tanpa rehash)", "Data tetap ketemu meski tabrakan", status20))

    # 21. BST Traversal In-Order
    vt = VehicleTree("plate")
    for plat in ("B 9999 ZZ", "B 1111 AA", "B 5555 MM"):
        system.registrasi(plat, "Owner", "MOBIL", "UMUM")
        v = system.by_plate.get(plat)
        vt.add(v)
    inorder_plates = [v.plate for v in vt.in_order()]
    status21 = "PASS" if inorder_plates == ["B 1111 AA", "B 5555 MM", "B 9999 ZZ"] else "FAIL"
    results.append((21, "BST", "Traversal in-order VehicleTree", "Terurut menaik menurut plat", status21))

    # 22. Graph Dijkstra Shortest Path
    peta = build_map()
    jalur22, dist22 = peta.shortest_path("GERBANG_UTAMA", "BLOK_A")
    status22 = "PASS" if dist22 == 50 and jalur22 == ["GERBANG_UTAMA", "BLOK_A"] else "FAIL"
    results.append((22, "Graph", "Dijkstra shortest path", "Rute & jarak terpendek akurat", status22))

    # 23. Graph Disconnected Node
    g_disc = Graph()
    g_disc.add_node("A")
    g_disc.add_node("B")
    jalur23, dist23 = g_disc.shortest_path("A", "B")
    status23 = "PASS" if dist23 == float("inf") and jalur23 == [] else "FAIL"
    results.append((23, "Graph", "Titik tidak terhubung", "Jarak inf, rute kosong, tidak crash", status23))

    # 24. Performa Benchmark 100.000 elemen
    bench = run_benchmark([1000, 10000, 100000])
    status24 = "PASS" if bench["cari"]["Hash Table"][100000] > 0 and bench["urut"]["Merge Sort"][100000] > 0 else "FAIL"
    results.append((24, "Benchmark", "Benchmark sampai n=100.000", "Selesai tanpa crash, data terukur", status24))

    return results


def main() -> None:
    print("=" * 80)
    print("SMART PARKING & VEHICLE MANAGEMENT SYSTEM - SKENARIO UJI LENGKAP")
    print("Cakrawala University · Data Structure DS01 · Kelompok 1")
    print("=" * 80)
    print(f"{'No':<3} | {'Kategori':<15} | {'Skenario':<35} | {'Hasil':<20}")
    print("-" * 80)

    results = run_all()
    lulus = 0
    gagal = 0
    for no, kat, skenario, exp, hasil in results:
        print(f"{no:<3} | {kat:<15} | {skenario:<35} | {hasil:<20}")
        if hasil == "PASS":
            lulus += 1
        else:
            gagal += 1

    print("-" * 80)
    print(f"Total: {len(results)} skenario | Lulus: {lulus} | Gagal: {gagal}")
    print("Catatan: Skenario 19 gagal (RecursionError) sesuai keterbatasan desain yang dianalisis.")
    print("=" * 80)


if __name__ == "__main__":
    main()
