"""SCRATCH: what does a waves-only s.tick() actually mutate? Determines the
admissibility gate design. NOT a committed result."""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()
from substrate.boot_core import boot_core, load_seeds_into
import domains.seed_registry  # noqa
from domains.wave_world import WaveWorld


def snapshot(s):
    """Full per-node attr snapshot: {nid: {key: repr(val)}}."""
    out = {}
    for nid in s.nodes():
        at = s.node(nid)["attrs"]
        out[nid.value if hasattr(nid, "value") else int(str(nid))] = {
            k: repr(v) for k, v in at.items()}
    return out


def main():
    print(provenance_line())
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves"])
    s.set_attr(s.nodes("WaveParams")[0], "propagate", 1.0)
    w = WaveWorld(s, h=16, w=16, seed=0, fovea_radius=0)

    # node types present
    types = {}
    for nid in s.nodes():
        t = s.node(nid)["type"]
        types[t] = types.get(t, 0) + 1
    print("NODE TYPES PRESENT:", dict(sorted(types.items(), key=lambda x: -x[1])))

    # run some steps to get a live field, then isolate one tick's mutations
    for i in range(20):
        w.step(ignite_k=(1 if i % 5 == 0 else 0))

    before = snapshot(s)
    # do exactly what step() does EXCEPT the tick, then a bare tick, and see
    # what the tick alone changed.
    st = float(s.node(w.retina)["attrs"]["step"]) + 1.0
    s.set_attr(w.retina, "step", st)
    states = s.get_attr_many(w._cell_ids, "state")
    recruited = [n for n, stt in zip(w._cell_ids, states) if stt == "recruited"]
    if recruited:
        s.set_attr_many(recruited, "state", "active")
        s.set_attr_many(recruited, "activated_at", st)
    s.set_attr_many(w._cell_ids, "driven", 0.0)
    w.ignite(1)
    w._mark_bursts(st)
    s.set_attr_many(s.nodes("Unit"), "bursting", 0.0)
    pre_tick = snapshot(s)
    s.tick(200_000)
    post_tick = snapshot(s)

    # what did the tick change?
    changed_types = {}
    changed_keys = {}
    for nid, at in post_tick.items():
        pat = pre_tick.get(nid, {})
        allk = set(at) | set(pat)
        for k in allk:
            if at.get(k) != pat.get(k):
                t = s.node([n for n in s.nodes() if (n.value if hasattr(n,"value") else int(str(n))) == nid][0])["type"] if False else None
                changed_keys[k] = changed_keys.get(k, 0) + 1
    # simpler: map nid->type
    nid_type = {}
    for n in s.nodes():
        v = n.value if hasattr(n, "value") else int(str(n))
        nid_type[v] = s.node(n)["type"]
    for nid, at in post_tick.items():
        pat = pre_tick.get(nid, {})
        allk = set(at) | set(pat)
        if any(at.get(k) != pat.get(k) for k in allk):
            t = nid_type.get(nid, "?")
            changed_types[t] = changed_types.get(t, 0) + 1
    print("TICK CHANGED node-types:", changed_types)
    print("TICK CHANGED attr-keys :", changed_keys)


if __name__ == "__main__":
    main()
