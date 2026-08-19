# Protein folding as collapse — scoping doc

**Date:** 2026-08-17. Scope-only, no code yet. Written before any worktree/
branch is opened, per house discipline (size before build).

**HEADLINE: folding is not a new architecture. It is the existing `collapse`
loop plus the existing sd loop (`ShapeDecode`) plus the existing
admissibility grammar (Γ), applied to a domain that hasn't used them yet.**
No new cognitive primitive is proposed here. What's new is one seed, a
handful of Rust Terms for continuous geometry/energy, and a graph schema for
residues/atoms/torsions. Read this against CLAUDE.md's "SHAPES, NOT NUMBERS"
and "BASE-AS-DIMENSION + frame/continuum" sections — this doc is the
worked application of both to a domain neither has touched.

---

## 0. SHAPES-NOT-NUMBERS classification, done first

For every mechanism below, is it (a) *a quantity that changes* → sd loop,
(b) *a set of allowed moves* → Γ production, or (c) genuinely a new
primitive? Answered per-mechanism in §2/§3. No scalar knob (rate, floor,
threshold, fixed weight) is proposed anywhere in this doc without first
being checked against (a)/(b) and rejected. Where one *is* proposed
(none, currently) it must be flagged and justified, not slipped in.

---

## 1. What "folding" maps to

Folding = an unfolded/extended conformational graph state COLLAPSING to
the lowest-energy (native) state. This is the same word the engine already
uses for the AbS render→compare→`Argmin` loop (vision, ink) and for the
F-16 order-N viability ladder's convergence. Not a metaphor of convenience
— literally the same collapse shape: propose candidate state(s) from a
codebook, render/evaluate against a continuous comparator, hold the
`Argmin`, iterate until residual is below tolerance or a fixed-point rule
stops firing.

---

## 2. Graph substrate (G)

| node type | notes |
|---|---|
| `Residue` | sequence-ordered via `next_residue` edge |
| `Atom` | children of `Residue`, backbone + sidechain |
| `Bond` | edges between `Atom`s, fixed geometry (length/angle) |
| `TorsionAngle` | one per rotatable bond (phi/psi/chi_n) — **value is a QUANTIZED BIN, not a float** (frame/continuum rule: in-frame = integer lattice) |
| `SecondaryStructure` | `Microtheory` grouping residues (helix/sheet/loop) |
| `Contact` | spatial-proximity / H-bond / disulfide edge — MINTED during collapse, never precomputed as a Python pass |

No agent decision lives in this schema — it's mechanical translation from
PDB/FASTA, same as `ChatWorld` tokenising text. World adapter builds it,
nothing more.

---

## 3. The two primitives, applied

### 3a. Γ (admissibility grammar) — classification: (b), a set of allowed moves

Do NOT write steric-clash / connectivity checks as Python `if` filters over
candidate conformations (this is exactly the humanoid-composer defect:
`insert_edge` bypassing `check_edge`, cost terms summed unconditionally).
Instead, admissible moves are GENERATED:

- `Production{backbone_bond_geometry}` — fixed bond length/angle, no
  Γ production ever generates a violating edge
- `Production{steric_exclusion}` — clash is an edge that is never
  admissible, not one filtered out after generation
