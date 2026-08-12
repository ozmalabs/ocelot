#!/usr/bin/env python3
"""AR1/AR3/AR4 measurement harness for META_SHAPE_FIRST_CLASS.

Run from EITHER tree — it measures whatever engine resolves:

    OZMA_TREE=/home/matt/ozmadev/ocelot            python3 ... (BEFORE)
    OZMA_TREE=/home/matt/ocelot-meta-shape-first-class python3 ... (AFTER)

AR1 reimplements the BEFORE scorer in Python (a read-only mirror of
`shape_decode.rs::recognise_meta_shape` at `ae38fe7`) so both verdicts can be
computed side by side in ONE process against ONE codebook — no cross-engine
comparison, no drift.
"""
from __future__ import annotations

import json
import os
import sys

TREE = os.environ.get("OZMA_TREE", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for p in (TREE, os.path.join(TREE, "runners", "dsl", "python")):
    if p in sys.path:
        sys.path.remove(p)
    sys.path.insert(0, p)
os.environ["OZMA_SEED_PERSIST_DISABLED"] = "1"

from substrate.world_adapter import WorldAdapter          # noqa: E402
from substrate.seed_loader import manifest_for            # noqa: E402


def boot(seeds=("shape_vocabulary",)):
    wa = WorldAdapter()
    for seed in seeds:
        wa.inner.load_seed_manifest(manifest_for(seed), wa.agent)
    return wa


# ---------------------------------------------------------------------------
#  THE BEFORE SCORER — a faithful Python mirror of shape_decode.rs @ ae38fe7:
#  text = " ".join(str string-valued attrs).lower(); score = #principles with a
#  substring keyword hit; argmax by (-score, name) — ALPHABETICAL TIEBREAK.
# ---------------------------------------------------------------------------
def before_verdict(s, type_, attrs):
    text = " ".join(str(v) for v in attrs.values() if isinstance(v, str)).lower()
    if not text:
        return None, []
    scored = []
    for sh in s.nodes("MetaShape"):
        nm = s.node(sh)["attrs"].get("name")
        if not nm:
            continue
        sc = 0
        for p in s.neighbours(sh, "has_principle"):
            kws = s.node(p)["attrs"].get("keywords") or []
            if any(str(k) in text for k in kws):
                sc += 1
        if sc > 0:
            scored.append((sc, str(nm)))
    if not scored:
        return None, []
    scored.sort(key=lambda t: (-t[0], t[1]))
    top = scored[0][0]
    return scored[0][1], sorted(n for c, n in scored if c == top)


CASES = [
    # (label, type_, attrs, expected_or_None, why)
    ("gate-by-policy", "Note", {"text": "gate the layer by policy"},
     "selective_gating",
     "gated_access matched TWO keywords (gate, policy); hierarchical_abstraction ONE (layer)"),
    ("winner-vs-recall", "Note",
     {"text": "the selection is a winner-take-all recall from an attractor"},
     None,
     "genuinely 2-vs-2 keywords across two shapes: an honest residual, not a letter"),
    ("typed-slots-predict", "Belief",
     {"predict": "the next frame", "observe": "the actual frame"},
     "prediction_minus_observation",
     "the item's own TYPED SLOTS are the shape; BEFORE discarded the keys entirely"),
    ("prose-only-predict", "Note",
     {"text": "you should predict things and observe them"},
     "prediction_minus_observation",
     "same words in PROSE — must still work (no regression on content evidence)"),
    ("typed-slot-gate", "Policy", {"gate": "on tom_capacity", "target": "reply prefix"},
     "selective_gating", "a typed `gate` slot"),
    ("consolidate-replay", "Note", {"text": "replay during sleep to consolidate"},
     "delayed_persistence", "unambiguous single-shape control"),
    ("broadcast", "Note", {"text": "a global hormone broadcast"},
     "global_message_passing", "unambiguous single-shape control"),
    ("no-shape", "MarkerClass", {"marker": "however", "role": "contrast"},
     None, "matches nothing: must stay a residual"),
    ("quintuple", "Concept",
     {"name": "quintuple", "definition": "multiply a number by five", "multiplier_factor": 5.0},
     None, "matches nothing: must stay a residual"),
    ("spatial", "SelectionalClassPair",
     {"verb": "slide", "subject_class": "physical_object", "object_class": "surface"},
     "spatial_dynamics", "unambiguous control that BEFORE already got right"),
]


def ar1():
    wa = boot()
    s = wa.s
    from domains.teach import categorise_by_shape
    rows = []
    for label, t, a, expected, why in CASES:
        b, tied = before_verdict(s, t, a)
        af = categorise_by_shape(wa, t, a)
        rows.append(dict(label=label, type=t, attrs=a, expected=expected,
                         before=b, before_tied=tied, after=af, why=why,
                         before_ok=(b == expected), after_ok=(af == expected)))
    return rows


def ar1_exhaustive():
    """EXHAUSTIVE adversarial sweep over the whole held codebook.

    For every ORDERED pair of distinct MetaShapes (11 shapes ⇒ 55 unordered
    pairs), build an observation carrying exactly ONE keyword from each shape.
    That is a forced tie by construction: both shapes score 1 principle and 1
    keyword. The question the sweep answers is what each recognizer does with a
    contest it genuinely cannot decide.
    """
    wa = boot()
    s = wa.s
    from domains.teach import categorise_by_shape

    shapes = {}
    for sh in s.nodes("MetaShape"):
        nm = str(s.node(sh)["attrs"].get("name"))
        kws = []
        for p in s.neighbours(sh, "has_principle"):
            kws += [str(k) for k in (s.node(p)["attrs"].get("keywords") or [])]
        if nm and kws:
            shapes[nm] = sorted(kws)

    names = sorted(shapes)
    rows = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            # pick the pair of keywords that do NOT contain one another, so the
            # tie is real rather than an artefact of substring overlap
            pick = None
            for ka in shapes[a]:
                for kb in shapes[b]:
                    if ka not in kb and kb not in ka:
                        pick = (ka, kb)
                        break
                if pick:
                    break
            if not pick:
                continue
            text = f"{pick[0]} and {pick[1]}"
            attrs = {"text": text}
            bv, tied = before_verdict(s, "Note", attrs)
            av = categorise_by_shape(wa, "Note", attrs)
            rows.append(dict(pair=[a, b], keywords=list(pick), text=text,
                             before=bv, before_tied=tied, after=av))
    return rows


def ar4():
    """AR4 — the existing consumers, against the fixed recognizer AND against a
    codebook that has GROWN by a runtime mint."""
    from domains.meta_shape import observe
    import domains.analogical_thinking as at

    wa = boot(seeds=("shape_vocabulary", "meta_shape_growth",
                     "seven_meta_shape_subsystems", "relation_vocabulary",
                     "mechanism_index"))
    out = {}
    out["shape_hits_before"] = sorted(at.shape_hits(wa.s, "gate the layer by policy"))
    out["realisation_counts_before"] = dict(at.metashape_realisation_counts(wa.s))
    out["codebook_before"] = len(wa.s.nodes("MetaShape"))

    # TransferDecode, through its own Term, against the fixed shared scorer.
    goal = [["measure", "the", "current", "FIRING", "RATE"],
            ["compare", "RATE", "to", "the", "set_point", "BUDGET"],
            ["regulate", "by", "FEEDBACK", "toward", "the", "BUDGET"]]
    td = wa.inner.evaluate({"type": "TransferDecode",
                            "goal": {"type": "Lit", "value": goal}}, {})
    out["transfer_decode_before"] = {
        "meta_shape": (td or {}).get("meta_shape") if isinstance(td, dict) else td,
        "retrieved": len((td or {}).get("retrieved") or ()) if isinstance(td, dict) else None,
    }

    # GROW the codebook at runtime, then re-run every consumer.
    observe(wa, "Note", {"text": "a global hormone broadcast"})
    observe(wa, "TradeRecord", {"buyer": "alice", "seller": "bob", "lot": "7"})
    observe(wa, "TradeRecord", {"buyer": "carol", "seller": "dave", "lot": "9"})
    out["codebook_after"] = len(wa.s.nodes("MetaShape"))
    out["minted"] = sorted(str(wa.s.node(n)["attrs"].get("name"))
                           for n in wa.s.nodes("MetaShape")
                           if wa.s.node(n)["attrs"].get("minted"))

    at._METASHAPE_COUNT_CACHE.clear()
    out["shape_hits_after"] = sorted(at.shape_hits(wa.s, "gate the layer by policy"))
    out["realisation_counts_after"] = dict(at.metashape_realisation_counts(wa.s))
    td2 = wa.inner.evaluate({"type": "TransferDecode",
                             "goal": {"type": "Lit", "value": goal}}, {})
    out["transfer_decode_after"] = {
        "meta_shape": (td2 or {}).get("meta_shape") if isinstance(td2, dict) else td2,
        "retrieved": len((td2 or {}).get("retrieved") or ()) if isinstance(td2, dict) else None,
    }

    # The reflective "what shape are you?" faculty.
    try:
        from domains.reflective_faculty import _run_self_shape
        out["self_shape"] = _run_self_shape(wa.s, None)
    except Exception as e:                                     # pragma: no cover
        out["self_shape_error"] = f"{type(e).__name__}: {e}"
    return out


def main():
    out = {"tree": TREE, "ar1": ar1(), "ar1_exhaustive": ar1_exhaustive(),
           "ar4": ar4()}
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
