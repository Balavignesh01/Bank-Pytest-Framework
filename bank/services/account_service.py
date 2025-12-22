from typing import Optional
from bank.models.store import AccountStore
class AccountUpdateError(Exception):
    pass
def deposit(
    account_id: str,
    amount: float,
    store: Optional[AccountStore] = None
) -> float:
    """
    Deposit funds into an account using Account ID.
    """
    if store is None:
        store = AccountStore()
    account_id = (account_id or "").strip().upper()
    if not account_id:
        raise AccountUpdateError("Account ID is required")
    if amount <= 0:
        raise AccountUpdateError("Deposit amount must be positive")
    acct = store.get_by_id(account_id)
    if not acct:
        raise AccountUpdateError("Account not found")
    acct.balance += float(amount)
    store.save_account(acct)
    return acct.balance
def withdraw(
    account_id: str,
    amount: float,
    store: Optional[AccountStore] = None
) -> float:
    """
    Withdraw funds from an account using Account ID.
    """
    if store is None:
        store = AccountStore()
    account_id = (account_id or "").strip().upper()
    if not account_id:
        raise AccountUpdateError("Account ID is required")
    if amount <= 0:
        raise AccountUpdateError("Withdraw amount must be positive")
    acct = store.get_by_id(account_id)
    if not acct:
        raise AccountUpdateError("Account not found")
    if acct.balance < amount:
        raise AccountUpdateError("Insufficient funds")
    acct.balance -= float(amount)
    store.save_account(acct)
    return acct.balance