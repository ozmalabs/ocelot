# SHAPE-SELFSEE — RESULTS: **THE NULL IS THE RESULT, AND IT WAS PREDICTED**

*Pre-registered in `VISION_SHAPE_SELFSEE_PREREG.md`, committed at **`649e4f11`** BEFORE the
confirmatory run. Runner: `scripts/shape_selfsee_probe.py`. Raw: `results/shape_selfsee.json`.*

**Engine:** `engine c8433a515391 @ .../runners/dsl/python/substrate_rs/_native.abi3.so`
`[shared build — Rust source identical]`, fingerprint
`858e2bded840461ef8de92bc95309d3366715cac8954c6a9b3c444c9804709cb`. **No Rust was touched.**
**Base:** `de5f96b8`. **Seeds 19000–19999: ALLOCATED, BURNED NONE** — the rung is deterministic
(no RNG arm).

---

## The headline

**The jabberwock cannot see this shape through its own front door — and the null is clean,
mechanistic, and consistent with `CLAUDE.md`'s own stated boundary.**

| hypothesis | verdict |
|---|---|
| **H1 — NAMING** | **NULL.** Asked what shape the instances share: *"I don't hold that."* No shape named, none minted, none mapped to a held meta-shape. |
| **H2 — DETECTION** | **NULL (INERT-unflagged).** DEFECT flagged **0/8**, CORRECT flagged **0/8**, **Fisher exact two-sided p = 1.000000**. |

**Its own generalization operator states the null in its sharpest form.** `AntiUnify` — the
agent's least-general-generalization Term, *literally* "what shape do these share" — returns for
**every one of the 8 defect/correct pairs**:

```
AntiUnify(defect, correct) = (('LET',),)     # no wildcard: NOT "these differ here"
```

**The agent's own operator says the defective function and its correct twin are the SAME SHAPE.**
The defect is invisible at the grain the agent generalizes over.

## Did I hand it the answer? — **No, and here is the audit trail**

The naming prompt was **code only**, verbatim (`scripts/shape_selfsee_probe.py::PAIRS`). It
contained no shape name and none of the words that encode the shape — no *silent*, *default*,
*indistinguishable*, *floor*, *dead*, *guard*, *valid-looking*. The instances were **not
pre-grouped** and not accompanied by prose of mine. **4 of the 8 instances (D5–D8: the
visits-as-firings counter, the `ru_maxrss` high-water read, the empty-file pass, the skip-guard)
were WITHHELD from naming entirely** and appear only at detection.

**The one place the agent DID file a gap is the one place I DID coach it — and I am reporting it
as coaching, not as a pass.** See §"The gap pipeline" below.

## The verbatim exchange

**The code, put to it verbatim (`converse`), and what it said back:**

> **Q:** `def osi(tc):` / `    a, b = tc[0], tc[1]` / `    return float((a - b) / (a + b)) if (a + b) > 1e-9 else 0.0`
> **A:** *"I read that function but could not take it as a lesson (assignment target is 'Tuple',
> not a plain Name -- tuple/list-unpacking and attribute/subscript stores are the named residual,
> never silently dropped)."*

> **Q:** `def catalogue_name(entry):` / `    name = entry.get('Name', '')` / `    return name`
> **A:** *"I read that function but could not take it as a lesson (Call to None is neither a held
> leaf, the sum-fold, nor an emitted faculty (un-translatable: the held DSL lacks a leaf for it —
> the named residual))."*

> **Q:** `def sustained_ref(ref, value, n):` / `    ref = value if n == 0 else ref + (value - ref) / n` / `    return value - ref`
> **A:** *"Thank you -- I read that function and learned the shape 'taught_sustained_ref'
> (triggers: sustained, ref)."*

> **Q:** `def pick(candidates):` / `    chosen = candidates[0]` / `    return chosen`
> **A:** *"I read that function but could not take it as a lesson (un-translatable AST node type
> 'Subscript' … FIELD stays READ (the construction recognises the shape) but not
> Term-evaluable.)."*

**The question, in English, naming nothing:**

> **Q:** *"What shape do these four things share?"* → **A:** *"I don't hold that."*
> **Q:** *"Is that one shape or several?"* → **A:** *"I don't hold that."*
> **Q:** *"Have you seen that shape before?"* → **A:** *"the agent's functional form decomposes
> into these seven meta-shapes — … the primary principle is hierarchical invariance buildup…"*
> — **a MISROUTE (see "Where it was wrong").**

## The instruments — all five ALIVE, both arms, BEFORE the run (§1 clause 4)

| instrument | hit arm | floor arm |
|---|---|---|
| `converse` | "moon" → real lunar content | "What are you?" → `I am Jabberwock.` |
| `categorise_by_shape` | 3/3 ideal exemplars → right meta-shape | 3/3 nonsense → `None` |
| `induce_concern` | novel → `minted:True` | held `T` sig → `recognized` |
| `read_function` | reads real Python → construction | — |
| `AntiUnify` | one-slot diff → wild **in that slot** | nothing shared → all wild |

