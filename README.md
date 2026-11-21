# SalesOps Squad + Agent Control Tower (demo)

> Portfolio project. **Mock data only**: every company, person and deal is fictional.
> Cost, token, risk and latency figures are **simulated estimates**, not Microsoft billing or Agent 365 output.

A multi-agent sales assistant built in Microsoft Copilot Studio (an orchestrator plus three specialist agents), with a small governance and cost dashboard built in code.

## Status

Work in progress. Sections below are placeholders.

## Problem

_TBD_

## Architecture

_TBD (diagram)_

- **Orchestrator (SalesOps Lead)** delegates to:
  - Lead Research Agent
  - Quote Agent
  - Follow-up Agent (human approval required before anything is sent)
- **Audit Logger flow** writes one row per agent run to `agent_runs`.
- **Agent Control Tower (demo)** dashboard reads `agent_runs` and `email_drafts`.

## Repo layout

| Path | Contents |
| --- | --- |
| `docs/agents/` | Agent descriptions and instructions, ready to paste into Copilot Studio |
| `docs/` | Test prompts and scoring sheet |
| `seed/` | Mock-data generator (Python + Faker) and CSVs |
| `dashboard/` | Agent Control Tower (demo) web app |
| `flows/` | Power Automate flow descriptions and screenshots (tenant IDs removed) |
| `tests/` | Optional test runner scripts |

## Setup

1. Copy `.env.example` to `.env` and fill in values locally. Never commit `.env`.
2. _Seed data and dashboard steps TBD._

## Results

_TBD (routing accuracy, policy compliance, audit coverage)_

## GA vs preview vs mocked

_TBD_
