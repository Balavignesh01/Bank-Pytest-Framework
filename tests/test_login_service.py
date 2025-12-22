# ============================================================
# Concepts demonstrated:
# ------------------------------------------------------------
# - Custom markers (@pytest.mark.login)
# - Fixture-based data setup
# - Dependency injection (store fixture)
# - Parametrization
# - Negative & security scenarios
# - monkeypatch for resilience testing
# - Runtime UI contract validation (NO mocks)
# ============================================================

import pytest
import os
import json

from bank.services.register_service import create_account
from bank.services.login_service import login

# ===================================================================
# FIXTURES — BACKEND UNIT TEST DATA
# ===================================================================
@pytest.fixture
def registered_user(store):
    return create_account("login_user", "password123", store)

@pytest.fixture
def another_user(store):
    return create_account("other_user", "otherpass", store)

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

@pytest.mark.login
def test_login_success(store, registered_user):
    logged_in = login(registered_user.account_id, "password123", store)
    assert logged_in is not None
    assert logged_in.account_id == registered_user.account_id

@pytest.mark.login
def test_login_account_id_case_insensitive(store):
    acc = create_account("SomeUser", "pw", store)
    logged_in = login(acc.account_id.lower(), "pw", store)
    assert logged_in is not None
    assert logged_in.account_id == acc.account_id

# -------------------------------------------------------------------
# PASSWORD COMBINATIONS
# -------------------------------------------------------------------

@pytest.mark.login
@pytest.mark.parametrize(
    "password,expected_ok",
    [
        ("password123", True),
        ("wrong", False),
    ],
    ids=["correct-password", "wrong-password"],
)
def test_login_password_combinations(store, password, expected_ok):
    acc = create_account("login_user", "password123", store)
    result = login(acc.account_id, password, store)
    assert (result is not None) is expected_ok

# -------------------------------------------------------------------
# INVALID INPUTS (SECURITY HARDENING)
# -------------------------------------------------------------------

@pytest.mark.login
@pytest.mark.parametrize(
    "account_id,password",
    [
        ("", "password123"),
        ("   ", "password123"),
        (None, "password123"),
        ("ABC123", ""),
        ("ABC123", None),
    ],
    ids=[
        "empty-id",
        "blank-id",
        "null-id",
        "empty-password",
        "null-password",
    ],
)
def test_login_invalid_inputs(store, account_id, password):
    result = login(account_id, password, store)
    assert result is None

# -------------------------------------------------------------------
# MULTI-USER SCENARIOS
# -------------------------------------------------------------------

@pytest.mark.login
def test_login_with_multiple_users(store, registered_user, another_user):
    user1 = login(registered_user.account_id, "password123", store)
    user2 = login(another_user.account_id, "otherpass", store)
    assert user1 is not None
    assert user2 is not None
    assert user1.account_id != user2.account_id

@pytest.mark.login
def test_login_wrong_password(store, registered_user):
    result = login(registered_user.account_id, "wrong", store)
    assert result is None
# -------------------------------------------------------------------
# MONKEYPATCH — RESILIENCE & FAILURE MODES
# -------------------------------------------------------------------

@pytest.mark.login
class TestLoginWithMonkeypatch:
    """Simulate backend lookup failures."""

    def test_login_store_lookup_failure(self, store, monkeypatch):
        def broken_get_by_id(*args, **kwargs):
            raise RuntimeError("Database unavailable")
        monkeypatch.setattr(store, "get_by_id", broken_get_by_id)
        with pytest.raises(RuntimeError):
            login("ANYID", "password123", store)
    def test_login_returns_none_when_store_returns_none(self, store, monkeypatch):
        monkeypatch.setattr(store, "get_by_id", lambda *_: None)
        result = login("ANYID", "password123", store)
        assert result is None

# ===================================================================
# REAL-TIME UI LOGIN VALIDATION (NO MOCKS, NO HARDCODED VALUES)
# ===================================================================

@pytest.mark.login
@pytest.mark.skipif(
    os.environ.get("UI_ACTION") == "login",
    reason="UI session not established yet during login",
)
@pytest.mark.skipif(
    not os.environ.get("UI_ACCOUNTS"),
    reason="UI not running – skipping runtime UI login validation",
)
class TestLoginUIRuntimeValidation:
    def test_ui_session_exists(self, ui_session):
        assert ui_session, "UI session missing"

    def test_ui_session_account_exists_in_ui_accounts(
        self, ui_accounts, ui_session
    ):
        ids = [a["accountId"] for a in ui_accounts]
        assert (
            ui_session["accountId"] in ids
        ), "Logged-in user not found in UI accounts"

    @pytest.mark.login
    def test_ui_logged_in_user_exists(ui_accounts, ui_session):
        ids = [a["accountId"] for a in ui_accounts]
        assert ui_session["accountId"] in ids


    def test_ui_login_state_consistency(self, ui_session):
        assert ui_session.get("accountId")
        assert ui_session.get("username") is not None
