# CONTAINMENT — RESULTS: the correction is RIGHT, GATED, and INERT. Containment is not the blocker; the PEER competition is.

*Pre-registration: `VISION_FIGADJ_NESTING_PREREG.md`, committed BEFORE any number.
Nothing in it was edited after the first number. **This rung reports OUTCOME 4 of its own
§5: the vacuity gate returned `D = 0` and the arm comparison was abandoned unrun.***

**ENGINE PROVENANCE (§10)** — printed from **inside every measuring process**, into
`results/figadj_nesting.log`:

```
engine a1d350bbd23b @ <this worktree>/runners/dsl/python/substrate_rs/_native.abi3.so
  [1 other tree build(s) shadowed]
```

Branch `worktree-agent-ac7efef13e76a8f7c`, base **`ee0a1af25ef5dea0e9bc8919f85ebe7e8e19f463`**.
Engine built in-tree by `scripts/engine_build.sh`; **no Rust change in this rung**.
Migrated provenance gate run as **its own step, first**: **7 passed**. `data/` is a
symlink to canonical (§10.2), never a copy.

---

## 1. THE HEADLINE

**The inversion is real, the correction removes it, and at the configuration the ladder
actually runs at THE CORRECTION CHANGES NOTHING — because the enclosing regions are not
losing to their contents. They are losing to their PEERS.**

| | |
|---|---|
| Vacuity gate M-E, 20 real G72 tiles | **`D = 0`** |
| Wide re-check, **224 real G72 tiles** | **0 tiles where a mint moved**, `Σ\|D\| = 0` |
| Nested pairs actually PRESENT in those 224 tiles | **18** — so this is not "no containment" |
| Enclosing components refused by a **PEER**, not a child | **17 / 17 = 100%** |

The conjunct is **not dead** — on a minimal synthetic stimulus it does exactly what it
was derived to do (§3). It is **inert on this material**, which is a different and more
useful fact.

**Per PREREG §3 M-E and PROTOCOL §1's fifth clause (FM-0): `D == 0` ⇒ STOP, claim
nothing, burn no further seed.** M-A, M-C, M-F and M-G were **not run**. No arm number
appears in this document, and none is inherited into a claim.

---

## 2. WHAT THIS CORRECTS IN THE FINDING I WAS BUILT ON

The surface rung (`VISION_SURFACE_ASSIGNMENT_RESULTS.md`, seeds 87000–87999) measured:

> A **featured** surface SHATTERS INTO ITS CONTENT (82–92 enclosed components inside R),
> and `G_own_lost`'s `perim(R) < perim(Q)` awards figure to the **SMALLER** perimeter —
> **so the surface LOSES TO ITS OWN CONTENT BY CONSTRUCTION.**

**That measurement is correct. The phrase "its own content" is what misled me, and I
inherited the mistake.** `bg < 0.5` — the flood's `enclosed` — means *"not reachable from
the frame"*, **not** *"inside another component"*. The 82–92 components inside R are
**PEERS OF EACH OTHER AT ONE LEVEL**, not children of anything. Measured directly on the
predecessor's own screen stimulus (side 14, tile ordinal 5, n=20 frames/corpus):

| corpus | content | components/frame | **nested pairs/frame** | largest proto | \|R\| |
|---|---|---|---|---|---|
| C1 cartoon | screen | 102.3 | **0.45** | 0.9 cells | 196 |
| C1 | mirror | 96.8 | **0.00** | 1.0 | 196 |
| C1 | flat | 18.1 | **0.00** | 0.0 | 196 |
| C2 live-action | screen | 101.6 | **0.15** | 0.9 | 196 |
| C2 | mirror | 49.0 | **0.10** | 4.0 | 196 |
| C2 | flat | 11.1 | **0.00** | 0.2 | 196 |

