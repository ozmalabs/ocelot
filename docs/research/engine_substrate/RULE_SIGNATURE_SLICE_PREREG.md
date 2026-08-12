# Rule-signature slice — pre-registration

**Posture:** MEASURE-THEN-BUILD. `RULES_AS_SHAPE_DESIGN_SPIKE.md` §11.2 names
one, and only one, buildable slice of the "rules as a reference layer" design:
a `where`-only, path-addressed, alpha-renamed `rule_signature`, stored as one
additive attr on `RuleSummary`, compared observationally against the existing
name-keyword `Argmax` at the `_pick_acting_rule` / `_pick_reply_rule` call
sites. This doc registers the bar **before** writing `rule_signature`, per
this folder's own house discipline (`GAMMA_REFLECTION_WIRING_PREREG.md`,
`DIRTY_PRECISION_PREREG.md`), and per CLAUDE.md's "RUN 15 CORRECTION" standing
rule: **power the gate before the endgame.**

**Engine baseline (unchanged source — this slice adds no Rust).**
`runners/dsl/python/substrate_rs/_native.abi3.so` sha256
`d7acb906da8ffb2c02c6feccd3bf3ecc62241b956f6343c336479a0f5e363843`. Worktree:
`/home/matt/ocelot-rule-signature-slice`, branch `rule-signature-slice`,
detached from `main` at `ca18152` (verified: `git log --oneline -1 main` →
`ca18152 Design spike: should rules be a reference layer over nodes -- yes,
qualified`).

**Coherence probe, run before anything else:** `add_node("T", {"lst":[1,2,3],
"tup":(1,2,3)})` reads back `[1,2,3]` (list) and `(1,2,3)` (tuple) distinctly,
confirmed live in this worktree via the `.pth` fallback to the canonical
tree's engine (see §0.1 — no Rust changes needed, so no rebuild was done).

---

## 0. Investigation findings — read before any bar was set

### 0.1 Rust vs Python for `rule_signature` — Python wins, and it is not close

§11.2 flags this as open ("investigate which is actually correct"). The
flattening operates over **already-parsed rule JSON** — `RuleSummary.rule_json`
(a Python `dict`, `json.loads`-ed from `native.export_rules()`'s own output) or
a seed file's own `r["where"]` (already a Python `dict`, loaded by
`json.load`). There is no `TermArena`, no `TermIdx`, no graph node in the loop
at any point — the function's signature is `dict -> frozenset[tuple]`, a pure
in-memory tree walk. `domains/rule_ir.py::canonical_rule_body` is the exact
precedent already in this tree: a Python structural canonicaliser over the
same rule-JSON shape, explicitly documented as "diagnostic data" rather than
an installed rule. `rule_signature` is the same class of thing. Writing this
in Rust would require either (a) a new PyO3-exposed Term that walks a
`Value::Dict` tree — a real new primitive, which §11.2 explicitly tries to
avoid — or (b) round-tripping the dict through `FromJsonString`/arena
construction just to walk it, which is strictly more machinery for zero
benefit, since nothing here needs arena identity, `TermIdx` sharing, or
engine-side matching speed (this is *investigation* tooling, not a hot path).
**Decision: pure Python, additive, no Rust.** This also means §10.4 of the
design spike (NodeID/install-order fallout) is categorically inapplicable —
confirmed here, not just assumed: this slice allocates no `NodeID`s (the one
`sub.set_attr(...)` call per `RuleSummary` node mutates an attr on an
*existing* node; it does not `add_node`).

### 0.2 The candidate-rule population — real, in-scope, counted before the bar was set

Scanning every `seeds/*.json` NOT on the task's exclusion list
(`arc_executor.json`, `arc_goals.json`, `arc_magnitude.json`,
`arc_decompose.json`, `goal_residuals.json`), structurally discovering (never
a hand list — same method `_ensure_acting_rule_provenance` /
`_ensure_reply_rule_provenance` already use) every active rule whose effects
write `chosen_action` or mint an agent-authored `Message`:

