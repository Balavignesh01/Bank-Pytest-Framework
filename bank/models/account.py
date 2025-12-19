import hashlib
from dataclasses import dataclass
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

@dataclass
class Account:
    account_id: str
    username: str
    password_hash: str
    balance: float = 0.0
    is_admin: bool = False
    @classmethod
    def from_plain_password(cls, account_id: str, username: str, password: str, balance: float = 0.0, is_admin: bool = False) -> "Account":
        return cls(
            account_id=account_id,
            username=username,
            password_hash=hash_password(password),
            balance=float(balance),
            is_admin=is_admin,
        )

    def check_password(self, password: str) -> bool:
        return self.password_hash == hash_password(password)
