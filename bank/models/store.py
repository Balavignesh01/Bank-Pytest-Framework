import os
import json
from pathlib import Path
from typing import Dict, Optional, List
from .account import Account
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
ACCOUNTS_FILE = DATA_DIR / "accounts.json"
class AccountStore:
    def __init__(self, path: Optional[str] = None):
        env_path = os.getenv("ACCOUNTS_JSON_PATH")
        if path:
            self.path = Path(path)
        elif env_path:
            self.path = Path(env_path)
        else:
            self.path = ACCOUNTS_FILE
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write_raw({})
        self._load()
    def _write_raw(self, data: Dict[str, dict]) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _load(self) -> None:
        with open(self.path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        self._accounts: Dict[str, Account] = {
            aid: Account(**adata) for aid, adata in raw.items()
        }

    def _dump(self) -> Dict[str, dict]:
        return {aid: account.__dict__ for aid, account in self._accounts.items()}

    def save(self) -> None:
        self._write_raw(self._dump())
    #public API used by services/tests
    def create(self, account: Account) -> None:
        if account.account_id in self._accounts:
            raise ValueError("Account id already exists")
        self._accounts[account.account_id] = account
        self.save()

    def save_account(self, account: Account) -> None:
        self._accounts[account.account_id] = account
        self.save()

    def get_account(self, account_id: str) -> Optional[Account]:
        return self._accounts.get(account_id)

    def get_by_user(self, username: str) -> Optional[Account]:
        for acct in self._accounts.values():
            if acct.username == username:
                return acct
        return None

    def get_by_id(self, account_id: str) -> Optional[Account]:
        return self.get_account(account_id)

    def list_accounts(self) -> List[Account]:
        return list(self._accounts.values())