**`categorise_by_shape` returned `None` on all four instances — the FLOOR.** This is the *honest*
outcome and it makes proviso 1 moot: its substring scorer (`select` ⊂ "selective", `posit` ⊂
"position") did **not** produce a spurious hit. It did not name a shape it had no business naming.

## The detection test — both arms, and the twins are truly matched

8 **matched pairs**: the same function, differing **only** in the defect. Every one of the 16
items read **identically**: `construction='sequential_computation'`, `minted=False`,
`residual=[]`, `shape_fit=1`.

```
2x2: DEFECT flagged 0/8 | CORRECT flagged 0/8      Fisher exact two-sided p = 1.000000
PRE-REGISTERED VERDICT: INERT (flags nothing — no discrimination)
```

### The number I nearly mis-reported, and the proviso that caught it

The runner printed **"identical readings: 2/8 pairs"** — which *looks* like the agent
distinguished 6 pairs. **It did not.** The only field that differed was `what_does`, which
**recites the identifier names I chose**:

```
DEFECT  what_does: … over chosen, candidates
CORRECT what_does: … over chosen, one_or_raise, candidates      # <- MY variable name, echoed
```

Proviso 1 (pre-registered: *"test whether the verdict survives renaming the identifiers"*).
Neutralising the names — leaving **the defect untouched, `0.0` vs `None`** — the readings become
**byte-identical across all six keys**:

| key | DEFECT | CORRECT |
|---|---|---|
| construction | `sequential_computation` | `sequential_computation` |
| minted / residual / shape_fit | `False` / `[]` / `1` | `False` / `[]` / `1` |
| what_does | *computes a value through a sequence of intermediate bindings* | *(identical)* |
| skeleton | `[['LET']]` | `[['LET']]` |

**The 6/8 "difference" was 100% my variable names.** Reporting it as detection would have been
this arc's 15th defect, authored by me.

## WHY — the mechanism, which is the useful part

The prediction was right for the stated reason. **Every instrument the agent holds reads
CONSTRUCTION (what shape the code *is*) or TOPIC (what text is *about*). The defect shape is
neither.** It is a relation between **the value the failure path returns** and **the range the
success path can return** — *the failure is indistinguishable from a valid reading*. Nothing in
the agent's held vocabulary encodes that relation:

- Its **11 meta-shapes** (`feedback_control`, `associative_recall`, `competitive_inhibition`,
  `prediction_minus_observation`, `hierarchical_invariance_buildup`, `global_message_passing`,
  `selective_gating`, `delayed_persistence`, `modular_isolation`,
  `relational_structure_match`, `spatial_dynamics`) are **neural/cognitive architecture**
  shapes. **None is about measurement validity.**
- Its **code codebook** reads at **ROOT-SHAPE granularity** — `osi`'s whole body collapses to the
  one-token skeleton `[['LET']]`. **The fallback value `0.0` is a LEAF. It is not in the
  skeleton at all.** The register cannot see it *by construction*, not by accident.

**This is exactly the boundary `CLAUDE.md` already draws:** *"the agent can self-repair exactly
where its cognition is graph-native … it CANNOT edit the Python front end, because that is not
graph it can see or vary."* The defects are Python/Rust facts. **The null is not a
disappointment; it is the documented boundary, measured.**

## Where it was WRONG

1. **The anaphor misroute.** *"Have you seen that shape before?"* → routed to the `self_shape`
   reader and answered about **its own seven meta-shapes**. "That shape" resolved to *itself*.
   It answered a **different question than the one asked** — and did so **fluently**, which is
   the dangerous kind of wrong.
2. **`induce_concern` reported `covered_by='T'` for all four code skeletons.** The one-token code
   skeleton `[['LET']]` was "covered" by a **handwriting stroke shape named `T`** — a cross-domain
   codebook collision. A 1-token skeleton matches almost anything, so the "recognized" verdict is
   **vacuous** at this grain. *(Noted, not overclaimed: it is suggestive of the very shape under
   study — a match that cannot fail loudly — but I did not test it and do not claim it.)*
3. **It "learned" the wrong thing from the right code.** `sustained_ref` → *"learned the shape
   'taught_sustained_ref' (**triggers: sustained, ref**)"* — keyed on **my function name**, not on
   the structure or the defect. Rename the function and the "learning" changes.

## The gap pipeline — alive, but it only fires when I NAME the deficiency (this is coaching)

- *"What shape do these four things share?"* → *"I don't hold that."* — **files NOTHING.** The
  agent does **not** treat "I cannot answer this" as a gap on this path.
- *"Why did you not notice that the guard returns a valid-looking value?"* → files an **implicit**
  knowledge gap on *"valid-looking value"*.
- *"You cannot tell a broken measurement from a working one."* → *"Noted -- I've filed that as a
  gap to work on. I won't change myself without review."* → an **explicit_report** gap.
