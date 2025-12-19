import random
import string
from typing import Optional
from bank.models.account import Account
from bank.models.store import AccountStore
class RegistrationError(Exception):
# Raised when we cannot create an account
def _generate_account_id(length: int = 6) -> str:
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=length))
def create_account(
    username: str,
    password: str,
    store: Optional[AccountStore] = None,
    is_admin: bool = False,
) -> Account:
    # Main account creation API used by tests
    if store is None:
        store = AccountStore()
    username = (username or "").strip()
    password = (password or "").strip()
    if not username or not password:
        raise RegistrationError("Username and password are required")
    normalized_username = username.lower()
    if store.get_by_user(normalized_username):
        raise RegistrationError("Username already exists")
    account_id = _generate_account_id()
    acct = Account.from_plain_password(
        account_id=account_id,
        username=normalized_username,
        password=password,
        balance=0.0,
        is_admin=is_admin,
    )
    store.create(acct)
    return acct