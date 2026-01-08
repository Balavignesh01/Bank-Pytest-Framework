# ============================================================
# Concepts covered:
# ------------------------------------------------------------
# - Custom markers (@pytest.mark.register)
# - Class-based grouping
# - Parametrization (single & multi-arg) with ids
# - Fixtures (store injection)
# - skip
# - monkeypatch (internal helper patching)
# - Exception assertions
# - Regression & edge-case validation
# - Data normalization tests
# - Boolean flag coverage
# - UI → pytest contract validation
# ============================================================

import pytest
import os
import json

from bank.services.register_service import (
    create_account,
    RegistrationError,
)

# ===================================================================
# FIXTURES — REAL UI STATE 
# ===================================================================

@pytest.fixture(scope="session")
def ui_accounts():
    raw = os.environ.get("UI_ACCOUNTS")
    if not raw:
        pytest.skip("UI_ACCOUNTS not provided by UI")
    return json.loads(raw)

# ===================================================================
# BACKEND REGISTRATION UNIT TESTS
# ===================================================================

@pytest.mark.register
class TestRegistrationBasic:
    # Basic happy-path and input-validation behavior

    def test_create_account_success(self, store):
        acc = create_account("alice", "secret", store)
        assert acc.username == "alice"
        assert isinstance(acc.account_id, str)
        assert len(acc.account_id) == 6
        assert acc.balance == 0.0
        assert acc.is_admin is False

    @pytest.mark.parametrize(
        "username,password",
        [
            ("", "pw"),
            ("   ", "pw"),
            ("user", ""),
            ("user", "   "),
            (None, "pw"),
            ("user", None),
        ],
        ids=[
            "empty-username",
            "whitespace-username",
            "empty-password",
            "whitespace-password",
            "none-username",
            "none-password",
        ],
    )
    def test_create_account_missing_fields_raises(
        self, store, username, password
    ):
        with pytest.raises(RegistrationError):
            create_account(username, password, store)

@pytest.mark.register
class TestRegistrationAdvanced:
    @pytest.mark.parametrize(
        "uname1,uname2",
        [
            ("bob", "bob"),
            ("bob", " Bob "),
            ("BOB", "bob"),
        ],
        ids=[
            "exact-duplicate",
            "whitespace-duplicate",
            "case-insensitive-duplicate",
        ],
    )
    def test_duplicate_username(self, store, uname1, uname2):
        create_account(uname1, "pw", store)
        with pytest.raises(RegistrationError):
            create_account(uname2, "pw", store)

    @pytest.mark.skip(
        reason="External email service not available in test environment"
    )
    def test_registration_triggers_welcome_email(self, store):
        create_account("temp", "pw", store)

# -------------------------------------------------------------------
# MONKEY PATCH 
# -------------------------------------------------------------------
    def test_account_id_collision(self, store, monkeypatch):
        def fixed_id(_=6):
            return "AAAAAA"
        monkeypatch.setattr(
            "bank.services.register_service._generate_account_id",
            fixed_id,
        )
        create_account("user1", "pw", store)
        with pytest.raises(Exception):
            create_account("user2", "pw", store)

# -------------------------------------------------------------------
# BACKEND LOGIC - NORMALIZATION AND UNIQUE CHECK
# -------------------------------------------------------------------

    def test_username_normalization(self, store):
        acc = create_account("  Alice  ", "pw", store)
        assert acc.username == "alice"

    def test_account_ids_unique(self, store):
        ids = set()
        for i in range(10):
            acc = create_account(f"user{i}", "pw", store)
            assert acc.account_id not in ids
            ids.add(acc.account_id)
        assert len(ids) == 10

# -------------------------------------------------------------------
# FUNCTION-LEVEL PARAMETRIZATION
# -------------------------------------------------------------------

@pytest.mark.register
@pytest.mark.parametrize(
    "username,is_admin",
    [
        ("regular_user", False),
        ("admin_user", True),
    ],
    ids=["regular-account", "admin-account"],
)
def test_create_account_admin_flag(store, username, is_admin):
    acc = create_account(username, "pw", store, is_admin=is_admin)
    assert acc.is_admin is is_admin
    assert acc.username == username.lower()

# -------------------------------------------------------------------
# REGRESSION / STABILITY TESTS
# -------------------------------------------------------------------

@pytest.mark.register
def test_multiple_accounts_independent(store):
    a1 = create_account("userA", "pw", store)
    a2 = create_account("userB", "pw", store)
    assert a1.account_id != a2.account_id
    assert a1.username != a2.username
    assert a1.balance == 0.0
    assert a2.balance == 0.0

@pytest.mark.register
def test_shared_store_prevents_duplicates(store):
    create_account("shared", "pw", store)
    with pytest.raises(RegistrationError):
        create_account("shared", "pw", store)

# ===================================================================
# REAL-TIME UI VALIDATION TESTS
# ===================================================================

@pytest.mark.register
@pytest.mark.skipif(
    os.environ.get("UI_ACTION") == "create-account",
    reason="UI account not created yet during create-account action",
)
@pytest.mark.skipif(
    not os.environ.get("UI_ACCOUNTS"),
    reason="UI not running - skipping runtime UI validation",
)
class TestRegistrationUIRuntimeValidation:

    def test_ui_accounts_exist(self, ui_accounts):
        assert isinstance(ui_accounts, list)
        assert ui_accounts, "No accounts found in UI localStorage"

    def test_ui_account_ids_unique(self, ui_accounts):
        ids = [a["accountId"] for a in ui_accounts]
        assert len(ids) == len(set(ids)), "Duplicate account IDs in UI"

    def test_ui_usernames_normalized(self, ui_accounts):
        for acc in ui_accounts:
            assert acc["username"] == acc["username"].lower()

    def test_ui_admin_account_exists(self, ui_accounts):
        admins = [a for a in ui_accounts if a.get("isAdmin")]
        assert admins, "Admin account missing in UI"

    def test_ui_accounts_have_required_fields(self, ui_accounts):
        for acc in ui_accounts:
            assert "accountId" in acc
            assert "username" in acc
            assert "balance" in acc
            assert "isAdmin" in acc