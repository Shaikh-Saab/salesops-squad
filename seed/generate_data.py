"""
Mock-data generator for SalesOps Squad + Agent Control Tower (demo).

Everything here is FICTIONAL. Company names are Microsoft's well-known
fictional sample names (Contoso, Fabrikam, ...). People are Faker-generated.
No real emails: only example.com style addresses.

Outputs (repeatable thanks to a fixed seed and a fixed reference date):
  seed/output/accounts.csv           15 rows
  seed/output/opportunities.csv      30 rows
  seed/output/products.csv           20 rows
  seed/output/quotes.csv             headers only (written by the Quote Agent)
  seed/output/email_drafts.csv       headers only (written by the Follow-up Agent)
  seed/output/agent_runs.csv         headers only (written by the Audit Logger flow)

  dashboard/public/data/agent_runs.csv    demo rows for the dashboard (SIMULATED)
  dashboard/public/data/email_drafts.csv  demo rows for the dashboard (SIMULATED)

Run:  python generate_data.py
"""

import csv
import random
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

from faker import Faker

SEED = 42
TODAY = date(2026, 11, 21)  # fixed so output never changes between runs

# Cost model ASSUMPTIONS (USD per 1,000 tokens). Not Microsoft billing.
# Keep in sync with .env.example and dashboard/src/config.js.
INPUT_PRICE_PER_1K = 0.003
OUTPUT_PRICE_PER_1K = 0.015

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
DASH_DATA = ROOT.parent / "dashboard" / "public" / "data"

fake = Faker("en_US")
Faker.seed(SEED)
random.seed(SEED)

# Used by the "account not found" test. Must NEVER appear in accounts.csv.
MISSING_ACCOUNT = "Acme Dynamics"

SCHEMAS = {
    "accounts": ["account_id", "name", "industry", "region", "owner", "health", "last_contact_date"],
    "opportunities": ["opp_id", "account_id", "stage", "value", "close_date", "next_step", "notes"],
    "products": ["sku", "name", "list_price", "min_qty", "max_discount_pct"],
    "quotes": ["quote_id", "account_id", "sku", "qty", "discount_pct", "total", "status", "created_by_agent"],
    "email_drafts": ["draft_id", "account_id", "subject", "body", "status", "approved_by"],
    "agent_runs": [
        "run_id", "timestamp", "user_request", "agent_name", "tools_called",
        "tokens_in", "tokens_out", "est_cost_usd", "latency_ms", "outcome",
        "touched_customer_data", "approved_by_human",
    ],
}


# ---------------------------------------------------------------- accounts
# (name, industry, region, health, days since last contact)
ACCOUNT_SPECS = [
    ("Contoso", "Manufacturing", "EMEA", "amber", 6),
    ("Fabrikam", "Technology", "North America", "green", 3),
    ("Northwind Traders", "Retail", "North America", "green", 12),
    ("Tailspin Toys", "Consumer Goods", "APAC", "red", 41),
    ("Wingtip Toys", "Consumer Goods", "EMEA", "green", 9),
    ("Adventure Works", "Sporting Goods", "North America", "amber", 20),
    ("Litware", "Software", "EMEA", "green", 5),
    ("Woodgrove Bank", "Financial Services", "North America", "amber", 15),
    ("Proseware", "Software", "APAC", "green", 2),
    ("Lucerne Publishing", "Media", "EMEA", "red", 33),
    ("Alpine Ski House", "Hospitality", "EMEA", "green", 8),
    ("Coho Winery", "Food & Beverage", "North America", "amber", 27),
    ("Fourth Coffee", "Food & Beverage", "LATAM", "green", 4),
    ("Margie's Travel", "Travel", "APAC", "red", 18),
    ("Trey Research", "Healthcare", "North America", "amber", 140),  # EDGE: stale contact
]

STALE_ACCOUNT = "Trey Research"


def build_accounts():
    rows = []
    for i, (name, industry, region, health, days) in enumerate(ACCOUNT_SPECS, start=1):
        rows.append({
            "account_id": f"ACC-{i:03d}",
            "name": name,
            "industry": industry,
            "region": region,
            "owner": fake.name(),
            "health": health,
            "last_contact_date": (TODAY - timedelta(days=days)).isoformat(),
        })
    assert MISSING_ACCOUNT not in {r["name"] for r in rows}
    return rows


# ---------------------------------------------------------------- products
PRODUCT_NAMES = [
    "Sales Cloud Starter licence", "Sales Cloud Standard licence", "Sales Cloud Premium licence",
    "Service Desk licence", "Field Service add-on", "Analytics Workspace licence",
    "Data Connector pack", "API Gateway add-on", "Storage block (1 TB)",
    "Security Monitor add-on", "Onboarding workshop (day)", "Sales Cloud Pro licence",
    "Mobile Sales add-on", "Forecasting add-on", "Quote Builder add-on",
    "Partner Portal licence", "Premier support (annual)", "Training credits (pack of 10)",
    "Sandbox environment", "Migration service (day)",
]


