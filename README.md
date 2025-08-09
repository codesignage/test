# Cashier App (Flask + SQLite)

A simple cashier system with login/registration, role-based access (manager/cashier), sales entry, products, and reports.

## Features
- Email/password auth (register = cashier by default)
- Manager role can manage users and products
- Sales entry with automatic totals and change
- Reports: daily totals and product totals for Today, 7/30/365 days
- SQLite DB, sample seed data

## Quickstart

```bash
# From the workspace root
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run DB migrations and seed sample data
python -m cashier_app.seed

# Run the app
python -m cashier_app.app
```

Open http://localhost:5000

## Default logins
- Manager: manager@example.com / password123
- Cashiers: alice@example.com / password123, bob@example.com / password123

You can override the manager via env vars when seeding:

```bash
export MANAGER_EMAIL="your.email@example.com"
export MANAGER_PASSWORD="your-strong-password"
python -m cashier_app.seed
```

## Notes
- Database file is at `cashier_app/cashier.sqlite3`
- Change `SECRET_KEY` and `DATABASE_URL` via env vars in production
- Reports are basic; extend as needed (CSV export, date pickers, etc.)