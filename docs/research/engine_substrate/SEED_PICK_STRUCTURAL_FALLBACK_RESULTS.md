# Seed-pick structural fallback — results

Companion to `SEED_PICK_STRUCTURAL_FALLBACK_PREREG.md` (read first — it
registers AR1–AR4's bar before any of the numbers below existed). Closes
`RULE_SIGNATURE_PRODUCTION_WIRING_RESULTS.md`'s own named charter for A3
(*"define `seed_signature(seed_manifest) -> frozenset[(rule_name,
*rule_signature_row)]`, mint it alongside `SeedSummary` the same additive-attr
way `where_signature_json` was minted onto `RuleSummary`, and build a
hand-constructed Class-A/B-style oracle over a SAMPLE of the 661-seed
population before trusting it in the live `_compose_experiment_rule` seed-skip
pick"*) and `SHAPE_AUDIT.md` §2.1's A3 finding — *"the agent decides which of
its own 888 seeds to switch off in a live experiment by counting how many of a
capability axis's residual predicate words appear as substrings of that
seed's filename, rule names and blurb."*

**Worktree:** `/home/matt/ocelot-seed-signature`, branch
`seed-pick-structural-fallback`, detached from `main` at `6314ebe`. Engine
unchanged — no Rust added: `runners/dsl/python/substrate_rs/_native.abi3.so`
sha256 `23ba3f1dbe20459c340440978d379c09d83eba7109b489a56a754ebd9b92a7af`
(identical before and after).

---

## The one thing worth reading if you read nothing else

**GO on the requested site, WITH A LOAD-BEARING REACHABILITY CAVEAT found
while building the live demonstration — reported here because it changes
what "GO" actually delivers, not buried.** The same lexicographic
fallback-on-abstain shape `RULE_SIGNATURE_PRODUCTION_WIRING_RESULTS.md` wired
for A1/A2 is now wired for A3, one grain up: `_compose_experiment_rule`'s
`vary` branch tries the existing `keywords_text` Argmax first, unchanged;
only when it genuinely abstains does it fall through to a second Argmax over
a NEW precomputed aggregate attr, `SeedSummary.where_signature_json` — the
union, over every rule a seed's own manifest declares (not the narrower
`RuleSummary`-mirrored subset A1/A2 read), of that rule's `where`-clause
structural signature. Measured on 6 genuine, mechanically-discovered Class A
probes (a word present in a seed's rules' structure but absent from every
seed's `keywords_text` corpus-wide) and 4 genuine Class B probes: **6/6 Class
A recovered, 4/4 Class B byte-unchanged**, both on the standalone Term AND on
the REAL `_compose_experiment_rule` Python function called directly (§5). The
fix is a PRECOMPUTED aggregate field, explicitly NOT a live Term-level join —
the design choice the task required be made and justified, not assumed (§2).

**The caveat, found while building the end-to-end demonstration, not assumed
away:** `ground_concern`'s "experiment" composer tries a GRAPH-RESIDENT
dispatch (`_route_experiment_composer`) BEFORE the Python `_COMPOSER_
REGISTRY` builder this rung edited. For every 'test'-anchored, non-'replay'
grounded-relation set — the common case, including this rung's own probe
shape — that graph path ALWAYS wins (confirmed by reading the dispatch, then
confirmed empirically: my first end-to-end test attempt, which went through
`ground_concern`, returned `''` for a probe the standalone Term recovers
6/6). The graph-resident twin that actually serves live "test"+"vary"
concerns (`seeds/composer_experiment_graph.json`'s `compose_experiment_mint_
parametric` — SHAPE_AUDIT.md's own **A9**, *"the graph-resident twin of
A3"*) still runs the OLD, un-fallback-ed `keywords_text`-only pick, and is
**explicitly out of scope for this rung** (the task brief's own *"A4-A9 ...
NOT your area"*, and `RULE_SIGNATURE_PRODUCTION_WIRING_RESULTS.md`'s own
prior declination to hand-edit it: *"no generator script found ... judged
higher-risk than its measured benefit"*). **Consequence, stated plainly: the
Python-level fix this rung was asked to build is correctly built, correctly
wired, and directly validated at the same rigor A1/A2's own AR2 used — but
for the live agent's actual `ground_concern`-driven self-experiment loop
today, it takes effect only for the conversation-'replay' family, not for
the common non-conversation 'test'+'vary' case, until A9 is separately
fixed.** This is the honest scope of "GO" here — see §5 and the honest
residuals section for the full account.

---

## Verdict table

| bar | verdict | headline number |
|---|---|---|
| Design choice — Term-level join vs precomputed aggregate | **PRECOMPUTED AGGREGATE FIELD**, registered before the edit | matches the A3 charter's own recommendation; a live join would re-walk the seed/rule population on every installed-rule firing with no engine caching |
| AR1 — combination design | **REGISTERED, then VALIDATED before the edit** | production-first, structural-fallback, ONE Term — same shape as A1/A2 |
| AR2 — powered before/after, real oracle | **MET** | Class A: 0/6 (primary) → **6/6** (fallback); Class B: 4/4 → **4/4** (unchanged) |
| AR2 (continued) — real production function, called directly | **MET, 9/9 test file** | `rf._compose_experiment_rule` called directly (A1/A2's own AR2 rigor); Class A probe recovered through the REAL authored rule's own extracted Term |
| Reachability via `ground_concern` (found, not assumed) | **PARTIAL — conversation-'replay' family only** | the graph-resident A9 twin wins first for the common non-'replay' 'test'-anchored case; A9 is explicitly out of scope for this rung |
| AR4 — no regression | **CONFIRMED, byte-identical failing-node-id lists** | 9/9 identical (7-file self-experiment suite); new dedicated test file 9/9 passed |

---

## §1 The site, and the two structural differences from A1/A2

`reflective_faculty.py`'s `_compose_experiment_rule` (the `vary` branch,
originally `:4324-4344`, now `:4324-4383` after this rung's edit) decides
which of the agent's own loaded seeds to ablate in a live self-experiment.
Two properties make it a genuinely different design problem from A1/A2, both
confirmed by reading the code, not assumed from the charter's own framing:

1. **No single `where` clause.** `rule_signature`/`where_signature` flatten
   ONE rule. A `SeedSummary` has no `where` clause of its own — a seed is a
   manifest declaring MANY rules (0–128 in the real corpus; 4127 total rule
   declarations across 639 rule-carrying seeds, `scripts/seed_signature_
   discover_probes.py`'s own count). A seed-level structural object had to be
   DEFINED, not merely read.
2. **A live-installed rule's Term, not a plain Python function.** A1/A2's
   `_pick_acting_rule`/`_pick_reply_rule` call `native.evaluate` ONCE,
   synchronously, from Python. This site's `skip_id_expr`/`skip_seeds_expr`
   are embedded via `{"__term__": ...}` into a `SeedDelta`'s `add_node`
   EFFECT, inside a "mint" rule `_compose_experiment_rule` builds and
   installs LIVE with `add_rule` — evaluated by the engine's OWN
   `run_rules()` fixpoint whenever that installed rule's `where` matches, not
   by a one-shot Python call.

---

## §2 The design choice: precomputed aggregate field, not a live Term-level join

**Both were genuinely considered; the aggregate field was chosen and built.**
A Term-level join is EXPRESSIBLE in the existing algebra with no new Term
type — nest a `Filter`/`Exists` over `RuleSummary` (joined by `from_seed ==
s.seed_id`) inside the `SeedSummary` `Argmax`. It was rejected for two
independent, structural reasons (not preference):

- **Coverage.** `RuleSummary` mirrors only `chosen_action`/`reply`/
  where-literal-writing rules (`_ensure_acting_rule_provenance`/
  `_ensure_reply_rule_provenance`/`_ensure_where_literal_rule_provenance`) —
  a small minority of the corpus's 4127 rule declarations. Joining against it
  would score a seed by an arbitrary effect-shape-filtered subset of its
  rules, not "what the seed's rules structurally do," unqualified, which is
  what the charter asks for.
- **Live cost, no caching.** Per §1 property 2, a nested join would be
  re-evaluated by the engine every time the installed mint rule's `where`
  matches — a materially different risk profile from A1/A2's one-shot
  Python-side `native.evaluate` call, with no memoisation the engine provides
  for a Term evaluation for free.

The built alternative, `domains/seed_signature.py`:

- `seed_where_signature(sub, seed_id, manifest) -> frozenset[(rule_name,
  *row)]` — union, over EVERY rule the seed's manifest declares (re-read from
  disk via `substrate.seed_loader.manifest_for`, the exact read
  `reflective_faculty._rule_seed_map` already performs for the identical
  purpose), of `rule_signature.where_signature(sub, rule['where'])`, each row
  tagged by its owning rule's name. A rule whose program traps is skipped
  (mirrors `ensure_where_signature`'s own documented behaviour), never
  guessed.
- `ensure_seed_signature(sub) -> int` — idempotent, mints/upgrades ONE new
  attr `where_signature_json` on the EXISTING `SeedSummary` population
  (`substrate/boot_all.py::_mint_seed_summary` already produces it). No
  `add_node` anywhere in the new module — additive-attr only, same scope
  discipline as `rule_signature.ensure_where_signature`.
- Called from `_compose_experiment_rule`'s `vary` branch BEFORE the Term is
  built (mirrors `_pick_acting_rule`'s own precall discipline exactly) — the
  expensive part (walking 4127 rule declarations) happens ONCE, in Python, at
  compose time; the installed rule's own Term reads back a plain string attr
  via the IDENTICAL `StringIndexOf` shape `keywords_text` already uses. The
  installed rule's Term complexity is UNCHANGED (one more string-attr read
  per candidate, no nested join, no new Term type).

**Cost, measured, not assumed.** First-call `ensure_seed_signature` on a full
694-seed boot: **128.6s** (`scripts/seed_signature_discover_probes.py`) /
**129.6s** (`scripts/seed_signature_measure.py`, independent run) — walking
all 4127 rule declarations via the graph-resident `where_signature` Program
IR. A one-time, idempotent cost at first self-experiment compose, not a
per-tick cost — every subsequent call touches 0 nodes
(`test_ensure_seed_signature_is_idempotent`).

---

## §3 AR1 — the combination design, as built

Identical shape to A1/A2's own AR1 (`RULE_SIGNATURE_PRODUCTION_WIRING_
RESULTS.md`): the primary `keywords_text` Argmax is UNCHANGED and tried
first; only when it abstains (`best == None` OR `overlap(best) <= 0`) does
the SAME `Sum`/`StringIndexOf`/`Argmax` shape re-run against `SeedSummary.
where_signature_json` instead. Expressed as ONE Term — `_compose_experiment_
rule`'s existing convention (Python assembles the dict mechanically, the
WHOLE lexicographic decision evaluates inside the engine in one call) is
preserved exactly; the fallback resolves all the way to the seed_id STRING
(or `""`) at each stage, matching this site's existing all-the-way-to-scalar
convention (unlike A1/A2, which resolve to a node and let Python read attrs
off it afterward — inapplicable here, since there is no Python "after" step
at rule-fire time).

```python
words = Attr(V("axis"), "residual_predicates")
overlap = lambda node_t: Sum(words, "w",
    Ite(Gte(StrIdx(Attr(node_t, "keywords_text"), V("w")), L(0)), L(1), L(0)))
