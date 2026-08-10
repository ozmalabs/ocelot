# VISION — DISSIPATION *IS* INFERENCE: one integer relaxation dynamics that is a physical law in one frame and MAP perception in the other, differing ONLY by a relabel (PRE-REGISTRATION)

*Committed ALONE, BEFORE any implementation and BEFORE any measurement
(PROTOCOL §3). Isolated worktree off `main` HEAD **`6342f643bb`** (LEDGER 196000 —
STALENESS DECAY). Engine canonical **`793ce09ed498a749abb79aeaea44b92e`**
(`_native.abi3.so`, shared build; this rung adds **NO Rust**, `term.rs` diff
EMPTY). Seed block **197000–197999**.*

Seed-claim check (verbatim, run before any number):

```
$ python3 scripts/seed_claim.py 197000 197999
SEED CLAIM 197000-197999: CLEAN -- no collision DETECTED.
  Scope: 896 files with seed sinks; 609 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

---

## 0. THE CLAIM (the project owner's, made a GATED OBJECT)

**Cognition is the SAME PROCESS as physics, in a different frame** — not "like",
not "running on", but the identical frame-local integer dynamics, read in two
frames. This rung does NOT try to prove that for all cognition (that is the
program). It builds ONE dynamics that is *provably* a physical law in one frame
and a cognitive operation in the other — **the SAME integer computation** —
differing ONLY by a relabel, with a falsifier that proves they are one process
and not two that happen to coincide.

The dynamics chosen is the known **statistical-mechanics ⇔ Bayesian-inference
identity**, made concrete and integer-native on the substrate: a discrete
**dissipative relaxation of a field** toward the minimum of a quadratic energy.
Read as physics it is the second law settling a coupled system to equilibrium;
read as cognition it is **MAP inference over a Gaussian Markov Random Field** —
perceptual filling-in / denoising a noisy input toward the clean percept. The
Gibbs distribution *is* the posterior; the energy minimum *is* the MAP estimate.

## 1. THE SHARED DYNAMICS — one rule set, integer-native, red-black exact descent

A W×H grid of cells. Each cell `i` holds an integer `val` = `x_i` (the field
value / estimate) and a fixed integer `obs` = `y_i` (the external field / noisy
observation). Cells are 4-connected by `adj` edges. A single hub `RelaxField`
node carries the control scalars `lam` (integer data precision λ), `phase` (the
red-black colour to update this half-sweep, 0/1), `sign` (+1 dissipative /
descent — the sound path; −1 anti-dissipative / ascent — the G4 falsifier), and
`enabled` (1 to fire).

The per-cell update (ONE rule, `df_relax`, `batch:true`, matching only cells
whose `par == phase`):

```
num  = lam*obs_i + Σ_{j∈adj(i)} val_j          # Sum over Neighbours(i,"adj")
den  = lam + deg_i                              # lam + Count(Neighbours(i,"adj"))
cand = IDiv(2*num + den, 2*den)                 # round-to-nearest INTEGER argmin
val_i ← IfThenElse(sign>0, cand, 2*val_i - cand)  # descent : reflected ascent
```

`cand` is the integer argmin of the cell's local energy parabola holding its
neighbours fixed. **Red-black colouring** (a cell updates only when
`par==phase`; `par=(row+col)&1`) makes every simultaneously-updated cell
mutually non-adjacent, so one coloured half-sweep is EXACT block coordinate
descent: each cell moves to its conditional integer argmin holding the (fixed,
opposite-colour) neighbours constant. Therefore the global energy is
**non-increasing every half-sweep, exactly, over the integer lattice** — no
rounding limit cycle, termination in finitely many steps (integer energy is
bounded below by 0 and strictly decreases off the fixed point). The measure
adapter flips `phase` between `run_rules(1)` calls (a mechanical clock, exactly
like `input_epoch`); it makes NO decision.

**NO Rust, NO new Term.** Every operator used exists today: `Sum`, `Neighbours`,
`Count`, `Attr`, `IDiv`, `Plus`, `Times`, `Minus`, `IfThenElse`, `Lt`/`Gt`/`Eq`,
`And`, `Var`, `Lit`. `term.rs` diff is EMPTY. The demonstration is a new seed
`seeds/dissipation_inference.json` plus a mechanical measure adapter
`scripts/dissipation_inference_measure.py` (builds the field graph, ticks
`run_rules`, reads attributes — no agent logic).

## 2. THE RELABEL TABLE — the ENTIRE difference between the two frames (pure, zero dynamics)

The seed, the rules, the attribute names (`val`,`obs`,`lam`,`adj`,`par`) and the
integer state are ONE neutral object. A frame is a pure interpretation dictionary
laid over it — it renames symbols and re-reads the same numbers; it touches no
arithmetic, no state, no rule.

| neutral object | PHYSICS frame | COGNITION frame |
|---|---|---|
| `val_i` (integer state) | microstate configuration `s_i` | posterior MAP estimate `x_i` |
| `obs_i` (fixed integer) | external field / boundary source | noisy observation `y_i` |
| `lam` (integer) | coupling to the field / inverse-temperature weight | likelihood precision (data term) |
| `adj` edge | nearest-neighbour interaction (Ising/Gaussian coupling) | MRF smoothness prior clique |
| `E(x)=λΣ(x−y)²+Σ_{edges}(x−x_j)²` | Gibbs / free-energy functional (Hamiltonian) | negative log-posterior `−log P(x\|y)` |
| a settling half-sweep | dissipative relaxation step (heat-bath / overdamped) | one coordinate-ascent step of MAP inference |
| the fixed point | thermodynamic **equilibrium** configuration | the **MAP percept** |
| `E` decreasing | free energy dissipated → 2nd law | evidence maximised → inference converges |
| `sign<0` | anti-dissipative (energy pumped IN) | inference run in reverse (posterior de-maximised) |

## 3. GATES (pre-registered BEFORE any number)

**G1 — THE IDENTITY (one computation, two readings).**
(a) A "physics-labelled" run and a "cognition-labelled" run — the SAME builder
differing ONLY by the relabel dictionary — produce a **BYTE-IDENTICAL integer
`val`-field trajectory, tick by tick** (the relabel touches no dynamics).
(b) The physics functional (Gibbs energy) and the cognition functional (negative
log-posterior), each computed on that ONE trajectory by an independent code path,
are the **element-wise-identical sequence** (they are the same formula, renamed).
(c) A source audit: the relabel is a pure `dict[str,str]` with no arithmetic and
no `set_attr`; the two readings share one rule set and one integer state.
PASS = (a) byte-identical ∧ (b) element-wise equal ∧ (c) audit clean.

**G2 — PHYSICS HOLDS (the 2nd law).**
On the sound path (`sign=+1`) the Lyapunov / free-energy functional `E(t)`
**decreases monotonically every half-sweep to a fixed point and never increases**;
report the curve. The coarse-grained entropy produced,
`S(t) = E(0) − E(t)` (free energy dissipated to the bath at fixed T = entropy
produced), **rises monotonically to its maximum** `E(0)−E(∞)`. `E` is computed
EXACTLY as an integer (sum of integer squares); the fixed point is reached in
finitely many sweeps and then `E` is constant.
PASS = `E(t+1) ≤ E(t)` for every t (strict until the fixed point) ∧ `E` reaches a
constant ∧ `S(t)` monotone non-decreasing to its max.

**G3 — COGNITION WORKS (percept recovery = MAP).**
`obs = clean + integer noise`. Initialise `val = obs`. The settling **recovers
the percept**: recovery error `‖val(t) − clean‖₁` drops below the input error
`‖obs − clean‖₁`, and the fixed point `val*` **MATCHES an independent reference
MAP** — (i) byte-identical to an independent numpy red-black integer
coordinate-descent denoiser (same fixed point, because it IS the same algorithm),
and (ii) within integer rounding of the exact real linear-solve MAP
`x* = (L+λI)⁻¹ λy` (the continuous cross-frame reference). "It matches because it
IS it."
PASS = final error < input error (denoising works) ∧ `val*` byte-identical to the
reference integer denoiser ∧ `‖val* − round(x*_real)‖∞` ≤ 1.

**G4 — BREAK-ONE-BREAKS-BOTH (the key falsifier, non-vacuity).**
Flip the SAME rule to anti-dissipative (`sign=−1`: `val_i ← 2·val_i − cand`, the
reflected ascent that forces `E` UP by the amount descent forced it down), same
grid, same init `val=obs`. Then **the physics breaks** — `E(t)` rises
monotonically (Lyapunov violated), diverging — **and the cognition breaks with
it** — recovery error rises monotonically / diverges (the percept is destroyed).
Breaking the dissipation breaks the inference: they are ONE process.
PASS = under `sign=−1`, `E(t)` strictly increasing over the window ∧ recovery
error strictly increasing over the window (both diverge from the sound run).

**G5 — INTEGER-NATIVE audit + DEFAULT-OFF byte-identity.**
(a) Every in-frame quantity is integer: all `FieldCell` attrs (`val`,`obs`,`par`)
and `RelaxField` control attrs (`lam`,`phase`,`sign`,`enabled`) hold integer
values across the whole trajectory; the ONLY floats are the cross-frame map — the
reference real linear-solve MAP and the normalised error/entropy ratios (the
Gibbs energy `E` itself is computed as an exact Python integer). No float appears
in a cell attr. (b) The dynamics is opt-in: the rules fire only when a
`RelaxField{enabled=1}` node exists, which the adapter creates on opt-in; the seed
is in NO default boot manifest and defines node types (`FieldCell`,`RelaxField`)
that appear in no existing graph, so **with the seed absent every existing path is
byte-identical to committed `main`** — the eye/substrate oracle
(`bash scripts/rung7_vision_bench.sh`) is unchanged BEFORE==AFTER, and the engine
canonical stays `793ce09e…`.
PASS = zero non-integer cell/control attrs ∧ oracle BEFORE==AFTER ∧ canonical md5
untouched ∧ seed unreferenced by any default loader.

## 4. HONEST SCOPE

This proves the identity on ONE dynamics, rigorously. It does **not** prove all
cognition is physics — that is the program; this is its anchor. A measured honest
negative is a valid landing and will be reported straight: e.g. the two
label-runs are NOT byte-identical (the relabel leaked into dynamics), or `E` is
NOT monotone (the integer scheme limit-cycles), or break-one does NOT break-both
(the recovery survives an anti-dissipative update — they would then be two
processes, not one). Any such result falsifies the identity as stated and is the
result.

## 5. WHAT IS BUILT

- `seeds/dissipation_inference.json` — the shared dynamics as graph data: the
  `df_relax` batch rule + the `RelaxField`/`FieldCell`/`adj` grammar. NO Rust.
- `scripts/dissipation_inference_measure.py` — IMPORT-INERT mechanical adapter
  (builds the grid, opts in, ticks `run_rules`, reads attrs, computes the two
  functionals + the reference MAP; never mutates a shared flag at import time).
- `tests/test_dissipation_inference_migrated.py` — runs the measure; gates G1–G5,
  each able to fail.
- `DISSIPATION_IS_INFERENCE_RESULTS.md` + `results/dissipation_inference/` — raw
  numbers, the two functional curves, the relabel table, the identity/divergence
  audits.
