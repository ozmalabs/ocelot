# PROGRAM SYNTHESIS — the arc, P0 → P7 (reviewer's entry point)

**Dates:** 2026-07-30/31. **Read this first**; every claim below is backed by
a phase document + a gated artifact, and every aggregate derives from
per-item rows (a baseline is a LIST of identities, never a count). The
plan and preregistrations were written before the code at every phase
(`PROGRAM_SYNTHESIS_PLAN.md`, `PROGRAM_SYNTHESIS_PREREG.md`,
`PROGRAM_SYNTHESIS_P3_PREREG.md`, `PROGRAM_SYNTHESIS_P7_PREREG.md`).

**The design in one sentence:** the agent learns to program the way this
tree does everything — constructions PROPOSE (a graph-resident codebook +
corpus statistics grown by the unchanged sd loop), EXECUTION DECIDES (a
pure fueled interpreter over a hub IR, held-out rows as the verdict), and
every loop decision is a seed rule running in the Rust `run_rules`
fixpoint, never Python.

## 1. Commit ledger

| phase | commit | what landed |
|---|---|---|
| P0 | `2d9148c2` | plan + prereg + ENUMERATED baseline (27 term-emittable identities; write battery 7/26 at fresh boot); the corpus histogram PICKS the IR variant set (21 variants @ 80.5% predicted) |
| P1 | `24200b3f` | the hub IR exists and executes: 26 `Prog*` Term variants (181→207) + `ProgEval` (pure, fueled, trap-honest, declared-oracles-only); naming primitives; 54 gates |
| P2 (+2.5) | `8b66db85`, in `1838e55f` | all read frames → ONE hub IR: python `ast` emitter 27→4099 identities; rust+lua via tree-sitter world adapters + correspondence seeds; LLVM-IR lift; same three programs written natively in rust/lua/python ProgEval to identical results; blocked reads file their own gaps |
| P3 | `1838e55f` | the "training run": the unchanged sd loop decodes 24,778 statement instances → 16 construction quanta + 131 ConstructionBigram rows; cross-language construction identity; merge-at-mint naming law |
| P4 | `941e671b` | the LLM-analog loop as SEED RULES (26 rules; codebook → lattice → enumerate → gap; CEGIS as rules; integer budgets); `SynthEnumerate` ported to Rust with exact parity; NL request + rows → accepted Program with held-out rows correct |
| P5 | `1e369e41` | every frame writes: python/rust/lua statement renderers as RenderRule graph data (42/29/31 rules, round-trip laws), llvm grows phi, and ONE accepted graph Program renders/compiles/runs identically on python + rust + lua + llvm→x86-64 |
| P6 (+B) | `d0af3f01` | the powered battery (125 tasks, Wilson CIs, twin-run byte-identical): MAIN .520, H6 null taken; the battery SURFACES a real defect (15 stalls); zero toolchain disagreements anywhere a surface built; P6-B: the self-improvement circle closes mechanically (gap → SelfConcern → promote → teach → same request accepts; write-precision 0.25 → 1.00 by measurement) |
| P6.5 | `c2319e05` | the stall fixed IN THE RULES (one seed rule); MAIN-POSTFIX .616; changed-set == stalled-set exactly (the paired claim, not the aggregate) |
| P7-A (+C) | `190e4598` | recursive ShapeDecode DESCENT (the decode's cover IS the plan; holes become sub-goals one grain finer; execution verdict at every level) — 3 frozen-gapped tasks solve end-to-end; P7-C: 15 idiom chunks mined (idiom grain ESCAPES the P3 family collapse); self-teach chunk rules |
| P7-B | `40dba0cc` | trace-guided LOCAL REPAIR (counterexample → refute → localize to the hole → re-solve with the grown row set; honest refusal to the global path); la_10 converts with 1 unit of post-failure work vs 3; locality proven statement-by-statement |
| P7-D | this rung | the POWERED re-measurement: MAIN-P7 .640; H7a/H7b/H7c verdicts (all three registered nulls, measured); the protocol-distinct REPAIR-ORACLE arm; this summary |

## 2. Headline capabilities as landed (all gated, all graph-native)

1. **One hub IR, five frames** (scope pin: python, rust, lua, x86-64 via
   the LLVM chain, LLVM IR). Read: python/rust/lua/LLVM-IR → hub IR.
   Write: python/rust/lua/LLVM→x86-64 — four executable surfaces off one
   accepted Program node, with toolchain truth (rustc, lua5.4/luajit, gcc)
   agreeing with ProgEval on every held-out call wherever a surface built
   (P6 §3: zero disagreements; the gaps are render-closure coverage, named).
2. **`ProgEval`** — one pure fueled Rust interpreter for the whole
   statement IR; traps honest, fuel uncatchable, externs by declared
   oracle only.
3. **The synthesis loop is rules, and the rules run in the fixpoint:**
   propose (codebook Argmax) → order (bigram lattice `vit` decode) →
   splice → evaluate → CEGIS (CounterExample/Excluded nodes, integer
   budgets) → enumerate (Rust `SynthEnumerate`) → accept (reflected
   `ir_subgraph`) or gap (SelfConcern). Zero Python decisions — the
   no-Python-decision source audit is a standing gate.
4. **Recursive descent (P7-A):** partial codebook cover = a skeleton;
   decode residuals = Hole sub-goals with MECHANICALLY DERIVED local rows
   (fold one-iteration unroll; final_expr live-vars); the same ladder one
   grain finer; fold-up re-verifies full rows. Small holes, big reach —
   with honest derivability boundaries (multi-item rows never guessed).
5. **Local repair (P7-B):** a verifier-revealed failing row refutes the
   accept, the TRACE (descent's own derivations reused as expectations)
   names the hole, the counterexample joins the hole's rows, only the hole
   re-solves. Refusal is honest (no hole → the untouched global path).
6. **Chunk mining + self-teach (P7-C):** recurring 2-4-statement idioms
   role/slot-abstracted from 4099 corpus functions; 15 survive a
   registered quantile threshold; idiom grain escapes P3's family
   collapse; accepted Programs feed a rules-decided self-teach mint.
7. **The self-improvement circle (P6-B):** a gapped request files a
   `SelfConcern{code_write}`, the human-gated promote → StandingConcern →
   teach-by-example loop closes, and the SAME request then accepts at
   rung 1 — the agent's own rule resolves the concern.

## 3. The powered numbers (what moved, what did not, and what every null said)

**Trajectory (primary score where an instrument existed):**

| moment | instrument | number |
|---|---|---|
| P0 baseline | 26-item write battery, fresh boot | **7/26** (frozen control; re-verified 7/26 with zero flips at P6 and gated ever since) |
| P6 MAIN | 125-task battery | **65/125 = .520 [.433, .606]** |
| P6.5 MAIN-POSTFIX | same, stall fixed in rules | **77/125 = .616 [.528, .697]** (paired claim: changed-set == the 15 stalled ids exactly) |
| P7-D MAIN-P7 | same, descent+repair+chunks | **80/125 = .640 [.553, .719]** (paired claim: changed-set == 7 ex-gapped ids exactly; zero flips of passing rows) |
| P7-D REPAIR-ORACLE | protocol-DISTINCT (one revealed ce) | 81/125 = .648; wrong accepts 19 → 2 (16 retired to honest gaps) — never compared to primary rows |

No single aggregate step in that trajectory is CI-separated; the honest
claims are the PAIRED identity lists at each step (deterministic machinery,
byte-identical twin runs at every measurement). What IS CI-separated:
nothing between arms of the same instrument — capability growth across the
arc shows up as the accumulating identity lists (15 stall recoveries, 3
descent solves, and the taxonomy shifting from parks to honest terminals).

**Every null and registered deviation, honestly listed:**

- **P1:** While/Raise shipped semantics-only (registered deviation).
- **P2 — the histogram over-predicted:** 56.4% of the corpus IR-emittable
  vs 83.3% predicted; the miss ENUMERATED (kwargs 1173 / slices 524 /
  typed-except 102 sub-construct blockers); emitted-but-not-predicted = 0.
- **P3 — codebook saturation:** 16 quanta vs the registered [40, 220]
  band; 18 merges vs ≥ 30. Measured cause: the 2/3 MDL join is
  family-collapsing at depth-1 grain. (P7-C later showed idiom grain
  escapes the collapse — the band was wrong about GRAIN, not about MDL.)
- **P6 — H6 null:** MAIN − FROZEN = +3.2 pp, CI spans zero; the entire
  delta = 4 spine ids. Proposal mass sat on the enumerator (63/77
  accepts). The battery also SURFACED the 15-task stall defect (12%) —
  diagnosed, not patched in the battery, fixed in the rules at P6.5.
- **P6 — render-closure gap:** 21/77 accepted tasks unrenderable to
  python (Abs/Min/Max/Fold outside the P5 closure); 3 exec disagreements
  = the registered div-by-zero cross-frame divergence. Coverage story,
  not correctness (zero toolchain disagreements where surfaces built).
- **P6.5:** the +9.6 pp aggregate was NOT claimed (CI spans zero); the
  claim was the paired list.
- **P7-A — H7a null at the stratum:** descent converts its cited 3 but
  first-fit hole enumeration overfits weak singleton-derived rows (4 new
  holdout_fails, all caught by held-out rows).
- **P7-B:** la_10 converts; la_11/21/29 PROVEN unreachable at the held
  grains (live-var collisions; parity/const outside the enumerator's
  reach); op-drop exclusion REJECTED as unsound.
- **P7-C:** 2/15 chunks cueable (no paired NL corpus — predicted, then
  measured); corpus idioms (adapter guards) barely overlap the battery
  domain (integer arithmetic).
- **P7-D — all three H7 verdicts are the registered nulls, at power**
  (`PROGRAM_SYNTHESIS_P7D.md`): H7a lower bound .142 vs the .409 bar;
  H7b zero primary conversions, attempts unchanged on 91/92 paired
  accepts (the 92nd is the one chunk-decoy id, +3); H7c +3.2 pp CI-spans-
  zero with the SAME four spine ids as H6 — chunk rung-1 accepts 0,
  descent identical in both arms (mechanism, not content). Capability
  mass remains on the enumerator (78/99 accepts) + the execution-verdict
  layer; the learned layer is a recognition/decoy surface at this
  corpus↔battery pairing.

**The arc's central empirical fact,** consistent from P6 through P7-D:
**"constructions propose, execution decides" is currently carried by the
DECIDE half.** The verdict layer (ProgEval + held-out rows + CEGIS +
fold-up refusal + repair refutation) never miscarried once — every wrong
accept the protocol could catch, it caught; every park became a terminal;
zero toolchain disagreements. The PROPOSE half's learned content has not
yet paid a CI-separated capability premium over the starter shapes + the
enumerator — three measurements now say so (H6, P7-A diagnostic, H7c), and
the cause is localized (content/domain mismatch + trigger grain), not
mysterious.

## 4. Consolidated residual ledger (the named levers, deduped across P4→P7D)

1. **Rust `SynthEnumerate` `exclude` parameter** — within-round candidate
   iteration is contract-blocked for output-valued Lits (P7-B §3); the
   named Rust lever if hole-level iteration is ever needed.
2. **Scalar-loop descent** — the sum_to_n family has no list row, hence no
   derivable hole; out of descent's registered scope. A scalar-recurrence
   hole taxonomy is the lever.
3. **Value-domain widening** — no `Mod`/floor in the kernel (parity ids
   unreachable); consts limited to defaults + spec outputs
   (count_above_ten's 10 unreachable); bool rows give the enumerator no
   purchase (br_13).
4. **Spec comprehension** — 3/125 requests not recognized (declarative /
   "please"-headed / "make"-headed); the cue vocabulary is the boundary.
5. **MBPP-style external probe** — the battery is self-authored; per the
   standing eval-subset rule, an external instrument is the next coverage
   claim (named at P6, still open).
6. **Render closure** — Abs/Min/Max/Fold into the python RenderRule set;
   `Min` into the llvm emitter (the P6 §3 gap heads).
7. **Chunk layer** — mining on a matched-domain corpus; trigger derivation
   needs a paired NL↔code corpus; multi-statement chunk splice order rides
   the P4-B lattice (known residual); containment discounting of nested
   window supports.
8. **Repair** — multi-round oracle instrument (la_11 needs round 2);
   fold-grain localization needs singleton ce rows (a trace-emitting
   ProgEval is the Rust-side alternative); acc-dependent fold bodies are
   invisible to init-pinned derived rows (documented blocker).
9. **P4 leftovers** — guided-search callables not ported; slot binding
   template-verbatim.
10. **LLVM read frontier** — `call` still outside the lift dialect.

## 5. Standing-rules compliance note

- **Power the gate before the endgame:** every capability claim since P6
  is on the 125-task instrument with Wilson CIs; deltas within 3× the
  per-episode step were never claimed; every aggregate that was
  numerically up but CI-overlapping is labelled
  `*_no_measured_gain` in the artifact itself.
- **A baseline is a list:** the artifacts
  (`results/prog_synthesis_battery.json`,
  `results/code_synthesis_baseline.json`, `results/prog_chunk_mine.json`,
  `results/prog_ir_python_coverage.json`) store per-item rows; the gates
  RE-DERIVE every aggregate from them; frozen arms are hash-pinned and
  were never overwritten across three append generations.
- **Synthetic-proven mechanism ≠ benchmark value:** every phase reports
  both, separately (e.g. descent's 3/3 cited conversions AND the H7a
  stratum null; the chunk proposability gate AND the 0-cueing battery
  footprint).
- **Eval-subset coverage is part of every claim:** domain pins (integer /
  list-of-int, scalar out), recognition failures in the denominator, the
  error_handling coincidence declared, the self-authored-battery
  limitation named with the MBPP lever.
- **No silent caps:** N never cut; the toolchain subsample rule is stated
  in the artifact; parks are a gated zero.
- **Protocol boundaries are labelled in the data:** the REPAIR-ORACLE
  arm's rows carry their protocol on every row, with a gate proving no
  primary aggregate includes them.