| population | count | files |
|---|---|---|
| acting candidates (`writes_chosen_action`) | **14** | `bigville_affect_decide`, `bigville_body_choice` (×4), `goal_derivation`, `grid_navigation`, `marshmallow_delay`, `quanta_navigation` (×2), `seek_primitive`, `snake_understanding`, `stage2_boundary`, `world_curiosity` |
| reply candidates (`writes_reply`) | **32** | `comprehend_instruction`, `conversation_attachment_reply`, `conversation_capability_reply`, `conversation_elaborate`, `conversation_grice`, `conversation_honest_floor`, `conversation_reply`, `conversation_reply_flag`, `conversation_self_concern`, `conversation_self_reply` (×5), `conversation_steering` (×3), `conversation_topic_reply` (×2), `embodied_instruction_goal` (×2), `gap_awareness` (×2), `instruction_understanding` (×2) |

**46 real, seed-sourced rules total.** This is the entire pool the oracle
design below draws from — no synthetic/hand-written rule bodies anywhere in
this slice's measurement. `gap_awareness.json`'s `note_reported_gap` — the
exact worked example in the design spike's §6 — is in this pool.

### 0.3 The two production call sites, confirmed unchanged by inspection

`_pick_acting_rule` (`reflective_faculty.py:2704-2765`) and `_pick_reply_rule`
(`:2963-3007`) both build a `Sum(axis_preds, "w", Ite(StringIndexOf(Attr(s,
"keywords_text"), w) >= 0, 1, 0))` `Argmax` over `RuleSummary` nodes filtered
to `{writes_chosen_action|writes_reply == 1.0, skippable == 1.0}`. Both call
`_ensure_acting_rule_provenance` / `_ensure_reply_rule_provenance` first
(idempotent mint/upgrade). This slice's new code:

- adds a **new, separate** module (`domains/rule_signature.py`) — it does not
  edit `_pick_acting_rule`, `_pick_reply_rule`,
  `_ensure_acting_rule_provenance`, or `_ensure_reply_rule_provenance` AT ALL.
  Zero-diff on those four functions is the AR5 gate (§ below), verified by
  `git diff` on the exact line ranges, not by re-reading the code and asserting
  it looks unchanged.
- mints/upgrades one **additional** attr (`where_signature_json`) on the same
  `RuleSummary` nodes those four functions already produce, via its own
  idempotent `ensure_where_signature` function — mirroring the "upgrade an
  existing node in place" precedent `_ensure_reply_rule_provenance`'s own
  docstring names, applied to a population it does not otherwise touch.
- adds a **new, standalone** ranking function per call site
  (`pick_acting_rule_structural`, `pick_reply_rule_structural`) that
  duplicates the SAME candidate filter (`writes_*==1.0 AND skippable==1.0`)
  but ranks by the structural score (§ AR3) instead of name overlap. Neither
  is called from `ground_concern`, `_compose_acting_variant`,
  `_compose_reply_ablation`, or any other production path — they are called
  only by the measurement script.

---

## AR1 — the oracle design

**The honest problem, stated exactly as §11.2 states it:** "better rule pick"
needs ground truth, and the only textbook oracle (does the downstream
experiment get adopted?) is slow, noisy, and — worse for a pre-registration —
would require *building* the full comparison to even generate a data point,
which is circular for deciding whether to build it.

**Decision: a hand-constructed, independently-verified oracle over the real
46-rule pool (§0.2), NOT the live-experiment-adoption oracle.** This is
option 2 from the task brief, chosen over option 1 (existing test fixtures)
because investigation found existing fixtures encode the *production*
Argmax's own output as their expected value (e.g.
`test_gradient_with_real_acting_rule_builds_a_genuine_variant` asserts
`av.get("removed_rule") == "hop_descend_gradient"` — that is what the
name-keyword Argmax already returns on that fixture, not an independent
ground truth a structural method could be checked against). Using them as
"ground truth" would silently define correctness as "agrees with the method
under test," which cannot detect the disagreements the whole slice exists to
find. They are used instead as **class C** below — a real, non-cherry-picked
population, reported honestly as *not* an independent oracle, alongside two
classes that are.

**The oracle: three probe classes, each hand-built by reading the actual rule
bodies (never guessed), each targeting a different honest question:**

