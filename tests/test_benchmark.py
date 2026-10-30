from core.benchmark import (
    benchmark_bentuk_bst,
    benchmark_cari,
    benchmark_sisip,
    benchmark_urut,
    run_benchmark,
)


def test_benchmark_mengukur_tiap_struktur() -> None:
    sisip = benchmark_sisip(500)
    cari = benchmark_cari(500)

    assert {r["struktur"] for r in sisip} >= {"Hash Table", "Dynamic Array", "Min Heap"}
    assert all(r["detik"] >= 0 for r in sisip)
    assert {r["struktur"] for r in cari} >= {"Hash Table", "BST", "Binary Search"}
    assert all(r["per_operasi_us"] is not None for r in cari)


def test_benchmark_melewati_kuadratik_di_n_besar() -> None:
    kecil = {r["struktur"]: r["detik"] for r in benchmark_urut(500)}
    besar = {r["struktur"]: r["detik"] for r in benchmark_urut(100_000)}

    assert kecil["Insertion Sort"] is not None
    assert besar["Insertion Sort"] is None  # sengaja dilewati, bukan dijalankan
    assert besar["Merge Sort"] is not None


def test_benchmark_menunjukkan_bst_merosot() -> None:
    hasil = benchmark_bentuk_bst(2_000)
    acak = next(r for r in hasil if r["kondisi"] == "Data teracak")
    urut = next(r for r in hasil if r["kondisi"] == "Data sudah terurut")

    assert urut["tinggi"] == urut["n"]  # rantai
    assert acak["tinggi"] < urut["tinggi"]


def test_run_benchmark_lengkap_pada_n_kecil() -> None:
    hasil = run_benchmark(sizes=(100, 1_000))

    assert hasil["sizes"] == [100, 1_000]
    for bagian in ("sisip", "cari", "urut"):
        assert hasil[bagian]
        assert {r["n"] for r in hasil[bagian]} == {100, 1_000}
    assert hasil["bentuk_bst"]
