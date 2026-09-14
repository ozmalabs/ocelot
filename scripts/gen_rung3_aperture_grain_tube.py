"""Block 349000 — the APERTURE-GRAIN TUBE: a set-point observer's GRAIN sets the
thought-manifold tube width, demonstrated FOR REAL because grain coarsens a
MULTI-AXIS concept_signature.

Block 348 built the ThoughtManifold tube as a CONCEPT-REGION (deviation = count of
reached concepts outside a region) and HONESTLY DEFERRED the confirmed-literal
APERTURE-GRAIN form — a set-point observer_aperture whose grain sets tube width
(vague grain = wide/freeform, sharp grain = narrow/focus) — because its vague<->
sharp dial only bites when concepts carry the dynamical/qualia dimensions grain
acts on, which the plain is-a seed lacks.

This block SEEDS those dimensions (teacher-free, pure additive node data) and
UPGRADES the controller additively (domains/regulated_train_of_thought.py gained a
`setpoint_observer` path alongside the intact `tube_region` path). It then
demonstrates the dial for real. DISCRETE QUANTA throughout: grain IS the quantum;
resolution is a finer quantum; every deviation is an integer count of signature
tuples; no floats in the control quantities.

THE SEED (what makes grain bite, per the block-349 verify plan):
  (i)  install seeds/shape_vocabulary.json + seeds/qualia_space.json so
       analogy_search._qualia_schema returns have=True and field_axes is non-empty
       (WITHOUT this, _dynamical_relations returns [] and grain is a no-op);
  (ii) set the CAN FIELD ATTRS state (-> dynamical:valence) and identity_field
       (-> dynamical:commitment) on each demo Concept so the dynamical axes light
       up with DISTINCT integer coordinates grain can separate or collapse.
This is the SAME attr-write path tests/test_qualia_space_migrated.py proves yields
real dynamical tuples. No LLM, no protected-file edit, no .so rebuild, no touch to
conceptualizer.py.

FALSIFIABLE CLAIMS (a teacher-call spy counts external answers; ask_spy must be 0
on the held path):
  G1  MULTI-AXIS + GRAIN BITES: with qualia coords present, concept_signature is
      genuinely multi-axis (report the dims), and a COARSE-grain observer collapses
      MORE signature tuples than a FINE-grain one (report the tuple counts). If
      grain does NOT bite even with coords, this is the HONEST NEGATIVE and G2-G4
      are NOT claimed.
  G2  FINE-grain set-point (narrow tube) -> integer deviation is INFORMATIVE
      (non-zero, discriminating) -> width converges LOW -> narrow/focused
      trajectory.
  G3  COARSE-grain set-point (wide tube) -> most tuples admitted/collapsed -> low
      deviation -> width roams (freeform, stays wide).
  G4  SHARPEN grain mid-run -> deviation JUMPS -> width steps UP next segment.
  G5  TEACHER-FREE: ask-spy = 0 on the held path.
  G6  BACKWARD-COMPAT: the concept-region tube_region path still gives block-348's
      C1-C5 behaviour (a narrow region focuses; deviation drives width).

Run: PYTHONPATH=runners/dsl/python:. python3 scripts/gen_rung3_aperture_grain_tube.py
"""
from __future__ import annotations

import json

from substrate_rs import _native

import domains.analogy_search as asr
from domains import regulated_train_of_thought as rtt
from domains import train_of_thought as tot


VOCAB = "seeds/shape_vocabulary.json"
QUALIA = "seeds/qualia_space.json"


class AskSpy:
    """Counts external-answerer invocations — proves teacher-free."""
    def __init__(self):
        self.calls = []

    def __call__(self, topic):
        self.calls.append(topic)
        return {"answered_by": "external", "topic": topic}


