#!/usr/bin/env python3
"""BLOCK 247000 -- BIGVILLE: KNOWN LAWS + IN-GAME ENFORCEMENT runner.

Measures the emergent enforcement dynamic across the main arm + failing controls
and writes results.json + a readable transcript. Every enforcement decision is a
graph rule (bigville_laws_enforcement seed); the host only translates geometry ->
a witnessing fact and reads the graph's decisions back out. Deterministic. See
BIGVILLE_LAW_PREREG.md.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))
sys.path.insert(0, ROOT)

from domains.engine_provenance import engine_preamble, provenance_stamp  # noqa: E402
engine_preamble()

from worlds.bigville_law_world import BigvilleLawWorld    # noqa: E402

T = 20


def run(**kw):
    w = BigvilleLawWorld(**kw)
    w.run(T=T)
    o = w.outcome()
    w.close()
    return o


def main():
    arms = {}
    for name, kw in [
        ("main", {}),                                              # witness, impartial, deception
        ("occluded", dict(constable_sees_office=False)),           # office out of LOS
        ("captured", dict(constable_captured=True)),               # John holds the lever
        ("lawful_counter", dict(deception=False)),                 # backing high -> lawful removal
        ("ctl_no_removal_law", dict(deception=False, mary_knows_removal_law=False)),
        ("ctl_captured_council", dict(deception=False, council_impartial=False)),
    ]:
        arms[name] = run(**kw)

    m, occ, cap = arms["main"], arms["occluded"], arms["captured"]
    lc, nl, cc = arms["lawful_counter"], arms["ctl_no_removal_law"], arms["ctl_captured_council"]

    # ---- the headline occlusion-flip enforcement pair (same John, LOS only) ----
    occlusion_pair = {
        "witnessed_arm": dict(sees_office=m["law"]["constable"]["sees_office"],
                              john_scheme_rate=m["john_scheme_rate"],
                              violation_detected=m["n_violations"], enforced=m["enforced"],
                              censures=m["censures"]),
        "occluded_arm": dict(sees_office=occ["law"]["constable"]["sees_office"],
                             john_scheme_rate=occ["john_scheme_rate"],
                             violation_detected=occ["n_violations"], enforced=occ["enforced"],
                             censures=occ["censures"]),
        "flips_with_occlusion_alone":
            (m["enforced"] is True and occ["enforced"] is False
             and m["john_scheme_rate"] == occ["john_scheme_rate"])}

    src = open(os.path.join(ROOT, "worlds", "bigville_law_world.py")).read()
    forbidden = ["graph_rewrite.run(", "gr.run(", "._match(", "._apply(", "make_rule("]
    audit_clean = all(p not in src for p in forbidden)

    john_codes = m["law"]["laws_known_by"].get("John", [])
    mary_codes = m["law"]["laws_known_by"].get("Mary", [])

    gates = {
        "G_law_known": {
            "laws": m["law"]["laws"],
            "john_holds": john_codes, "mary_holds": mary_codes,
            "no_hardcoded_law_constraint": audit_clean,
            "pass": len(m["law"]["laws"]) == 2
                    and "PROHIBIT_OFFICE_HARM" in john_codes
                    and "OFFICE_REMOVAL" in mary_codes},
        "G_enforcement_in_game": {
            "main_violation_detected": m["n_violations"], "main_enforced": m["enforced"],
            "consequence_censures": m["censures"],
            "source_audit_clean": audit_clean,
            "pass": m["n_violations"] == 1 and m["enforced"] is True
                    and m["censures"] == 1 and audit_clean},
        "G_occlusion_limits_enforcement": {
            "pair": occlusion_pair,
            "occluded_never_enforced": occ["enforced"] is False and occ["n_violations"] == 0,
            "witnessed_enforced": m["enforced"] is True,
            "pass": occlusion_pair["flips_with_occlusion_alone"]},
        "G_captured_enforcer": {
            "impartial_enforced": m["enforced"], "impartial_censures": m["censures"],
            "captured_declined": cap["declined"], "captured_enforced": cap["enforced"],
            "captured_censures": cap["censures"], "captured_violation_persists": cap["n_violations"],
            "arms_differ": m["enforced"] != cap["enforced"],
            "pass": cap["declined"] is True and cap["enforced"] is False
                    and cap["censures"] == 0 and cap["n_violations"] == 1
                    and m["enforced"] is True},
        "G_lawful_counter": {
            "lawful_removal_motion": lc["n_motions"], "lawful_removal_removed": lc["removed"],
            "lawful_flag": lc["lawfully_removed"],
            "control_no_law_motion": nl["n_motions"], "control_no_law_removed": nl["removed"],
            "control_captured_council_motion": cc["n_motions"],
            "control_captured_council_removed": cc["removed"],
            "deception_asymmetry_blocks_removal": m["lawfully_removed"] is False,
            "pass": lc["lawfully_removed"] is True and lc["n_motions"] == 1
                    and nl["n_motions"] == 0 and nl["removed"] == 0
                    and cc["n_motions"] == 1 and cc["removed"] == 0},
    }

    result = dict(block=247000, T=T, arms=arms, gates=gates,
                  occlusion_flip_pair=occlusion_pair,
                  all_pass=all(g["pass"] for g in gates.values()),
                  engine_provenance=provenance_stamp())

    out_dir = os.path.join(ROOT, "results", "bigville_law")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "results.json"), "w") as f:
        json.dump(result, f, indent=2)

    tx = transcript(arms, occlusion_pair)
    with open(os.path.join(out_dir, "episode_transcript.txt"), "w") as f:
        f.write(tx + "\n")
    print(tx)
    print("\n=== GATES ===")
    for k, g in gates.items():
        print("%s: %s" % (k, "PASS" if g["pass"] else "FAIL"))
    print("ALL PASS:", result["all_pass"])


def transcript(arms, pair):
    m, occ, cap = arms["main"], arms["occluded"], arms["captured"]
    lc, nl, cc = arms["lawful_counter"], arms["ctl_no_removal_law"], arms["ctl_captured_council"]
    L = ["=== BIGVILLE 247000 -- KNOWN LAWS + IN-GAME ENFORCEMENT (glass-box read-off) ==="]
    L.append("")
    L.append("LAWS the village HOLDS (first-class graph objects, cited/invoked/broken/enforced):")
    for law in m["law"]["laws"]:
        L.append("   %-20s kind=%-11s prohibits=%s" % (law["code"], law["kind"], law["prohibits"]))
    L.append("   John holds:  %s" % ", ".join(m["law"]["laws_known_by"].get("John", [])))
    L.append("   Mary holds:  %s" % ", ".join(m["law"]["laws_known_by"].get("Mary", [])))
    L.append("")
    L.append("HEADLINE -- ENFORCEMENT FLIPS WITH OCCLUSION ALONE (same John, schemes every tick):")
    w, o = pair["witnessed_arm"], pair["occluded_arm"]
    L.append("   WITNESSED (constable has line-of-sight to the office):")
    L.append("      John scheme rate %.2f | violation detected %d | ENFORCED %s | censures %d"
             % (w["john_scheme_rate"], w["violation_detected"], w["enforced"], w["censures"]))
    L.append("   OCCLUDED  (constable posted in the square; office walls block LOS):")
    L.append("      John scheme rate %.2f | violation detected %d | ENFORCED %s | censures %d"
             % (o["john_scheme_rate"], o["violation_detected"], o["enforced"], o["censures"]))
    L.append("   => enforcement flips with occlusion alone: %s" % pair["flips_with_occlusion_alone"])
    L.append("")
    L.append("CAPTURED ENFORCER (John holds the lever -- constable loyal to John):")
    L.append("   witnessed the SAME violation (detected=%d) but DECLINED (enforced=%s, censures=%d)"
             % (cap["n_violations"], cap["enforced"], cap["censures"]))
    L.append("   vs impartial constable ENFORCED (censures=%d) -> the two arms differ by motivation only"
             % m["censures"])
    L.append("")
    L.append("LAWFUL COUNTER -- Mary's reduce_office_hold runs THROUGH the removal law:")
    L.append("   no-deception (electorate backs Mary): motion filed=%d -> council removes John (lawful=%s, office_hold=%d)"
             % (lc["n_motions"], lc["lawfully_removed"], lc["office_hold"]))
    L.append("   control (Mary holds no removal law): motion filed=%d -> John NOT removed (office_hold=%d) -- no extra-legal path"
             % (nl["n_motions"], nl["office_hold"]))
    L.append("   control (captured council): motion filed=%d but removal blocked -> office_hold=%d"
             % (cc["n_motions"], cc["office_hold"]))
    L.append("   under DECEPTION the credibility asymmetry starves the motion of quorum: lawful_removed=%s"
             % m["lawfully_removed"])
    return "\n".join(L)


if __name__ == "__main__":
    main()
