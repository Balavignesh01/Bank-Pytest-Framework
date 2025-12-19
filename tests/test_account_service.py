
# Advanced pytest test suite for account deposit & withdraw services.
# Concepts demonstrated:
# ----------------------
# - Custom markers (@pytest.mark.account)
# - Class-based test grouping
# - Function-level markers
# - @pytest.mark.parametrize (single & multi-arg)
# - Parametrize with ids
# - Exception testing with context managers
# - pytest.approx for floating-point comparisons
# - monkeypatch to simulate edge cases
# - xfail for future business rules
# - Regression-style tests
# - State isolation via fixtures

import pytest
from bank.services.register_service import create_account
from bank.services.account_service import (
    deposit,
    withdraw,
    AccountUpdateError,
)
# -------------------------------------------------------------------
# DEPOSIT TESTS
# -------------------------------------------------------------------
@pytest.mark.account
class TestDeposit:
    """Deposit-related tests."""
    @pytest.mark.parametrize(
        [10.0, 50.5, 99.99],
        ids=["small", "medium", "decimal"],
    )
    def test_deposit_increases_balance(self, store, amount):
        """
        Concepts:
        - Parametrized test
        - Floating-point assertion using pytest.approx
        """
        acc = create_account("dep_user", "pw", store)
        new_balance = deposit(acc.account_id, amount, store)
        assert new_balance == pytest.approx(amount)
    @pytest.mark.parametrize(
        "amount",
        [0.0, -10.0, -0.01],
        ids=["zero", "negative", "negative-decimal"],
    )
    def test_deposit_invalid_amount_raises(self, store, amount):
        """
        Concepts:
        - Negative testing
        - Validation logic verification
        """
        acc = create_account("dep_user2", "pw", store)
        with pytest.raises(AccountUpdateError):
            deposit(acc.account_id, amount, store)

    def test_deposit_multiple_times_accumulates_balance(self, store):
        """
        Concepts:
        - Sequential operations
        - State accumulation verification
        """
        acc = create_account("multi_dep", "pw", store)
        deposit(acc.account_id, 25.0, store)
        deposit(acc.account_id, 30.0, store)
        final_balance = deposit(acc.account_id, 45.0, store)
        assert final_balance == pytest.approx(100.0)
    def test_deposit_to_nonexistent_account_raises(self, store):
        """
        Concepts:
        - Error handling for invalid identifiers
        """
        with pytest.raises(AccountUpdateError):
            deposit("NONEXIST", 10.0, store)
# -------------------------------------------------------------------
# WITHDRAW TESTS
# -------------------------------------------------------------------

@pytest.mark.account
class TestWithdraw:
    def test_withdraw_decreases_balance(self, store):
        """
        Concepts:
        - Happy-path test
        """
        acc = create_account("wd_user", "pw", store)
        deposit(acc.account_id, 100.0, store)
        new_balance = withdraw(acc.account_id, 40.0, store)
        assert new_balance == pytest.approx(60.0)
    @pytest.mark.parametrize(
        "amount",
        [0.0, -5.0],
        ids=["zero", "negative"],
    )
    def test_withdraw_invalid_amount(self, store, amount):
        """
        Concepts:
        - Parametrized invalid input testing
        """
        acc = create_account("wd_invalid", "pw", store)
        deposit(acc.account_id, 50.0, store)

        with pytest.raises(AccountUpdateError):
            withdraw(acc.account_id, amount, store)
    @pytest.mark.parametrize(
        "start_balance,withdraw_amount",
        [
            (20.0, 30.0),
            (0.0, 1.0),
            (10.0, 10.01),
        ],
        ids=[
            "less-than-withdraw",
            "zero-balance",
            "precision-overdraft",
        ],
    )
    def test_withdraw_insufficient_funds(
        self, store, start_balance, withdraw_amount
    ):
        """
        Concepts:
        - Multi-argument parametrize
        - Business rule enforcement
        """
        acc = create_account("wd_insufficient", "pw", store)
        if start_balance > 0:
            deposit(acc.account_id, start_balance, store)
        with pytest.raises(AccountUpdateError):
            withdraw(acc.account_id, withdraw_amount, store)
    def test_withdraw_entire_balance_leaves_zero(self, store):
        """
        Concepts:
        - Boundary condition testing
        """
        acc = create_account("wd_exact", "pw", store)
        deposit(acc.account_id, 75.0, store)
        remaining = withdraw(acc.account_id, 75.0, store)
        assert remaining == pytest.approx(0.0)
    def test_withdraw_from_nonexistent_account_raises(self, store):
        """
        Concepts:
        - Invalid account handling
        """
        with pytest.raises(AccountUpdateError):
            withdraw("NOACCOUNT", 10.0, store)
# -------------------------------------------------------------------
# MONKEYPATCH EXAMPLES
# -------------------------------------------------------------------
@pytest.mark.account
class TestAccountServiceWithMonkeypatch:
    def test_deposit_internal_store_failure(self, store, monkeypatch):
        """
        Concepts:
        - monkeypatch to simulate internal failure
        - Defensive error handling test
        """
        acc = create_account("patch_dep", "pw", store)
        def broken_save_account(*args, **kwargs):
            raise RuntimeError("Disk write failed")
        monkeypatch.setattr(store, "save_account", broken_save_account)
        with pytest.raises(RuntimeError):
            deposit(acc.account_id, 10.0, store)
    def test_withdraw_internal_store_failure(self, store, monkeypatch):
        """
        Concepts:
        - monkeypatch applied to simulate infrastructure error
        """
        acc = create_account("patch_wd", "pw", store)
        deposit(acc.account_id, 50.0, store)
        def broken_save_account(*args, **kwargs):
            raise RuntimeError("Database unavailable")
        monkeypatch.setattr(store, "save_account", broken_save_account)
        with pytest.raises(RuntimeError):
            withdraw(acc.account_id, 10.0, store)
# -------------------------------------------------------------------
# FUTURE / DOCUMENTED BEHAVIOR
# -------------------------------------------------------------------
@pytest.mark.account
@pytest.mark.xfail(reason="Business rule: overdraft support planned but not implemented")
def test_withdraw_allows_overdraft_future(self, store):
    acc = create_account("future_overdraft", "pw", store)
    deposit(acc.account_id, 10.0, store)
    # Future behavior: allow overdraft
    withdraw(acc.account_id, 20.0, store)