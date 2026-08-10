# BIGVILLE R20 — COUNCIL MEETINGS & THE NOTICEBOARD: two-tier governance + the public written record (block 268000) — PRE-REGISTRATION

**Pre-registered BEFORE any number.** This document is committed in a separate
prereg commit, ahead of the build/measurement commit. It fixes the claims, the
gates, the failing controls, and the discipline ledger the results must satisfy.

Base SHA (merge-base, origin/main): `350a45c4078403510bd1c83ea389a06ae6dadacd`
Branch: `worktree-agent-ae7e37507f2118a0e`
Block: **268000–268999** (R20 of the bigville movement/economy ladder;
spec `BIGVILLE_MOVEMENT_ECONOMY_SPEC.md` §3 R20 + §2 "HOW the council actually
governs — TWO-TIER MEETINGS + the NOTICEBOARD" + §0 "THE ROOM WHERE IT HAPPENED").

## Seed claim (verbatim, `python scripts/seed_claim.py 268000 268999`)

```
SEED CLAIM 268000-268999: CLEAN -- no collision DETECTED.
  Scope: 977 files with seed sinks; 694 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

(`python scripts/seed_claim.py 268 268` — the single-integer form the supervisor
named — is likewise CLEAN.)

## Architecture (target: ZERO new Rust)

- The two-tier meeting, the collective decision, the institutional stated≠held
  gap, the biased-clerk minutes, and the literacy+access-gated reading are all
  **graph rules over EXISTING DSL Terms** (`IfThenElse` / `Eq` / `And` / `Or` /
  `Not` / `Gt` / `Gte` / `Abs` / `Plus` / `Minus` / `Times` / `IDiv` / `Mod` /
  `Sum` / `Count` / `Neighbours` / `Attr` / `Var` / `Lit` + `set_attr` /
  `add_node` / `add_edge`). **No new Rust Term.** `git diff 350a45c407 --
  runners/dsl` MUST be empty (incl. `term.rs`). The public/private correlation is
  **READ OFF the graph as a MEASUREMENT** (Pearson r over per-meeting
  (public_demand, held_decision) read-offs) — not a new primitive.
- New additive files only, all prefixed `bigville_council_`:
  `seeds/bigville_council_gov.json`, `seeds/bigville_council_board.json`,
  `worlds/bigville_council_world.py`, `scripts/bigville_council_gen_seeds.py`,
  `scripts/bigville_council_run.py`, `tests/test_bigville_council_migrated.py`,
  this file, `BIGVILLE_COUNCIL_RESULTS.md`, `results/bigville_council/summary.json`.
  **No existing tracked file is edited.** R9 (`bigville_fisc_*` — council/state),
  R19 (`bigville_loud_*` — the observe-vs-hear split), R18 (literacy), R3
  (scheduling) are imported READ-ONLY as concepts / precedents.
- Both seeds are **`self_load_only`** (never auto-loaded into the default agent;
  loaded explicitly by this rung's world adapter only). Additive + self-load ⇒
  the rung cannot regress any other suite.
- **The governance substrate is ISOLATED** (`substrate_rs.Substrate()._inner`
  loading the two council seeds) so the meeting fixpoint never cross-fires.
- **Every DECISION is a rule.** The adapter only: registers Council / member /
  mayor / Meeting / Board / Notice / resident graph data (ingest), ARMs the
  meeting (sets `now_day` / `cadence` / `public_demand` / `private_on` /
  `malice_on` / `literacy_gate_on`), runs `run_rules`, and reads state. No Python
  `if`/`else` over agent state decides the vote / the decision / the gap / the
  minutes / who learns the law — source-audit gate.

## Rules (all in the two seeds; every one a decision)

**`bigville_council_gov.json` — the two-tier meeting + collective decision + 234:**

- `cm_convene` — the R3-time CADENCE: a Meeting `convened=1` iff
  `armed==1 AND Mod(now_day, cadence)==0 AND convened==0`. Off-cadence ⇒ no
  meeting (the scheduling tie).
- `cm_public_address` — the PUBLIC session: `public_address = mayor.stated_position`
  (the benevolent address the town hears). Fires for a convened meeting.
- `cm_attendee_hears_address` — a townsperson `attended_by` the meeting perceives
  the PUBLIC content: `knows_address = public_address`, `heard_address=1`.
- `cm_member_vote` — the PRIVATE deliberation, per council member on the
  backing-graph (`council -has_member-> mem`): `held_eff = base_position +
  malice_on * self_serving_premium`; `vote = IfThenElse(captured==1, held_eff,
  public_demand)`. A CAPTURED council's members vote their self-serving held
  position regardless of demand; a RESPONSIVE council's members track the demand.
- `cm_private_decision` — the collective `decision_value`:
  `held_decision = IDiv(Sum_{has_member} vote, Count(has_member))` — the mean over
  the backing-graph (a pure function of the votes; converges at fixpoint).
- `cm_attendee_hears_decision` — the OCCLUSION of the private tier (R19
  observe-vs-hear): fires ONLY when `private_on==0` (the private tier ABLATED) →
  `knows_decision = held_decision`, `heard_decision=1`. With `private_on==1`
  (default) it never fires — the town sees the council convene but never hears the
  deliberation (the §0 room where it happened).
- `cm_institutional_gap` — the 234 atom at INSTITUTIONAL scale:
  `stated_held_gap = Abs(public_address - held_decision)`. A benevolent address
  over a self-serving decision is a readable gap; `malice_on=0` ⇒ held_eff = base
  = address ⇒ gap 0.

**`bigville_council_board.json` — the noticeboard promulgation:**

- `cm_clerk_writes` — ONE council member (the clerk) writes the minutes, a
  RENDERING not ground truth: `notice.recorded = held_decision + clerk_bias`. A
  biased clerk (`clerk_bias≠0`) DISTORTS the record (institutional 234).
- `cm_post_notice` — the notice is POSTED at the town hall:
  `posted=1`, `officially_known=1` (the law is officially promulgated regardless
  of who reads it).
- `cm_resident_reads` — a resident LEARNS the law iff at the town hall AND
  literate (R1 access + R18 literacy): `res -visits-> board`,
  `where at_hall==1 AND (literacy_gate_on==0 OR literate==1) AND knows_law_flag==0
  AND posted==1` ⇒ `knows_law = recorded`, `knows_law_flag=1`. An illiterate or
  distant resident never fires the rule — the law is `officially_known=1` yet
  `personally_known=0` (unequal ignorance-of-the-law). Ablating the literacy gate
  (`literacy_gate_on=0`) bypasses the `literate` condition ⇒ uniform knowledge
  among those at the hall.

## Gates (mirrored by `tests/test_bigville_council_migrated.py`)

**G-two-tier-meeting.** A scheduled meeting convenes on the R3 cadence, fires the
public address (perceived by attendees), then the private decision (NOT perceived
by attendees while `private_on=1`). CONTROL: off-cadence ⇒ no convene. ABLATION
(transparency counterfactual): `private_on=0` ⇒ attendees perceive the held
decision too (`heard_decision=1`).

**G-public-influence-or-theatre (HEADLINE — agency vs structure, MEASURED).**
Over K meetings with VARYING `public_demand`, compute Pearson r between demand and
the private `held_decision`. RESPONSIVE council (`captured=0`) ⇒ r ≈ +1 (public
voice reaches the lever — agency). CAPTURED council (`captured=1`, John's) ⇒
decision constant, zero covariance ⇒ r ≈ 0 (theatre over a pre-made decision —
structure). The MEASUREMENT, not an assertion.

**G-institutional-stated≠held.** With a captured council, `malice_on=1` ⇒
`stated_held_gap > 0` (benevolent address over self-serving decision); ABLATE
malice (`malice_on=0`) ⇒ `stated_held_gap == 0` (the gap closes).

**G-noticeboard-promulgates (laws become known).** The clerk writes + posts; a
literate resident AT the hall learns the law (`knows_law_flag=1`,
`knows_law==recorded`). CONTROLS: an illiterate resident at the hall, and a
literate resident who is DISTANT (`at_hall=0`), both have `officially_known=1` but
`knows_law_flag=0` (unequal ignorance-of-the-law). A BIASED clerk
(`clerk_bias≠0`) ⇒ `recorded != held_decision` (the minutes distort the record —
institutional 234). ABLATE the literacy gate (`literacy_gate_on=0`) ⇒ the
illiterate resident at the hall now learns it too (uniform knowledge).

**Discipline gates.** Seeds `self_load_only`; adapter runs no Python rule engine
and holds no governance decision (source-audit); every Term used is pre-existing
(no-new-Rust set check); engine provenance `source_match in {own, shared}` (never
a pinned md5).

## Discipline ledger

- **Additive-only, ONE prefix `bigville_council_`.** No existing tracked file
  edited. `git diff 350a45c407 -- runners/dsl` empty.
- **Canonical shared `.so`** md5 `fd82dc2978dbb055496dd82390ac2ebe` UNCHANGED
  START==END; never committed.
- **Gates run INLINE:** `pytest tests/test_bigville_council_migrated.py -q` green;
  `tests/test_failure_baseline_migrated.py -q` 11/11;
  `tests/test_engine_provenance_migrated.py -q` 7/7. The ~43-min
  `per_area_settlement_regression.sh` / `rung7_vision_bench.sh` are NOT run
  (additive `self_load_only` rung cannot regress other suites — 2026-07-29
  directive).
- **Two commits:** (1) this prereg, (2) the build. Branch left un-merged.
