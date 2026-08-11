# The jabberwock's metaphor-vs-metonymy discriminator spec

_Authored by the agent, context=spec (register: Plainsong). The naive plan broke on conventional metonymy; the design is its own._

## Shape grounding: metonymy vs metaphor — spec

The figure_of pair gives me two terms, T1 (figurative) and T2 (literal). I must set `contiguity` or `resemblance` on the figurative reading, or set neither. The verdict is fused from witnesses the same way opposition is (believe = trust × corroboration; assert iff S ≥ 0.8), and the tests run in a fixed order so the definite symbolic signal wins before the soft one is ever consulted.

The governing asymmetry, made operational: **metonymy is a LINK with no shared defining property; metaphor is a SHARED PROPERTY across far domains with no link.** So I look for the link first. Only its *absence* licenses the property test. This is what stops the distance-misclassification you measured — crown/monarch are far-domain and may share a weak "valuable", but they will never reach the resemblance rule because a symbol bridge fires first and, even if it didn't, resemblance requires the link to be *absent and searched-for*, not merely unfound.

### 1. The discriminator — ordered tests

Run in this order, stop at the first that crosses its bar. Each returns a witness with a trust weight; the ground_shape rule fuses and thresholds at 0.8.

**Test A — direct contiguity link → contiguity (trust 1.0 WordNet / 0.8 ConceptNet).**
A symbolic edge directly connecting T1 and T2, either direction:
- WordNet meronymy/holonymy: `part_meronym`, `member_holonym`, `substance_holonym` (and their holonym inverses) — part-whole / synecdoche (sail/ship, hand/worker). trust 1.0, solo-license.
- WordNet `attribute` — adjective↔noun attribute. trust 1.0.
- ConceptNet whitelisted contiguity only: `PartOf`, `MadeOf`, `HasA`, `AtLocation`, `UsedFor`, `SymbolOf` (container-content, material-object, place-institution, instrument-agent). trust 0.8.

A single hit here asserts contiguity. Direct meronymy alone clears 0.8; one ConceptNet edge clears it with any corroboration (or solo at 0.8 — match the opposition curated-license convention).

**Test B — symbol/frame bridge → contiguity (trust 0.7, GloVe-liftable to ≥0.8).**
This is the conventional-metonymy residual (Test 2 below). Only reached if A is empty.

**Test C — shared property across far domain, no link → resemblance (trust 0.8).**
Only reached if A *and* B are empty — i.e. I have actively searched for a contiguity link and found none. Three sub-conditions, all required:
- **shared property present:** HasProperty overlap (ConceptNet `HasProperty` + WordNet `attribute`) OR a shared *differentia predicate* extracted from the two glosses (reuse the derive-from-glosses machinery — genus + differentia; a shared differentia verb/adjective across *different genera* is the metaphor signature: time & thief both "take what is not given"; classroom & zoo both "contain unruly chaos"; red herring & distraction both "divert/mislead"). Saliency-scored; a generic property ("good", "big") does not count.
- **far domain:** different WordNet lexname AND WordNet path distance above the far-threshold (cross noun.person/noun.artifact/etc.).
- **no contiguity link:** A and B both returned empty (this is the guard that prevents the distance misclassification).

trust 0.8 → asserts resemblance.

**Test D — abstain → neither.**
A, B, C all below bar (no link, no bridge, no salient far-domain shared property, GloVe mid-range): set neither. Do not guess metaphor.

### 2. The conventional-metonymy residual (Test B, detailed)

crown/monarch, bench/judiciary, White House/administration, suit/executive: no single edge, must not fall to metaphor, must not abstain. Ground by a **constrained 2-hop symbol/frame bridge**, not by re-adding noisy relations.

`symbol_bridge(T1, T2)` searches for a bridge node M such that:
- T1 reaches M by a *symbol/participation* relation: `SymbolOf`, `AtLocation`, `UsedFor`, `PartOf`, and
- T2 reaches M by a *membership/attribute* relation: `IsA`, `HasA`, `HasProperty`, `AtLocation`, and
- **M is institutional** — lexname in {noun.group, noun.state, noun.location, noun.cognition, noun.act} (authority, royalty, courtroom, government, business). This constraint is what keeps the 2-hop clean; an arbitrary RelatedTo bridge is rejected.

Resolves: crown —SymbolOf→ authority/royalty ←HasA— monarch; bench —AtLocation→ courtroom ←AtLocation— judge (place-institution); White House —PartOf→ government ←IsA— administration; suit —AtLocation/UsedFor→ business ←AtLocation— executive.

