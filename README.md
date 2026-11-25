# SplitBill

A full-stack expense-sharing application built with **FastAPI, PostgreSQL, and Next.js**. Users can view their groups, record shared expenses, split costs equally or by exact amounts, and see each member's net balance.

> **Demo project:** The selected user is identified by an `X-User` request header. This is not production authentication.

## Features

- Select a demo user and view the groups they belong to.
- View group members, active expenses, individual shares, and net balances.
- Add expenses with **Equal Split** or **Exact Split**, with a live preview.
- Prevent duplicate expense creation using an `Idempotency-Key`.
- Allow only the original payer to **soft-delete** an expense.
- Use a responsive dashboard with loading, validation, error, and retry states.

## Tech Stack

| Layer | Technologies |
| --- | --- |
| Frontend | Next.js (App Router), React, TypeScript, Tailwind CSS |
| Backend | Python 3.13, FastAPI, Pydantic, SQLAlchemy |
| Database | PostgreSQL 16, Psycopg |
| Migrations | Alembic |
| Local infrastructure | Docker Compose |
| Testing and quality | Pytest, FastAPI TestClient, Ruff, TypeScript, ESLint |

## Project Structure

```text
splitbill/
├── backend/
│   ├── app/
│   │   ├── routers/          # HTTP endpoints
│   │   ├── schemas/          # Request/response validation
│   │   ├── services/         # Business rules and calculations
│   │   ├── repositories/     # Database access
│   │   ├── models.py         # SQLAlchemy models
│   │   └── main.py
│   ├── alembic/              # Database migrations
│   ├── tests/                # Backend tests
│   ├── seed.py               # Demo users and groups
│   └── .env.example
├── frontend/
│   ├── src/app/              # Next.js App Router
│   ├── src/components/       # UI components
│   ├── src/lib/              # Formatting utilities
│   └── .env.example
├── docker-compose.yml
├── README.md
└── AI_NOTES.md
```

## Getting Started (Windows / PowerShell)

**Prerequisites:** Git, Docker Desktop with Compose, Python 3.13, and a Node.js version supported by the installed Next.js release.

### 1. Clone and start PostgreSQL

```powershell
git clone https://github.com/Bishxxp/splitbill.git
cd splitbill
docker compose up -d db
```

### 2. Run the backend

Open a terminal at the repository root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `backend/.env` and set `DATABASE_URL` to match the local credentials and port in `docker-compose.yml`. For the development configuration used in this project:

```dotenv
DATABASE_URL=postgresql+psycopg://splitbill:local_dev_password@127.0.0.1:5432/splitbill
```

Then migrate, seed a **fresh** database, and start the API:

```powershell
python -m alembic upgrade head
python seed.py
python -m uvicorn app.main:app --reload
```

API documentation: **http://localhost:8000/docs**

### 3. Run the frontend

Open another terminal at the repository root:

```powershell
cd frontend
npm ci
Copy-Item .env.example .env.local
npm run dev
```

Confirm `frontend/.env.local` contains:

```dotenv
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Open **http://localhost:3000**. Restart the Next.js dev server after changing `.env.local`.

> On macOS/Linux, replace PowerShell-specific activation/copy commands with `source .venv/bin/activate` and `cp`. Never commit `.env` or `.env.local`.

### Demo users and groups

| Group | Members |
| --- | --- |
| Chiang Mai trip | `alice`, `bob`, `carol` |
| Office lunch | `bob`, `dan` |

Choose a **Current User**, select a group, then add or inspect expenses. A user sees only their own groups.

## API Reference

Requests use the demo header `X-User: alice` (or another seeded user). Expense creation also requires a unique `Idempotency-Key` header.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/groups` | List groups for the selected user |
| `GET` | `/groups/{group_id}` | Get group details and members |
| `GET` | `/groups/{group_id}/expenses` | List active expenses |
| `POST` | `/groups/{group_id}/expenses` | Create an expense |
| `DELETE` | `/groups/{group_id}/expenses/{expense_id}` | Soft-delete an expense (payer only) |
| `GET` | `/groups/{group_id}/balances` | Get member net balances |

Example **Equal Split** request body:

```json
{
  "description": "Dinner",
  "paid_by": "alice",
  "amount": "100.00",
  "split": {
    "type": "equal",
    "members": ["alice", "bob", "carol"]
  }
}
```

Resulting shares: **alice 33.34, bob 33.33, carol 33.33**.

Example **Exact Split** request body:

```json
{
  "description": "Lunch",
  "paid_by": "bob",
  "amount": "100.00",
  "split": {
    "type": "exact",
    "shares": {"alice": "50.00", "bob": "30.00", "carol": "20.00"}
  }
}
```

Example balances response for **only** the 100.00 THB Dinner expense above:

