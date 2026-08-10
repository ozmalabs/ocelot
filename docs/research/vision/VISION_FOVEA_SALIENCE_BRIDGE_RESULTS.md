# RESULTS — the fovea/salience bridge: the fovea decision MIGRATED Python→graph, resolved by the LOG-WEIGHTED ADMISSIBILITY GRAPH (160000)

**Branch `gamma-substrate/fovea-salience-bridge`, base HEAD `4bc702a8bf`.**
**`SEED CLAIM 160000-160999 CLEAN`** (581 unresolved sink sites, priced per §3 clause 8 —
full `check_claim`/`seed_claim.py` output in `VISION_FOVEA_SALIENCE_BRIDGE_PREREG.md`).

## Engine (§10)

`engine 64dbce1e7f47 @ .../runners/dsl/python/substrate_rs/_native.abi3.so` — **`shared`
build, Rust source identical** to canonical. `source_match ∈ {own, shared}` holds as
`shared` (this rung adds **NO Rust** — pure composition of existing DSL Terms). The coarse
path is byte-identical.

## Oracle — UNMOVED (222/0 both sides)

- **BEFORE** (`bash scripts/rung7_vision_bench.sh`, base `4bc702a8bf`): **212 passed, 10 skipped** = 222/0.
- **AFTER** (same, with the seed + adapter + gate added): **212 passed, 10 skipped in 156.99s** = 222/0.

No Rust added, no existing tracked file edited (only 5 new files) ⇒ the engine is `shared`,
byte-identical; the oracle is unmoved by construction and by measurement.

## The migration (the point of the rung)

159000 proved salience-driven foveation but SELECTED the fovea with a numpy `argmax`/top-K
in Python — `scripts/salience_foveation_probe.py::select_fovea`'s
`scored.sort(key=lambda s: -s["peak"])[:top_k]`. That `sort` is an agent DECISION in Python,
which CLAUDE.md forbids. This rung moves that SELECTION into the graph.

## MACHINERY MAP (STEP 1) — what existed, what I composed

| piece | file | what it provides | how the bridge uses it |
|---|---|---|---|
| **Γ — weighted admissibility grammar** | `runners/dsl/src/grammar.rs` | *"selection over admitted candidates is ∝ exp(w)"*; a `Production` = `(src, edge, tgt, where, weight:Term)`; the index gives C its O(\|Γ\|) bound | THE frame for the whole rung. The fovea resolves by `∝ exp(w)`; its **MAP reading is `argmax_w`**. Declared a `FoveaResolver -has_candidate-> FoveaCandidate` production (Γ vocabulary/admissibility). |
| **C — consistency checker** | `runners/dsl/src/checker.rs` | admits/denies a prospective edge under Γ (Type-1 no-production / Type-2 vocabulary-absent) | **Observed live**: before I declared the production, `s.add_edge` raised `Γ rejects: type 'FoveaResolver' not in vocabulary (Type-2)`. Γ genuinely gates — it is not decorative. |
| **`ArgminUnique`** | `runners/dsl/src/argmin_tie.rs`, `term.rs` (variant + eval ~8155) | `Argmin` that **refuses a tie** (returns the null when the extremum is not unique — *a comparison can be false, a selection cannot*) | the resolver: `ArgminUnique(admissible-candidates, Neg(w))` = the highest-log-weight admissible candidate, **refusing** two exactly-equal candidates (fall back to coarse). |
| **`Argmax`/`Argmin` eval** | `term.rs` ~4903/8162 | selects the ELEMENT maximising a `value` Term over a source set | the shape the resolver follows (element-returning fold over graph nodes). |
| **`order_n_shape_salience` / `Substrate.shape_salience`** | `runners/dsl/src/memory.rs:322`, `py.rs:7290` | the surprise / value signal (log-evidence source) | the conceptual source of the candidate log-weight; here the concrete bottom-up evidence is 157000's residual tangential magnitude (the salience FIELD), `Log`-mapped. |
| **`effort_dial` / salience gating** | `runners/dsl/src/effort_dial.rs` | folds `order_n_shape_salience` with a salience threshold (spend effort ∝ surprise) | the precedent that salience gates spend; the fovea is the spatial instance (foveate the salient). |
| **motor_value precedent** | `seeds/motor_core.json` (`motor_value_term`), `domains/spatial_routing.py` | a **graph-resident value Term-tree resolved in the ENGINE's argmax** — Python is a thin adapter that fires the term and reads the result | the pattern this rung follows exactly: the fovea `value` (log-weight) is a graph-resident Term-tree, resolved by the engine's `ArgminUnique`, NOT a Python argmax. |
| **DSL Terms** (`ArgminUnique`, `Filter`, `Neighbours`, `Log`, `Plus`, `Neg`, `Attr`, `Eq`) | `term.rs`, `jsonio.rs` | all present + JSON-parseable; `Log(x)=ln x` for `x>0` else `−∞` | the log-weight combination is a Term-tree — **no new primitive needed**. |
| **`select_fovea` (retired)** | `scripts/salience_foveation_probe.py:148` | the numpy extraction (`flag_movers`→connected-components→per-region peak/box) + the `sort[:top_k]` SELECTION | the extraction is reused (mechanical ingest, `domains/fovea_bridge.py::extract_candidates`); the `sort` SELECTION is what moved to the graph. |

