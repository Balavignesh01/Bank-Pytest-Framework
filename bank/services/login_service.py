from typing import Optional

from bank.models.store import AccountStore
from bank.models.account import Account


def login(
    username: str,
    password: str,
    store: Optional[AccountStore] = None
) -> Optional[Account]:
    if store is None:
        store = AccountStore()
    username = (username or "").strip().lower()
    password = (password or "").strip()

    if not username or not password:
        return None

    acct = store.get_by_user(username)
    if not acct:
        return None

    return acct if acct.check_password(password) else None
