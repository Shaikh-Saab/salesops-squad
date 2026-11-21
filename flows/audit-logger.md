# Flow: Log agent run (Audit Logger)

Built in Power Automate as an **agent flow / Copilot Studio tool**. Every agent calls it at the end of its turn. It writes one row to `agent_runs`.

## Inputs (from the agent)
| Input | Type | Example |
| --- | --- | --- |
| agent_name | Text | Quote Agent |
| user_request | Text | Give Contoso a 60% discount on SKU-12. |
| tools_called | Text | products.read;pricing_policy.read |
| outcome | Text | success / escalated / failed |
| touched_customer_data | Text | yes / no |
| approved_by_human | Text (optional) | yes / no / n-a (default n-a) |
| response_text | Text (optional) | The agent's reply, used for the token estimate |

## Steps
1. **Trigger:** "When an agent calls the flow" (Copilot Studio skill trigger) with the inputs above.
2. **Compose run_id:** `guid()`. **Compose timestamp:** `utcNow()`.
3. **Estimate tokens (SIMULATED):** Copilot Studio doesn't expose exact per-run token usage to the flow, so estimate about 4 characters per token:
   - `tokens_in = div(length(user_request), 4) + 800` (800 = assumed system prompt and context overhead)
   - `tokens_out = div(length(response_text), 4)`
4. **Estimate cost (SIMULATED):** `est_cost_usd = tokens_in / 1000 * 0.003 + tokens_out / 1000 * 0.015`. These prices are **assumptions** kept in one place (an environment variable or a settings row). They are not Microsoft billing.
5. **latency_ms:** the difference between the trigger time and now, or left empty if not measurable. Label it an estimate.
6. **Add a new row** to `agent_runs` with all the fields.
7. **Condition:** if outcome is `escalated` or `failed`, post a message to a Teams channel (or send an email to your own inbox) with the agent, request and outcome.
8. **Respond to the agent:** return `run_id`.

## Screenshot checklist (for this folder)
- [ ] Flow overview (blur any tenant or environment IDs)
- [ ] One run history showing success
- [ ] The `agent_runs` table with new rows
