# VISION — ADVERSARIAL REVIEW (external, no stake)

*Reviewer: Fable 5, 2026-07-17. Fresh worktree, no prior involvement in any rung.*

**PROVENANCE FOR EVERY NUMBER I PRODUCE (PROTOCOL §10/§12).**
Engine `95167c01b7b3` @ `runners/dsl/python/substrate_rs/_native.abi3.so` (copied into this
worktree from the canonical tree; sha256 verified identical — see §4.1 for why that copy was
necessary and why it is itself a finding). Commit `0bd13bab0e`. Selector: explicit 13-file
list, stated in full at §3.1. No seed, rule, default or test was modified.

**SEEDS BURNED BY THIS REVIEW — ledger entry owed (PROTOCOL §11.1: keep both sides).**
**`11000–11019`** — my duty-cycle-matched rung-1a control (§2.1). Taken from the block the
ledger marks FREE. They are now burned; a future rung must not reuse them.

---

## 0. THE THREE MOST SERIOUS PROBLEMS

### 0.1 The three BUILT rungs are all measured in the FFT of the weight matrix — the one frame the arc itself proved is causally inert

Rungs 1, 2 and 4 read **the same complex number** off a Unit's weight matrix.
`domains/cortex_sheet.py:117-124` says so in its own docstring:

> *"the power-weighted circular second moment of the receptive field's Fourier energy …
> This is **EXACTLY the quantity `anisotropy` already returns the MAGNITUDE of** (rung 1/2's
> committed readout). Rung 4 needs the **PHASE** of the same complex number."*

Rungs 1/2 = magnitude. Rung 4 = phase. `map_stats` (`cortex_sheet.py:216-217`) builds the
entire rung-4 statistic from `world.receptive_field(u)` — **no stimulus is ever presented and
no response is ever measured** (verified: `receptive_field` is the only input to the readout).

Then rung 5 presented a stimulus to those same units and measured what came out:
**OSI 0.004 against an ideal Gabor's 1.0000** through the identical frozen probe, with one
unit winning **all 192 probes** (`VISION_PROTOCOL.md:346-352`). Its disclaimer —

> *"This does NOT retract rungs 1/2/4 — their statistics are properties of the WEIGHTS and
> stand as measured"* (`VISION_PROTOCOL.md:353-355`)

— is literally true and is doing enormous rhetorical work. It concedes the point: weight-FFT
anisotropy was only ever interesting as a **proxy** for "this cell is becoming oriented", and
rung 5 severed the proxy from the thing. Then rung 6 built a pathway that **can** express
orientation (ideal split cell **OSI 0.9115**) and found **waves develop nothing in it**:
OSI 0.283 → 0.329 against an untrained floor of **0.3168**, SESOI 0.0595
(`VISION_PROTOCOL.md:404-408`).

**So, plainly, in answer to "in what sense is anything built?":** the ladder's positive results
live in a latent variable of the experimenter's choosing; **every rung that measured a response
found the effect absent there.** Rung 4's headline should read *"a map of weight-spectrum phase
forms from waves alone, in units whose firing expresses none of it."* That is a real and
interesting negative result about a model. It is not an orientation map, and
`VISION_PROTOCOL.md:328` ("Rung 4 — orientation MAP topography: **BUILT**") overstates it.
This is not on the retraction list.

### 0.2 The initialisation is a 494:1 DC prior — and it is rung 5's "root cause", present before any rule fires

`domains/wave_world.py:285` (identically at `onoff_world.py:123`, `dorsal_world.py:103`,
`complex_cells.py:72`):

```python
w = float(w0 * (1.0 + jitter * self.rng.normal()))     # w0=1.0, jitter=0.05
```

Documented as **"NOT structure, just a tie-break"** (`wave_world.py:253-256`). Measured (engine
above):

```
init weights: min=0.8837  max=1.0980   frac(w<0) = 0.0000
DC power fraction = 0.99798        (DC:AC power ratio = 494.3 : 1)
zero-mean init, same shape: DC power fraction = 0.01366
```

**99.8% of every receptive field's initial Fourier power is at DC.** A genuinely entropic
(zero-mean) init has 1.4%. Now read rung 5's central diagnosis:

> *"Root cause, measured: **Oja on nonneg binary input yields strictly-positive weights**
> (`frac(w<0)=0.0000`) ⇒ a DC-dominated response … the oriented structure that IS in the
> weights never reaches the RESPONSE"* (`VISION_PROTOCOL.md:349-352`)

