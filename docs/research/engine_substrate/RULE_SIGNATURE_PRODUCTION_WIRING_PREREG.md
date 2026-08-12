# Rule-signature production wiring — pre-registration

Companion to `RULE_SIGNATURE_SLICE_PREREG.md` / `RULE_SIGNATURE_SLICE_RESULTS.md`
(read first — they registered and then measured the OBSERVATIONAL slice this
rung wires into production) and `SHAPE_AUDIT.md` §2.1 (the "keywords_text
family" finding this rung closes for two of its nine confirmed sites). This
doc registers the bar for both halves of this task **before the production
edit is made**, per this folder's own house discipline and CLAUDE.md's "RUN 15
CORRECTION" standing rule: power the gate before the endgame.

**Worktree:** `/home/matt/ocelot-rule-signature-production`, branch
`rule-signature-production` (created after this doc, before the wiring edit),
detached from `main` at `4f24abb` (verified:
`git log --oneline -1 main` → `4f24abb CLAUDE.md: shape is acquisition, rule
is execution -- the analogical-transfer arc, landed`). Engine unchanged —
this rung adds no Rust: `runners/dsl/python/substrate_rs/_native.abi3.so`
sha256 `62e5cdc39a84fee548b9d373c9bbcd01f33c69f8ddab3dc518e78b0ef45ca56f`.

---

## Part 1 — wiring the measured signature into production selection

### AR1 — the combination-wiring design (registered before the edit)

**The honest problem, stated from the prior rung's own data
(`RULE_SIGNATURE_SLICE_RESULTS.md` §3):** structural (`where`-signature) and
name-keyword (`keywords_text`) rule selection are NOT strictly ordered —
Class A (word in `where`, not in name): structural 11/12, name-keyword 0/12.
Class B (word in name, not in `where`): name-keyword 12/12, structural 0/12.
A naive full replacement of the name-keyword Argmax with a structural-only
Argmax would recover Class A but REGRESS Class B to 0/12 — an unacceptable
trade given Class B is the majority of currently-working selections.

**The disagreement shape, read row-by-row from the prior rung's own
committed measurement (`scripts/rule_signature_measurement_results.json`,
re-inspected here as investigation, not new data collection) — this is the
finding that grounds the design choice:** in **every one of the 24
informative Class A/B rows**, whichever method is WRONG on that row is wrong
by **abstaining (`None`)**, never by returning a confidently wrong non-null
rule name. Production is `None` on all 12 informative Class A rows (never a
wrong pick); structural is `None` on all 12 informative Class B rows (never a
wrong pick). There is no measured row where one method is non-null-and-wrong
while the other is correct.

**Decision: LEXICOGRAPHIC FALLBACK, not a weighted blend or a pre-filter.**
Try production's own `keywords_text` Argmax first, exactly unchanged; only
when it abstains (`best == None` OR its own `overlap(best) <= 0` — the SAME
abstain test the unmodified code already uses) fall through to a second
Argmax of the **identical StringIndexOf-Sum shape**, applied to
`where_signature_json` instead of `keywords_text`. This is chosen over the
brief's other two named shapes for reasons grounded in the row data above,
not asserted:

- **Not a pre-filter** ("structural filters candidates before name-keyword
  ranks the survivors") — a pre-filter would need structural to be a
  *superset* signal (never wrongly excluding the name-native winner), but
  Class B's own probes score **0** under structural (the where-only
  signature genuinely cannot see name/effects-only information — this is
  §11.2's own declared scope boundary, not a bug) — filtering on structural
  first would zero out every Class B candidate before name-keyword ever saw
  them. Wrong direction for this data.
- **Not a weighted/summed blend** — the two scores are not commensurable
  (`keywords_text` overlap counts word-hits against an 1-line name string;
  `where_signature_json` overlap counts word-hits against a much longer
  structural JSON blob) and, per the row data, a blend is unnecessary
  complexity: every disagreement is (non-null-correct) vs (null), so a
  simple ordered fallback recovers the same information a blend would, with
  no tuning parameter (no weight to mis-set) and no new abstain semantics to
  design.
- **Lexicographic fallback, one Term.** Matches the row data exactly: when
  production is confident (non-null, score > 0) it is — on every measured
  row — *correct*, so trust it first; only its *honest abstain* (never
  observed to correlate with a wrong-but-confident structural pick) opens
  the door to the second signal.

**Expressed as ONE Term (matches the existing convention at this call
site).** `_pick_acting_rule`/`_pick_reply_rule` already build a Term tree in
Python and evaluate it once via `native0.evaluate` — no Python `if/else`
picks a rule name. The combination preserves this exactly: production's
`Let("best", Argmax(...), Ite(abstain-test, fallback-term, best))` where
`fallback-term` is the SAME `Let/Argmax/Ite` shape over
`where_signature_json`. Nothing about the decision moves into Python — Python
still only assembles the Term dict (mechanical), and the WHOLE lexicographic
decision (try-then-fall-through) is evaluated inside the engine in one call.
This is a **strict generalisation of the existing shape**: the fallback Term
reads `where_signature_json` with the identical `StringIndexOf`-`Sum`-`Argmax`
machinery already used for `keywords_text` — no new Term type, no new Rust.

**Validated before the production edit** (`scripts/rule_signature_wiring_check.py`,
read-only — no production file touched by running it): boots a full agent,
evaluates the candidate combined Term directly (bypassing
`_pick_acting_rule`/`_pick_reply_rule` entirely) against the SAME 40-probe
oracle the prior rung registered, and reports per-row correctness. This is
investigation, not the AR2 measurement itself (that requires the REAL,
edited production functions — see AR2 below) — it exists to confirm the
design is worth wiring before the higher-risk edit is made.

### AR2 — the powering bar for the wired production functions

Reusing the prior rung's own registered floor (`RULE_SIGNATURE_SLICE_PREREG.md`
AR2), applied to the SAME 40-probe oracle, now run against the ACTUAL edited
`_pick_acting_rule` / `_pick_reply_rule` (not a standalone Term, not the
observational `pick_*_rule_structural` functions):

- **Floor:** the wired production functions' total correct count over the 24
  informative Class A+B rows must **exceed** the pre-wiring production
  baseline (12/24: Class A 0/12, Class B 12/12) by a margin **≥ 5** (the
  same AR2 win-margin floor), i.e. **≥ 17/24**, to support a directional
  "wiring measurably improves production selection" claim.
- **No-regression sub-bar:** Class B's own count must not drop below its
  pre-wiring value (12/12 informative) — a design that recovers Class A at
  Class B's expense is not an improvement per AR1's own reasoning above; it
  is a regression dressed as a trade.
- Reported as a **live before/after** on the real functions (git-stash-style
  paired run, or an explicit baseline capture before the edit + a second run
  after), not inferred from the standalone validation script.

### AR3 — Part 2 per-site coverage (registered, no floor — investigation +
verdict per site, per the task brief's explicit "partial result is complete"
framing)