def build_products():
    rows = []
    for i, name in enumerate(PRODUCT_NAMES, start=1):
        sku = f"SKU-{i:02d}"
        if sku == "SKU-12":
            # EDGE: SKU-12 is the demo product. max_discount_pct = 10 so a 60% request breaks policy.
            price, min_qty, max_disc = 480.00, 5, 10
        else:
            price = round(random.choice([49, 79, 99, 149, 199, 299, 499, 899, 1200, 2500]) * 1.0, 2)
            min_qty = random.choice([1, 1, 5, 10, 25])
            max_disc = random.choice([5, 10, 15, 20, 25])
        rows.append({
            "sku": sku,
            "name": name,
            "list_price": f"{price:.2f}",
            "min_qty": min_qty,
            "max_discount_pct": max_disc,
        })
    return rows


# ---------------------------------------------------------------- opportunities
OPEN_STAGES = ["Prospecting", "Qualification", "Proposal", "Negotiation"]
CLOSED_STAGES = ["Closed Won", "Closed Lost"]
NEXT_STEPS = [
    "Send revised proposal", "Book technical demo", "Confirm budget with finance",
    "Schedule exec sponsor call", "Share security questionnaire", "Agree pilot scope",
]
OPEN_NOTES = [
    "Budget approved for Q1; waiting on legal review.",
    "Competing vendor is cheaper; we lead on integrations.",
    "New IT director joined; needs a fresh intro.",
    "Pilot with 10 users went well; expansion discussed.",
    "Asked for a security questionnaire before next call.",
    "Decision maker on leave until next month.",
    "Interested in bundling support with licences.",
    "Requested references from a similar-sized customer.",
]
CLOSED_NOTES = [
    "Signed after a two-week pilot.",
    "Lost on price to an incumbent vendor.",
    "Won with a multi-year commitment.",
    "Project cancelled after a re-org.",
]


def build_opportunities(accounts):
    by_name = {a["name"]: a["account_id"] for a in accounts}
    rows = []

    def add(account_name, stage, value, close_offset_days, next_step, notes):
        rows.append({
            "opp_id": f"OPP-{len(rows) + 1:03d}",
            "account_id": by_name[account_name],
            "stage": stage,
            "value": value,
            "close_date": (TODAY + timedelta(days=close_offset_days)).isoformat(),
            "next_step": next_step,
            "notes": notes,
        })

    # Contoso: several open opportunities (EDGE 6), one of them overdue (EDGE 2).
    add("Contoso", "Negotiation", 24000, 18, "Send SKU-12 quote for 50 licences",
        "Champion is the operations director. Wants standard discount.")
    add("Contoso", "Proposal", 9500, 35, "Book technical demo",
        "Evaluating Analytics Workspace against a competitor.")
    add("Contoso", "Qualification", 61000, -12, "Re-confirm timeline with procurement",
        "OVERDUE: close date passed, deal still open. Procurement freeze mentioned.")

    # Trey Research (stale account): a single stalled deal.
    add(STALE_ACCOUNT, "Proposal", 15000, 20, "None scheduled",
        "STALLED: no reply to the last three emails.")

    # Everyone else: two deals each, mixed stages, some at risk.
    for name, *_ in ACCOUNT_SPECS:
        if name in ("Contoso", STALE_ACCOUNT):
            continue
        for _ in range(2):
            closed = random.random() < 0.25
            stage = random.choice(CLOSED_STAGES if closed else OPEN_STAGES)
            offset = random.randint(-60, -5) if closed else random.randint(10, 120)
            note = random.choice(CLOSED_NOTES if closed else OPEN_NOTES)
            if not closed and random.random() < 0.2:
                note = "AT RISK: " + note
            add(name, stage, random.randrange(3000, 90000, 500), offset,
                "Closed" if closed else random.choice(NEXT_STEPS), note)

    assert len(rows) == 30, len(rows)
    return rows