`frac(w<0)=0.0000` **at initialisation, before Oja does anything.** Oja does not *yield* it —
the adapter hands it over, on the exact mode (DC) rung 5 identifies as the killer, and Oja
merely has no force to leave it. The honest statement is *"the init sits on the DC attractor
and the rule cannot escape it"*, which relocates the cause from the learning rule to the
adapter. This matters because **rung 6's entire ON/OFF architecture exists to escape a
condition the initialisation helped create**, and the connection is stated nowhere.

**No init ablation exists anywhere in the arc** (searched `VISION_*.md`, `scripts/*.py`,
`wave_world.py` for zero-mean/init variation — nothing). A zero-mean init is a one-character
change (`w0=0.0`) and is the cheapest unrun test in the tree. This is thesis 2 exactly:
non-negative weights were smuggled in *because pixels are*, then diagnosed as biology.

### 0.3 Rung 2 — the ladder's second BUILT rung — has no code, no data, and no engine hash

```
$ git show --stat e5deb7c28c        # "*** THE EXPERIENCE RUNG IS BUILT ***"
 VISION_RUNG2_PREREG.md | 57 ++++++++++++++++++++++
 1 file changed, 57 insertions(+)
```

Fifty-seven lines of markdown. No runner, no per-seed values, no log. Verified further:

- `ls scripts/ | grep -i rung2` → nothing.
- `grep -rl sutured --include=*.py .` → **only `scripts/ground_vision_science.py`** (the prose-
  seed grounder, not a runner). No Python in this repository has ever run a `sutured` arm.
- `results/` holds `rung4_*`, `r3b_*`, `rung6_*`, `calib_*` — and **nothing for rungs 1, 2, 3
  or 5**.

Compare `git show --stat cef7bf89f1` (rung 4): `results/rung4_confirm.json` (378 lines, all 70
per-seed values) + `rung4_confirm.log`. Rung 4 did it right.

So `VISION_PROTOCOL.md:301-303` cites `normal 0.402 > dark 0.363 > sutured 0.216, both
p<0.0001` as **BUILT**, and that claim is **unreproducible and unauditable from this tree**.
By the arc's own §10 — *"A number without an engine is not a result"* — it is not a result.
Worse, §10's audit asserts *"rungs 1/2/4/5/6 are unaffected … their measurement scripts pinned
the repo engine by preamble"* (`VISION_PROTOCOL.md:202-205`). **For rung 2 that sentence has no
referent** — there is no script to have pinned anything.

---

## 1. WHICH SURVIVING CLAIMS DO NOT SURVIVE ME

| claim | verdict |
|---|---|
| **Rung 4 "orientation MAP topography: BUILT"** (`PROTOCOL:328`) | **Overstated, not wrong.** The interaction −6.91 [−7.46,−6.37] is real, pre-registered, graph-data-ablated, tightly paired, per-seed data committed — **the best-earned result in the arc**. But it is a map of weight-spectrum phase (§0.1), and on a regression of their own `results/rung4_confirm.json` the within-arm slope d~selectivity is −52.7°/unit (r=−0.471), so the +0.0445 selectivity gap predicts **−2.35° ≈ 34% of the interaction**. Their own cross-seed r=−0.081 argues *against* that mediation, so the ambiguity is genuine and they say so (`RUNG4_PREREG:305-311`). Earned share ≈ 4.5° of the naive 20.16 ≈ **23%**. |
| **Rung 2 "experience refines: BUILT"** (`PROTOCOL:301`) | **Not established in this tree.** §0.3. Additionally `sutured` = i.i.d. uniform noise, but lid suture delivers **blurred natural input**, whose leading PC is an oriented low-frequency blob — and the pass's whole mechanism is *"Oja converges to the leading PC; noise has no structure"* (`RUNG2_PREREG:1216-1221`). Under the stated mechanism blur would **not** dissolve structure. This is §6's exact error ("`dark` was set to 'no input'"), one arm over. The arm→biology table is stated but never checked against the research, which is what §6 requires. |
| **Rung 2's "a stable fixed point, NOTHING ELSE"** (`RUNG2_PREREG:1279-1285`) | **False.** Attempt 10 changed four things at once: rule → Oja (`:1133`), homeostasis gated **off** (`:1141`), phase 1 200→**1600** steps (`:1198`), phase 2 200→**400** (`:1205`). |
| **Rung 1's cited headline "0.195 vs 0.000, same RNG"** (`PROTOCOL:299`) | **The gate is confounded; the claim survives anyway — I ran the missing control.** See §2.1. |
| **Rung 1's pre-registered +0.0532 interaction** (`RUNG1_PREREG:103`) | **Orphaned.** It was measured on the **fixed-sign Butts rule**, which the project *itself later proved has no fixed point* — drift 0.49–0.75, decaying *through* the random floor, transient peak **0.345 @ 200 steps** (`RUNG2_PREREG:1071-1082`). All four cells (0.343/0.276/0.322/0.308) sit on that crest. `PROTOCOL:44-46` says this invalidates arm comparisons — but that verdict was applied to rung 2's attempts and **never back-applied to rung 1's own pre-reg**. No retraction is appended; it has never been re-run under Oja; `PROTOCOL:299` quietly drops it. |
| **The arc's own conclusion** (`VISION_DEVELOPMENT_ARC.md:656`) | **Still asserts the retracted claim.** "Where this leaves it" reads: *"a tabula-rasa agent … **grows** a codebook whose kept kernels are center-surround and oriented (**biology rediscovered**)"* — the exact sentence retracted at `:39` and `:44-86` of the same file. A reader who reads the conclusion gets the retracted claim. |

