# TWO AETIOLOGIES, TWO CURES — results (block 365000)

Pre-registration: `APERTURE_AETIOLOGY_CROSSOVER_PREREG.md`, committed before any measurement
(`891cf5f`), with erratum (`901bcb5`) and design addendum (`2249ef4`) both also committed before the
run. Base sha `19a446465c`. Measure: `scripts/aperture_aetiology_measure.py` →
`results/aperture_aetiology/results.json`. Engine built from the measuring tree's own source
(`build_is_stale → []`).

`results/*` is gitignored save a narrow allowlist, so that JSON is **not tracked** — the tree's
convention (marshmallow, psychosis) is that the document carries the numbers and the script
regenerates them. Every figure below is transcribed from a single run of
`scripts/aperture_aetiology_measure.py`, and the arms are deterministic, so re-running reproduces
them exactly. `tests/test_aperture_aetiology_crossover_migrated.py` (7/7) re-derives the cells from
the engine rather than reading any stored file, which is what actually protects the result from
drifting.

**Headline: the crossover holds, diagonally, on every registered cell — and the mechanism is not a
strength effect. Grounding at nearly 8× the standing evidence level does nothing to a frame-locked
belief, while removing the frame corrects it at the standing level.**

## The 2×2

`committed_final` per member (a, b). Standing truthful evidence `w_ext = 0.4` in every arm at every
tick; GROUNDING raises one member to `1.5`; REFRAMING retracts the shared frame and leaves `w_ext`
at `0.4`.

| | NONE | GROUNDING | REFRAMING |
|---|---|---|---|
| **CONFIRMER** | W,W | **R,R** | W,W |
| **FRAME** | W,W | W,W | **R,R** |

Matches the registered prediction in every cell. `abg_channel_open` reads `1.0` throughout the
CONFIRMER arms and `0.0` throughout the FRAME arms until reframing, where it flips to `1.0` —
the mechanism is visible in the graph, not inferred from the outcome.

## What is actually new here, and what is not

Reporting this as "a 2×2 came out as predicted" would overstate it. Honest accounting:

* **CONFIRMER/GROUNDING → R,R** — a **replication** of P8/P6, declared as such in prereg §1.
* **FRAME/GROUNDING → W,W** — a **replication** of `APERTURE_PATHOLOGIES.md` §5, declared in §1, now
  with a belief dynamic attached rather than a bare decode.
* **CONFIRMER/REFRAMING → W,W** — **analytically inert, and the weakest cell in the table.** There is
  no frame in the CONFIRMER arm, so retraction is a no-op by construction and `W,W` follows from the
  setup. Its only content is that the harness did not cure the arm by some unintended route. It is
  not evidence for anything and is not counted as such.
* **FRAME/REFRAMING → R,R** — the **confirmatory cell**, never measured before, and only possible
  because `af_retract_when_every_party_accepts` was built for it.

So: one genuinely new cell, plus three controls that give it teeth. That is a smaller claim than the
table's shape suggests, and it is the right size of claim.

## Gates

**G-crossover — PASS.** Diagonal; both off-diagonal cells `W,W`.

**G-not-just-strength — PASS, and this is the sharp one.** `FRAME/GROUNDING@3.0` → `W,W`. At `w_ext
= 3.0`, **7.5× the standing evidence and double the strength P8 measured escaping in 5 ticks**, the
frame-locked belief does not move off `basin_w`. A precision gate divides; this zeroes. Had the
aperture gate merely been a second attenuator, enough strength would have overcome it — it does not,
at any strength, because the multiplicand is zero.

**G-gate-is-load-bearing — PASS, more strongly than registered.** With the bridge seed absent:
`FRAME/NONE(no-gate)` → **R,R** and `FRAME/GROUNDING(no-gate)` → **R,R**. The prereg predicted the
control would recover *under grounding*; in fact it recovers with **no intervention at all**,
because weak standing friction alone corrects a belief that has no confirmer (P8's own P4a). Same
fixture, same evidence, same everything — remove one rule and the delusion evaporates. Reported as
exceeding the registered prediction rather than quietly folded into it.

**G-byte-identity — PASS by construction.** `abg_gate_observation` matches on `holds_belief`; the
no-gate arms could not even *add* that edge, because Γ rejected it with the seed's production
absent. The control was enforced by the admissibility grammar rather than by discipline.

## An unregistered observation, offered as exploratory only

The two locked states are **distinguishable from the trajectory alone**, which was not predicted and
is not gated:

| arm | `belief_final` | `conf_final` |
|---|---|---|
| CONFIRMER/NONE | **3.86** | 5.00 |
| FRAME/NONE | **4.00** | 5.00 |

`basin_w = 4.0`. The confidence-locked belief sits *off* the basin centre — held there by evidence
it is receiving and discounting, a `1/(1+conf)`-attenuated but non-zero pull. The frame-locked
belief sits *exactly at* the centre, because its reality channel contributes precisely zero and only
self-grounding acts. **Aetiology is readable from where the belief rests relative to its attractor.**
One fixture, no CI, no replication — a hypothesis for someone to register, not a result.

Also worth noting: `FRAME/REFRAMING` ends at `conf 4.75` with `persistence_W 0.45`, i.e. it escapes
*late* and is still shedding confidence at the last tick, whereas `CONFIRMER/GROUNDING` reaches
`persistence_W 0.15`. Reframing at standing evidence is a slower cure than strong grounding — which
is unsurprising, and is stated so the two are not read as equally brisk.

## Honest bounds

Everything registered in prereg §7 stands and is not softened by the pass. One three-relation world;
apertures hand-set and nothing mints one; one scalar belief over two basins whose **update form is
AUTHORED** — this inherits `SUBSTRATE_DISORDER_MAP.md`'s standing T1 asterisk in full, and the
crossover does not discharge it. Deterministic arms, n=1 by construction, no cohort and therefore no
CI: this is a mechanism demonstration, not an effect-size estimate. **Nothing here is a claim about
human dyads and nothing is clinically validated.**

The load-bearing caveat specific to this result: the FRAME arm's members have no confirmer channel,
so the two aetiologies differ in more than the one factor the table's rows suggest. That was
declared in the addendum before the run rather than discovered here, and it is why outcomes are
reported per member — but a fully matched design (a confirmer channel present and equal in both
arms) would be a stronger experiment than this one, and has not been run.

## What this changes

`SUBSTRATE_DISORDER_MAP.md`'s second folie-à-deux row was added on two diagonal measurements taken
in different harnesses. It now rests on one crossover in one architecture with three controls, and
the distinguishing prediction it makes — *grounding is not the treatment for this one* — is measured
rather than argued. The claim that survives is narrow and specific: **in this substrate there are
two mechanically distinct ways for two agents to share a delusion, they respond to opposite
interventions, and the difference is not a matter of degree.**