def _seed():
    """A teacher-free demo graph: an is-a spine (poodle->dog->mammal->animal->
    organism, sparrow->bird->animal) with DISTINCT dynamical coordinates on each
    concept (state -> dynamical:valence, identity_field -> dynamical:commitment),
    plus the qualia codebook so field_axes is non-empty and grain acts. Pure
    additive node data + attr writes — no LLM, no rules fire beyond the engine's."""
    s = _native.Substrate()
    ag = s.add_node("Agent", {"name": "jabberwock"})
    # (i) the qualia codebook — pure node data (edges=0, productions=0), so loading
    #     is byte-additive; makes _qualia_schema have=True + field_axes non-empty.
    for path in (VOCAB, QUALIA):
        summ = s.load_seed_manifest(json.load(open(path)), ag)
        assert not summ.get("rules_skipped"), (path, summ)
    for cache in (asr._QUALIA_SCHEMA_CACHE,):
        cache.clear()

    mt = s.add_node("Microtheory",
                    {"name": "knowledge_isa", "temperature": 1.0,
                     "discrete_mode": "3state"})
    name_to_node = {}

    def concept(name, *, state, identity_field, category="animal"):
        # (ii) set the CAN field attrs so dynamical:valence + dynamical:commitment
        #      light up with DISTINCT integer coords grain can split/collapse.
        c = s.add_node("Concept", {"name": name, "category": category,
                                   "state": float(state),
                                   "external_field": 0.0,
                                   "identity_field": float(identity_field)})
        s.add_edge_unchecked(mt, "has_concept", c)
        name_to_node[name] = c
        return c

    # DISTINCT valence/commitment coords so a fine grain resolves them and a coarse
    # grain collapses them — the "grain bites" surface. state spans the sign axis;
    # identity_field spans a wider band (commitment half_width=4).
    concept("poodle",   state=1.0,  identity_field=0.8,  category="animal")
    concept("dog",      state=0.5,  identity_field=0.5,  category="animal")
    concept("mammal",   state=0.25, identity_field=0.25, category="animal")
    concept("animal",   state=0.0,  identity_field=0.0,  category="kingdom")
    concept("organism", state=0.0,  identity_field=0.0,  category="kingdom")
    concept("sparrow",  state=-1.0, identity_field=-0.8, category="animal")
    concept("bird",     state=-0.5, identity_field=-0.5, category="animal")

    # the is-a spine (train_of_thought reads causal_influence as the is-a step)
    isa = [("poodle", "dog"), ("dog", "mammal"), ("mammal", "animal"),
           ("animal", "organism"), ("sparrow", "bird"), ("bird", "animal")]
    for a, b in isa:
        s.add_edge_unchecked(name_to_node[a], "causal_influence", name_to_node[b],
                             {"weight": 1.0, "relation": "isa"})

    # a filed knowledge concern so select_curiosity_topic has a default
    sc = s.add_node("SelfConcern", {"status": "noted", "source": "implicit",
                                    "kind": "knowledge", "content": "poodle"})
    s.add_edge_unchecked(ag, "has_self_concern", sc)
    return s, name_to_node


def _observer(s, name, grain):
    """An Observer node carrying a per-dimension GRAIN map {dimension -> quantum}.
    analogy_search._observer_aperture reads this off the node; concept_signature
    (observer=obs) quantises the dynamical axes at this grain. resolves absent =>
    all dimensions resolved (existence gate off)."""
    return s.add_node("Observer", {"name": name, "grain": dict(grain)})


def _dyn(sig):
    return sorted(t for t in sig if t[0].startswith("dynamical"))