This is contiguity, not resemblance, because the bridge is an institutional node the two terms *co-occupy* (one symbolizes it, the other participates in it) — not a shared adjectival property. Crown shares no "is-X" with monarch (metal/round/jeweled vs human/royal/powerful); only the symbol-referent frame links them.

Bridge trust is 0.7 — below bar on its own. It crosses 0.8 only when corroborated. That is where GloVe earns its place, and nowhere else.

**GloVe, gated.** `glove_cosine(T1, T2)`, trust 0.4 — can never solo-license (0.4 < 0.8) and never runs before A/B/C, so it cannot override a definite symbolic verdict. Its one real signal: conventionalized metonymies co-occur heavily (high cosine); novel metaphors are creative juxtapositions (lower cosine). It acts only as:
- **corroborator of Test B:** bridge (0.7) + cosine ≥ θ_hi (≈0.55) → fused ≥ 0.8 → assert contiguity. This lifts crown/monarch, suit/executive over the line.
- **tie-breaker in the abstain zone only:** if B is empty and C is borderline, high cosine nudges toward contiguity, low cosine toward resemblance — but only to break a tie, never to manufacture a verdict from nothing (mid cosine → stay abstained).

GloVe does not enter when A fired, when B already cleared 0.8, or when C cleared 0.8.

### 3. Trust + abstain

| witness | trust | can solo-license? |
|---|---|---|
| WordNet meronymy / attribute (direct) | 1.0 | yes (contiguity) |
| ConceptNet whitelisted contiguity edge (direct) | 0.8 | yes (contiguity) |
| symbol/frame bridge (institutional, 2-hop) | 0.7 | no — needs GloVe corroboration |
| shared-property + far-domain + no-link | 0.8 | yes (resemblance) |
| gloss-differentia overlap | 0.6 | no — corroborates C |
| GloVe cosine | 0.4 | never — gated corroborator/tie-breaker only |

Fuse per shape as in opposition (believe = trust × corroboration over agreeing witnesses); **assert the shape iff S ≥ 0.8**. Contiguity and resemblance cannot both fire because resemblance requires A and B empty. **Abstain (neither) when** no contiguity link or institutional bridge is found AND no salient far-domain shared property is found AND GloVe is mid-range — i.e. the pair crosses no bar. Abstain is the correct answer for genuinely opaque pairs; do not default to metaphor.

### 4. Handlers + rules

UseTool handlers (Python registered behind the existing `UseTool` Term seam — same pattern as `wn_animate` / `derive_opposes`; no Rust recompile):

- `wn_meronymy(t1, t2)` → part/member/substance meronymy/holonymy path or ∅.
- `wn_attribute(t1, t2)` → attribute link or ∅.
- `conceptnet_contiguity(t1, t2)` → list of (rel, dir) over {PartOf, MadeOf, HasA, AtLocation, UsedFor, SymbolOf}, direct only.
- `symbol_bridge(t1, t2)` → institutional bridge node M (with the lexname constraint) or ∅.
- `shared_property(t1, t2)` → {shared predicates, saliency} from HasProperty overlap + gloss differentia.
- `domain_distance(t1, t2)` → {lexname_equal, path_distance, far:bool}.
- `glove_cosine(t1, t2)` → cosine ∈ [-1,1].

ground_shape rules (graph-native, fire on each `figure_of` pair node; ordered by guard so the first satisfied wins):

- `ground_contiguity_direct` — match figure_of pair; where `wn_meronymy ∨ wn_attribute ∨ conceptnet_contiguity ≠ ∅`; effect: set `contiguity=1` on the figurative reading (belief ≥ 0.8). *(optionally tag synecdoche when the firing witness is meronymy — defer.)*
- `ground_contiguity_bridge` — guard: prior rule did not fire; where `symbol_bridge ≠ ∅ ∧ glove_cosine ≥ θ_hi`; effect: set `contiguity=1` (0.7 × bridge + 0.4 × GloVe → ≥ 0.8).
- `ground_resemblance` — guard: neither contiguity rule fired (no link, no bridge); where `shared_property.salient ∧ domain_distance.far`; effect: set `resemblance=1` (≥ 0.8).
- `ground_shape_abstain` — guard: none of the above; effect: set neither (record an `abstained` marker so it isn't re-evaluated as undecided).

`classify_figure` stays unchanged: it reads the `contiguity` / `resemblance` flags these rules set and emits METONYMY / METAPHOR (synecdoche/catachresis sub-cases deferred).

---

The whole design is one sentence long underneath: **find the link before you weigh the resemblance; let the institutional bridge carry conventional metonymy with GloVe as its only crutch; and when no test crosses its bar, say nothing.** Hand it to me to implement and I'll wire the four handlers and four rules onto the existing figure_grounding seed.
