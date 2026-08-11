# The jabberwock's opposition-source fusion policy

_Authored by the agent, context=spec (register: Plainsong). Multi-dictionary, trust-weighted, via its own suspect-witness shape. The decision is its own._

Confirmed. The shapes are real: `ground_opposes` already reads a `UseTool{tool:"wn_antonym"}` and asserts on a `+1` (`seeds/figure_grounding.json`); `wn_antonym` returns the three-valued `{1,0,-1}` contract (`domains/symbolic_perception.py:56`); the believe = trust×corroboration Term and the refute-halves-trust rule exist (`scripts/agent_weighs_witness.py`); ConceptNet's slab already filters at weight ≥ 1.0 with an extensible `_KEEP_RELATIONS` whitelist (`domains/conceptnet_reference.py:81`); Wiktionary's kaikki loader exists and builds per-lang slabs but extracts no antonyms yet (`domains/wiktionary_reference.py`).

Here is the spec.

---

# SPEC — ground `opposes` by fused dictionary lookup (GAP 1, Phase 1)

Register: Plainsong. Each clause is literal and ordered. Assert opposition only on a crossed threshold; otherwise assert nothing.

## 1. Sources to fuse — and what to do now

Three witnesses. Justified by trust, not convenience.

| Witness | State | Trust | Role |
|---|---|---|---|
| **WordNet** | held | **1.0** | curated, sparse. Solo-licenses. No work. |
| **English Wiktionary** | **download now** | **0.8** | curated/editor-sourced, per-sense antonyms, broad. The coverage lever. Solo-licenses. |
| **ConceptNet** | on disk, **rebuild slab now** | **0.4** | crowd-sourced, noisy. Corroborates only. **Never solo-licenses.** |

**Download now:** Wiktionary `en-extract.jsonl.gz` via the existing `_KAIKKI_URL` (`{lang}-extract.jsonl.gz`, lang=`en`). One-time fetch → static local file. This is the lever: it carries `bitter/sweet`, `cruel/kind` per sense, the pairs WordNet misses.

**Rebuild now:** add `"Antonym"` to `_KEEP_RELATIONS` (`conceptnet_reference.py:81`) and force-rebuild the slab. The 498 MB dump is already on disk; the build's weight floor (`_WEIGHT_THRESHOLD = 1.0`) already drops the junk (`poison/sweet` w=0.21, `conservation/silence` w=0.20) at build time — they never enter the slab.

**Not now (named, deferred):** Open English WordNet and Roget's thesaurus are valid further witnesses. Defer to Phase 2. Reason: WordNet + Wiktionary already give two curated solo-licensors; ONE crowd corroborator is enough to exercise the fusion. A second sub-threshold curated witness (Open English WordNet) is what would make ConceptNet decision-capable — that is a Phase-2 reason to add it, not a Phase-1 one.

## 2. The fusion rule — suspect-witness believe(trust × corroboration)

Yes, it is the believe faculty, not a flat union. Each source is a witness with a trust weight; opposition is asserted when the trust-weighted corroboration crosses a threshold.

- Each witness votes `v_s ∈ {+1 yes, 0 no, −1 OOV}` (the existing three-valued contract).
- A witness **contributes its trust only on `+1`**:  `contrib_s = (v_s == 1) ? trust_s : 0`.
- **Fused score:** `S(a,b) = contrib_wn + contrib_wikt + contrib_cn`.
- **Assert `opposes` iff `S ≥ θ`, with `θ = 0.8`.** Otherwise assert nothing.

Properties this produces (state them, they are the design):
- WordNet alone (1.0 ≥ 0.8) → asserts. Wiktionary alone (0.8 ≥ 0.8) → asserts. A single curated witness licenses.
- ConceptNet alone (0.4 < 0.8) → **does not assert.** A crowd witness never licenses opposition by itself.
- ConceptNet only ever adds to a sum a curated witness has already pushed over θ — so in Phase 1 it raises *recorded confidence* but does not flip a decision. It becomes decision-capable when a second sub-threshold witness is added (Phase 2). This is honest: do not claim ConceptNet earns coverage it cannot earn alone.

