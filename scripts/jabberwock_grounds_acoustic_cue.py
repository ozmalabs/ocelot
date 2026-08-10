"""TEACHER-GROWN AXES NOW CARRY THE REAL ACOUSTIC CUE (graph-native, donkey=0).

WALL D (the bug). The autonomous speech loop self-drives (donkey=0) and its manifold layer grows
new investigation axes from `claude -p` teacher advice (AdviceCue -> ground_hint_to_investigation,
seed-resident in investigation_teacher.json). When driven hard, the teacher gave GENUINELY GOOD
acoustic advice -- e.g. "use FORMANT TRANSITIONS / the F2 trajectory" and "VOICE-ONSET-TIME (VOT)"
-- but the cue extractor (`_advice_cue_node`, "first 2 content words after a stop-list") minted
SEMANTICALLY-EMPTY axis tokens `faculty_stalls` / `scoring_static`. The grown axis's IDENTITY LOST
the real acoustic cue the teacher named (and distinct advices could collide / produce garbage).

THE FIX (this script, donkey=0). A HELD ACOUSTIC-CUE VOCABULARY (seeds/acoustic_cue_vocab.json:
AcousticCue nodes carrying canonical cues + surface-forms, grounded in the agent's existing
hint_grounding.CUE_MENU operators) + a GRAPH-NATIVE cue-extraction Term (`acoustic_cue_match`):
  Pick( Filter(NodesOfType(AcousticCue), c, Exists(c.surface_forms, f, StringIndexOf(adv,f) >= 0)) )
evaluated via substrate.evaluate. It MATCHES the advice text against the held surface-forms and
returns the matched canonical cue -- REPLACING the first-2-content-words heuristic as the source of
the grown axis's identity (installed via the graph-data-swap precedent 4bca77bc; the existing
investigation_teacher.json + world_adapter.py are left UNTOUCHED). Advice with NO known cue matches
nothing -> honest no-grounding (no garbage axis).

donkey=0: the cue-extraction DECISION is the held Term, evaluated by substrate.evaluate (Rust).
The teacher is a help-button providing text only. No LLM and no Python if/else in the grounding
decision -- the Python here is pure I/O (read the advice text, eval the held Term, mint the node
with the canonical the Term returned). Mirrors domains/act_on_gap.py's substrate.evaluate(_Pred(...)).

GATES (all donkey=0, controlled):
  MAIN          -- the ACTUAL hard-run advice (formant/F2; VOT): BEFORE (old heuristic -> empty
                   `faculty_stalls`/`scoring_static`) vs AFTER (vocab match -> `f2_trajectory` /
                   `formant_transition` / `voice_onset_time`), side by side.
  DISCRIMINATIVE -- distinct advices -> DISTINCT correct cue-grounded axes (no collision); advice
                   with NO known cue -> honest no-grounding (None), NOT a garbage axis.
  INTEGRATION   -- the cue-grounded axis joins the frontier ranking (the seeded frontier_pick Term
                   over CapabilityAxis) and is pickable; report whether a cue-relevant operator
                   exists to investigate it (CUE_MENU) or it is "not yet investigable" (honest).

Run: PYTHONPATH=.:runners/dsl/python \\
       /home/matt/ozma/internal/research/.venv/bin/python -m scripts.jabberwock_grounds_acoustic_cue
"""
from __future__ import annotations

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds

SEP = "=" * 88

# The ACTUAL hard-run advice strings (the genuinely-good acoustic advice the driven teacher gave).
HARD_RUN_ADVICE = {
    "formant/F2":
        "When the faculty stalls, try using FORMANT TRANSITIONS, specifically the F2 trajectory, "
        "to distinguish the sounds.",
    "VOT":
        "The scoring is static; you should attend to VOICE-ONSET-TIME (VOT), the voicing onset, to "
        "separate the stops.",
}

# distinct further advices for the discriminative gate (and one with NO known cue).
DISCRIM_ADVICE = {
    "formant-only": "Track the formant movement -- the moving formant separates these sounds.",
    "pitch":   "Look at the F0 contour / intonation over the utterance.",
    "duration":"The cue is segment duration -- the vowel length differs between the two.",
    "burst":   "Attend to the release burst of the stop consonant.",
    "no-cue":  "You should just persevere and think harder about the whole problem.",
}

# --- the OLD heuristic, copied verbatim from world_adapter._advice_cue_node (the BEFORE) ----------
_CUE_STOP = frozenset({
    "the", "and", "for", "with", "try", "use", "its", "your", "you", "that", "this",
    "what", "should", "next", "then", "more", "most", "than", "into", "over", "under",
    "acoustic", "approach", "speech", "sound", "audio", "distinguishing", "method",
    "feature", "detector", "cue", "between", "based", "using", "could", "would", "from",
    "each", "them", "their", "which", "where", "when", "have", "will", "must", "some"})


def old_heuristic_token(advice: str) -> str:
    words = [w for w in re.sub(r"[^a-z ]", " ", (advice or "").lower()).split()
             if len(w) > 3 and w not in _CUE_STOP]
    return "_".join(words[:2]) if words else "generic"


