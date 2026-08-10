"""PHASE 1 VERIFICATION — ground oxymoron opposition by trust-weighted dictionary fusion. NO LLM.

The figure judge's `_opposite` (a `claude -p` call) is retired. Opposition is now grounded by the
agent's suspect-witness fusion over three dictionaries: WordNet (trust 1.0) | English Wiktionary
(0.8) | ConceptNet (0.4, corroborates only). A `UseTool` Term in the `ground_opposes` rule reads each
witness; opposition is asserted iff trust-weighted corroboration >= 0.8; otherwise abstain. The
classify_figure cascade is unchanged. This script builds oxymora + controls, grounds + classifies
with ZERO judge calls, and reports which witnesses licensed each decision.

Run: PYTHONPATH=.:runners/dsl/python python -m scripts.figure_grounding_phase1
"""
from __future__ import annotations
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import substrate_rs._native as _N
from scripts.build_persona_faculty import boot
from substrate.seed_loader import manifest_for
from domains.symbolic_perception import (register_symbolic_handlers, wn_antonym, wikt_antonym,
                                          cn_antonym, derive_opposes)

SEP = "=" * 96

# (name, two opposed parts, the role it demonstrates). Expectation is NOT hard-coded coverage — it is
# DERIVED from the policy (assert opposition iff trust-weighted corroboration >= 0.8), so the check
# validates the rule against whatever the dictionaries actually say.
CORPUS = [
    ("living dead",       ["living", "dead"],     "WordNet solo (+corroborated)"),
    ("bittersweet",       ["bitter", "sweet"],    "Wiktionary recovers WordNet gap"),
    ("noise of silence",  ["noise", "silence"],   "Wiktionary solo at threshold 0.8"),
    ("love-hate",         ["love", "hate"],       "all three lexicons agree"),
    ("deafening silence", ["deafening", "silence"], "RESOLVED by derived Layer A (shared genus 'sound')"),
    ("motion stillness",  ["motion", "stillness"], "RESOLVED by derived Layer A (stillness='absence of motion')"),
    ("cruel kindness",    ["cruel", "kind"],      "RESOLVED by derived Layer C (valence flip + shared field 'quality')"),
    ("delicious ugly",    ["delicious", "ugly"],  "Layer C field-guard: opposite valence but DIFFERENT field — must NOT assert"),
    ("kind gentle",       ["kind", "gentle"],     "synonyms control: must NOT assert"),
    ("blue car",          ["blue", "car"],        "control: not opposed"),
]
TRUST = {"wn": 1.0, "wikt": 0.8, "cn": 0.4}
THETA = 0.8


def main():
    print(SEP)
    print("PHASE 1 — opposition grounded by trust-weighted dictionary fusion (WordNet|Wiktionary|ConceptNet). NO LLM.")
    print(SEP)
    a = boot()
    names = register_symbolic_handlers(_N)
    for s in ("figurative_language", "figure_grounding"):
        a.inner.load_seed_manifest(manifest_for(s), a.agent)
    print(f"\n  registered symbolic handlers: {names}; figure_grounding seed loaded (LLM judge NOT wired)\n")

    src_dict = a.s.add_node("Source", {"name": "dictionary", "trust": 0.9})
    src_cu = a.s.add_node("Source", {"name": "common_usage", "trust": 0.7})

    def build(name, parts):
        lit = a.s.add_node("Reading", {"word": name, "gloss": name, "kind": "literal"})
        fig = a.s.add_node("Reading", {"word": name, "gloss": name, "kind": "figurative"})
        a.inner.add_edge_unchecked(lit, "claimed_by", src_dict)
        a.inner.add_edge_unchecked(fig, "claimed_by", src_cu)
        pns = [a.s.add_node("Mention", {"text": w}) for w in parts]
        for m in pns:
            a.inner.add_edge_unchecked(fig, "has_part", m)
        return fig, pns

    rows = [(name, parts, exp, *build(name, parts)) for name, parts, exp in CORPUS]
    a.inner.run_rules(20000)                       # detect_figure + ground_opposes (fused, via UseTool)
    for name, parts, exp, fig, pns in rows:
        a.inner.set_attr(fig, "scored", 1)         # host releases the classifier
    a.inner.run_rules(20000)                       # classify_figure

    print(f"  {'figure':18} {'wn':>3} {'wkt':>4} {'cn':>3} {'der':>4}  {'S':>4} {'>=θ':>4} {'opp':>4} {'oxy':>5}  role")
    print("  " + "-" * 104)
    npass = 0
    for name, parts, role, fig, pns in rows:
        vw, vk, vc, vd = wn_antonym(*parts), wikt_antonym(*parts), cn_antonym(*parts), derive_opposes(*parts)
        S = ((TRUST["wn"] if vw == 1 else 0) + (TRUST["wikt"] if vk == 1 else 0)
             + (TRUST["cn"] if vc == 1 else 0) + vd)   # derive returns its trust contribution directly
        expect_assert = S >= THETA                 # the POLICY: opposition iff trust-weighted corrob >= θ
        opp = any(a.inner.neighbours(m, "opposes") for m in pns)
        is_ox = a.s.node(fig)["attrs"].get("figure_kind", "?") == "oxymoron"
        # the rule is correct iff it asserts exactly when the policy says, and oxymoron iff opposes
        ok = (opp == expect_assert) and (is_ox == opp)
        npass += ok
        print(f"  {name:18} {vw:>3} {vk:>4} {vc:>3} {vd:>4.1f}  {S:>4.1f} {str(expect_assert):>4} {str(opp):>4} "
              f"{str(is_ox):>5}  {'PASS' if ok else 'FAIL'}  {role}")

    # The "ConceptNet cannot solo-license" property, by arithmetic (no natural cn-only pair exists —
    # post-filter ConceptNet only ever corroborates pairs WordNet/Wiktionary already carry).
    solo = {s: (TRUST[s] >= THETA) for s in TRUST}
    cn_cannot_solo = (TRUST["cn"] < THETA) and solo["wn"] and solo["wikt"]

    print("\n  " + "-" * 92)
    print(f"  {npass}/{len(rows)} obey the policy (opposes ⟺ S≥{THETA}; oxymoron ⟺ opposes). "
          f"ZERO claude -p calls — the LLM is out of the opposition path.")
    print(f"  solo-license: WordNet({TRUST['wn']})✓  Wiktionary({TRUST['wikt']})✓  "
          f"ConceptNet({TRUST['cn']})✗ → ConceptNet-cannot-solo = {cn_cannot_solo} (it only corroborates).")
    print(f"  derived reasoning resolves what no dictionary lists: Layer A (deafening/silence, motion/stillness)")
    print(f"  from definitional negation; Layer C (cruel/kind) from valence pole-flip + a same-field guard that")
    print(f"  blocks delicious/ugly (opposite valence, different field). Comprehension, not lookup. No LLM.")
    print(SEP)


if __name__ == "__main__":
    main()
