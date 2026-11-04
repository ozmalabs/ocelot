# Doing Science Research on the OCELOT Substrate

OCELOT is not a benchmark-chasing repository; it is an empirical cognitive-science and architecture research program. Every claim in [`CLAUDE.md`](../CLAUDE.md) and [`docs/features/`](features/) is backed by a primary-source **Pre-Registration → Measurement Script → Results** triad archived under [`docs/research/`](research/INDEX.md) (~4,550 documents across 16 research threads).

This guide documents the epistemological principles, experimental lifecycle, instrument-calibration gates, engine-provenance checks, RNG seed accounting, and baseline discipline required to conduct valid science on the `(G, Γ, C)` substrate.

---

## 1. Epistemological Foundation: Goal-Using, Not Goal-Seeking

1. **Benchmarks are targets to aim at, not the purpose of the work.**
   As stated at the top of [`CLAUDE.md`](../CLAUDE.md), a task score or battery number is used in the archery sense—something to aim at so aim can be measured and corrected. Optimizing a benchmark score at the cost of the underlying mechanism is backwards.
2. **Generalization across bodies and problem shapes is the measure of competence.**
   A mechanism that lands in one modality or embodiment and is then independently re-derived or transferred to another (e.g., the `ShapeDecode` dynamic-quantization loop moving across vision, speech, handwriting, spatial navigation, and F-16 / humanoid control) is stronger evidence than fitting a single domain benchmark more tightly.
3. **Report both mechanism proof and benchmark value:**
   - *"Synthetic-proven mechanism ≠ benchmark value; report both."*
   - *"A diagnosed null that localizes the cause and generalizes the lesson is a better outcome than an un-understood pass."* Nulls and retractions are reported as headline findings, never buried or edited out after the fact.
4. **Magic numbers fall OUT of natural processes; they do not go IN ([`VISION_PROTOCOL.md`](../VISION_PROTOCOL.md) §13).**
   Every numeric observation or parameter in an experiment belongs to one of three categories:
   - **Category 1 — Fell out of the mechanism (Evidence):** Fixed by the system's own constraints, dynamic range, noise floor, or information budget (e.g., Weber–Fechner `0.9991` from a log receptor; centre–surround emerging from zero initialization under decorrelation). Survives distribution shift.
   - **Category 2 — Put in as a constant (Fails on distribution shift):** Chosen to make an output look right (e.g., importing a fixed threshold `μ = 0.024` from a paper without importing the gain-control loop that normalized its scale). Never tune a failed constant—tuning is metric surgery wearing a lab coat. Ask what constraint the number should fall out of.
   - **Category 3 — Put in as forced architecture (Silently unfalsifiable, §13.1):** An architecture where each rule is solely responsible for one half of a qualitative signature so the model *cannot fail* to produce that signature. Always ask: **"Could this model have produced the opposite result?"** If no rule could have failed to yield the qualitative signature, reproducing it is a calibration of magnitudes, not an emergent derivation.

---

## 2. The Experimental Lifecycle: `PREREG` → Measure → `RESULTS`

Every empirical investigation follows a strict, prospective three-step workflow:

```
1. Commit *_PREREG.md  ──►  2. Run scripts/<experiment>.py  ──►  3. Commit *_RESULTS.md
   (before looking)            (pinned engine + claimed seeds)       (honest report + stamp)
```

### Step 1: Write and Commit the Pre-Registration (`docs/research/<topic>/*_PREREG.md`)
Before running a confirmatory measurement, commit a `*_PREREG.md` document containing all seven required elements ([`VISION_PROTOCOL.md`](../VISION_PROTOCOL.md) §3):

