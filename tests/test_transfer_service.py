# tests/test_transfer_service.py
#
# Advanced pytest test suite for transfer service.
#
# This file contains TWO validation layers:
# 1️⃣ Backend unit tests using isolated AccountStore (store fixture)
# 2️⃣ Real-time UI validation using browser localStorage snapshot
#
# Concepts demonstrated:
# ----------------------
# - Custom marker (@pytest.mark.transfer)
# - Class-based test grouping
# - Multi-user transfer scenarios
# - Round-trip and chained transfers
# - @pytest.mark.parametrize (single & multi-arg)
# - Parametrize with ids
# - Failure-path matrices
# - Boundary and edge-case testing
# - pytest.approx for floating point safety
# - monkeypatch to simulate infrastructure failures
# - Regression and state-consistency tests
# - UI → pytest contract validation (NEW)

import pytest
import os
from bank.services.register_service import create_account
from bank.services.transfer_service import transfer_funds, TransferError
from bank.services.account_service import deposit


# ===================================================================
# BACKEND TRANSFER TESTS (Pure business logic)
# ===================================================================

# -------------------------------------------------------------------
# HAPPY PATH / SCENARIO TESTS
# -------------------------------------------------------------------
@pytest.mark.transfer
class TestTransferScenarios:
    def test_round_trip_transfer(self, store):
        """
        Concepts:
        - Multi-user interaction
        - Round-trip transfer (A → B → A)
        """
        a = create_account("a1", "pw", store)
        b = create_account("a2", "pw", store)

        deposit(a.account_id, 200, store)
        transfer_funds(a.account_id, b.account_id, 60, store)
        transfer_funds(b.account_id, a.account_id, 25, store)

        assert store.get_by_id(a.account_id).balance == pytest.approx(165)
        assert store.get_by_id(b.account_id).balance == pytest.approx(35)

    def test_chain_transfers(self, store):
        """
        Concepts:
        - Chained transfers (A → B → C)
        - Intermediate balance verification
        """
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
        """
        Concepts:
        - Sequential state mutation
        - Regression-style test
        """
        a = create_account("seqA", "pw", store)
        b = create_account("seqB", "pw", store)

        deposit(a.account_id, 500, store)

        for amt in (50, 75, 125):
            transfer_funds(a.account_id, b.account_id, amt, store)

        assert store.get_by_id(a.account_id).balance == pytest.approx(250)
        assert store.get_by_id(b.account_id).balance == pytest.approx(250)


# -------------------------------------------------------------------
# FAILURE / NEGATIVE TESTS
# -------------------------------------------------------------------
@pytest.mark.transfer
class TestTransferFailures:
    @pytest.mark.parametrize(
        "amount",
        [0, -10, -1],
        ids=["zero", "negative", "negative-small"],
    )
    def test_invalid_amounts(self, store, amount):
        """
        Concepts:
        - Parametrized invalid inputs
        - Defensive validation
        """
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
        """
        Concepts:
        - Branch testing via parametrization
        """
        a = create_account("good", "pw", store)
        fake = "ZZZZZZ"

        if missing == "from":
            with pytest.raises(TransferError):
                transfer_funds(fake, a.account_id, 10, store)
        else:
            with pytest.raises(TransferError):
                transfer_funds(a.account_id, fake, 10, store)

    @pytest.mark.parametrize(
        "start,transfer",
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
    def test_insufficient_matrix(self, store, start, transfer):
        """
        Concepts:
        - Failure-path matrix
        - Multi-arg parametrize
        """
        a = create_account("iA2", "pw", store)
        b = create_account("iB2", "pw", store)

        if start > 0:
            deposit(a.account_id, start, store)

        with pytest.raises(TransferError):
            transfer_funds(a.account_id, b.account_id, transfer, store)

    def test_transfer_to_same_account_fails(self, store):
        """
        Concepts:
        - Business rule validation
        """
        a = create_account("self", "pw", store)
        deposit(a.account_id, 100, store)

        with pytest.raises(TransferError):
            transfer_funds(a.account_id, a.account_id, 10, store)


# -------------------------------------------------------------------
# MONKEYPATCH / INFRASTRUCTURE FAILURE TESTS
# -------------------------------------------------------------------
@pytest.mark.transfer
class TestTransferWithMonkeypatch:
    def test_transfer_get_account_failure(self, store, monkeypatch):
        """
        Monkeypatch get_account to simulate store read failure.
        """
        a = create_account("patchA", "pw", store)
        b = create_account("patchB", "pw", store)
        deposit(a.account_id, 50, store)

        def broken_get_account(*args, **kwargs):
            raise RuntimeError("Store read failed")

        monkeypatch.setattr(store, "get_account", broken_get_account)

        with pytest.raises(RuntimeError):
            transfer_funds(a.account_id, b.account_id, 10, store)

    def test_transfer_save_account_failure(self, store, monkeypatch):
        """
        Monkeypatch save_account to simulate persistence failure.
        """
        a = create_account("patchA2", "pw", store)
        b = create_account("patchB2", "pw", store)
        deposit(a.account_id, 50, store)

        def broken_save_account(*args, **kwargs):
            raise RuntimeError("Store write failed")

        monkeypatch.setattr(store, "save_account", broken_save_account)

        with pytest.raises(RuntimeError):
            transfer_funds(a.account_id, b.account_id, 10, store)


# ===================================================================
# REAL-TIME UI VALIDATION TESTS (NEW)
# These tests validate browser localStorage state sent by UI
# ===================================================================

@pytest.mark.transfer
@pytest.mark.skipif(
    not os.environ.get("UI_ACTIVE"),
    reason="UI not running – skipping UI state validation tests",
)
class TestTransferUIStateValidation:
    def test_ui_has_multiple_accounts_for_transfer(self, ui_accounts):
        customers = [a for a in ui_accounts if not a.get("isAdmin")]
        assert len(customers) >= 2, (
            "At least two customer accounts are required for transfers"
        )

    def test_ui_balances_are_never_negative(self, ui_accounts):
        for acc in ui_accounts:
            assert acc["balance"] >= 0

    def test_ui_transfer_history_structure(self, ui_transfers):
        for t in ui_transfers:
            assert "fromAccountId" in t
            assert "toAccountId" in t
            assert "amount" in t

    def test_ui_session_is_not_admin_for_transfers(self, ui_session):
        assert not ui_session.get("isAdmin")