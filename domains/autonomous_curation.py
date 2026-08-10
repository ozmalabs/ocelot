"""autonomous_curation — the FINAL thread of 'the assistant out of the loop':
the agent LEARNS NEW FAILURE-SHAPES from its OWN mistakes, instead of a human
banking the lessons.

THE INSIGHT — it is the SAME learning loop, one level up
================================================================================
The native manifold-collapse learning loop (scripts/native_collapse.py) is:
    SURPRISE (the failure signal)  ->  LOCALIZE the missing structure
    ->  CONSTRUCT it (bank the edge)  ->  next time it is covered.
AUTONOMOUS FAILURE-CURATION is that exact loop pointed at FAILURE-SHAPES instead
of at next-symbol transitions:

  1. DETECT     — surprise fires on a conclusion (high prediction-error on some
                  dimension). Surprise is SHAPE-INDEPENDENT: it fires even when no
                  banked failure-shape matches (the native -log(conf) Term).
  2. UNMATCHED  — the generative skeptic (domains.generative_skeptic.generate_probe)
                  tries to MATCH a banked failure-shape and BOTTOMS OUT
                  (residual == 'novel_failure_no_matching_shape')  ->  a NOVEL failure.
  3. RESOLVE    — LOCALIZE the weak link (the dimension carrying the highest
                  surprise / prediction-error) and DO-CONTRAST there
                  (domains.meta_monitor.investigate). The collapse it reveals
                  (lever_harms / disconnected_lever) is the RESOLUTION — what was
                  actually wrong.
  4. CONSTRUCT  — ABSTRACT the failure-SHAPE from the resolution: the surface
     / BANK     PATTERN the conclusion exhibits at the weak dimension + the PROBE
                  ('check this dimension') + the hat-input recipe, and BANK it as a
                  new FailureLesson graph node. This is the CONSTRUCT step of the
                  learning loop, on the meta level — a native graph mutation, the
                  same kind native_collapse.construct_gap_direct uses.
  5. SELF-CLOSE — the generative skeptic now MATCHES the newly-banked shape (its
                  next harvest_failure_shapes() reads the new FailureLesson) -> the
                  same failure (and near-misses of the same shape) is caught
                  forever after. The residual self-closes, one mistake at a time.

WHERE THE COGNITION LIVES (composed from the agent's OWN graph-resident pieces)
================================================================================
  · surprise         — the native Term scripts.native_collapse.T_SURPRISE
                       (-log(conf)), evaluated IN RUST by substrate.evaluate. The
                       per-dimension localization is a MaxOver / argmax over the
                       conclusion's dimension surprises (native), exactly the
                       weak-link localization the manifold uses.
  · the skeptic      — domains.generative_skeptic (its bottom-out IS the trigger).
  · the do-contrast  — domains.meta_monitor.investigate / record_intervention /
                       install_investigation_rule / agent_conclude_investigation
                       (the 3-way lever_helps/lever_harms/disconnected_lever Rule,
                       decided from MEASUREMENT, not assumption).
  · the BANK         — a native graph mutation: add a FailureLesson node + edge,
                       exactly the add_node/add_edge native_collapse banks a
                       transition with. The match_patterns are ABSTRACTED from the
                       resolved failure (the content tokens at the weak dimension),
                       NOT hand-authored.

DONKEY / ARCHITECTURE AUDIT
================================================================================
  · ADDITIVE — a NEW module only. No core touched (CortexLoop / solve_for_n.py /
    cortex_loop.py untouched). order_n_postulates.py and speech_science.py
    (task B's) NOT touched. generative_skeptic.py / self_check_hat.py /
    meta_monitor.py READ as references, not modified.
  · NO net, NO .fit, NO gradient, NO sweep, NO loss/optimiser. The new shape is
    ABSTRACTED from the agent's OWN resolved do-contrast (the localized weak link
    + its content tokens), banked as a native graph mutation — NOT hand-authored.
  · surprise + localization are NATIVE Terms (Neg/Log/MaxOver). The do-contrast
    verdict is the meta-monitor's graph Rule. Python here is world-adapter glue:
    marshal the conclusion's per-dimension numbers onto graph nodes, run the
    caller's measurement callables (world-I/O), abstract the tokens, add the node.

HONEST BOUNDARY (named, not forced to pass)
================================================================================
A SILENT novel failure — one that exposes NO localized surprise, no dimension
that prediction-error can point at (a fluent, internally-consistent wrong
conclusion whose error is only visible against ground truth the agent does not
hold) — gives the RESOLVE step nothing to localize. The do-contrast has no weak
link to toggle, so the loop cannot abstract a shape from it: it bottoms out the
SAME way the skeptic does, one level deeper. That is the irreducible fresh-mind
residual: the loop self-closes the failures it can FEEL (localized surprise), not
the ones it cannot. `curate` reports this case rather than faking a bank.
"""
from __future__ import annotations

