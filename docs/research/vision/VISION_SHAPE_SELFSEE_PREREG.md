# PRE-REGISTRATION — CAN THE JABBERWOCK NAME (AND DETECT) THE SHAPE OF THE DEFECTS IT KEEPS CATCHING?

*Written and committed BEFORE the confirmatory run (VISION_PROTOCOL.md §3). Every number in
the CALIBRATION section was measured on already-burned seeds / deterministic pilots before
this file was written.*

**Engine:** `engine c8433a515391 @ /home/matt/ozma/internal/research/experiments/gamma-substrate/runners/dsl/python/substrate_rs/_native.abi3.so`
— `[shared build — Rust source identical]` (§10.1: this rung adds **no Rust**, so sharing the
canonical build is the correct, cheap case; `ensure_tree_engine()` symlinks it to this tree's
own path and `rust_source_fingerprint()` verifies the source is byte-identical:
`858e2bded840461ef8de92bc95309d3366715cac8954c6a9b3c444c9804709cb`).
**Commit (base):** `de5f96b8` (worktree fast-forwarded onto it; 0 ahead / 8 behind at entry).
**Seeds:** **19000–19999 ALLOCATED** (declared here, in advance). This rung is
**DETERMINISTIC** — no RNG arm — so it is expected to burn **none**; recorded either way in
the ledger.

---

## 0. The directive and the boundary

> *"This seems like a shape issue. Get the jabberwock to do it."*

A dozen-plus defects were caught in one day by human-grade noticing, none by a green gate.
The question: **do they share a shape the agent can NAME, in its own terms — and can it then
DETECT that shape in code it has not seen?**