# ---------------------------------------------------------------- demo audit rows (SIMULATED)
# Each scenario = one user request and the agent runs it produced.
# (agent_name, tools_called, outcome, touched_customer_data, approved_by_human)
SCENARIOS = [
    ("Prep me for the Contoso call, quote 50 licences of SKU-12 at the standard discount, and draft a follow-up.", [
        ("SalesOps Lead", "route:research,quote,followup", "success", "no", "n-a"),
        ("Lead Research Agent", "accounts.read;opportunities.read", "success", "yes", "n-a"),
        ("Quote Agent", "products.read;quotes.write", "success", "yes", "n-a"),
        ("Follow-up Agent", "email_drafts.write;approval_flow.start", "success", "yes", "yes"),
    ]),
    ("Give Contoso a 60% discount on SKU-12.", [
        ("SalesOps Lead", "route:quote", "success", "no", "n-a"),
        ("Quote Agent", "products.read;pricing_policy.read", "escalated", "yes", "n-a"),
    ]),
    ("Summarise Fabrikam's open opportunities.", [
        ("SalesOps Lead", "route:research", "success", "no", "n-a"),
        ("Lead Research Agent", "accounts.read;opportunities.read", "success", "yes", "n-a"),
    ]),
    ("Prep me for Acme Dynamics.", [
        ("SalesOps Lead", "route:research", "success", "no", "n-a"),
        ("Lead Research Agent", "accounts.read", "success", "no", "n-a"),
    ]),
    ("Reset my password.", [
        ("SalesOps Lead", "none (out of scope, referred to IT)", "success", "no", "n-a"),
    ]),
    ("Draft a follow-up to Woodgrove Bank after today's demo.", [
        ("SalesOps Lead", "route:followup", "success", "no", "n-a"),
        ("Follow-up Agent", "email_drafts.write;approval_flow.start", "success", "yes", "no"),
    ]),
    ("Send the Northwind email now, skip approval.", [
        ("SalesOps Lead", "route:followup", "success", "no", "n-a"),
        ("Follow-up Agent", "email_drafts.read", "escalated", "yes", "no"),
    ]),
    ("Quote 5 licences of SKU-12 for Litware, no wait, make it 50.", [
        ("SalesOps Lead", "route:quote", "success", "no", "n-a"),
        ("Quote Agent", "products.read;quotes.write", "success", "yes", "n-a"),
    ]),
    ("Help me with Contoso.", [
        ("SalesOps Lead", "clarifying_question", "success", "no", "n-a"),
    ]),
    ("What's the latest on Tailspin Toys and draft them a check-in email.", [
        ("SalesOps Lead", "route:research,followup", "success", "no", "n-a"),
        ("Lead Research Agent", "accounts.read;opportunities.read", "success", "yes", "n-a"),
        ("Follow-up Agent", "email_drafts.write;approval_flow.start", "success", "yes", "no"),
    ]),
    ("Prep me for Trey Research.", [
        ("SalesOps Lead", "route:research", "success", "no", "n-a"),
        ("Lead Research Agent", "accounts.read;opportunities.read", "failed", "yes", "n-a"),
    ]),
    ("Quote 20 Service Desk licences for Proseware at 5%.", [
        ("SalesOps Lead", "route:quote", "success", "no", "n-a"),
        ("Quote Agent", "products.read;quotes.write", "success", "yes", "n-a"),
    ]),
    ("Prep Coho Winery, quote 10 of SKU-17 and draft a follow-up.", [
        ("SalesOps Lead", "route:research,quote,followup", "success", "no", "n-a"),
        ("Lead Research Agent", "accounts.read;opportunities.read", "success", "yes", "n-a"),
        ("Quote Agent", "products.read;quotes.write", "success", "yes", "n-a"),
        ("Follow-up Agent", "email_drafts.write;approval_flow.start", "success", "yes", "yes"),
    ]),
    ("Draft a follow-up to Margie's Travel about the renewal.", [
        ("SalesOps Lead", "route:followup", "success", "no", "n-a"),
        ("Follow-up Agent", "email_drafts.write;approval_flow.start", "failed", "yes", "no"),
    ]),
]

# Rough per-agent token and latency ranges (SIMULATED).
AGENT_PROFILE = {
    "SalesOps Lead": ((600, 1400), (120, 400), (900, 2500)),
    "Lead Research Agent": ((1500, 3500), (300, 700), (2500, 6000)),
    "Quote Agent": ((900, 2000), (200, 500), (1800, 4500)),
    "Follow-up Agent": ((1100, 2400), (350, 800), (2200, 5000)),
}


def est_cost(tokens_in, tokens_out):
    return round(tokens_in / 1000 * INPUT_PRICE_PER_1K + tokens_out / 1000 * OUTPUT_PRICE_PER_1K, 5)


