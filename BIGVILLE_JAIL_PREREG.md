# PREREG — block 314000: the jail (custodial sentences)

The court could fine and dock standing; it could not **jail**. A serious offence
warrants a **custodial sentence** — the guilty are held, removed from circulation,
for a term, then released. This rung adds a real custodial institution.

## The mechanism (`bigville_jail.json`) — composes with the court

A `Charge` may carry a prescribed `jail_term` (days) — the statutory penalty for
the offence, set when the Constable files it (a data lookup, not an agent's
subjective choice; the guilt verdict is still the council's collapse). The jail is
a first-class institution (`Town -has_jail-> Jail`). Three rules:

- **`jl_imprison`** — a **guilty** charge with `jail_term > 0` (not yet enacted)
  imprisons the defendant: `Jail -holds_inmate-> d`, `d.imprisoned = 1`,
  `d.sentence_remaining = jail_term`, once. This is *in addition to* the fine +
  standing hit `ct_sentence` already applies — custody and fine are independent
  consequences of one guilty verdict.
- **`jl_serve_day`** — when the town is armed to advance a day
  (`town.advancing == 1`), each inmate with time left decrements
  `sentence_remaining` by 1, once per day (a `served_today` guard, reset by the
  adapter each day — the `collect_tax` idiom).
- **`jl_release`** — an inmate whose `sentence_remaining` reaches 0 is freed:
  `del_edge Jail holds_inmate d`, `d.imprisoned = 0`. They serve the FULL term, no
  early release.

## Gates (pass/fail, pre-registered)

1. **G-custodial-imprisons (HEADLINE):** a guilty charge with `jail_term > 0`
   imprisons the defendant — held on the jail roll, `imprisoned = 1`,
   `sentence_remaining = term`.
2. **G-term-counts-down-and-releases (HEADLINE):** advancing `term` days brings
   `sentence_remaining` to 0 and **releases** the inmate — off the jail roll,
   `imprisoned = 0`.
3. **G-serves-the-full-term:** with a 3-day term the inmate is still held after 2
   days and freed only on the 3rd — no early release, no over-holding.
4. **G-fine-only-does-not-jail:** a guilty charge with `jail_term = 0` fines the
   defendant (`ct_sentence`) but imprisons no one (the jail roll stays empty) —
   custody is reserved for offences that prescribe it.
5. **G-acquitted-not-jailed (falsifier):** an acquitted defendant is never
   imprisoned, even when the charge prescribed a term — only a guilty verdict jails.
6. **G-no-python-decision (source audit):** imprison / serve / release are the seed
   rules; the adapter only mints the jail, sets the prescribed term, arms the
   day-advance, and reads state.

## Scope / honesty
- `jail_term` is a prescribed statutory penalty on the charge; letting the council
  **collapse on the sentence** (fine vs jail vs term length) is the natural next
  rung and is deferred. The custodial *lifecycle* (imprison → serve → release) is
  what 314000 delivers.
- `imprisoned` is a readable participation flag; gating civic participation on it
  (an imprisoned councillor cannot sit on a jury) needs the court quorum to count
  only free councillors, so it is deferred (else a jailed juror would deadlock the
  verdict).
- Isolated demonstrator (`self_load_only`); composes with `bigville_court`; no
  Rust; `.so` untouched (`a8a9012c`).
