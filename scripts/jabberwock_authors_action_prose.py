"""The jabberwock AUTHORS the REGISTER it narrates its actions in — so that every
time it acts it can say, in its own rendered prose, WHAT it is doing and WHY, and
that goes into the ARC-AGI API `reasoning` field (where 'thinking' is recorded).
(Creator: "say what it is doing and why in prose every time it takes an action.")

The agent already renders relations; here it acquires (1) a render rule that turns
an ACTION it takes into a first-person clause, and (2) the connective + a few REASON
phrasings keyed to its situation (just observing / moving its known body / seeking a
landmark). It asks its teacher, installs, verifies the engine renders a real
sentence, and persists. Python only supplies which reason fits the state; the surface
is the engine's.
"""
from __future__ import annotations
import json, os, re, sys
os.environ.setdefault("ARC3_THIN", "1")
sys.path.insert(0, "."); sys.path.insert(0, "scripts")
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from scripts.claude_teacher import make_ask

SEED = "seeds/action_prose.json"

Q = """A graph-native agent narrates each action it takes, in FIRST PERSON, as concise reasoning —
"what I am doing and why" — to record as its thinking. It renders with its own engine. I need you
to author the GRAMMAR as JSON.

(1) An "explain" render-rule TEMPLATE that reads an action node with a string attr "verb" (the
control it pressed, e.g. "Up","Down","Left","Right","Select") and renders a first-person clause that
states the action AND, after a connective, renders a reason. Template spec grammar (nested JSON):
  ["Cat", <item>, ...]                    sequence
  ["Surface","text","literal words"]      literal text
  ["Slot","verb"]                         value of the node's "verb" attr (a control name)
  ["Slot","connector"]                    value of the node's "connector" attr
  ["Render",["Slot","reason"]]            render the child reason node (recurse)
So the rendered sentence should read like: "I am pressing Up in order to <reason>." (your wording).

(2) The CONNECTIVE word, and three REASON phrasings (plain strings, first person, no leading "to"):
  - just OBSERVING (no goal yet, learning how the world works)
  - MOVING ITS OWN BODY (it has identified which figure is itself)
  - SEEKING a landmark it wants to reach (a cross on the floor)

Output ONLY this JSON between the markers (fill every field):
@@@grammar
{{"explain_template": <template spec>,
  "explain_binding": ["verb","connector","reason"],
  "connector": "...",
  "reason_observe": "...", "reason_move_body": "...", "reason_seek": "..."}}
@@@end{err}"""


def _check(agent, g):
    agent.install_relations_renderer()
    agent.install_render_rule("relations", "ActExplain",
        template=agent._spec_to_renderer_term(g["explain_template"]),
        binding_pattern=g["explain_binding"])
    out = {}
    for key in ("reason_observe", "reason_move_body", "reason_seek"):
        node = agent.s.add_node("ActExplain", {"verb": "Up", "connector": g["connector"]})
        reason = agent.s.add_node("Term.Leaf", {"form": g[key]})
        agent.inner.add_edge_unchecked(node, "child.reason", reason)
        out[key] = agent._render_node(node)
    ok = all(isinstance(v, str) and "Up" in v and len(v.split()) >= 6 for v in out.values())
    return ok, out


def run(max_repair=3):
    agent = WorldAdapter(seeds=()); load_all_seeds(agent)
    ask = make_ask(timeout=300.0, preamble="")
    prior = ""
    for attempt in range(1, max_repair + 2):
        print(f"--- consult attempt {attempt} ---", flush=True)
        m = re.search(r"@@@grammar\s*(.+?)\s*@@@end", ask(Q.format(err=prior)) or "", re.DOTALL)
        if not m:
            prior = "\n\nReturn ONLY the JSON between @@@grammar and @@@end."; continue
        try:
            g = json.loads(m.group(1).strip())
        except Exception as e:
            prior = f"\n\nJSON parse error: {e}."; print("  bad json:", e, flush=True); continue
        try:
            ok, out = _check(agent, g)
        except Exception as e:
            prior = f"\n\nInstalling/rendering raised {type(e).__name__}: {e}. Fix the template spec."
            print("  render raised:", e, flush=True); continue
        for k, v in out.items():
            print(f"  {k}: \"{v}\"", flush=True)
        if ok:
            json.dump(g, open(SEED, "w"), indent=2)
            print(f"\n✓ the jabberwock authored its action-reasoning register; persisted to {SEED}.", flush=True)
            return True
        prior = "\n\nSome sentences didn't mention the control 'Up' or were too short. Fix the wording."
        print("  invalid; feeding back.", flush=True)
    print("\n✗ action register not authored.", flush=True)
    return False


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
