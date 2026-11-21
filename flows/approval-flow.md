# Flow: Request email approval

Built in Power Automate. It is the **only** place an email can be sent, and only after a named human approves.

## Steps
1. **Trigger:** called by the Follow-up Agent with `draft_id` (or "When a row is added" to `email_drafts` where status = pending).
2. **Get row** from `email_drafts` and the related account name.
3. **Start and wait for an approval** (Approvals connector, type "Approve/Reject - First to respond"):
   - Title: `Approve follow-up to <account>`
   - Details: subject and body
   - Assigned to: **your own account only**
4. **If approved:**
   - Update the row: status = `approved`, approved_by = the responder's name.
   - Send the email to the **test inbox only** (`TEST_INBOX_EMAIL`, your own address). Never to a customer.
   - Update the row: status = `sent`.
5. **If rejected:** update the row: status = `rejected`, approved_by = the responder's name.
6. **Log the decision:** call "Log agent run" (or update the latest Follow-up Agent row) with approved_by_human = `yes` or `no`.

## Fallback (if approvals take too long to set up)
Add an `approved` yes/no column to `email_drafts`, flip it by hand in the table, and show the dashboard row changing.

## Screenshot checklist
- [ ] The approval card in Teams or Outlook
- [ ] The row moving pending → approved → sent
- [ ] Blur tenant IDs and any real email addresses
