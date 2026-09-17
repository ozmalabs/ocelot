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

---

## Update — the path is RESCUED by meta-shape match (sub-experiment (j2))

The path boundary above was **not** the ceiling it looked like. The per-element outlier
read failed on the path because criticality there is not a *within-instance* outlier —
but the felt move that works is *higher-order*: recognise the **whole graph's meta-shape**
and match it against a library of **earned** (exactly-solved-once) exemplars, importing
the exemplar's solution as a **structural-role template**. "This graph feels like a chain
→ a chain's load-bearing nodes are its spine → flag the spine." That is analogical
retrieval against solved exemplars — the same move a person makes recognising a
problem-shape they have seen before — and it is what the earlier read omitted.

Implemented and run in `track_j2_metashape_rescue.py` (exit 0, M1–M4 PASS):

- **M1 — path rescued.** A fresh path (size 7, unseen) matches the chain exemplar
  (meta-shape distance 0), imports its earned `spine` role template, and flags its
  cut-vertices **exactly (F1 = 1.0)** — the case track (j) scored F1 = 0. Fresh star and
  cycle also F1 = 1.0.
- **M2 — felt path solver-free.** Matching a fresh graph makes **0** Tarjan calls; the
  5 exact solves were the one-time **library build** (spy-separated). Feel is cheap;
  the solver only earned the library.
- **M3 — feel-then-verify boundary (near-path decoy).** A chain-plus-one-chord matches
  the chain exemplar only *loosely* — meta-shape distance **6** vs **0** for a clean path
  — and the imported template is genuinely **wrong** there (predicts `{n0,n1,n3,n4}`, truth
  `{n2,n3,n4}`, F1 = 0.57). The elevated match-distance is the built-in "this isn't a
  clean chain, verify me" signal; verification is what corrects it. The prior is lossy by
  design, and the match-distance says when to trust it.
- **M4 — earned, not planted.** Every template's critical-role set was learned by solving
  the exemplar exactly once (auditable in the library: chain→`spine`, star→`hub`,
  clique/cycle→`[]`, tree→`{hub,spine}`); a fresh graph's answer comes from the meta-match
  plus a structural role, never a hand-authored `chain→spine` table (that hand-table is the
  hollow Arm-2 control).

### The ceiling, reframed: coverage, not local-vs-global

Track (j)'s "local-shape-bounded" conclusion was too pessimistic. The real bound is a
**coverage ceiling**: the felt read works for any configuration whose **meta-shape matches
a solved exemplar** — *including* global-criticality cases like the path — and fails only
where the meta-shape matches nothing in the library. Cheap felt priors are not restricted
to local structure; they are restricted to *previously-felt shapes*, which is a much more
favourable and human-like bound (you feel what you have seen the shape of before).

The unmapped-domain **numerology fence still stands**: the exemplars and targets here are
all checkable graphs, so this licenses "meta-shape match imports a known solution across
fresh instances of a solved shape," not "trust a felt read where there is no ground truth
and no solved exemplar."

### Files added for the rescue

`tests/capability/number_qualia/track_j2_metashape_rescue.py` and the
`meta_shape` / `degree_role` / `build_solution_library` / `felt_meta_match` additions to
`runners/number_runner.py`.



---

## Track (j3) — the aperture manifold: "local/global is aperture, not magic"

Track (j2)'s meta-shape library rescued the path, but it was not a *separate* mechanism.
Matching the whole configuration against solved exemplars is the order-4 rung of the
substrate's shape ladder — the **same structural read at a coarser aperture**. This track
collapses the library into the aperture dial the substrate already owns:
`domains.order_n_concepts.nth_order_terms` (the finite-difference machinery
`falling_world` uses to discover an order-2 generator from raw pixels). Order 0 is the
value; each order is one finite-difference pass — a wider aperture over the *same*
structural coordinate. Local vs global was never two kinds of property; it is one read at
two orders.

**Design principle — no single method is chosen.** Every aperture stays *live* as a
parallel coordinate over the structural quantity (degree in traversal order); we read the
shape of the resulting (node × order) manifold — the map of local outliers per order — and
never argmax to one aperture or "switch to calculator k". The property localizes wherever a
bounded-radius outlier appears at *some* aperture; its shape across apertures *is* the
confidence interval.