import re

from substrate_rs import (Attr, Var, Neg, Log, MaxOver, Neighbours, Div, Max,
                          Min, Lit)

import domains.generative_skeptic as GS
import domains.meta_monitor as MM


# ===========================================================================
#  NATIVE surprise / localization Term-trees — the cognition.
#  A "Dim" node carries a dimension's claimed/realised support; surprise is the
#  agent's OWN -log(conf) Term, and the weak-link is the MaxOver of the per-dim
#  surprises (the same localization the manifold-collapse loop uses).
# ===========================================================================

_D = Var("D")
_EPS = Lit(1e-3)
# confidence at a dimension = realised/claimed, clamped to (eps, 1]
T_DIM_CONF = Max(items=(_EPS, Min(items=(Lit(1.0),
    Div(Attr(_D, "realised"), Max(items=(Attr(_D, "claimed"), _EPS)))))))
# surprise at a dimension = -log(conf)  (the agent's native error signal)
T_DIM_SURPRISE = Neg(Log(T_DIM_CONF))
# the weak link = the MOST-surprising dimension's surprise, localized NATIVELY:
# MaxOver the per-dim surprise over the conclusion's has_dim neighbours (the same
# argmax-localization scripts.native_collapse uses to find WHERE to construct).
T_MAX_DIM_SURPRISE = MaxOver(
    source=Neighbours(Var("Conc"), "has_dim"),
    var_name="D", value=T_DIM_SURPRISE, default=Lit(0.0))


def _native(s):
    return s._inner if hasattr(s, "_inner") else s


# ---------------------------------------------------------------------------
# DETECT — marshal a conclusion's per-dimension prediction-error onto the graph,
# evaluate the native surprise at each dimension, and LOCALIZE the weak link
# (the most-surprising dimension) NATIVELY.
# ---------------------------------------------------------------------------

