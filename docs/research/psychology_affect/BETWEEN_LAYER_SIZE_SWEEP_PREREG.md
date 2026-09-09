# Between-layer function across scale — CPU size sweep — PREREG

**Block**: 308000

**Task**: The user — *"do it on the CPU — it is fine at this scale."* CPU
lifts the 6 GB GPU ceiling, letting the between-layer extraction (block 307000)
run across a SIZE SWEEP. This registers the test: **is the between-layer
FUNCTION a stable structure across model scale?**

Models (Qwen3 family, same architecture + tokenizer, only size varies — a
controlled within-family sweep, cleaner than mixing architectures):
- Qwen3-0.6B (28 layers), Qwen3-1.7B (28), Qwen3-4B (36). All local HF
  safetensors under `/applications`, run on CPU (fp32).

(gemma-3 was intended as a cross-architecture point but this account is not on
Google's HF access list — 403 — so the sweep is within the Qwen3 family.)

## 1. What is measured

Per model, on the same 10-prompt factual/relational battery (block 307000):
- **resolution depth** = the layer at which the answer first becomes the
  logit-lens top prediction, expressed as a FRACTION of the stack (so 28- and
  36-layer models are comparable).
- **delta-growth** = median ratio `||Δ_last|| / ||Δ_first||` — how much more
  work late layers do than early ones.
- **per-relation resolution ordering** — which relation types (capital, isa,
  antonym, morphology) resolve earliest → latest.

## 2. Falsifiable claims

1. **Fractional resolution band is scale-invariant**: across 0.6B/1.7B/4B, the
   answer resolves in the same mid-late FRACTIONAL band of the stack (not a
   fixed absolute layer), and delta-growth is large at every size. I.e. the
   SHAPE of the between-layer function — most committing work late, as a
   fraction of depth — is stable across scale.
2. **Per-relation ordering is scale-invariant**: the ordering of relation
   types by resolution depth (e.g. category-membership before specific factual
   recall) is the same across sizes. (Registered as a SEPARATE claim precisely
   so it can fail independently of claim 1 — the neat ordering seen at 1.7B
   alone must be re-tested.)

## 3. Anti-faking / method

- Identical battery, readout, device (CPU), dtype (fp32) across all models —
  only the model size varies.
- Resolution depth as a FRACTION of the stack, so different layer counts are
  comparable (an absolute-layer comparison would be meaningless).
- Held-out answer used only to rank where the model itself produced it.
- Both claims reported with their measured outcome; a failing claim (esp.
  claim 2) reported as failing, not hidden.
- **default == today**: reuses block-307000's external-venv torch tooling
  (lazy import); the substrate `.so` md5 stays
  `7efe75eba05b006cafd15dbb4b7da246`; protected CAN-internals / toolbox
  untouched; models + venv under `/applications`, NOT committed.

## 4. Honest bounds

- ONE model family (Qwen3), 3 sizes — a within-family scale sweep, not a
  cross-architecture law. gemma inaccessible (gated).
- CPU, fp32; a small 10-prompt demonstration battery — the per-relation
  orderings are indicative, not population statistics (n=1–3 prompts per
  relation).
- Logit lens is a known-imperfect probe (calibrated for the final layer);
  the resolution depths are qualitative trajectory markers.