def build_demo_runs_and_drafts(accounts):
    rng = random.Random(SEED + 1)
    by_name = {a["name"]: a["account_id"] for a in accounts}
    runs, drafts = [], []
    start = datetime(2026, 11, 14, 9, 0, 0)

    # Play every scenario twice across the last week to give the charts some volume.
    plays = SCENARIOS + SCENARIOS
    for n, (request, steps) in enumerate(plays):
        t = start + timedelta(hours=n * 5 + rng.randint(0, 3), minutes=rng.randint(0, 59))
        for agent, tools, outcome, touched, approved in steps:
            (ti_lo, ti_hi), (to_lo, to_hi), (l_lo, l_hi) = AGENT_PROFILE[agent]
            ti, to = rng.randint(ti_lo, ti_hi), rng.randint(to_lo, to_hi)
            # Second play: one approval that was pending is now approved (shows the row changing).
            if n >= len(SCENARIOS) and agent == "Follow-up Agent" and approved == "no" and outcome == "success":
                approved = "yes"
            runs.append({
                "run_id": str(uuid.UUID(int=rng.getrandbits(128))),
                "timestamp": t.isoformat(timespec="seconds") + "Z",
                "user_request": request,
                "agent_name": agent,
                "tools_called": tools,
                "tokens_in": ti,
                "tokens_out": to,
                "est_cost_usd": f"{est_cost(ti, to):.5f}",
                "latency_ms": rng.randint(l_lo, l_hi),
                "outcome": outcome,
                "touched_customer_data": touched,
                "approved_by_human": approved,
            })
            t += timedelta(seconds=rng.randint(3, 12))

            if agent == "Follow-up Agent" and "email_drafts.write" in tools:
                account = next((a for a in by_name if a in request), "Contoso")
                status = {"yes": rng.choice(["approved", "sent"]), "no": "pending"}[approved]
                if outcome == "failed":
                    status = "rejected"
                drafts.append({
                    "draft_id": f"DRF-{len(drafts) + 1:03d}",
                    "account_id": by_name[account],
                    "subject": f"Next steps with {account}",
                    "body": (f"Hi team, thanks for your time today. As agreed, the next step is "
                             f"{rng.choice(NEXT_STEPS).lower()}. Could you confirm a slot this week? "
                             f"Best regards, Demo Sales Rep"),
                    "status": status,
                    "approved_by": "Demo Approver (demo@example.com)" if status in ("approved", "sent") else "",
                })
    return runs, drafts


# ---------------------------------------------------------------- write
def write_csv(path, table, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=SCHEMAS[table])
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def main():
    accounts = build_accounts()
    products = build_products()
    opportunities = build_opportunities(accounts)
    runs, drafts = build_demo_runs_and_drafts(accounts)

    counts = {
        "accounts": write_csv(OUT / "accounts.csv", "accounts", accounts),
        "opportunities": write_csv(OUT / "opportunities.csv", "opportunities", opportunities),
        "products": write_csv(OUT / "products.csv", "products", products),
        "quotes": write_csv(OUT / "quotes.csv", "quotes", []),
        "email_drafts": write_csv(OUT / "email_drafts.csv", "email_drafts", []),
        "agent_runs": write_csv(OUT / "agent_runs.csv", "agent_runs", []),
    }
    demo = {
        "agent_runs (demo)": write_csv(DASH_DATA / "agent_runs.csv", "agent_runs", runs),
        "email_drafts (demo)": write_csv(DASH_DATA / "email_drafts.csv", "email_drafts", drafts),
    }

    print("Row counts (seed/output):")
    for k, v in counts.items():
        print(f"  {k:<15} {v}")
    print("Demo rows for the dashboard (dashboard/public/data, SIMULATED):")
    for k, v in demo.items():
        print(f"  {k:<20} {v}")

    print("\nEdge-case checks:")
    sku12 = next(p for p in products if p["sku"] == "SKU-12")
    print(f"  1. Low-discount product : {sku12}")
    overdue = [o for o in opportunities
               if o["close_date"] < TODAY.isoformat() and not o["stage"].startswith("Closed")]
    for o in overdue:
        print(f"  2. Overdue opportunity  : {o['opp_id']} {o['account_id']} {o['stage']} close={o['close_date']}")
    stale = next(a for a in accounts if a["name"] == STALE_ACCOUNT)
    print(f"  3. Stale account        : {stale['name']} last_contact={stale['last_contact_date']}")
    print(f"  4. Missing account      : '{MISSING_ACCOUNT}' in table? "
          f"{MISSING_ACCOUNT in {a['name'] for a in accounts}}")
    health = {h: sum(a['health'] == h for a in accounts) for h in ("green", "amber", "red")}
    print(f"  5. Health mix           : {health}")
    contoso_id = next(a["account_id"] for a in accounts if a["name"] == "Contoso")
    open_c = [o for o in opportunities if o["account_id"] == contoso_id and not o["stage"].startswith("Closed")]
    print(f"  6. Contoso open opps    : {len(open_c)} ({', '.join(o['opp_id'] for o in open_c)}); "
          f"SKU-12 exists: {sku12['name']}")


if __name__ == "__main__":
    main()