def detect(s, conclusion_text: str, dimensions: list, *,
           name: str) -> dict:
    """DETECT: build a Conclusion node + one Dim node per (name, claimed, realised,
    tokens) in `dimensions`, evaluate the native per-dimension surprise, and
    localize the weak link = the dimension with the highest surprise.

    `dimensions` is a list of dicts {name, claimed, realised, tokens} — the
    conclusion's own exposed per-axis support numbers (world-I/O: read off the
    conclusion's printed numbers, exactly as the hat reads claimed/realised). The
    SURPRISE and the argmax-localization are NATIVE Terms; Python only marshals.

    Returns {conc, dims:[{node,name,surprise,...}], weak_link, max_surprise}.
    """
    conc = s.add_node("Conclusion", {"origin": "autonomous_curation",
                                     "name": name, "text": conclusion_text})
    try:
        s.add_production({"src": {"type": "Conclusion", "var": "a"},
                          "edge_type": "has_dim",
                          "tgt": {"type": "Dim", "var": "b"},
                          "provenance": "autonomous_curation:has_dim"})
    except Exception:
        pass
    dims = []
    for d in dimensions:
        dn = s.add_node("Dim", {
            "origin": "autonomous_curation",
            "name": d["name"],
            "claimed": float(d.get("claimed", 1.0)),
            "realised": float(d.get("realised", 1.0)),
            "tokens": d.get("tokens", d["name"])})
        try:
            s.add_edge(conc, "has_dim", dn)
        except Exception:
            pass
        surp = float(s.evaluate(T_DIM_SURPRISE, {"D": dn}))
        s.set_attr(dn, "surprise", surp)
        dims.append({"node": dn, "name": d["name"], "surprise": surp,
                     "claimed": float(d.get("claimed", 1.0)),
                     "realised": float(d.get("realised", 1.0)),
                     "tokens": d.get("tokens", d["name"])})

    # LOCALIZE the weak link NATIVELY: the MaxOver Term evaluates the per-dim
    # surprise over the conclusion's has_dim neighbours and returns the max IN
    # RUST — the same argmax-localization the collapse loop uses to find WHERE to
    # construct. Python then reads back WHICH dim carries that max (the argmax) to
    # do-contrast it; the surprise + the max are native, not Python arithmetic.
    max_surprise = float(s.evaluate(T_MAX_DIM_SURPRISE, {"Conc": conc})) if dims else 0.0
    weak = next((d for d in dims if abs(d["surprise"] - max_surprise) < 1e-9), None) \
        if dims else None
    s.set_attr(conc, "max_surprise", float(max_surprise))
    if weak is not None:
        s.set_attr(conc, "weak_link_dim", weak["name"])
    return {"conc": conc, "dims": dims, "weak_link": weak,
            "max_surprise": max_surprise}


# ---------------------------------------------------------------------------
# RESOLVE — do-contrast at the localized weak link via the meta-monitor's own
# investigator. The 3-way verdict it reaches IS the resolution (what was wrong).
# ---------------------------------------------------------------------------

def resolve(s, detection: dict, *, name: str, measure_with, measure_without,
            connection_band: float = 0.05) -> dict:
    """RESOLVE: do-contrast at the localized weak link, via the agent's OWN
    investigator (meta_monitor). Toggle the weak dimension's support
    (with vs without) by the caller's measurement callables — the SAME world-I/O
    the hat's do-contrast uses — and let the meta-monitor's investigate_connection
    RULE conclude lever_helps / lever_harms / disconnected_lever from the MEASURED
    direction. That verdict is the resolution.

    Returns {weak_link, payoff_with, payoff_without, delta, meta_verdict}.
    """
    weak = detection["weak_link"]
    p = MM.register_process(s, name, effort_label="curation_weak_link",
                            payoff_label="dim_support")
    s.set_attr(p, "connection_band", float(connection_band))

    with_val = float(measure_with())
    without_val = float(measure_without())
    MM.record_intervention(s, name, with_val, without_val)

    inv = MM.install_investigation_rule(s)
    issues = MM.agent_conclude_investigation(s, inv["rule_index"])
    issue = next((i["issue"] for i in issues if i["name"] == name), "none")

    return {"weak_link": weak["name"] if weak else None,
            "weak_link_tokens": weak["tokens"] if weak else "",
            "payoff_with": with_val, "payoff_without": without_val,
            "delta": with_val - without_val,
            "connection_band": float(connection_band),
            "meta_verdict": issue}


# ---------------------------------------------------------------------------
# BANK (the CONSTRUCT step, meta level) — ABSTRACT the failure-shape from the
# resolution and write a new FailureLesson graph node. The agent's own do-contrast
# supplies the shape; nothing is hand-authored.
# ---------------------------------------------------------------------------

_STOP = {"the", "and", "for", "with", "this", "that", "from", "into", "over",
         "than", "vs", "are", "was", "its", "has", "not", "but", "all", "any",
         "out", "off", "per", "via", "more", "less", "very", "such", "they",
         "you", "your", "our", "their", "a", "an", "of", "to", "in", "on", "is",
         "it", "by", "as", "at", "or", "be", "so", "no"}


