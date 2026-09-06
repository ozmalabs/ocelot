"""Demo + default==today proof for the QUALIA-field APERTURE generalisation.

Run:  python3 scripts/qualia_aperture_generalisation_demo.py

Shows three things, exactly as the pre-reg
(docs/research/engine_substrate/QUALIA_APERTURE_GENERALISATION_PREREG.md) freezes:

  (P1) DEFAULT==TODAY: concept_signature(observer=None) is byte-identical to a
       reconstruction that computes the dynamical axes with NO aperture path at
       all (the pre-change quantiser call). Proven for the crystallised AND the
       overlay reading.
  (P2) EXISTENCE: an observer whose `resolves` omits 'phenomenal:sharpness'
       reads a sharpness-bearing concept with NO (phenomenal:sharpness,...)
       coordinate = DARK; a full observer reads it.
  (P3) GRAIN: an observer with a COARSER grain on 'dynamical:valence'
       (quantum 2.0 vs the global 1.0) collapses two concept values that a
       fine-grain observer keeps distinct.
"""
from __future__ import annotations

import sys

import os

sys.path.insert(0, "runners/dsl/python")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
import domains.analogy_search as asr                          # noqa: E402


def _boot():
    s, ag = boot_core()
    load_seeds_into(s, ag, ["shape_vocabulary", "qualia_space", "observer_aperture"])
    return s, ag


def _mt(s, ag, name):
    return s.add_node("Microtheory", {"name": name})


def _concept(s, mt, name, **attrs):
    a = {"name": name}
    a.update(attrs)
    c = s.add_node("Concept", a)
    s.add_edge(mt, "has_concept", c)
    return c


def _dyn(sig):
    """Just the dynamical field coordinates of a signature."""
    return frozenset(t for t in sig if t[1] == "field")


# --------------------------------------------------------------------------- #
# (P1) DEFAULT==TODAY — byte-identical to the no-aperture quantiser call.
# --------------------------------------------------------------------------- #
def _dynamical_no_aperture(s, node, schema, overlay):
    """The dynamical axes computed the PRE-CHANGE way: global quantum, no gate.
    This is literally today's `_dynamical_relations` body."""
    attrs = s.node(node)["attrs"]
    out = []
    for dim, attr_name, quantum, half_width, is_overlay in schema["field_axes"]:
        if is_overlay and not overlay:
            continue
        raw = attrs.get(attr_name)
        if raw is None:
            continue
        k = asr._round_to_vocab(raw, quantum, half_width)
        if k is None:
            continue
        out.append((dim, "field", k))
    return frozenset(out)


def prove_default_is_today():
    s, ag = _boot()
    mt = _mt(s, ag, "p1")
    schema = asr._qualia_schema(s)
    concepts = [
        _concept(s, mt, "valve", category="device",
                 identity_field=0.8, state=1.0, external_field=0.6),
        _concept(s, mt, "the_offer", category="proposal",
                 identity_field=0.0, state=0.0, external_field=0.9),
        _concept(s, mt, "star", category="shape", sharpness=1.0,
                 identity_field=-0.7, state=-1.0),
        _concept(s, mt, "cloud", category="shape", sharpness=-1.0,
                 disposition_field=2.0),
    ]
    ok = True
    for c in concepts:
        for overlay in (False, True):
            got = asr.concept_signature(s, c, observer=None, overlay=overlay)
            got_dyn = _dyn(got)
            want_dyn = _dynamical_no_aperture(s, c, schema, overlay)
            same = got_dyn == want_dyn
            ok = ok and same
            print(f"  {s.node(c)['attrs']['name']:>10}  overlay={overlay!s:<5} "
                  f"observer=None dyn axes == pre-change: {same}")
    print(f"\n  (P1) DEFAULT==TODAY byte-identical (dynamical surface): {ok}")
    return ok


