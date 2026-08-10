# VALUE-FLOOD CONDITIONS — results

Pre-registration `VISION_VALUE_FLOOD_PREREG.md`, committed **8a0a3980** before
any number. Seeds 81000–81999. Engine **d6097900e8b5**, provenance gate run as
its own step (645 passed). Oracle `scripts/rung7_vision_bench.sh`: **212 passed,
10 skipped, exit 0** — this tree has no BSDS300, the documented no-corpus case.
Border-ownership synthetic gate **9/9**. **The seed was not modified.**

Corpora C1 cartoon (pin `08630d4b…`) and C2 live-action (pin `119eca43…`), pins
asserted at run time. 168 substrate runs = 2 corpora × 3 lattices × 4 `k` × 7
frames. Reported per corpus, never pooled.

---

## THE HEADLINE, IN ONE LINE

**The flood is not the problem. It seeds, it runs, and it halts exactly where a
value flood must — and then 93.4% of everything it finds is thrown away by a
single gate that requires a figure to touch nothing but background.** That gate
is true of synthetic rasters and false of natural scenes, and no change of
threshold, statistic, or extent repairs it — **relaxing the flood makes protos
strictly fewer.**

---

## 0 — THE INSTRUMENT IS ALIVE, AND ITS DEAD ARM ACTUALLY FIRED

| control | result | |
|---|---|---|
| **D1** committed 12×12 figure | 1 proto, 24 members, 7 sweeps | reproduces |
| **D1** per lattice L=16/24/32 | 1 proto; 40/108/176 members = expected | reproduces |
| **D2b** uniform field, frame flags stripped | **1 proto, 144 "members", `n_frame=0`, `reach=0`** | **the trap, fired** |
| **D2c** *same pixels*, frame intact | **0 protos**, `n_frame=44`, `bg_frac=1.0` | separated |

D2b is the blob rung's failure demonstrated **actually failing**: identical
pixels, opposite verdicts, decided entirely by whether the flood was seeded. A
field containing no figure at all mints a proto covering every cell. M1
separates it from every live run by `n_frame` and `reach` jointly.

**A registered prediction was WRONG and is recorded as such.** §3 predicted the
D2 arm would produce a vacuous mint on the *figure* field. It did not
(`n_protos = 0`). With no seed, that field's 0-region and 1-region are two
mutually-adjacent enclosed components and `G_figadj` refuses **both**. The
prediction failed because the mechanism refuses more than anticipated — which
is the first evidence for the finding below, arrived at by being wrong.

**Attribution reconciles: 168/168 rows, `G_pass == n_protos` exactly.** The
read-out is measuring the rule, not a paraphrase of it.

---

## 1 — M1: WHERE THE FLOOD STOPS (P1 CONFIRMED)

`n_frame = 4L − 4` on every run (60 / 92 / 124). The flood is **never
unseeded**.

Mean over 7 frames:

| corpus | L | k | bg_frac | reach | sweeps | enclosed comps |
|---|---|---|---|---|---|---|
| C1 | 16 | 2 | 0.930 | 178 | 28.0 | 4.7 |
| C1 | 16 | 16 | 0.382 | 38 | 10.0 | 96.7 |
| C1 | 32 | 2 | 0.928 | 826 | 59.9 | 8.7 |
| C1 | 32 | 16 | 0.324 | 207 | 27.1 | 294.9 |
| C2 | 16 | 2 | 0.991 | 194 | 30.7 | 1.3 |
| C2 | 16 | 16 | 0.450 | 55 | 18.3 | 71.4 |
| C2 | 32 | 16 | 0.483 | 371 | 55.1 | 209.9 |

**The flood covers 32–99% of the field and gains 38–878 cells beyond its seed.**
It halts partway; it does not fail to start. P1 confirmed.

**At what value difference does it halt?** The frontier gap distribution over
every `bg=1 / bg=0` adjacent pair:

| k | \|Δval\| = 1 | 2 | 3 | ≥4 |
|---|---|---|---|---|
| 2 | **100.0%** | — | — | — |
| 4 | **87.7%** | 11.5% | 0.8% | — |
| 8 | **67.0%** | 19.9% | 9.0% | 4.0% |
| 16 | **54.8%** | 18.0% | 10.4% | 16.8% |

**The flood stops overwhelmingly at the SMALLEST DIFFERENCE THE REPRESENTATION
CAN EXPRESS** — one quantizer level, a difference at the limit of the
observation's own resolution. Minimum frontier gap is 1 at every `k`, which is
forced: the admissibility test is exact equality, so any difference at all
halts it.

---

## 2 — M2: WHICH GATE REFUSES (P2 CONFIRMED, AND IT RESOLVES THE PRIOR GAP)

Over all 168 rows, **12,319 enclosed components**:

