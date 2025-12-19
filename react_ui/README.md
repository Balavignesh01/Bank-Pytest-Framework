# ABC Bank – React UI (banking_clean_flow/react_ui)

This folder contains a React single–page application that mirrors the existing
banking flow (login, create account, dashboard, transfer funds, admin) but uses
**local browser storage** instead of Tkinter and local text files.

## How to run the React UI

From this `react_ui` folder:

```bash
npm install
npm run dev
```

Then open the URL printed by Vite (usually http://localhost:5173).

## Notes

- Existing Python modules, services, and pytest tests are untouched in the main
  `banking_clean_flow` project.
- The React UI is purely for visual interaction and does **not** talk to the
  Python code or filesystem.
- Data is stored in `window.localStorage` under the key `bcf_accounts_v1`.

Admin demo login:

- Account ID: `ADMIN1`
- Password: `admin123`
