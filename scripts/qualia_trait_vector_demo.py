#!/usr/bin/env python3
"""COGNITIVE PERSONALITY as a VECTOR of independent CAN-relaxable qualia axes.

Run: python3 scripts/qualia_trait_vector_demo.py

The agent's cognitive style is not one dial — it is a PERSONALITY: a vector of
independent traits, each its own CAN-produced / crystallising / seeded dynamical
qualia axis on its own distribution (domains/disposition.TRAIT_REGISTRY). This
generalises the single `disposition` scalar WITHOUT forking the mechanism: every
trait is its own `Concept` in the shared `agent_disposition` Mt, moved by the
SAME can_native_identity_field_feedback dynamics, mirrored to its own
`dynamical:<trait>` axis. openness IS the old disposition; abstraction and
skepticism are new, seeded-neutral, and INERT this layer.

This script demonstrates the four things the vector has to earn:

  (a) TWO PERSONALITIES — two agents SEEDED with DIFFERENT trait vectors occupy
      DISTINCT multi-axis signatures (distinct dynamical:openness / abstraction /
      skepticism coordinates). People sit on a distribution across MANY traits.

  (b) INDEPENDENCE — each trait moves under ITS OWN evidence and ONLY its own:
      relaxing openness does not move skepticism or abstraction (separate CAN
      Concepts, separate fields). No cross-talk.

  (c) THE WHOLE VECTOR AT ONCE — trait_vector reads the entire personality in
      one call; personality_signature reads the personality AS a point in qualia
      space (its coordinate on every trait axis).

  (d) BACK-COMPAT — openness IS the old disposition: disposition_level ==
      trait_level(openness), same axis dynamical:disposition, same default.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent
                       / "runners" / "dsl" / "python"))

from substrate_rs import _native

import domains.analogy_search as asr
import domains.disposition as disp


class _Agent:
    """Minimal agent wrapper: a `.s` substrate handle + an `.agent` hub node —
    the shape domains/disposition.py accepts (getattr(agent, 's', agent))."""
    def __init__(self):
        asr._QUALIA_SCHEMA_CACHE.clear()
        self.s = _native.Substrate()
        self.agent = self.s.add_node("Agent", {})


def section(title):
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def _fmt_vector(vec):
    return "{" + ", ".join(f"{k}={v:+d}" for k, v in vec.items()) + "}"


def _fmt_signature(sig):
    """The personality as a point: trait -> its dynamical:<trait> coordinate."""
    parts = []
    for name, coord in sig.items():
        if coord is None:
            parts.append(f"{name}=·")          # neutral floor (omitted by sig)
        else:
            parts.append(f"{name}={coord[0].split(':')[1]}:{coord[2]:+d}")
    return "  ".join(parts)


def main():
    section("SETUP — the trait registry (the vector's components, as DATA)")
    for name, spec in disp.TRAIT_REGISTRY.items():
        tag = " (== old disposition)" if name == disp.OPENNESS_TRAIT else \
              " (seeded neutral, INERT this layer)"
        print(f"  {name:12s} seed={spec.seed:+.1f}  axis={spec.axis}{tag}")

    # ---------------------------------------------------------------- (a) --
    section("(a) TWO PERSONALITIES — different trait VECTORS, distinct signatures")
    # Agent A: OPEN + ABSTRACT + CREDULOUS.
    A = _Agent()
    disp.set_trait_seed(A, "openness", +2.0)
    disp.set_trait_seed(A, "abstraction", +3.0)
    disp.set_trait_seed(A, "skepticism", -2.0)
    # Agent B: CLOSED + CONCRETE + SKEPTICAL.
    B = _Agent()
    disp.set_trait_seed(B, "openness", -3.0)
    disp.set_trait_seed(B, "abstraction", -2.0)
    disp.set_trait_seed(B, "skepticism", +3.0)

    va, vb = disp.trait_vector(A), disp.trait_vector(B)
    print(f"  A (open/abstract/credulous):  {_fmt_vector(va)}")
    print(f"  B (closed/concrete/skeptical):{_fmt_vector(vb)}")
    print()
    sa, sb = disp.personality_signature(A), disp.personality_signature(B)
    print(f"  A signature (point in qualia space):  {_fmt_signature(sa)}")
    print(f"  B signature (point in qualia space):  {_fmt_signature(sb)}")
    assert va != vb and sa != sb
    print("→ two agents, two DISTINCT multi-axis personality signatures. The "
          "vector is a real point in an N-dimensional cognitive-style space.")

    # ---------------------------------------------------------------- (b) --
    section("(b) INDEPENDENCE — each trait moves under its OWN evidence, only")
    a = _Agent()
    disp.set_trait_seed(a, "openness", 0.0)
    disp.set_trait_seed(a, "abstraction", 0.0)
    disp.set_trait_seed(a, "skepticism", 0.0)
    print(f"  start:                         {_fmt_vector(disp.trait_vector(a))}")

    disp.relax_trait(a, "openness", +1.0, ticks=3)     # drive ONLY openness
    v = disp.trait_vector(a)
    print(f"  after +openness (3 ticks):     {_fmt_vector(v)}")
    assert v["openness"] > 0
    assert v["abstraction"] == 0 and v["skepticism"] == 0, v
    print("    → openness moved; abstraction & skepticism DID NOT (separate "
          "CAN Concepts, separate fields — no cross-talk).")

    disp.relax_trait(a, "skepticism", +1.0, ticks=4)   # now drive ONLY skepticism
    v = disp.trait_vector(a)
    print(f"  after +skepticism (4 ticks):   {_fmt_vector(v)}")
    assert v["skepticism"] > 0
    assert v["abstraction"] == 0, v                      # abstraction still inert
    print("    → skepticism moved independently; abstraction still untouched. "
          "Each axis has its own dynamics.")

    # ---------------------------------------------------------------- (c) --
    section("(c) THE WHOLE VECTOR / PERSONALITY read at once")
    print(f"  trait_vector(a)          = {disp.trait_vector(a)}")
    print(f"  personality_signature(a) = {_fmt_signature(disp.personality_signature(a))}")
    print("→ the entire personality — position on every trait axis — read in "
          "one call. Not one dial: a vector.")

    # ---------------------------------------------------------------- (d) --
    section("(d) BACK-COMPAT — openness IS the old disposition")
    d = _Agent()                                        # fresh, seeded default
    lvl_new = disp.trait_level(d, "openness")
    lvl_old = disp.disposition_level(d)
    print(f"  fresh agent (seeded default):")
    print(f"    disposition_level(d)        = {lvl_old}")
    print(f"    trait_level(d, 'openness')  = {lvl_new}")
    print(f"    DEFAULT_DISPOSITION_SEED    = {disp.DEFAULT_DISPOSITION_SEED}")
    assert lvl_new == lvl_old == int(disp.DEFAULT_DISPOSITION_SEED) == -1
    # the openness axis IS dynamical:disposition (the old name)
    ax = disp.TRAIT_REGISTRY["openness"].axis
    print(f"    openness axis name          = {ax}")
    assert ax == "dynamical:disposition"
    # old set_disposition_seed still works, and moves the same trait
    disp.set_disposition_seed(d, +2.0)
    assert disp.trait_level(d, "openness") == +2
    print("    set_disposition_seed(d, +2) → trait_level(openness) == +2 ✓")
    print("→ every old single-disposition caller is unchanged: openness IS the "
          "old disposition, same axis, same default, same API.")

    section("SUMMARY")
    print("The single disposition scalar is now the `openness` component of a "
          "trait VECTOR:\n"
          "  · N named traits, each a CAN-produced/crystallising/seeded axis on "
          "its own distribution;\n"
          "  · ONE shared mechanism (relaxation + crystallisation + mirror) — "
          "adding a trait is a registry row, not code;\n"
          "  · traits are INDEPENDENT (separate Concepts, separate fields);\n"
          "  · the whole personality reads as a point in qualia space;\n"
          "  · openness IS the old disposition — back-compat is exact.")


if __name__ == "__main__":
    main()
