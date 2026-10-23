from dataclasses import dataclass


@dataclass
class Result[T]:
    """Pembungkus hasil operasi: berhasil/gagal, pesan, dan datanya.

    Dipakai supaya lapisan views tidak perlu menangani exception, cukup
    memeriksa `ok` lalu menampilkan `message`.
    """

    ok: bool
    message: str
    data: T | None = None

    @classmethod
    def success(cls, message: str, data: T | None = None) -> "Result[T]":
        return cls(True, message, data)

    @classmethod
    def fail(cls, message: str) -> "Result[T]":
        return cls(False, message, None)

    def __bool__(self) -> bool:
        return self.ok