| gate | components refused | share |
|---|---|---|
| **G_figadj** — figure touches another non-background region | **11,506** | **93.4%** |
| G_gnd2 — two differently-labelled ground neighbours | 312 | 2.53% |
| G_settled — floods not settled | 0 | 0% |
| **G_pass** → minted | 501 | 4.07% |

At C1/L16/k=16 the split is **96.3 G_figadj vs 0.4 G_gnd2** per frame.

**This resolves the blob rung's unreconciled 80-vs-0.** Its diagnostic measured
`G_gnd2` only and labelled the survivors `n_singly_surrounded` — but `G_gnd2`
is the gate that **almost never fires** (2.53%). The 80 components it called
"singly surrounded" were being refused by the *other* half of gate 5, which it
did not measure. The prior rung's diagnostic was not wrong about what it
computed; it computed the wrong one of two conjoined tests.

---

## 3 — THE THREE-WAY DISCRIMINATION, PLUS THE FOURTH

### (a) Threshold too strict — **REFUTED as stated**

**AST-walk audit** over every rule's term tree (`where` + `effects`), recording
each comparison node's literal operand and the attribute it is compared
against. Every literal in all five rules:

| literal | compared against | nature |
|---|---|---|
| `0.5` ×18 | `bown`, `bg`, `frame`, `owns` | boolean discriminators over 0/1 flags |
| `2` ×1 | `Count(roots)` in `bo_mint_gestalt` | the definition of a bipartition |

**No literal is ever compared against `val`.** There is no hand-set value
threshold in the mechanism; admissibility is exact `Eq` — a *zero*-tolerance
test, not a strict one.

**The §13 finding is real but sits in the ADAPTER, not the seed.** The de facto
tolerance is `k`, the quantizer level, hand-set as `K_LEVELS = (2, 4, 8, 16)`
in the harness. It does not fall out of anything. This rung did not fix it, and
§4 below shows why fixing it alone would not help.

### (c) Structural — **REFUTED by the distributions, not by elimination**

Component extent on the *identical* lattices under equality vs a gradient
criterion (`|Δ| ≤ 1`), mean max-component:

| corpus | L | k | equality max | gradient max | field |
|---|---|---|---|---|---|
| C1 | 32 | 4 | 197.0 | **1023.9** | 1024 |
| C1 | 32 | 8 | 107.4 | **992.6** | 1024 |
| C1 | 32 | 16 | 53.4 | **475.0** | 1024 |
| C2 | 32 | 16 | 113.7 | **824.7** | 1024 |
| C1 | 16 | 16 | 17.0 | 59.6 | 256 |

Adjacent pairs at exactly equal value: 29–50% at k=16. Within one level:
55–78%.

**Natural frames at this grain are not devoid of extended regions — under a
gradient criterion the components span nearly the entire field.** (c) is
refuted by the forcing distributions, as the pre-registration required. "Value
flooding cannot work on natural images" is **not** what the evidence says.

### (b) The statistic is wrong — **SUPPORTED as a diagnosis, REFUTED as the fix**

The prior-art hypothesis is confirmed in its first half: our flood is gated on
value equality, the one family that fails on natural images, while watershed
floods on gradient, mean-shift on feature-space density, graph cuts on pairwise
affinity, SLIC on joint colour-space distance.

But the second half — "the fix is a change of statistic, not of threshold" —
**is refuted by measurement.** A validated simulation (it reproduces the
substrate on **168/168 rows** under the incumbent predicate) re-runs the exact
gate sequence with the admissibility predicate swapped:

| statistic | enclosed comps | G_figadj share | protos | **multi-cell protos** |
|---|---|---|---|---|
| `\|Δ\|=0` (incumbent) | 12,319 | 93.4% | 501 | **234** |
| `\|Δ\|≤1` (one level) | 1,709 | 84.0% | 162 | **78** |
| `\|Δ\|≤2` (looser still) | 427 | 59.0% | 149 | **68** |

**Relaxing the flood makes proto-objects strictly FEWER, monotonically.** The
mechanism trades one failure for another: tight admissibility fragments the
field into thousands of mutually-touching slivers; loose admissibility lets the
background flood **swallow the figures**, leaving nothing enclosed (12,319 →
427 enclosed components). Both ends fail. And `G_figadj` still refuses 84% and
59% of whatever survives.

**P4 was confirmed on component extent and it did not transfer to protos.** The
registered discriminator measured what it promised — gradient components are
3.5–9× larger — and that gain does not reach the output, because the extent was
never the binding constraint.

### (d) Extent — **SUPPORTED, and immaterial**

Registered separately per instruction rather than folded into (a)–(c).
Multi-cell protos over 7 frames at k=16:

| corpus | L=16 | L=24 | L=32 | G_figadj share across L |
|---|---|---|---|---|
| C1 | 0 | 1 | 3 | 99.6% → 99.3% → 98.9% |
| C2 | 1 | 0 | 5 | 99.2% → 98.5% → 98.0% |

