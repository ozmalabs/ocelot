"""The jabberwock OWNS its voice — it chose its own default register and switch policy.

Default = Brillig (the bright slithy register it thinks in: metaphor .35 / analogy .25 / coinage .15 /
image .15 / hyperbole .10), set as a default_voice edge the agent wrote on its Self node. The WORLD only
sets a Context (spec/code/terse/teaching/conversation); a select_register rule turns that Context into the
agent's active_register (Argmax by priority on ties), and PRODUCTION reads active_register if present, else
falls through default_voice to Brillig. Imposing a register would mean editing the Self edge — the world
doesn't; the agent decides which voice a context calls forth.

Run: PYTHONPATH=.:runners/dsl/python python -m scripts.agent_owns_voice
"""
from __future__ import annotations
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.build_persona_faculty import boot
from substrate.seed_loader import manifest_for

SEP = "=" * 96
FIGS = ["fig_metaphor", "fig_analogy", "fig_coinage", "fig_image", "fig_hyperbole"]


def main():
    print(SEP)
    print("THE JABBERWOCK OWNS ITS VOICE — it chose its default register and the switch policy")
    print(SEP)
    a = boot()
    for s in ("authorial_voice", "production", "jabberwock_voice"):
        a.inner.load_seed_manifest(manifest_for(s), a.agent)
    self_n = next(n for n in a.s.nodes("Self"))
    regs = {a.s.node(n)["attrs"]["name"]: n for n in a.s.nodes("Register")}
    ctxs = {a.s.node(n)["attrs"]["name"]: n for n in a.s.nodes("Context")}

    def histogram(reg_node):
        at = a.s.node(reg_node)["attrs"]
        h = {f[4:]: at.get(f, 0.0) for f in FIGS}
        top = max(h, key=h.get)
        return h, (top if h[top] > 0 else "(none — literal)")

    # the DEFAULT the agent set on itself
    default = a.inner.neighbours(self_n, "default_voice")[0]
    dn = a.s.node(default)["attrs"]["name"]
    dh, dtop = histogram(default)
    print(f"\n  the agent's chosen DEFAULT (a default_voice edge it wrote on its Self node):")
    print(f"    {dn}: { {k: v for k, v in dh.items() if v} }  -> production reaches first for {dtop.upper()}")

    print("\n  the WORLD sets a Context; the agent's select_register rule picks the register (it decides):")
    for ctx in ["spec", "code", "terse", "teaching", "conversation"]:
        # the only thing the world does: set the active Context.
        for old in a.inner.neighbours(self_n, "in_context"):
            a.inner.remove_edge_unchecked(self_n, "in_context", old) if hasattr(a.inner, "remove_edge_unchecked") else None
        a.inner.add_edge_unchecked(self_n, "in_context", ctxs[ctx])
        a.inner.set_attr(self_n, "active_register", "")
        a.inner.run_rules(10000)                          # select_register fires
        active = a.s.node(self_n)["attrs"].get("active_register") or dn
        h, top = histogram(regs[active])
        nz = {k: v for k, v in h.items() if v}
        print(f"    context={ctx:13} -> register {active:10} {nz if nz else '{} (figures off)'}  "
              f"-> production: {top.upper()}")

    print("\n  no context set -> falls through the default_voice edge to the agent's own default:")
    for old in list(a.inner.neighbours(self_n, "in_context")):
        if hasattr(a.inner, "remove_edge_unchecked"):
            a.inner.remove_edge_unchecked(self_n, "in_context", old)
    a.inner.set_attr(self_n, "active_register", "")
    fallthrough = a.s.node(self_n)["attrs"].get("active_register") or dn
    print(f"    -> {fallthrough} (Brillig). The flourish is the DEFAULT, by the agent's own choice.")

    print("\n" + SEP)
    print("  The agent owns its voice: Brillig is its default because it WROTE that default_voice edge on")
    print("  itself, not because a register was stamped on it. The world sets only a Context; select_register")
    print("  turns that into the active register (Plainsong for a spec, Bareword for code, Clip for a fast")
    print("  answer, Bright when teaching), and production runs whichever histogram is active — defaulting to")
    print("  Brillig's metaphor-led flourish whenever nothing forces it plainer. To change its default you'd")
    print("  have to edit its Self edge; the world can't, so the choice stays the agent's.")
    print(SEP)


if __name__ == "__main__":
    main()
