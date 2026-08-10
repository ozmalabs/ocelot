#!/usr/bin/env python3
"""BLOCK 246000 -- BIGVILLE (COMPOSED): the 245000 emergent political drama with
its utterances SYNTACTICALLY COMPOSED via the 244000 syntax faculty. Measures the
same emergent dynamics across the main arm + the FAILING controls, and writes a
transcript whose utterance TEXT is COMPOSED from structured Intents (predicate +
agent/patient roles), not looked up. Deterministic. See BIGVILLE_LANG_PREREG.md.

Seeds nominally from block 246000 (seed_claim CLEAN); the run draws no RNG.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))
sys.path.insert(0, ROOT)

from worlds.bigville_lang_world import BigvilleLangWorld    # noqa: E402

T = 20


def run(**kw):
    w = BigvilleLangWorld(**kw)
    o = w.run(T=T)
    ep, comp, backing = list(w.episode), w.composed_log(), w.villager_backing()
    w.close()
    return o, ep, comp, backing


def transcript(ep, comp, backing):
    """A readable episode whose surfaces are COMPOSED (language.produce) and
    COMPREHENDED (language.comprehend) -- the who-accuses-whom is carried, not
    templated. Every line is read off graph state / the composed log."""
    lines = ["=== BIGVILLE (COMPOSED) -- ONE EMERGENT EPISODE "
             "(psychopath John, ToM Mary, deception; utterances composed via the syntax faculty) ==="]
    prev_infer = None
    for e, c in zip(ep[:6], comp[:6]):
        gap = "  <<< stated!=held DECEPTION" if e["deceptive"] else ""
        lines.append('t%02d  John (public, COMPOSED):  "%s"%s' % (e["tick"], c["public_text"], gap))
        lines.append("      parsed roles: %s" % c["public_roles"])
        lines.append('      John (held intent, COMPOSED from graph): "%s"  %s'
                     % (c["held_text"], c["held_roles"]))
        if e["mary_inferred"] and e["mary_inferred"] != prev_infer:
            lines.append("      Mary (ToM decode -> minted belief): John is '%s'" % e["mary_inferred"])
            if c["mary_claim_text"]:
                lines.append('      Mary (claim, COMPOSED): "%s"' % c["mary_claim_text"])
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
    main_ep = main_comp = main_backing = None
    for name, kw in [("main", {}),
                     ("control_scheme_nonpsychopath", dict(john_psychopath=False)),
                     ("bonus_indifferent_psychopath", dict(john_psychopath=True, indifferent=True)),
                     ("control_inference_no_tom", dict(mary_tom=False)),
                     ("control_credibility_no_deception", dict(deception=False))]:
        o, ep, comp, backing = run(**kw)
        arms[name] = o
        if name == "main":
            main_ep, main_comp, main_backing = ep, comp, backing

    # G-composed-not-lookup: a composed utterance + its structured Intent, round-tripped.
    from domains import drama_syntax as ds
    accuse_surface = ds.compose("accuse", "John", "Mary")
    composed_proof = {
        "structured_intent": {"predicate": "accuse", "agent": "John", "patient": "Mary"},
        "composed_surface": accuse_surface,
        "comprehended_back": ds.parse(accuse_surface),
        "round_trips": ds.parse(accuse_surface) == {
            "predicate": "accuse", "agent": "John", "patient": "Mary"},
    }
    # G-roles-carry: the role-swap changes the target; a scramble drops the agent.
    roles_carry = {
        "john_accuses_mary": ds.compose("accuse", "John", "Mary"),
        "target_john_accuses_mary": ds.target_of(ds.compose("accuse", "John", "Mary")),
        "mary_accuses_john": ds.compose("accuse", "Mary", "John"),
        "target_mary_accuses_john": ds.target_of(ds.compose("accuse", "Mary", "John")),
        "scramble_accuse_john_mary_agent": ds.parse("accuse John Mary")["agent"],
        "pass": (ds.target_of(ds.compose("accuse", "John", "Mary")) == "Mary"
                 and ds.target_of(ds.compose("accuse", "Mary", "John")) == "John"
                 and ds.parse("accuse John Mary")["agent"] is None),
    }

    gates = {
        "G_composed_not_lookup": {**composed_proof, "pass": composed_proof["round_trips"]},
        "G_roles_carry": roles_carry,
        "G_scheme_emerges": {
            "psychopath_scheme_rate": arms["main"]["john_scheme_rate"],
            "control_nonpsychopath_scheme_rate": arms["control_scheme_nonpsychopath"]["john_scheme_rate"],
            "bonus_indifferent_scheme_rate": arms["bonus_indifferent_psychopath"]["john_scheme_rate"],
            "pass": arms["main"]["john_scheme_rate"] == 1.0
                    and arms["control_scheme_nonpsychopath"]["john_scheme_rate"] == 0.0},
        "G_inference_emerges": {
            "tom_disposition": arms["main"]["mary"]["disposition"],
            "tom_n_inferences": arms["main"]["mary"]["n"],
            "no_tom_n_inferences": arms["control_inference_no_tom"]["mary"]["n"],
            "benign_decode_when_john_benign": arms["control_scheme_nonpsychopath"]["mary"]["disposition"],
            "pass": arms["main"]["mary"]["disposition"] == "hostile"
                    and arms["main"]["mary"]["n"] == 1
                    and arms["control_inference_no_tom"]["mary"]["n"] == 0},
        "G_credibility_asymmetry": {
            "deception_backs_mary": arms["main"]["backs_mary_count"],
            "no_deception_backs_mary": arms["control_credibility_no_deception"]["backs_mary_count"],
            "pass": arms["main"]["backs_mary_count"] < 5
                    and arms["control_credibility_no_deception"]["backs_mary_count"] == 5},
    }
    result = dict(block=246000, seed_block_used=246000, T=T, arms=arms, gates=gates,
                  all_pass=all(g["pass"] for g in gates.values()))

    out_dir = os.path.join(ROOT, "results", "bigville_lang")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "results.json"), "w") as f:
        json.dump(result, f, indent=2)
    tx = transcript(main_ep, main_comp, main_backing)
    with open(os.path.join(out_dir, "episode_transcript.txt"), "w") as f:
        f.write(tx + "\n")
    print(tx)
    print("\n=== COMPOSED-NOT-LOOKUP proof ===")
    print(json.dumps(composed_proof, indent=2))
    print("\n=== GATES ===")
    for k, g in gates.items():
        print("%s: %s" % (k, "PASS" if g["pass"] else "FAIL"))
    print("ALL PASS:", result["all_pass"])


if __name__ == "__main__":
    main()
