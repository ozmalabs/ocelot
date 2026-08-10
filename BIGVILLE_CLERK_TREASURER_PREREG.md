# PREREG — block 345000: the Clerk-Treasurer (records, taxes, reconciliation)

*User: "There needs to be another council paid position — a Clerk-Treasurer whose job it is to
keep records and collect taxes. The bank and the council do not magically get money; they have
to keep their own written records (someone has to do them) and they have to reconcile those."*

The fiscal sibling of the Constable (339000): a public function is an **office-holder's job**, not
an automatic effect. Money is not magic — the treasury only gains coin because someone **collects**
it; every move is **written** into a ledger (someone has to do the books); and the record must
**reconcile** against the actual coin, so error or embezzlement surfaces.

## The mechanism (`bigville_clerk_treasurer.json`)

`Town -has_treasury-> Treasury{coin}`; `Treasury -has_ledger-> Ledger{recorded}`;
`Town -has_clerk-> Agent{role:clerk_treasurer, salary, honesty}`; each collection files a
`LedgerEntry{amount, kind, subject}`.

- **`ct_collect`** — the clerk collects a resident's assessed tax **and writes the record**. The
  resident pays the full tax; `honesty·tax` reaches the treasury (a dishonest clerk pockets the
  rest); the clerk records the **full** amount + a `LedgerEntry`. No clerk in office ⇒ the rule
  never fires ⇒ the treasury stays flat (money is not magic).
- **`ct_pay_clerk`** — the paid salary is drawn from the treasury as a **recorded** expense
  (`recorded -= salary` + a `LedgerEntry`), so it keeps the books balanced.
- **`ct_reconcile`** — `discrepancy = treasury.coin − ledger.recorded`; `reconciled` iff 0. An
  honest, diligent clerk reconciles to 0; an **unrecorded** transaction (actual > recorded) or
  **embezzlement** (recorded > actual) surfaces as a non-zero discrepancy.

## Gates (pass/fail)
1. **G-money-not-magic (HEADLINE):** no clerk ⇒ the treasury stays flat, no entries.
2. **G-clerk-collects-and-records:** the clerk collects the taxes and files one ledger entry each;
   recorded == collected.
3. **G-books-reconcile:** an honest clerk's record reconciles to the actual coin (discrepancy 0).
4. **G-clerk-is-paid:** the salary is drawn from the treasury as a recorded expense; still balanced.
5. **G-embezzlement-surfaces (HEADLINE):** a dishonest clerk records the full tax but banks less;
   reconciliation shows the missing coin (discrepancy −4.5, not reconciled).
6. **G-unrecorded-income-surfaces:** coin entering without a record surfaces (+4, not reconciled).
7. **G-no-python-decision:** collect/pay/reconcile are the seed rules; the adapter arms and reads.

## Scope / honesty
- Self-contained demonstrator (`self_load_only`); `.so` untouched. Composes with the recognition/
  office pattern (the clerk's authority could be `Count(recognizers)` like the Constable) and with
  the fiscal seeds (`bigville_fisc*`); wiring the treasury to the real economy is a follow-on.
- Embezzlement here is a fixed `honesty` skim; a decision to embezzle (a collapse valued by the
  clerk's honesty vs opportunity) is the natural next step.
- `reconciled` uses exact equality (integers/clean fractions); a tolerance band is a refinement.