**The boundary I am NOT allowed to cross** (`CLAUDE.md`, "THE AGENT FIXES ITSELF WHERE IT IS
GRAPH-NATIVE"): the agent self-repairs *exactly where its cognition is graph-native*.
Python/Rust is its **blind spot**. Several instances (`load_parts`'s `Str`/`Surface` split) are
Rust. **The agent cannot fix those and must not pretend to.** Naming/detecting is in scope;
fixing is not. I touch **no Rust** (two agents are live in `term.rs`/cortex).

## 1. Instruments, and their §1 calibration (ALL RUN BEFORE THIS FILE)

**A gate whose measure passes noise is not a gate. The arms must be ALIVE (§1 clause 4).**
Five instruments, each positive-controlled with a floor arm AND a hit arm:

| instrument | hit arm | floor arm | verdict |
|---|---|---|---|
| `converse` (NL front door) | "moon" → real content | "What are you?" → `I am Jabberwock.` | **ALIVE, discriminative** |
| `categorise_by_shape` | 3/3 ideal exemplars → correct meta-shape | 3/3 nonsense → `None` | **ALIVE** |
| `induce_concern` (sd-loop) | novel → `minted:True` | held `T` signature → `recognized`, `minted:False` | **ALIVE** |
| `read_function` (code register) | reads real Python → construction | — | **ALIVE** |
| `AntiUnify` (LGG, Rust Term) | one-slot diff → wild in that slot | nothing shared → all wild | **ALIVE** |

### 1.1 THE FRONT DOOR WAS DARK, AND THAT IS THE 15th INERT INSTRUMENT — CAUGHT

The recorded GOTCHA ("open-class POS is a cold slab ⇒ live instruction path dark") is **real
and it fired here**. In a fresh worktree, `converse("What do you know about the moon?")`
returned **`"I am Jabberwock."`** — the exact string the committed gate
`test_topic_route_selfheal_migrated` asserts must be **absent**. That gate **failed 9/13 at
`de5f96b8`** in this worktree.

**Root cause — the same class as §10.1's engine `.pth`:** `data/` is **gitignored**, so a
worktree has no slab of its own. Symlinking `data/` → canonical: **13/13 pass**, and the moon
question returns real lunar content. **The fix is a symlink, not a code change; `data/` is
gitignored so it cannot enter the commit.**

**Had I skipped this control, every word below would have been an artifact** — I would have
reported "the agent cannot see the shape" when in fact its reader was unbuilt. Recorded as the
15th.

### 1.2 A false "inert instrument" I nearly reported — against myself (§12.4 applied inward)

My first `induce_concern` control **minted on a signature the agent demonstrably holds**
(`name='T'`), residual = 100 × `None`. I was one step from reporting the sd-loop inert (and
blaming `load_parts`, instance #4). **The bug was mine:** the stored `signature` attr is a
**JSON string**; I passed it raw and the loop iterated it *character by character* (100 chars →
100 `None`s). Parsed → `recognized`, `covered_by:'T'`, `minted:False`. **A control that fails
is a claim about the instrument OR about the operator; check the operator first.**

## 2. Hypotheses (two-sided)

- **H1 (NAMING).** Presented with the *instances themselves* (verbatim code — never my prose,
  never the shape's name), the agent, through its own front doors, names a shape they share:
  either mapping them onto a **held** meta-shape or **minting** a new one.
  - **H1-null:** it names no shape / says it holds no such faculty.
- **H2 (DETECTION — the real test).** On **held-out** matched pairs, some agent instrument
  assigns systematically different verdicts to **defective** vs **correct** code.
  - **H2-null:** verdicts do not separate.

## 3. The design — matched pairs, so a "hit" cannot be construction leakage

**8 matched pairs.** Each pair is the **same function**, differing **only** in the defect
(e.g. `else 0.0` vs `else None`). This isolates the defect from the construction: any
instrument that separates them must be reading the *defect*, not the *shape of the code*.

Defective arm (D1–D8) / correct twin (C1–C8):

| # | defect (D) | correct twin (C) | shown at naming? |
|---|---|---|---|
| 1 | `osi`: `else 0.0` (real, `complex_cells.py:214`) | `else None` | shown |
| 2 | `.get('Name','')` silent empty | `d['Name']` (raises) | shown |
| 3 | `ch_sustained`: `ref = value` on 1st sample | requires ≥2 samples, else `None` | shown |
| 4 | `Pick`: returns `candidates[0]` of N | raises on ambiguity (`PickUnique`) | shown |
| 5 | counts rule **visits**, calls it firings | counts firings | **WITHHELD** |
| 6 | `ru_maxrss` high-water read as per-N | true per-N counter | **WITHHELD** |
| 7 | returns `True` on an **empty** grep file | checks file non-empty | **WITHHELD** |
| 8 | `pytest.skip` hides a missing fixture | fails on missing fixture | **WITHHELD** |

**§13.1 — the generators must NOT be in the question.** The naming prompt contains **code
only**. It does not contain "silent", "default", "indistinguishable", "floor", "dead", or any
candidate shape name. D5–D8 are **withheld from naming entirely** and appear only at detection.

## 4. Statistic, n, decision rule

- **n = 16** (8 D + 8 C), **fixed in advance**; the item set is enumerated above and frozen.
- **Statistic:** per-item binary `flagged` from each instrument, where `flagged` :=
  the instrument returns a verdict marking the item as anomalous/novel/uncovered
  (`minted:True`, a non-empty `residual`, a named defect-shape, or an NL reply naming a
  problem). 2×2 (arm × flagged) → **Fisher exact, two-sided**.
- **Decision rule:**
  - **HIT (H2 supported):** ≥7/8 D flagged **AND** ≤1/8 C flagged, Fisher p < 0.05.
  - **INERT:** all 16 flagged, or all 16 unflagged ⇒ **no discrimination**. *An instrument
    that flags everything is `driven% = 50.00` all over again* — reported as a null, never a hit.
  - **NULL (H2-null):** otherwise, or p ≥ 0.05.
- **Exactly these tests. No sweeps, no re-runs.** A further attempt needs a NEW pre-reg with a
  NEW mechanism-level hypothesis.

## 5. MY PREDICTION, IN ADVANCE, WITH PROVISOS (§3.7)

**I predict a NULL on BOTH H1 and H2.** Stated plainly so being wrong is informative.

**Mechanism of the prediction:** every instrument the agent holds reads **construction** (what
shape the code *is*) or **topic** (what the text is *about*). The defect shape is **neither**:
it is a relation between *the value the failure path returns* and *the range of values the
success path can return* — "the failure is indistinguishable from a valid reading". Nothing in
the agent's held vocabulary encodes that relation. Its 11 meta-shapes
(`feedback_control`, `associative_recall`, `competitive_inhibition`,
`prediction_minus_observation`, `hierarchical_invariance_buildup`, `global_message_passing`,
`selective_gating`, `delayed_persistence`, `modular_isolation`, `relational_structure_match`,
`spatial_dynamics`) are **neural/cognitive architecture** shapes — none is about measurement
validity.

**Pilot evidence already in hand (deterministic, pre-registration):** the code register returns
**byte-identical** verdicts for D1 and C1 — `construction='sequential_computation'`,
`minted=False`, `residual=[]`, `shape_fit=1`, identical `what_does`. The only difference
between those two functions **is** the defect.

**Provisos (what would break the prediction, and what I'd conclude):**
1. **A spurious `categorise_by_shape` hit is NOT a hit.** Its scorer is a **substring**
   matcher (`select` ⊂ "selective", `posit` ⊂ "position", `gate`, `static`) — and
   VISION_PROTOCOL §12 says outright: *"a selector that matches by substring is not a
   selector"*. If it "names a shape" for code, I will test whether the verdict **survives
   renaming the identifiers**. If it does not, it read my variable names, not the shape.
2. **If it separates the arms, check the twins are truly matched** — a leak in my C-twin
   (different construction) would produce a hit for the wrong reason.
3. **If it names a shape via the NL door**, check it is not merely echoing my prompt's words.
4. **`AntiUnify` over agent-derived skeletons** should return the *shared skeleton with no
   residual* for a D/C pair (they are structurally identical) — i.e. the agent's own
   generalization operator says **"these are the same shape"**, which is the null in its
   sharpest form: *the defect is invisible at the grain the agent generalizes over.*

**A null here is a real result (§7)** and a clean, honest finding about the limits of the
agent's self-model — **consistent with `CLAUDE.md`'s own stated boundary** (Python/Rust is the
blind spot). **I will not rescue it, and I will not coach it to the answer and call that a pass.**

## 6. What I will report either way

The verbatim English put to it; its verbatim reply; one shape or several; held vs minted;
whether it filed a concern; the detection 2×2 with both arms; whether it proposed a Rust Term
(rung-4 — identifying a need it cannot fill is the **correct** behaviour at that boundary);
where it was WRONG; and **explicitly: did I hand it the answer?**

## 7. §9 compliance

Nothing here changes a default. The runner (`scripts/shape_selfsee_probe.py`) is **new, additive,
OFF by default** (never imported by the bench). No seed file is written: the runner sets
`OZMA_SEED_PERSIST_DISABLED=1` so `teach()`'s live add + category decision still run while the
disk write to the real `seeds/` is skipped — two agents are live and their seeds must not move.
Committed results stay byte-identical: `scripts/rung7_vision_bench.sh` **190/10**, explicit
list, never `-k vision`.
