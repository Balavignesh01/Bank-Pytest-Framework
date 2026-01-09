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
    db_file = tmp_path / "accounts.json"  # temporary json file path
    monkeypatch.setenv("ACCOUNTS_JSON_PATH", str(db_file))
    st = AccountStore()
    yield st  
    if db_file.exists():
        with open(db_file, "r", encoding="utf-8") as f:
            json.load(f) 

# -------------------------------------------------------------------
# UI STATE FIXTURES (Injected from React localStorage)
# -------------------------------------------------------------------
@pytest.fixture
def ui_accounts():

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