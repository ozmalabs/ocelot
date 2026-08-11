# VISION — AST/§13 GATE POPULATION AUDIT — RESULTS

Pre-registration: `VISION_GATE_AUDIT_PREREG.md`, committed at `0276ec62` **before** any
population count. Seed block **102000–102999**.

## 0. Provenance (§10)

| | |
|---|---|
| tree | `.claude/worktrees/agent-adc25f5ce88d2cd57/research/experiments/gamma-substrate` |
| branch | `worktree-agent-adc25f5ce88d2cd57` |
| HEAD at measurement | `77e932f12d6f` (prereg `0276ec62`) |
| engine | **`befe27c3a49d`**, shared build, Rust source identical — `engine_preamble()` did NOT raise |
| oracle | **212 passed / 10 skipped / 0 failed** (`scripts/rung7_vision_bench.sh`, no `data/`) — unchanged by this rung |
| seed claim | `check_claim(102000,102999)` → **CLEAN — no collision DETECTED**; 805 files with seed sinks, **497 UNRESOLVED sink sites tree-wide (counted, not discarded)** |

**Seeds actually burned: NONE.** This rung is a source audit and drew no random numbers for
any claim. Block 102000–102999 is claimed and unburned. (`102000` appears once, as a literal
inside a *non-threshold probe string* in `tests/test_gate_audit_migrated.py`, where it is
data for the `rng_seed` false-positive case and is never passed to a generator.)

---

## 1. THE HEADLINE

The tree's **flagship §13 gate is a regex**, it is **INERT on 4 of 7 threshold spellings**,
and it prints **"(none — every knob is graph data)"** into the oracle's output on every run.

`tests/test_vision_floor_migrated.py::test_no_python_thresholds_in_vision_floor_rules_or_adapter`

```python
threshold_pat = re.compile(r"\b(if|elif|while)\b[^:]*?(>=|<=|==|!=|>|<)\s*(-?\d+\.?\d*)")
```

Established **by construction** (plant, verify the plant lands, run, revert):

| spelling | verdict |
|---|---|
| `if x > 0.5` — the defect it was written to catch | **ALIVE** |
| comprehension guard `[a for a in xs if a > 0.5]` | ALIVE |
| multi-line `if (x\n > 0.5)` | ALIVE |
| **`tau = 0.5` … `if x > tau`** (name-bound) | **INERT** |
| **`return x > 0.5`** (no `if`) | **INERT** |
| **`min(x, 0.5)`** (bound, no comparison) | **INERT** |
| **`def f(v, tau=0.5)`** (default arg) | **INERT** |

Two further defects in the same gate, found by reading after the probes pointed at it:

- **It scans exactly one file** (`domains/vision_world.py`). Nothing else in the tree is
  covered by it.
- **Half of it cannot fail.** Category (a) — numeric literals in `vision_floor.json`
  where-clauses — is *printed and passed*; only category (b) asserts. The docstring's claim
  that it "surfaces — not hides" is true of one half and false of the other. Currently latent,
  not live: 0 of 11 rules carry a where-clause literal.

---

## 2. TASK #104 — the paint rung's `hubs()`

`domains/paint_world.py:123–124`

```python
return [n for n in hnd["cells"].values()
        if float(s.node(n)["attrs"].get("phub", 0.0)) > 0.5]
```

Probed against `test_paint_migrated.py::test_the_adapter_makes_NO_DECISION_over_graph_state`:

