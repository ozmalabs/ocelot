# ORBIT AUGMENTATION — the S6 wall dissolves, measured

**Date:** 2026-08-01
**Status:** RESULT (n=1, decisive on the arc's named residual). Run live by the
orchestrator against the real `SynthEnumerate` Term; reproducible in ~2s.

## 0. What was claimed, and what was wrong

Arc-4 S6 measured that structural rejection converts no traps, and I drew this
conclusion: *"the revealed rows are exhausted; excluding a decoy supplies no new
constraint; knowing something is wrong is not knowing what is right."*

The first clause was **false**, and two independent spikes said so before this
measurement — `RESEARCH_SYNTHESIS_MATHEMATICS.md` (theory) and
`RESEARCH_MATH_CAPABILITY_AUDIT.md` (audit) both derived, by different routes,
that a symmetry group **manufactures free labeled examples** from the rows
already held. This file measures it.

## 1. The measurement

Task: `br_10_top_of_three` — *"returns the largest of three numbers"*, the
arc's registered true regression. Revealed rows (3): `(1,9,3)→9`, `(7,2,5)→7`,
`(4,4,4)→4`. Held-out (never shown to the search): `(2,4,11)→11`, `(-3,-9,-5)→-3`.

| example set | `SynthEnumerate` finds | size | tested | held-out |
|---|---|---|---|---|
| the 3 revealed rows | `Max(a, b)` | 3 | 532 | **WRONG** — returns 4, expected 11 |
| **S₃ orbit of those same 3 rows** (13 distinct rows, **zero new oracle calls**) | `Max(a, Max(b, c))` | 5 | 25,240 | **CORRECT** |

Decoy check, independent of the enumerator:
`max(a,b)` satisfies **all 3 revealed rows** (`True`) and **fails their orbit**
(`False`). The orbit is what kills it.

## 2. Why this is not the thing the shape probe measured as null

`PROGRAM_SYNTHESIS_ARC5_SHAPE_PROBE.md` measured **0/13 pruning successes** and
was right to. It tested **exclusion**: remove the trap from the candidate space
and re-enumerate. That provably cannot work, and the probe found the mechanism —
exclusion prunes by *behavioural signature*, and a trap's defining property is
behavioural identity with the correct answer **on the revealed rows**, so
excluding the trap excludes the correct completion with it (8/13 cases).

Orbit augmentation is a **different intervention**: it does not remove
candidates, it **enriches the example set**, which changes the behavioural
signature space itself. Once `(3,1,9)→9` is present, `Max(a,b)` is no longer
behaviourally identical to the correct program, and the enumerator's *existing,
unchanged* observational-equivalence machinery separates them without help.

Both results stand. They measure different mechanisms, and only one of them is
the mathematics.

## 3. Why it is sound — and the failure mode that must be gated

Augmentation is only valid if the conjectured symmetry is **true of the
problem**. A wrong conjecture manufactures wrong labels and would produce
confidently wrong programs — precisely the Soloway plan-shaped-wrongness failure
this project has been avoiding. So the conjecture must be refutable, and it is,
cheaply and before any augmentation:

1. **Refutation from the revealed rows themselves.** If any two revealed rows
   are permutations of each other with different outputs, the symmetry is
   refuted outright.
2. **Refutation by unsatisfiability.** If augmenting makes the example set
   unsatisfiable (no program found at any admissible size), the conjecture is
   evidence-against and must be withdrawn rather than forced.
3. **The verdict layer is unchanged.** An augmented-set solution still faces
   every existing structural detector and the held-out protocol. Augmentation
   changes what the *search* sees; it does not touch what *acceptance* requires.

This makes the conjecture a **hypothesis the system can test on data it already
holds**, not an assumption it must be given.

## 4. Honest scope — what this does NOT establish

- **n = 1.** One task, decisively converted. Nothing here measures how many
  tasks carry a conjecturable symmetry.
- **Coverage is the open question, and the early read is small.** The shape
  probe measured only **3/76** traps as arity≥2 *and* prompt-naming a symmetric
  operation — using a lexicon it had to invent, because the seed vocabulary
  holds none (`shape_vocabulary.json` is systems-flavoured: scheduler,
  memory_store, gating). So 3/76 measures an invented lexicon's reach, not the
  ceiling of symmetry detection in principle.
- **The spec-side reader does not exist.** Deciding "this request is an N-ary
  symmetric aggregate" is the missing piece both the audit and the probe named
  independently. Until it exists, symmetry must be conjectured by a lexicon,
  and a lexicon is exactly the kind of content four arcs have measured as thin.
- **Search cost rises**: 532 → 25,240 candidates tested. Cheap here; it is a
  real budget question at scale and must be measured, not assumed.

## 5. What this changes

The S6 wall is not a wall about information; it is a wall about **which
information we bothered to compute**. Two of the three known ways to shrink a
version space were considered exhausted (more data: unavailable; exclusion:
useless). The third — *restriction of the hypothesis space via structure*
(Mitchell 1980) — turns out to be reachable here by acting with a group on data
already in hand.

The next experiment is therefore about **coverage and soundness**, not
mechanism: how many specs admit a refutable symmetry conjecture, how many
convert, and how many false conjectures are correctly refused before they can
manufacture a wrong label.