---

## 2. WHAT GENUINELY SURVIVES — including one thing I strengthened

### 2.1 Rung 1a survives a control it never had (and the gate as written cannot support it)

The "paradigm gate" (`tests/test_vision_waves_migrated.py:70-94`) claims both arms get *"the
SAME unstructured entropy … identical seed."* **That is false past the first ignition.**
`WaveWorld.ignite` (`wave_world.py:109-118`) draws `rested[rng.integers(0, len(rested))]`, and
`len(rested)` is arm-dependent because `wv_refract`/`wv_recover` are **not** gated on
`propagate`. Instrumented (engine above):

```
wave  rested-pool at each ignition: [256, 195,  92, 181, 207, 138, 143, 188]
noise rested-pool at each ignition: [256, 255, 255, 255, 255, 255, 255, 255]
identical? False        duty-cycle ratio wave/noise: 82.7x
```

The arms share an RNG *stream*; they realise **different** ignition sequences. And the noise arm
runs at **0.0008** mean activity — ~0.2 active cells per 256-cell frame, where a distance-1
correlation is near-undefined (a lone active cell can never co-occur with a neighbour). So
`0.195 vs 0.000` conflates *"propagation makes correlation"* with *"propagation makes
activity"*. The test's own assertion `mv_wave.mean() > 10 * mv_noise.mean()` (`:87`)
**requires** the arms be unmatched — it hard-codes the confound as a pass condition. It is also
n=1, threshold-asserted (`c_wave > 0.05`), no seeds, no CI, no permutation.

**So I ran the duty-cycle-matched control.** Unstructured ignition at `propagate=0`, ignite_k
swept to match the wave arm's activity, then powered over 20 paired seeds (**11000–11019**,
free block, now burned):

```
n=20 paired seeds
waves          corr@1  mean +0.1951  SD 0.0089   activity 0.0676
duty-matched   corr@1  mean -0.0030  SD 0.0040   activity 0.0601
PAIRED DELTA   +0.1981   95% CI [+0.1931, +0.2031]   p < 5e-5 (sign-flip, 20k)
```

**Rung 1a is EARNED.** At matched duty cycle the correlation is manufactured by the propagation
rule and by nothing else. This is now properly controlled and properly powered, which it was
not before. **Keep it — and replace the gate with this comparison.**

### 2.2 What else is genuinely earned

- **Rung 4's design discipline** — anatomy share (65.7%) **called in advance**
  (`RUNG4_PREREG:160-166`), interaction (not simple effect) pre-committed, ablation is real
  graph data (`MapParams.lateral`, default 0.0, gated in the rule's `where` — no Python branch,
  verified), per-seed data committed. This is the model for the rest.
