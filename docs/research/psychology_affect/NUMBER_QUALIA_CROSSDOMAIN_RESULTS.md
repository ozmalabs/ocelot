# Number-Qualia Cross-Domain Transfer — Results (sub-experiment (j), run for real)

This is the implemented, executed result of the cross-domain-transfer experiment designed
in `docs/experiments/number-qualia-experiment-design.md` §9e. It is the honest outcome —
a **partial success with a clearly-mapped boundary**, plus a methodological correction
that matters more than the headline number.

Run: `PYTHONPATH=runners/dsl/python:. python3 tests/capability/number_qualia/track_j_cross_domain_transfer.py`
→ exit 0, all three reported claims PASS.

## Arc summary — from a felt read to a self-growing thought pipeline

This file grew across a seven-commit arc that turned the number-qualia felt read into a
self-extending "intelligence" pipeline. In order (each builds on the last, all
python/JSON over the frozen `.so`, decisions live in graph Terms, feel-then-verify
throughout, donkey=0):

1. **`56e4468c` — aperture manifold** (`track_j3`). "Local/global is aperture, not magic":
   a property the node-local read missed (a path's global criticality) localizes natively
   via `order_n_concepts` finite differences at a coarser aperture. One read, many live
   apertures, no single method chosen.
2. **`3109ca33` — wire the confidence gate into the frontier** (the intermediate,
   *less-honest* form: a Python-stamped `blind*1e9` scalar mask). Superseded next.
3. **`e336cb2e` — anti-shapes / signed shape field.** An AntiShape is a Shape like any
   other with negative polarity (native `dynamical:valence`). The match/net-sign is a
   *composed Term* (L1 shape-distance = `Sum(Abs(Minus))`), not a scalar. Fool me once:
   verify catching a false commit mints a negative-valence shape; can't get fooled again.
4. **`f68b1dec` — retire the hardcoded `has_cycle` veto.** Blindness becomes entirely
   *learned* (an earned anti-shape), not a hand-coded special case.
5. **`c8e20119` — rescue-by-reading before distrust.** "Wrong is usually the wrong
   *reading*, not an untrustworthy shape": a caught failure is triaged for a verified
   rescuing reading first; the anti-shape is the last resort.
6. **`97428cf8` — cycle detection triggers the cyclic reading.** A cycle is *detected*
   (2-core peel) and *triggers a different approach* (read it the cyclic way) rather than
   being distrusted — detection as a reading *selector*, categorically unlike the retired
   veto.
7. **`949c4e83` — repertoire self-extension.** On a *repeated* no-rescue class the pipeline
   *authors a new reading composed from held primitives*, verify-gated and per-class
   (no regression), flipping the class from distrusted to rescued. It learns not just
   *what* it can't read but *how* to read it.

**The resulting cascade** (cheapest layer first, each firing only when the prior doesn't
suffice): detect structure → read it the right way → if caught wrong, search for a rescuing
reading → if a no-rescue class *repeats*, author a new reading from held primitives → only a
genuinely unreadable structure is held as earned, aperture-scoped, re-earnable distrust.
Trust and distrust are one geometry (a signed shape field read by one Term); the repertoire
grows itself. The honest ceiling that remains: the authorable primitives are graph-structural,
so cross-domain self-extension (authoring readings over non-graph coordinates) is the next
frontier.

**Cross-domain self-extension (`track_j4`) — the loop is domain-general.** The frontier the
arc named is now demonstrated: the recognise → compose-from-held-primitives → verify → adopt
loop is not a graph trick. `track_j4_cross_domain_self_extension.py` instantiates the *identical*
loop over **numeric sequences** (the number-qualia integer axis) and shows only the primitive
vocabulary changes, not the machinery. The felt read is a sequence's "degree" — the order k at
which its k-th finite difference is constant (falling_world's move) — via the **same**
`order_n_concepts.nth_order_terms` aperture dial that drives the graph felt read; verify is exact
differencing. Polynomial sequences (constant..cubic) get the correct felt degree solver-free
(S1); a geometric sequence's felt read **abstains** — the sequence-domain no-rescue class, the
analogue of the barbell (S2); on a **repeat** the loop **authors** a `log_degree` reading from
held numeric primitives (log + the finite-difference dial — a geometric sequence is degree-1 in
log space), verify-gated, and rescues the geometric class (S3) — the exact analogue of `bridge`
rescuing the barbell, in a different domain; the authored reading is per-class and does **not**
mis-read polynomials (S4, no regression); and felt reads stay solver-free with verify the separate
step (S5, clean feel-then-verify accounting cross-domain). The cross-domain map:

| domain   | coordinate         | felt read (cheap)            | verify (exact)      | authored reading (held prims)      |
|----------|--------------------|------------------------------|---------------------|------------------------------------|
| graph    | degree in order    | aperture-manifold outliers   | Tarjan cut-vertices | `bridge` (cycle_core + bridge edge)|
| sequence | values in index    | constant finite-diff order   | exact differencing  | `log_degree` (log + finite-diff)   |

The machinery — felt read via one shared aperture dial, abstain as no-rescue, repeated-no-rescue →
author from held primitives, verify-gated, regression-free — is identical across the two. Added
`seq_felt_degree` / `seq_verify_degree` / `seq_read_log_degree` / `seq_verify_then_update` /
`seq_extend_repertoire` (+ `_SEQ_AUTHORABLE` / `_SEQ_REPERTOIRE`) to `number_runner.py`, and
`track_j4_cross_domain_self_extension.py`. This closes the arc's honest ceiling: the pipeline
grows readings not just within graphs but across domains, by recombining each domain's held
primitives under the one feel-then-verify loop.

**Domain as a first-class object (`track_j5`) — the decision spine written once.** track_j4 argued
the loop is domain-general by hand-instantiating it twice; `track_j5_domain_registry.py` *factors
it out*. The shared control-flow **spine** (solver-free felt read → verify + score → confirmed /
caught-wrong → search the repertoire for a verify-confirmed rescuing reading → first-hit distrust
vs repeat → author from held primitives → verify-gated adopt) is written **once** as
`domain_verify_then_update(domain, obj, ...)`, driven by a lightweight `Domain` dataclass supplying
the four pieces the spine needs (coordinate extractor, solver-free default read, exact verify,
authorable readings) plus a scorer and a live repertoire. The graph and sequence domains are
registered as `GRAPH_DOMAIN` / `SEQUENCE_DOMAIN` built from the *existing* functions (no logic
duplicated). A genuinely **new third domain** — `RESIDUE_DOMAIN` (residue-run partition over
integer lists: feel parity-runs, verify mod-3 runs, author a `mod_k_runs` reading composed from
the held modulus + run-boundary primitives) — plugs into the same loop with **no new loop code**,
only a registration. Claims (all pass, run by author): E1 graph reproduced through the generic
loop (path confirmed, barbell rescued); E2 sequence reproduced (polynomial confirmed, geometric
abstain→repeat→author `log_degree`); E3 the new residue domain plugs in with no new loop code
(confirmed / no-rescue→repeat→author `mod3_runs`); E4 felt reads solver-free (SolverSpy=0), verify
the separate step; E5 the generic loop's `(reason, reading)` **matches** the existing hand-written
loops on both a **confirmed** path (graph path-7, sequence n²) and a **rescue** path (graph barbell
→ `(rescued_by_reading, spanned_k0)` in both loops; sequence 2ⁿ repeat → `log_degree` in both).

Scope stated honestly: the generic loop reproduces the shared **decision spine**, not the graph
loop's substrate **side-effects** — Shape-node minting, the `field_valence<0` repel, and held-state
repeat-detection stay in `verify_then_update`; the generic loop takes the first-vs-repeat
distinction as an explicit `prior_no_rescue` flag (the memory backend owns that state) and uses a
deliberately coarser reason vocabulary (a first no-rescue reports `abstained`, not
`no_rescue_minted_antishape`). The two existing loops and every function the tracks call are
untouched — track_j3 (5/5) and track_j4 (5/5) still pass. The conceptualizer audit stays green: the
`Domain` layer is pure Python plumbing over the identical felt-read/verify structure and relocates
no decision into Python (the graph shape-field decision remains the composed `net_valence_term`
graph Term). Added `Domain` / `domain_verify_then_update` + `GRAPH_DOMAIN` / `SEQUENCE_DOMAIN` /
`RESIDUE_DOMAIN` registrations to `number_runner.py`, and `track_j5_domain_registry.py`. The
pipeline's growth loop is now written once and open to any domain that supplies the four pieces.

**Attempted next unification — memory backend — BLOCKED (honest negative result).** The natural
follow-on was to make the fool-me-once / re-earnable signed-shape-field *memory* domain-general
too (currently the graph loop derives first-vs-repeat from held `Shape` nodes via `_held_shape_for`
+ `net_valence_term`, while sequence/residue fake it with a caller-supplied `prior_no_rescue` flag).
The mechanism *architecture* works and is sound: the memory helpers (`domain_mint` /
`domain_held_shape` / `domain_net_valence`) are domain-general, the match stays the composed
`net_valence_term` graph Term (audit-green, no decision moved to Python), behavior-preservation
holds on graph (barbell anti-shape repels a fresh barbell at −1.0 but does NOT falsely repel path7
or star6, both 0.0), and first-vs-repeat becomes genuinely state-derived rather than a flag. **But
it is blocked by a real correctness bug for non-graph domains, confirmed in-loop:** `aperture_signature`
is an ordinal-*rank* key (a monotonicity/curvature fingerprint), not a *class* fingerprint. Every
strictly-increasing numeric sequence collapses to the same low-order rank signature, so a *geometric*
anti-shape held at any fixed aperture falsely repels an unrelated but readable *cubic* (both rank to
`[0,1,2,3,…]`) — the cubic, which should `confirm` at degree 3, instead gets
`repelled_by_held_antishape`. No single fixed `memory_aperture` separates a class from the whole
monotone family; a "discriminating aperture" only ever separates the one hand-picked pair a test
happens to use. The graph domain is immune only because degree-coordinates of distinct graph classes
genuinely differ in rank. **Root cause + open frontier:** an anti-shape must be keyed by *what makes
it a no-rescue class* — its verify-outcome / the reading-that-failed, i.e. two structures are the
same anti-shape iff the same reading fails the same way on them — NOT by the raw coordinate's rank
signature. Designing that class-fingerprint (and a mint-guard that refuses to enable memory for a
domain whose key does not discriminate its classes, falling back to flag-based behavior) is a genuine
research step; it was NOT committed. The landed state is the sound `track_j5` domain-registry
generalization; the memory unification is deferred until the class-fingerprint is solved rather than
shipped with a false no-false-distrust guarantee. (Recorded per the discipline that a caught,
unfixed correctness bug is documented as the open problem, not papered over.)

**Memory backend unification — RESOLVED via a class fingerprint (`track_j6`).** The blocked
frontier above is now solved. The root cause was keying anti-shapes on the coordinate's
ordinal-*rank* signature, which collapses whole families (all monotone sequences rank alike). The
fix keys the memory on a per-domain **class fingerprint** — *what makes a structure a no-rescue
class*, i.e. its felt-read/verify **outcome**, not its raw coordinate: two structures are the same
anti-shape iff **the same reading fails the same way** on them. Per domain: graph keeps its
rank-signature key (graph classes genuinely differ in rank → behavior-preserving); sequence key =
`(seq_felt_degree, authorable-reading-that-claims-it)` (e.g. geometric → `(None, log_degree)`,
cubic → `(3, None)`, Fibonacci → `(None, None)`); residue key = `(felt_confirms, authorable-that-
rescues)`. The no-false-distrust property now holds **by construction**, verified adversarially far
beyond the test battery: the anti-shape key set and the confirm key set are **disjoint**, so an
anti-shape key structurally cannot address a confirmable structure — a held geometric anti-shape
does not repel `n`, `n²`, `n²+n`, `n³`, `n³+n`, `n⁴`, shifted/scaled geometrics, or a constant
(all confirm); a residue no-rescue anti-shape does not repel any monotone-confirmable list. This is
the exact bug the prior attempt shipped, now impossible rather than merely untested. First-vs-repeat
is genuinely **derived from held state** (a held negative-valence entry for this class key == a
repeat) rather than a caller-supplied flag; fool-me-once still fires on a genuine same-class repeat
(a fresh 4ⁿ is repelled with zero verify calls). The signed-valence decision stays the composed
`net_valence_term` graph Term (conceptualizer audit green); the class-key match is bookkeeping over
felt/verify outcomes, not a relocated decision.

Two honest scope notes (from the adversarial review, applied before commit): (1) the **felt-time
rule-out (phase A)** is solver-free for every domain — a felt-*differing* candidate is cleared with
no verify, and felt reads are always `SolverSpy=0`; the phase-B full-key confirm is additionally
solver-free for sequence/graph, but the **residue** full key includes the mod-3 partition, so on a
rare felt-*collider* (a confirmable list whose parity boundaries happen to match a held anti-shape's)
residue spends one verify to confirm the class differs — acceptable (it fires only for a genuine
collider candidate and mint is post-verify), but not a blanket "repel-check is always solver-free"
for residue. (2) the sequence `(None, None)` key currently merges genuinely-distinct unclaimed
no-rescue classes (Fibonacci, n⁵-and-up, primes) into one anti-shape — correct fool-me-once today
(they are all "nothing authorable rescues this"), a latent coarseness to refine when an authorable
reading is added for one of them. The memory is **opt-in** per call (pass a substrate/memory to
enable; without one the loop is byte-for-byte the prior flag-based behavior, so track_j5 is
unchanged). Added `Domain.class_key` / `Domain.felt_component`, the per-domain class keys, a
`ClassFingerprintMemory`, and `domain_memory_verify_then_update` to `number_runner.py`, and
`track_j6_class_fingerprint_memory.py` (C1–C6, all pass). The fool-me-once / re-earnable memory is
now domain-general: a new domain inherits earned, class-keyed, false-distrust-free distrust for
free by supplying its class fingerprint alongside the four pieces.

**Refinement — the `(None,None)` bucket split by an authorable recurrence reading (`track_j6`
C7–C11).** The scope note above flagged that the sequence `(None,None)` key merged genuinely-
distinct unclaimed no-rescue classes (Fibonacci, primes, higher-degree). That refinement is now
done — and it is the natural next in-domain self-extension. Two coupled changes: **(1) a felt-degree
over-fit fix** — a probe exposed that `seq_felt_degree` spuriously confirmed *any* short sequence as
a high-degree polynomial (an n-point sequence's (n−1)th difference is trivially ≤2 values, equal by
coincidence), so Pell `[0,1,2,5,12,29,70]` wrongly read degree 5. Fixed with a scaled **witness
margin** (a degree-k claim is credible only if `k ≤ len−2−1`, falling_world's order-N witness
minimum), applied to both `seq_felt_degree` and `seq_verify_degree` so their agreement (track_j4 S1)
holds; pell/fib → None, genuine polynomials keep their degree. **(2) an authorable `linrec2`
reading** — an exact rational 2×2 solve for `(a,b)` in `x[n]=a·x[n-1]+b·x[n-2]` from the first two
triples, then an all-terms recurrence check (feel = the fit, verify = the all-terms check;
solver-free). Registered after `log_degree` so a geometric (also a degenerate linrec) keeps its
`log_degree` claim. This lets Fibonacci become a *claimed* class with its own key, and the
over-fit fix is the precondition (without it Pell/Fibonacci never reach the authorable claim).

Caught-and-fixed during review (the honest part): the adversarial semantic review found that
keying the class on the reading **name** alone (`(None,'linrec2')`) re-introduced the exact
class-merge defect one level down — Pell `(a=2,b=1)` and Fibonacci `(a=1,b=1)` are distinct
recurrences but collapsed to the same key, so a held Fibonacci anti-shape falsely repelled Pell
in-loop. Verified by own probe, then fixed by keying on the **full namespaced signature**
(`('linrec2', ('linrec2',a,b))`) the reading already computes. After the fix, Fibonacci, Pell,
geometric, and primes are **four distinct classes**; Fibonacci and Lucas correctly share a key
(same recurrence); a held Fibonacci anti-shape does not repel Pell/geometric/primes but does repel
Lucas (C9). The confirm-key set and anti-key set stay disjoint. Added `seq_read_linrec2` + the
witness margin + full-signature `seq_authorable_claim`/`seq_class_key` to `number_runner.py`;
track_j6 gains C7–C11 (all pass); track_j3/j4/j5 unchanged; audit green; the recurrence solve is
solver-free. (Residual latent coarseness, noted: still-unclaimed no-rescue classes — primes,
higher-degree, order-≥3 recurrences — share `(None,None)` until a reading is authored for each; the
mechanism to split them is now the demonstrated pattern.)

**Runtime discovery of an unseen class (`track_j7`).** A factual record, not a writeup: the
sequence self-extension now searches wider recurrence orders (`discover_recurrence`) using the
held exact-solve primitive (`_solve_linrec_order`, the same one `linrec2` uses) at a wider order
when the order-2 repertoire fails. `track_j7` exercises this on tribonacci / fib² — order-3 linear
recurrences the starting repertoire ({log_degree, linrec2}) provably does not claim: the loop
fails, then on repeat composes and verifies a `linrec3` reading from the held primitive, adopts it,
and reuses it on a fresh instance (E1–E5, all pass). The `seq_read_linrec2` body was refactored to
call `_solve_linrec_order` at order 2 (behavior-preserving; j6 unchanged). Solver-free felt path,
verify-gated adoption, no pretrained artifact.

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

**Update — the wiring is now done** (`scripts/jabberwock_gates_its_aperture.py`, the
`aperture_salience` concept in `seeds/residual_salience.json`). The blind-regime confidence
gate is stamped onto each `CapabilityAxis` as a `blind` attr (mechanically, from
`felt_aperture_read` over the axis's structure — solver-free, SolverSpy = 0), and the
frontier salience term gains one addend, `- blind*1e9`, appended to the existing
`cost_salience` term (which itself extends `residual_salience`). A blind axis is repelled so
the frontier Argmax never picks it to *commit*: the agent abstains and the pick moves to a
trustable axis, or — if every axis is blind — no axis wins and the loop routes to verify.
Gates (all pass, donkey = 0): ABSTAIN (a high-residual blind axis loses to a lower-residual
trustable one, where plain cost salience would have committed the falsely-sharp peak),
COMMIT-TRUST (a high-residual *trustable* axis still wins — the gate repels only blind axes),
ALL-BLIND (every axis repelled → route to verify), BACKWARD COMPAT (blind = 0 everywhere is
numerically identical to `cost_salience`, and the live `_frontier_advance` reflex still
resolves onto the hard frontier), FROZEN CORE (the `understand` Drive stays `frozen:true`;
only its `frontier_pick_term` data attr moved — not a frozen-core invariant). The full
cost-scheduling suite (which shares the edited seed) still passes. Honest limit: this does not
*solve* the unbounded-radius case; the win is that the frontier abstains there instead of
committing a falsely-sharp peak.

**Superseded by the signed shape field (anti-shapes).** The `blind*1e9` addend above was a
Python-stamped SCALAR mask — a Python decision wearing a graph read's clothing — and a fixed
`has_cycle` predicate rather than something learned. It is now superseded by `valence_salience`
(same seed), which reads a **native signed, aperture-indexed shape field**. Three corrections
drove the replacement: (1) *an AntiShape is a Shape like any other, merely negative polarity* —
the substrate already carries polarity natively (`dynamical:valence`, −/0/+), so the track (j2)
solution library (positive exemplars) and the anti-shapes are **one field at opposite sign**,
not two mechanisms; (2) *the anti-shape's identity depends on the aperture* — a shape is a
reading at an `order_n_concepts` order `k`, so a `Shape` node carries `(aperture k, order-k
signature, valence)` and a false commit caught at `k` mints a negative shape **at `k`**, which
repels a fresh structure only at its own aperture (noise at k=1 but clean at k=2 is not
repelled); (3) *the match must be a Term op, not a static method* — the match/net-sign is the
**decision**, so it is the Term the substrate evaluates. The `.so` is frozen (no new Rust op),
but a shape signature is a vector of ints and shape-distance is L1 = `Sum(Abs(Minus(...)))`, so
`net_valence` is **composed from existing Term ops**:

```
salience(axis) = shortfall + (1 - saturation) - cost + net_valence(axis)
net_valence(x) = Sum over Shape nodes at aperture == aperture(x) of
                     valence(sh) * [ L1(csig(x), sig(sh)) <= tol ? 1 : 0 ]
```

Python only *stamps* signature attrs (arithmetic I/O) and *mints* `Shape` nodes on verify
outcomes (structural I/O); no Python computes the pick (conceptualizer audit passes).
**Fool me once, can't get fooled again:** verify catching a false commit mints a valence=−1
shape at the used aperture (symmetric with minting +1 on a confirmed success); the next
matching structure carries negative net valence and is repelled from memory, verify not spent.
**Re-earnable:** a −1 shape later confirmed drifts toward 0/+ by the same valence update — earned
distrust, not permanent paranoia. Gates (all pass, `scripts/jabberwock_holds_antishapes.py`,
donkey = 0): STAGE-B/FOOLED (a *broom* — acyclic, so the built-in gate passes and the felt read
commits, yet it misses the spine interiors at F1 = 0.5, a genuine numerology the `has_cycle`
gate is blind to — is caught by verify and minted as an anti-shape), FOOL-ME-ONCE (a fresh broom
is repelled, verify saved), APERTURE-SCOPED (the same broom at k=2 is not repelled), RE-EARNABLE,
SYMMETRY (positive pulls, negative pushes, one field read by the same Term), BACKWARD COMPAT
(empty field ≡ `cost_salience`; live `_frontier_advance` still resolves onto the hard frontier),
FROZEN CORE, donkey = 0. The full cost-scheduling suite still passes. Honest limit unchanged:
the felt read still cannot *solve* the unbounded-radius case; the win is that a caught failure is
*held* as a negative-valence shape and the frontier abstains from it thereafter without a
hardcoded predicate. Added: `valence_salience` / `net_valence` composition, the
`aperture_signature` / `mint_shape` / `stamp_candidate_signature` / `verify_then_update`
machinery in `number_runner.py`, and `scripts/jabberwock_holds_antishapes.py`.

**Follow-up — the hardcoded `has_cycle` veto is retired.** With blindness now *learned* as a
negative-valence shape, the built-in `has_cycle` confidence gate inside `felt_aperture_read` was
a redundant special-case — a hand-coded predicate doing what the shape field now does by earning.
It is removed: the felt read no longer vetoes cycle-bearing structures, so it *commits and is
allowed to be wrong* on a ring+tail (F1 = 0.33), verify catches that first mistake, and the same
`verify_then_update` loop mints the anti-shape that repels the next matching structure. The
`RETIRED-PREDICATE` gate in `scripts/jabberwock_holds_antishapes.py` demonstrates end-to-end that
the ring+tail — the exact case the old veto abstained on — is now handled by the learned loop with
no built-in cycle test (commit → verify catches → mint → next ring+tail repelled, verify saved).
`track_j3`'s M5 is updated honestly: the fence is no longer "abstain via a cycle predicate" but
"commit, be caught by verify, and remember" — distrust is earned per-shape and aperture-scoped,
never hardcoded. `has_cycle` remains defined as a plain cheap invariant but nothing in the felt
path calls it. The confidence gate now has *no* built-in special-cases: it commits on a bounded
witness, returns an honest null only when no aperture separates anything, and learns everything
else from caught failures.

**When it's wrong: rescue-before-distrust.** A caught false commit has two very different
causes, and conflating them was a real over-distrust bug: the shape may be *genuinely blind* to
the felt repertoire, or it may just have been *read the wrong way*. "Wrong is usually the wrong
aperture/reading, not an untrustworthy shape" — the same move as the whole arc, now applied to
failure itself. `verify_then_update` now **triages** before minting distrust: on a caught wrong
commit it searches a small fixed structural reading repertoire (`default` flanked-hub, `non_leaf`,
`spanned_k0/1/2`) for a reading that **verify confirms** on this structure. If one rescues it, the
lesson is "read this shape with reading R" — a **positive** shape tagged `reading=R` (imported on
re-encounter, still feel-then-verify), *not* an anti-shape. Only when **no** reading in the
repertoire verifies is the anti-shape minted (the honest last resort). The rescue stays
non-circular because a broadly-applicable reading like `non_leaf` (correct on trees, wrong on
cycles) is only *adopted* for a shape once verify confirms it there — it is never trusted for free.
Concretely: the *broom* (default read misses the spine interiors, F1=0.5) is now **rescued** by
`non_leaf` and held positive — previously it was wrongly minted as an anti-shape; the *ring+tail*
(the ring closes, so no reading verifies) correctly gets the anti-shape. Gates
(`scripts/jabberwock_holds_antishapes.py`, all pass, donkey=0): WHEN-IT'S-WRONG (broom rescued vs
ring+tail anti-shape last resort), FOOL-ME-ONCE, APERTURE-SCOPED, RE-EARNABLE, SYMMETRY,
RETIRED-PREDICATE, BACKWARD COMPAT, FROZEN CORE. Added the reading repertoire (`apply_reading` /
`search_rescue_reading`) and a `reading` tag on held shapes in `number_runner.py`. Honest limit
unchanged: the felt read still cannot *solve* the no-rescue case; the win is it now distrusts a
shape only after confirming no reading rescues it, so it corrects *reading* mistakes instead of
laundering them into distrust.

**Cycle detection triggers the cyclic reading (not distrust).** A cycle is not untrustworthy — it
is a *different structure that needs a different reading*. `felt_aperture_read` now **detects** a
cycle up front (`cycle_core`, the 2-core found by iteratively peeling degree-1 leaves — cheap,
structural, solver-free) and, when one is present, **triggers** the cycle-aware reading (a node
purely on a ring is not a cut vertex; only where a part attaches to the ring is). This is a reading
*selector*, categorically different from the retired `has_cycle` *veto*: detection routes to the
right approach rather than abstaining. Effect: ring+tail and a plain cycle — which previously
abstained or were caught-wrong — are now **read correctly and confirmed** (F1=1.0), no distrust
needed. The learned anti-shape is now reserved for the *genuine* no-rescue case: a barbell (two
cycles joined by a bridge path) is cyclic yet no reading in the repertoire captures its cut
vertices, so it correctly falls through to the negative-valence anti-shape (last resort). Gates
(`scripts/jabberwock_holds_antishapes.py`, all pass, donkey=0): CYCLE-DETECTED (ring+tail/cycle
detected → cyclic reading → confirmed), WHEN-IT'S-WRONG (broom rescued by reading vs barbell
anti-shape), FOOL-ME-ONCE / APERTURE-SCOPED / RE-EARNABLE / SYMMETRY (now on the barbell
anti-shape), RETIRED-PREDICATE (ring+tail detected+read correctly, not vetoed), BACKWARD COMPAT,
FROZEN CORE. Added `cycle_core` (detection) and `_read_cycle_aware` (the triggered reading) to the
repertoire in `number_runner.py`; `felt_aperture_read` detects-then-branches. `track_j3` M4/M5
updated honestly (cycle-6 and ring+tail now detected→cyclic-reading→confirmed rather than
abstain/caught-wrong). The genuine no-rescue fence still has teeth (barbell).

**Repertoire self-extension: learning HOW to read, not just WHAT it can't.** The anti-shape
mechanism learns *what* the pipeline cannot read yet (a no-rescue class becomes a negative-valence
shape). Self-extension closes the loop: on a **repeated** no-rescue class (the same anti-shape hit
again after being distrusted once), the pipeline **authors a new reading** and adopts it, flipping
the class from distrusted to rescued. Non-circularity is the crux and is respected three ways: (1)
the authored reading is **composed from primitives already held** (`cycle_core` + a bridge-edge
proxy over the held adjacency/degree), not a bespoke class-specific solver — the pieces recombine
to rescue the class, the same recognise-then-compose move the salience terms and the track (j2)
library used; (2) it is **verify-gated** — only adopted when verify confirms it rescues the class;
(3) adoption is **per-class**, so a globally-imperfect authored reading (the bridge reading is
right on bridged multi-cycles, wrong on plain cycles) is **harmless** — it only ever *wins* where
it is actually right, and existing readings keep winning where they are right (**no regression**,
verified). The trigger is *repetition*: the first encounter of a no-rescue class is distrusted (no
investment yet); only when it recurs does the pipeline invest in authoring. Demonstrated
end-to-end (`SELF-EXTEND` gate, all pass, donkey=0): barbell #1 → `no_rescue_minted_antishape`
(distrust), barbell #2 → `self_extended_authored_reading` (bridge reading authored from held
primitives and adopted), barbell #3 → `rescued_by_reading` (the class is now read correctly); the
repertoire grows 6 → 7 readings and ring+tail/cycle/path/broom are unaffected. Added `cycle_core`
edge-level bridge proxy (`_bridge_edge_endpoints`), the authorable `_read_bridge` reading, and
`extend_repertoire` (verify-gated authoring) plus `_held_shape_for` (first-hit vs repeat) to
`number_runner.py`; `verify_then_update` gained the repeated-no-rescue → self-extend branch. This
turns the pipeline from *fixed-repertoire* into *self-growing*: it accumulates not just distrust
of what fooled it, but the readings that dissolve those failures — each earned, verified, and
regression-free.

### Files added

`tests/capability/number_qualia/track_j3_aperture_manifold.py` and the
`aperture_manifold` / `manifold_shape` / `has_cycle` / `felt_aperture_read` / `f1_score`
additions to `runners/number_runner.py`.
