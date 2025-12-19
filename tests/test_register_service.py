# Advanced pytest test suite for registration service.
# Concepts covered (with REAL usage, not just comments):
# -------------------------------------------------------
# - Custom markers (@pytest.mark.register)
# - Test classes for logical grouping
# - Function-level and class-level markers
# - @pytest.mark.parametrize (single & multi-arg)
# - @pytest.mark.parametrize with ids
# - Fixtures (store fixture from conftest.py)
# - Built-in markers: skip, xfail
# - monkeypatch (patching internal helpers)
# - Context-manager exception assertions
# - Multiple assertions per test
# - Indirect behavior verification
# - Test ordering independence
# - Edge-case validation
# - Data normalization tests
# - Boolean flag coverage

import pytest
from bank.services.register_service import (
    create_account,
    RegistrationError,
    _generate_account_id,  # internal helper – patched via monkeypatch
)
# -------------------------------------------------------------------
# BASIC REGISTRATION TESTS
# -------------------------------------------------------------------
@pytest.mark.register
class TestRegistrationBasic:
    """
    Basic, happy-path and input-validation behavior.
    """
    def test_create_account_success(self, store):
        """
        Concept:
        - Basic happy-path test
        - Asserts multiple attributes on returned object
        """
        acc = create_account("alice", "secret", store)
        assert acc.username == "alice"
        assert acc.account_id is not None
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
        """
        Concepts:
        - @pytest.mark.parametrize with ids
        - Exception assertion using context manager
        - Defensive validation testing
        """
        with pytest.raises(RegistrationError):
            create_account(username, password, store)
# -------------------------------------------------------------------
# ADVANCED / EDGE CASE TESTS
# -------------------------------------------------------------------
@pytest.mark.register
class TestRegistrationAdvanced:
    """
    Advanced and edge-case behavior.
    These tests verify:
    - username normalization
    - duplicate detection
    - monkeypatch usage
    - xfail behavior
    - skip behavior
    """
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
        """
        Concepts:
        - Multi-argument parametrization
        - Data normalization verification
        - Business rule enforcement
        """
        create_account(uname1, "pw", store)

        with pytest.raises(RegistrationError):
            create_account(uname2, "pw", store)
    @pytest.mark.skip(reason="External email service not available in test environment")
    def test_registration_triggers_welcome_email(self, store):
        create_account("temp", "pw", store)
    @pytest.mark.xfail(
        reason="ID collision handling is delegated to AccountStore",
        strict=False,
    )
    def test_id_collision_xfail(self, store, monkeypatch):
        """
        Concepts:
        - @pytest.mark.xfail
        - monkeypatch to force deterministic failure
        - Documenting known edge cases
        monkeypatch ensures that _generate_account_id()
        always returns the same value, forcing a collision.
        """
        def fixed_id(length=6):
            return "AAAAAA"

        monkeypatch.setattr(
            "bank.services.register_service._generate_account_id",
            fixed_id,
        )
        # First creation succeeds
        create_account("user1", "pw", store)
        # Second creation collides at store layer
        with pytest.raises(ValueError):
            create_account("user2", "pw", store)
    def test_username_is_normalized_to_lowercase(self, store):
        """
        Concept:
        - Data normalization verification
        - Indirect behavior testing
        """
        acc = create_account("  Alice  ", "pw", store)
        assert acc.username == "alice"
    def test_account_ids_are_unique_for_multiple_accounts(self, store):
        """
        Concepts:
        - Loop-based assertion
        - Uniqueness verification
        """
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
    """
    Concepts:
    - Function-level marker
    - Parametrization with ids
    - Boolean flag coverage
    """
    acc = create_account(username, "pw", store, is_admin=is_admin)
    assert acc.is_admin is is_admin
    assert acc.username == username.lower()
# -------------------------------------------------------------------
# REGRESSION / STABILITY TESTS
# -------------------------------------------------------------------
@pytest.mark.register
def test_multiple_accounts_do_not_interfere_with_each_other(store):
    """
    Concepts:
    - Regression testing
    - State isolation verification
    """
    a1 = create_account("userA", "pw", store)
    a2 = create_account("userB", "pw", store)
    assert a1.account_id != a2.account_id
    assert a1.username != a2.username
    assert a1.balance == 0.0
    assert a2.balance == 0.0
@pytest.mark.register
def test_store_injection_allows_shared_state(store):
    """
    Concepts:
    - Dependency injection via fixtures
    - Shared state across calls
    """
    create_account("shared", "pw", store)
    with pytest.raises(RegistrationError):
        create_account("shared", "pw", store)