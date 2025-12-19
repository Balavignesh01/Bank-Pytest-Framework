"""
Advanced pytest test suite for login service.
Concepts demonstrated:
----------------------
- Custom markers (@pytest.mark.login)
- Fixtures returning domain objects
- Fixture dependency injection
- Function-level and module-level tests
- @pytest.mark.parametrize (single & multi-arg)
- Parametrize with ids
- Truth-table testing
- Negative-path validation
- monkeypatch for simulating backend failures
- Regression testing
- Explicit state setup per test
"""
import pytest
from bank.services.register_service import create_account
from bank.services.login_service import login
# -------------------------------------------------------------------
# FIXTURES
# -------------------------------------------------------------------
@pytest.fixture
def registered_user(store):
    """
    Fixture that creates and returns a registered user.
    Concepts:
    - Fixture returning a domain object
    - Shared setup logic
    """
    acc = create_account("login_user", "password123", store)
    return acc
@pytest.fixture
def another_user(store):
    """
    Fixture creating an additional user for multi-user scenarios.
    """
    return create_account("other_user", "otherpass", store)
# -------------------------------------------------------------------
# BASIC LOGIN TESTS
# -------------------------------------------------------------------
@pytest.mark.login
def test_login_success(store, registered_user):
    """
    Concepts:
    - Happy-path test
    - Fixture usage
    """
    logged_in = login(registered_user.username, "password123", store)
    assert logged_in is not None
    assert logged_in.account_id == registered_user.account_id
    assert logged_in.username == registered_user.username
@pytest.mark.login
def test_login_is_case_insensitive_for_username(store):
    """
    Concepts:
    - Data normalization verification
    """
    create_account("Login_User", "pw", store)
    logged_in = login("login_user", "pw", store)
    assert logged_in is not None
    assert logged_in.username == "login_user"
# -------------------------------------------------------------------
# PARAMETRIZED LOGIN COMBINATIONS
# -------------------------------------------------------------------
@pytest.mark.login
@pytest.mark.parametrize(
    "username,password,expected_ok",
    [
        ("login_user", "password123", True),     # correct
        ("login_user", "wrong", False),          # bad password
        ("no_such_user", "password123", False),  # unknown user
        ("LOGIN_USER", "password123", True),     # case-insensitive username
        (" login_user ", "password123", True),   # whitespace username
    ],
    ids=[
        "correct-credentials",
        "wrong-password",
        "unknown-user",
        "case-insensitive",
        "whitespace-trimmed",
    ],
)
def test_login_combinations(store, username, password, expected_ok):
    """
    Concepts:
    - Parametrize for truth-table testing
    - Covers multiple logical branches in one test
    """
    create_account("login_user", "password123", store)
    result = login(username, password, store)
    assert (result is not None) is expected_ok
# -------------------------------------------------------------------
# NEGATIVE / EDGE CASE TESTS
# -------------------------------------------------------------------
@pytest.mark.login
@pytest.mark.parametrize(
    "username,password",
    [
        ("", "password123"),
        ("   ", "password123"),
        ("login_user", ""),
        ("login_user", "   "),
        (None, "password123"),
        ("login_user", None),
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
def test_login_invalid_inputs(store, username, password):
    """
    Concepts:
    - Defensive validation testing
    - Ensures login fails safely
    """
    create_account("login_user", "password123", store)
    result = login(username, password, store)
    assert result is None
@pytest.mark.login
def test_login_does_not_mutate_store(store, registered_user):
    """
    Concepts:
    - Regression test
    - Ensures login is read-only
    """
    before = store.get_by_user("login_user")
    login("login_user", "password123", store)
    after = store.get_by_user("login_user")
    assert before.account_id == after.account_id
    assert before.password_hash == after.password_hash
# -------------------------------------------------------------------
# MULTI-USER SCENARIOS
# -------------------------------------------------------------------
@pytest.mark.login
def test_login_with_multiple_users(store, registered_user, another_user):
    """
    Concepts:
    - Multiple fixtures
    - Isolation between users
    """
    user1 = login("login_user", "password123", store)
    user2 = login("other_user", "otherpass", store)
    assert user1.account_id != user2.account_id
    assert user1.username == "login_user"
    assert user2.username == "other_user"
@pytest.mark.login
def test_login_wrong_user_password_pair(store, registered_user, another_user):
    """
    Concepts:
    - Cross-user credential validation
    """
    result = login("login_user", "otherpass", store)
    assert result is None
# -------------------------------------------------------------------
# MONKEYPATCH TESTS
# -------------------------------------------------------------------
@pytest.mark.login
class TestLoginWithMonkeypatch:
    """
    Tests demonstrating monkeypatch usage for login service.
    """
    def test_login_store_lookup_failure(self, store, monkeypatch):
        """
        Concepts:
        - monkeypatch to simulate backend failure
        - Error propagation behavior
        """
        def broken_get_by_user(*args, **kwargs):
            raise RuntimeError("Database unavailable")
        monkeypatch.setattr(store, "get_by_user", broken_get_by_user)
        with pytest.raises(RuntimeError):
            login("login_user", "password123", store)
    def test_login_returns_none_when_store_returns_none(self, store, monkeypatch):
        """
        Concepts:
        - monkeypatch to control dependency behavior
        """
        def fake_get_by_user(username):
            return None
        monkeypatch.setattr(store, "get_by_user", fake_get_by_user)
        result = login("login_user", "password123", store)
        assert result is None
# -------------------------------------------------------------------
# DOCUMENTED FUTURE BEHAVIOR
# -------------------------------------------------------------------
@pytest.mark.login
@pytest.mark.xfail(reason="Account lockout after multiple failures not implemented yet")
def test_login_account_lockout_future(store):
    """
    Concepts:
    - xfail for planned security feature
    """
    create_account("secure_user", "pw", store)
    # Simulate multiple failed attempts
    login("secure_user", "bad1", store)
    login("secure_user", "bad2", store)
    login("secure_user", "bad3", store)
    # Future behavior: account should be locked
    assert login("secure_user", "pw", store) is None