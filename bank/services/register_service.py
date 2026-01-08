import random
import string
from typing import Optional
from bank.models.account import Account
from bank.models.store import AccountStore
class RegistrationError(Exception):
    pass
def _generate_account_id(length: int = 6) -> str:
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=length))
def create_account(
    username: str,
    password: str,
    store: Optional[AccountStore] = None,
    is_admin: bool = False,
) -> Account:
    if store is None:
        store = AccountStore()
    # Normalize inputs
    username = (username or "").strip()
    password = (password or "").strip()
    if not username or not password:
        raise RegistrationError("Username and password are required")
    normalized_username = username.lower()
    # Username uniqueness check
    if store.get_by_user(normalized_username):
        raise RegistrationError("Username already exists")
    # Generate unique Account ID (collision-safe)
    for _ in range(10):
        account_id = _generate_account_id()
        if not store.get_by_id(account_id): # if not none == true
            break
    else:
        raise RegistrationError("Failed to generate unique Account ID")
    acct = Account.from_plain_password(
        account_id=account_id,
        username=normalized_username,
        password=password,
        balance=0.0,
        is_admin=is_admin,
    )
    store.create(acct)
    return acct