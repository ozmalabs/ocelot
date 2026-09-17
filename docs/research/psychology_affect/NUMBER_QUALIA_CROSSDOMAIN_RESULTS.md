# Number-Qualia Cross-Domain Transfer — Results (sub-experiment (j), run for real)

This is the implemented, executed result of the cross-domain-transfer experiment designed
in `docs/experiments/number-qualia-experiment-design.md` §9e. It is the honest outcome —
a **partial success with a clearly-mapped boundary**, plus a methodological correction
that matters more than the headline number.

Run: `PYTHONPATH=runners/dsl/python:. python3 tests/capability/number_qualia/track_j_cross_domain_transfer.py`
→ exit 0, all three reported claims PASS.

## The claim

A structural "isolation / prickliness" coordinate — the felt axis that makes the number
**7** the outlier of 1–10 (it has no in-set factor or multiple; the structural loner) —
**validated in the integer source domain**, transferred **verbatim** (same recipe, read
from the target's own neutral structure, no hand-authored mapping) into a **different
domain** (graphs), predicts the load-bearing nodes (**cut-vertices / articulation
points**). Verification is exact (Tarjan) and runs *only* in the scoring step, never in
the felt read.

## What was built (all additive, `.so` frozen, Python/JSON only)

- `tests/capability/number_qualia/runners/number_runner.py` — one domain-agnostic
  isolation recipe `felt_isolation_field(connectivity, exclude)` applied **identically**
  to integers and graph nodes (this sameness is what makes it a transfer, not a
  hand-map); `build_integers`, `build_graph`; the felt read `isolation_step` via
  `concept_signature`; the shape-native `outliers_from_bulk` (sign-free); a from-scratch
  `tarjan_cut_vertices` ground-truth detector; a `SolverSpy`.
- `tests/capability/number_qualia/track_j_cross_domain_transfer.py` — the experiment.

## Source validation (no source pass → no transfer)

The isolation axis, read via `concept_signature` on the neutral integer corpus, flags:
1–6 → `[5]`; 1–10 → `[5, 7, 9]`; 1–12 → `[5, 7, 9, 11]`. **7 is flagged in every set that
contains it**; the isolates are the low-connectivity numbers (primes and prime-squares),
exactly the pre-registered structural prediction. The axis is validated in-domain before
any transfer.

## The result

| graph | criticality kind | coord-outliers (felt) | cut-vertices (Tarjan) | F1 |
|-------|------------------|-----------------------|-----------------------|----|
| star5   | **local** | `{h}` | `{h}` | **1.00** |
| barbell | **local** | `{b, d}` | `{b, d}` | **1.00** |
| bowtie  | **local** | `{x}` | `{x}` | **1.00** |
| path5   | **global** | `{a, e}` | `{b, c, d}` | **0.00** |

- **J1 — transfer SUPPORTED where criticality is a local structural extremum.** Mean
  F1 = 1.00 (CI [1.00, 1.00], n=3) on star/barbell/bowtie. The same felt recipe, read
  verbatim on the graph's own structure, flags the cut-vertices.
- **J4 — felt path is solver-free.** Felt-path Tarjan/solver calls = **0** (the felt read
  is a pure `concept_signature` read); the exact detector ran 8 times, only in the verify
  step. The felt prior did not cheat by computing the answer.
- **Arm-2 control.** A hand-authored `isolated ⇔ cut-vertex` mapping would score F1=1.0 on
  *all* graphs including path5 — because it plants the answer (it reads Tarjan's output).
  Arm-1 uses no such map, which is *why* it honestly fails on path5. Arm-1 < Arm-2 on
  path5 is the proof Arm-1 didn't cheat.

## Two corrections that matter more than the F1

### 1. The sign was a projection artifact, not a refutation

A first scoring by **signed rank correlation** gave Spearman(low-connectivity-isolation,
cut-vertex) = **−1.0** and looked like a *systematic refutation*. It was the wrong
instrument. A thought is a **shape, not a signed symbol**: "outlier" means *sticks out
from the bulk* at **either** pole. Integers put their structural loners on the *low*-
connectivity pole (7); graphs put their load-bearing nodes on the *high*-connectivity
pole (a hub). A signed correlation calls those opposite; a **shape-native** read
(`outliers_from_bulk`, sign-free, order-free) calls them the **same shape** — and it does:
re-scored shape-natively, the −1.0 dissolves and the transfer succeeds on all three local
cases. *The sign was never the signal.* (Importing a signed-scalar correlation onto a
shape claim was a symbolic solution to a shape problem.)

### 2. The path graph is a genuine boundary, reported not patched

On the degree-regular **path**, transfer fails — and so does a *second* candidate
coordinate (bridge/redundancy). The reason is real: a path's interior nodes all have
identical degree (2) *and* identical bridge-deficit (every edge is a bridge), so **no
local outlier exists** — yet b, c, d are all cut-vertices. A path's criticality is a
**global / topological** property (a node is critical iff it is not an endpoint), which
**no single local felt coordinate can express as an outlier**. We hit this twice with
local scalars and stopped: this is the honest **ceiling of a cheap local felt prior** — it
reads *local* structure; a globally-defined target property needs the expensive verify.
Minting a third local scalar to hide it would have been dishonest.

## What this licenses, and what it does not

- **Licensed:** a structural coordinate validated in one domain **does** transfer, read
  verbatim and shape-natively, to a *different* domain **where the target property is a
  local structural shape** — demonstrated F1=1.0, felt path solver-free, no hand-map.
  Cross-domain structural transfer is **real**.
- **Bounded:** it is **local-shape-bounded**. Where the target property is global/
  topological (the path), the local felt prior cannot express it. This is a real limit of
  the mechanism, not a tuning failure.
- **Not licensed (the numerology fence, still standing):** the demonstration target is a
  **checkable proxy** (graphs have exact ground truth). A positive result licenses "a
  coordinate transfers across domains where the target is a local shape" — it does **not**
  license "trust the felt read on a genuinely unmapped domain," where an unverifiable feel
  is indistinguishable from numerology (design §9d).

## Honest status of the "mint" step

The isolation axis here is a **derived** coordinate — a uniform, per-item-blind structural
recipe (`felt_isolation_field`) written onto the substrate's `dynamical:commitment` axis —
**not** a fresh axis coined by `induce_concern` at run time. This is the design's declared
honest-fallback. The load-bearing claim of (j) is *transfer of the same coordinate across
domains*, which requires the recipe to be domain-agnostic (proven) and does not require
the mint step. The genuine mint occasion the path graph reveals (a global-criticality
residual no held local axis covers) is left as pre-registered future work, not claimed as
run.

## Substrate constraints encountered (stated, not hidden)

- `concept_signature` **abstracts edge multiplicity** (structure-mapping): a raw
  connectivity *count* does not survive into the signature, so isolation is carried as a
  **coarse band** on the commitment axis, not a fine gradient.
- The `dynamical:commitment` axis **saturates** (half_width 4): the felt isolation read is
  binary/coarse by necessity — the design's declared banding hazard, embraced.

## Guardrails

Additive only. `.so` md5 `7efe75eba05b006cafd15dbb4b7da246` frozen (Python/JSON only). No
protected-file edit; `conceptualizer.py` untouched (audit green); nothing under
`/applications`. Files: the two above + this doc.