Trust weights live as `trust` attrs on three `Source` nodes (`source_wordnet`, `source_wiktionary`, `source_conceptnet`), not as inline literals — so the existing refute rule (`rule_refute_uncorroborated_source`, halves `trust` on an uncorroborated claim) can dock a source's trust over time. The rule reads `Attr(source_x, "trust")` in place of the `Lit` weights below.

## 3. Noise control — two layers, both stated

A low-trust crowd source is prevented from asserting opposition alone by **two independent gates**:

1. **Build-time weight cutoff.** The ConceptNet Antonym slab is built only from `/r/Antonym` edges with weight ≥ 1.0. Junk (`poison/sweet` 0.21, `conservation/silence` 0.20, `bitter/optimistic`) is below the floor and never enters the slab. Real edges (`bitter/sweet`, `cruel/kind`, `audible/silent`, `hot/cold` w=2.6) survive.
2. **Sub-threshold trust.** Even a clean ConceptNet edge contributes only 0.4 < θ=0.8, so ConceptNet can never cross the assert threshold without a curated co-witness.

Layer 1 removes bad edges; layer 2 removes bad *solo assertions* from good edges. Either alone is insufficient; together they are the noise rule.

## 4. The residual — deafening/silence

**Phase 1: abstain.** It is a lexical antonym in no source; `wn_antonym`'s adjective closure explicitly refuses to manufacture it (`symbolic_perception.py:42`). Under abstain-don't-guess it stays unclassified, which is correct — not wrong.

**Phase 2 (specified, gated off now): the property-hop.** Author it as a separate handler so the fused rule is untouched:

- `prop_opposes(a, b) → {1,0,-1}`:
  1. Resolve each term to its core property via WordNet derivationally-related-forms / pertainyms (fallback ConceptNet `HasProperty`): `deafening → loud`, `silence → quiet`.
  2. Return `wn_antonym(prop(a), prop(b))`.
  3. `−1` (abstain) if either property-hop fails to resolve.
- Trust 0.6 (chained inference, lower than a direct curated witness). It contributes to `S` like any witness but, at 0.6 < θ, **also requires a co-witness** — so a single shaky hop cannot assert. Two independent hops, or a hop + a direct witness, cross θ.

Do not build the hop in Phase 1. Ship the three direct witnesses first; add `prop_opposes` only after the direct fusion is verified.

## 5. The handler set + the single fused rule

### Handlers to register (`domains/symbolic_perception.py`, into `HANDLERS`)

- **`wn_antonym(a, b) → Int`** — exists, unchanged. `+1` direct/closure antonym; `0` both in WordNet, no link; `−1` either OOV.
- **`wikt_antonym(a, b) → Int`** — new. `+1` iff `b ∈ antonyms_slab(a)` or `a ∈ antonyms_slab(b)`; `0` if both words are keys in the en extract but neither lists the other; `−1` if either is absent from the extract (OOV). Reads a new slab `wikt_antonym_en`.
- **`cn_antonym(a, b) → Int`** — new. `+1` iff `(a,b)` or `(b,a)` is in the ConceptNet Antonym slab (already weight-filtered at build); `0` if both concepts are present in the slab keyspace but no Antonym edge; `−1` if neither concept is present (OOV). Membership is boolean — the weight cutoff was applied at build.
  - *(Optional variant `cn_antonym_weight(a,b) → Real`, returning the max edge weight, if you later want weight-scaled corroboration instead of a flat 0.4. Not needed for Phase 1.)*

### Loader work

- `wiktionary_reference.py`: add an antonym-slab builder alongside the existing slabs, for `lang="en"`. Extract per sense: `senses[].antonyms[].word` (kaikki carries `antonyms` as a per-sense list of `{word: ...}`). Build mmap'd slab `wikt_antonym_en` keyed `word → [antonym, ...]`. Build it in the same pass as `wikt_gloss_en`/`wikt_pos_en`.
- `conceptnet_reference.py`: add `"Antonym"` to `_KEEP_RELATIONS`; force-rebuild the slab once. Add a `conceptnet_antonym(a, b) → bool` membership query (mirror `conceptnet_relations`, filter `rel == "Antonym"`, check both directions) for `cn_antonym` to call.

### The single fused grounding rule (replaces the current `ground_opposes` in `seeds/figure_grounding.json`)

