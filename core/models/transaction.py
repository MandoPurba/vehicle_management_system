from dataclasses import dataclass, field
from datetime import datetime

from core.models import TxType


@dataclass
class Transaction:
    """Satu entri di UndoStack."""

    tx_type: TxType
    vehicle_id: str
    slot_index: int | None = None
    time: datetime = field(default_factory=datetime.now)
    promoted_id: str | None = None  # kendaraan dari queue yang naik saat CHECK_OUT
