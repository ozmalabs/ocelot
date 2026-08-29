# What implementation *forced* — and, secondarily, what it broke

Paper 01 argues that a universal framework acquires a falsifiable surface by being implementable
forwards, and records a debt: the implementation's evidence is scattered through engineering history
rather than assembled. This is the assembly.

**It was first drafted around implementation *failures* and that was the wrong object.** Failures show
the account is breakable. The stronger evidence is what building **forced** — because a theorist
chooses what goes in a theory and does not choose what a working system turns out to require.

---

## 1. Why forcing is better evidence than failure

A framework's author controls its content. That is precisely why coherence is weak evidence: anything
awkward can be accommodated before anyone sees it. **A forcing is not under that control.** Build the
thing, and it either works or it does not; when it does not, the missing piece is dictated by the task
rather than chosen by the author.

So each forced structure admits a three-way test, and all three outcomes are informative:

| outcome | what it means |
|---|---|
| **(i) already in the account** | the account covered ground it was not built to cover |
| **(ii) added because of this** | honest growth, with a recorded external cause rather than an aesthetic one |
| **(iii) still not in the account** | a live gap, and the most useful entry a document like this can hold |
| **(iv) already in use, unstated** | the structure was operating before the theory named it; building forced it into explicit form |

Outcome (ii) is not a weakness. A framework that never grew under construction would be either
complete or untested, and the second is far likelier.

**Outcome (iv) is the one worth separating, and it is easy to mistake for (ii).** There is a
difference between *inventing* structure because a build demands it and *externalising* structure one
was already using without having written it down. The first could be an artefact of the build — a
scaffolding requirement mistaken for a feature. The second cannot be, because the structure has a
prior existence the build did not create; what the build supplied was the obligation to state it in a
form something else could execute.

That is this account's own claim about self-models, arriving as method rather than as doctrine: a
frame cannot be transparent to itself at the level it is running at, so it externalises in order to
inspect. **Building is a prosthetic aperture onto one's own operation** — and per
Remark~`rem:failure-instrument`, the reason it works is that an implementation that does not run tells
you where the tacit account was incomplete, which introspection alone will not.

The epistemic limit is sharp and stated here rather than left implicit: *"I was already using this"* is
a first-person report and is not independently checkable. It cannot carry the weight a pre-registered
prediction carries. What it changes is not the strength of the evidence but its **kind** — the build
transcribed rather than generated. And it is checkable in principle, though not here: structure in use
before it was stated should leave traces in decisions and writing that predate the formalism.

---

## 2. The catalogue of forcings

### F1. Seldon manifolds — forced into the open, not into existence *(outcome iv)*

**The whole of paper 02 exists because a decision had to be made on different timescales, which
required machinery to project the future — and that machinery was already in use, mentally, before it
was ever built.** What implementation forced was not its invention but its *externalisation*: an
executable form has to be complete in a way a tacit one never has to be, so building it is what
required every field, bound and edge case to be named.

That distinction decides what the case is worth. Had the manifold been invented to make a build work,
it would be suspect as scaffolding. Having been in use beforehand, it is structure with a prior
existence that the build only transcribed — which is why it belongs in outcome (iv) and not (ii), and
why it is the corpus's clearest instance of implementation acting as an aperture onto the author's own
operation rather than as a source of new content.

Nothing in the substrate demanded it; paper 02 says so in its own scope section — *"Graphic Equalisation requires only admissible continuation and deterministic
collapse. It does not require a graph or containing frame to represent unrealised futures as an
object."* Optional to the substrate, **compulsory to the task.**

That is the clearest instance in the corpus of structure arriving from outside the theory. The
reachable-future object, its cost and capacity and deformability fields, the horizon, the width — none
of it was deduced from `(g, r, Γ)`. It was what remained after asking how a thing decides now against
consequences arriving later.

**Gap, recorded here because it is real:** *paper 02 nowhere states this origin.* It presents the
machinery as additional structure a frame may instantiate — true, and not the reason it was built. A
reader cannot currently tell that the content was in use before it was formalised, which discards the
evidential value entirely and also mis-states what kind of thing the paper is. **If the machinery was
operating before it was written, then 02 describes something that runs rather than proposing a
design** — which is a claim about its subject matter, and is where 02a's measured plural horizons
already point. This is the single most valuable fix this document identifies.

### F2. Frame ≡ dimension — the implementation had already answered *(outcome i, running backwards)*

The theory asked what the actual difference between a frame and a dimension is. The corpus sweep found
that **no frame primitive exists in the Rust substrate at all** — the engine had never needed two
things, because one edge type in two roles does all the work.

This is a forcing in the reverse direction: the implementation constrained the theory rather than the
theory specifying the implementation. It is strong precisely because nobody arranged it — the engine
was built without the question being asked, and its silence was the answer. Paper 01 now carries the
unification (`cor:frame-dimension`).

### F3. A seed must come from the container — forced by bootstrapping *(outcome i)*