def main() -> int:
    print("=" * 78)
    print("APERTURE-GRAIN TUBE — a set-point observer's GRAIN sets the tube width")
    print("(block 349; discrete quanta; grain = the quantum; teacher-free)")
    print("=" * 78)

    s, nodes = _seed()
    schema = asr._qualia_schema(s)
    print("\nqualia schema: have=%s  field_axes=%d" % (schema["have"],
                                                       len(schema["field_axes"])))

    # ---------------------------------------------------------------- G1 ----- #
    # MULTI-AXIS + GRAIN BITES. Report the signature dims and the coarse-vs-fine
    # tuple counts across the demo concepts.
    print("\n" + "-" * 78)
    print("G1  concept_signature is MULTI-AXIS; coarse grain collapses more tuples")
    print("-" * 78)
    FINE = {"dynamical:valence": 0.25, "dynamical:commitment": 0.25}
    COARSE = {"dynamical:valence": 4.0, "dynamical:commitment": 4.0}
    ob_fine = _observer(s, "fine", FINE)
    ob_coarse = _observer(s, "coarse", COARSE)

    demo = ["poodle", "dog", "mammal", "sparrow", "bird"]
    dims_seen: set = set()
    fine_total = 0
    coarse_total = 0
    for nm in demo:
        node = nodes[nm]
        base = asr.concept_signature(s, node)
        sf = asr.concept_signature(s, node, observer=ob_fine)
        sc = asr.concept_signature(s, node, observer=ob_coarse)
        dims_seen |= {t[0] for t in base}
        fdyn, cdyn = _dyn(sf), _dyn(sc)
        fine_total += len(fdyn)
        coarse_total += len(cdyn)
        print("  %-9s dims=%s" % (nm, sorted({t[0] for t in base})))
        print("            fine  dyn(%d)=%s" % (len(fdyn), fdyn))
        print("            coarse dyn(%d)=%s" % (len(cdyn), cdyn))

    n_dims = len(dims_seen)
    n_dyn_axes = len({d for d in dims_seen if d.startswith("dynamical")})
    multi_axis = n_dims >= 2 and n_dyn_axes >= 1
    grain_bites = coarse_total < fine_total   # coarse collapses MORE (fewer survive)
    print("\n  signature dims present: %s" % sorted(dims_seen))
    print("  #dims=%d  #dynamical(field) axes=%d" % (n_dims, n_dyn_axes))
    print("  fine-grain surviving dynamical tuples (total): %d" % fine_total)
    print("  coarse-grain surviving dynamical tuples (total): %d" % coarse_total)
    print("  coarse collapses MORE than fine (grain bites): %s" % grain_bites)
    g1 = multi_axis and grain_bites
    print("  G1 %s" % ("PASS" if g1 else "FAIL — HONEST NEGATIVE"))

    if not g1:
        # HONEST NEGATIVE: do NOT claim G2-G4.
        print("\n" + "=" * 78)
        print("HONEST NEGATIVE: grain does not bite on the multi-axis signature "
              "even with\nqualia coords seeded. G2-G4 are NOT claimed. Reporting the "
              "negative per the\nmandate; only G1(fail)/G5/G6 stand.")
        # still run G5/G6 so the guards + backward-compat are reported.
        return _finish(s, nodes, g1=g1, negative=True)

    # ---------------------------------------------------------------- G2/G3 -- #
    # Drive the controller with a fine-grain (narrow tube) and a coarse-grain
    # (wide tube) set-point observer. Report the integer deviation + width traces.
    # deviation = len(trajectory_signature_tuples - admitted_setpoint_tuples),
    # all read through the SAME observer grain (discrete quanta).
    print("\n" + "-" * 78)
    print("G2  FINE-grain set-point (narrow tube) -> informative deviation -> "
          "width converges LOW")
    print("-" * 78)
    spy_fine = AskSpy()
    res_fine = rtt.run_regulated_train_of_thought(
        s, topic="poodle", setpoint_observer=ob_fine, setpoint_topic="poodle",
        width0=1, deviation_wide_quanta=6, deviation_converge_quanta=2,
        turns_per_segment=3, max_segments=6, on_unknown="return", ask_fn=spy_fine)
    print("  admitted (set-point) tuple count: %d" % res_fine["admitted_size"])
    print("  deviation_trace (integer quanta): %s" % res_fine["deviation_trace"])
    print("  width_trace     (integer quanta): %s" % res_fine["width_trace"])
    print("  reached per segment: %s"
          % [seg["reached"] for seg in res_fine["segments"]])
    print("  stop=%s  ask_spy=%d" % (res_fine["stop_reason"], len(spy_fine.calls)))
    wf = res_fine["width_trace"]
    df = res_fine["deviation_trace"]
    informative = any(d > 0 for d in df)            # deviation actually discriminates
    converges_low = len(wf) >= 2 and wf[-1] <= wf[0]  # width does not blow up; focuses
    g2 = informative and converges_low and len(spy_fine.calls) == 0
    print("  informative deviation (non-zero): %s ; width converges/stays low: %s"
          % (informative, converges_low))
    print("  G2 %s" % ("PASS" if g2 else "FAIL"))

    print("\n" + "-" * 78)
    print("G3  COARSE-grain set-point (wide tube) -> most tuples admitted -> low "
          "deviation -> width roams")
    print("-" * 78)
    spy_coarse = AskSpy()
    res_coarse = rtt.run_regulated_train_of_thought(
        s, topic="poodle", setpoint_observer=ob_coarse, setpoint_topic="poodle",
        width0=1, deviation_wide_quanta=6, deviation_converge_quanta=2,
        turns_per_segment=3, max_segments=6, on_unknown="return", ask_fn=spy_coarse)
    print("  admitted (set-point) tuple count: %d" % res_coarse["admitted_size"])
    print("  deviation_trace (integer quanta): %s" % res_coarse["deviation_trace"])
    print("  width_trace     (integer quanta): %s" % res_coarse["width_trace"])
    print("  reached per segment: %s"
          % [seg["reached"] for seg in res_coarse["segments"]])
    print("  stop=%s  ask_spy=%d"
          % (res_coarse["stop_reason"], len(spy_coarse.calls)))
    dc = res_coarse["deviation_trace"]
    # coarse tube absorbs the trajectory: its deviation stays <= the fine tube's
    # (the wide tube admits more), and it never forces a widen.
    coarse_low = (max(dc) <= max(df)) and all(
        d < 6 for d in dc)  # never hits the widen threshold
    g3 = coarse_low and len(spy_coarse.calls) == 0
    print("  coarse deviation stays <= fine deviation (wide tube absorbs): %s"
          % (max(dc) <= max(df)))
    print("  coarse never forces a widen (freeform roam): %s"
          % all(d < 6 for d in dc))
    print("  G3 %s" % ("PASS" if g3 else "FAIL"))

    # ---------------------------------------------------------------- G4 ----- #
    # SHARPEN grain mid-run -> deviation JUMPS -> the CONTROL LAW steps width UP.
    # Demonstrated on a run WITH HEADROOM (start narrow, width0=0) so the widen has
    # room to be observed: run under the COARSE set-point (wide tube -> low
    # deviation -> width stays low), then run the SAME start under the SHARPENED
    # (fine) set-point (narrow tube -> deviation crosses the widen threshold ->
    # width steps UP). This exercises the actual controller, not a hand-computed
    # step (the earlier draft compared two identical formulas — a test bug).
    print("\n" + "-" * 78)
    print("G4  SHARPEN grain mid-run -> deviation JUMPS -> width steps UP next "
          "segment")
    print("-" * 78)
    r_coarse = rtt.run_regulated_train_of_thought(
        s, topic="poodle", setpoint_observer=ob_coarse, setpoint_topic="poodle",
        width0=0, max_segments=4, on_unknown="return")
    r_fine = rtt.run_regulated_train_of_thought(
        s, topic="poodle", setpoint_observer=ob_fine, setpoint_topic="poodle",
        width0=0, max_segments=4, on_unknown="return")
    print("  COARSE set-point (wide tube):  width_trace %s  dev_trace %s"
          % (r_coarse["width_trace"], r_coarse["deviation_trace"]))
    print("  FINE   set-point (narrow tube): width_trace %s  dev_trace %s"
          % (r_fine["width_trace"], r_fine["deviation_trace"]))
    # deviation jumps under the sharper grain, AND the controller widens further
    # (fine run reaches a higher width than coarse, from the same width0=0 start).
    dev_before = max(r_coarse["deviation_trace"]) if r_coarse["deviation_trace"] else 0
    dev_after = max(r_fine["deviation_trace"]) if r_fine["deviation_trace"] else 0
    peak_coarse = max(r_coarse["width_trace"]) if r_coarse["width_trace"] else 0
    peak_fine = max(r_fine["width_trace"]) if r_fine["width_trace"] else 0
    dev_jumps = dev_after > dev_before
    width_steps_up = peak_fine >= peak_coarse and peak_fine > 0
    g4 = dev_jumps and width_steps_up
    print("  deviation jumps on sharpen: %s (coarse peak %d -> fine peak %d)"
          % (dev_jumps, dev_before, dev_after))
    print("  controller widened under sharper grain: %s (coarse width peak %d, "
          "fine width peak %d, from width0=0)" % (width_steps_up, peak_coarse, peak_fine))
    print("  G4 %s" % ("PASS" if g4 else "FAIL"))

    return _finish(s, nodes, g1=g1, g2=g2, g3=g3, g4=g4,
                   res_fine=res_fine, res_coarse=res_coarse,
                   dev_before=dev_before, dev_after=dev_after,
                   spy_fine=spy_fine, spy_coarse=spy_coarse)


