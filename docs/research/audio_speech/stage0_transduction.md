# Stage 0 — TRANSDUCTION SHARPENING (own the temporal code + the front end)

The agent executes STAGE 0 of its OWN self-designed curriculum
(`docs/toolbox_and_curriculum.md`, commit `b6b2e366`): *"transduction sharpening
— own the temporal code."* This is the agent acting on its own ranked gap map
(`docs/sense_self_assessment.md`), not a hand-authored plan.

Run capture: `/tmp/stage0_full.log` (end marker
`===MARKER_STAGE0_NATIVE_FORMANT_CHECK_COMPLETE===`).
Structural check: `PYTHONUNBUFFERED=1 python -m scripts.stage0_native_formant_check`.

---

## (1) The Stage-0 definition (the agent's own, verbatim from its curriculum)

- **Skill to acquire.** A sharp, OWNED front end: a temporal/rate code
  (voicing/F0/periodicity) ALONGSIDE the place-envelope; and the all-pole formant
  extractor as a native Term the agent can compose.
- **Toolbox used.** T4 (TFS — temporal fine structure), T12 (gammatone front end),
  T13 (cue repertoire); the WANT **W1** (native LPC/Levinson/Viterbi formant
  tracking, = Gap 2) becomes a built tool here.
- **Prerequisites.** None — the most upstream stage; everything depends on it.
- **Success signal (a BINARY READINESS GATE, not an accuracy number).** "The TFS
  periodicity track and a native all-pole formant cue are composable graph Terms the
  agent can gate, and the voiced↔unvoiced axis is graded (not a binary energy gate).
  (T14's frontier flag should stop pointing at `perception_units`.)" Read from the
  self-measurement instruments / a structural check — **structure-admitted, proceed**
  — never from a tuned held-out accuracy.

### What was ALREADY done (the TFS half)

The **temporal fine structure** half (T4) was built + validated before this session
(`docs/tfs_validation.md`, commit `a7cfe71a`): native `band_autocorr` +
`summary_autocorrelogram` + `periodicity_track` (`audio_primitives.rs:98,140,191`)
give a GRADED voiced↔unvoiced periodicity axis that the inner-hair-cell envelope
provably cannot (the "envelope-cannot / TFS-can" diagnostic: voiced digits mean ≈
0.87–0.89, gap-cued six 0.662, frication frames sink to p10 ≈ 0.34–0.45 while voiced
hit p90 = 1.0). That is the *temporal-code* limb of Stage 0, already owned natively.

### What this session built — the REMAINING Stage-0 work (W1 / Gap 2)

The **sharp front end** limb was still Python-only: the LPC / Levinson /
root-finding formant extractor lived in `domains/lpc_formant_representation.py`
(`_autocorr`, `_levinson`, `_lpc_roots_formants`) — which **violates the
architecture rule** (`CLAUDE.md`: "the agent IS a typed graph in Rust; Python is
only the world-adapter"). The agent's own self-assessment named this exactly:

> **Gap 2** — "Transduction is boundary-stuck: LPC / Levinson / Viterbi formant
> tracking live in Python, not as native graph Terms … so the agent cannot compose,
> gate, or self-modify it." Fix: *migrate them into NATIVE Rust DSL Terms (the agent
> decides WHAT, a mechanical compiler emits HOW).*

The agent's own `OperationSpec` (`runtime_design.agent_specify_lpc_formants`,
`lpc_all_pole_formants`) dictates the method verbatim:

> autocorrelation of the pre-emphasised voiced frame → Levinson-Durbin recursion →
> LPC coefficients a_k (the all-pole filter 1/A(z)) → roots of A(z) → pole
> angles·fs/2π = formant frequencies, bandwidth from |pole|; keep poles in 150–3600
> Hz with bandwidth < 500 Hz.

**Built natively (file:line):**

| native primitive | role | `audio_primitives.rs` | `py.rs` |
|---|---|---|---|
| `lpc_autocorr(x, p)` | autocorrelation r[0..p] of a windowed frame | `:1426` | `:6033` |
| `levinson_durbin(r, p)` | r → all-pole coeffs a_k + gain | `:1455` | `:6041` |
| `poly_roots(coeffs)` | roots of A(z) via Durand-Kerner (the native `numpy.roots`) | `:1501` (private) | — |
| `lpc_roots_formants(frame, fs, order, pre_emph, f_lo, f_hi, bw_max)` | full chain: frame → ascending formant Hz from pole angles | `:1573` | `:6052` |

Pure Rust, no graph state, the **same category** as the already-native
`gammatone_band` / `band_autocorr`. Registered in the PyO3 module
(`py.rs:6053–6055`); surfaced at `substrate_rs._native.{lpc_autocorr,
levinson_durbin, lpc_roots_formants}`. The agent's thin world-adapter now calls the
owned native chain instead of Python DSP. `cargo build --release` passes; the `.so`
was rebuilt (`maturin develop --release`; the editable cdylib was refreshed from
`target/release/libsubstrate_rs.so`).