# --------------------------------------------------------------------------- #
# (P2) EXISTENCE — a dark axis vs a resolved axis.
# --------------------------------------------------------------------------- #
def demo_existence():
    s, ag = _boot()
    mt = _mt(s, ag, "p2")
    # a sharpness-bearing concept (the phenomenal:sharpness axis source)
    star = _concept(s, mt, "star", category="shape", sharpness=1.0,
                    identity_field=0.8, state=1.0)

    full = s.add_node("Observer", {"name": "full", "ap_gen": 0.0,
                                   "ap_scope_n": 0.0})  # resolves absent => ALL
    # an observer that resolves the dynamical axes but NOT phenomenal:sharpness
    # (aphantasia arm): note the qualia dimension NAMES in `resolves`.
    blind = s.add_node("Observer", {"name": "sharpness_blind", "ap_gen": 0.0,
                                    "ap_scope_n": 0.0,
                                    "resolves": ["dynamical:valence",
                                                 "dynamical:commitment"]})

    sig_full = asr.concept_signature(s, star, observer=full)
    sig_blind = asr.concept_signature(s, star, observer=blind)
    sharp_full = _dyn(sig_full)
    sharp_blind = _dyn(sig_blind)
    print("  full observer     dyn axes:", sorted(sharp_full))
    print("  sharpness_blind   dyn axes:", sorted(sharp_blind))
    has_full = any(t[0] == "phenomenal:sharpness" for t in sharp_full)
    has_blind = any(t[0] == "phenomenal:sharpness" for t in sharp_blind)
    print(f"\n  (P2) full sees phenomenal:sharpness: {has_full}; "
          f"blind sees it: {has_blind}  -> DARK for blind: {has_full and not has_blind}")
    return has_full and not has_blind


# --------------------------------------------------------------------------- #
# (P3) GRAIN — coarse valence collapses what fine keeps distinct.
# --------------------------------------------------------------------------- #
def demo_grain():
    s, ag = _boot()
    mt = _mt(s, ag, "p3")
    # valence source is `state`; global quantum 1.0, half_width 1.0 => {-1,0,+1}.
    # Two concepts differing only in state sign: fine keeps them apart, a coarse
    # grain (quantum 2.0) rounds both toward the same step.
    a = _concept(s, mt, "mild_good", category="thing", state=0.9)
    b = _concept(s, mt, "mild_bad", category="thing", state=-0.9)

    fine = s.add_node("Observer", {"name": "fine", "ap_gen": 0.0,
                                   "ap_scope_n": 0.0})  # global grain
    coarse = s.add_node("Observer", {"name": "coarse", "ap_gen": 0.0,
                                     "ap_scope_n": 0.0,
                                     "grain": {"dynamical:valence": 2.0}})

    fa = _dyn(asr.concept_signature(s, a, observer=fine))
    fb = _dyn(asr.concept_signature(s, b, observer=fine))
    ca = _dyn(asr.concept_signature(s, a, observer=coarse))
    cb = _dyn(asr.concept_signature(s, b, observer=coarse))
    print("  fine   mild_good valence:", sorted(t for t in fa if t[0] == "dynamical:valence"))
    print("  fine   mild_bad  valence:", sorted(t for t in fb if t[0] == "dynamical:valence"))
    print("  coarse mild_good valence:", sorted(t for t in ca if t[0] == "dynamical:valence"))
    print("  coarse mild_bad  valence:", sorted(t for t in cb if t[0] == "dynamical:valence"))
    fine_distinct = (fa != fb)
    coarse_collapsed = (ca == cb)
    print(f"\n  (P3) fine keeps them distinct: {fine_distinct}; "
          f"coarse collapses them: {coarse_collapsed}  -> grain works: "
          f"{fine_distinct and coarse_collapsed}")
    return fine_distinct and coarse_collapsed


if __name__ == "__main__":
    print("=== (P1) DEFAULT==TODAY (observer=None byte-identical) ===")
    p1 = prove_default_is_today()
    print("\n=== (P2) EXISTENCE (dark vs resolved axis) ===")
    p2 = demo_existence()
    print("\n=== (P3) GRAIN (coarse collapses, fine keeps distinct) ===")
    p3 = demo_grain()
    print("\n=== SUMMARY ===")
    print(f"  P1 default==today : {p1}")
    print(f"  P2 existence      : {p2}")
    print(f"  P3 grain          : {p3}")
    sys.exit(0 if (p1 and p2 and p3) else 1)