def _abstract_patterns(weak_tokens: str, conclusion_text: str) -> list:
    """ABSTRACT the surface match-patterns of the failure-shape from the resolved
    weak link: the CONTENT tokens the conclusion exhibits AT the weak dimension.
    These are the surface signature a future conclusion of the SAME shape will
    show. Loose (keyword-level), exactly the surface order_n_postulates and the
    skeptic match on. NOT a hand-written probe list — derived from the resolution.

    Returns a small list of regex patterns (the distinctive content tokens at the
    weak link). Generalises: a pattern is a single content TOKEN, so any
    conclusion mentioning that token (a near-miss of the same shape) will match,
    not only the exact sentence.
    """
    text = (weak_tokens or "").lower()
    toks = [t for t in re.split(r"[^a-z0-9]+", text) if len(t) > 3 and t not in _STOP]
    # keep the distinctive content tokens at the weak link, de-duped, order-stable
    seen, pats = set(), []
    for t in toks:
        if t in seen:
            continue
        seen.add(t)
        pats.append(re.escape(t))
    return pats[:6] or [re.escape(text)] if text else []


def bank(s, detection: dict, resolution: dict, *, shape_name: str | None = None,
         microtheory: str = "generative_skeptic",
         surprise_floor: float = 0.10) -> dict:
    """BANK the abstracted failure-shape as a new FailureLesson graph node — the
    CONSTRUCT step of the learning loop on the meta level. A native graph mutation
    (add_node + has_lesson edge), the same kind native_collapse banks a transition
    with. The shape is ABSTRACTED from the resolution:
      · match_patterns  — the content tokens at the localized weak link
      · probe_template  — 'check THIS dimension' (the localized weak link)
      · weak_link       — the dimension the surprise pointed at
      · hat_inputs      — read the weak dimension's claimed vs realised support
    Only banks when the resolution found a real miss (lever_harms /
    disconnected_lever); a clean do-contrast (lever_helps) means there was no
    failure to learn.

    Returns {banked (bool), node, failure_shape, match_patterns, reason}.
    """
    mv = resolution.get("meta_verdict", "none")
    weak = detection["weak_link"]
    # THE HONEST BOUNDARY: a SILENT novel failure exposes NO localized surprise —
    # no dimension the prediction-error can point at (a fluent, internally-
    # consistent wrong conclusion whose error is only visible against ground truth
    # the agent does not hold). With nothing localized, the do-contrast is run on
    # an arbitrary dimension; there is no real weak link to abstract a shape from.
    # The loop BOTTOMS OUT rather than banking a spurious shape.
    if detection.get("max_surprise", 0.0) < surprise_floor:
        return {"banked": False, "node": None, "failure_shape": None,
                "match_patterns": [],
                "reason": (f"SILENT failure: max localized surprise "
                           f"{detection.get('max_surprise', 0.0):.4f} < floor "
                           f"{surprise_floor:.2f} — no dimension the prediction-error "
                           f"points at; nothing to localize or abstract. The "
                           f"fresh-mind residual: the loop self-closes the failures "
                           f"it can FEEL, not the silent ones.")}
    if mv not in ("lever_harms", "disconnected_lever"):
        return {"banked": False, "node": None, "failure_shape": None,
                "match_patterns": [],
                "reason": (f"do-contrast verdict '{mv}' is not a miss — nothing to "
                           f"bank (the weak link held; no new failure-shape)")}
    if weak is None:
        return {"banked": False, "node": None, "failure_shape": None,
                "match_patterns": [],
                "reason": "no localized weak link — silent failure, cannot abstract"}

    conc_text = s.node(detection["conc"])["attrs"].get("text", "")
    pats = _abstract_patterns(resolution.get("weak_link_tokens", weak["tokens"]),
                              conc_text)
    fs = shape_name or f"learned__{weak['name']}__{mv}"
    probe = (f"CHECK THE WEAK DIMENSION '{weak['name']}': a do-contrast on a past "
             f"episode showed this dimension's support {('was COUNTERPRODUCTIVE' if mv=='lever_harms' else 'did NOT reach the conclusion')} "
             f"(verdict={mv}). Re-measure this dimension's claimed vs realised "
             f"support WITH vs WITHOUT it before trusting a conclusion that leans on it.")
    wl = (f"{weak['name']} — the dimension the prediction-error localized; a "
          f"do-contrast found it {mv}.")
    hi = (f"claimed_support = the '{weak['name']}' dimension's claimed support; "
          f"realised_support = what it realised under do-contrast (the collapse).")

    # the BANK: a native graph mutation — add the FailureLesson + has_lesson edge.
    mt = next((m for m in s.nodes("Microtheory")
               if s.node(m)["attrs"].get("name") == microtheory), None)
    if mt is None:
        mt = s.add_node("Microtheory", {"name": microtheory,
                                        "origin": "autonomous_curation"})
    node = s.add_node("FailureLesson", {
        "name": f"lesson_learned__{weak['name']}",
        "node_type": "FailureLesson",
        "definition": (f"AUTONOMOUSLY CURATED from a resolved novel failure: "
                       f"conclusion '{conc_text[:120]}' had its weak link localized "
                       f"to '{weak['name']}' (surprise {weak['surprise']:.3f}); a "
                       f"do-contrast resolved it as {mv}. Banked so the skeptic "
                       f"catches this failure-shape and its near-misses."),
        "failure_shape": fs,
        "match_patterns": pats,
        "probe_template": probe,
        "weak_link": wl,
        "hat_inputs": hi,
        "category": "failure_lesson",
        "origin": "autonomous_curation",
        "curated": 1,
        "source_meta_verdict": mv})
    try:
        s.add_production({"src": {"type": "Microtheory", "var": "a"},
                          "edge_type": "has_lesson",
                          "tgt": {"type": "FailureLesson", "var": "b"},
                          "provenance": "generative_skeptic:has_lesson"})
    except Exception:
        pass
    try:
        s.add_edge(mt, "has_lesson", node)
    except Exception:
        pass
    return {"banked": True, "node": node, "failure_shape": fs,
            "match_patterns": pats,
            "reason": f"abstracted shape '{fs}' from the resolved {mv} weak link"}