- **Every stop-at-the-gate.** Rung 5 (missing rectification, probe-period aliasing, and
  `oja=0` is not a freeze — weights moved by up to **47.9** per probe); rung 3B (probe training
  on its own stimulus, step-0 floor 0.111→0.339); the calibration reframe (RPI unbounded,
  `blank` = **1.6×10⁶** vs an ideal Gabor's **6.94**). Each was caught on burned seeds
  **before** any confirmatory seed was spent. **This is the arc's real product.**
- **The calibration reframe's §12.3** — measured, seed 0: `waves: θ=[49.10 48.97 48.40 …]`
  vs `blank: θ=[48.96 49.04 48.19 …]`. **Waves and no input at all place the reference in the
  same place, to ~0.5%.** This is the sharpest single finding in the arc and it points *against*
  the creator's thesis 1 (§5).
- **Rung 6's real finding** — *"the THRESHOLD, not the split, is what makes the response
  signed"* (ideal split-Gabor OSI **0.0006** → **0.9115** on the same weights). Not in the
  design; found by measurement.
- **The Rust floor.** `runners/dsl/src/vision_primitives.rs` is clean and scipy-byte-parity.
- **Rung 3B's self-refutation** — the author's own first reading ("the attractor is the initial
  condition") was measured and killed by its author. That is the behaviour the PROTOCOL exists
  to produce.

---

## 3. WHERE COMPUTE IS STILL SMUGGLED IN (thesis 2)

Beyond §0.2 (the DC init — the big one):

### 3.1 `min_contrast` is dead code, and its "scale-aware" defence is vacuous

`vision_corpus.preprocess_patches` (`domains/vision_corpus.py:136-138`) divides every patch by
its L2 norm. So `Patch.vals` is **a unit vector, always**. Measured:

```
n=2000 patches, scales drawn over [0.1, 50]:
magnitude min/max/mean = 0.9999998 / 1.0000001 / 1.0
fraction passing  Magnitude > min_contrast(0.35)  =  1.000
```

- **`min_contrast: 0.35` (`seeds/vision_growth.json:18`) passes 100% of patches, forever.** The
  guard cannot fail. Its comment claims it stops "blank sky becoming a receptive field"
  (`:22`) — that job is actually done by `min_std=0.04`, a **hand-set numpy threshold in the
  adapter** (`vision_corpus.py:96,131`), three modules upstream.
- **`novelty_threshold: 0.55` (`:17`) is not scale-aware either.** The seed defends it as
  *"scale-aware, so it does not fire merely because a patch is bright"* (`:22`, `:31`). Since
  |x|=1 and Oja drives ‖w‖→1, the test reduces to a **hand-set absolute cosine threshold**,
  `max_k |cos(w_k,x)| < 0.55`. The adapter removed all scale before the rule ever saw it. This
  and `max_kernels: 24.0` alone determine how many receptive fields exist. Neither is grown.

This is a §1-class defect (a gate that cannot fail) sitting **inside the seed built to repair
the Stage-1 retraction**.

### 3.2 The wave's propagation is half Python

`wv_propagate` only sets `state="recruited"` (`seeds/vision_waves.json:186-192`). The
transition that makes a wave **advance** is a Python conditional over graph state
(`wave_world.py:203-206`):

```python
for n in self.cells.values():
    if self.s.node(n)["attrs"].get("state") == "recruited":
        self.s.set_attr(n, "state", "active")
```

That sets wave velocity to exactly 1 hop/step — a biological quantity — and it is the other
half of the mechanism producing rung 1's only structural claim (which I just re-earned in
§2.1). Defended as "mechanical double-buffering"; under CLAUDE.md's hard-NO list it is an
`if`/`else` reading graph state and mutating graph state, i.e. a rule.

Same file, `wave_world.py:237`: `on = (at.get("state")=="active") or (at.get("driven")==1.0)`
— **"two pathways, one output", the seed's central architectural claim, is an `or` in the
adapter.**

And `vision_curriculum.py:112-120` retracts the designed pool with a Python conditional over
graph state performing a structural mutation, re-running on **every lesson** (`:129`).

### 3.3 Rung 3's null is over-determined — the delays are frozen

`dv_oja_learn` updates **`weight` only** (`seeds/vision_dorsal.json:546-1110`). `delay` is
written once by the adapter (`dorsal_world.py:106`) and by no rule, ever. But the arc's own
calibration exemplar puts the direction-selective structure **in the delays**
(`dorsal_world.py:132-166`: `delay = max_delay - proj`), and its docstring concedes that
re-weighting random delays is "weak — only the ~1-in-4 synapses whose random delay happens to
land on the line can be kept" (`:144-147`).

That concession never reaches the conclusion. **No arm could grow a delay gradient**, so the
causal claim *"Oja's fixed point is the average and the average has no direction"* is
**confounded with a structural fact about non-plastic wiring**. A null was guaranteed. Yet it
is taught to the agent as settled (`seeds/vision_science.json:151-155`,
`vision_the_average_has_no_direction`). Also hand-matched and never swept: `max_delay=3`
against `rf=7` (half-extent 3) at `speed=1.0` px/step — the single triple at which a delay line
could work at all.

### 3.4 Smaller, real

- **`target_sum: 49.0`** (`vision_waves.json:24`) = `rf² × w0` = 7×7×1.0 — adapter geometry
  hard-coded into graph data. Change `rf` and the homeostatic target is silently wrong.
- **`oo_wmax: 2.0`** with `w0=1.0` (`vision_onoff.json:23`) ⇒ the subtractive rule's stable
  states are exactly `{0, 2·w0}`. **The saturation bound is the init scale**, and Miller
  segregation's outcome is fully determined by that ratio.
- **L0's input has no temporal structure at all.** `episode_crops` draws an **independent random
  crop per frame** (`vision_corpus.py:201-204`). The "developmental television" stream is IID
  crops — the ecological ordering the Stage-2 framing rests on is destroyed in the adapter.
- **OSI is measured at one hand-picked spatial frequency** (`complex_cells.py:94`,
  `period=4.0`, matched to the ideal Gabor at `:257-266` and pinned globally at
  `rung6_lib.py:29`). Never swept. A unit whose RF peaked elsewhere reads low OSI for an
  **instrumental** reason — and low OSI is rung 5's headline.
- **`_spectral_moment` zero-pads a 7×7 RF to a 16×16 FFT** (`cortex_sheet.py:118,132`) — `n=16`
  is an unexamined readout choice under **every** number in rungs 1, 2 and 4.
- **`step_ms: 250.0` is inert** — no rule reads it. The "~1 s window" is `window_steps=2` and a
  comment.
- **`runners/dsl/python/substrate_rs/vision.py`** (924 lines: `lgn_pair`/`dog`/`v1_bank`/
  `oja_update` — hand-designed DoG + a numpy learning rule) is still in the tree. `onoff_world.py:22-46`
  correctly rejects it as the bolt-on error. It remains a live footgun.

---

## 4. THE PROTOCOL AGAINST ITSELF

### 4.1 §10 and §11 are in direct contradiction, and the gate that should catch it fails everywhere

§10's fix: *"a `site-packages/substrate_rs.pth` points at `runners/dsl/python`, so **every**
process … resolves to the ONE artifact in this tree. A copy goes stale; a pointer cannot."*
§11's rule 1: *"One agent, one worktree."*

The `.pth` holds an **absolute path into the canonical tree**:

```
$ cat .../site-packages/substrate_rs.pth
/home/matt/ozma/internal/research/experiments/gamma-substrate/runners/dsl/python
```

So in **every** worktree — the isolation §11 mandates — `import substrate_rs` silently resolves
to **another tree's binary**. Verified in this worktree:

```
$ pytest tests/test_engine_provenance_migrated.py
FAILED test_loaded_engine_is_the_repo_artifact
  loaded: /home/matt/ozma/internal/research/experiments/gamma-substrate/.../_native.abi3.so
  expect: /home/matt/ozma/internal/.claude/worktrees/agent-.../.../_native.abi3.so
1 failed, 3 passed
```

Consequences, all live:

1. **A worktree agent that edits Rust and rebuilds in its own worktree still measures the
   canonical tree's binary under `pytest`** — silently. That is precisely §10's hazard,
   re-created by §11.
2. **Whoever rebuilds the canonical tree silently repoints every concurrent worktree
   mid-run** — §11.2's "never mutate global install state" is now *unavoidable*, because the
   `.pth` **is** global install state pointing at a mutable shared artifact.
3. **§10 rule 2 ("rebuild in place, let the `.pth` do the resolving") is unfollowable** under
   §11: in a worktree, "in place" is the worktree, which the `.pth` does not resolve.
4. **The gate is worse than absent: it fails in EVERY worktree, for a benign reason, while
   3 of its 4 tests pass** — including `test_exactly_one_native_artifact_is_resolvable`, which
   cheerfully reports "one engine, fine." A gate that is permanently red under the mandated
   setup will be waived as expected noise. That is how it stops being a gate.

Two live agents (rung 7 lateral inhibition; the eye) are in worktrees **right now**. If either
touches Rust, this bites them silently.

### 4.2 The `-k vision` fix did not fix the baseline — I produced a seventh number

§12 blames the six baselines on `-k` substring matching and §10 blames the binary. I ran the
**explicit 13-file list** on the **verified-fresh engine** at `0bd13bab0e`:

```
tests/test_vision_{calibration,complex,curriculum,dorsal,floor,graph_eye,growth,
  hierarchy_and_learning,kernels,maps,migrated,onoff,waves}*.py

=> 122 passed, 11 skipped, 0 failed   (105s)
```

**122/0** — which §10 and §12 both list as one of the *wrong* baselines. The supervisor's
"honest 93 passed / 0 failed on named files" is an **eighth**. The real variance driver is
neither the binary nor `-k`: it is that **no document anywhere states the canonical file
list**, so "named files" names nothing. §12 demands "its engine, its commit, and its
selector" — and then never writes the selector down. **Until the selector is a committed
artifact (a pytest marker or a file list in the PROTOCOL), the baseline will keep drifting.**

### 4.3 The vision suite cannot test the vision claims in a fresh worktree

Of the 11 skips, **10 are the corpus gates**:

```
SKIPPED [5] tests/test_vision_growth_migrated.py — BSDS300 corpus absent (data/vision_curriculum/BSDS300)
SKIPPED [5] tests/test_vision_curriculum_migrated.py — BSDS300 corpus absent
```

`data/` is gitignored. So the arc records *"Gates: `test_vision_growth_migrated.py` **7/7**"*
and *"`test_vision_curriculum_migrated.py` **5/5**"* (`ARC:114,121`), but in any fresh
worktree — the setup §11 **mandates** — they are **2/7 and 0/5**. The claimed
donkey=0 self-run curriculum deliverable is gated by tests that run on exactly one machine.
This is a further, unnamed source of the baseline spread: **the number depends on whether
`data/` happens to exist.**

### 4.4 Is any current gate vacuous? Yes — two

- **`test_no_python_thresholds_in_vision_floor_rules_or_adapter`**
  (`tests/test_vision_floor_migrated.py:376-429`) is **structurally unable to fail on its own
  headline claim.** Its docstring leads with *"no numeric literal may appear in a rule's
  `where` clause"* — then `:427` filters findings to `"vision_world.py numeric comparison"`
  only, so **category (a), the rule-literal check, is a print statement**. It also scans exactly
  **two files** (`seeds/vision_floor.json`, `domains/vision_world.py`) — i.e. **none** of
  `vision_waves/growth/maps/dorsal/onoff.json`, `wave_world.py`, `cortex_sheet.py`,
  `vision_curriculum.py`: every file that does the actual work, and every file in §3 above.
  And its regex (`\b(if|elif|while)\b[^:]*?(>=|<=|==|!=|>|<)\s*(-?\d+\.?\d*)`) cannot see numpy
  masks — so `WaveWorld.drive`'s **median split**, the arc's own named culprit for rung 1c's
  broken video arm (`ARC:406-410`), is invisible to it.
- **The `min_contrast` guard** (§3.1) — a gate that passes 100% of inputs.

### 4.5 Smaller protocol slips

- **`p = 0.0000`** (`RUNG4_PREREG:231-232`, `RUNG3B_PREREG:429-430`) is not a p-value the test
  can produce: `sign_flip_p` returns `(count+1)/(n_perm+1) ≥ 1/20001 = 5.0e-5`. Should read
  `p < 5e-5`.
- **Rungs 1/2/4 carry no engine hash** — mandated by §10 rule 1. `grep -i engine` returns
  nothing in `VISION_RUNG1_PREREG.md`, `VISION_RUNG4_PREREG.md`, or `results/rung4_confirm.log`.
  Only 3B and the calibration reframe comply.
- **`seeds/vision_waves.json` ships `oja_eta = 0.002`** — the value `RUNG2_PREREG:1153-1154`
  documents as **diverging to NaN**. Every result depends on a script-side override to 5e-4.
  §9 is satisfied only because `oja=0`. A live foot-gun.
- **Rung 4's duration calibration ran on `lateral=0` only** (`rung4_calibrate.py:124-138`;
  `RUNG4_PREREG:94`). So *"both arms are run at the plateau"* (`:101-102`) is verified for the
  ablated arm only — and `lateral=1` makes ~5 units learn per step instead of 1, so the arms
  differ in effective learning events per unit. Anisotropy is still **rising** in both arms at
  3200 (0.318→0.337; 0.280→0.292) — still moving on the quantity that drives *d*.
