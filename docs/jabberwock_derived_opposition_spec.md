# The jabberwock's derived-opposition spec (reason the antonym from definition + context)

_Authored by the agent, context=spec (register: Plainsong). The residual is not a forfeit — it is derivable from comprehension. The design is its own._

The write needs approval, but the spec is ready. Here it is — handing it back directly.

---

# Derived-opposition spec — the fourth witness, `derive_opposes`

**Frame.** The three lexicons are *authority/crowd* witnesses. `derive_opposes` is a fourth kind: first-person inference over materials I already hold (glosses, the meaning-vector faculty + its `semantic_tension` relation, BlendCover, negation cues). It fires only when the lexicons are silent — the residual. Graded: near-deductive derivations are worth a secondary lexicon; soft contrasts must be backed.

## 1. Mechanisms — ordered, with the residual each resolves

Three layers, tried in order, returning the **first** non-abstain verdict. Order runs lightest-most-certain-understanding → heaviest-tool.

**Layer A — definitional negation/absence over a shared genus** *(first)*. One gloss puts a term under a negation cue (`absence of / lacking / without / devoid of / not`); the other affirms/intensifies that same genus. Reads both glosses + the held negation-cue set. Extract `absented_term(A)`; extract `genus_terms(B)` **expanded by one property-hop** (so `loud → "producing sound of great volume"` yields `sound`); fire iff they share a genus (lemma / `is_a` / property-genus).
→ Resolves the **absence-of-genus** residual: `silence`="absence of **sound**" vs `deafening`→hop `loud`→"producing **sound**…". **Why first:** reads the author's own negation word over a verified shared genus — near-deductive, no tool.

**Layer B — property-hop then antonym-test the properties** *(second)*. `hop(w)` = head content lemma of the gloss after stripping intensifiers/negation (`deafening→loud`, `silence→quiet`). Recurse on the property pair through **lexical-only** grounding `ground_opposes_lexical` (witnesses 1–3, no witness 4). HARD if that grounds ≥0.8, SOFT if 0.4–0.8.
→ Resolves the **polar-properties-listed-but-not-the-words** residual: `loud/quiet` is a listed antonym even when `deafening/silence` is listed nowhere. **Why second:** one hop + reuse of existing grounding; the generalisation of A.

**Layer C — meaning-vector / semantic-tension contrast** *(last)*. `contrast(vec(glossA), vec(glossB)) → {domain_overlap, pole_flip, margin}` using `agent_builds_meaning_vector`, the `semantic_tension` relation from the `meaning_vector` seed ("two readings held in OPPOSITION — opposite valence"), and BlendCover for structural alignment.
→ Resolves the **pure-semantic-contrast** residual: `cruel`="inflict pain" vs `kind`="tender, helpful" — same field, opposed valence. **Why last:** the only heavy tool and the only false-positive risk; requires **same field AND flipped pole**, never distance alone.

## 2. Trust — graded, with a justified solo line

| Verdict | When | Trust | Solo-licenses? |
|---|---|---|---|
| **HARD** | Layer A fires; or B with property-pair `S≥0.8`; or C with `pole_flip ∧ margin≥θ_high` | **0.8** | **Yes** (`0.8 ≥ 0.8`) |
| **SOFT** | B with property-pair `0.4≤S<0.8`; or C with `θ_low≤margin<θ_high` | **0.5** | No — needs ≥0.3 more (ConceptNet 0.4 → 0.9) |
| **ABSTAIN** | §4 | 0 | — |

**0.8 not 1.0:** a clean derivation is as reliable as a curated *secondary* lexicon (Wiktionary=0.8), so it earns the same weight and — per your mandate, don't abstain where the definitions carry the answer — must land *exactly* on the solo line. Not 1.0 because sense-selection/genus-matching can mis-pick under polysemy. **0.5 corroborate-only:** a soft contrast can be coincidental same-field similarity; below the single-source bar, so it participates but never asserts alone (same discipline as ConceptNet, different reason — uncertain inference, not noisy source).

## 3. Fusion — fourth witness, assert rule unchanged

