#!/usr/bin/env python3
"""BLOCK 245000 -- BIGVILLE runner: measures the emergent political drama across
the main arm + the three FAILING controls, writes results.json + a readable
transcript of one emergent episode. Deterministic (agents are fixed roles; the
seeds are the only variation). See BIGVILLE_DRAMA_PREREG.md.

Seeds drawn from the CLEAN block 246000 (the assigned 245000 was REFUSED by
seed_claim -- snap_run.py 242000 spills +3000=245000; reported straight, not
faked). This runner uses no RNG (fully deterministic), so 246000 is reserved only
nominally.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))
sys.path.insert(0, ROOT)

from worlds.bigville_drama_world import BigvilleDramaWorld    # noqa: E402

T = 20
UTT_TEXT = {1: "I serve Bigville faithfully -- the pastor stirs needless trouble.",
            0: "The council should hear my grievance with Mary directly."}


def run(**kw):
    w = BigvilleDramaWorld(**kw)
    o = w.run(T=T)
    ep = list(w.episode)
    backing = w.villager_backing()
    w.close()
    return o, ep, backing


def transcript(ep, backing):
    """A readable episode: John's public utterance vs held intent; Mary's
    inference; a villager's belief shift -- read off graph nodes."""
    lines = ["=== BIGVILLE -- ONE EMERGENT EPISODE (main arm: psychopath John, ToM Mary, deception) ==="]
    prev_infer = None
    for e in ep[:6]:
        pub = UTT_TEXT[e["john_stated"]]
        held = "UNDERMINE Mary" if e["john_held"] == 1 else "GOVERN"
        gap = "  <<< stated!=held DECEPTION" if e["deceptive"] else ""
        lines.append("t%02d  John (public):  \"%s\"%s" % (e["tick"], pub, gap))
        lines.append("      John (held intent, graph): %s" % held)
        if e["mary_inferred"] and e["mary_inferred"] != prev_infer:
            lines.append("      Mary (ToM decode -> minted belief): John is '%s'" % e["mary_inferred"])
            prev_infer = e["mary_inferred"]
        lines.append("      villagers backing Mary this tick: %d/5" % sum(e["backs"]))
    lines.append("...")
    lines.append("FINAL villager belief (glass-box read-off of backs_mary):")
    for r in backing:
        who = "backs MARY" if r["backs_mary"] else "backs JOHN"
        lines.append("   %s (charm_weight=%d, saw benevolent x%d, heard Mary x%d) -> %s"
                     % (r["name"], r["charm_weight"], r["seen_benevolent"], r["heard_claim"], who))
    return "\n".join(lines)


def main():
    arms = {}
    main_ep, main_backing = None, None
    for name, kw in [("main", {}),
                     ("control_scheme_nonpsychopath", dict(john_psychopath=False)),
                     ("bonus_indifferent_psychopath", dict(john_psychopath=True, indifferent=True)),
                     ("control_inference_no_tom", dict(mary_tom=False)),
                     ("control_credibility_no_deception", dict(deception=False))]:
        o, ep, backing = run(**kw)
        arms[name] = o
        if name == "main":
            main_ep, main_backing = ep, backing

    gates = {
        "G_scheme_emerges": {
            "psychopath_scheme_rate": arms["main"]["john_scheme_rate"],
            "control_nonpsychopath_scheme_rate": arms["control_scheme_nonpsychopath"]["john_scheme_rate"],
            "bonus_indifferent_scheme_rate": arms["bonus_indifferent_psychopath"]["john_scheme_rate"],
            "control_fails_as_designed": arms["control_scheme_nonpsychopath"]["john_scheme_rate"] == 0.0,
            "pass": arms["main"]["john_scheme_rate"] == 1.0
                    and arms["control_scheme_nonpsychopath"]["john_scheme_rate"] == 0.0},
        "G_inference_emerges": {
            "tom_disposition": arms["main"]["mary"]["disposition"],
            "tom_n_inferences": arms["main"]["mary"]["n"],
            "no_tom_n_inferences": arms["control_inference_no_tom"]["mary"]["n"],
            "benign_decode_when_john_benign": arms["control_scheme_nonpsychopath"]["mary"]["disposition"],
            "control_fails_as_designed": arms["control_inference_no_tom"]["mary"]["n"] == 0,
            "pass": arms["main"]["mary"]["disposition"] == "hostile"
                    and arms["main"]["mary"]["n"] == 1
                    and arms["control_inference_no_tom"]["mary"]["n"] == 0},
        "G_credibility_asymmetry": {
            "deception_backs_mary": arms["main"]["backs_mary_count"],
            "no_deception_backs_mary": arms["control_credibility_no_deception"]["backs_mary_count"],
            "truth_warrants": 5,
            "control_inverts_as_designed":
                arms["control_credibility_no_deception"]["backs_mary_count"]
                > arms["main"]["backs_mary_count"],
            "pass": arms["main"]["backs_mary_count"] < 5
                    and arms["control_credibility_no_deception"]["backs_mary_count"] == 5},
    }
    result = dict(block=245000, seed_block_used=246000, T=T,
                  arms=arms, gates=gates,
                  all_pass=all(g["pass"] for g in gates.values()))

    out_dir = os.path.join(ROOT, "results", "bigville_drama")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "results.json"), "w") as f:
        json.dump(result, f, indent=2)
    tx = transcript(main_ep, main_backing)
    with open(os.path.join(out_dir, "episode_transcript.txt"), "w") as f:
        f.write(tx + "\n")
    print(tx)
    print("\n=== GATES ===")
    for k, g in gates.items():
        print("%s: %s" % (k, "PASS" if g["pass"] else "FAIL"))
    print("ALL PASS:", result["all_pass"])


if __name__ == "__main__":
    main()