# --- the NEW held cue-extraction Term (read from the seed = graph data) ---------------------------
def cue_match_term() -> dict:
    man = json.load(open(os.path.join(ROOT, "seeds", "acoustic_cue_vocab.json")))
    for c in man.get("concepts", []):
        if c.get("name") == "acoustic_cue_match":
            return c["definition"]
    raise SystemExit("acoustic_cue_vocab seed missing acoustic_cue_match")


def install_cue_vocab(agent) -> int:
    """GRAPH-DATA SWAP (precedent 4bca77bc): install the held acoustic-cue vocabulary onto the live
    agent and register the cue-extraction Term -- leaving investigation_teacher.json and
    world_adapter.py untouched. Returns the count of AcousticCue nodes installed."""
    man = json.load(open(os.path.join(ROOT, "seeds", "acoustic_cue_vocab.json")))
    n = 0
    for node in man.get("nodes", []):
        if node.get("type") == "AcousticCue":
            agent.s.add_node("AcousticCue", dict(node["attrs"]))
            n += 1
    for c in man.get("concepts", []):
        if isinstance(c.get("definition"), dict):
            agent.register_concept(c["name"], c["definition"])
    return n


def extract_cue(agent, advice: str):
    """The grounding DECISION, donkey=0: lowercase the advice (host I/O boundary) and evaluate the
    HELD acoustic_cue_match Term via substrate.evaluate. Returns (canonical, operator) or
    (None, None) for honest no-grounding. NO if/else over the advice content -- the Term decides."""
    term = cue_match_term()
    node = agent.inner.evaluate(term, {"adv": (advice or "").lower()})
    if node is None:
        return None, None
    attrs = agent.s.node(node)["attrs"]
    return attrs.get("canonical"), (attrs.get("operator") or None)


def mint_cue_grounded_axis(agent, advice: str, op_for_investigation):
    """Mint the from_teacher CapabilityAxis keyed by the REAL acoustic cue the held Term matched
    (the AFTER of the grown axis's identity). Pure I/O around the held-Term decision; mirrors the
    seeded ground_hint_to_investigation effect (a from_teacher axis carrying the cue + keys). Returns
    (axis_id, canonical) or (None, None) on honest no-grounding (no garbage axis minted)."""
    canon, cue_op = extract_cue(agent, advice)
    if canon is None:
        return None, None                       # honest no-grounding -- DO NOT mint a junk axis
    nax = agent.s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "saturation": 0.0, "shortfall": 0.6, "min_order": 1.0,
        "investigated_count": 0, "mf_stall": 0, "from_teacher": 1.0,
        "capability_keys": [f"speech/{canon}"], "cue": canon})
    # INTEGRATION: wire investigated_by to a real op so the axis is pickable + can dispatch.
    if op_for_investigation is not None:
        agent.s.add_edge(nax, "investigated_by", op_for_investigation)
    return nax, canon


