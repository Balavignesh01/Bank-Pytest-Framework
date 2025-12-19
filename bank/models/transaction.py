from dataclasses import dataclass, asdict
from datetime import datetime
import json
from pathlib import Path
from typing import List, Optional

@dataclass
class Transaction:
    tx_id: str
    from_account: Optional[str]    
    to_account: Optional[str]
    amount: float
    timestamp: str
    note: str = ""

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d):
        return cls(**d)

class TransactionStore:
    def __init__(self, path: str | None = None):
        self.path = Path(path or (Path.cwd() / "data" / "transactions.json"))
        self.path.parent.mkdir(parents=True, exist_ok=True)

        if not self.path.exists():
            self._write([])
        self._load()

    def _load(self):
        with self.path.open("r", encoding="utf-8") as f:
            self._data = json.load(f)

    def _write(self, data):
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        self._data = data

    def add_transaction(self, tx: Transaction):
        self._data.append(tx.to_dict())
        self._write(self._data)

    def list_transactions(self) -> List[Transaction]:
        return [Transaction.from_dict(t) for t in self._data]

    def find_by_account(self, account_id: str) -> List[Transaction]:
        return [
            Transaction.from_dict(t)
            for t in self._data
            if t.get("from_account") == account_id or t.get("to_account") == account_id
        ]