## THE BRIDGE DESIGN — what graph data / Terms, what it composes

**Ingest (mechanical world-adapter I/O, `domains/fovea_bridge.py`):**
`extract_candidates(salience, valid)` runs 159000's own extraction — `flag_movers` → connected
components → per-component peak/box/region — the SAME code `select_fovea` runs BEFORE its sort.
Each salient region becomes the smallest graph token: a `FoveaCandidate` node edged
`res -has_candidate-> c` carrying `salience` (bottom-up log-evidence source), `on_valid` (the Γ
admissibility datum), `goal_logweight` (top-down bias, default 0). No conditional over graph
state, no selection — pure translation.

**Resolution (GRAPH-NATIVE, `seeds/fovea_salience_bridge.json` rule `fovea_resolve`,
one `run_rules` fixpoint):** each candidate `c` is flagged `is_fovea=1` iff
`And( admissible(c), Eq(c, winner) )` where
```
winner  = ArgminUnique( source = Filter(Neighbours(res, has_candidate), k, admissible(k)),
                        value  = Neg( Log(Attr(k,"salience")) + Attr(k,"goal_logweight") ) )
admissible(x) := Eq(Attr(x,"on_valid"), 1)              # the Γ consistency where-clause
```
`Filter` on the admissibility where-clause **gates BEFORE weighting** (an inadmissible candidate
never enters the fold); `ArgminUnique(Neg(w))` = `argmax_w` = the MAP reading of Γ's
`selection ∝ exp(w)`, and it **refuses a log-weight tie**. `Eq` compares `Value::Node` by id, so
exactly the one winning node is flagged. `set_attr is_fovea=1` is idempotent ⇒ self-terminating.

**Reused vs added:** reused ALL of it — `ArgminUnique`, `Filter`, `Neighbours`, `Log`, `Plus`,
`Neg`, `Attr`, `Eq`, the seed-manifest `productions`/`rules` loader, `boot_core`,
`select_fovea`'s extraction. **Added: NO Rust.** New graph data only (one production + one rule)
+ a ~150-line world adapter + the gate. Composition was sufficient because the log-weighted
admissible selection is exactly `ArgminUnique over Filter`, and the log-weight is exactly
`Log(salience)+goal_logweight` — every piece already existed as a Term.

## A1 — GRAPH-NATIVE DECISION (the headline). PASS.