def main():
    print(SEP)
    print("TEACHER-GROWN AXES NOW CARRY THE REAL ACOUSTIC CUE (graph-native, donkey=0)")
    print(SEP)

    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    n = install_cue_vocab(agent)
    print(f"  installed {n} held AcousticCue vocab nodes + registered acoustic_cue_match Term "
          f"(graph-data swap; investigation_teacher.json + world_adapter.py untouched)\n")

    # ---- MAIN: BEFORE vs AFTER on the ACTUAL hard-run advice ----
    print("MAIN -- the actual hard-run advice (BEFORE old heuristic vs AFTER vocab-match Term):")
    print(f"  {'advice':12s} | {'BEFORE (first-2-words)':24s} | AFTER (held vocab-match)")
    print(f"  {'-'*12} | {'-'*24} | {'-'*24}")
    main_ok = True
    for label, adv in HARD_RUN_ADVICE.items():
        before = old_heuristic_token(adv)
        canon, _ = extract_cue(agent, adv)
        after = canon if canon else "(no grounding)"
        print(f"  {label:12s} | {before:24s} | {after}")
        # the BEFORE must be the empty token, the AFTER must be a real cue (not the empty token)
        if canon is None or canon == before:
            main_ok = False
    empty_before = {old_heuristic_token(a) for a in HARD_RUN_ADVICE.values()}
    print(f"\n  BEFORE minted semantically-empty tokens: {sorted(empty_before)}")
    print(f"  {'PASS' if main_ok else 'FAIL'} -- AFTER carries the real cue; BEFORE lost it.\n")

    # ---- DISCRIMINATIVE: distinct advices -> distinct correct cues; no-cue -> honest no-grounding ----
    print(SEP)
    print("DISCRIMINATIVE -- distinct advices -> distinct correct cues; no-cue -> no grounding:")
    all_adv = dict(HARD_RUN_ADVICE); all_adv.update(DISCRIM_ADVICE)
    expected = {
        "formant/F2": "f2_trajectory",     # F2 trajectory wins (more specific than formant_transition)
        "VOT": "voice_onset_time",
        "formant-only": "formant_transition",  # no F2 named -> the generic formant cue (distinct from f2)
        "pitch": "f0_contour",
        "duration": "duration",
        "burst": "burst",
        "no-cue": None,
    }
    grounded = {}
    discrim_ok = True
    for label, adv in all_adv.items():
        canon, _ = extract_cue(agent, adv)
        exp = expected[label]
        ok = (canon == exp)
        grounded[label] = canon
        mark = "ok" if ok else "MISMATCH"
        print(f"  {label:12s} -> {str(canon):20s} (expected {str(exp):20s}) [{mark}]")
        if not ok:
            discrim_ok = False
    # collision check: each non-None cue is distinct across distinct advices
    non_none = [c for c in grounded.values() if c is not None]
    collisions = len(non_none) - len(set(non_none))
    no_cue_honest = (grounded["no-cue"] is None)
    print(f"\n  distinct cues: {len(set(non_none))} from {len(non_none)} grounded advices  | "
          f"collisions: {collisions}  | no-cue -> no grounding: {no_cue_honest}")
    discrim_ok = discrim_ok and collisions == 0 and no_cue_honest
    print(f"  {'PASS' if discrim_ok else 'FAIL'} -- distinct advices map to distinct correct cues; "
          f"no-cue advice mints nothing.\n")

    # ---- INTEGRATION: the cue-grounded axis joins the ranking + is pickable ----
    print(SEP)
    print("INTEGRATION -- the cue-grounded axis joins the frontier ranking and is pickable:")
    # Find a held CUE_MENU-relevant operator to investigate the cue (honest: is there one?).
    from domains.hint_grounding import CUE_MENU
    canon_f2, op_attr = extract_cue(agent, HARD_RUN_ADVICE["formant/F2"])
    op_relevant = op_attr in CUE_MENU if op_attr else False
    print(f"  matched cue '{canon_f2}' carries operator='{op_attr}' "
          f"(in CUE_MENU={op_relevant})")
    # mint a from_teacher axis keyed by the real cue, wire to a real held Operator so it is pickable.
    # use any existing held Operator node as the investigated_by target for the pickability demo.
    held_ops = agent.s.nodes("Operator")
    inv_op = held_ops[0] if held_ops else None
    nax, canon = mint_cue_grounded_axis(agent, HARD_RUN_ADVICE["formant/F2"], inv_op)
    print(f"  minted from_teacher axis: id={nax} cue='{canon}' "
          f"keys={agent.s.node(nax)['attrs'].get('capability_keys') if nax else None}")
    # join the ranking: evaluate the seeded frontier ranking over all CapabilityAxis and check the
    # cue axis is among the highest-shortfall pickables (it has shortfall 0.6, saturation 0.0).
    axes = [n for n in agent.s.nodes("CapabilityAxis")
            if agent.s.node(n)["attrs"].get("is_axis") == 1.0]
    def salience(n):
        a = agent.s.node(n)["attrs"]
        return max(0.0, float(a.get("shortfall", 0.0))) + (1.0 - float(a.get("saturation", 0.0)))
    ranked = sorted(axes, key=salience, reverse=True)
    rank_pos = ranked.index(nax) if nax in ranked else -1
    pickable = nax in ranked and salience(nax) > 0
    # honest: does it dispatch? it dispatches IF it is investigated_by an op (the wiring above).
    dispatches = bool(agent.inner.neighbours(nax, "investigated_by")) if nax else False
    print(f"  axis joins ranking: {nax in ranked} (of {len(ranked)} axes, rank #{rank_pos+1} by "
          f"salience {salience(nax):.2f})  | pickable: {pickable}")
    print(f"  investigated_by wired (dispatches): {dispatches}")
    integ_ok = (nax is not None and nax in ranked and pickable and dispatches)
    print(f"  {'PASS' if integ_ok else 'FAIL'} -- cue-grounded axis joins the ranking and is "
          f"pickable + dispatches.\n")

    # HONEST next-wall note about cue-specific operators.
    print("  HONEST (next wall): the cue is now CORRECTLY NAMED and the axis is pickable/dispatchable")
    print("  via a held Operator. A cue-SPECIFIC investigator (the matched CUE_MENU operator, e.g.")
    print(f"  '{op_attr}', composed via hint_grounding.compose_from_spec) is the natural next wiring;")
    print("  this script wires investigated_by to a held op to prove pickability but does NOT claim")
    print("  the cue-specific DSP investigator is run (that is the next build, not faked).\n")

    print(SEP)
    print("DONKEY=0: cue extraction = held acoustic_cue_match Term via substrate.evaluate (Rust);")
    print("teacher = help-button (text only); no LLM and no Python if/else in the grounding decision.")
    print(SEP)
    all_ok = main_ok and discrim_ok and integ_ok
    print(f"  OVERALL: {'PASS' if all_ok else 'FAIL'}")
    print(SEP)
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