- **Class A — "where-native."** For a candidate rule, pick a literal atom
  string that appears somewhere in its `where`-clause content (an attr key, an
  attr's literal value, or a member of a literal list/set value) but does
  **not** appear as a substring of the rule's own name. Ground truth: THIS
  rule is correct, by construction (the investigator read the where-clause and
  confirmed the atom is there) — independent of either ranking method.
  **Pre-registered prediction:** structural (which reads where-clause content)
  should find it; name-keyword (which only reads the name) should miss it or
  score it 0. This class exists to test the core hypothesis in the direction
  it is supposed to win.
- **Class B — "name-native."** For a candidate rule, pick a word that appears
  in the rule's own name (hence would score under name-keyword overlap) but
  does **not** appear anywhere in the rule's `where`-clause content (verified
  by construction the same way). Ground truth: still THIS rule (the word
  names it), independent of method. **Pre-registered prediction, stated before
  looking:** structural (where-only, per §11.2's explicit scope) should
  MISS or under-score this rule, because the distinguishing information lives
  in the name/effects, which this slice deliberately does not signature. This
  class exists to state, in advance, the honest boundary of a where-only
  signature — a scope-correct null is not a defect, and pre-registering it
  stops it from being reported later as a surprise loss.
- **Class C — "fixture-neutral."** Real `residual_predicates` arrays lifted
  verbatim from existing test fixtures (`test_acting_variant.py`,
  `test_structural_variant.py`, `test_self_delta.py`) — a non-cherry-picked,
  independently-authored (by past rungs, for unrelated purposes) probe set.
  **Not an independent oracle** (§ above) — reported as an *agreement-rate*
  measure only ("does structural pick the same rule the shipped Argmax
  already picks, on real historical probes"), never as a correctness check.

**What "better" means, stated before data:** on Class A, structural is better
if it names the correct rule (or scores it strictly higher than any wrong
candidate) more often than name-keyword does. On Class B, name-keyword is
expected to win — this is not a contest, it is a scope-boundary
confirmation. Class C reports raw agreement rate only, with no "better/worse"
claim attached (there is no independent ground truth to grade against).

**Honest limitation, stated up front:** classes A and B are hand-constructed
by one investigator reading rule bodies, over 46 real rules — not drawn from
a live agent's own concern stream, and not checked against downstream
experiment-adoption outcomes. This is the acknowledged cost of sidestepping
the slow/noisy live oracle (§11.2's own framing). It answers a narrower
question than "does this make the agent better at self-improvement" — it
answers "does structural rule-shape reading recover information a bare rule
name discards, on real rule bodies, when independently checked." That
narrower question is exactly what §11.2 asks this slice to answer.

---

## AR2 — the powering bar

Per CLAUDE.md's RUN 15 correction: *"deltas within ~3× the per-episode step
are not results"* and *"power the gate before the endgame."* This is a
discrete agree/disagree measurement, not a continuous metric, so the analogue
of "per-episode step" is: **one disagreement between the two rankings, on one
probe, is noise; a claim needs enough independent probes that a handful of
disagreements cannot be the whole story.**

**Registered floor, set from the real pool size (§0.2) before any comparison
was run:**

- **N ≥ 30 total probes**, split with **≥ 8 probes in each of Class A and
  Class B** (Class C is uncapped — use all real fixture arrays found, reported
  separately, no floor since it is not the hypothesis-test class).
- Within Class A or Class B alone, a directional claim ("structural wins on
  where-native probes") requires the **winning method's win count to exceed
  the losing method's by at least 5** (out of the ≥8-probe class) — a 5-3 split
  on 8 probes is not reported as a finding; it is reported as underpowered
  within that class, exactly as A14's real-only n=2 precedent reports small-n
  honestly rather than dressing it up.
- If the ≥30/≥8-per-class floor is not reached (e.g. the real rule pool cannot
  support enough honestly-distinct probes), the measurement is reported as
  **underpowered**, with the raw counts given exactly as measured — never
  rounded up to a claim the N does not support.

This bar was written into this document before `pick_*_structural` was
executed against any probe.

---

## AR3 — build `rule_signature` + the comparison wiring (scope)

Exactly §11.2's scope, no more:

- `rule_signature(where_clause: dict|None) -> frozenset[tuple]` — pure
  function, `where` only (not `match`, not `effects`), path-addressed
  (dot/`[i]` routes from the where-clause root, e.g.
  `items[0].source.node.name`, matching the design spike's own §6.2 worked
  notation), alpha-renamed (`Var` `name` fields renamed positionally in
  first-DFS-appearance order to `?0`, `?1`, …; every other scalar — including
  `Lit` values — kept literal, i.e. the "alpha" tier of the spike's own §3
  three-tier scheme, not "alpha+lit"). Two row kinds only (no `"re"` match-edge
  rows — match is out of scope): `("rt", path, term_type)` one per Term node,
  `("ra", path, field, atom)` one per scalar field.
- Stored as **one new attr**, `where_signature_json` (a JSON string — the
  same convention `rule_json` already uses on the same node type), on the
  **existing** `RuleSummary` population. No new node type, no new edge type,
  no mirror, no lifecycle — `ensure_where_signature` upgrades an existing
  `RuleSummary` in place (idempotent, guarded on the attr already being
  present).
- The comparison ranking (`domains/rule_signature.py`,
  `pick_acting_rule_structural` / `pick_reply_rule_structural`): same
  candidate filter as production, structural score computed by (1) finding
  every `where_signature` row whose stringified form contains any
  `axis_preds` word as a substring (the identical substring semantics
  production's own `StringIndexOf` uses, applied to the wider structural
  surface instead of just `keywords_text`), (2) building a real
  `Value::FrozenSet` of those matched rows, (3) invoking the real Rust
  `FixedCount` Term (`native.evaluate`) over that `FrozenSet` to obtain the
  score. This is a genuine, if narrow, use of the named primitive:
  `FixedCount` on a `Set`/`FrozenSet` is cardinality by construction (its own
  doc comment says so), so the substantive step is which rows survive the
  filter (deeper structural surface), not the arithmetic `FixedCount`
  performs — stated here honestly rather than overclaimed.
- `StructSim` is used only as an **ancillary, exploratory** check (pairwise
  structural similarity between candidate rules' signatures, to characterise
  clustering) — not part of the AR1 hypothesis test, because `StructSim`
  compares two structures of the same kind, and `axis_preds` (a flat word
  list) is not the same kind of object as a `where`-signature; forcing it
  into that role would be a less faithful use of the primitive than the
  filtered-`FixedCount` design above. Reported separately in AR4, clearly
  labeled ancillary.
- **Zero changes to `_pick_acting_rule`, `_pick_reply_rule`,
  `_ensure_acting_rule_provenance`, `_ensure_reply_rule_provenance`.**

---

## AR4 — the measurement

Run all ≥30 probes (§AR2) through both rankings on the real, seed-sourced
`RuleSummary` population (§0.2), record per-probe: production winner,
structural winner, oracle answer (Class A/B) or "n/a — agreement-rate only"
(Class C), agree/disagree. Report:

- per-class win table (structural-correct / name-correct / both-correct /
  neither) for A and B, with the AR2 win-margin gate applied before any
  directional claim;
- Class C raw agreement rate, explicitly labeled non-oracle;
- the ancillary `StructSim` clustering note, labeled exploratory;
- if underpowered anywhere, say so plainly, per this arc's own standing
  culture (A14's n=2 precedent) — no forced positive finding.

---

## AR5 — no regression

- **Zero-diff gate**: `git diff main -- domains/reflective_faculty.py` must
  be **empty** for the four named functions' line ranges (in fact, for the
  whole file — this slice does not edit it at all). Checked mechanically
  (`git diff --stat`), not by inspection.
- **Existing suites, byte-identical files, run as-is**: `tests/test_acting_variant.py`,
  `tests/test_structural_variant.py`, `tests/test_self_delta.py`,
  `tests/test_gap_awareness_migrated.py`,
  `tests/test_self_concern_promote_migrated.py` — paired failing-node-id
  lists (not counts) reported in the RESULTS doc, against a baseline run on
  the same worktree before this slice's new files existed.
- New files added by this slice (`domains/rule_signature.py`,
  `scripts/rule_signature_measure.py`, this doc, the RESULTS doc) do not
  count against the zero-diff gate — the gate is specifically that production
  rule-selection *behavior* (the four named functions, and anything that
  calls them) is untouched.

---

## Reproduce

```bash
cd /home/matt/ocelot-rule-signature-slice
python3 scripts/rule_signature_measure.py       # AR4 — the measurement
systemd-run --scope --user -p MemoryMax=8G -p MemoryHigh=7G -- \
  python3 -m pytest tests/test_acting_variant.py tests/test_structural_variant.py \
    tests/test_self_delta.py tests/test_gap_awareness_migrated.py \
    tests/test_self_concern_promote_migrated.py -q     # AR5
git diff main -- domains/reflective_faculty.py         # AR5 zero-diff gate (expect empty)
```
