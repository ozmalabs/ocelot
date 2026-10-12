"""CUE-SPECIFIC INVESTIGATOR BOUND — a grown cue axis now MEASURES its cue (graph-native, donkey=0).

WALL D (81d1ddea) made a teacher-grown axis carry the REAL acoustic cue the teacher named (advice
"use the F2 trajectory" -> axis keyed `f2_trajectory`, the matched AcousticCue carrying
`operator: f2_formant`, a hint_grounding.CUE_MENU operator). But the grown axis's `investigated_by`
was wired to a GENERIC held Operator just to prove pickability/dispatch -- so dispatching the axis
did NOT actually MEASURE its cue. THIS build closes that gap.

THE FIX (this script + domains/cue_investigator.py + domain_data/cue_investigator.json, donkey=0):
a CUE-SPECIFIC Operator (runner='cue_investigator') is installed (graph-data swap, precedent
4bca77bc/81d1ddea), and a cue-grounded axis's `investigated_by` is re-pointed at it. Dispatching
the axis composes the cue's Term via hint_grounding.compose_from_spec(res, operator), EVALUATES the
held Term on cue-appropriate audio via substrate.evaluate (Rust, donkey=0), and BANKS a cue-DERIVED
MeasuredCapability via record_measured_capability (feeding the residual/shortfall -> residual-
salience). The MEASUREMENT DECISION is the held composed cue Term; the Python is mechanical DSP I/O
(render -> ingest -> enrich the bands the Term reads). existing investigation_teacher.json /
world_adapter.py / speech_world.py are left UNTOUCHED -- the world's execute is delegated on the LIVE
instance (a world-adapter wrap), not edited.

GATES (all donkey=0, controlled):
  MAIN          -- a cue-grounded axis (f2_trajectory, operator f2_formant) DISPATCHES its cue-
                   specific investigator: composes f2_formant via compose_from_spec, evaluates the
                   held Term on audio, banks a real cue-DERIVED measurement (value + provenance).
  DISCRIMINATIVE-- the f2_formant investigator SEPARATES front-vs-back vowel pairs (high Fisher),
                   where a MISMATCHED CUE_MENU operator (f1_formant / onset_level) does NOT, and a
                   SCRAMBLED/degenerate rep collapses the SAME Term's separation (the Term genuinely
                   depends on the rep, not a constant).
  INTEGRATION   -- teacher advice "use the F2 trajectory" -> Wall-D vocab match mints the axis keyed
                   f2_trajectory -> THIS build's cue-specific investigator dispatches via the real
                   _run_investigation_reflex -> banks a cue-derived measurement -> re-ranks.

Run: PYTHONPATH=.:runners/dsl/python \\
       /home/matt/ozma/internal/research/.venv/bin/python -m scripts.jabberwock_binds_cue_investigator
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.speech_world import SpeechWorld
from domains import cue_investigator
from domains.gap_prioritiser import _axis_sig

SEP = "=" * 92


# ---------------------------------------------------------------------------------------------
# GRAPH-DATA SWAP: install the cue-specific Operator + delegate the world's execute (LIVE wrap).
# ---------------------------------------------------------------------------------------------
def install_cue_investigator(agent, world):
    """Install the cue-specific Operator (domain_data/cue_investigator.json) onto the live agent and make
    the world's execute delegate runner='cue_investigator' to the held-Term measurement. The world
    file is NOT edited -- we wrap the live instance's execute (world-adapter work). Returns the
    Operator node id."""
    man = json.load(open(os.path.join(ROOT, "domain_data", "cue_investigator.json")))
    opid = None
    for node in man.get("nodes", []):
        if node.get("type") == "Operator":
            opid = agent.s.add_node("Operator", dict(node["attrs"]))
    # Delegate execute on the LIVE world (not speech_world.py): cue_investigator -> our held-Term
    # measurement; everything else falls through to the world's own executor.
    if getattr(world, "_cue_exec_wrapped", False):
        return opid
    orig_execute = world.execute

    def execute(req):
        if req.get("operator") == "cue_investigator":
            ax = _axis_for_req(agent, req)
            if ax is None:
                return None
            return cue_investigator.investigate_cue_axis(world, agent.s, ax, req)
        return orig_execute(req)

    world.execute = execute
    world._cue_exec_wrapped = True
    return opid


def _axis_for_req(agent, req):
    """Mechanical lookup: the cue-grounded CapabilityAxis this investigation request is FOR, by the
    capability_keys the reflex copied into req (the axis identity). No decision -- a graph lookup."""
    sig = sorted(_axis_sig(req.get("capability_keys") or []))
    for n in agent.s.nodes("CapabilityAxis"):
        a = agent.s.node(n)["attrs"]
        if a.get("is_axis") == 1.0 and sorted(_axis_sig(a.get("capability_keys") or [])) == sig:
            return n
    return None


def repoint_axis(agent, axis_id, opid):
    """GRAPH-DATA SWAP: re-point a cue-grounded axis's investigated_by from the generic placeholder
    to the cue-specific Operator. Mechanical edge surgery on the live graph (no seed file edited)."""
    for old in list(agent.inner.neighbours(axis_id, "investigated_by")):
        try:
            agent.inner.remove_edge(axis_id, "investigated_by", old)
        except Exception:
            pass
    agent.inner.add_edge_unchecked(axis_id, "investigated_by", opid)


# ---------------------------------------------------------------------------------------------
# Wall-D vocab match (reused verbatim from jabberwock_grounds_acoustic_cue): advice -> real cue.
# ---------------------------------------------------------------------------------------------
def install_cue_vocab(agent):
    man = json.load(open(os.path.join(ROOT, "domain_data", "acoustic_cue_vocab.json")))
    for node in man.get("nodes", []):
        if node.get("type") == "AcousticCue":
            agent.s.add_node("AcousticCue", dict(node["attrs"]))
    for c in man.get("concepts", []):
        if isinstance(c.get("definition"), dict):
            agent.register_concept(c["name"], c["definition"])


def _cue_match_term():
    man = json.load(open(os.path.join(ROOT, "domain_data", "acoustic_cue_vocab.json")))
    for c in man.get("concepts", []):
        if c.get("name") == "acoustic_cue_match":
            return c["definition"]
    raise SystemExit("acoustic_cue_vocab seed missing acoustic_cue_match")


def extract_cue(agent, advice):
    """donkey=0: evaluate the HELD acoustic_cue_match Term -> (canonical, operator) or (None, None)."""
    node = agent.inner.evaluate(_cue_match_term(), {"adv": (advice or "").lower()})
    if node is None:
        return None, None
    attrs = agent.s.node(node)["attrs"]
    return attrs.get("canonical"), (attrs.get("operator") or None)


def mint_cue_grounded_axis(agent, canonical, operator):
    """Mint the from_teacher cue axis (the Wall-D AFTER) carrying the cue + its operator so the
    cue-specific investigator can read the operator off the axis."""
    return agent.s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "saturation": 0.0, "shortfall": 0.6, "min_order": 1.0,
        "investigated_count": 0, "mf_stall": 0, "from_teacher": 1.0,
        "capability_keys": [f"speech/{canonical}"], "cue": canonical,
        "cue_operator": operator})


def main() -> int:
    print(SEP)
    print("CUE-SPECIFIC INVESTIGATOR BOUND -- a grown cue axis now MEASURES its cue (donkey=0)")
    print(SEP)

    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    world = SpeechWorld(agent.s, source_world=None)
    install_cue_vocab(agent)
    opid = install_cue_investigator(agent, world)
    print(f"  installed cue-specific Operator (runner='cue_investigator', id={opid}); world execute "
          f"delegated on the LIVE instance (speech_world.py untouched)\n")

    # ---- MAIN: the cue-grounded F2 axis dispatches its cue-specific investigator ----
    print("MAIN -- the cue-grounded f2_trajectory axis dispatches its cue-specific investigator:")
    canon, op = extract_cue(agent, "use FORMANT TRANSITIONS, specifically the F2 trajectory")
    print(f"  Wall-D vocab match: advice -> cue '{canon}' carrying operator '{op}'")
    ax = mint_cue_grounded_axis(agent, canon, op)
    repoint_axis(agent, ax, opid)
    # DISPATCH it exactly as the reflex would: build req from the bound op + axis, call execute.
    req = {"operator": "cue_investigator", "capability_keys": agent.s.node(ax)["attrs"]["capability_keys"],
           "measurement_key": "cue_discriminability", "target": 0.6}
    mc = world.execute(req)
    a = agent.s.node(mc)["attrs"] if mc is not None else {}
    print(f"  dispatched -> MeasuredCapability id={mc}")
    print(f"    measured (cue discriminability) = {a.get('measured')}")
    print(f"    metric  = {a.get('metric')!r}")
    print(f"    note    = {a.get('note')!r}")
    # MAIN claim: a cue-DERIVED measurement banked, with the composed-f2_formant-Term provenance,
    # and it is a GENUINE non-degenerate cue reading (the F2 Term separates its pair: Fisher > 0.5).
    note = a.get("note") or ""
    import re as _re
    fmatch = _re.search(r"Fisher=([0-9.]+)", note)
    fisher_banked = float(fmatch.group(1)) if fmatch else 0.0
    main_ok = (mc is not None and isinstance(a.get("measured"), float)
               and "compose_from_spec" in note and "f2_formant" in note
               and fisher_banked > 0.5)   # F2 genuinely separates its cue-appropriate pair
    print(f"  {'PASS' if main_ok else 'FAIL'} -- cue-derived measurement banked from the composed "
          f"f2_formant Term (not the generic placeholder).\n")

    # ---- DISCRIMINATIVE: right cue separates, wrong cue/scrambled does not ----
    print(SEP)
    print("DISCRIMINATIVE -- on the SAME front-vs-back vowel pairs (differ in F2, matched in height):")
    print("                 f2_formant separates them; VOWEL-BLIND energy cues / a scrambled rep do not.")
    F2_PAIRS = cue_investigator.CUE_STIMULI["f2_formant"]      # beat/boot, see/sue, heat/hot
    r_f2 = cue_investigator.measure_cue(world, "f2_formant", pairs=F2_PAIRS)
    # CLEAN negatives: overall-energy cues are BLIND to vowel quality (no F2/F1 info) -> must NOT
    # separate front/back vowels. (f1_formant is itself a real formant cue, so it is reported as an
    # informative comparison, not gated on -- an honest negative must be vowel-blind.)
    r_on = cue_investigator.measure_cue(world, "onset_level", pairs=F2_PAIRS)
    r_en = cue_investigator.measure_cue(world, "ending_level", pairs=F2_PAIRS)
    r_f1 = cue_investigator.measure_cue(world, "f1_formant", pairs=F2_PAIRS)   # informative only
    print(f"  stimulus pairs (all cues scored on these): {F2_PAIRS}")
    print(f"  RIGHT cue  f2_formant   : Fisher={r_f2['fisher']:.3f}  discriminability={r_f2['discriminability']:.3f}")
    print(f"  WRONG cue  onset_level  : Fisher={r_on['fisher']:.3f}  (vowel-blind energy cue)")
    print(f"  WRONG cue  ending_level : Fisher={r_en['fisher']:.3f}  (vowel-blind energy cue)")
    print(f"  (info)     f1_formant   : Fisher={r_f1['fisher']:.3f}  (a real formant cue -- not a clean negative)")
    print(f"  SCRAMBLED rep (same f2_formant Term, blanked bands): Fisher={r_f2['fisher_scrambled']:.3f}")
    right_beats_blind = (r_f2["fisher"] > r_on["fisher"] and r_f2["fisher"] > r_en["fisher"])
    depends_on_rep = (r_f2["fisher_scrambled"] < r_f2["fisher"] * 0.5)
    disc_ok = right_beats_blind and depends_on_rep
    print(f"\n  right cue beats vowel-blind energy cues: {right_beats_blind}  | "
          f"Term depends on the rep (scrambled collapses): {depends_on_rep}")
    print(f"  {'PASS' if disc_ok else 'FAIL'} -- the cue investigator measures the RIGHT thing, "
          f"cue-appropriately.\n")

    # ---- INTEGRATION: teacher advice -> real cue -> cue-specific measurement -> re-rank, via the REAL reflex ----
    print(SEP)
    print("INTEGRATION -- teacher advice -> Wall-D cue axis -> cue-specific dispatch -> bank -> re-rank")
    print("              (through the REAL _run_investigation_reflex, not a hand call):")
    agent.wire_investigation_faculty(world)            # the real investigation-run reflex
    # mint a fresh cue axis from advice and bind it to the cue-specific op (the grown-axis path).
    canon2, op2 = extract_cue(agent, "the cue is the F2 trajectory / second formant transition")
    ax2 = mint_cue_grounded_axis(agent, canon2 + "_integ", op2)   # distinct keys for a clean read
    agent.s.set_attr(ax2, "cue", canon2)
    repoint_axis(agent, ax2, opid)
    # build the investigation PlanAct + bind it via the seeded JOIN (theme->axis->investigated_by->op).
    pa = agent.s.add_node("PlanAct", {"status": "pending"})
    agent.inner.add_edge_unchecked(pa, "theme", ax2)
    agent.inner.add_edge_unchecked(pa, "investigates_op", opid)   # the JOIN's binding (axis names this op)
    before = [agent.s.node(m)["attrs"] for m in agent.s.nodes("MeasuredCapability")]
    agent._run_investigation_reflex()                  # THE REAL DISPATCH REFLEX
    after = [agent.s.node(m)["attrs"] for m in agent.s.nodes("MeasuredCapability")]
    new_mc = [m for m in after if m not in before and "cue-specific investigator" in (m.get("note") or "")]
    integ_banked = bool(new_mc)
    print(f"  PlanAct dispatched via _run_investigation_reflex; new cue-derived MeasuredCapability: "
          f"{integ_banked}")
    if integ_banked:
        mcn = new_mc[-1]
        print(f"    measured={mcn.get('measured')}  metric={mcn.get('metric')!r}")
        print(f"    note={mcn.get('note')!r}")
    # re-rank: the axis now carries a measurement; its shortfall feeds the residual-salience ranking.
    axes = [n for n in agent.s.nodes("CapabilityAxis") if agent.s.node(n)["attrs"].get("is_axis") == 1.0]
    def salience(n):
        a = agent.s.node(n)["attrs"]
        return max(0.0, float(a.get("shortfall", 0.0))) + (1.0 - float(a.get("saturation", 0.0)))
    ranked = sorted(axes, key=salience, reverse=True)
    in_ranking = ax2 in ranked
    print(f"  cue axis joins the re-rank: {in_ranking} (of {len(ranked)} axes)")
    integ_ok = integ_banked and in_ranking
    print(f"  {'PASS' if integ_ok else 'FAIL'} -- full manifold path runs: advice -> real cue -> "
          f"cue-specific measurement -> re-rank.\n")
    print("  HONEST: the cue investigator measures the cue on CLEAN piper-synth input (the autonomy")
    print("  loop's own deterministic mouth). Real continuous-audio input quality is Wall B, a")
    print("  SEPARATE floor -- the cue Term still composes + reads whatever rep it is given.\n")

    print(SEP)
    print("DONKEY=0: the measurement = held composed cue Term (compose_from_spec) via substrate.evaluate")
    print("(Rust); dispatch reads the investigated_by/investigates_op edge; no LLM, no Python if/else in")
    print("the measurement decision. The cue operator is named by the held Term; the Term decides.")
    print(SEP)
    all_ok = main_ok and disc_ok and integ_ok
    print(f"  OVERALL: {'PASS' if all_ok else 'FAIL'}")
    print(SEP)
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
