"""HLE world, LLM-style — present each HLE question the SAME WAY an LLM gets it
(the full question text as one prompt) through the agent's CURRENT pipeline
(ConversationWorld: comprehend -> reason -> conjecture -> epistemic-access), and
read off the GAPS in the response.

  run:  python scripts/hle_llm_probe.py [--n=40]

This is a DIAGNOSTIC, not a score. The agent has no grounded physics/math/bio
knowledge and its comprehension is built for simple sentences, so the honest
expectation is that most questions land in not_comprehended / inadmissible. The
value is the GAP MAP: where, and how, the response falls short — and whether the
agent declines honestly (inadmissible / resolvable-via-route) rather than
fabricating.
"""
from __future__ import annotations
import sys
sys.path.insert(0, ".")
from substrate_rs import _native
from domains.language_world import LanguageWorld, teacher_stub
from scripts.language_test import training_bank
from domains.conversation_world import ConversationWorld
from domains.hle_world import HLEWorld, load_hle_math_bank

BANK = "data/hle_math.json"


def setup():
    s = _native.Substrate()
    world = LanguageWorld(s, training_bank(), teacher_stub)
    LanguageWorld.summary(world.run())
    world.teacher_disabled = True          # LLM-style: no teacher scaffolding
    cw = ConversationWorld(world, interlocutor="user")
    return s, world, cw


def main(argv):
    n = 40
    for a in argv[1:]:
        if a.startswith("--n="):
            n = int(a.split("=", 1)[1])

    questions = load_hle_math_bank(BANK, only_exact_match=True)[:n]
    print(f"HLE LLM-style probe — {len(questions)} questions presented as a "
          f"raw prompt through ConversationWorld\n")

    s, world, cw = setup()
    hle = HLEWorld(questions)
    log = hle.run_llm_style(cw, limit=n)

    gm = HLEWorld.gap_map_llm(log)
    print("=" * 68)
    print("GAP MAP — where the response falls short (first failing stage)")
    print("=" * 68)
    order = ["coherence_abstain", "not_comprehended", "miscomprehended_assert",
             "degenerate_echo", "inadmissible", "resolvable_via_route",
             "conjecture", "answered_grounded", "correct", "errors"]
    tot = gm["questions"] or 1
    for k in order:
        v = gm.get(k, 0)
        print(f"  {k:22} {v:4}  ({100*v/tot:4.0f}%)")
    print(f"  {'questions':22} {gm['questions']:4}")

    print("\n" + "=" * 68)
    print("EXAMPLES — question -> comprehended? -> band/stance -> reply")
    print("=" * 68)
    shown = 0
    for e in log:
        if shown >= 8:
            break
        q = (e["question"][:90] + "...") if len(e["question"]) > 90 else e["question"]
        print(f"\nQ: {q}")
        print(f"   gold: {str(e['gold'])[:50]}")
        print(f"   comprehended={e['comprehended']}  speech_act={e['speech_act']}  "
              f"band={e['band']}")
        st = (e["stance"] or e.get("error") or "")
        print(f"   stance: {st[:110]}")
        print(f"   reply:  {str(e['reply'])[:110]}")
        shown += 1

    # honest read-out
    nc = gm["not_comprehended"]
    mis = gm["miscomprehended_assert"]
    echo = gm["degenerate_echo"]
    real = gm["answered_grounded"]
    print("\n" + "-" * 68)
    print("HONEST READ-OUT")
    print(f"  · The grounded MATH is reachable from talking now (single entity):"
          f" a question dispatches to the capability layer (the reason.py tower)"
          f" — verified separately, 'gcd of 48 and 36' -> 12, 'is 91 prime' ->"
          f" False, correct, through the conversation.")
    print(f"  · But on HLE's RESEARCH prose the gap is upstream and TWO-fold:")
    print(f"    GAP 1 (comprehension): {nc} never parse; {mis} mis-read as "
          f"ASSERTIONS and silently 'stored' ('OK'); {echo} dispatch to the "
          f"capability but the parse is DEGENERATE — it echoes a token "
          f"('G', 'order', 'X'), not a real computation. {100*(nc+mis+echo)/tot:.0f}% "
          f"never shaped the question into a computable meaning.")
    print(f"    GAP 2 (capability SCOPE): the tower is computational number "
          f"theory + linear algebra (gcd/primality/factorial/...), not research "
          f"topology/bordism/Lie-cohomology — so even a clean parse has no "
          f"capability for these. genuine grounded computes: {real}.")
    print(f"  · correct={gm['correct']} (expected ~0 on research math). The "
          f"earlier 'no grounded math' read was WRONG — the math is there and "
          f"now reachable from talk; the wall is comprehension-of-hard-prose + "
          f"tower scope. This maps the GAP, it is not a score.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