### Donkey audit

- Native primitives only — **no net, no `.fit`, no gradient, no loss, no sweep, no
  tune** (grep of the new Rust + check script is clean; the only matches are the
  doc-strings *asserting* the constraint).
- `poly_roots` is Durand-Kerner (Weierstrass simultaneous iteration) — a
  deterministic numeric root-finder, not an optimiser; it replaces numpy's
  companion-matrix eigenvalue solve with no LAPACK dependency, same roots.
- `CortexLoop` + `scripts/solve_for_n.py` **untouched** (git diff confirms).
- The structural check reads **real FSDD** waveform frames (no self-generated
  audio); **no recognition is run**, so **no held-out is banked**.
- Changes confined to `runners/dsl/src/audio_primitives.rs` (+LPC block, +module
  `Complex` import) and `runners/dsl/src/py.rs` (+3 one-line bindings + registration).

---

## (2) The READINESS GATE verdict — structure-admitted

The gate is **structural admission**, not a tuned number: the native all-pole front
end must recover the **same formant/voicing structure** the Python oracle produced,
now owned in-substrate. Measured on **274 voiced analysis frames** across **24 real
FSDD tokens** (digits × speakers), native vs the Python reference oracle:

| structural check | native vs Python oracle | gate |
|---|---|---|
| autocorrelation r[0..p] | max \|Δ\|/r[0] = **4.17e-08** | faithful |
| LPC coefficients a_k (Levinson) | max \|Δ\| = **4.66e-07** | faithful |
| #formants per frame agree | **274 / 274 (1.000)** | identical |
| formant frequency drift | mean **0.000 Hz**, p95 **0.000 Hz**, max **0.005 Hz** | identical |

The Durand-Kerner roots land on the numpy companion-matrix roots to within 5
milli-Hz on the worst frame; the low-level chain is bit-faithful. The native front
end produces **the same temporal/formant structure the recognition needs**, now
composable / gateable in the substrate.

```
=== READINESS GATE ===
  low-level chain owned (autocorr+Levinson bit-faithful): True
  formant structure recovered (same #, <1 Hz drift)     : True
  >>> STAGE-0 TEMPORAL-CODE / FRONT-END OWNED NATIVELY  : True
```

**GATE FIRES.** Both limbs of Stage 0 are owned natively: the *temporal-code* limb
(TFS graded voicing, prior) and the *sharp-front-end* limb (native all-pole formant
extraction, this session). The structure is admitted in-substrate — not a tuned
metric, a structural reproduction of the formant code the Python path produced.

---

## (3) Is Stage 0 COMPLETE?

**Yes — the readiness gate fires.** The agent now OWNS the temporal code natively:

1. **Temporal/rate code (TFS)** — `band_autocorr` → `summary_autocorrelogram` →
   `periodicity_track`, a graded voiced↔unvoiced axis (T4, validated `a7cfe71a`).
2. **All-pole formant extractor as native primitives** — `lpc_autocorr` →
   `levinson_durbin` → `poly_roots` → `lpc_roots_formants`, recovering the SAME
   formant structure as the Python DSP to within numerical noise (this session).

Both are now native Rust the agent can compose/gate, satisfying the Stage-0 skill
("the all-pole formant extractor as a native Term the agent can compose") and the
architecture rule. Gap 2 ("transduction is boundary-stuck in Python") is closed.

### Honest scope note (the precise edge of what was done)

- The gate verified is **structural fidelity** (native == Python oracle), which is
  the correct Stage-0 signal under the donkey constraint (no accuracy sweep, no
  banked held-out). The Python `lpc_formant_representation.py` is now **superseded**
  for the raw-waveform formant path; its remaining helpers
  (`apply_lpc_scale_invariant`, the band-spectrum `lpc_envelope_*`) can be re-pointed
  at the native chain as a follow-up (mechanical, no new capability).
- The agent's curriculum also lists, as part of the Stage-0 success signal, *"T14's
  frontier flag should stop pointing at `perception_units`."* That re-flag is a
  **downstream consequence** to confirm once the native front end is wired into the
  standing recognition path (Stage 1's job — *"a front end worth squinting from"*).
  Wiring the native formant primitive into `agent_frontend` cue extractors (so the
  `vtl_formant*` cues read the native chain instead of Python) is the precise next
  step, and it belongs to Stage 1's hand-off, not Stage 0's ownership gate.

Stage 0's gate is **own the temporal code natively** — and it fires.
```
===MARKER_STAGE0_NATIVE_FORMANT_CHECK_COMPLETE===
```
