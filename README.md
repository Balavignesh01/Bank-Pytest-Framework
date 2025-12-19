# MIT Bank - Advanced Pytest + UI

This project is a demo banking application focused on Pytest based testing framework
with an interactive UI

## Features

### Domain
- Create account (username + password) → generates **account ID**
- Login using **account ID + password**
- Edit account details with admin actions (username, password)
- Transfer funds between accounts
- JSON-based storage for simplicity (file-based)

### UI
- Modern light theme 
- Screens:
  - Login
  - Create Account
  - Account Details
  - Transfer Funds
  - Admnin
  - Logout(same for all sessions)
- Smooth navigation between screens

### Pytest (Advanced Level)
- Layered fixtures using `tmp_path`
- Separated service layer for easier testing
- Parametrized tests
- Custom exceptions and negative tests
- Monkeypatch-based failure simulation
- Integration (end-to-end) tests tying together:
  - register → login → edit(admin) → transfer

## Project Layout

```bash
├── .pytest_cache/
├── __pycache__/
├── bank/
│   ├── __pycache__/
│   ├── models/
│   │   ├── __pycache__
│   │   ├── __init__.py
│   │   ├── transaction.py
│   │   ├── account.py
│   │   └── store.py
│   ├── services/
│   │   ├── __pycache__
│   │   ├── __init__.py
│   │   ├── account_service.py
│   │   ├── login_service.py
│   │   ├── register_service.py
│   │   └── transfer_service.py
│   └── __init__.py
│── data/
│── react_ui
│   ├── node_modules/
│   ├── src
│   │    ├── App.jsx
│   │    ├── main.jsx
│   │    └── style.css
│   ├── index
│   ├── package
│   ├── package-lock
│   └── vite.config
├── tests/
│   ├── __pycache__
│   ├── conftest.py
│   ├── test_account_service.py
│   ├── test_login_service.py
│   ├── test_register_service.py
│   └── test_transfer_service.py
│── .gitignore
│── pytest.ini
│── README.md
│── requirements.txt
│── run_tests.py
└── test_server.py
```
## Running Tests
This cmd ups the server for pytest and this port listens from the UI for actions 
```bash
pip install -r requirements.txt

run in root : python test_server.py 
```
## Running the UI
This folder contains a React single–page application that mirrors the existing
banking flow (login, create account, transfer funds, admin) but uses
local browser storage.

From this `react_ui` folder:

```bash
npm install
npm run dev
```
## Admin login credentials 
Admin demo login:

- Account ID: `ADMIN1`
- Password: `admin123`