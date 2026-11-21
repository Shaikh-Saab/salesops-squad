# Seed data (mock only)

`generate_data.py` creates repeatable, **fictional** data for the SalesOps Squad agents. It uses a fixed random seed (42) and a fixed reference date (21 Nov 2026), so every run produces the same files.

Company names are Microsoft's well-known fictional sample names (Contoso, Fabrikam, ...). Owner names come from Faker. The only email addresses are `example.com` placeholders.

## Run it

**macOS / Linux (Terminal)**
```bash
cd seed
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python generate_data.py
```

**Windows (PowerShell)**
```powershell
cd seed
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python generate_data.py
```
If PowerShell blocks the activate script, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.

## What it writes

| File | Rows | Purpose |
| --- | --- | --- |
| `output/accounts.csv` | 15 | Import into Dataverse / Supabase |
| `output/opportunities.csv` | 30 | Import |
| `output/products.csv` | 20 | Import |
| `output/quotes.csv` | headers only | Created empty; the Quote Agent writes rows |
| `output/email_drafts.csv` | headers only | Created empty; the Follow-up Agent writes rows |
| `output/agent_runs.csv` | headers only | Created empty; the Audit Logger flow writes rows |
| `../dashboard/public/data/agent_runs.csv` | 62 | **Simulated** demo runs for the dashboard |
| `../dashboard/public/data/email_drafts.csv` | 10 | **Simulated** demo drafts for the dashboard |

## Built-in edge cases (the tests depend on these)

1. `SKU-12` (Sales Cloud Pro licence) has `max_discount_pct = 10`, so a 60% discount breaks policy.
2. `OPP-003` (Contoso) is overdue: close date 2026-11-09 and still in Qualification.
3. `Trey Research` has a stale `last_contact_date` (2026-07-04) and one stalled deal.
4. `Acme Dynamics` is deliberately **not** in the accounts table (used for the "not found" test).
5. Health mix: 7 green, 5 amber, 3 red.
6. `Contoso` has 3 open opportunities, and `SKU-12` exists.

There is one deviation from "2 to 3 opportunities per account": with exactly 30 opportunities and Contoso holding 3, Trey Research has 1. That fits its role as the stale account.

## Import into Dataverse

1. Go to make.powerapps.com, pick your dev environment, then **Tables → New table → Import → Import data from Excel or .CSV**.
2. Import one CSV per table, using the file name as the table name (`accounts`, `opportunities`, ...). Set the ID column as the primary name, or keep the default primary name and map the ID to a text column.
3. Check the column types: `value`, `list_price`, `total`, `est_cost_usd` → Decimal; `qty`, `min_qty`, `max_discount_pct`, `tokens_*`, `latency_ms` → Whole number; dates → Date only.
4. For `quotes`, `email_drafts` and `agent_runs`, import the headers-only files (or create the columns by hand) so the agents and flows have a table to write to.

## Import into Supabase

1. In the Table Editor, create each table with the columns from the CSV header (or use **New table → Import data from CSV**, which creates columns for you).
2. Enable Row Level Security. For the public dashboard, add a read-only `select` policy on `agent_runs` and `email_drafts` only.
3. Put `SUPABASE_URL` and `SUPABASE_ANON_KEY` in your local `.env` (never commit it).