- `Production{ramachandran_basin}` — phi/psi pair admissible iff
  `(phi,psi)` falls in a held basin set (basin set itself is sd-loop
  codebook data, see 3b — Γ reads it, doesn't hardcode it)
- `Production{disulfide_constraint}`, `Production{proline_ring_constraint}`

`admissible_moves` returns the weighted `(type, attrs, weight)` set exactly
as the existing engine primitive already does elsewhere. This is the
"generated absence" pattern from the bigville violence-seed retrospective
— folding's steric/geometric constraints are a textbook case of a subsystem
that should declare productions rather than reimplement filtering.

### 3b. sd loop — classification: (a), a quantity that changes

- **Rotamer library = `ShapeSignature` codebook.** `sd_recognize` matches
  observed chi-angle bin combination to a known rotamer. `sd_transform_decode`
  covers a uniform backbone-dependent rotamer shift (one delta across the
  chi dims — rung 2, not a new rotamer). `sd_infer_dimension` covers a
  chi-angle residual that's COUPLED across dims in a way no existing
  rotamer explains (rung 3 — mints a `LatentDimension`, e.g. a
  backbone-coupling term). `sd_mint_quantum` mints a genuinely novel
  rotamer only when rungs 1-3 fail — the same Occam order the ink/omniglot
  arc already proved out, transplanted, not reinvented.
- **Secondary-structure motifs = meta-shapes.** Helix/sheet/turn recognized
  against the `analogical_thinking` `MetaShape`/`ShapePrinciple` codebook
  (the grain `META_SHAPE_FIRST_CLASS_RESULTS.md` just fixed the
  recognizer+mint path for). Non-canonical turns / novel loop
  conformations mint new entries the same way.

### 3c. Frame/continuum split — the hard rule, checked explicitly

- IN-FRAME (integer lattice): torsion-angle bins, rotamer indices,
  secondary-structure labels. Never store a raw float dihedral as agent
  state — `coord_ints` returning `None` on a float slot is CORRECT
  elsewhere in this codebase and the same discipline applies here.
- CROSS-FRAME (continuous, lives only in the comparator/map): the physical
  energy function (force field), bond geometry idealization, RMSD-to-native.
  This is the verdict layer — exactly the AbS pattern already measured on
  Omniglot: **bins propose (rotamer/motif codebook decode), continuous
  decides (energy comparator + held `Argmin` over candidate set)**. Direct
  transplant of "bins propose, continuous decides," not a new idea.

### 3d. Conformational search = quanta navigation — classification: (a)

`space_quantize` / `qf_*` rules, reused not reinvented:
- N-dimensional, one axis per torsion angle, **per-dimension resolution**
  (backbone phi/psi need finer quanta than a surface lysine chi3)
- foveated — decode fine detail only where focus is (flexible loop
  regions), coarse elsewhere (rigid secondary-structure cores) — this is
  the SAME mechanism as spatial foveation in `spatial_sense`, not a
  protein-specific hack
- frontier flood over reachable rotamer/backbone states, portals = the
  Γ-admissible transitions from §3a
- multi-source frontier-seek for exploring multiple nucleation sites (real
  folding is not single-source)

### 3e. Order-N viability ladder — classification: (a), reused from F-16 arc

- order-0 reflex: fixed local minimization step (steepest-descent nudge on
  one torsion)
- order-1 held-ratio: statistical/knowledge-based potential, held not
  re-derived per step (a PDB-derived rotamer/torsion frequency table —
  itself sd-loop codebook data, not a fitted scalar)
- order-N search: full sampling (MC / replica exchange) when 0/1 residual
  doesn't converge

**No bespoke step-size/rate knob anywhere in this ladder.** If a step size
is needed it is a rung-2 sd-loop transform (a delta in the existing basis),
per the F-16 "each ad hoc rate eventually needs its own rate" finding — not
a fresh scalar.

---

## 4. What's genuinely new — classification: (c)

Two things don't reduce to existing primitives and need sizing before
build:

1. **Energy-term evaluation** (bonded + nonbonded: bond/angle/dihedral
   springs, van der Waals, electrostatics, H-bond, solvation). This is the
   cross-frame comparator itself. Proposed as a new Rust Term
   (`runners/dsl/src/term.rs`), NOT Python — per architecture rule, no
   agent decision math in Python, and this is exactly the kind of
   primitive-in-Rust/composition-in-graph split the rule requires. Size
   this FIRST — it's very likely the largest single build item and the
   place this scope is most likely to be wrong about effort.
2. **RMSD / structural-distance metric** for the native-structure gate.
   Reuse the `DtwTo`/`PointSetDist` precedent from the ink arc (verdict-
   layer comparator, already proven as a Rust primitive pattern) — do not
   build a bespoke metric from scratch, adapt that one.

Everything else in §3 is composition of primitives that already exist and
are already tested (sd loop: F-16 + ink + Omniglot; Γ: original substrate;
quanta nav: `quanta_navigation.json`, 8/8 gated).

---

## 5. Seed

`protein_folding` seed. Depends on `core` + `shape_decode_loop` +
`quanta_navigation`. Ships: rotamer codebook (PDB-derived, real data — per
[[project_bigville_as_test_substrate]] precedent, real data beats synthetic
fixtures for this kind of validation), Ramachandran basin set, Γ
productions from §3a, secondary-structure meta-shape seeds if not already
covered by the general meta-shape codebook.

---

## 6. World adapter (Python, mechanical only — the architecture rule applies in full)

```
ingest: PDB/FASTA text -> Residue/Atom/Bond nodes.  No decisions.
        (mechanical translation, same shape as ChatWorld tokenising text)
tick(): substrate runs Γ + sd loop + quanta-nav collapse to fixed point
emit:   read final TorsionAngle/coordinate state -> PDB out.  Pure query.
```

Any temptation to write "if clash then reject conformation" in the adapter
is the self-correction prompt firing — that's a Γ production, not Python.

---

## 7. Open risks / sizing questions (name before building, per house rule)

- **Energy function is the real unknown.** Force-field complexity (how
  many terms, how much accuracy needed to discriminate native from
  decoys) is unsized. This is where effort estimate is least trustworthy.
  Size it as its own rung before committing to the rest.
- **Dimensionality.** ~20 residues × ~4 torsions ≈ 80 dims minimum for a
  small peptide; a real domain is 10x+ that. Foveation is not optional,
  it's load-bearing from the first gated test, not an optimization added
  later.
- **Codebook seed data provenance.** Rotamer library / Ramachandran basins
  need real PDB-derived statistics, not hand-picked bins — same "real
  data over synthetic fixture" lesson bigville already taught this
  project.
- **No claim of folding "working" without a powered gate.** Per the
  run-15 standing rule (power the gate before the endgame — deltas within
  ~3x the per-episode step are noise), first gate is a small peptide with
  KNOWN native structure, RMSD-to-native as the held comparator, enough
  independent folding attempts for a CI-separated result — not one
  successful trajectory presented as a headline.

---

## 8. Suggested first gated rung (not started — for sign-off)

Smallest defensible slice: a short peptide (≤20 residues) with a known
PDB native structure, existing published rotamer library as codebook
seed, minimal energy Term (bonded terms + simple LJ, no electrostatics/
solvation yet — smallest cross-frame comparator that can discriminate
anything), order-0+order-1 ladder only (no full MC search yet), gate =
RMSD-to-native under a pre-registered threshold, powered N (multiple
independent folding runs, Wilson CI, not N=1).

This rung either confirms the collapse/sd-loop/Γ composition works at
toy scale, or localizes exactly which of the three primitives doesn't
transfer — either outcome is a result worth having, per this project's
own standing preference for a null that localizes cause over a pass that
doesn't explain itself.
