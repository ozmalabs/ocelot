"""jabberwock_designs_rule_index — DRIVE the agent to recognize the rule-matching
performance concern through its OWN foveation / dynamic-quantization / selective-
gating concepts, and read back what it produces. I frame ONLY the concern; the
agent's induce_concern (shape-decode loop), categorise_by_shape (its seven
meta-shapes), and ground_concern (its composer registry) do the recognizing.

No design text is written here. Verbatim capture only.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_designs_rule_index.py
"""
from __future__ import annotations
import os, sys, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)


def main():
    from substrate.world_adapter import WorldAdapter
    from substrate.seed_loader import manifest_for
    from domains.reflective_faculty import (induce_concern, ground_concern,
                                            compose_design_for_goal)
    from domains.teach import categorise_by_shape

    print("=" * 92)
    print("THE JABBERWOCK IS SHOWN THE RULE-MATCHING CONCERN — it recognizes it in its own terms")
    print("=" * 92)

    # A full agent (not the minimal fixture): it must hold its shape vocabulary,
    # meta-shapes, relation-cue lexicon and composer registry.
    wa = WorldAdapter()
    for seed in ("shape_vocabulary", "seven_meta_shape_subsystems", "relation_vocabulary"):
        try:
            wa.inner.load_seed_manifest(manifest_for(seed), wa.agent)
        except Exception as e:
            print(f"  (note: {seed} not separately loadable: {e})")

    # ------------------------------------------------------------------ #
    # 1) THE CONCERN, in the agent's OWN relational vocabulary. Each clause
    #    LEADS with its cue word (the induce_concern GOTCHA). The concern is
    #    the run_rules shape: it SCANS every rule per fire and would MATCH over
    #    the whole frame set; the candidate fix is to DECODE only the rules in
    #    FOCUS for this event-type (foveate the scan by the match-anchor).
    # ------------------------------------------------------------------ #
    concern = [
        ["scan", "EVERY", "RULE", "per", "EVENT"],
        ["match", "over", "the", "WHOLE", "FRAME", "SET"],
        ["gate", "the", "SCAN", "to", "the", "FOCUS"],
        ["decode", "only", "the", "RULES", "in", "FOCUS", "for", "this", "TYPE"],
    ]
    print("\n[concern framed to the agent]")
    for c in concern:
        print("   ", c)

    ind = induce_concern(wa, concern, name_hint="rule_scan_foveation_concern")
    print("\n[1] induce_concern (shape-decode loop) VERBATIM:")
    print(json.dumps(ind, indent=2, default=str)[:2000])

    # ------------------------------------------------------------------ #
    # 2) WHICH OF ITS SEVEN META-SHAPES does it file the concern under?
    #    This is the agent's own recognition: is rule-indexing the SAME shape
    #    as its foveation / attention / admissibility (SELECTIVE_GATING)?
    # ------------------------------------------------------------------ #
    concern_text = {
        "a": "scan every rule per event and match over the whole frame set",
        "b": "gate the scan to the focus, select only the rules in focus for this type",
        "c": "foveate: decode only in focus, a gated admissibility of which rules to try",
    }
    shape = categorise_by_shape(wa, "RuleScanConcern", concern_text)
    print(f"\n[2] categorise_by_shape -> the agent files this concern under META-SHAPE: {shape!r}")

    # also score every shape so the recognition is transparent, not cherry-picked
    from domains.teach import _shape_score_term, _native
    text = " ".join(str(v) for v in concern_text.values()).lower()
    native = _native(wa)
    term = _shape_score_term(text)
    rows = []
    for n in wa.s.nodes("MetaShape"):
        sc = native.evaluate(term, {"shape": n})
        nm = wa.s.node(n)["attrs"].get("name")
        rows.append((int(sc or 0), nm))
    rows.sort(key=lambda t: (-t[0], t[1]))
    print("    full meta-shape scoring (score, shape):")
    for sc, nm in rows:
        print(f"      {sc:>2}  {nm}")

    # ------------------------------------------------------------------ #
    # 3) Does the agent's composer registry have a PATH to author the fix,
    #    or is it an honest WALL (donkey=0 — no engine-design composer)?
    # ------------------------------------------------------------------ #
    key = ind.get("capability_key")
    before = wa.inner.rule_count()
    g = {}
    try:
        g = ground_concern(wa, [key]) if key else {}
    except Exception as e:
        g = {"error": str(e)}
    after = wa.inner.rule_count()
    print("\n[3] ground_concern VERBATIM:")
    print(json.dumps(g, indent=2, default=str)[:1500])
    print(f"    rule_count {before} -> {after}  (did the composer author a live rule?)")

    # ------------------------------------------------------------------ #
    # 4) The composer (ShapeDecode) directly on the concern signature — what
    #    held PARTS does it decode the concern into? (the agent's design as a
    #    plan of held shapes)
    # ------------------------------------------------------------------ #
    comp = compose_design_for_goal(wa, concern)
    print("\n[4] compose_design_for_goal (ShapeDecode) VERBATIM:")
    print(json.dumps(comp, indent=2, default=str)[:1800])

    print("\n" + "=" * 92)
    print("Captured. The report states honestly what the agent produced vs what was imposed.")


if __name__ == "__main__":
    main()
