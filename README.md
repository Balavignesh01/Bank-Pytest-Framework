# ABC Bank - Advanced Pytest + Tkinter UI Project

This project is a demo banking application focused on **Pytest testing patterns**
with a **modern light-theme Tkinter UI**.

## Features

### Domain
- Create account (username + password) → generates **account ID**
- Login using **account ID + password**
- Edit account details (username, password)
- Transfer funds between accounts
- JSON-based storage for simplicity (file-based)

### UI (Tkinter)
- Modern light theme with ttk styling
- Screens:
  - Login
  - Register (Create Account)
  - Dashboard (view balance and actions)
  - Edit Account
  - Transfer Funds
- Smooth navigation between screens

### Pytest (Advanced Level)
- Layered fixtures using `tmp_path`
- Separated service layer for easier testing
- Parametrized tests
- Custom exceptions and negative tests
- Monkeypatch-based failure simulation
- Integration (end-to-end) tests tying together:
  - register → login → edit → transfer

## Project Layout

```bash
banking_pytest_advanced_ui/
├── bank/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── account.py
│   │   └── store.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── account_service.py
│   │   ├── login_service.py
│   │   ├── register_service.py
│   │   └── transfer_service.py
│   └── ui/
│       ├── __init__.py
│       ├── theme.py
│       ├── main_app.py
│       └── screens/
│           ├── __init__.py
│           ├── dashboard_screen.py
│           ├── edit_screen.py
│           ├── login_screen.py
│           ├── register_screen.py
│           └── transfer_screen.py
├── tests/
│   ├── conftest.py
│   ├── test_account_service.py
│   ├── test_integration_flow.py
│   ├── test_login_service.py
│   ├── test_register_service.py
│   ├── test_store_and_ids.py
│   ├── test_transfer_service.py
│   └── test_failure_monkeypatch.py
├── pytest.ini
├── requirements.txt
└── run_app.py
```

## Running Tests

```bash
pip install -r requirements.txt
pytest -q
```

## Running the UI

```bash
python run_app.py
```

> Note: Tkinter requires a desktop / GUI environment to display windows.
