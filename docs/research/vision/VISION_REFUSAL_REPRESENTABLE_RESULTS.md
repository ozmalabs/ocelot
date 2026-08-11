# A REPRESENTABLE REFUSAL — RESULTS

> **LEDGER ROW (for transcription; do not edit VISION_PROTOCOL.md):**
> **117000–117999 ALLOCATED; the discrimination is DETERMINISTIC so NONE consumed by it; the randomised replicate draws 117000–117049 (LITERAL, in-block); 1 unknown sink in my file (`default_rng(sd)` loop form), disclosed; Term index 180 CONSUMED (`ArgminRefusal`; 175–179 unmoved).** **A REPRESENTABLE REFUSAL — THE FOUR-WAY DISCRIMINATOR, and a rule can finally HEAR a refusal.** The ArgminUnique rung's terminus ("can refuse, no caller can hear it") closed: a NEW additive Term `ArgminRefusal` (idx 180) routes a held `RefusalMark` NODE to the TIE PATH ONLY (empty stays `None`) — **the split the shared `default` cannot make, because `argmin_or_argmax_over` returns `default` on BOTH the tie-path AND the empty-path**. REFUSED becomes a first-class value distinct from `None` (NOTHING), `Bool(false)` (NO), and a real winner (REAL). **BASELINE reproduced (tie≡empty≡`None` at raw+`Attr`; tie≡`Bool(false)` at the WTA `Eq`).** **ARM D: four distinct rule branches; the OLD idiom `Eq(cand,ArgminUnique)` reads `Bool(false)` ×5 on a tie, the NEW read-refusal-first reads REFUSED ×5.** **GOVERNING LAW both directions: a selection over ordinary values NEVER yields the token (token appears IFF the uniqueness comparison failed); token distinct from None/false/0 and TRUTHY.** **PyO3: a world adapter knowing only the marker id tells all four apart — no re-collapse in Python.** **COMPOSE: a walled ShapeDecode no-match LIFTS to the SAME marker.** **HEAR+MINT (seed `refusal_representable.json`): a rule mints EXACTLY 1 `Residual` on a tie, 0 on a winner, 0 on empty — graph-native, no Python decision.** **PERSISTENCE: a graph with the minted Residual+marker round-trips byte-identically; a graph without is unchanged.** **REPLICATE 50/50/50 (117000–117049).** §13: uniqueness is exact equality, the token is a held NODE (data), NO constant. §9: **oracle 222/0 before (`e039d2eec2dd`) AND after (`7041d2e6a7dd`)**, provenance re-verified stable post-measurement, migrated gate `test_refusal_representable_migrated.py` **10/10** with an in-process positive control (ArgminUnique MISCLASSIFIES a tie as REAL). NO `Value` variant, NO `py.rs` change, NO existing Term's serialization touched. **NAMED SUCCESSOR: PROMOTE (`SelfConcern→StandingConcern`) + GROUND (teacher); ARM the 16 existing WTA sites (one `Eq(sel,RefusalMark)` read each).** **WHAT I GOT WRONG: assumed option-B was zero-Rust (the shared `default` conflates tie/empty — needs the split); flattened the seed effects first (caught by the rule not firing); a cosmetic `describe()` string nearly read as a failed arm; `cargo test` can't link pyo3 here so the variant-table invariant was checked on the generated table directly (181/181/181).**


