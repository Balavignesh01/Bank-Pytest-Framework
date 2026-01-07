from typing import Optional
from bank.models.store import AccountStore
from bank.models.account import Account
def login(
    account_id: str, 
    password: str,
    store: Optional[AccountStore] = None
) -> Optional[Account]:
    if store is None:
        store = AccountStore()
    # Normalize inputs
    account_id = (account_id or "").strip().upper()
    password = (password or "").strip()
    if not account_id or not password:
        return None
    # Fetch account by ID (NOT username)
    acct = store.get_by_id(account_id)
    if not acct:
        return None
    # Password validation
    return acct if acct.check_password(password) else None