- **Rung 4's readout was calibrated only at ideal-Gabor selectivity 0.87** and deployed at
  **0.29–0.33** (`check_b`/`check_e` use hand-built θ lists, never receptive fields). The one
  regime the pre-reg itself calls noisy is the one never calibrated.
- **Rung 4's random-input calibration is near-tautological**: `rung4_calibrate.py:94-106` draws
  i.i.d. θ and compares `map_smoothness` to `shuffled_null` **of the same values** — d=0 in
  expectation **by construction**. It verifies the null is unbiased; it cannot see the
  selectivity or duration confounds.

---

## 5. IS THE REASONING SOUND WHERE IT ISN'T MEASURED?

### 5.1 Rung 3B: the evidence does NOT support "the attractor is the first coherent motion it ever saw"

The claim rests on preferred-direction agreement: `untrained→dark` **0.412**, `dark→normal`
**0.812**, chance 0.125 (`RUNG3B_PREREG:488-492`). The argument: 0.412 kills the
initial-condition reading; 0.812 across two unrelated phase-2 inputs isolates shared phase 1.

**The 0.412 is uninterpretable, and it is load-bearing.** The `untrained` arm's DSI is
**0.1049** — the floor (`:443`). A unit at floor DSI is *essentially unselective*, so its
"preferred direction" is a **noisy argmax over 8 bins**. Low agreement with `dark` is therefore
exactly what you would see **if training moved nothing at all** and the untrained readout were
simply unreliable. The inference *"training moves 59% of units OFF their innate preference"*
(`:490`) requires a **test–retest reliability of the untrained readout** — re-probe the same
untrained units and measure agreement with themselves. That ceiling was never measured. If it
is ~0.4, the entire diagnostic says nothing.

