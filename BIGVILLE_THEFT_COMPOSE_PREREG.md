# BIGVILLE THEFT-COMPOSITION PREREG (design-audit 6.4)

The theft-composition refactor: `bigville_theft` stops self-seeding what already has
canonical seeds and COMPOSES them instead. Strictly ordered, each step its own gated
commit (LEDGER 354000, 355000, …). Gates run every step:

```
python -m pytest tests/test_theft_migrated.py tests/test_court_migrated.py \
  tests/test_recognition_coload_migrated.py tests/test_tools_migrated.py \
  tests/test_recognition_migrated.py -q
```

Step A (6.7) was already MEASURED done (block 353000): co-loaded recognition counts do
not cross-contaminate (per-claim by the match-bound join), so theft may compose
`bigville_recognition` directly with no scoping pre-step.

---

## Step B (6.1) — unify the recognition COUNT (LEDGER 354000) — LANDED

**Claim.** The `Count(InNeighbours "recognizes")` primitive was authored three times
(rc_authority / own_recognition / oc_recognition). Promote ONE canonical count into
`bigville_recognition` and have theft compose it.

**Build.**
- `bigville_recognition` v1.1.0: new `rc_count` — parameterised over the claim NODE,
  matches a bare `[r -recognizes-> claim]` edge (binding the specific claim) and sets
  `claim.recognition = Count(InNeighbours(claim, "recognizes"))`. Generic: fires for ANY
  recognizes-target. `rc_authority` (writes the legacy `authority` attr the recognition
  demonstrator reads) is RETAINED — `rc_count` writes the canonical `recognition` attr,
  additive and non-breaking.
- `bigville_theft` v1.3.0: `depends_on: [bigville_recognition]`; `own_recognition`
  DELETED; the adapter loads `bigville_recognition` before `bigville_theft`.
- Scope note (why not also delete `own_decide`/`own_grant`): the ownership COLLAPSE lean
  (`legitimacy·deference − prop_skepticism`) differs from `rc_recognize`'s
  (`fear·force + opportunism − loyalty`). Routing one collapse through the other needs a
  shared-stance codebook with a per-decision scope — that is finding **6.2 (deferred)**,
  not 6.1. The ownership collapse therefore stays theft-local; only the COUNT is unified.
  (A single generic collapse would also have to mutate `rc_recognize`'s lean, risking the
  frozen `test_recognition_migrated` gate, or drop the distinct stance types the co-load
  guard relies on.)

**Gates (positive).** All theft behavioural gates unchanged and green; the co-load guard
green (own.recognition == 2 now produced by rc_count, auth.authority == 2 by rc_authority);
`test_recognition_migrated` green (rc_authority retained, `recognition` attr unread there).

**Falsifier (`=off`).** `test_the_ownership_count_genuinely_moved_to_bigville_recognition`:
load ONLY `bigville_theft` (no recognition dependency), seed a recognized OwnershipClaim →
`recognition` stays 0 (theft alone no longer counts). Load recognition too → count restored
to 3. Proves the count was composed OUT, not duplicated.

**Source-audit rewrite.** `test_no_python_decides_theft_or_law` no longer pins
`own_recognition`; it asserts `depends_on` recognition, `own_recognition` absent, the
canonical `rc_count` shape in recognition, and theft's `recognizes` read (the composed wire).

Result: **37 passed** across the five gates.

---

## Step C (6.3 + 6.10) — compose the court (LEDGER 355000) — LANDED

