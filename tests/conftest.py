# tests/conftest.py
# Advanced concepts added:
# - Auto JSON validity check after each test
# - Store snapshot fixture
# - Parametrized fixture for multiple users
# - Yield fixtures for teardown logic

import json
import os
from pathlib import Path
import pytest
from bank.models.store import AccountStore


@pytest.fixture
def store(tmp_path, monkeypatch):
    """
    Isolated AccountStore for each test.
    Includes teardown validation that accounts.json remains valid JSON.
    """
    db_file = tmp_path / "accounts.json"
    monkeypatch.setenv("ACCOUNTS_JSON_PATH", str(db_file))

    st = AccountStore()
    yield st  # --- test runs here ---

    # Teardown: verify JSON always valid
    with open(db_file, "r") as f:
        json.load(f)


@pytest.fixture(params=["alice", "bob", "charlie"])
def username_set(request):
    """
    Parametrized fixture used in multiple tests.
    """
    return request.param


@pytest.fixture
def multi_user_store(store):
    """
    Creates 3 users in the store — used for multi-step scenario testing.
    """
    from bank.services.register_service import create_account
    users = []
    for name in ["u1", "u2", "u3"]:
        users.append(create_account(name, "pw", store))
    return store, users