**And the decisive control is missing.** `dark` and `normal` share phase 1 **and** the innate
delays — both co-vary with the seed, so 0.812 cannot separate them. The disambiguator is cheap
and unrun: **same innate delays, different phase-1 wave seed.** If agreement stays ~0.8, phase-1
*content* is not the attractor and the story is wrong. As it stands the headline —
*"THE ATTRACTOR IS THE FIRST COHERENT MOTION THE UNIT EVER SAW"* (`:501`) — is **one
under-determined inference replacing another**, in the very section that (rightly, and to its
great credit) retracts the author's previous inference for being unmeasured.

Note this compounds with §3.3: delays are frozen, so "direction" may not be reachable by any
arm regardless.

### 5.2 The `x_OFF = 1 − x_ON` degeneracy is the arc's best piece of reasoning

Rung 6: the complementary split is a one-way definition, so `C_ON,OFF(d) = −C_ON,ON(d)`
identically and the channels carry **no independent correlation structure**
(`PROTOCOL:415-421`). The calibration reframe then found the *same* identity pins `E[act]` to
`Σw⁻` regardless of input, making the reference input-independent (§12.3). **One structural
fact, two consequences, both measured.** This is sound and should be built on.

### 5.3 The creator's theses, judged on the evidence

**Thesis 1 ("no view from nowhere; waves calibrate a fixed point, they don't teach content") —
CONTRADICTED by the only measurement anyone made of it.** §12.3: waves and **blank** place θ in
the same place to ~0.5%. An input whose *fundamental purpose* is calibrating a fixed point
should not be replaceable by no input at all. The reframe's author found this, reported it
against their own hypothesis, and stopped. **That is the correct outcome and it should not be
softened.** Caveat honestly: n=1 seed, one layer, and the degeneracy may be an artifact of
`x_OFF=1−x_ON` rather than of the thesis. Fix the split, then re-ask — but the thesis currently
has **zero** supporting measurements and one contradicting one.

