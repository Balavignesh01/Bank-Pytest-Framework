# ===================================================================
# ACCOUNT SERVICE TESTS
# Concepts covered:
# - Custom markers (@pytest.mark.account)
# - Class-based grouping
# - Function-level markers
# - Parametrization (single & multi-arg)
# - Parametrize with ids
# - Exception testing (pytest.raises)
# - pytest.approx for float safety
# - monkeypatch for fault injection
# - xfail for future rules
# - Regression testing
# - Fixture-based state isolation
# - REAL-TIME UI DATA validation (no mocks, no hardcoded values)
# ===================================================================
import pytest
import os
import json

from bank.services.register_service import create_account
from bank.services.account_service import (
    deposit,
    withdraw,
    AccountUpdateError,
)

# ===================================================================
# FIXTURES — REAL UI STATE (SOURCE OF TRUTH)
# ===================================================================

@pytest.fixture(scope="session")
def ui_accounts():
    raw = os.environ.get("UI_ACCOUNTS")
    if not raw:
        pytest.skip("UI_ACCOUNTS not provided by UI")
    return json.loads(raw)

@pytest.fixture(scope="session")
def ui_session():
    raw = os.environ.get("UI_SESSION")
    if not raw:
        pytest.skip("UI_SESSION not provided by UI")
    return json.loads(raw)

# ===================================================================
# BACKEND UNIT TESTS (NO UI DEPENDENCY)
# ===================================================================

@pytest.mark.account
class TestDepositUnit:

    @pytest.mark.parametrize(
        "amount",
        [10.0, 50.5, 99.99],
        ids=["small", "medium", "decimal"],
    )
    def test_deposit_increases_balance(self, store, amount):
        acc = create_account("dep_user", "pw", store)
        new_balance = deposit(acc.account_id, amount, store)
        assert new_balance == pytest.approx(amount)

    @pytest.mark.parametrize(
        "amount",
        [0.0, -10.0, -0.01],
        ids=["zero", "negative", "negative-decimal"],
    )
    def test_deposit_invalid_amount_raises(self, store, amount):
        acc = create_account("dep_user2", "pw", store)
        with pytest.raises(AccountUpdateError):
            deposit(acc.account_id, amount, store)

    def test_deposit_multiple_times_accumulates(self, store):
        acc = create_account("multi_dep", "pw", store)
        deposit(acc.account_id, 25.0, store)
        deposit(acc.account_id, 30.0, store)
        final_balance = deposit(acc.account_id, 45.0, store)
        assert final_balance == pytest.approx(100.0)

    def test_deposit_nonexistent_account(self, store):
        with pytest.raises(AccountUpdateError):
            deposit("NONEXIST", 10.0, store)

@pytest.mark.account
class TestWithdrawUnit:
    def test_withdraw_decreases_balance(self, store):
        acc = create_account("wd_user", "pw", store)
        deposit(acc.account_id, 100.0, store)
        remaining = withdraw(acc.account_id, 40.0, store)
        assert remaining == pytest.approx(60.0)

    @pytest.mark.parametrize(
        "amount",
        [0.0, -5.0],
        ids=["zero", "negative"],
    )
    def test_withdraw_invalid_amount(self, store, amount):
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
        ids=["overdraw", "zero-balance", "precision-overdraft"],
    )
    def test_withdraw_insufficient_funds(
        self, store, start_balance, withdraw_amount
    ):
        acc = create_account("wd_insufficient", "pw", store)
        if start_balance > 0:
            deposit(acc.account_id, start_balance, store)
        with pytest.raises(AccountUpdateError):
            withdraw(acc.account_id, withdraw_amount, store)
    def test_withdraw_exact_balance_leaves_zero(self, store):
        acc = create_account("wd_exact", "pw", store)
        deposit(acc.account_id, 75.0, store)
        remaining = withdraw(acc.account_id, 75.0, store)
        assert remaining == pytest.approx(0.0)

    def test_withdraw_nonexistent_account(self, store):
        with pytest.raises(AccountUpdateError):
            withdraw("NOACCOUNT", 10.0, store)

# ===================================================================
# MONKEYPATCH — INFRASTRUCTURE FAILURE SIMULATION
# ===================================================================

@pytest.mark.account
class TestAccountServiceFailures:
    # Resilience tests using monkeypatch
    def test_deposit_store_write_failure(self, store, monkeypatch):
        acc = create_account("patch_dep", "pw", store)
        def broken_save(*args, **kwargs):
            raise RuntimeError("Disk write failed")
        monkeypatch.setattr(store, "save_account", broken_save)
        with pytest.raises(RuntimeError):
            deposit(acc.account_id, 10.0, store)

    def test_withdraw_store_write_failure(self, store, monkeypatch):
        acc = create_account("patch_wd", "pw", store)
        deposit(acc.account_id, 50.0, store)
        def broken_save(*args, **kwargs):
            raise RuntimeError("DB unavailable")
        monkeypatch.setattr(store, "save_account", broken_save)
        with pytest.raises(RuntimeError):
            withdraw(acc.account_id, 10.0, store)

# ===================================================================
# FUTURE BUSINESS RULE (DOCUMENTATION VIA TEST)
# ===================================================================

@pytest.mark.account
@pytest.mark.xfail(reason="Overdraft feature planned but not implemented")
def test_withdraw_overdraft_future(store):
    acc = create_account("future_overdraft", "pw", store)
    deposit(acc.account_id, 10.0, store)
    withdraw(acc.account_id, 20.0, store)

# ===================================================================
# REAL-TIME UI VALIDATION TESTS (NO MOCKS)
# ===================================================================

@pytest.mark.account
@pytest.mark.skipif(
    not os.environ.get("UI_ACCOUNTS"),
    reason="UI not running – skipping runtime UI validation",
)
class TestAccountUIRuntimeValidation:

    def test_ui_accounts_exist(self, ui_accounts):
        assert ui_accounts, "UI has no accounts"

    def test_ui_balances_are_non_negative(self, ui_accounts):
        for acct in ui_accounts:
            assert acct["balance"] >= 0, f"Negative balance: {acct}"

    def test_ui_account_ids_unique(self, ui_accounts):
        ids = [a["accountId"] for a in ui_accounts]
        assert len(ids) == len(set(ids)), "Duplicate account IDs in UI"

    def test_ui_admin_account_present(self, ui_accounts):
        admins = [a for a in ui_accounts if a.get("isAdmin")]
        assert admins, "Admin account missing in UI"

    def test_logged_in_user_exists(self, ui_accounts, ui_session):
        ids = [a["accountId"] for a in ui_accounts]
        assert ui_session["accountId"] in ids, "Session user not in UI accounts"

    def test_logged_in_user_balance_valid(self, ui_accounts, ui_session):
        user = next(
            a for a in ui_accounts if a["accountId"] == ui_session["accountId"]
        )
        assert user["balance"] >= 0
