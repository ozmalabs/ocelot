# Capability Suite — Track 5 Results (validity keystones + unified scorecard)

The final track closes the suite: it establishes VALIDITY (the T2/T4 positives are not
surface tricks) and produces the one side-by-side scorecard of substrate vs human vs
published-LLM numbers.

## Part 1 — Potemkin validity keystones (arXiv:2506.21521)

A benchmark shared across systems is only valid if a system cannot pass it by a surface
trick without the underlying capability. The minting analogue of a "potemkin" is a
residual that is PRESENT on the surface every segment (a naive "any residual this
segment → mint" heuristic would fire) but does NOT recur to the readiness threshold —
i.e. no genuine, persistent representational gap.

**Result (`track5_keystones_and_scorecard.py`, exit 0, K1–K5 PASS):**

- **K1 potemkin caught** — on the adversarial battery (threshold unreachable within the
  run) a naive gate would mint 4 predicates (`category, causal_influence, field, name`);
  the real persistence gate mints **0**. The surface-pass is refused.
- **K2 genuine still mints** — on the recurring battery (threshold reachable) the real
  gate mints — so K1 is *discrimination*, not a gate that never fires.
- **K3 discrimination** — the real-minted set is a strict subset of the naive set
  (empty ⊂ {4 surface predicates}); the gate excludes exactly the non-recurring ones.

This is the load-bearing validity check: it shows the T2 fine-grained-fidelity and T4
accommodation-gate positives reflect the persistence-gated capability, not a substrate
that mints on any surface signal.

## Part 2 — The runners: substrate / LLM / human

- **substrate runner** (`runners/substrate_runner.py`) — used by all tracks;
  teacher-free graph reads and `run_minting_train_of_thought`.
- **LLM harness** (`runners/llm_harness.py`) — **OFF by default, teacher-free**. It only
  emits a prompt bundle and reads pasted-back results; it has no network client, no key
  handling, no `requests` import. **K4** verifies `run(enable=False)` contacts nothing
  and `run(enable=True)` without a user-supplied local model *raises* rather than
  silently reaching out. The substrate's minting loop is never fed an LLM.
- **human protocol** (`runners/human_protocol.md`) — the same battery as a written
  protocol (typicality ranking H2; accommodation-readiness H4) with anonymized
  results-entry JSON the scorer reads. The vendored Rosch norm is the default human
  column; fresh subjects are optional.

## Part 3 — The unified scorecard (FLEX CIs)

`scoring/scorecard.py` assembles the one side-by-side view (**K5**):

| metric | substrate | human | LLM (published ref) |
|--------|-----------|-------|---------------------|
| **RQ2** typicality Spearman ρ ↑ | **0.890** (CI [0.888, 0.894]) | 1.0 | decoder ~0.15 · BERT ~0.38 |
| **RQ1** category recoverability AMI ↑ | **1.0** (explicit is-a structure) | 1.0 | ~0.55 (emergent) |
| **RQ3** ℒ objective (coarse→fine) | 2.57 → **4.56** | richer/higher | over-compressed/low |
| **gate F1** (accommodation) ↑ | **1.0** | 1.0 (by construction) | — |

Substrate beats the published BERT typicality bar on RQ2. The RQ1 row carries its
honest caveat inline: the substrate's perfect recovery is *explicit structure*, not the
emergent geometric feat the LLM ~0.55 represents.

## The suite verdict (prove / stretch / measure)

- **Prove** — T4 (accommodation gate: persistent→mint, transient→no-mint,
  duplicate→refused, P=R=1.0) and T5 (potemkin caught) establish the capability is real
  and not a surface trick.
- **Stretch** — T2 (coarse↔fine ρ from ~0 to 0.89) and T3 (ℒ 2.57→4.56) show the
  substrate spans from the LLM over-compression regime to the human detail-preserving
  band, purely by grain.
- **Measure** — the unified scorecard places the substrate's numbers next to the
  published human and LLM values on all three Rubric-A metrics + the Rubric-B gate.

## Honesty commitments (recap)

- All metrics are the published ones (Spearman ρ, AMI/NMI/ARI, ℒ, gate P/R); the scorer
  is pure Python, validated against known values.
- The human baseline is a documented order-faithful reconstruction of Rosch (1975)
  (`fixtures/PROVENANCE.md`); the LLM column is the paper's published reference unless a
  user opts into a fresh, local, teacher-free run.
- The comparison is asymmetric on evidence and says so: the substrate's own numbers are
  fresh in-repo measurements; the LLM numbers are cited from arXiv:2505.17117.
- The saturation limit in T2 (commitment half_width=4) and the structural-vs-emergent
  asymmetry in T1 are stated, not hidden.

## What a newer LLM changes — and the sharper thesis (frontier update, Sept 2026)

The RQ2 reference points (decoder ~0.15, BERT ~0.38) and RQ1 ~0.55 are
**accessible-model, embedding-based snapshots circa 2025** — the paper excludes closed
frontier models (it needs embeddings). A newer model **raises** RQ2 ρ toward the human
ceiling, so "substrate ρ 0.89 beats BERT 0.38" is a **snapshot, not the load-bearing
claim**. This suite is **architecture validation**, not a leaderboard win.

The Sept-2026 frontier makes the point sharper, not weaker. **GPT-6 Astra** (released
Sept 3 2026) scores **99.9% on ARC-AGI-3** and — per ARC Prize's own analysis — does so
by *"turn[ing] unfamiliar environments into compact symbolic world models ... [and
developing] its own domain-specific language shorthand"*, even writing game-specific code
libraries in the PRO-LONG harness. So the honest thesis is **not "LLMs cannot build new
representations"** — frontier models demonstrably do. The thesis is:

