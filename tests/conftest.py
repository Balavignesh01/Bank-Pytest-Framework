# tests/conftest.py
# Advanced concepts included:
# - Isolated JSON-backed store per test
# - Teardown validation (JSON integrity check)
# - Parametrized fixtures
# - Multi-user scenario fixture
# - UI state fixtures injected via test_server (localStorage bridge)
# - Yield fixtures for setup/teardown control
import json
import os
from pathlib import Path
import pytest
from bank.models.store import AccountStore
# -------------------------------------------------------------------
# CORE STORE FIXTURE (Backend / Unit tests)
# -------------------------------------------------------------------
@pytest.fixture
def store(tmp_path, monkeypatch):
    """
    Isolated AccountStore for each test.
    Uses a temp JSON file and validates JSON integrity on teardown.
    """
    db_file = tmp_path / "accounts.json"
    monkeypatch.setenv("ACCOUNTS_JSON_PATH", str(db_file))
    st = AccountStore()
    yield st  # ----- test executes here -----
    # Teardown: ensure persisted JSON is always valid
    if db_file.exists():
        with open(db_file, "r", encoding="utf-8") as f:
            json.load(f)
# -------------------------------------------------------------------
# PARAMETRIZED FIXTURE (General test reuse)
# -------------------------------------------------------------------
@pytest.fixture(params=["alice", "bob", "charlie"])
def username_set(request):
    """
    Parametrized username fixture.
    Useful for repetitive validation tests.
    """
    return request.param
# -------------------------------------------------------------------
# MULTI-USER STORE FIXTURE
# -------------------------------------------------------------------
@pytest.fixture
def multi_user_store(store):
    """
    Creates multiple users in the store.
    Used for multi-step and transfer scenarios.
    """
    from bank.services.register_service import create_account
    users = []
    for name in ["u1", "u2", "u3"]:
        users.append(create_account(name, "pw", store))

    return store, users
# -------------------------------------------------------------------
# UI STATE FIXTURES (Injected from React localStorage)
# Source: test_server.py → ENV variables
# -------------------------------------------------------------------
@pytest.fixture
def ui_accounts():
    """
    Snapshot of accounts coming from browser localStorage.
    Passed via test_server.py as UI_ACCOUNTS env variable.
    """
    raw = os.environ.get("UI_ACCOUNTS")
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        pytest.fail("UI_ACCOUNTS environment variable contains invalid JSON")
    if not isinstance(data, list):
        pytest.fail("UI_ACCOUNTS must be a list of account objects")
    return data
@pytest.fixture
def ui_session():
    """
    Active UI session snapshot from browser localStorage.
    Passed via test_server.py as UI_SESSION env variable.
    """
    raw = os.environ.get("UI_SESSION")
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        pytest.fail("UI_SESSION environment variable contains invalid JSON")
    if data is not None and not isinstance(data, dict):
        pytest.fail("UI_SESSION must be a JSON object or null")
    return data