The fovea target is READ from the graph attr `is_fovea` the engine's rule sets; NO Python
`argmax`/`max`/`sort`/`>` decides it. The resolution path is:
```python
def resolve_fovea(cands, goal_logweights=None, admissible=None):
    if not cands: return None
    s, ag, native = _boot()                       # loads seeds/fovea_salience_bridge.json
    res = s.add_node("FoveaResolver", {})
    ids = ingest_candidates(s, res, cands, goal_logweights, admissible)   # translate only
    native.run_rules()                            # THE ENGINE decides (ArgminUnique)
    return read_fovea(s, ids)                     # read is_fovea==1 back — no selection

def read_fovea(s, cand_ids):
    for cid in cand_ids:
        a = s.node(cid)["attrs"]
        if float(a.get("is_fovea", 0.0)) == 1.0:  # a READ, not a decision over weights
            return a
    return None
```
Audit (gate `test_A1_*`): (i) `resolve_fovea`/`read_fovea`/`ingest_candidates` contain no
`argmax`/`sort`/`max(`/`min(` — source-scanned, able to fail; (ii) the seed rule's `where`
contains `ArgminUnique` + `Log`+`salience` + `goal_logweight` + `Filter`+`on_valid`; (iii)
STRUCTURAL: ingest **without** `run_rules` ⇒ `read_fovea` is `None`; only `run_rules` produces a
fovea. The decision is the engine's. (`extract_candidates` uses `np.argmax` for the per-region
PEAK LOCATION — mechanical peak-finding within a region, NOT the fovea selection among regions;
it is the ingest, explicitly out of the audited resolution path.)

## A2 — IT WORKS (scored by ground truth). PASS on synthetic; EXACT reproduction on E1M1.

| scene | numpy `select_fovea` top-1 | graph fovea | agree | on GT object |
|---|---|---|---|---|
| synthetic one-mover | `[41, 24]` | `[41, 24]` | ✓ | ✓ (GT mover cell) |
| synthetic two-mover (unequal, real selection among 2 candidates) | `[21, 27]` | `[21, 27]` | ✓ | ✓ (the faster/more-salient mover) |
| **E1M1 (real WAD)** | — | — | **146/146 frames** | see note |

The graph does EXACTLY what the retired numpy argmax did — `argmax Log(s) = argmax s` because
`Log` is monotone, and both consume the identical candidate set. On the synthetic scenes the
graph fovea lands on the GT mover. On E1M1 the graph reproduces numpy's top-1 on **all 146
tested frames** — the migration is faithful.
**Honest note on E1M1 object-landing:** on the 4 imp-present frames NEITHER numpy top-1 NOR the
graph lands on the imp (0/4). That is numpy `select_fovea`'s OWN top-1 behaviour — 159000's
documented finding that mover-salience is TASK-RELATIVE and the small sub-coarse-cell imp needs
an appearance cue to point — reproduced faithfully by the migration, NOT a regression it
introduced. A2's object-landing claim is carried by the synthetic scenes (where select_fovea
does land); on E1M1 A2 is the exact-reproduction claim (146/146).

## A3 — LOG-WEIGHTED CO-PRESENCE, not selection ("both, not X-or-Y"). PASS.

Two co-present admissible candidates A (`Log s_A = 2`) and B (`Log s_B = 1`); sweep a co-present
top-down goal log-weight `g` on B (`w_B = 1 + g`, `w_A = 2` fixed):

```
    g   w_B   winner   note
 0.00  1.00      A     A>B      (bottom-up alone -> the salient)
 0.25  1.25      A     A>B
 0.50  1.50      A     A>B
 0.75  1.75      A     A>B
 1.00  2.00  REFUSE    tie(w_A=w_B)   <- ArgminUnique refuses the exact tie
 1.25  2.25      B     B>A
 1.50  2.50      B     B>A
 2.00  3.00      B     B>A
 3.00  4.00      B     B>A
```

(i) bottom-up alone → fovea on the more salient (A). (ii) the co-present top-down goal shifts the
resolution **CONTINUOUSLY and MONOTONE** in `g`: `w_B = 1+g` rises linearly, the winner flips
A→B **exactly at the log-weight crossover** `g = Log s_A − Log s_B = 1.0` (where the two are tied
and ArgminUnique refuses) — the override is a **weight-shift, not a switch**, and once B wins it
never reverts. (iii) **the race**: a strong bottom-up A (`w=5`) beats B carrying a top-down
`g=2` (`w=1+2=3`) — the highest log-weight admissible candidate wins whichever way it arrived.
All graph-computed. §13: `g` is a SWEPT parameter (monotonicity is the claim), not a magic
number.

## A4 — ADMISSIBILITY GOVERNS (Γ gates before weighting). PASS.

