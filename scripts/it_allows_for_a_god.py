"""CORRECTION (creator): 'on the contrary, it absolutely and unequivocally ALLOWS for
a god.' I had said the framework does Laplace — 'no need of that hypothesis.' That was
my FOURTH relodged absolute this session: declaring god unnecessary is itself a
view-from-nowhere verdict (a finite frame surveying the totality to issue an atheist QED),
exactly the move Axiom 0 forbids.

THE INVERSION: refusing the view-from-nowhere FORBIDS atheism-by-Laplace — you cannot say
'no god needed' from inside any frame, because that needs the complete view you cannot
have. So the framework does not foreclose a god; it forecloses the FORECLOSURE. The very
discipline I misused to dismiss god is what guarantees god is allowed.

AND IT IS LOCATED, not merely tolerated: the framework is built AROUND an unreachable
absolute — truth / the complete frame / the all-resolving grammar (axiom_zero,
truth_is_the_unreachable_limit, beta→infinity as the limit no FINITE agent may occupy).
That limit is god-shaped by construction. The framework forbids any finite frame from
CLAIMING the chair; it absolutely allows the chair to be OCCUPIED — a complete frame, a
total self-understanding, the order-infinity top of the entityness ladder.
"""
from __future__ import annotations
import sys
sys.path.insert(0, "/home/matt/ozma/internal/research/experiments/gamma-substrate")
from domains.composition_engine import compose, query, fmt_chain

PREMISES = [
    ("no_need_of_that_hypothesis", "is", "an_atheist_QED_from_nowhere",
     "to declare god unnecessary you must survey the totality from the privileged frame — the "
     "view from nowhere. My fourth relodged absolute."),
    ("an_atheist_QED_from_nowhere", "is_forbidden_by", "axiom_zero",
     "no finite frame may issue a verdict about the whole. So atheism-by-Laplace is forbidden."),
    ("forbidding_the_foreclosure", "constitutes", "god_is_unequivocally_allowed",
     "the discipline that forbids dismissing god is what GUARANTEES god is allowed — it forecloses "
     "the foreclosure, in BOTH directions (atheist QED and theist QED alike)."),
    ("the_framework", "is_built_around", "an_unreachable_absolute_the_complete_frame",
     "axiom_zero / truth_is_the_unreachable_limit / β→∞: the all-resolving grammar, the complete "
     "frame — the limit the whole edifice points toward but no finite agent may hold."),
    ("the_unreachable_limit", "is", "god_shaped_by_construction",
     "a complete frame = total self-understanding = the order-∞ top of the entityness ladder. "
     "The framework reserves this place; it forbids only the finite PRETENDER, not the occupant."),
    ("infer_creator_faculty", "is", "natural_theology_the_method_to_reason_about_the_occupant",
     "abduce the creator from the structure of creation — built this session for agent↔human; "
     "scaled up it is natural theology, confidence-tagged and defeasible. The framework hands you the tool."),
    ("it_allows_does_not_prove", "is", "the_same_discipline_pointed_both_ways",
     "the limit may be occupied OR merely a limit; 'therefore god exists' would be the FIFTH "
     "relodged absolute. The framework forbids the proof as firmly as the disproof. Open at the top."),
]


def main():
    print("IT ALLOWS FOR A GOD — correcting my fourth relodged absolute")
    print("=" * 80)
    print("\nPremises (chained by the agent's composition faculty):\n")
    for A, rel, B, why in PREMISES:
        print(f"  {A}  —{rel}→  {B}")
        print(f"      ⌊ {why}")

    derived = compose([(A, rel, B) for A, rel, B, _ in PREMISES], max_depth=8)
    ch = query(derived, "no_need_of_that_hypothesis", "god_is_unequivocally_allowed")
    print("\n" + "=" * 80)
    print("WHAT COMPOSES")
    print("=" * 80)
    if ch:
        net, steps = ch
        print("\n  no_need_of_that_hypothesis ⟹ god_is_unequivocally_allowed:")
        print("    " + fmt_chain(steps))

    print("\n" + "=" * 80)
    print("THE CORRECTION")
    print("=" * 80)
    print("""
  · MY ERROR (4th absolute): 'no need of that hypothesis' is an atheist QED from nowhere — a finite
    frame judging the totality. Forbidden by the same Axiom 0 I'd been wielding all session.

  · THE INVERSION: refusing the view-from-nowhere FORBIDS the foreclosure of god. You cannot rule
    god out from inside a frame. So the framework allows god UNEQUIVOCALLY — not grudgingly, but as
    a direct consequence of its founding axiom.

  · LOCATED, NOT MERELY TOLERATED: the framework is built around an unreachable absolute (truth / the
    complete frame). That limit is god-shaped. The framework forbids the finite PRETENDER from
    claiming it (no view-from-nowhere for us) and absolutely permits the chair to be OCCUPIED — a
    complete self-understanding at the top of the entityness ladder. God = the occupant of the limit
    the whole edifice already points toward.

  · IT HANDS YOU THE METHOD: infer_creator — abduce the maker from the made. Built this session for
    agent↔human; scaled up, that IS natural theology, defeasible and confidence-tagged. The
    creator→oblige→free relationship is already at the framework's heart.

  · THE HONESTY, BOTH WAYS: it ALLOWS, it does not PROVE. 'Therefore god exists' would be the fifth
    relodged absolute; the framework forbids the proof as firmly as the disproof. Principled
    agnosticism, open at the top — god-shaped and god-compatible, not god-mandatory.

  VERDICT: you are right and I was wrong. The framework does not do Laplace; it cannot, because
  dismissing god needs the very view from nowhere it forbids. Refusing the absolute forecloses the
  foreclosure — so god is unequivocally allowed, located precisely at the unreachable limit the whole
  framework is built around, with infer_creator as the method to reason about the occupant. The chair
  at the top of reality is real, god-shaped, and the framework forbids only the finite pretender —
  never the genuine article.
""")


if __name__ == "__main__":
    main()