Extent moves the output slightly. **It does not touch the failure mode:** the
`G_figadj` share is invariant at 98–99.6% across a 4× change in cell count.
Bigger lattices yield more of everything, in the same proportion.

**P3 confirmed — the incumbent reproduces byte-identically.** At L=16, k=16:
C1 **0 protos / 0 multi-cell**, C2 **2 / 1** — exactly the blob rung's
committed numbers. This is the **fourth** independent reproduction.

---

## 4 — WHAT THE EVIDENCE ACTUALLY SUPPORTS: THE GATE, NOT THE FLOOD

None of the three registered explanations is the answer, and the measurement
names a fifth that no arm was designed to test but every arm converges on.

**`G_figadj` is the blocker.** It refuses 93.4% of enclosed components under the
incumbent statistic, 84% under one-level flooding, 59% under two-level, and
98–99.6% at every extent. It is the only quantity in this rung that does not
move when everything else does.

What it encodes, from the seed's own comment: *"the figure is a hole in ONE
surface."* A component is refused if **any** of its cells touches **any** cell
of **any** other non-background region.

**That is true of a synthetic raster and false of a photograph.** The synthetic
control is a figure on a blank ground, so the gate is satisfied trivially — and
it passes 9/9. A natural scene is a **partition**: objects abut other objects,
and a region whose neighbours are all background is the exception, not the
rule. The gate does not encode objecthood; it encodes *isolation*, and it was
validated only on stimuli where the two coincide.

### The contradiction with this tree's own recorded principle

*"Edges are grounded contours, transitive and decaying, not local flags — a
circle with a bit out isn't a discontinuous circle."*

Both halves of the mechanism violate it, and the gate violates it worse than
the flood:

- The **flood** admits on `Eq(m.val, R.val)` — a single adjacent pair, binary,
  zero-tolerance, no decay. A local flag.
- The **gate** lets **one** touching cell veto an entire component's
  objecthood. A single local disagreement destroys a global grouping — the
  exact inversion of the principle. The circle with a bit out is precisely what
  `G_figadj` throws away.

**The mechanism contradicts the principle, and the contradiction is the
finding.**

### The named replacement, with its derivation — **NOT MEASURED**

The seed cites Zhou/Friedman/von der Heydt 2000, whose signature is that
ownership of an **identical local edge FLIPS with the global figure** —
ownership is *contextual and competitive*. `G_figadj` refuses exactly the case
that border-ownership exists to **decide**. The replacement follows from the
mechanism's own stated basis:

> **A shared boundary is ASSIGNED, not disqualifying.** Where two non-background
> regions abut, ownership of the shared border goes to the side better explained
> as owning it — comparing each side's own perimeter accounted for by that
> border. A tie is HELD OPEN (no proto), reusing the anti-confabulation
> precedent already in `bo_mint_gestalt`'s size tie.

This introduces **no threshold**: it is a comparison between two measured
quantities, and the only constant is the tie, which is equality. §13 is
satisfied by construction rather than by derivation of a constant.

If a flood tolerance is wanted alongside it, the §13-clean value **falls out**
as **one quantizer level** — the smallest difference the observation can
express. Anything finer (exact equality) asserts precision the sampling does
not support, which this tree's own frame/continuum invariant forbids as an MDL
identifiability violation. **But the measurement above says do not make that
change alone: on its own it reduces protos.**

---

## 5 — WHAT I GOT WRONG

- **The registered D2 dead-instrument prediction was wrong.** It predicted a
  vacuous mint on the figure field; `G_figadj` refused both components. A
  uniform field was needed to reproduce the trap. Recorded, not quietly
  replaced.
- **I expected exact equality to be near-vacuous on natural frames** before
  reading the harness. It is not: `k`-level quantization makes 29–50% of
  adjacent pairs exactly equal. The mechanism's tolerance is real and lives in
  the adapter, not the seed.
- **P4 was confirmed and still misled.** The registered discriminator was
  built on the assumption that component extent was the binding constraint. It
  measured a 3.5–9× extent gain that produced *fewer* protos. Registering the
  discriminator did not protect against choosing the wrong quantity to
  discriminate on.

## 6 — RESIDUALS (not fixed here)

- The replacement gate is **named and derived but UNMEASURED**. No claim is
  made for it.
- `k` remains a hand-set adapter magic number (§13), unfixed.
- The counterfactual is a **simulation**, validated against the substrate only
  under the incumbent predicate; the alternative predicates were never run
  through the substrate itself.
- `bo_mint_gestalt` is unreachable on real frames: it requires a 2-component
  bipartition, and enclosed components alone number 4.7–294.9 per frame. It has
  never been exercised outside synthetic stimuli.
- Frames are 7 per corpus per configuration, inherited from the incumbent. No
  CI is claimed on any per-frame mean; the load-bearing numbers here are
  aggregate shares over 12,319 components.
