# Actionable Plan - Hart Flowers

_Generated from `florist_call.txt` by `claude-sonnet-5`. Not yet reviewed by a human._

## Problem statement

Rosie manually transcribes wedding order details from emails into a spreadsheet every week, a slow and error-prone process that has already caused a near-miss on a wedding date.

## 1. Current Workflow

- Wedding order details arrive via email from couples, including colours, flower preferences, date, and sometimes a Pinterest board.
  > They all come in by email. Couples send me their colours, the flowers they like, the date, sometimes a Pinterest board.

- Rosie manually copies each order into a spreadsheet once a week, taking about four hours.
  > Every Monday I copy each one into a spreadsheet by hand. It takes me most of the morning, about four hours.

- Only Rosie handles the order intake process; her assistant is involved only in deliveries, not orders.
  > Just me. My assistant does the deliveries, she never touches the orders.

- The manual process leads to mistakes, including a near-miss where a wedding's flowers were almost sent on the wrong date.
  > Last month I got a date wrong and nearly sent a whole wedding's flowers to the wrong Saturday.

> **Partially covered.** The call didn't establish how many wedding orders come in per week/month, or how long this workflow has been in place, so the true scale of the bottleneck is unclear.

## 2. Output

- Rosie wants a single, consolidated sheet per wedding containing all order details.
  > One sheet per wedding with everything on it, so I can order my stock straight from it.

- The sheet needs to be usable directly for placing stock orders.
  > One sheet per wedding with everything on it, so I can order my stock straight from it.

- It's unconfirmed whether the output needs to integrate with accounting software.
  > I'm not sure. I'd have to ask my accountant.

> **Partially covered.** Whether the output must feed into accounting software (and therefore what format/fields it needs) is unresolved - Rosie needs to check with her accountant.

## 3. Expectations

> **Not covered in this call.** The call did not establish a timeline for when Rosie wants a solution in place, nor any concrete definition of what a successful reduction in wasted time or errors would look like to her.

## Recommendation

_Agent judgement, built on the findings above - not customer-stated fact._

Introduce a structured intake form (e.g. a simple web form or templated email reply) that couples fill in directly, which auto-populates a single per-wedding record - eliminating the manual weekly copy step and reducing the chance of transcription errors like the date mix-up. Before finalising the output format, confirm with Rosie's accountant whether the sheet needs to integrate with accounting software, as this will determine whether a spreadsheet-only solution suffices or whether an export/integration step is needed.

## Implementation steps

1. **Confirm accounting integration requirement** - Rosie should check with her accountant on whether wedding order data needs to feed into accounting software, and if so, in what format - this determines whether the solution can be a standalone spreadsheet template or needs an integration/export capability.
2. **Design a structured intake form** - Replace free-form email intake with a form (web form or structured email template) capturing colours, flowers, date, and inspiration links directly into a standard per-wedding record, removing the need for manual transcription.
3. **Automate consolidation into one sheet per wedding** - Set up a simple automation (e.g. form responses populating a templated spreadsheet tab per wedding) so Rosie no longer manually copies data every Monday, directly targeting the four-hour weekly task she described.
4. **Add a validation step for key details like dates** - Build in a simple check or confirmation step for critical fields such as wedding date, to prevent a repeat of the near-miss Rosie described.
5. **Clarify success criteria and timeline with Rosie** - Since the call did not establish a deadline or a specific definition of success, follow up to pin down when she wants this live and what reduction in time/errors would count as a win, before committing to a rollout plan.

## Questions to take back to the customer

**Current Workflow**

- Roughly how many wedding orders do you process in a typical week or month?
- How long has this weekly spreadsheet process been in place?
- Has the date error happened more than once, or was that a one-off?

**Output**

- Can you check with your accountant whether the sheet needs to feed into your accounting software, and if so, which one?
- Does anyone besides you need to read or use this sheet (e.g. suppliers, accountant, assistant)?
- Is a spreadsheet format sufficient, or would a different format (PDF, form, etc.) work better for ordering stock?

**Expectations**

- When would you like a new process in place by?
- If this process were fixed, what would 'better' look like to you - fewer hours spent, zero missed details, something else?
- How many hours per week would you consider a successful reduction from the current four hours?
- Is avoiding another date-mix-up incident the main measure of success, or are there other outcomes you care about?