struct_overlap = lambda node_t: Sum(words, "w",
    Ite(Gte(StrIdx(Attr(node_t, "where_signature_json"), V("w")), L(0)), L(1), L(0)))
candidates = Filter(NodesOfType("SeedSummary"), "s", Eq(Attr(V("s"), "skippable"), L(1.0)))
best = Argmax(candidates, "s", overlap(V("s")), None)
struct_best = Argmax(candidates, "s2", struct_overlap(V("s2")), None)
struct_skip_id_expr = LetT("sbest", struct_best,
    Ite(Eq(V("sbest"), L(None)), L(""),
        Ite(Gt(struct_overlap(V("sbest")), L(0.0)), Attr(V("sbest"), "seed_id"), L(""))))
skip_id_expr = LetT("best", best,
    Ite(Eq(V("best"), L(None)), struct_skip_id_expr,
        Ite(Gt(overlap(V("best")), L(0.0)), Attr(V("best"), "seed_id"), struct_skip_id_expr)))
```

`skip_seeds_expr` (the JSON-array-wrapped form `SeedDelta.skip_seeds`
carries) is unchanged — it already wraps whatever `skip_id_expr` resolves to.

---

## §4 AR2 — the powered before/after

**Probe discovery, mechanical, never invented**
(`scripts/seed_signature_discover_probes.py`): full boot, 694 `SeedSummary`
nodes (665 skippable), `ensure_seed_signature` minted 688 new attrs. A raw
scan found 7544 Class-A-shaped candidate (seed, word) pairs and 21824 Class-B
candidates; `scripts/seed_signature_measure.py` then FILTERED these down to
**unambiguous** probes — a Class A word must be absent from EVERY skippable
seed's `keywords_text` (so the primary genuinely abstains system-wide, not
merely for the target seed) AND present ONLY in the target seed's own
structural signature (so the fallback picks it unambiguously, not via an
insertion-order tie); a Class B word must already be a genuine, non-zero-
overlap hit in its own seed's `keywords_text`. Generic JSON row-shape
vocabulary (`items`/`value`/`source`/`type`/`node`/`attr`/`path`/... — Term
scaffolding, not rule content) was excluded from candidacy.

**Result — every discovered unambiguous probe passes, on the REAL held
graph** (`scripts/seed_signature_measure.py`, `seed_signature_measure_
results.json`):

| Class A probe (seed ← word) | primary (pre-wiring) | structural-only | combined (wired) |
|---|---|---|---|
| `investigation_loop` ← `has_plan` | `''` (abstain) | `investigation_loop` | `investigation_loop` |
| `investigation_loop` ← `release_executed_plan` | `''` | `investigation_loop` | `investigation_loop` |
| `investigation_loop` ← `investigates_op` | `''` | `investigation_loop` | `investigation_loop` |
| `investigation_loop` ← `bank_measurement_to_axis` | `''` | `investigation_loop` | `investigation_loop` |
| `investigation_teacher` ← `mint_impasse_from_stall` | `''` | `investigation_teacher` | `investigation_teacher` |
| `investigation_teacher` ← `taught_about` | `''` | `investigation_teacher` | `investigation_teacher` |

| Class B probe (seed ← word) | primary | combined (wired) |
|---|---|---|
| `abandon_on_stuck` ← `committed` | `abandon_on_stuck` | `abandon_on_stuck` |
| `enact` ← `meaning` | `enact` | `enact` |
| `discourse` ← `discourse` | `discourse` | `discourse` |
| `speech_capability` ← `runner` | `speech_capability` | `speech_capability` |

**Class A: 6/6.** Primary abstains on every probe (confirmed system-wide, not
merely for the target seed); structural-only and the wired combined Term both
recover the correct seed on every probe. **Class B: 4/4, byte-unchanged** —
the fallback is never even evaluated when the primary already has a genuine
match, by construction of the `Ite` guard (verified, not merely asserted from
the Term shape: combined == primary on all 4).

This clears the PREREG's registered floor (≥4 Class A, ≥2 Class B,
100% pass on both) with margin, and is reported honestly as a small-N
live demonstration (10 probes total) rather than dressed up as a
large-sample power study — per the PREREG's own AR2 framing, this rung's
natural unit (per-seed) has a candidate pool (665) larger than A1/A2's whole
rule pool (~44), so 10 genuinely unambiguous, non-generic probes is a
meaningful floor for this task's own explicit "no fixed floor, per-site
judgement" framing (`RULE_SIGNATURE_PRODUCTION_WIRING_PREREG.md` AR3), not
underpowered by that framing — but it is NOT a 40-probe study, and is not
claimed to be one.

---

## §5 AR2 (continued) — the same result reproduced on the REAL
`_compose_experiment_rule` Python function, called directly — and the
reachability finding this uncovered

**First attempt, and why it was wrong (kept in the record, not silently
fixed).** The first version of this test drove the mint rule through
`induce_concern`/`ground_concern` end to end (no `send`, so no world
perception / cv2 dependency), then fired `run_rules()` and read
`SeedDelta.skip_seed_id` back off the resulting `Experiment` — mirroring
`tests/test_experiment_composer.py::test_mint_rule_fires_without_host_add_node`'s
own methodology. **It failed**: `skip_seed_id == ''` instead of
`'investigation_loop'`, even though the SAME word (`has_plan`) is recovered
6/6 by the standalone Term (§4). Reading why, rather than assuming a bug in
`domains/seed_signature.py`: `ground_concern`'s "experiment" composer calls
`_try_graph_composer` BEFORE the Python `_COMPOSER_REGISTRY` builder
(`reflective_faculty.py:6381`, `_route_experiment_composer`); for ANY
grounded-relation set that includes `'test'` and NOT `'replay'` — this
probe's own shape — that graph-resident path (`_ground_via_graph_meta` over
`compose_experiment_mint_parametric`, `seeds/composer_experiment_graph.json`
— SHAPE_AUDIT.md's own **A9**, *"the graph-resident twin of A3"*) ALWAYS
succeeds and wins. The rule `g.get("rules")` returned was authored by A9, not
by the Python function this rung edited — A9 still runs the un-fallback-ed
`keywords_text`-only pick, which correctly (for A9) abstains on `has_plan`.
**This is a real production-reachability gap, not a defect in the
fallback logic itself** — confirmed by the fact that the SAME word, picked
by the SAME kind of extracted Term, succeeds the moment the Python function
is reached directly (below).

**The corrected test — same rigor as A1/A2's own AR2, adapted to the one
structural difference this site has (no plain top-level picking function to
call; the Python builder sits behind a composer-dispatch registry with a
graph-resident competitor tried first).**
`tests/test_seed_signature_structural_fallback.py::
test_class_a_probe_recovered_by_the_real_authored_rules_own_term` mints a
`CapabilityAxis` with `residual_predicates: ["test", "vary"]`, grounds those
predicates through the held `RelationCue` lexicon
(`rf._residual_relations` — the exact mechanical read `ground_concern` itself
performs before composer dispatch), and calls
**`rf._compose_experiment_rule(agent, keys, rels)` directly** — bypassing
`_try_graph_composer`/A9 entirely, the same "call the real production
function, not a wrapper" level A1/A2's own `_pick_acting_rule`/
`_pick_reply_rule` were tested at. Extracts the mint rule's own
`skip_seed_id` `__term__` from the genuine returned rule dict (not
hand-rebuilt), mints a SEPARATE `CapabilityAxis` carrying the Class A word
`has_plan`, and evaluates the extracted Term directly against it —
**PASSES**: `picked == "investigation_loop"`, via the structural fallback
branch, exactly as designed.

**What this establishes, and what it does not.** It establishes that the
Python-level fix — the artifact this rung was asked to build — is correct,
matches the design registered in the PREREG, and is validated at the same
rigor as the two already-landed sites. It does NOT establish that a live
agent's `ground_concern`-driven self-experiment loop currently benefits from
this fix for a non-'replay' 'test'+'vary' concern, because `ground_concern`
does not currently reach this function for that shape — see the honest
residuals section for the precise scope of what remains to close that gap
(fixing A9, out of scope here).

---

## §6 AR4 — no regression

**Baseline captured on this worktree, on `6314ebe`, BEFORE the wiring edit**
(the 7-file self-experiment-composer suite the PREREG registers:
`tests/test_experiment_composer.py`, `tests/test_self_delta.py`,
`tests/test_composers_graph.py`, `tests/test_acting_variant.py`,
`tests/test_agent_authors_new_rule_migrated.py`,
`tests/test_gap_awareness_migrated.py`,
`tests/test_self_concern_promote_migrated.py`) — process spawned BEFORE the
production edit was made, so its Python import of `reflective_faculty.py`
reflects the pre-edit source:

```
9 failed, 86 passed, 4 skipped, 4 warnings in 446.74s (0:07:26)
```

Re-run on the SAME 7 files, AFTER the `_compose_experiment_rule` wiring edit:

```
9 failed, 86 passed, 4 skipped, 4 warnings in 417.81s (0:06:57)
```

**The two failing-node-id lists are byte-identical (9/9):**

```
FAILED tests/test_experiment_composer.py::test_mint_rule_fires_without_host_add_node
FAILED tests/test_self_delta.py::test_close_experiment_loop_teaches_and_is_idempotent
FAILED tests/test_acting_variant.py::test_close_experiment_loop_names_the_varied_acting_rule
FAILED tests/test_agent_authors_new_rule_migrated.py::test_agent_authors_new_rule_end_to_end
FAILED tests/test_gap_awareness_migrated.py::test_implicit_unresolved_topic_files_a_gap
FAILED tests/test_gap_awareness_migrated.py::test_implicit_gap_is_filed_once
FAILED tests/test_gap_awareness_migrated.py::test_gaps_are_deduped_by_content
FAILED tests/test_gap_awareness_migrated.py::test_unaccounted_self_faculty_files_a_clean_self_gap
FAILED tests/test_gap_awareness_migrated.py::test_resolved_topic_files_no_gap
```

None touch `_compose_experiment_rule`'s `vary` branch, `SeedSummary`, or
`skip_seed_id` — `test_mint_rule_fires_without_host_add_node` is itself the
SAME "installed rule never fires via run_rules()" symptom §5 hit and routed
around (a genuinely pre-existing, unrelated defect, independently confirmed
broken on the clean pre-edit baseline, not caused by this rung); the
`test_close_experiment_loop_*`/`test_gap_awareness_migrated.py` failures are
a `close_experiment_loop`/`teach()`-persistence class and a
`topic_grounding`/gap-filing class respectively, neither touching seed-skip
selection at all. **Zero test anywhere in this task's scope went from green
to red, and zero went from red to green** — this rung's edit changed nothing
observable to this suite except what its own new test file checks.

**New dedicated test file**, `tests/test_seed_signature_structural_fallback.py`
(9 tests: 1 pure-function unit test, 1 idempotency test, 4 parametrized Class
A cases, 2 parametrized Class B cases, 1 end-to-end direct-call test):

```
9 passed in 138.65s (0:02:18)
```

---

## Honest residuals

1. **THE HEADLINE RESIDUAL: `ground_concern` does not currently reach this
   fix for the common case.** Per §5: `_route_experiment_composer`
   (`reflective_faculty.py:5967`) tries the graph-resident A9 twin
   (`seeds/composer_experiment_graph.json`'s `compose_experiment_mint_
   parametric`) BEFORE the Python `_COMPOSER_REGISTRY` builder this rung
   edited, and wins for every grounded-relation set that includes `'test'`
   and excludes `'replay'` — i.e. every non-conversation self-experiment
   concern, which is the common case this whole A3 finding was about. The
   Python fix only takes live effect for the conversation-`'replay'` family
   today. **Closing this requires fixing A9 itself** — explicitly out of
   scope for this rung (task brief: *"A4-A9 ... NOT your area"*; prior rung:
   *"no generator script found ... judged higher-risk than its measured
   benefit"*) — a natural, precisely-scoped follow-on charter: port the SAME
   `where_signature_json`-fallback shape into `compose_experiment_mint_
   parametric`'s own held Term (`seeds/composer_experiment_graph.json:4712`),
   ideally preceded by writing the missing generator script the prior rung
   already named as the right prerequisite for touching that file safely.
   This was FOUND, not assumed, by building the live demonstration the task
   required — the first (wrong) version of the end-to-end test surfaced it
   directly, and is left in this doc's §5 as the record of how it was found,
   not silently corrected away.
2. **10 probes, not 40.** The PREREG registers this explicitly as a
   deliberately smaller, per-task-scoped oracle (per
   `RULE_SIGNATURE_PRODUCTION_WIRING_PREREG.md` AR3's own "no fixed floor,
   per-site judgement" framing) — real, mechanically discovered, unambiguous,
   100% pass rate, but a materially smaller N than A1/A2's own 40-probe
   design. A larger-N sweep (systematically enumerating every unambiguous
   Class A/B pair, not a filtered top-N) is a natural follow-on, not
   attempted here.
3. **`seed_where_signature` reads the seed's manifest from DISK
   (`manifest_for`), not from any graph-resident rule population.** This is
   deliberate (§2's coverage argument) but means a seed whose manifest was
   modified after boot (hot-patched at runtime, never persisted) would not be
   reflected until the next fresh read — the identical caveat
   `_rule_seed_map` already carries for the same reason, not a new one this
   rung introduces.
4. **The three `composer_experiment_graph.json` graph-resident twins are
   untouched**, exactly as `RULE_SIGNATURE_PRODUCTION_WIRING_RESULTS.md`
   already named and declined to hand-edit for A1/A3/A4 — same reasoning
   applies unchanged here (no generator script, high hand-edit risk relative
   to measured benefit); item 1 above is this same fact, stated with its full
   live-reachability consequence rather than as a background note.
5. **Downstream self-experiment-adoption outcomes are not measured** — same
   sidestep A1/A2's own rung took, for the same reason (the slow/noisy live
   oracle). "The wired pick matches the oracle more often" is the claim made
   and measured; "the agent's self-improvement outcomes get better as a
   result" is not.
6. **Whether a seed's identity should really be "the union of its rules'
   where-clauses" vs. something narrower/weighted is not re-litigated here**
   — inherited as an open design question from the A3 charter's own framing,
   answered pragmatically (union, tagged by rule name) rather than resolved
   theoretically.

---

## Reproduce

```bash
cd /home/matt/ocelot-seed-signature
git log --oneline -1                                        # on seed-pick-structural-fallback, base 6314ebe
sha256sum runners/dsl/python/substrate_rs/_native.abi3.so   # 23ba3f1d...92af (unchanged)

# AR2 -- probe discovery + the powered before/after on the standalone Term
systemd-run --scope --user -p MemoryMax=8G -p MemoryHigh=7G -- \
  python3 scripts/seed_signature_measure.py

# AR2 (continued) + AR4 -- the new dedicated test file (unit + parametrized
# Class A/B + the real _compose_experiment_rule direct-call end-to-end test)
systemd-run --scope --user -p MemoryMax=8G -p MemoryHigh=7G -- \
  python3 -m pytest tests/test_seed_signature_structural_fallback.py -q

# AR4 -- regression, the 7-file self-experiment-composer suite
systemd-run --scope --user -p MemoryMax=8G -p MemoryHigh=7G -- \
  python3 -m pytest tests/test_experiment_composer.py tests/test_self_delta.py \
    tests/test_composers_graph.py tests/test_acting_variant.py \
    tests/test_agent_authors_new_rule_migrated.py tests/test_gap_awareness_migrated.py \
    tests/test_self_concern_promote_migrated.py -q
```