1. **Two-sided hypothesis:** Predicted directions can invert; always state a two-sided test.
2. **Exact statistic and readout:** Specify the exact metric, aggregation level, and comparison arm.
3. **Sample size `n` fixed in advance by power analysis:**
   - *"Power the gate before the endgame."* Deltas within ~3× the per-episode step (`1/n`) are noise (see the Omniglot Run 15 correction in `CLAUDE.md`, where a 4-alphabet subset hid noise that a powered `n = 400` 10-alphabet gate with Wilson confidence intervals resolved).
   - Restrict pilot power analyses to **already-burned** RNG seeds.
   - State eval-subset coverage explicitly as part of every claim.
4. **Claimed confirmatory RNG seeds (`scripts/seed_claim.py`):**
   - Never reuse pilot RNG seeds for confirmatory runs.
   - Run `python3 scripts/seed_claim.py <lo> <hi>` and paste the emitted `SEED CLAIM <lo>-<hi>: CLEAN` verdict block directly into your `*_PREREG.md` (enforced by `domains/seed_record.py::preregs_missing_claim`).
5. **Explicit decision rule:** State the exact pass/fail thresholds and what a null result establishes.
6. **Exact list of tests (no sweeps, no post-hoc re-runs):**
   - *"Never rescue a failed gate by changing the measure"* (metric surgery, §5). If a failure suggests the readout was wrong, report the failure honestly in `*_RESULTS.md` and open a **new** prospective pre-registration for the new readout.
7. **Advance prediction with provisos:** State what you expect to happen and which assumptions are load-bearing.

---

## 3. Calibrating the Instrument Before Measuring the Agent

**A gate whose measure passes noise—or passes a dead arm—is not a gate ([`VISION_PROTOCOL.md`](../VISION_PROTOCOL.md) §1 & §2).** Before comparing experimental arms, calibrate your measurement instrument against all five checks:

### 3.1 The Five-Clause Instrument Gate (§1)
1. **Random-input floor:** Run the measure on unstructured random noise; it must score at the floor.
2. **Ideal-exemplar ceiling:** Run the measure on a synthetic ideal exemplar of the target structure; it must score near the ceiling.
3. **Learning duration stability (unless duration is your declared IV, §1.2):**
   If you report a single-timepoint score per arm and that score drifts with training duration on the same input, arm comparisons are reading arbitrary points on a transient curve.
   - *Exemption (§1.2, Troxler):* If duration is your **pre-registered independent variable** and all arms span the exact same time-course, comparing the time-courses is valid.
4. **The arms must be ALIVE (§1.1 — "Scores at the floor" is satisfied by death):**
   A guarded division like `(a - b) / (a + b) if (a + b) > 1e-9 else 0.0` returns a flawless `0.0000` floor when a unit **never fires at all**. Always positive-control the arm by reporting how many probe conditions elicit a non-zero response, and avoid unbounded `peak / base` ratios where `base → 0` explodes.
5. **The mechanism must be LOAD-BEARING downstream (§1.5 & §13.2 — the FM-0 vacuity gate):**
   *"Works" and "is load-bearing" are different properties.* A subsystem can reproduce a published signature in isolation while being wired to nothing downstream. Toggle the mechanism on and off and measure:
   $$D = \max |\text{on} - \text{off}|$$
   on every downstream attribute you claim it affects. If `D == 0.0` exactly, the mechanism is decorative—**stop immediately and burn no confirmatory RNG seeds**.

### 3.2 Convergence vs. Exact-Equality Termination (§2 & §2.1)
1. **Check convergence on the formative distribution first:** Checkpoint your structure metric and weight drift $\|\mathbf{w}(t) - \mathbf{w}(t-\Delta)\| / \|\mathbf{w}\|$ out to $\ge 3200$ steps. A rule that never settles or converges to zero structure cannot support developmental or ablation comparisons.
2. **"Converged" $\neq$ "Terminated" (`run_rules` over floats):**
   - `run_rules` terminates on **exact value equality**. Over `float64`, a contraction map whose fixed point lies between two representable floats lands in a period-2 **1–4 ULP dithering orbit** and runs until the iteration cap even though its dynamics have settled to $10^{-16}$.
   - Never infer "did not converge" from "hit the iteration cap"—measure the **amplitude** across single ticks (`~1e-16` = settled dither; `O(1)` = genuine orbit), and never sample a phase-dependent residual on only one phase of a 2-step cycle.
   - When exact cycle termination is needed on a deterministic relaxation, use `TypedGraph::state_fingerprint()` + opt-in `detect_cycles` on `run_rules` (exact state-history equality—no magic $\varepsilon$ tolerance).