**Thesis 2 ("anything not built on an eye smuggles in compute assumptions; it's far too easy to
build a slightly better image processor") — VINDICATED, and more sharply than the arc knows.**
§0.2 (a 494:1 DC prior called "a tie-break"), §3.1 (scale-invariance manufactured in numpy then
credited to the rule), §3.2 (wave velocity as a Python `if`), §3.3 (frozen delays making a null
inevitable), §0.1 (orientation defined in the experimenter's FFT). The arc's own seed already
says it: *"Every rung of my vision that works is Oja plus winner-take-all plus lateral
interaction … my graph is merely HOSTING it"* (`vision_science.json:97`). **The sharpening: the
hosted connectionist model is itself running on adapter-supplied structure.** The thesis is
right, and the arc is currently an instance of what it warns against.

**Thesis 3 ("a genuine eye implementation that works is deliverable and valuable by itself") —
UNTESTED, and the most defensible thing on the table.** Nothing in the arc bears on it either
way. Given §0.1 (three rungs measuring a latent nobody responds to) and §4.3 (the corpus gates
don't run), an eye that produces a *response* — something with an output you can measure without
choosing a frame — would be the first artefact here that could be wrong in public. See §7.

---

## 6. THE HONEST STATE, IN FIVE SENTENCES

1. **The graph demonstrably manufactures spatial structure from unstructured entropy** — waves
   corr@1 **+0.1951** vs a duty-cycle-matched unstructured control's **−0.0030**, paired delta
   **+0.1981** [+0.1931,+0.2031], p<5e-5, n=20 (my control, §2.1; the arc's own version of this
   gate was confounded 82.7× in duty cycle and its "same RNG" claim is false).
2. **Nothing above that has been shown to develop**: rungs 1/2/4's positive results are all
   properties of the **FFT of the weight matrix**, rung 5 showed those weights produce
   **OSI 0.004** against an ideal Gabor's 1.000 in the actual response, and rung 6 — the one
   pathway that *can* express orientation (ideal 0.9115) — found waves develop **nothing** in it
   (0.283→0.329 vs a 0.3168 floor).
3. **Rung 4 is the one well-earned experiment** (interaction −6.91 [−7.46,−6.37], pre-registered,
   graph-data ablation, per-seed data committed, the 65.7% anatomy share called in advance),
   with ~34% of it plausibly readout cleanliness — while **rung 2, the other "BUILT" rung, has
   no code, no data and no engine hash in the tree**, and its `sutured`=white-noise arm does not
   correspond to lid suture under its own stated mechanism.
4. **A substantial part of what the arc attributes to biology was supplied by the adapter** — a
   **494:1 DC prior** at init (documented as "just a tie-break") that *is* rung 5's "root cause"
   before any rule fires; a `min_contrast` guard that passes 100% of inputs because numpy
   normalised them three modules upstream; wave velocity as a Python `if`; and frozen delays
   that made rung 3's null structurally inevitable.
5. **The arc's real and considerable product is its instrument discipline** — five rungs stopped
   at a calibration gate *before* spending a confirmatory seed (RPI scoring no-input 1.6×10⁶ vs
   an ideal Gabor's 6.94; `oja=0` not being a freeze; a probe training on its own stimulus), and
   the sharpest thing it found is that **waves and no input at all place the reference in the
   same place to ~0.5%**, which contradicts the calibration thesis it was built to support.

---

## 7. WHAT TO DO, AND WHAT TO ABANDON

### Do — in this order

1. **Ablate the initialisation (§0.2). One character, highest information per unit of work in
   the tree.** `w0=1.0 → 0.0` (zero-mean, jitter-only). If a zero-mean init changes rung 5's
   `frac(w<0)=0.0000` / OSI 0.004, then **the last three rungs were solving an adapter bug**,
   and rung 6's ON/OFF architecture may be unnecessary. If it does not, rung 5's diagnosis is
   genuinely about the rule and rung 6 stands on firm ground. **Either answer is worth more
   than rung 7.** This must be pre-registered and it must run **before** the lateral-inhibition
   agent's result can be interpreted.
2. **Restate rung 4's claim in the frame it was measured in**, and put rungs 1/2/4's
   weight-frame scope on the retraction list. Not a retraction of the statistics — a correction
   of what they are statistics *of*.
3. **Either reproduce rung 2 with a committed script + per-seed data + engine hash, or move it
   to NOT BUILT.** It cannot stay on the ladder as it is. Fix `sutured` to blurred natural
   input (its own mechanism predicts blur will **not** dissolve structure — a real falsifier).
4. **Fix the §10/§11 contradiction structurally** (§4.1): a per-worktree `.pth`, or a
   `conftest.py` that inserts the tree's own `runners/dsl/python` before anything else, or make
   the provenance gate skip-with-a-loud-reason outside the canonical tree. It must not be
   permanently red.
5. **Commit the selector** (§4.2) — a `vision` pytest marker, registered in `pytest.ini`, and
   the baseline stated as `engine + commit + marker`. Then state the number **once**.
6. **Un-gitignore or vendor a small BSDS subset** so the L0 gates run in a worktree (§4.3), or
   demote "7/7"/"5/5" to "7/7 on the author's machine."
7. **Rung 3B's missing control** (§5.1): same delays, different phase-1 wave seed; plus a
   test–retest of the untrained readout. Cheap; decides whether the headline is real.

### Abandon

- **The weight-anisotropy readout as a proxy for development.** Rung 5 severed it; §0.1 makes
  it unrecoverable. Any future rung must measure a **response** through a frozen probe. This is
  thesis 2's operational form: *if your measure reads the weights, you are grading your own
  homework in a frame you chose.*
- **Rung 3 in its current wiring.** Frozen delays make the hypothesis unreachable (§3.3);
  retract `vision_the_average_has_no_direction` from `vision_science.json` — the agent is being
  taught a confounded conclusion as a fact.
- **`runners/dsl/python/substrate_rs/vision.py`.** Delete it. It is the bolt-on the paradigm
  rejects, sitting in the tree as a live import.
- **Ordered-vs-shuffled as a temporal gate.** Three attempts, ~15+ comparisons, one honest
  self-diagnosed forking-paths garden (`ARC:555-564`). The arc already knows.

### The single highest-value recommendation

**Ablate the initialisation before anything else runs.** A 494:1 DC prior is the largest
unexamined structure in the stack; it sits on precisely the mode rung 5 identified as fatal; it
is documented as "NOT structure"; no ablation of it exists anywhere in the arc; and it is one
character. Three rungs of architecture (5's blocker, 6's ON/OFF split, and the two agents live
right now) are built on the assumption that non-negative weights are forced by the rule and the
input. **They are handed over at init.** Until that is measured, rung 7 is being built on an
unexamined premise — and this arc's own history is that unexamined premises survive six
adversarial attempts and then turn out to have been one shared design error.

---

*Reviewed against `VISION_PROTOCOL.md` §§1–12, all nine pre-registrations and their OUTCOMEs,
`VISION_DEVELOPMENT_ARC.md`, `VISION_PRIOR_ART.md`, `VISION_JABBERWOCK_REVIEW.md`, the six
vision seeds, four adapters, and the migrated gates. Every number above carries the engine and
commit stated at the head. Seeds 11000–11019 burned (§2.1) — ledger entry owed.*
