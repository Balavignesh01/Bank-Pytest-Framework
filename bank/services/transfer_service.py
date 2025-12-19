from typing import Optional
from bank.models.store import AccountStore
class TransferError(Exception):
    pass
def transfer_funds(
    from_account_id: str,
    to_account_id: str,
    amount: float,
    store: Optional[AccountStore] = None,
) -> None:
    if store is None:
        store = AccountStore()
    if amount <= 0:
        raise TransferError("Transfer amount must be positive")
    if from_account_id == to_account_id:
        raise TransferError("Cannot transfer to the same account")
    from_acct = store.get_account(from_account_id)
    to_acct = store.get_account(to_account_id)
    if not from_acct or not to_acct:
        raise TransferError("Invalid account id(s)")
    if from_acct.balance < amount:
        raise TransferError("Insufficient funds")
    from_acct.balance -= float(amount)
    to_acct.balance += float(amount)
    store.save_account(from_acct)
    store.save_account(to_acct)