> **Their architecture bounds it, and the cost is so many orders of magnitude higher
> that it is different in kind — not a factor-of-N gap.**

Three concrete, sourced distinctions (see `scoring/metrics.LLM_REFERENCE._frontier_2026`):

- **Persistence class.** Astra's new representation lives in the **context window** (notes
  it chooses to keep) or **opaque per-session reasoning state** — it evaporates at session
  end; the weights are frozen. The substrate mints a **persistent `CapabilityAxis` node**
  that survives and is reused. Astra **re-derives per session**; the substrate **accretes**.
  A weight-level new axis still requires retraining.
- **Harness / memory dependence.** Astra's 99.9% uses the **Provider Adapter** harness
  (provider-managed opaque state). Under the **neutral Standard harness** — the
  apples-to-apples condition ARC Prize says a future AGI should solve, and the one closest
  to the substrate's teacher-free, no-hidden-state setting — Astra scores **62.7%**. ARC
  Prize attributes the gap to *memory handling, not raw reasoning*.
- **Cost class (the crux).** Astra's ARC-AGI-3 runs cost **~$19K** (Provider Adapter,
  99.9%) to **~$26K** (Standard, 62.7%) **per benchmark**; ARC Prize prices the human
  brain-energy baseline at **~0.067 cents per game**. The substrate mints a new axis in
  **~55 native graph ops, no GPU** (Track 6). That is many orders of magnitude —
  **different in kind**.

So a bigger model narrows the typicality ρ gap and *matches the substrate on building
representations at all* — but does not change the **persistence** or **cost** class. Those
are the durable, architecture-level results (T3/T4/T6), sharpened by the frontier evidence
rather than refuted by it. (ARC Prize explicitly does **not** claim AGI and notes
ARC-AGI-3 is bounded/closed-ended, not open-ended representational growth.)

## Guardrails

Additive only. `.so` md5 `7efe75eba05b006cafd15dbb4b7da246` frozen; no protected-file
edit; `conceptualizer.py` untouched (audit green); nothing under `/applications`. Files:
`tests/capability/minting/{track5_keystones_and_scorecard.py, runners/llm_harness.py,
runners/human_protocol.md, scoring/scorecard.py}` + this doc.
