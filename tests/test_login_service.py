# tests/test_login_service.py
# ============================================================
# Advanced pytest test suite for LOGIN service (Account ID based)
#
# This file contains TWO layers of validation:
# 1️⃣ Backend authentication tests using isolated AccountStore
# 2️⃣ Security, regression, and resilience tests (no UI dependency)
#
# Login is validated strictly using:
# - Account ID
# - Plain-text password (hashed internally)
#
# Concepts demonstrated:
# ------------------------------------------------------------
# - Custom markers (@pytest.mark.login)
# - Fixture-based test data setup
# - Dependency injection (store fixture)
# - Account-ID based authentication validation
# - Case normalization & input sanitization
# - @
import pytest
from bank.services.register_service import create_account
from bank.services.login_service import login
# -------------------------------------------------------------------
# FIXTURES
# -------------------------------------------------------------------
@pytest.fixture
def registered_user(store):
    return create_account("login_user", "password123", store)
@pytest.fixture
def another_user(store):
    return create_account("other_user", "otherpass", store)
# -------------------------------------------------------------------
# BASIC LOGIN TESTS (ACCOUNT ID BASED)
# -------------------------------------------------------------------

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
# ------------------------------------------------------------------
@pytest.mark.login
@pytest.mark.parametrize(
    "password,expected_ok",
    [
        ("password123", True),
        ("wrong", False),
    ],
)
def test_login_password_combinations(store, password, expected_ok):
    acc = create_account("login_user", "password123", store)
    result = login(acc.account_id, password, store)
    assert (result is not None) is expected_ok

# -------------------------------------------------------------------
# INVALID INPUTS
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

    assert user1.account_id != user2.account_id

@pytest.mark.login
def test_login_wrong_password(store, registered_user):
    result = login(registered_user.account_id, "wrong", store)
    assert result is None

# -------------------------------------------------------------------
# MONKEYPATCH TESTS (UPDATED FOR get_by_id)
# -------------------------------------------------------------------

@pytest.mark.login
class TestLoginWithMonkeypatch:
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