### What it shows (all five claims PASS; run `track_j3_aperture_manifold.py`)

- **M1 — the path localizes natively (F1 = 1.0), no library.** The path's degree is a flat
  interior band `[1,2,2,2,2,2,1]` at order 0 (the track-(j) failure), but at order 1 the
  finite differences `[1,0,0,0,0,-1]` put the only nonzero entries at the *boundary* and a
  flat zero run through the interior — the interior is a bounded order-1 generator (a ramp),
  and its interior nodes are exactly the cut-vertices. Read across the live apertures, F1 = 1.0.
- **M2 — the same read, a different shape (star, F1 = 1.0).** The hub is an order-0 outlier;
  the identical manifold read flags it with no method switch. Node-local and global
  criticality are two aperture settings of one read.
- **M3 — the felt path is solver-free.** Zero cut-vertex/Tarjan calls across every felt read
  (SolverSpy = 0); the exact solver is only the separate verify step.
- **M4 — honest null on the plain cycle.** No cut vertices exist; the manifold is flat at
  *every* aperture, so the read reports "no separating structure — verify" and manufactures
  no false peak. (Had it committed it would have scored F1 = 0.0 — the abstain is protective.)
- **M5 — the fence, with teeth (anti-Dunning-Kruger).** On a ring+tail the only true
  cut-vertex is the tail's attach point; every ring-interior node *looks* exactly like a
  path interior to any local coordinate (degree 2, a neighbour each side) but is **not**
  critical, because the "way around" is the whole rest of the ring — an **unbounded-radius**
  fact no bounded aperture can see. The felt read would have committed the falsely-sharp peak
  `{y0,y1,y2,y3,y4}` at F1 = 0.33; instead a cheap **confidence gate** detects the blind
  regime (a cycle is present) and **abstains to verify**. The system detects where its own
  local coordinates are blind rather than feeling falsely confident.

### The ceiling, sharpened again: witness radius, not coverage

Track (j2)'s coverage ceiling ("works where the meta-shape matches a solved exemplar")
sharpens to a **witness-radius ceiling**: the felt read recovers any property with a
**bounded-radius witness at some aperture** (a path's global criticality *is* such a
witness — a local order-1 boundary), and **honestly abstains** where the only witness is
**unbounded-radius** (does a large loop close?). Widening the aperture over a local
coordinate crosses many apparent local/global lines but cannot cross that one; there is no
cheaper local coordinate that fixes it, so the honest move is to detect the blind regime and
escalate. The meta-shape "library" was order-4 doing by lookup what order-1 does by finite
difference — one aperture dial, not two mechanisms.

The choice of *which dimension to difference along* (traversal order here) is itself part of
the aperture; for novel structure it must be earned/verified rather than assumed, and an
ordering that makes noise look like a generator is the numerology failure mode. The
unmapped-domain numerology fence therefore still stands: this licenses "one felt read at
multiple live apertures, with an honest abstain where the discriminating structure is
unbounded-radius," not "trust a felt peak wherever it appears."

### Relevance to the manifold-navigation machinery

The substrate's manifold-collapse work (`docs/research/engine_substrate/manifold_collapse.md`,
the combine-all likelihood product, the `jabberwock_reviews_design` "diverse cheap checks
sculpt a manifold" design) builds and collapses a manifold and measures its peakiness, but
its escalation triggers are **scalar** (argmax margin, `mf_stall` plateau, residual salience)
— they say "stuck" without saying "stuck *where*" and do not detect their own blind regime.
This track is a minimal, honest witness that the design's own doc-only claim — *the manifold's
shape says where to look, and a diverse check dissolves a falsely-sharp peak* — is
implementable: a per-dimension flatness read over live apertures plus a confidence gate that
abstains where the checks are jointly blind. Wiring this into `frontier_pick`/the escalation
ladder (feedable via a `set_attr` on frontier salience, no frozen-Rust or tuned-seed changes)
is the identified next stage, not done here.

### Files added

`tests/capability/number_qualia/track_j3_aperture_manifold.py` and the
`aperture_manifold` / `manifold_shape` / `has_cycle` / `felt_aperture_read` / `f1_score`
additions to `runners/number_runner.py`.