---

## 4. Designing World Adapters and Experimental Arms

1. **The Paradigm-Forcing Rule (§0):**
   The Python world adapter supplies **unstructured entropy and a clock** (plus mechanical I/O translation). **The graph makes the structure.** Never pre-compute features or branch on graph state in Python.
2. **Express Ablations as Graph Data:**
   Every experimental condition or lesion (e.g., `bcm=0`, `associative=1`, `saw=0`) must be an attribute on a graph-resident `*Params` or `*Policy` node read by seed rules (via `PickUnique` or absence-tolerant `Count(Filter(...))`), never a Python `if/else` branch in the test harness.
3. **Defaults Preserve Committed Results (§9):**
   Every new mechanism or flag ships **off by default** (or absence-tolerant) so all committed benchmarks and tests reproduce byte-identically.
4. **Statistical Analysis Rules (§4 & §6):**
   - **Unit of analysis is the independent SEED/RUN**, never individual units within a run that share input and compete via winner-take-all (counting coupled units massively inflates false-positive $p$-values).
   - **Test the INTERACTION, not the simple effect**, whenever the no-mechanism control is non-null.
   - **Verify what your control arm actually models (§6):** Pre-registration protects statistics, not experimental design (e.g., dark-reared animals still have spontaneous retinal waves; setting `dark` to "zero input" confounds deprivation with silence).
   - **Positive-control the reader before trusting NL or dataset output (§10.2):** Because `data/` is gitignored, a fresh git worktree without a symlinked `data/` directory can return fluent fallback replies (like `"I am Jabberwock."` on topic queries) or skip corpus tests. Always symlink `data/` (`ln -s <canonical>/data data`) and run a positive control on the reader first.

---

## 5. Engine Provenance and Worktree Isolation

In a multi-agent research codebase where work happens in isolated git worktrees (`.worktrees/...`) and the Rust engine (`substrate_rs`) evolves alongside seeds, **a number without an engine is not a result ([`VISION_PROTOCOL.md`](../VISION_PROTOCOL.md) §10 & §11).**

### 5.1 The Source-Content Invariant (`domains/engine_provenance.py`)
The provenance invariant asks: **Is the loaded `_native.abi3.so` binary a build of THIS tree's Rust source (`runners/dsl/src/**/*.rs` + `Cargo.toml`)?**
- `source_match == "own"`: Built in this tree and up to date with its `.rs` content record (`_native.build.json`).
- `source_match == "shared"`: Symlinked from another tree whose Rust source fingerprint (`rust_source_fingerprint()`) is **byte-identical** to this tree's. Safe and fast when your rung touches no Rust.
- `source_match == "DIVERGED"` or `stale_rust` non-empty: **Loud refusal (`EngineProvenanceError`).** You edited `.rs` files or diverged from the binary's source without rebuilding.

### 5.2 Mandatory Preamble and Result Stamping in Measurement Scripts
Every standalone measurement script under `scripts/` must call `engine_preamble()` **before** importing `substrate_rs`, and must stamp `provenance_stamp()` / `provenance_line()` into its output artifact and `*_RESULTS.md`:

```python
from domains.engine_provenance import engine_preamble, provenance_line, provenance_stamp

# 1. Pin this tree's engine and refuse to measure if DIVERGED or stale:
engine_preamble()

import substrate_rs as srs

# ... run experiment ...

# 2. Stamp provenance into JSON results and print for *_RESULTS.md:
results["engine_provenance"] = provenance_stamp()
print(provenance_line())
# e.g.: engine 95167c01b7b3 @ /path/to/_native.abi3.so [shared build from ... — Rust source identical]
```

