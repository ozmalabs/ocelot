"""N EYES, M CORTICES — is the many-to-many projection ALREADY expressible?

The audit found ZERO population grabs: all 185 NodesOfType selections in the
vision tree read CONFIG nodes, and every rule is hub-anchored. So the question
is not "can we de-singleton the populations" (they were never singletons) but:

  1. can ONE cortex receive from TWO eyes?   (the ocular-dominance setup)
  2. can TWO cortices receive the SAME eyes? (the internal replication control)
  3. is N=0 / M=0 inert rather than a crash?

`add_signed_units` takes `bipolars` as a PARAMETER, so the eye->cortex
projection is already graph data rather than wiring. This asks whether that is
actually true, or only looks true.

NOT a rung. No pre-registration consumed, no confirmatory seed burned.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains import engine_provenance as ep  # noqa: E402

ep.engine_preamble()

from domains.onoff_world import add_onoff_retina, add_signed_units  # noqa: E402
from domains.wave_world import WaveWorld  # noqa: E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402


def boot():
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves", "vision_onoff"])
    return s


def eye_of(s, syn, eye_cells):
    """Which eye does this synapse's presynaptic bipolar belong to?"""
    for b in s.in_neighbours(syn, "oo_pre"):
        for c in s.in_neighbours(b, "drives"):
            for name, cells in eye_cells.items():
                if str(c) in cells:
                    return name
    return "?"


def main() -> None:
    print(ep.provenance_line())

    # ---- (1) ONE CORTEX, TWO EYES ----------------------------------------
    print("\n=== (1) ONE cortex receiving TWO eyes ===")
    s = boot()
    left = WaveWorld(s, h=16, w=16, seed=101)
    right = WaveWorld(s, h=16, w=16, seed=202)
    bl = add_onoff_retina(left)
    br = add_onoff_retina(right)
    print(f"left bipolars={len(bl)}  right bipolars={len(br)}")

    lcells = {str(v) for v in left.cells.values()}
    rcells = {str(v) for v in right.cells.values()}

    # Wire ONE unit population from EACH eye's bipolars, onto the SAME hub.
    # add_signed_units anchors has_sunit on world.retina, so pass `left` twice
    # and give it the RIGHT eye's bipolars for the second call: the unit's
    # administrative owner and its INPUT are independent facts.
    u_l = add_signed_units(left, bl, 2, rf=5, seed=1)
    u_r = add_signed_units(left, br, 2, rf=5, seed=1)
    print(f"units owned by left hub: {len(u_l) + len(u_r)}")

    for tag, us in (("from LEFT eye", u_l), ("from RIGHT eye", u_r)):
        u = us[0]
        srcs = {}
        for syn in s.in_neighbours(u, "oo_post"):
            e = eye_of(s, syn, {"L": lcells, "R": rcells})
            srcs[e] = srcs.get(e, 0) + 1
        print(f"  unit {tag}: synapse sources = {srcs}")

    # THE REAL QUESTION: can ONE unit be driven by BOTH eyes at once?
    print("\n  -- one unit wired from BOTH eyes --")
    merged = dict(bl)
    for k, v in br.items():                 # same (row,col,pol) keys COLLIDE
        merged[k] = v
    print(f"  merged bipolar dict: {len(merged)} entries "
          f"(left {len(bl)} + right {len(br)} = {len(bl) + len(br)})")
    print("  ^ the keys are (row,col,polarity) and the two eyes share a "
          "coordinate frame, so a plain dict merge SILENTLY DROPS one eye.")
    ub = add_signed_units(left, merged, 1, rf=5, seed=1)[0]
    srcs = {}
    for syn in s.in_neighbours(ub, "oo_post"):
        e = eye_of(s, syn, {"L": lcells, "R": rcells})
        srcs[e] = srcs.get(e, 0) + 1
    print(f"  merged-dict unit: synapse sources = {srcs}")

    # Wire binocularly the HONEST way: two calls onto one unit is not possible
    # through add_signed_units (it mints the unit), so do it by hand and see
    # whether Gamma admits a second eye's bipolar onto an existing SUnit.
    print("\n  -- does Gamma admit a SECOND eye's bipolar onto an existing SUnit? --")
    try:
        b_extra = br[(8, 8, 1)]
        syn = s.add_node("OOSynapse", {"weight": 1.0, "touched": -1.0,
                                       "drow": 0.0, "dcol": 0.0,
                                       "polarity": 1.0})
        s.add_edge(b_extra, "oo_pre", syn, None)
        s.add_edge(syn, "oo_post", u_l[0], None)
        srcs = {}
        for sy in s.in_neighbours(u_l[0], "oo_post"):
            e = eye_of(s, sy, {"L": lcells, "R": rcells})
            srcs[e] = srcs.get(e, 0) + 1
        print(f"  ADMITTED. unit now binocular: sources = {srcs}")
    except Exception as e:                            # noqa: BLE001
        print(f"  REJECTED: {type(e).__name__}: {e}")

    # ---- (2) TWO CORTICES, SAME EYES -------------------------------------
    print("\n=== (2) TWO cortices from the SAME eye ===")
    s2 = boot()
    eye = WaveWorld(s2, h=16, w=16, seed=101)
    b2 = add_onoff_retina(eye)
    cx_a = add_signed_units(eye, b2, 2, rf=5, seed=7)
    cx_b = add_signed_units(eye, b2, 2, rf=5, seed=7)
    print(f"cortex A units: {cx_a}")
    print(f"cortex B units: {cx_b}")
    print(f"disjoint unit sets: {not (set(map(str, cx_a)) & set(map(str, cx_b)))}")
    print("  ^ both hang off the SAME retina hub via has_sunit: there is no "
          "Cortex hub, so 'which cortex' is not a fact the graph holds.")

    # ---- (3) DEGENERATE: no eye at all ------------------------------------
    print("\n=== (3) N=0 — a graph with no eye ===")
    s3 = boot()
    print("  booted with zero Retina hubs; rules have nothing to match.")
    print(f"  Retina nodes: {list(s3.nodes('Retina'))}  "
          f"SUnit nodes: {list(s3.nodes('SUnit'))}")
    try:
        for _ in range(3):
            s3.tick()
        print("  tick() x3 on an eyeless graph: INERT (no crash)")
    except Exception as e:                            # noqa: BLE001
        print(f"  CRASHED: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