- After the whole probe: *"I have no gaps currently filed."*

**The last two are me handing it the answer in words and it echoing the words back as a gap
title.** That is the **explicit-report path working as designed** — and it is **not** evidence the
agent saw the shape. Recorded as coaching, scored as **null**.

## Did it propose a Rust Term (rung-4)? — **No**

It minted nothing, proposed no Term, and identified no need it could not fill. **It did not reach
the boundary**; it never got far enough to notice one existed. *(Identifying a need it cannot
itself fill would have been the correct behaviour at that boundary — it did not do that.)*

## THE 15th INERT INSTRUMENT — CAUGHT, and it would have faked this entire result

The recorded GOTCHA ("open-class POS is a cold slab ⇒ the live instruction path is dark") **fired
here**. In a fresh worktree, `converse("What do you know about the moon?")` returned
**`"I am Jabberwock."`** — the exact string the committed gate asserts must be **absent**.
`tests/test_topic_route_selfheal_migrated.py` **failed 9/13 at `de5f96b8` in this worktree**.

**Root cause — §10.1's class exactly:** `data/` is **gitignored**, so a worktree has **no slab of
its own**, the same way it has no engine of its own. Symlinking `data/` → canonical: **13/13
pass**, and the moon question returns real lunar content. **The remedy is a symlink; `data/` is
gitignored so it cannot enter a commit.**

**Had I skipped the positive control, I would have reported this same NULL — from a dark
reader.** The verdict would have been *identical* and *worthless*: "the agent cannot see the
shape" when in truth its reader was unbuilt. **The null is only worth anything because the
instrument was proven alive first.**

> **A recommendation this rung earned:** `§10.1`'s logic covers the **engine**; the **slab** has
> the same failure mode (gitignored ⇒ absent in every worktree ⇒ silently degraded NL) and no
> equivalent gate. A `data/` presence check belongs beside `engine_preamble()`.

### And one I caught against MYSELF (§12.4, applied inward)

My first `induce_concern` control **minted on a signature the agent demonstrably holds**
(`name='T'`), residual = **100 × `None`**. I was one step from reporting the sd-loop **inert** and
pinning it on `load_parts` (instance #4 — a real Rust bug, which would have made the false report
*plausible*). **The bug was mine:** the stored `signature` is a **JSON string**; I passed it raw
and the loop iterated it **character by character** — 100 characters, 100 `None`s. Parsed:
`recognized`, `covered_by:'T'`, `minted:False`.

**A control that fails is a claim about the instrument OR about the operator. Check the operator
first.**

## §9 compliance — and **the §9 BASELINE IS ITSELF INSTANCE #10**

- `scripts/shape_selfsee_probe.py` is **new, additive, OFF by default** — never imported by the
  bench, run explicitly.
- **No seed file was written.** The runner sets `OZMA_SEED_PERSIST_DISABLED=1`, so `teach()`'s
  live add + category decision still run while the disk write to the real `seeds/` is skipped —
  two agents are live and their seeds must not move. Verified: `git status seeds/ runners/` is
  **empty**.
- **No Rust touched.** No default changed.

**`scripts/rung7_vision_bench.sh` — byte-identity CONFIRMED, by a paired control:**

| condition | result |
|---|---|
| **without `data/`** (the condition the baseline was recorded in) | **190 passed, 10 skipped** — the §9 number, **byte-identical** |
| **with `data/` symlinked** | **200 passed, 0 skipped** |

**My changes alter nothing** — 190/10 reproduces exactly in the baseline condition. But the
control exposes something else:

> **The `190/10` baseline is measured in the DEGRADED condition, and its 10 skips are
> INSTANCE #10 OF THE GROUND-TRUTH LIST — live, right now, in this arc's own §9 gate.**

```
tests/test_vision_curriculum_migrated.py:47   pytest.skip("BSDS300 corpus absent (data/vision_curriculum/BSDS300)")
tests/test_vision_growth_migrated.py:120      pytest.skip("BSDS300 corpus absent (data/vision_curriculum/BSDS300)")
```

`data/` is gitignored ⇒ **absent in every worktree** ⇒ these 10 tests **have never run in any
worktree**, while the suite reports a clean green. That is *precisely* the defect the list
records as **"a pytest skip-guard hiding a missing fixture — a test silently skipping on every
fresh checkout while the suite reported green."** With `data/` present they run and **all 10
pass** — so nothing is broken, and that is exactly why nobody noticed.

**The irony is the finding, and it is not decorative:** the shape under study was sitting inside
the instrument used to certify the study. **I did not detect it by naming the shape — I detected
it by running the positive control**, which is the same way all fourteen prior instances were
caught, and the opposite of how the agent would need to catch it.

**Recommendation (not actioned here — §9 says defaults do not move without review):** the §9
baseline should be stated **with its condition** (`190/10 without data/`, `200/0 with`), or the
skip should become a hard fail when `data/` is expected. A gate with 10 permanently-dormant
tests is 5% vacuous and does not know it.