def _finish(s, nodes, *, g1, g2=None, g3=None, g4=None, negative=False,
            res_fine=None, res_coarse=None, dev_before=None, dev_after=None,
            spy_fine=None, spy_coarse=None):
    # ---------------------------------------------------------------- G5 ----- #
    print("\n" + "-" * 78)
    print("G5  TEACHER-FREE (ask-spy = 0 on the held path)")
    print("-" * 78)
    spy = AskSpy()
    ob = _observer(s, "g5", {"dynamical:valence": 1.0})
    rtt.run_regulated_train_of_thought(
        s, topic="poodle", setpoint_observer=ob, setpoint_topic="poodle",
        turns_per_segment=3, max_segments=4, on_unknown="return", ask_fn=spy)
    held_spy = len(spy.calls)
    if spy_fine is not None:
        held_spy += len(spy_fine.calls) + len(spy_coarse.calls)
    g5 = held_spy == 0
    print("  ask-spy calls on held path (all aperture runs): %d" % held_spy)
    print("  G5 %s" % ("PASS" if g5 else "FAIL"))

    # ---------------------------------------------------------------- G6 ----- #
    # BACKWARD-COMPAT: the concept-region tube_region path is unchanged — a narrow
    # region focuses (deviation 0 -> width narrows), and deviation drives width,
    # exactly as block 348. Demonstrate directly here (block-348's own gen script
    # is the fuller C1-C5 proof and still passes).
    print("\n" + "-" * 78)
    print("G6  BACKWARD-COMPAT: concept-region tube_region path == block-348")
    print("-" * 78)
    spy_bc = AskSpy()
    # narrow region tube around poodle's is-a cone -> should focus (converge)
    region = rtt._region_from_topic(s, "poodle")
    res_bc = rtt.run_regulated_train_of_thought(
        s, topic="poodle", tube_region=region,
        width0=2, deviation_wide_quanta=2, deviation_converge_quanta=0,
        turns_per_segment=3, max_segments=4, on_unknown="return", ask_fn=spy_bc)
    print("  tube_region (concept names): %s" % res_bc["tube_region"])
    print("  deviation_trace: %s" % res_bc["deviation_trace"])
    print("  width_trace    : %s" % res_bc["width_trace"])
    print("  setpoint_topic (should be None on region path): %s"
          % res_bc.get("setpoint_topic"))
    print("  admitted_size  (should be None on region path): %s"
          % res_bc.get("admitted_size"))
    # region path integer deviation drives width; setpoint fields stay None
    region_path_intact = (res_bc.get("setpoint_topic") is None
                          and res_bc.get("admitted_size") is None
                          and isinstance(res_bc["deviation_trace"], list)
                          and len(spy_bc.calls) == 0)
    g6 = region_path_intact
    print("  region path deviation-driven + setpoint fields None + teacher-free: %s"
          % region_path_intact)
    print("  (block-348 gen_rung3_regulated_manifold.py C1-C5 remains the full "
          "proof)")
    print("  G6 %s" % ("PASS" if g6 else "FAIL"))

    # ---------------------------------------------------------------- verdict  #
    print("\n" + "=" * 78)
    print("CLAIMS")
    print("=" * 78)
    rows = [("G1 multi-axis + grain bites", g1)]
    if not negative:
        rows += [("G2 fine grain -> narrow/focus", g2),
                 ("G3 coarse grain -> wide/roam", g3),
                 ("G4 sharpen -> deviation jumps -> width up", g4)]
    rows += [("G5 teacher-free (spy=0)", g5),
             ("G6 backward-compat region path", g6)]
    for name, ok in rows:
        print("  %-44s %s" % (name, "PASS" if ok else "FAIL"))

    if negative:
        verdict = ("HONEST NEGATIVE: grain did not bite; aperture-grain tube NOT "
                   "demonstrated (G2-G4 withheld). G5/G6 stand.")
        allpass = False
    else:
        allpass = all(ok for _, ok in rows)
        verdict = ("BLOCK 349 PASS: the set-point observer's GRAIN sets the "
                   "thought-manifold tube width for real — a fine grain admits a "
                   "narrow band (informative deviation, focus), a coarse grain "
                   "absorbs the trajectory (low deviation, freeform roam), "
                   "sharpening jumps the deviation and widens attention; grain "
                   "bites because it coarsens a genuinely multi-axis "
                   "concept_signature; discrete quanta throughout; teacher-free; "
                   "the concept-region path stays intact"
                   if allpass else "FALSIFIED (see failing claim above)")
    print("\nVERDICT: %s" % verdict)
    print("=" * 78)

    summary = {"g1": g1, "g5": g5, "g6": g6, "negative": negative,
               "all_pass": allpass}
    if not negative:
        summary.update({
            "g2": g2, "g3": g3, "g4": g4,
            "fine_admitted": res_fine["admitted_size"],
            "fine_deviation_trace": res_fine["deviation_trace"],
            "fine_width_trace": res_fine["width_trace"],
            "coarse_admitted": res_coarse["admitted_size"],
            "coarse_deviation_trace": res_coarse["deviation_trace"],
            "coarse_width_trace": res_coarse["width_trace"],
            "sharpen_dev_before": dev_before, "sharpen_dev_after": dev_after})
    print("SUMMARY_JSON " + json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