# ---------------------------------------------------------------------------
# THE WHOLE LOOP — DETECT -> UNMATCHED -> RESOLVE -> BANK -> (the skeptic
# self-closes on the next harvest).
# ---------------------------------------------------------------------------

def curate(s, conclusion_text: str, dimensions: list, *, name: str,
           measure_with, measure_without, connection_band: float = 0.05,
           shape_name: str | None = None) -> dict:
    """The full autonomous-failure-curation loop in one call:

      DETECT    — surprise fires; localize the weak link (native).
      UNMATCHED — the generative skeptic bottoms out on this conclusion
                  (no banked shape) -> a NOVEL failure.
      RESOLVE   — do-contrast at the weak link (meta-monitor) -> the verdict.
      BANK      — abstract the shape from the resolution, add a FailureLesson.

    SELF-CLOSE is then verifiable by re-running the skeptic (generate_probe) on
    the SAME conclusion: it now MATCHES the banked shape.

    Returns the full trace {detection, skeptic_before, resolution, bank}.
    """
    # DETECT — native surprise + weak-link localization.
    det = detect(s, conclusion_text, dimensions, name=name)

    # UNMATCHED — the generative skeptic tries to match a banked shape and (for a
    # genuinely novel failure) bottoms out. This is the trigger for curation.
    probe_before = GS.generate_probe(s, conclusion_text)
    is_novel = (not probe_before["matched"]) and \
        probe_before.get("residual") == "novel_failure_no_matching_shape"

    # RESOLVE — do-contrast at the localized weak link via the agent's investigator.
    res = resolve(s, det, name=name, measure_with=measure_with,
                  measure_without=measure_without, connection_band=connection_band)

    # BANK — abstract the failure-shape from the resolution; native graph mutation.
    bk = bank(s, det, res, shape_name=shape_name)

    return {"detection": det, "skeptic_before": probe_before,
            "is_novel": is_novel, "resolution": res, "bank": bk}


__all__ = ["detect", "resolve", "bank", "curate",
           "T_DIM_SURPRISE", "T_DIM_CONF"]