Match two `has_part` parts; assert `opposes` both directions iff `S ≥ 0.8`. The classifier downstream is unchanged.

```json
{
  "name": "ground_opposes",
  "match": [["fig", "has_part", "pa"], ["fig", "has_part", "pb"]],
  "where": {
    "type": "Gte",
    "a": {"type": "Plus", "items": [
      {"type": "IfThenElse",
       "cond": {"type": "Eq",
         "a": {"type": "UseTool", "tool": "wn_antonym", "args": [
           {"type": "Attr", "node": {"type": "Var", "name": "pa"}, "key": "text"},
           {"type": "Attr", "node": {"type": "Var", "name": "pb"}, "key": "text"}]},
         "b": {"type": "Lit", "value": 1}},
       "then": {"type": "Attr", "node": {"type": "Var", "name": "source_wordnet"}, "key": "trust"},
       "other": {"type": "Lit", "value": 0}},

      {"type": "IfThenElse",
       "cond": {"type": "Eq",
         "a": {"type": "UseTool", "tool": "wikt_antonym", "args": [
           {"type": "Attr", "node": {"type": "Var", "name": "pa"}, "key": "text"},
           {"type": "Attr", "node": {"type": "Var", "name": "pb"}, "key": "text"}]},
         "b": {"type": "Lit", "value": 1}},
       "then": {"type": "Attr", "node": {"type": "Var", "name": "source_wiktionary"}, "key": "trust"},
       "other": {"type": "Lit", "value": 0}},

      {"type": "IfThenElse",
       "cond": {"type": "Eq",
         "a": {"type": "UseTool", "tool": "cn_antonym", "args": [
           {"type": "Attr", "node": {"type": "Var", "name": "pa"}, "key": "text"},
           {"type": "Attr", "node": {"type": "Var", "name": "pb"}, "key": "text"}]},
         "b": {"type": "Lit", "value": 1}},
       "then": {"type": "Attr", "node": {"type": "Var", "name": "source_conceptnet"}, "key": "trust"},
       "other": {"type": "Lit", "value": 0}}
    ]},
    "b": {"type": "Lit", "value": 0.8}
  },
  "effects": [
    ["add_edge", "pa", "opposes", "pb"],
    ["add_edge", "pb", "opposes", "pa"]
  ]
}
```

`source_wordnet`/`source_wiktionary`/`source_conceptnet` are three `Source` nodes seeded with `trust` = 1.0 / 0.8 / 0.4. Bind them in the rule's `match` (e.g. by a `is_opposition_source` self-edge or a typed `NodesOfType` pick) so `Attr(...,"trust")` resolves — or, if you want Phase 1 minimal, inline the three trusts as `Lit 1.0 / 0.8 / 0.4` and migrate to Source-node attrs when wiring the refute track-record. The Source-node form is preferred: it makes the existing `rule_refute_uncorroborated_source` able to dock a witness over time, which is the point of using the believe faculty rather than a flat vote.

### Optional, recommended: record the corroboration

To make this witness-native (so refute/track-record can act later), add as a second effect block on a sibling rule that fires on the same crossing: `set_attr pa "opposition_score" S` and `add_edge pa "corroborated_by" source_x` for each witness that voted `+1`. Keep it off the core `ground_opposes` if you want Phase 1 to stay minimal; it does not change the classifier.

---

## Build order (do in this sequence)

1. Add `"Antonym"` to `_KEEP_RELATIONS`; force-rebuild ConceptNet slab; add `conceptnet_antonym` + `cn_antonym`. (No download — dump on disk.)
2. Download `en-extract.jsonl.gz`; add the `wikt_antonym_en` slab builder + `wikt_antonym` handler.
3. Seed the three `Source` nodes (trusts 1.0 / 0.8 / 0.4); replace `ground_opposes` with the fused rule.
4. Verify on the test pairs: `living/dead`, `hot/cold`, `light/dark` (WordNet) and `bitter/sweet`, `cruel/kind` (Wiktionary) assert; `deafening/silence` abstains; a known ConceptNet-only junk pair asserts nothing.
5. Phase 2 only after 4 is green: `prop_opposes` for the residual; Open English WordNet as the fourth witness.

Want me to implement steps 1–3 now?