By the antecedent-state principle a mint cannot authorise its own installation, so a graph's first
mint-rules must be installed from outside it. This reads as a derivation and was reached by needing an
agent to start at all: something has to be present before anything can grow. The account already had
the principle; construction is what made its consequence unavoidable.

### F4. Growth without a primitive spark — forced by novelty at runtime *(outcome i/ii)*

An agent meeting something it has no category for must either fail or grow. The sd loop — decode
against a held codebook, mint a quantum only when the residual will not fit — is what remained once
"add a primitive for the new case" was ruled out. That minting is itself a **rule** rather than a
primitive is the account's requirement; that the loop had to exist at all was the task's.

### F5. Quanta per body shape — forced by two bodies over one belief *(outcome ii)*

Navigation forced decoding **per body shape** over a single persistent belief, because a 1×1 and a 2×2
body route differently over identical terrain. Frame-relative individuation was in the account;
*per-body config-space decoding, foveation, and per-dimension residual splits* were not, and arrived
because a flood does not occur per pixel — it occurs at quanta.

### F6. Direction not established from here

Several results *look* forced but this document cannot establish which way the derivation ran, and
saying so is cheaper than guessing: **time as inferred from closure cycles** (the engine has no clock,
ticks being rule firings — but whether the theory or the engine settled that first is not recorded),
and **the residual/absent distinction**. Listed so they are not silently claimed.

---

## 3. Secondary: what implementation broke

Failures remain evidence — weaker, and worth keeping brief. Three classes, with the fourth being the
interesting absence.

**Predicted.** The meta-shape recognizer scored by substring containment and broke ties
**alphabetically by the shape's own name**; across all 55 pairs of eleven meta-shapes, **44 are ties
and the old scorer decided 44/44 by the alphabet**. The account's prediction is structural — *a
recognizer that always answers can never produce a residual, and a grain with no residual cannot
grow.* Deleting the tiebreak is what made the mint reachable (`META_SHAPE_FIRST_CLASS_RESULTS.md`).
Also: finer base grain **fragmented** (33.8 → 26.2, run 5), and partial-credit metrics and
higher-order relations **all lost** (→ 30.0, runs 7–9) — strictness is the signal, twice.

**Repaired by the account, not by patching.** A ratio stored as a float broke integer-nativeness and
**the fix was not a cast** — a ratio is a cross-frame reading, so the seed publishes two integers
(`CALIBRATED_DIFFICULTY_RESULTS.md`). The moon-bug routing fix was attempted twice as a Python string
check and refused twice, because that is a routing decision masquerading as parse. The motor-program
slope collapse was **hand-written as a bespoke rule when it was rung 2 of an existing ladder**, amid
**60 count-divided learners across 8 embodied seeds, none inside the shape-matching faculties**.

**Underspecification, found only by building.** Unconditional rule mirroring measured NO-GO at
**51,769 mirror nodes for one rule** and **+2,557 per checkpoint-reload cycle with no convergence**
(`RULE_REFERENCE_LAYER_SIZING_RESULTS.md`); two unfixed siblings remain enumerated in
`SHAPE_AUDIT.md`. `CapabilityAxis` identity is a **truncated, order-dependent string join** that can
misroute novelty as duplicate — a growth failure presenting as successful recognition, **still live**.

**Disconfirmation — empty, and that is the finding.** Almost nothing in the record is the account
being *contradicted* by its implementation. Either the account is loose enough that outcomes rarely
contradict it, or contradictions were absorbed as implementation corrections because nobody was
looking for the other kind. The second is likelier: **no document in this tree is written to ask "did
this outcome contradict the account?"** — they ask whether the rung passed. Until one is, the emptiness
proves nothing.

---

## 4. The selection problem

**Assembled by the same hand that produced it, from a record that hand wrote.** Three bounds and one
irreparable hole. The record is **pre-registered** — 94 `*_PREREG.md` against 109 `*_RESULTS.md`, and
a prediction recorded in advance and reported failed is not post-hoc selection. Every item cites a
document or commit. Base rates are lower bounds from keyword sweeps, not a census.

The hole: **there is no register of failures or forcings that were never written down**, and its size
cannot be estimated from inside the record.

Under paper 01's own rule this is not independent evidence at all — same hand, same vocabulary,
disqualified exactly as the computing case is. It shows the account is **specified enough to be built
from and broken by**, which most frameworks cannot demonstrate. It does not show the account is true.

---

## 5. Next

1. **State F1's origin in paper 02.** The forcing is the evidence and the paper currently discards it.
2. **Establish direction for F6** from git history rather than recollection — and test F1's outcome
   (iv) claim the same way, by looking for the manifold's structure in decisions and notes predating
   the formalism. That is the only route from a first-person report to something checkable.
3. **Write one prereg that asks whether an outcome would contradict the account**, so §3's empty class
   can be populated or its emptiness can start meaning something.
