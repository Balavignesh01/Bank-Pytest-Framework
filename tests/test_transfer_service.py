# ============================================================
# Concepts demonstrated:
# ------------------------------------------------------------
# - Custom marker (@pytest.mark.transfer)
# - Class-based grouping
# - Multi-user transfer scenarios
# - Round-trip and chained transfers
# - Parametrization (single & multi-arg) with ids
# - Failure-path matrices
# - Boundary and edge-case testing
# - pytest.approx for floating-point safety
# - monkeypatch for infrastructure failures
# - Regression and state-consistency tests
# - UI → pytest contract validation (NO MOCKS)
# ============================================================

import pytest
import os
import json

from bank.services.register_service import create_account
from bank.services.transfer_service import transfer_funds, TransferError
from bank.services.account_service import deposit

# ===================================================================
# FIXTURES — REAL UI STATE
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

@pytest.fixture(scope="session")
def ui_transfers():
    raw = os.environ.get("UI_TRANSFERS")
    if not raw:
        pytest.skip("UI_TRANSFERS not provided by UI")
    return json.loads(raw)

# ===================================================================
# BACKEND TRANSFER UNIT TESTS
# ===================================================================

@pytest.mark.transfer
class TestTransferScenarios:
    # Happy-path and multi-user scenarios
    def test_round_trip_transfer(self, store):
        a = create_account("a1", "pw", store)
        b = create_account("a2", "pw", store)
        deposit(a.account_id, 200, store)
        transfer_funds(a.account_id, b.account_id, 60, store)
        transfer_funds(b.account_id, a.account_id, 25, store)
        assert store.get_by_id(a.account_id).balance == pytest.approx(165)
        assert store.get_by_id(b.account_id).balance == pytest.approx(35)

    def test_chain_transfers(self, store):
        a = create_account("uA", "pw", store)
        b = create_account("uB", "pw", store)
        c = create_account("uC", "pw", store)
        deposit(a.account_id, 300, store)
        transfer_funds(a.account_id, b.account_id, 100, store)
        transfer_funds(b.account_id, c.account_id, 50, store)
        assert store.get_by_id(a.account_id).balance == pytest.approx(200)
        assert store.get_by_id(b.account_id).balance == pytest.approx(50)
        assert store.get_by_id(c.account_id).balance == pytest.approx(50)

    def test_multiple_sequential_transfers(self, store):
        a = create_account("seqA", "pw", store)
        b = create_account("seqB", "pw", store)
        deposit(a.account_id, 500, store)
        for amt in (50, 75, 125):
            transfer_funds(a.account_id, b.account_id, amt, store)
        assert store.get_by_id(a.account_id).balance == pytest.approx(250)
        assert store.get_by_id(b.account_id).balance == pytest.approx(250)

# ===================================================================
# FAILURE / NEGATIVE TESTS
# ===================================================================

@pytest.mark.transfer
class TestTransferFailures:
    @pytest.mark.parametrize(
        "amount",
        [0, -10, -1],
        ids=["zero", "negative", "negative-small"],
    )
    def test_invalid_transfer_amounts(self, store, amount):
        a = create_account("iA", "pw", store)
        b = create_account("iB", "pw", store)

        deposit(a.account_id, 50, store)        

        with pytest.raises(TransferError):
            transfer_funds(a.account_id, b.account_id, amount, store)

    @pytest.mark.parametrize(
        "missing",
        ["from", "to"],
        ids=["missing-source", "missing-destination"],
    )
    def test_missing_accounts(self, store, missing):
        a = create_account("good", "pw", store)
        fake = "ZZZZZZ"

        if missing == "from":
            with pytest.raises(TransferError):
                transfer_funds(fake, a.account_id, 10, store)
        else:
            with pytest.raises(TransferError):
                transfer_funds(a.account_id, fake, 10, store)

    @pytest.mark.parametrize(
        "start,amount",
        [
            (20, 30),
            (0, 1),
            (5, 10),
            (100, 100.01),
        ],
        ids=[
            "less-than-needed",
            "zero-balance",
            "small-insufficient",
            "precision-overdraw",
        ],
    )
    def test_insufficient_balance_matrix(self, store, start, amount):
        a = create_account("iA2", "pw", store)
        b = create_account("iB2", "pw", store)

        if start > 0:
            deposit(a.account_id, start, store)

        with pytest.raises(TransferError):
            transfer_funds(a.account_id, b.account_id, amount, store)

    def test_transfer_to_same_account_fails(self, store):
        a = create_account("self", "pw", store)
        deposit(a.account_id, 100, store)

        with pytest.raises(TransferError):
            transfer_funds(a.account_id, a.account_id, 10, store)

# ===================================================================
# MONKEYPATCH — INFRASTRUCTURE FAILURE SIMULATION
# ===================================================================

@pytest.mark.transfer
class TestTransferWithMonkeypatch:

    def test_store_read_failure(self, store, monkeypatch):
        a = create_account("patchA", "pw", store)
        b = create_account("patchB", "pw", store)
        deposit(a.account_id, 50, store)
        def broken_get_by_id(*args, **kwargs):
            raise RuntimeError("Store read failed")
        monkeypatch.setattr(store, "get_by_id", broken_get_by_id)
        with pytest.raises(RuntimeError):
            transfer_funds(a.account_id, b.account_id, 10, store)

    def test_store_write_failure(self, store, monkeypatch):
        a = create_account("patchA2", "pw", store)
        b = create_account("patchB2", "pw", store)
        deposit(a.account_id, 50, store)
        def broken_save_account(*args, **kwargs):
            raise RuntimeError("Store write failed")
        monkeypatch.setattr(store, "save_account", broken_save_account)
        with pytest.raises(RuntimeError):
            transfer_funds(a.account_id, b.account_id, 10, store)

# ===================================================================
# REAL-TIME UI VALIDATION TESTS (NO MOCKS)
# ===================================================================

@pytest.mark.transfer
@pytest.mark.skipif(
    os.environ.get("UI_ACTION") == "transfer-funds",
    reason="Transfer not applied yet during transfer action",
)
@pytest.mark.skipif(
    not os.environ.get("UI_ACCOUNTS"),
    reason="UI not running – skipping runtime UI validation tests",
)
class TestTransferUIRuntimeValidation:

    def test_ui_has_multiple_customer_accounts(self, ui_accounts):
        customers = [a for a in ui_accounts if not a.get("isAdmin")]
        assert len(customers) >= 2, (
            "At least two customer accounts are required for transfers"
        )

    def test_ui_balances_never_negative(self, ui_accounts):
        for acc in ui_accounts:
            assert acc["balance"] >= 0

    def test_ui_transfer_history_structure(self, ui_transfers):
        for t in ui_transfers:
            assert "fromAccountId" in t
            assert "toAccountId" in t
            assert "amount" in t

    def test_ui_session_not_admin_for_transfer(self, ui_session):
        assert not ui_session.get("isAdmin", False)