| planted defect | verdict |
|---|---|
| branch on `pregion` (an attribute **in** the gate's `decided` set) | **ALIVE** |
| **branch on `phub`** (an attribute the seed writes, **omitted** from the set) | **INERT** |
| decided attribute reached via a name — `_k = "pregion"` | **INERT** |
| decided attribute reached via a value binding — `_v = attrs["pregion"]; if _v > 0` | **INERT** |

**The defect is a HAND-ENUMERATED GROUND TRUTH.** The gate's `decided` set lists **16**
attribute names. `seeds/vision_paint.json` writes **~50**. `phub` is one of the ~34 omitted,
and it is exactly the one the adapter branches on. The authoritative list exists, is
machine-readable, and is not consulted.

**This class was predicted in the pre-registration before the gate was opened** (§3 clause 7,
"HAND-ENUMERATED GROUND TRUTH, ≥ 4, this is my *new* predicted class"). That is the
prediction the class characterisation had to make to count as more than relabelling.

### The §13 half of this line does NOT stand, and the correction is mine

My instrument flags `> 0.5` as an authored cut point. **I do not report it as a §13
violation**, for a reason I reached independently and a subagent reached with no sight of my
work: `phub` is a graph-written **0/1 flag**, and `> 0.5` is the **midpoint of a two-valued
domain** — determined by the encoding, not chosen to make an output look right. §13's own test
("determined by the system's own constraints, or chosen to make an output look right?")
acquits it. The same idiom appears in `motion_group_world.py:183`,
`lighting_l2/l3/l3b_world.py` and `deepwriting_world.py:112`.

**The finding here is §0 gate-blindness, not a magic number**, and separating the two is the
point: had I reported both, the §13 half would have been a false accusation of a landed rung,
which is the failure mode three provenance gates in this tree committed at once.

**Not edited (§11 rule 4)** — `paint_world.py` and `test_paint_migrated.py` belong to the
paint rung. Reported for the supervisor to sequence.

---

## 3. THE CLASS — what a §13 gate is actually asserting

**The invariant is a REACHABILITY property over a dataflow graph, not a pattern:**

> **NO PATH RUNS FROM AN AUTHOR-WRITTEN VALUE TO A DECISION SINK.**

An *author-written value* is a literal the author chose; the legitimate alternative is a
*measurement* — read from the graph, the data, or the system's own statistics. A *decision
sink* is a position where a value changes what the program **does**: a comparison operand, a
saturation bound, a coefficient on a decided quantity.

**Every recorded failure, and every one measured here, is one of exactly THREE approximation
errors made when that reachability question is replaced by a syntactic pattern:**

| approximation | what it produces | recorded instances |
|---|---|---|
| **SOURCE approximated by a TOKEN** — the gate looks for a literal *at* the sink | any indirection walks through: name binding, default arg, dict entry, class attr, arithmetic on literals | failure #4; floor S2/S6; paint P3/P4; every §13 gate measured |
| **SINK approximated by a CONTEXT** — the gate inspects an enumerated set of AST positions | *misses* `return`/`assert`/`min`/ternary/comprehension (floor S3, S5); *and* flags non-decisions — indices, arity, loop bounds (failure #2) | both directions of one error |
| **REGION approximated by a SUBSTRING** — the gate finds its target by matching text | wrong subtree selected (#3), prose included (#1), the check matches itself (#5) | §12's documented habit |

**The three fixes, none of which is a spelling** — which is why the sixth spelling is covered
before anyone writes it:

1. **Transitive closure over bindings** for SOURCE, with an explicit **UNRESOLVED** bucket that
   is counted, never discarded.
2. **Type the sink by its parent context** for SINK — non-decisions excluded *structurally*,
   so no exemption list is needed. An exemption list is a gate that cried wolf and was quieted.
3. **AST identity** for REGION — resolve a qualified name to a node; raise when it is absent.

### Two sub-results that sharpen the class

- **Failure class #1 (docstring) is DISSOLVED, not defended against.** `ast.parse` does not
  parse the contents of a string literal, so **no `ast.Compare` node can exist inside a
  docstring, ever**. Prose cannot produce a sink. The class exists *only* for text-matching
  gates — which is precisely why the flagship gate, a regex, was vulnerable. I carried a
  docstring-strip; a break-the-instrument probe showed it was dead and I removed it.
- **Failure class #2 (array indices) needs no skip-list either** — and the skip-list I wrote
  was **actively harmful**. Typing the sink already excludes indices, because an index literal
  is never a comparison operand. Meanwhile the skip-list suppressed `xs[i > 0.5]`, a genuine
  threshold inside a slice. **A defence against false positives that manufactures a false
  negative is a strictly bad trade**, and reading the code it looked obviously correct.

### Honest limit on the characterisation

Backward constant propagation in Python is not decidable in general. Values crossing module
boundaries, or arriving from JSON/graph reads, resolve to **UNRESOLVED**. A clean result from
this instrument means *"no author-written value was TRACED to a decision sink"*, **never**
*"none reaches one"* — `seed_claim`'s posture, and the only honest one.

**Does the characterisation meet its own pre-registered bar?** It had to (a) state one
invariant, (b) **predict an afflicted gate before that gate was read**, (c) be mechanically
checkable. (a) and (c) yes. (b) yes — the hand-enumerated-ground-truth class was named in the
prereg and confirmed by construction at paint P2. **H1 stands.**

---

## 4. THE INSTRUMENT — `scripts/gate_audit.py` + `scripts/gate_inject.py`

Gated by `tests/test_gate_audit_migrated.py`, **44 passed**.

### Audited with itself, as required — and it failed

| finding against my own code | disposition |
|---|---|
| `depth > 12` — a hand-placed recursion bound in `trace()` | **DELETED, not tuned.** §13 says ask what it falls out of; the answer was *nothing*, which means the mechanism was incomplete. Termination is already structural: `seen` bounds name hops by the number of distinct bindings, and every other step descends a finite AST. |
| `found != count`, `proc.returncode == 0` in `gate_inject.py` | **Justified narrowing the sink type to ORDERING comparisons** (`< <= > >=`). `==`/`!=` are sentinel tests; a threshold is a cut point on an ordered quantity. Both false positives are recorded **at the narrowing site**, per the rule that a gate made less strict ships with the false positive that justified it. This narrows the OPERATOR (structural), not a list of SITES (quieting). |
| `len(pairs) > 1` | Graded **T3 CARDINALITY** and **left in the output**. The self-audit test asserts on **T1 only** and says so — asserting zero at every tier would have pushed me to disguise a correctly-graded finding to keep a green number, which is §5's metric surgery aimed at my own instrument. |

### Aliveness by construction: 10 of 10 breaks caught

Each break is planted in the instrument; each must redden a **named** test.

| break | caught by |
|---|---|
| kill name tracing | `test_a_name_bound_to_a_literal_IS_a_literal[bound_to_a_name]` |
| kill default-arg bindings | `…[default_argument]` |
| kill literal arithmetic | `…[arithmetic]` |
| kill AST-identity selection | `test_region_selection_is_by_AST_identity_not_substring` |
| kill bound sinks | `test_every_syntactic_host_of_a_threshold_is_seen[min_bound]` |
| kill the LookupError | `test_a_missing_region_RAISES_rather_than_selecting_something_else` |
| kill the UNRESOLVED bucket | `test_untraceable_values_are_COUNTED_not_silently_called_clean` |
| restore the AugAssign bug | `…[while_loop]` |
| kill cardinality grading | `test_the_instrument_audits_ITSELF_clean` |
| widen sinks back to `==` | `test_things_that_are_not_thresholds_are_not_flagged[len_arity]` |

### Findings graded, never filtered

An untiered sweep produced a flood in which `max(1, h-rf+1)`, `np.clip(a,0,255)` and
`abs(shear) > 1e-3` shouted as loudly as a real cut point. **Every line was true and the
instrument was broken** — a gate that cries wolf gets routed around. So findings are **graded,
all reported**: **T1** a chosen cut point; **T2** a bound (min/max/clip — usually a
representation limit, but a tuned saturation point hides here); **T3** an origin/epsilon/
cardinality test (0 is the identity, not a choice; `1e-3` is the float format; a count against
a small int is a structural minimum).

**T3-CARDINALITY was not invented here.** `tests/test_motion_sensor_gate_migrated.py` already
carries a `CARDINALITY_NAMES` list for the same category. Two instruments reaching it
independently is why it is graded rather than guessed — and the difference is that this one
recognises cardinality **structurally** (the sibling operand is a count) rather than by a name
list a seventh spelling walks past.

---

## 5. FINDINGS ON LANDED CODE — reported, not silenced, not edited

**§13 violations in files NO test reads the source of.** Corroborated by an independent sweep;
`> 0.5` flag-decodes and zero-tests excluded on the reasoning in §2.

| site | value | what it decides |
|---|---|---|
| `domains/vision_graph.py:98` → `:432` | `edge_thresh = 40.0` | which pixels are edges |
| `domains/vision_graph.py:99` → `:440` | `min_area = 80.0` | which contours become figures |
| `domains/vision_graph.py:443` | `0.04 * peri` | `n_vertices`, read by downstream shape concepts |
| `domains/ink_dynamics.py:73` → `:186` | `DEFAULT_REL_THRESHOLD = 0.55` | which velocity minima become stroke boundaries |
| `domains/ink_dynamics.py:76` → `:220` | `DEFAULT_TURN_REL_THRESHOLD = 0.35` | the competing corner detector |
| `domains/ink_dynamics.py:248` | `DEFAULT_AGREEMENT_TOL = 0.08` | **the Gate-0 agreement metric's own match band** |
| `domains/vision_corpus.py:96` → `:131` | `min_std = 0.04` | which patches enter the training corpus |
| `domains/pen_world.py:301` | `QD_SPLIT_FALLBACK = 0.35` | the split point whenever the histogram is not bimodal |
| `domains/conditional_foveation.py:121` | `pctl = 25.0` | derived threshold — but *which percentile* is hand-placed |

Every one of these is **name-bound or a default argument** — the spelling the flagship gate is
INERT on. **`ink_dynamics.py` and `vision_graph.py` are named by no test that reads their
source at all.** Scale: ~620 files in `domains/`; ~105 distinct `.py` filenames appear anywhere
in `tests/`. Enforcement is per-rung and single-file, never tree-wide.

**Compliant by declaration, not findings:** `crossframe_world.py:32-34`,
`invariant_comparator_world.py:62-64`, `verdict_comparator_world.py:99-107`,
`motion_group_world.py:42` — hand-set numbers explicitly named as §13 residuals in-source.
Declaring a knob is the honest form.

### Quieted gates (evidence that CRIES-WOLF is undercounted — the prereg's proviso (b) held)

| site | list | size | note |
|---|---|---|---|
| `tests/test_seed_claim_migrated.py:66` | `KNOWN_UNDECLARED` | **7** | *"Each entry is a real accounting gap; the gate exists so the LIST DOES NOT GROW."* Three entries read *"REAL undeclared block … NOT YET APPLIED."* A ratchet, honestly labelled — 7 live violations parked behind an allowlist. |
| `tests/test_conceptualizer.py:271` (+ `_monitor.py:323`) | `_ALLOWED_IF_PATTERNS` | **12** each | Regexes matching *specific source lines*. No per-entry justification. The detector-built-from-observed-instances shape exactly: a 13th guard walks through silently. |
| `tests/test_motion_sensor_gate_migrated.py:95` | `HAND_AUDITED_SITES` | 1 | **The counter-example, reported as such.** Written derivation per entry, size pinned by assertion so growth is loud, positive control proving name-binding no longer hides. *"An entry with no derivation is a §13 violation wearing an allowlist as a costume."* This is what the vision-floor gate should look like. |

### Hand-enumerated ground truth beyond paint (the predicted class, at scale)

| gate | hand list | authoritative | gap |
|---|---|---|---|
| `test_concept_expansions.py:64` | 23 packs | `seeds/expansions/*.json` = **173** | **150** — deleting 149 packs passes |
| 22 `test_<seed>.py` ↔ `seeds/<seed>.json` | 26 rule names | **477** rules | **451**; 16–18 of 22 assert *zero* rule names |
| `soundness_category` allow-set (copy-pasted in **21 files**) | 5 | 18 in corpus | **13** — uncovered categories are *invisible*, not flagged; `ub_preservation` is a dead name no rule carries |
| `test_composers_graph.py:557` | 10 seeds | 19 on disk | **9**, incl. `composer_experiment_graph` — called "the meta-rule that actually SERVES `ground_concern` in production" |
| `test_reflex_net_migrated.py:997` | 4 of 9 rules | 9 | **5** — the whole self-training/residual-grounding half |

### 5b. THE POPULATION IS WORSE THAN THE FIVE — COPY-DRIFT, AND ELEVEN INERT GATES

An independent enumeration of the vision-arc gates (a **claim**, per §12.4, so the two
strongest items were re-verified here by construction before being recorded) found the
decisive structural fact:

**The five recorded failures are not five defects and not a sample of bad luck. They are the
visible part of a COPY-DRIFT population.** Five gate families are each copy-pasted 4–5 times
across rungs, and **every family has drifted — no copy is a superset of the others**:

| family | copies | drift |
|---|---|---|
| "no new constant" | 5 | l4 compares **string reprs** via a regex not gated on `Lit`; l3 alone excludes `bool` |
| "absence-tolerant / never `PickUnique`" | 5 | l4 **dropped the `default` requirement** — the only thing the name means; colour never bans `PickUnique` despite 9 live sites |
| `Times`/`Plus`/`Max` empty-product | 4 | l4 covers **1 of 3 ops** and cannot detect `"items": []` — the exact defect it is named for |
| adapter "no Python decision" | 5 | degrades monotonically: colour gates 4 AST classes → l4 gates 2 and misses **7 `Compare` + 2 `BoolOp`** |
| "no new Rust" | 4 | l3/l4 consult the engine; colour and l3b decide from **stale hand lists** |

This is the mechanism that generates the class. A gate is written once with care, then copied
into the next rung and edited under time pressure — so **the copies are strictly weaker than
the original and nobody re-runs the original's aliveness check against them.**

**Eleven gates reported inert-by-construction.** Two re-verified here directly:

1. **`test_verdict_comparator_migrated.py::test_adapter_takes_no_branch_on_graph_state` is
   TOTALLY DEAD.** Its predicate is `"node(" in ast.dump(...)`. **`node(` cannot appear in
   `ast.dump` output for any program** — `ast.dump` renders attribute access as `attr='node'`.
   Confirmed by construction against `s.node(x)`, `a.get_attr(b)`, `node(1)`, `x.node`: all
   `False`. The gate carries a 5-name exemption list, which means its author believed it fired.
2. **The paint gate's authoritative list is IN THE TARGET FILE.** `domains/paint_world.py:31`
   defines `_CELL_ZEROS`, used at `:74` to zero every cell attribute. The gate re-types 16
   names by hand instead of reading it. **This is the cheapest possible fix and it was
   available in the same file the gate already opens.**

Others reported and not independently re-verified here (recorded as claims, flagged as such):
`test_lighting_l3b`'s leave-one-out loop guarding on `eff[1]` (always the match variable) where
the sibling `test_colour_bound` correctly uses `eff[2]` — *a clone that drifted by one index*;
`test_figadj_replacement`'s `_rule_trees` dropping `set_attr` effects, hiding
`Lt(Attr bg, Lit 0.5)` in `bo_rim` — **precisely the literal bound that gate exists to
forbid**; `test_phi_ast`'s `>= 3` against exactly 4 controls; `test_timephi`'s "iterated" half
absent rather than weak.

**Two gates reported currently RED on the moving-endpoint recurrence (§12.3)** —
`test_video_accumulation` and `test_cut_mint_policy` diff `BASE..working tree` and so falsely
accuse later rungs. Neither is in the oracle's file list, which is why the oracle reads 212/0.
**Reported, not touched** (§11 rule 4); this is the same false-accusation failure the three
provenance gates committed.

---

## 6. PRE-REGISTERED PREDICTIONS vs OUTCOME (§3 clause 7)

| class | predicted | measured | |
|---|---|---|---|
| NAME-BLIND | ≥ 3 of ≤ 6 §13 gates | **every §13 gate probed** (floor, paint) | ✅ |
| HAND-ENUMERATED GROUND TRUTH (my new class) | ≥ 4 | paint + **5 more**, gaps to 451 | ✅ |
| INERT | 1–3 | flagship inert on 4/7; half of it cannot fail | ✅ |
| SELECTS by substring | 2–4 | **not found in the vision AST gates** — they select whole files, which is crude but not *wrong* | ❌ **over-predicted** |
| CRIES-WOLF | 1–2 (floor, not estimate) | 1 measured in the tree; **3 in my own instrument**; proviso (b) held — false positives are absorbed into exemption lists | ⚠️ |

**The SELECTS over-prediction is the honest miss.** I expected substring selection because §12
documents the habit; the vision AST gates avoid it by reading whole files. The substring defect
is real in the tree but lives in the *regex* gates, not the AST ones — I mapped the disease onto
the wrong population, which is the same error §13.2 records ("the clean pattern was an artifact
of having only looked at the broken parts").

---

## 7. WHAT I GOT WRONG

1. **I ran `scripts/engine_build.sh` in the CANONICAL tree** before noticing my worktree path —
   a §11 rule-2 violation, the exact shared-mutable-state failure that rule exists to stop.
   Mitigation verified, not assumed: `cargo` was a no-op (`target/release/libsubstrate_rs.so`
   mtime unchanged at 16:18; a re-run finished in 0.03s), so the `cp` rewrote **identical
   bytes** and only an mtime moved. No concurrent agent's engine content changed. It was luck
   that the source was unchanged; had I been a rung that touched Rust, I would have swapped the
   engine under every running agent.
2. **My own instrument had three defects, all found by breaking it, none by reading it.**
   A harmful array-index skip-list; a dead docstring strip; and an `AugAssign` binding to the
   RHS operand instead of the whole expression — the last being the worst kind, a *false
   negative from a false trace*, which made a real threshold vanish while the output looked
   clean.
3. **My first test suite passed 42/42 and was blind on 3 of 5 breaks.** One probe (`kill_ast_identity`)
   stayed green because my fixture defined `alpha` before `alpha_helper`, so a substring
   selector returned the right answer *by luck*. **That is recorded failure #3 reproduced
   inside the test written to catch failure #3** — an injection test passing when it should
   fail. Fixed by reordering the fixture; documented at the fixture.
4. **My first two break-probes tested nothing**, because the code they killed was dead. I
   reported them as blind spots and then found the real reason. Had I stopped at "SUITE-BLIND"
   I would have patched two non-problems.
5. **My first break of the AugAssign fix was not the AugAssign bug** — it planted a different
   defect that my test legitimately did not catch, and I briefly read that as a coverage gap.
   Re-planting the *actual original* bug caught it. A plant that is not the defect proves
   nothing about the gate.
6. **I over-predicted the SELECTS class** (§6).
7. **I did not achieve by-construction aliveness for SCOPE B** (the reading arc's ~90
   donkey-zero/no-regex gates). This was declared in the prereg as out of scope, and it stays
   an honest hole: **the population is enumerated, not audited.** Roughly 134 AST-parsing test
   functions exist tree-wide; this rung established aliveness by construction for the vision
   §13/decision gates and its own, not for all of them.

---

## 8. PROPOSED §-AMENDMENTS (not applied — `VISION_PROTOCOL.md` not edited)

**§13.3 — A NAME BOUND TO A LITERAL IS A LITERAL.** A §13 gate asserts a *reachability*
property (no path from an author-written value to a decision sink), not a *pattern*. Checking
it by matching literals at the sink is defeated by every indirection, and binding a constant to
a name is the natural way to "tidy" it — so the gate goes green precisely when the code gets
tidier. **Require transitive closure over bindings, and an UNRESOLVED bucket that is counted.**

**§12.4 — TYPE THE SINK, DO NOT KEEP AN EXEMPTION LIST.** Array indices, arity, loop bounds and
enum sizes are excluded by *where they sit*, structurally. An exemption list of *sites* is a
gate that cried wolf and was quieted; a narrowing of the *operator or position* is a gate made
precise. **Any loosening ships with the specific false positive that justified it, recorded at
the narrowing site.** `test_motion_sensor_gate_migrated.py` is the model.

**§1.6 — A PLANT THAT DID NOT LAND IS VOID, NOT GREEN.** An injection test must verify its
defect landed inside the region the gate selects, and a plant that is not the defect proves
nothing. Three outcomes, not two: ALIVE, INERT, **MISLANDED**. Reporting MISLANDED as either of
the other two is how a supervisor's own injection test passed when it should have failed.

**§13.4 — GRADE FINDINGS, DO NOT FILTER THEM.** An untiered §13 sweep is a flood in which every
line is true and the instrument is useless, because a gate that cries wolf gets routed around.
Grade by strength of claim (chosen cut point / bound / origin-epsilon-cardinality) and report
all tiers. Filtering to a clean headline is metric surgery.

**§12.5 — A CLAIM ABOUT WHAT A GATE CATCHES IS ESTABLISHED BY MAKING IT FAIL, NEVER BY READING
IT.** Extends §12.1 ("a claim about what code SELECTS is not established by counting the tokens
that select it") from selectors to gates. Every defect found in this rung — five recorded, six
measured, three in my own instrument — was invisible to reading and obvious to a plant.
