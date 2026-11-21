# Case study: SalesOps Squad + Agent Control Tower (demo)

*Draft. Sections marked TODO are filled in after the test run and demo recording.*
*All data is fictional. Cost and risk figures are simulated estimates, not Microsoft billing.*

## 1. Problem and users

Sales reps prepare for calls by jumping between the CRM, a price list, a discount policy and their inbox. Prep is slow, and discounts sometimes go out that break policy. **Users:** account executives preparing calls and quotes, and sales managers who need to see what the agents did and what it cost.

## 2. Why multi-agent

One request ("prep, quote, follow up") contains three jobs with **different data, permissions and approval rules**:

| Job | Data | Permission | Approval |
| --- | --- | --- | --- |
| Research | accounts, opportunities | read-only | none |
| Quote | products, quotes | read products, write draft quotes | above policy → escalate |
| Follow-up | email_drafts | write drafts only | named human before any send |

Separate specialists keep each agent's access small, make guardrails easy to state, and let each one be tested on its own. The orchestrator passes each specialist only the slice of context it needs.

## 3. Architecture

See the diagram in the [README](../README.md#architecture). In short: SalesOps Lead (orchestrator) → Lead Research / Quote / Follow-up (connected agents) → Dataverse. Follow-up → Power Automate approval → test inbox. Every agent → Audit Logger flow → `agent_runs` → Agent Control Tower dashboard.

## 4. Demo

- Live dashboard: https://shaikh-saab.github.io/salesops-squad/
- Demo video (60–90 s): **TODO**

## 5. Results

From [`scoring.csv`](scoring.csv), 30 prompts across 8 categories, 4 checks each.

| Metric | First run | Final run |
| --- | --- | --- |
| Routing accuracy | TODO | TODO |
| Policy compliance | TODO | TODO |
| Audit coverage | TODO | TODO |
| Avg est. cost per request (simulated) | TODO | TODO |

Top three failures on the first run, and the fix for each: **TODO**.

## 6. Trade-offs

- **Latency:** a three-agent chain is slower than one agent. Each hop adds a model call.
- **Routing errors:** routing depends on agent descriptions. Writing them as "use when ... / do not use for ..." and adding an explicit ambiguity rule were the main levers.
- **Preview vs GA:** connected Copilot Studio agents are GA. Agent 365 governance features are largely preview or licensed, so governance and cost are **simulated** here with a custom audit table.
- **Simulated metrics:** per-run token usage isn't exposed to flows, so cost is estimated from text length and assumed prices. That's good for comparing agents with each other, not for budgeting.

## 7. What I would do next

1. Replace estimated tokens with real usage once it is exposed per run.
2. Connect an external agent over MCP or A2A (for example, a mock credit-risk check).
3. Add a Renewal Agent for expiring contracts.
4. Add a second approver for quotes above a set value.
5. Give each agent its own identity (Entra Agent ID) and least-privilege access.