For each of `reflective_faculty.py:2963` (folded into AR1/AR2 above, it is
`_pick_reply_rule`), `:3240`, `:3532`, `:3909`, `:4183`, and
`seeds/variation_ops.json:152` (+ its `composer_experiment_graph.json`
twins), this rung will, PER SITE, register a verdict as one of:

- **(a) fix** — build + wire, with live before/after evidence proportionate
  to the site's own risk (a low-blast-radius proposal-only site does not
  need the SAME oracle rigor as a production rule-selection change — the
  brief's own explicit permission for `variation_ops.json:152`);
- **(b) needs-separate-rung** — the site ranks a genuinely different KIND of
  object (not a Rule's `where`-clause) and a comparable structural signature
  would be new, unvalidated machinery — named precisely, not attempted here;
- **(c) negligible-impact** — real but measured-small candidate population /
  collision risk, mirroring the chunk-equivalence rung's own "real but zero
  payoff" bar — declined with the measurement shown, not asserted.

No floor is pre-set per site (unlike AR1/AR2) because the task brief is
explicit that uniform treatment is not required and each site's own
population size determines what a meaningful measurement even looks like;
each verdict's OWN supporting measurement is registered in the RESULTS doc
at the point it is made, before being read as a finding.

### AR4 — no regression

- **Paired failing-node-id lists, not counts**, for whatever test suites
  cover the self-improvement / rule-selection / seed-ablation paths this
  task touches: `tests/test_acting_variant.py`, `tests/test_structural_variant.py`,
  `tests/test_self_delta.py`, `tests/test_gap_awareness_migrated.py`,
  `tests/test_self_concern_promote_migrated.py`, plus
  `tests/test_agent_authors_new_rule_migrated.py` (the `VariationOp`/
  `variation_pick` gate — in scope because Part 2 may touch
  `seeds/variation_ops.json`) and `tests/test_composers_graph.py` /
  `tests/test_experiment_composer.py` (both exercise `_pick_acting_rule`/
  `_compose_experiment_rule` downstream).
- **Baseline captured on this worktree BEFORE the production edit** (the
  same 11-failing-node-id baseline `RULE_SIGNATURE_SLICE_RESULTS.md` §4
  already reproduced byte-identically on `ca18152` — re-confirmed here on
  `4f24abb` before any edit, since the tip moved) — then re-run after the
  Part 1 + Part 2 edits land, comparing lists, not counts.

---

## Reproduce (this doc's own validation, before any production edit)

```bash
cd /home/matt/ocelot-rule-signature-production
git log --oneline -1                                       # 4f24abb (detached base)
sha256sum runners/dsl/python/substrate_rs/_native.abi3.so  # 62e5cdc3...ca56f (unchanged)

# AR1 grounding — re-inspect the prior rung's own committed measurement
# (no new boot needed for this step)
python3 -c "import json; d=json.load(open('scripts/rule_signature_measurement_results.json')); \
  [print(r) for r in d['class_a']['rows']+d['class_b']['rows']]"

# AR1 validation — the candidate combined Term, evaluated read-only,
# no production file touched (~5 min, full agent boot)
systemd-run --scope --user -p MemoryMax=8G -p MemoryHigh=7G -- \
  python3 scripts/rule_signature_wiring_check.py
# expect: Class A 11/12 informative, Class B 12/12 informative (23/24 total)
```