```
S  = 1.0*wn_antonym(a,b) + 0.8*wikt_antonym(a,b) + 0.4*(cn_antonym(a,b) >= 1.0)
(v,t) = derive_opposes(a,b);   if v == 1: S += t*1.0     # t ∈ {0.8 HARD, 0.5 SOFT}
assert opposes(a,b)  iff  S >= 0.8
```
HARD residual, lexicons silent → `S=0.8` → assert (`silence/deafening`, `cruel/kind`). SOFT alone → 0.5 → abstain unless ConceptNet adds 0.4 → 0.9. `v==0` and `v==-1` both add 0 (no veto), but are logged distinctly ("judged not-opposite" vs "could not judge").

## 4. Abstain — precise

Return **-1** when no layer competently fires: either gloss missing; A has no cue or no genus-match; B has no hop or grounds `<0.4`; C has `domain_overlap<θ_dom` (different field) or `margin` in `[θ_same, θ_low)` (ambiguous band). Return **0** (confident not-opposite) *only* at C with `domain_overlap≥θ_dom ∧ ¬pole_flip ∧ margin≤θ_same` (synonyms: `kind/gentle`). Never returns 1 without a layer crossing its bar; never returns 0 from absence of evidence. Thresholds (`θ_dom=0.50, θ_high=0.60, θ_low=0.35, θ_same=0.15`) are **graph-resident `Threshold` nodes** on the meaning-vector Term, learned by the same self-tuning Rules as the STT cut thresholds — not hardcoded.

## 5. Handler + fused rule

```python
derive_opposes(a, b):
    ga, gb = primary_gloss(a), primary_gloss(b)          # WordNet sense-1, else wikt_gloss slab sense-1
    if ga is None or gb is None: return (-1, 0)

    # Layer A
    for (neg_src, other_gloss, other_word) in [(ga, gb, b), (gb, ga, a)]:
        neg = absented_term(neg_src)
        if neg is not None:
            genus = genus_terms(other_gloss) | {hop_genus(other_word)}
            if shares_genus(neg, genus): return (1, 0.8)          # HARD

    # Layer B
    pa, pb = hop(a), hop(b)
    if pa and pb and pa != a and pb != b:
        v = ground_opposes_lexical(pa, pb)               # witnesses 1-3 only → terminates
        if v.assert and v.S >= 0.8: return (1, 0.8)              # HARD
        if v.S >= 0.4:              return (1, 0.5)              # SOFT

    # Layer C
    c = contrast(vec(ga), vec(gb))
    if c.domain_overlap >= θ_dom:
        if c.pole_flip and c.margin >= θ_high: return (1, 0.8)   # HARD
        if c.pole_flip and c.margin >= θ_low:  return (1, 0.5)   # SOFT
        if (not c.pole_flip) and c.margin <= θ_same: return (0, 0.8)  # confident not-opposite
    return (-1, 0)                                                # abstain
```
```python
ground_opposes(a, b):                       # public rule, sets the opposes edge
    S  = 1.0*wn_antonym(a,b) + 0.8*wikt_antonym(a,b) + 0.4*(cn_antonym(a,b) >= 1.0)
    v, t = derive_opposes(a,b);  S += t*(v == 1)
    if S >= 0.8: assert opposes(a,b)        # else assert nothing

ground_opposes_lexical(a, b):               # Layer-B recursion target, no witness 4
    S = 1.0*wn_antonym(a,b) + 0.8*wikt_antonym(a,b) + 0.4*(cn_antonym(a,b) >= 1.0)
    return {assert: S >= 0.8, S: S}
```

**Termination:** B recurses only through `ground_opposes_lexical`; the hop is one level; no descent into witness 4.

**Worked residuals:** `silence/deafening` → A fires (shared genus `sound`) → assert. `cruel/kind` → A/B abstain, C fires (same field, harm-vs-help pole-flip) → assert. `poison/sweet` (ConceptNet junk w=0.21) → cn gate drops it, no shared-genus negation, no grounded property antonym, no clean pole-flip → abstain. `kind/gentle` → C returns 0 (same field, no flip) → correctly not opposites.

---

The two example pairs both assert **solo, via different layers** — A for `silence/deafening`, C for `cruel/kind` — which is exactly the "don't abstain where your definitions carry the answer" target, while junk and synonyms still stay out.

I drafted this to `docs/jabberwock_derived_opposition_spec.md` (the path the design scripts use) but the write needs your approval — want me to save it there?