**There is no component that IS the surface, so there is nothing for a containment
correction to rescue.** The predecessor declared this bound honestly ("`ProtoObject` has
four attributes… SURF = 0 IS NOT EVIDENCE OF FAILED IDENTIFICATION") and I restated it in
my own prereg §3 M-G — **and I still built a mechanism whose premise it excludes.** That
is the rung's central error and it is mine, not the predecessor's.

Across a wider real-frame sample the same fact holds at the representation level:
**128 tiles, 4,323 components, 6 nested pairs** — 1.4 per 1,000 components.

---

## 3. THE CONJUNCT IS ALIVE — the positive control that separates "inert" from "dead"

§1's fourth clause: *"scores at the floor" is satisfied by DEATH.* So the mechanism is
demonstrated on a stimulus that **does** contain the relation, before the null is
believed. A 60-cell ring enclosing a 4-cell hole, all four arms, one `run_rules` fixpoint:

| arm | protos minted (sizes) |
|---|---|
| incumbent (`bo_mint_enclosed`) | `[]` — contact vetoes both |
| replacement (v1.1.0) | **`[4]`** — only the HOLE |
| wellposed (v1.2.0, standing) | **`[4]`** — only the HOLE |
| **nested (this rung)** | **`[60, 4]`** |

**That middle row IS the inversion, reproduced on the smallest stimulus that can carry
it: a 60-cell region loses figure status to the 4-cell hole inside it.** The correction
mints the ring **without taking the hole away from it** — the hole is genuinely a figure
*on* the ring, which is what nested figure-ground means. The read-out reconciles
(`G_pass == n_protos`) under every arm. Gate:
`tests/test_border_ownership_nesting_migrated.py::test_the_INVERSION_is_real_and_the_scope_removes_it`.

**No size is read anywhere in this.** The ring is 15× the hole and that ratio is not
available to the rule; what changes is *which borders count as R's own contour*.

---

## 4. THE MECHANISM OF THE NULL, TRACED ON THE SETTLED GRAPH

The interesting result is not "there is no containment" — **there is** (18 pairs in 224
tiles). It is that **removing the contained rival rescues nothing**. Every enclosing
component in the 224-tile sweep was traced to the gate that refuses it under the `nested`
arm:

| why the enclosing component is STILL refused | count |
|---|---|
| **`G_own_lost` against a PEER** | **17** |
| `G_illposed` (peer) | 0 |
| `G_gnd2` | 0 |
| PASS | 0 |
| **total enclosing components** | **17** |

**100%, no exceptions.** Each carried 1–2 contained children and **1–16 peer rivals**
(sizes 8–66 cells). The children were never the binding constraint.

**The attribution rests on a read-out, so the read-out is reconciled against the rules'
own minted output before it is believed: `G_pass == n_protos` on **384 rows / 0
mismatches**, across all four arms on real tiles.** `D = 0` itself is a fact about the
**rules** — it compares `n_protos` minted by the graph under two flag settings, not a
Python replication.

**⇒ THE FINDING: at G72 on real frames, ownership's blocker is the PEER competition —
`perim(R) < perim(Q)` against an ABUTTING sibling — not the containment inversion.** The
surface rung named a real defect in the predicate; this rung measures that **it is not
the operative one**, and that fixing containment cannot move the ladder until the peer
competition is addressed. That is the lever the next rung should price, and it is now
named rather than guessed.

---

## 5. GATES — every floor RE-EARNED in this tree, on this engine, nothing inherited

| gate | result |
|---|---|
| **Oracle** `bash scripts/rung7_vision_bench.sh`, **before** any change | **222 passed / 0 failed** (with `data/`) |
| **Oracle, after every change** | **222 passed / 0 failed** — see §5.1 |
| Provenance gate, its own step, first | **7 passed** |
| Synthetic border-ownership, **incumbent** | **9 / 9** |
| Synthetic, **replacement** (v1.1.0) | **9 / 9** |
| Synthetic, **wellposed** (v1.2.0) | **9 / 9** |
| **New synthetic, containment (4 arms)** | **13 / 13** |
| AST §13 gate, replacement | 7 / 7 |
| AST §13 gate, wellposed | 8 / 8 |
| **AST §13 gate, containment (new)** | **10 / 10** |
| **M-D2 injection positive control** | **PASS — and the plant was verified to LAND** |

**The registered SPECKLE control and the SINGLE-CELL FIGURE constraint, both re-earned
under the new arm** (`tests/test_border_ownership_nesting_migrated.py`): iid speckle at
18×18/k=16 mints **0** under `nested` (20 fields, RNG 92700), and a genuine single-cell
figure **still mints in all four arms**. The correction only ever *removes* rivals, so
speckle was the direction of risk and is asserted in both directions. `n=100` was **not**
run — M-E aborted first, per the decision rule.

`test_the_scope_never_REMOVES_a_proto_the_standing_arm_minted` asserts the direction the
derivation implies (a range correction can only make `G_own_lost` easier to pass), so a
drop would be caught as *something other than scoping*.

### 5.1 §9 — DEFAULTS PRESERVE COMMITTED RESULTS

`bown_nest` defaults **0.0** in the seed node and in `set_flag`, asserted by two separate
AST tests. The `Or(flag < 0.5, …)` short-circuits, so the committed v1.2.0 well-posed
path is byte-identical. The oracle is **222/0 both before and after** the change.

### 5.2 M-D2 — and why the landing check is the load-bearing half

`scripts/nesting_ast_injection_control.py`. The previous rung's supervisor injected a
size bound, watched the gate pass, and **the control was wrong, not the gate** — the
plant had landed on a different `Not>Exists>Exists` in the same rule. So this harness
**asks the gate module itself** for the path it selects, mutates exactly there, then
**re-reads the mutated seed through the same selector and asserts the plant is visible to
it**. A no-op injection is a FAILURE, not a pass.

```
[baseline]  rc=0  10 passed in 0.05s
[selector]  3 sites; injecting at bo_mint_owned.where['items', 5, 'items', 0, 'arg',
                                    'predicate', 'predicate', 'items', 3]
[landing]   plant visible to the selector: True
[injected]  rc=1  3 failed, 7 passed in 0.07s
[reverted]  rc=0  10 passed in 0.05s
M-D2 PASS: green -> plant LANDS -> RED -> revert -> green
```

The seed is restored from an in-memory copy of the original **bytes** and asserted
byte-identical afterwards.

---

## 6. §13 — WHAT THE CONJUNCT IS, AND WHAT IT PROVABLY IS NOT

A rival `X` enters the competition only if:

```
Exists q ∈ {Cell : q.glabel == X.glabel ∧ q.bg < 0.5}
  Exists p ∈ Neighbours(q) : p.glabel ≠ X.glabel ∧ p.glabel ≠ R.glabel
```

— *"X has a neighbour that is neither X nor R"*, i.e. **X is not a hole in R**. Applied at
**three** sites, asserted to be exactly three: the ownership comparison's rival, and the
v1.2.0 well-posedness conjunct's two — **one definition of "rival", used by both**, or
the two conjuncts disagree about what a rival is (PREREG §1.3).

**Zero `Count` nodes in the subtree** — the standing refused fix in this line of work is a
minimum-size threshold, and no size test can be written without bounding a count.
Asserted from the other side too: **the conjunct READS exactly `{glabel, bg}`** and
nothing else, so it cannot distinguish a 1-cell hole from a 200-cell hole and cannot
exclude a rival for being small. Every literal is a `0.5` against a 0/1 flag; every
`glabel` comparison is `Attr` vs `Attr` (9 of them, asserted exactly). Selector locates
the conjunct **BY SHAPE**, never by substring — the four substring-selector failures in
this arc are why.

**The derivation, in one line** (full form in PREREG §1): Zhou/von der Heydt measure
border ownership **of an EDGE, with a SIDE**, not of a region; `G_own_lost` quantified "R
must win" over **all** of R's borders, including the border with a hole, which is not part
of R's outer contour at all. Where `Q ⊂ R` the shared border **is** the whole of
`perim(Q)`, so `|B|/perim(Q) = 1` identically for every R — pinned by the geometry, not
decided by the competition, the same degeneracy v1.2.0 found at `rim = 1`, one level up.
**This composes with v1.2.0 rather than fighting it, and the difference in RESOLUTION is
stated in the prereg precisely because that is where tuning would hide:** v1.2.0 held its
case open because there was no fact of the matter; here there is one and Zhou supplies it.

---

## 7. WHAT I GOT WRONG — in full

1. **THE CENTRAL ERROR: I BUILT A MECHANISM ON A PREMISE THE SOURCE DOCUMENT ITSELF
   EXCLUDED.** I read "the surface loses to its own content" as containment. It is not:
   `enclosed` means *unreachable from the frame*, and the 82–92 components are peers. The
   predecessor stated the relevant bound plainly and **I restated it in my own prereg
   §3 M-G and built the thing anyway.** A one-line count of nested pairs — the diagnostic
   I eventually wrote — would have killed this before a line of seed JSON. **Cheap
   diagnostics belong BEFORE the derivation, not after the gate.**
2. **MY PREREG §7 DISCLOSED AN EDIT THAT TURNED OUT TO BE UNNECESSARY, AND I HAD NOT
   CHECKED.** I predicted `test_the_conjunct_is_a_NEGATED_EXISTENTIAL_not_a_bound` would
   need amending. It passed untouched — my appended node is an `Or`, not an `Exists`, so
   its count of direct inner existentials was unchanged. Disclosing in advance was right;
   **asserting a consequence I had not verified was not.** The inherited-test edits that
   *were* needed were mechanical and precedented (add `bown_nest` to `FLAG_KEYS`, bump two
   version pins — byte-for-byte the shape of what the v1.2.0 rung did for `bown_wp`).
3. **PREDICTION 1 WAS WRONG, AND IT WAS THE ONE THE RUNG TURNED ON.** I predicted `D > 0`
   with the proviso *"if nesting is rare at k=16 the conjunct could be near-vacuous"*. The
   proviso fired — but **harder than the proviso stated**: I framed it as a question of
   *rarity*, and the answer is that even where the relation **is** present (18 pairs) the
   conjunct still moves nothing, because the enclosing components are refused by peers
   regardless. Being right about the risk and wrong about its mechanism is not being
   right.
4. **I nearly logged a 20-tile `D = 0` as the finding.** 20 tiles cannot distinguish "no
   containment" from "containment is not the blocker" — different claims with different
   next rungs. The 224-tile sweep plus the per-component gate trace is what separates
   them, and I only ran it because a quiet control is supposed to be investigated rather
   than recorded.
5. **Predictions 2–6 are UNTESTED, not confirmed.** M-A at n=100, M-C, M-F and M-G never
   ran. The speckle and single-cell floors reported in §5 are the **synthetic** miniatures
   only. Nothing in §5 licenses a real-frame yield or size-distribution claim.

---

## 8. SCOPE — what is NOT shown (§8)

- **No real-frame yield or cost number is claimed.** M-C did not run; the incumbent 3.3 /
  10.7 and wellposed 7.1 / 14.4 baselines are quoted only as the comparison this rung
  *would* have made.
- **The size distribution (M-F) is not measured**, so the brief's actual target — few and
  large — gets **no evidence from this rung** either way. The only size facts here are
  diagnostic: median proto size **1–2 cells** and largest proto **~1 cell against
  \|R\| = 196** on the screen stimulus, consistent with every predecessor's fragment
  finding, and re-observed rather than re-measured.
- **The new arm (M-G) did not run.** Whether a screen composite could mint as one object
  is **not** answered; §2 argues it *cannot* at this configuration for a structural
  reason, and that argument is a diagnosis, not a measurement of the arm.
- **The conjunct is NOT validated as load-bearing.** It ships default-OFF as a derived,
  gated, currently-inert capability. **`D = 0` at G72 is recorded as the fact about it.**
- The 17/17 peer attribution is measured on **two corpora at one grain (G72, k=16)**. It
  is not shown to hold at other grains, and the resolution rung's own finding — that
  component structure changes sharply with tile size — is a reason to expect it may not.

---

## 9. DISPOSITION — why the seed ships anyway, stated plainly

The change is committed **with the flag OFF and the null as its headline**. It is
correct, derived rather than tuned, gated at 13 + 10 tests, positive-controlled by
injection, and byte-identical by default (oracle 222/0 either side). On material that
contains the relation it does exactly what it was derived to do.

**It is not a result, and this document does not present it as one.** §13.2's rule is
that "works" and "is load-bearing" are different properties; this conjunct **works** and
is **not load-bearing at G72**. Anyone reaching for it must re-run M-E on their own
configuration first.

---

## 10. SEEDS — 92000–92999

**Measured draws, unknown sinks 0, none outside the block:**

| seed | consumed by | status |
|---|---|---|
| **92700** | `test_border_ownership_nesting_migrated` — speckle miniature | **BURNED** |
| **92701** | same — superset direction check | **BURNED** |
| 92800 | prereg M-E; **superseded** — M-E ran on real tiles, no RNG | not drawn |
| 92900 | `figadj_nesting_measure` M-A | **not drawn** — run aborted at M-E |
| 92000–92014, 92100–92114 | `nesting_surface_measure` (M-G) | **not drawn** — never ran |

`scripts/seed_claim.py` now reports the block OCCUPIED by **exactly three files, all
mine** (23 integers, all in-block). **Disclosure:** my ad-hoc screen diagnostic (§2)
constructed `RandomState(92000)`; `build_stimulus` consumes the generator **only** on the
`scramble` arm, which I did not run, so no draw was taken — recorded as claimed-not-
consumed rather than left to inference.

---

## 11. LEDGER ROW (carried here — `VISION_PROTOCOL.md` NOT edited)

| **92000–92999 (2 draws measured — 92700, 92701; unknown_sinks 0, none outside block)** | **CONTAINMENT — THE CORRECTION IS RIGHT, GATED, AND INERT; AND THE PREMISE I WAS GIVEN DOES NOT HOLD AT G72.** Ownership was made to respect containment — a rival ENCLOSED by R is removed from the competition, derived from Zhou/von der Heydt's ownership being a property OF AN EDGE WITH A SIDE (a figure is routinely GROUND for a smaller figure on it) and from `\|B\|/perim(Q) == 1` being pinned by geometry rather than decided, the same degeneracy v1.2.0 found at `rim=1` one level up; ONE rival definition shared by both conjuncts. **THE VACUITY GATE RETURNED `D = 0` AND THE RUNG STOPPED ITSELF: 224 real G72 tiles, ZERO mints moved.** **BUT THE NULL IS NOT "NO CONTAINMENT" — 18 NESTED PAIRS ARE PRESENT, AND ALL 17 ENCLOSING COMPONENTS ARE REFUSED BY `G_own_lost` AGAINST A **PEER**, 100%, NO EXCEPTIONS (1–16 peer rivals each, sizes 8–66). THE BLOCKER AT THIS GRAIN IS THE PEER COMPETITION, NOT THE CONTAINMENT INVERSION — the surface rung named a real defect and this measures that it is NOT THE OPERATIVE ONE.** **AND IT CORRECTS THE FINDING IT WAS BUILT ON: `bg<0.5` means UNREACHABLE-FROM-FRAME, not INSIDE-ANOTHER-COMPONENT — the screen's 82–92 "enclosed components inside R" are PEERS AT ONE LEVEL, 0.00–0.45 nested pairs/frame, largest proto ~1 cell against \|R\|=196. There is no component that IS the surface, so containment had nothing to rescue.** **THE CONJUNCT IS ALIVE, NOT DEAD (§1 clause 4): on a 60-cell ring around a 4-cell hole the standing arm mints `[4]` — THE 60-CELL REGION LOSES TO THE 4-CELL HOLE INSIDE IT, the inversion on the smallest stimulus that carries it — and the corrected arm mints `[60, 4]`, keeping the hole as a figure ON the ring. No size is read: the ring is 15× the hole and that ratio is not available to the rule.** §13: **ZERO `Count` in the subtree**, and asserted from the other side — the conjunct READS EXACTLY `{glabel, bg}`, so it cannot tell a 1-cell hole from a 200-cell one; 3 sites asserted exactly, 9 `Attr`-vs-`Attr` glabel comparisons, selector BY SHAPE never substring. **M-D2 INJECTION POSITIVE-CONTROLLED WITH THE LANDING VERIFIED** — the harness asks the gate module for its own selected path, mutates there, and RE-READS THROUGH THE SAME SELECTOR asserting the plant is visible (a no-op injection FAILS), answering the predecessor's wrong-subtree control: green → lands → 3 red → revert → green. **FLOORS ALL RE-EARNED IN-TREE, NONE INHERITED: oracle 222/0 BEFORE AND AFTER; synthetic 9/9 × 3 arms + 13/13 new (4 arms); AST 7/8/10; provenance its own step 7 passed. Speckle 0 and the GENUINE SINGLE-CELL FIGURE STILL MINTS IN ALL FOUR ARMS — but SYNTHETIC MINIATURES ONLY, n=100 NOT RUN.** Seed v1.3.0, `bown_nest` **OFF by default** (§9, byte-identical); no Rust. **WHAT IT GOT WRONG: IT BUILT A MECHANISM ON A PREMISE ITS OWN PREREG RESTATED AS EXCLUDED — the predecessor's honest bound ("no `Surface` type, `ProtoObject` has four attributes") was quoted in §3 M-G and the thing was built anyway; A ONE-LINE NESTED-PAIR COUNT WOULD HAVE KILLED IT BEFORE ANY SEED JSON, and cheap diagnostics belong BEFORE the derivation. PREDICTION 1 FAILED IN A WAY ITS OWN PROVISO DID NOT COVER: it framed the risk as RARITY, and the answer is that even where the relation IS present the conjunct moves nothing. IT NEARLY LOGGED A 20-TILE `D=0` AS THE FINDING — 20 tiles cannot separate "no containment" from "containment is not the blocker", two claims with different next rungs. And its prereg §7 disclosed an inherited-gate edit as necessary WITHOUT CHECKING; that test passed untouched.** **DISPOSITION STATED, NOT BURIED: the conjunct WORKS and is NOT LOAD-BEARING at G72 (§13.2's two properties); it ships OFF with `D=0` as the recorded fact about it, and M-C / M-F / M-G NEVER RAN so NO yield, NO size-distribution and NO surface-arm claim is made.** **NAMED NEXT LEVER: price the PEER competition — `perim(R) < perim(Q)` against an abutting sibling — which this rung measures to be what actually holds the ladder.** |