**Claim.** `bigville_theft` reimplemented the whole verdict path (`th_vote` / `th_cast_guilty`
/ `th_verdict`). Delete it and COMPOSE `bigville_court` (whose verdict rides
`agent_judgment`'s `jc_conclude`). Reconcile the fine sink (6.10) onto the Treasury.

**Build.**
- `th_charge` now mints a court **Charge/Matter**: adds `off -about_subject-> taker` and
  `town -has_charge-> off`; sets `weight = item.theft_standing`, `threshold =
  Count(on_council)·0.5 + 0.5` (a strict majority, equivalent to the old
  `2·guilty > total`), `penalty=0`/`standing_penalty=0` so `ct_sentence` is an economic
  no-op (theft keeps its own damages/fine economics in `th_penalty`), `status="filed"`.
- New `th_refer`: seats each juror's `considers` edge onto the charge so `jc_conclude` fires
  per juror.
- `th_vote` / `th_cast_guilty` / `th_verdict` **deleted**.
- `th_restitution` / `th_penalty` now gate on `off.status == "guilty"` (the court's verdict).
- **Fine sink (6.10):** `th_penalty`'s fine and `th_collect`'s fine now flow to the town
  **Treasury** (`tr.collected`), the same coffer `ct_sentence` fines — not `court.coin`.
- Adapter: loads `agent_judgment` + `bigville_court`; mints a `Treasury` + `has_treasury`
  and the graded `Stance` codebook (denounce/condemn/doubt/exonerate); `make_juror` seats the
  juror on `on_council` + `governs` and maps `credence=lawfulness`, `punitiveness=−doubt`
  (leaving `deference` — which `own_decide` reads — untouched; the defendant's standing is 0
  so `jc_conclude`'s deference term vanishes). `verdict()` reads `off.status`; `court_coin()`
  reads the Treasury.
- **Panel note (deviation from the literal plan).** The plan proposed generalising
  `bigville_court` to a `has_juror` panel + a per-`Matter` `lean` attr. Instead theft seats
  its jurors on the court's existing `on_council` judging panel and reproduces the ownership
  lean by attribute-mapping through `jc_conclude`'s existing formula. This composes the court
  with **zero changes to `bigville_court`**, keeping the jail-via-court and agent_judgment
  gates byte-green (a `has_juror`/lean-attr generalisation of the shared court would risk
  them for no functional gain — `on_council` already IS the panel the court judges with).

**Gates (positive).** All theft behavioural gates green under the composed verdict (guilty
when a lawful majority condemns; acquitted under a doubting jury; identity/consent/own-property
non-theft; fine/damages/debt/constable economics unchanged, fine now to the Treasury).
`test_court_migrated`, `test_jail_migrated`, `test_agent_judgment_migrated`,
`test_recognition_migrated`, co-load, tools all green.

**Falsifier (`=off`).** `test_the_verdict_genuinely_moved_to_bigville_court`: load theft
WITHOUT `agent_judgment`/`bigville_court` → a recognized, charged theft NEVER reaches a
verdict (`status` stays `filed`, goods not restituted). Composing the court decides it
guilty and restitutes. Proves the verdict was composed out, not duplicated.

Result: **52 passed** across theft/court/jail/agent_judgment/recognition/co-load/tools.

## Step D (bond evolve) (LEDGER 356000) — LANDED

**Claim.** `con_duty` reads a first-class `Bond`'s warmth correctly, **but** the adapter seeded
the `Bond`'s affect slots as a STATIC final scalar and theft did not depend on
`bigville_bond_update`, so the feeling never evolved. Compose the bond dynamics; re-derive the
`constable_choice` gates from the EVOLVED warmth (a benefit/betrayal history, not a scalar).

**Build.**
- `bigville_theft` `depends_on: [..., bigville_bond_update]`; the adapter loads it.
- `constable_bond(toward, *, benefit, betrayal, update_gain=1.0, …)` seeds the `Bond` at a
  NEUTRAL 0 prior with the bond-update knobs (`update_gain>0`, `pos_weight=0.2`,
  `neg_weight=0.2`, `reappraise_factor=0.5`), attaches `BondEvent` nodes
  (`bond -has_event-> ev`; positive `benefit`, negative `betrayal`), and runs the dynamics so
  `bond_event_benefit` raises `affect_affection` (`= update_gain·pos_weight·magnitude·0.5`) and
  `bond_event_betrayal` raises `affect_resentment` (`= update_gain·neg_weight·magnitude`) and
  re-appraises affection down. `con_duty` then reads the EVOLVED
  `affect_affection − affect_resentment`.
- Gates re-derived from history: default `benefit=1.0` → affection 0.1 → enforce (was
  `affection=0.1`); `benefit=9.0` → affection 0.9 > duty 0.5 → **forbear**; `benefit=1.0,
  betrayal=3.0` → resentment 0.6, warmth < 0 → **enforce**. The choices EMERGE from the evolved
  bond, no preset scalar.

**Falsifier (`=off`).** `test_the_constable_feeling_is_evolved_not_a_static_scalar`: the same
large `benefit=9.0` history makes a fond constable **forbear** at `update_gain=1` but
**enforce** at `update_gain=0` (the bond frozen at its 0 prior — the documented bond
falsifier). Proves `con_duty` reads the evolved bond, not a preset feeling.

**Gates.** Theft 20 green (incl. the new Step-D falsifier); court/jail/agent_judgment/
recognition/co-load/tools + the bond behavioural suites green. (Pre-existing unrelated red:
`test_bigville_bond_migrated::test_runners_dsl_untouched_zero_new_rust` compares `runners/dsl`
against a stale hardcoded `BASE` ref that already differed by 3 Rust files before this session;
this refactor touched ZERO Rust.)

Result: **54 passed** across the required + blast-radius gates.

## Step E (adapter shrink) (LEDGER 357000) — LANDED

**Claim.** With B–D landed, the theft adapter should stop minting graph data that belongs in
seeds and shrink to per-scenario world-ingest + arm + read.

**Build.**
- The collapse stance **codebooks** (TheftStance / OwnStance / DutyStance + the graded
  judgment `Stance` the court's jurors collapse over) are now SEED DATA in
  `bigville_theft.json`'s `nodes` (installed by the Rust loader via integer `local_id`s), not
  minted in the adapter — the adapter's four stance loops are deleted.
- The other two things the plan named were already retired earlier: `has_juror` minting went
  away in **Step C** (jurors are seated on the court's `on_council` panel); the static `Bond`
  scalar went away in **Step D** (the constable's feeling is now an evolved benefit/betrayal
  history).
- What remains in the adapter is legitimate per-scenario **world-ingest** — Town/Court/Treasury,
  agents/items/`OwnershipClaim`s/`Bond`s+events — plus `take()` (arm) and the read-offs. That is
  admissible adapter work (the accepted court/recognition adapters build their worlds the same
  way); it is NOT seedable (per-scenario) and is not deleted.

**Gates.** 54 green (theft/court/co-load/tools/recognition/jail/agent_judgment). The Step-C
falsifier dropped its manual stance minting (the codebook now comes from the loaded theft seed).

Result: **adapter shrunk to seed-load + world-ingest + arm + read; all gates green.**

---

## Summary

Steps B–E all landed, each its own gated commit (LEDGER 354000–357000), the theft/court/
co-load/tools/recognition/jail/agent_judgment gates green throughout. Design-audit findings
6.1 (count), 6.3 (court), 6.4 (headline), 6.10 (fine sink) flipped to RESOLVED. Skipped 6.2
(shared stance codebook — needs a `for_decision` scope; the distinct stance node types are
retained deliberately). No `.so` touched.