Pre-registration `VISION_REFUSAL_REPRESENTABLE_PREREG.md`, committed
**`925cd3f10b4d`** before any number. The successor to
`VISION_ARGMIN_UNIQUE_RESULTS.md` ("`ArgminUnique` can refuse, and no caller in
the seed layer can hear it"). **A rule can now hear it.**

- **branch (as observed):** `worktree-agent-aaf96dcd062b68070` — the name I see.
- **base SHA (as observed):** `92f3c35e9ac23dd93feb46851b32c02cffa2943c`.
- **engines.** THIS RUNG ADDS RUST, so it built its own, twice:
  - `e039d2eec2dd` — this tree's build of the **UNCHANGED** source, for the
    baseline collapse + the pre-change oracle.
  - **`7041d2e6a7dd`** — this tree's build of the changed source (`own`); every
    post-change number is from it.
- **provenance, its OWN step, before AND after measurement:**
  `tests/test_engine_provenance_migrated.py` **7 passed** before; after all
  measurement `domains/engine_provenance.py` re-read **`engine 7041d2e6a7dd @
  …/runners/dsl/python/substrate_rs/_native.abi3.so`** — UNCHANGED (provenance
  stable). Each measuring script also compares `provenance_line()` against
  `EXPECT_ENGINE` inside its own process and aborts on divergence.
- **oracle:** `bash scripts/rung7_vision_bench.sh` → **222 passed, 0 failed**,
  exit 0, `data/` symlinked (§10.2, the with-corpus case) — on the pre-change
  engine (`e039d2eec2dd`) AND on the post-change engine (`7041d2e6a7dd`).
- **seeds:** **117000–117999 ALLOCATED; the discrimination is DETERMINISTIC so
  NONE is consumed by it.** The randomised replicate draws **117000–117049**
  (LITERAL elements of the block — no `base + K` offset). `check_claim` verbatim
  is in the pre-registration (§3 clause 8), **511 unresolved sinks tree-wide**
  priced. **My measurement file carries 1 unknown sink** (`scripts/seed_audit.py`):
  the `default_rng(sd)` LOOP-variable form the static tool cannot resolve —
  disclosed, not buried; the values ARE literal elements of 117000–117049.
- **loadavg** recorded in the artifact JSON; peak observed **1.43** on 12 cores,
  never more than 2 workers. **No wall-clock cutoff was used as a verdict.**
- **CPU:** engine build + measurement + gate, sequential; the oracle alone.

---

## THE HEADLINE

**A refusal is now a FIRST-CLASS value distinct from all three things it collapsed
into — at the caller, at a consuming rule, and across the PyO3 boundary — and a
graph-resident rule HEARS it and MINTS a `Residual` node from it. Every committed
result is byte-identical.**

The design: a NEW additive Term **`ArgminRefusal`** (index 180) that routes a held
**`RefusalMark`** node to the **tie-path ONLY** (a comparison matched nothing),
returning `Value::None` on an empty source — **the split the shared `default`
cannot make.** REFUSED is then `Node(mark)`, distinct from `None` (NOTHING),
`Bool(false)` (NO), and a real winner node (REAL).

**The measured facts, all CONFIRM:**

| arm | result |
|---|---|
| BASELINE collapse (unchanged engine) | tie and empty **byte-identical** — both `None` at the raw sel and the `Attr` site; a tie reads `Bool(False)` at the WTA `Eq` site, identical to "not the winner" |
| ARM D — four-way at a consuming rule | tie→**REFUSED**, empty→**NOTHING**, unique→**REAL**, non-winner→**NO** — four DISTINCT branches |
| the collapse, one level up | OLD idiom `Eq(cand, ArgminUnique)` on a tie: **all 5 `Bool(False)`**; NEW with the refusal read first: **all 5 REFUSED** |
| ARM G dir 1 (governing law) | a SELECTION over ordinary values NEVER yields the token; the token appears IFF the uniqueness comparison failed |
| ARM G dir 2 | `Eq(token, None/false/0)` all `False`; the token is TRUTHY — distinct from all three |
| ARM P — PyO3 | a world adapter knowing only the marker id classifies all four: `REFUSED/NOTHING/REAL/NO` |
| ARM C — compose | a WALLED ShapeDecode no-match LIFTS to the SAME marker; both refusals are the same token |
| HEAR + MINT | a seed rule mints **exactly 1** `Residual` on a tie, **0** on a unique winner, **0** on empty |
| ARM R — persistence | a graph WITH a minted Residual + the marker round-trips byte-identically; a graph WITHOUT any refusal machinery is unchanged |
| REPLICATE (117000–117049) | tie→REFUSED **50/50**, distinct→REAL **50/50**, empty→NOTHING **50/50** |
| §9 oracle | **222/0 before AND after**; migrated gate **10/10**; provenance stable |

---

## 0 — THE BASELINE COLLAPSE, REPRODUCED (the "before")

On the UNCHANGED engine (`e039d2eec2dd`), the three cases are byte-identical at
every caller shape (`results/refusal_representable.json` → `baseline_collapse`):

| case | raw `sel` | `Attr(sel,"score")` | `Eq(firstCand, sel)` |
|---|---|---|---|
| **tie (REFUSED)** | `None` | `None` | **`Bool(False)`** |
| **empty (NOTHING)** | `None` | `None` | `None` (no candidate) |
| unique (REAL) | `Node(5)` | `Float(3.0)` | `Bool(False)` |

`baseline_collapse_holds = True`: **tie and empty are byte-identical `None`** at
the raw sel AND the `Attr` site, and a tie reads `Bool(False)` at the WTA `Eq`
site — **byte-identical to "you are not the winner"** (the unique-REAL row's
first-candidate read is the same `Bool(False)`). This is exactly the
`argmin_or_argmax_over` finding: the tie-path and the empty-path both return
`default`/`None` (term.rs ~8195 and ~8223), so no `default` value could separate
them. **The collapse is real and is the thing this rung removes.**

---

## 1 — WHAT WAS BUILT

**`TermNode::ArgminRefusal { source, var_name, value, refused: Option<TermIdx> }`**
— one Term variant, **APPENDED LAST** in the enum so `GapAbduce` stays 175,
`GapVerify` 176, `ArgminUnique` 177, `SupportInfer` 178, `MotionEnergy` 179; the
new Term is **180**, `NUM_TERM_VARIANTS` **180 → 181** (regenerated by
`tools/gen_term_variants.py`; the `variant_table_covers_the_enum` invariant holds
by construction — 181 names, 181 index arms, all unique, verified programmatically:
the crate's `cargo test` harness cannot link pyo3 in this environment, a
pre-existing issue unrelated to this change, so the invariant was checked on the
generated table directly).

The fold is identical to `Argmin` with ONE change threaded through
`argmin_or_argmax_over` as a new `refused_on_tie: Option<TermIdx>` parameter: on a
**tie** (`n_at_best > 1`) it returns the evaluated `refused` token; on an **empty
source** it returns `Value::None`. Every existing caller (`Argmin`/`Argmax`/
`ArgminUnique`) passes `refused_on_tie = None` and is byte-identical.

**§13 satisfied BY CONSTRUCTION.** Uniqueness is `cmp_value == Equal` — exact
equality. There is no constant in the variant and nowhere to put one. The
distinctness is a held **NODE** (data — minted by seed, referenced via
`Pick(NodesOfType("RefusalMark"))`), NOT a reserved magic string (§13).

**§9 by non-existence + additivity.** No committed seed except this rung's binds
the Term; `test_ArgminRefusal_is_bound_by_no_OTHER_committed_seed` gates it. No
`Value` variant was added, so `truthy`/Eq/Ord/hash/serde/`py.rs` are untouched — a
Node crosses PyO3 as a `NodeID` already. No existing Term's struct or
serialization changed.

**The seed** `seeds/refusal_representable.json` (v1.0.0, depends on `core`) ships
the held `RefusalMark` node and ONE reusable rule `refusal_query_mints_residual`:
given a `refusal_probe` query whose `refusal_cand` set has no unique extremum,
`ArgminRefusal` returns the marker, the rule HEARS it (`Eq(sel, mark)`), and MINTS
a `Residual` node linked to the query. Inert on any graph without those edges (no
committed seed has them) → byte-identity.

---

## 2 — ARM D: THE FOUR-WAY AT A CONSUMING RULE

`results/refusal_representable.json` → `arm_d_fourway`, engine `7041d2e6a7dd`. A
classifier rule set reads the selection result and sets a distinct `verdict`:

| case | raw `sel` | rule verdict |
|---|---|---|
| tie | `Node(2)` (the marker) | **REFUSED** |
| empty | `None` | **NOTHING** |
| unique | `Node(5)` (the winner) | **REAL** |

`arm_d_distinct = True`. And the WTA axis, read WITH the refusal read first
(`NO_vs_YES`): the winner (idx 2) → **YES**, every other candidate → **NO**.

**The collapse, separated — the headline (`tie_all_refused`):**

| candidate | OLD idiom `Eq(cand, ArgminUnique)` | NEW (refusal read first) |
|---|---|---|
| 0–4 (all, on a tie) | **`Bool(False)`** ×5 | **REFUSED** ×5 |

Under the old idiom a tie is `Bool(False)` at every candidate — indistinguishable
from "you are not the winner." With the marker read first, **the rule reports
REFUSED** — it can finally tell "there is no unique winner" from "you specifically
are not the winner." **This is the ArgminUnique rung's C1 erasure, closed.**

---

## 3 — ARM G: THE GOVERNING LAW, BOTH DIRECTIONS

*A comparison can be false, a selection cannot — so the token must be reachable
ONLY by a comparison-matched-nothing.*

**Direction 1 — a selection never yields the token** (`arm_g`):
- over DISTINCT candidates: plain `Argmin` → `Node(5)`, `ArgminRefusal` → `Node(5)`
  — **neither is the token** (`dir1_neither_is_the_token = True`).
- on a TIE: plain `Argmin` → `Node(3)` (a winner), `ArgminRefusal` → `Node(2)` (the
  marker). **The token appears ONLY on the tie, ONLY from `ArgminRefusal`**
  (`dir1_token_ONLY_on_tie = True`).

**Direction 2 — the token is distinct from None/false/0 and is truthy:**
`Eq(token, None) = False`, `Eq(token, False) = False`, `Eq(token, 0) = False`,
and `IfThenElse(token, "truthy", "falsy") = "truthy"`. `dir2_all_distinct = True`.

**Boundary (P4, stated in the prereg):** direction 1 is true by construction — the
token is emitted only on the tie branch and the marker is never a candidate. A rule
COULD feed the RefusalMark node into a candidate source as DATA, and then a
selection would "return" it — but that is not something a selection over ORDINARY
percepts can do. The law holds for every selection over the values a scene produces.

---

## 4 — ARM P (PyO3), ARM C (compose), HEAR+MINT, ARM R (persistence)

**ARM P — the PyO3 boundary.** A world adapter that knows ONLY the RefusalMark node
id classifies all four across the boundary: `REFUSED` (a `NodeID` == marker),
`NOTHING` (Python `None`), `REAL` (a `NodeID` != marker), `NO` (Python `False`).
`all_four_distinct_across_pyo3 = True`. **The refusal does not re-collapse in
Python** — the exact failure the prereg guarded against.

**ARM C — composition.** A walled `ShapeDecode` (empty goal) erases `explained` to
a bare `None` (the ArgminUnique-rung C1 erasure, reproduced). A rule reads the wall
(`authored != True`) and LIFTS it to the SAME `RefusalMark`. `Eq(lifted,
ArgminRefusal_tie_token) = True` — **both refusals are the same token**;
`shapedecode_wall_reaches_rule_as_REFUSED_not_None = True`. The marker is a general
refusal representation, not bound to one Term.

**HEAR + MINT.** The seed rule fires in `run_rules`: tie → **1** `Residual` minted,
unique → **0**, empty → **0** (NOTHING is not a refusal; the token is not returned
on empty). `hear_and_mint_correct = True`. **A rule HEARS a refusal and turns it
into a first-class inspectable graph object**, with no Python decision.

**ARM R — persistence.** A graph containing the minted `Residual` + the
`RefusalMark` round-trips byte-identically through `graph_to_dict` /
`graph_from_dict` (`graph_with_residual_roundtrips_identical = True`); a graph
WITHOUT any refusal machinery is byte-identical too
(`graph_without_refusal_roundtrips_identical = True`). The whole mind round-trips
as durable JSON, unchanged for graphs that hold no refusal.

**REPLICATE (seeds 117000–117049, LITERAL):** 50/50 tie→REFUSED, 50/50
distinct→REAL, 50/50 empty→NOTHING. `all_perfect = True`. The four-way is
deterministic per case; the replicate varies the DATA, not the discrimination.

---

## 5 — THE SUCCESSOR (named, NOT built)

A `Residual` node minted from a heard refusal is the object the existing
gap-awareness / `SelfConcern → StandingConcern` self-improvement spine can PROMOTE
and the teacher can GROUND — "the agent reasons over / promotes / grounds it." The
parallax rung's "no object here" becoming a representable refusal a rule hears is
the perception instance: a `parallax_efference` FLAT world armed on its own uniform
motion mints 0 objects; routed through `ArgminRefusal` (or the same marker
convention on its grouping selector) that "nothing here" becomes a `Residual` a
rule can promote. **This rung built HEAR + MINT; PROMOTE + GROUND is the successor.**

**The 16 existing WTA sites are NOT armed** (P3, stated in advance). At an existing
`Eq(node, sel)` site, `Eq(candidate, marker)` is `False` for every candidate, so
REFUSED still reads `False` there UNLESS the site adds an `Eq(sel, RefusalMark)`
read. That rule-layer arming — one read per site, priced by the real-scene tie rate
the ArgminUnique rung established is unmeasured — is the arming work, not this rung.

---

## 6 — WHAT I GOT WRONG

1. **I ASSUMED OPTION B WAS "ZERO NEW RUST"; IT IS NOT.** The prereg fork listed a
   held sentinel returned as `ArgminUnique`'s `default` as potentially zero-Rust. On
   reading `argmin_or_argmax_over` I found the tie-path AND the empty-path BOTH
   return `default` — so a sentinel-as-default conflates REFUSED with NOTHING. The
   honest four-way REQUIRES separating the two return paths, which the existing
   `default` cannot. Predicted-and-corrected before building; the cost (one new
   Term) is stated, not hidden.
2. **MY FIRST SEED EFFECTS WERE FLATTENED.** `AddNode(...) + AddEdge(...)`
   concatenated two effect-ops into one flat array; the loader correctly rejected
   it ("effect must be an array"). Caught by verifying the rule FIRED (0 residuals
   minted) before trusting the seed — not by the load summary alone. Fixed to a
   list-of-ops.
3. **A COSMETIC ASSERTION MISMATCH nearly read as a failed arm.** `dir2_all_distinct`
   first reported `false` because my `describe()` rendered a Str as `str('truthy')`
   while the assertion expected `Str('truthy')` — the underlying facts (all three
   `Eq` `False`, truthy `'truthy'`) were correct. Fixed the formatter, not the fact.
4. **1 UNKNOWN SEED SINK IN MY OWN FILE.** The replicate's `default_rng(sd)` loop
   form is exactly the shape `seed_audit` cannot resolve (the ArgminUnique rung's
   §11.6 blind spot). The values are literal elements of 117000–117049; the ledger
   cannot see that they are. Disclosed.
5. **`cargo test` CANNOT LINK pyo3 in this environment**, so I could not run
   `variant_table_covers_the_enum` via cargo; I verified its invariant on the
   generated table directly (181/181/181, unique, ArgminRefusal→180). The release
   engine itself built and installed cleanly — the failure is test-harness-only.

---

## 7 — SCOPE: WHAT IS *NOT* SHOWN

- **The PROMOTE/GROUND closure is NAMED, not built.** This rung demonstrates HEAR +
  MINT only.
- **The 16 existing WTA sites are NOT armed.** The Term is bound only by this rung's
  own seed; arming a real site is a rule-layer change priced by the (unmeasured)
  real-scene tie rate.
- **Stimuli are synthetic** candidate sets, not natural scenes.
- **`Argmax` is not fixed**, nor are `EnclosedCount` or the motion sensor (the
  refusal-capacity rung's other "cannot refuse" mechanisms) — separate rungs.
- **The four-way is at the VALUE level and at a rule that reads the refusal token.**
  A rule that does NOT read the token still collapses REFUSED into `false`/`None` —
  representability is a prerequisite the consumer must use, not an automatic rewrite
  of every existing consumer.
