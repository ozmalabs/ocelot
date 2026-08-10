#!/usr/bin/env python3
"""BIGVILLE sim-loop runner (scaffold). Runs the small-cast political drama as a
STEPPED spatial world through the per-agent occlusion-gated observation query,
and DUMPS every tick's graph-read-off state to JSON for the self-contained web
viewer (bigville_viewer_glassbox.html).

This is engineering scaffold, not a gated measurement rung. It reuses the PROVEN
block-245000 substrate + rules unchanged (own engine); it adds only the host
sim loop, the grid, the geometric perception gate, and the reporter/newspaper
mechanism. See BIGVILLE_BUILD_NOTES.md.

Run:  python scripts/bigville_sim_run.py
View: open results/bigville_sim/bigville_viewer_glassbox.html  (it fetches the
      JSON dumped alongside it; or the JSON is inlined by the packager below).
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))
sys.path.insert(0, ROOT)

from worlds.bigville_sim_world import BigvilleSimWorld    # noqa: E402

T = 20


def main():
    out_dir = os.path.join(ROOT, "results", "bigville_sim")
    os.makedirs(out_dir, exist_ok=True)

    # SEED ONCE -> live -> dump -> resume -> continue (persistence is load-bearing).
    w1 = BigvilleSimWorld(john_psychopath=True, mary_tom=True, deception=True)
    for _ in range(T // 2):
        w1.step()
    dump_path = os.path.join(out_dir, "bigville_checkpoint.json")
    w1.dump(dump_path)
    frames1 = list(w1.frames)
    w1.close()
    w = BigvilleSimWorld.resume(dump_path)     # no re-seed; same rules, saved state
    resumed_from = w.tick
    for _ in range(T - w.tick):
        w.step()
    frames = frames1 + list(w.frames)          # full timeline across the checkpoint
    payload = dict(block="bigville_scaffold", T=T, n_frames=len(frames),
                   frames=frames)
    with open(os.path.join(out_dir, "bigville_state.json"), "w") as f:
        json.dump(payload, f, indent=1)

    # Package a self-contained viewer with the state INLINED (CSP-safe: no fetch,
    # no external host) from the template next to this script's sibling viewer.
    tmpl_path = os.path.join(ROOT, "worlds", "bigville_viewer_glassbox.html")
    if os.path.exists(tmpl_path):
        with open(tmpl_path) as f:
            html = f.read()
        inlined = html.replace(
            "/*__BIGVILLE_STATE__*/null",
            json.dumps(payload))
        with open(os.path.join(out_dir, "bigville_viewer_glassbox.html"), "w") as f:
            f.write(inlined)

    # a terse text read-out proving the state is READ from the graph, not mocked
    last = frames[-1]
    john = next(i for i in last["inhabitants"] if i["id"] == "John")
    mary = next(i for i in last["inhabitants"] if i["id"] == "Mary")
    rep = next(i for i in last["inhabitants"] if i["id"] == "reporter")
    print("=== BIGVILLE scaffold: seed-once -> live -> dump -> resume ===")
    print("checkpoint dumped at tick %d, resumed at tick %d, ran to %d (no re-seed)"
          % (T // 2, resumed_from, T))
    print("=== final-tick glass-box read-off (from graph) ===")
    print("JOHN  ", json.dumps(john["state"]))
    print("       perceives:", json.dumps(john["perceives"]))
    print("  THREE LAYERS (held / journal / face):")
    for k in ("held", "journal", "face"):
        print("    %-8s %s" % (k + ":", john["three_layer"][k]))
    print("    self_deception:", john["three_layer"]["self_deception"])
    print("MARY  ", json.dumps(mary["state"]))
    print("       perceives:", json.dumps(mary["perceives"]))
    print("  MARY journal:", mary["three_layer"]["journal"])
    print("REPORTER", json.dumps(rep["state"]))
    print("NEWSPAPER", json.dumps(last["newspaper"]))
    print("VILLAGER BACKING (perception-gated):")
    for i in last["inhabitants"]:
        if i["state"]["role"] == "villager":
            s = i["state"]
            print("   %s charm=%d seen_ben=%d seen_hos=%d heard=%d -> backs %s"
                  % (s["name"], s["charm_weight"], s["seen_benevolent"],
                     s["seen_hostile"], s["heard_claim"], s["backs"]))
    print("wrote:", os.path.join(out_dir, "bigville_state.json"))


if __name__ == "__main__":
    main()
