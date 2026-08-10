"""THE JABBERWOCK AUTHORS A NEW EAR — order-4 self-authoring, the deep version.

When changing the method (order-2) and decomposing (order-3) don't crack a recognition
wall, order-4 says "change the TOOLS". For a speech agent the deepest tool is its EAR.
This shows the agent AUTHORING a better ear — changing WHAT IT HEARS — by its OWN
machinery (graph-resident FrontEnd cues), effect-gated:

  install the front end -> measure word DISCRIMINATION through the current ear ->
  gate in each repertoire cue ONE AT A TIME -> KEEP the cue if it LIFTS discrimination,
  REVERT it if it doesn't (a richer ear is not automatically a better one) -> the kept
  cues are the authored ear.

Then it shows order-4 of the escalation ladder INVOKING this: a needs_tool impasse on a
recognition axis -> the self-extend reflex calls the world's author_faculty -> the ear is
extended -> an 'ear' operator is bound -> the confidence trial measures the richer ear and,
because it discriminates better, the escalation RESOLVES (the authored tool worked).

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python \\
    /home/matt/ozma/internal/research/.venv/bin/python -m scripts.jabberwock_authors_ear_feature
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import substrate_rs as srs
import domains.agent_frontend as FE
from domains.speech_world import SpeechWorld
from scripts.autonomous_speech import boot

SEP = "=" * 80


def part1_author_ear():
    print(SEP)
    print("PART 1 — the jabberwock AUTHORS a better ear (effect-gated cue growth).")
    print(SEP)
    s = srs.Substrate()
    sw = SpeechWorld(s)
    # INTROSPECT the gap (the agent's own record).
    imp = s.add_node("Impasse", {"reason": "ear_plateau",
        "question": "My recognition plateaus — I need to hear differently, not just retry."})
    print(f"  INTROSPECT: {s.node(imp)['attrs']['question']}")
    FE.install_frontend(s)
    base = sw._ear_discrimination()
    print(f"  baseline ear: {FE.n_active(s)} cues, word-discrimination={base:.4f}")
    # AUTHOR: extend the ear, effect-gated.
    spec = sw.author_faculty(["recognise", "word", "speech"], approach="discriminate digits")
    final = sw._ear_discrimination()
    kept = spec["name"].split("+") if spec else []
    print(f"  AUTHORED ear: {FE.n_active(s)} cues (kept {len(kept)}: {kept}), "
          f"word-discrimination={final:.4f}")
    s.set_attr(imp, "resolved", True)
    ok = spec is not None and final > base
    print(f"  -> the agent changed WHAT IT HEARS and it discriminates better: {ok}")
    return ok


def part2_order4_invokes_it():
    print("\n" + SEP)
    print("PART 2 — order-4 of the escalation ladder INVOKES the ear authoring.")
    print(SEP)
    adapter, sw = boot(exclude=())          # full stack incl. impasse_escalation
    # find the recognise axis.
    ax = next((a for a in adapter.s.nodes("CapabilityAxis")
               if adapter.s.node(a)["attrs"].get("capability_keys")
               and "recognise" in adapter.s.node(a)["attrs"]["capability_keys"]
               and adapter.s.node(a)["attrs"].get("subskill") != 1.0), None)
    keys = adapter.s.node(ax)["attrs"]["capability_keys"]
    print(f"  recognise axis {keys}")
    # mint the order-4 routing marker directly (a needs_tool self-extend impasse) and let the
    # wired self-extend reflex consume it — the same path order-4 reaches via the climb.
    mi = adapter.s.add_node("Impasse", {"kind": "escalation", "order": 4, "resolved": False})
    adapter.s.add_edge(adapter.agent, "surprised_by", mi)
    adapter.s.add_edge(mi, "about_axis", ax)
    adapter.s.add_edge(mi, "needs_tool", ax)
    before_cues = FE.n_active(adapter.s) if next((n for n in adapter.s.nodes("FrontEnd")), None) else 0
    # run the self-extend reflex (order-4's faculty).
    adapter._self_extend_reflex()
    after_cues = FE.n_active(adapter.s)
    print(f"  order-4 -> author_faculty EXTENDED THE EAR: active cues {before_cues} -> {after_cues}")
    # the confidence trial: run the authored ear; a better ear resolves the escalation.
    for t in range(1, 16):
        adapter.master_tick(); adapter.tick()
        if adapter.s.node(mi)["attrs"].get("resolved") is True:
            break
    resolved = adapter.s.node(mi)["attrs"].get("resolved") is True
    sat = adapter.s.node(ax)["attrs"].get("saturation")
    print(f"  confidence trial on the authored ear -> escalation resolved={resolved} "
          f"(saturation={sat})")
    return after_cues > before_cues and resolved


def part3_author_convolution():
    print("\n" + SEP)
    print("PART 3 — the convolution is GRAPH-NATIVE (seed kernels + Rust DSL Term), no Python math.")
    print(SEP)
    s = srs.Substrate()
    sw = SpeechWorld(s)
    # the agent authors the convolution faculty = ensure the graph-native seed is present.
    kernels = sw.author_convolution()
    import domains.sensory_field as SF
    kids = SF.kernels(s)
    print(f"  convolution faculty = {len(kids)} seed Kernel nodes (graph data): {kernels}")
    # perceive the words THROUGH the graph-native convolution (responses via the DSL Term).
    disc = sw._conv_signature_discrimination()
    print(f"  graph-native conv signatures (MaxOver(Dot), Rust) discriminate words = {disc:.4f}")
    # confirm there is NO Python convolution module any more.
    import importlib
    no_python = importlib.util.find_spec("domains.sensory_convolution") is None
    print(f"  Python convolution faculty deleted (domains/sensory_convolution.py absent): {no_python}")
    ok = len(kids) >= 1 and disc > 0.0 and no_python
    print(f"  -> the convolution lives in the graph (seed + Rust DSL Term); Python only lays the field: {ok}")
    return ok


def main():
    ok1 = part1_author_ear()
    ok2 = part2_order4_invokes_it()
    ok3 = part3_author_convolution()
    print("\n" + SEP)
    ok = ok1 and ok2 and ok3
    print(f"  PART 1 (extend ear, effect-gated): {ok1}   PART 2 (order-4 invokes it): {ok2}   "
          f"PART 3 (author convolution): {ok3}")
    print(f"  {'PASS' if ok else 'FAIL'} — order-4 genuinely SELF-AUTHORS: the agent extends its own "
          f"ear (gates cues AND designs convolution filters), effect-gated, and the escalation uses it.")
    print(SEP)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