### 5.3 Building the Engine Safely (`scripts/engine_build.sh`)
If your experiment modifies any `.rs` file under `runners/dsl/src/`:
```bash
bash scripts/engine_build.sh
# Or for a Python-extension-only rebuild without relinking Rust probe binaries:
bash scripts/engine_build.sh --lib-only
```
- **Never run raw `cp target/release/libsubstrate_rs.so python/substrate_rs/_native.abi3.so`!** In a worktree, `_native.abi3.so` is a symlink to the canonical tree's binary; a plain `cp` writes *through* the symlink and clobbers the canonical engine underneath other running processes (§10.3). `scripts/engine_build.sh` uses `cp --remove-destination` (unlinking first), writes `_native.build.json`, and verifies provenance.
- **Never run `pip install` or unpinned `maturin develop` into global `site-packages`.**

---

## 6. RNG Seed Accounting and the Burned-Seed Ledger

To prevent p-hacking, seed cherry-picking, and accidental overlap between exploratory pilots and confirmatory gates, RNG seed integers are tracked across the repository:

1. **Check a seed range before claiming it (`scripts/seed_claim.py`):**
   ```bash
   python3 scripts/seed_claim.py 90000 90999
   ```
   This scans all ASTs across `scripts/`, `domains/`, `substrate/`, `tools/`, `runners/`, `benchmarks/`, `demos/`, and `tests/` (`scripts/seed_audit.py`) plus the declared table in `VISION_PROTOCOL.md`.
2. **Paste the `SEED CLAIM` verdict into your `*_PREREG.md` and append your block to `VISION_PROTOCOL.md`'s burned-seed ledger.**
3. **Refresh the committed measured-occupancy record (`domains/seed_record.py`):**
   Whenever a commit adds, moves, or removes RNG seed draws in Python code, regenerate the tracked ledger audit artifact:
   ```bash
   python3 -m domains.seed_record --write
   ```
   `tests/test_seed_record_migrated.py` gates that `results/seed_ledger_measured.json` is fresh against the live tree.

---

## 7. Reporting Results and Maintaining the Failure Baseline

### 7.1 Writing `docs/research/<topic>/*_RESULTS.md`
Every completed measurement produces a `*_RESULTS.md` containing:
- **Provenance header:** Output of `provenance_line()`, git commit SHA, environment condition (whether `data/` is linked and optional dependencies are installed), and the **exact test/benchmark selector** used.
  - *Selector discipline (§12):* Prefer an explicit file list or committed shell runner (like `scripts/rung7_vision_bench.sh`) over `pytest -k <substring>`. Substring selectors match unintended tests (e.g., `-k vision` matches `provisional` in `test_meaning_inference_migrated.py`).
- **Pre-registered table filled in verbatim:** Every pre-registered arm, confidence interval, positive/negative control, and interaction test.
- **Scope discipline (§8):** Explicitly state both what the result establishes and what it does **not** establish.

### 7.2 Enumerated Failure Baselines (`scripts/failure_baseline.py`)
**A baseline must be a list of node IDs with diagnoses and last-green commits, never a count (`CLAUDE.md`, `scripts/failure_baseline.py`).**
- A prose claim like *"19 pre-existing failures"* hides regressions when an old failure is fixed and a new one breaks on the same day.
- `results/failure_baseline.json` (gated by `tests/test_failure_baseline_migrated.py`) enumerates every known red node ID, its failure class (`GITIGNORED_DATA_ABSENT`, `OPTIONAL_DEP_UNGUARDED`, etc.), and its per-file diagnosis.
- To verify or update the baseline list:
  ```bash
  python3 scripts/failure_baseline.py verify
  ```