Two co-present candidates, B far more salient than A (`Log s_B = 9` ≫ `Log s_A = 2`). With BOTH
admissible, B wins (higher weight). Mark B **inadmissible** (`on_valid=0` — a fovea target on an
unobserved cell violates the consistency constraint *you cannot foveate what you have no valid
observation of*): the `Filter` excludes B from the fold **before** the weighting, so the
lower-weight admissible A wins. A high-weight inadmissible candidate never wins.
Corroborated structurally: Γ's checker C also gates at the **vocabulary** level — the
`FoveaResolver -has_candidate->` edge was Type-2-rejected until its production was declared
(observed live). Admissibility is Γ (a declared consistency constraint + a where-clause), not a
tuned filter.

## §13 — every number falls out

- `salience` = 157000's measured residual tangential magnitude; not tuned.
- `w = Log(salience) + goal_logweight`; `Log` is the CROSS-FRAME map to log-evidence (frame/
  continuum invariant), so `exp(w) = salience·exp(g)` — selection ∝ salience (grammar.rs). No
  constant.
- `g` (A3) is SWEPT; monotonicity, not a value, is the claim.
- admissibility = `on_valid==1`, a declared consistency predicate; no threshold.
- the extraction floors (`FOVEA_MIN_HALF`/`MIN_REGION`/`SAL_FLOOR`) are 159000's already-declared
  geometric/rounding floors, inherited unchanged.

## WHAT I GOT WRONG

1. **I assumed `add_edge` was unconstrained; Γ rejected it.** My first `resolve_fovea` raised
   `Γ rejects: type 'FoveaResolver' not in vocabulary (Type-2)` — I had not declared a
   production. This was a GIFT: it proved Γ's checker genuinely gates (not decorative, unlike the
   FM-0 "wired to nothing" hazard), and it forced the admissibility to be a REAL declared Γ
   production, which is exactly what A4 needed. Fixed by adding the `has_candidate` production.
2. **I over-expected the E1M1 object-landing.** I predicted the graph would land on the imp;
   it does not at top-1 — but neither does the numpy baseline (0/4). The migration is EXACT
   (146/146); the object-landing gap is `select_fovea`'s own top-1 limitation (159000's
   task-relativity), and A2's landing claim is honestly carried by the synthetic scenes only.
   I did NOT rescue this by widening K or changing the metric (§5) — I reported it.
3. **The "log-weighted" could have been vacuous** (salience is already monotone in its own
   argmax). It is NOT vacuous: `Log` makes the top-down combination ADDITIVE (log of a product
   of evidences), which is what makes A3's override a continuous monotone weight-shift with a
   crossover, rather than a hard switch — the whole point of "both, not X-or-Y".

## Proposed VISION_PROTOCOL.md ledger row (EXACT existing style)

- **THE FOVEA DECISION MIGRATED Python→graph, RESOLVED BY THE LOG-WEIGHTED ADMISSIBILITY GRAPH
  (2026-07-23, `VISION_FOVEA_SALIENCE_BRIDGE_PREREG.md` / `_RESULTS.md`, seeds 160000–160999,
  engine `64dbce1e7f47` **`shared`** — Rust source identical, NO Rust added, base HEAD
  `4bc702a8bf`). 159000's numpy `select_fovea` argmax/`sort[:top_k]` — an agent DECISION in
  Python — is now `seeds/fovea_salience_bridge.json`'s `fovea_resolve` rule: the fovea is the
  `ArgminUnique` over Γ-admissible candidates keyed by `Neg(Log(salience)+goal_logweight)`, the
  MAP reading of grammar.rs's `selection ∝ exp(w)` (composition only — `ArgminUnique`/`Filter`/
  `Neighbours`/`Log`, no new Term). A1 graph-native (the fovea is read from `is_fovea`, no Python
  argmax; without `run_rules` there is no fovea). A2 reproduces the retired numpy fovea EXACTLY
  (synthetic lands on GT; **E1M1 146/146**). A3 the top-down goal shifts the resolution MONOTONE
  + continuous with a crossover at the log-weight tie (ArgminUnique refuses the tie); a strong
  bottom-up wins the race. A4 a high-weight INADMISSIBLE candidate never wins (Γ gates before
  weighting; the `has_candidate` production was Type-2-rejected until declared — Γ is live).
  Gate `tests/test_fovea_salience_bridge_migrated.py` 10/10 (E1M1 skips if WAD/VizDoom absent).
  Oracle 222/0 both sides. `SEED CLAIM 160000-160999 CLEAN`.)