```json
{
  "group_id": 1,
  "balances": [
    {"username": "alice", "balance": "66.66"},
    {"username": "bob", "balance": "-33.33"},
    {"username": "carol", "balance": "-33.33"}
  ]
}
```

Positive balances indicate money owed **to** a member; negative balances indicate money the member owes.

## Key Design Decisions

### 403 vs 404

- **403 Forbidden:** The user is recognized but is not a member of the group, or tries to delete an expense paid by someone else.
- **404 Not Found:** The requested group/expense does not exist, or an expense has already been deleted.

The frontend hides deletion controls from non-payers for usability, but the **backend checks permissions independently**. Returning 403 to non-members gives explicit feedback, while a production system might prefer 404 to avoid disclosing a group's existence.

### Money and remaining satang

Amounts are stored using PostgreSQL **`NUMERIC(12,2)`** and handled with Python **`Decimal`**. For Equal Split, the amount is converted to integer satang, divided evenly, and any remainder is distributed one satang at a time in the specified member order. For example, 100.00 / 3 = **33.34 + 33.33 + 33.33**. The frontend previews this calculation; the backend validates the submitted expense.

### Balances

```text
net_balance = amount_paid_by_member - total_shares_assigned_to_member
```

Only active (non-deleted) expenses are included. For each group, the sum of net balances is zero.

### Idempotency

Expense creation requires an `Idempotency-Key`. A unique database constraint on **`(group_id, idempotency_key)`** prevents two expense rows from using the same key within a group. Repeating the same POST request with the same key returns the existing expense instead of creating another one. This was manually verified using two requests that both returned expense ID `9`.

### Soft delete

Deletion updates `is_deleted` to `true` instead of removing the row. Deleted records are excluded from expense lists and balance calculations; only the original payer can delete an expense.

## Testing

### Prepare the test database (one-time setup)

From the repository root, create a **separate** database:

```powershell
docker compose exec db psql -U splitbill -d postgres -c "CREATE DATABASE splitbill_test;"
```

From `backend/`, with the virtual environment active, apply migrations to the test database:

```powershell
$env:DATABASE_URL = "postgresql+psycopg://splitbill:local_dev_password@127.0.0.1:5432/splitbill_test"
python -m alembic upgrade head
Remove-Item Env:\DATABASE_URL
```

> The test fixtures reset data in `splitbill_test`. Never point automated tests at your development database. If the database already exists, skip its creation step.

### Backend checks (`backend/`)

```powershell
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
```

Backend tests exercise splitting rules, validation, API access, balances, idempotency, and soft deletion. An earlier development run reported **27 passing tests**; rerun the suite before submission.

### Frontend checks (`frontend/`)

```powershell
npx tsc --noEmit
npm run lint
npm run build
```

### Manual end-to-end checks

1. Switch between Alice, Bob, Carol, and Dan; confirm group visibility.
2. Add an Equal Split of 100.00 across three members; verify 33.34 / 33.33 / 33.33.
3. Add an Exact Split; verify the shares sum to the expense amount.
4. Confirm that only the payer sees the Delete button and that the API rejects unauthorized deletion.
5. Delete an expense; verify the list and balances update, and `is_deleted = true` in PostgreSQL.
6. Repeat a POST with the same idempotency key; verify it returns the same expense ID.
7. Stop the API, confirm the error state, restart it, and use Retry.

These are **manual browser/API checks**, not automated browser E2E tests.

## Troubleshooting

| Problem | What to check |
| --- | --- |
| Port `5432` is in use | Stop the other PostgreSQL instance or update the Compose port and `DATABASE_URL`. |
| Database connection fails | Verify `docker compose ps` and `backend/.env`; use `127.0.0.1` for the local host. |
| Browser reports `Failed to fetch` | Make sure FastAPI runs on port 8000 and Next.js uses the correct API URL. |
| Frontend environment changes do not apply | Restart `npm run dev`. |
| Tests affect unexpected records | Check the test-database configuration before running Pytest. |

## Known Limitations and Next Steps

- **Demo identity only:** `X-User` is not secure authentication. Add authenticated sessions or tokens before production use.
- **Fixed demo groups:** Group creation, invitations, and membership editing are not implemented.
- **No settlement workflow:** The app calculates balances but does not record repayments or transfer money.
- **THB only:** Multi-currency handling is out of scope.
- **No automated browser E2E suite:** Add Playwright and CI (e.g., GitHub Actions) as future work.
- **Idempotency policy:** Further document and test behavior when a key is reused with a *different* payload, including concurrent cases.

## AI Assistance

AI was used during development for technical explanations, implementation guidance, debugging, and testing support. See [`AI_NOTES.md`](AI_NOTES.md) for the prompts, errors caught and corrected, and code-review process.

## Submission

- The repository contains separate `backend/` and `frontend/` directories and incremental Git history.

## Author

Kunnagirt Nantipa
