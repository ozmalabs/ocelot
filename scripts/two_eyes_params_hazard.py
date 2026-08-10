"""THE ACTUAL OBSTACLE: `Pick(NodesOfType("WaveParams"))`.

The populations are hub-anchored and already multi-instantiable (verified by
two_eyes_feasibility.py). The ONE thing that is genuinely a singleton is the
PARAMS node: every rule reads its config via `Pick(NodesOfType("<X>Params"))`.

That is fine while there is exactly ONE params node — every eye shares one
config, which is the correct default. It becomes a HAZARD the moment a per-eye
arm is needed (monocular deprivation: one eye open, one deprived), because the
obvious move — mint a second params node — makes `Pick` select among TWO, and
`Pick` has no defined choice. If that is nondeterministic, it does not merely
break the second eye: it silently repoints EVERY committed vision result at an
arbitrary config.

This asks the question rather than assuming the answer.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains import engine_provenance as ep  # noqa: E402

ep.engine_preamble()

from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402


def main() -> None:
    print(ep.provenance_line())
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves"])

    existing = list(s.nodes("WaveParams"))
    print(f"\nWaveParams nodes after boot: {len(existing)} -> {existing}")

    import substrate_rs as S

    # Read the params node's OWN name attr through the exact Term shape every
    # vision rule uses: Attr(Pick(NodesOfType("WaveParams")), "name").
    # NodesOfType has no named constructor export; build it via the generic
    # Term wire form, which is what the seed JSON uses anyway.
    pick_name = S.Term("Attr",
                       node=S.Term("Pick",
                                   source=S.Term("NodesOfType",
                                                 node_type="WaveParams")),
                       key="name")

    def read(term):
        # NO bare except: an error must be LOUD, not a value. The first cut of
        # this probe swallowed an AttributeError into a string and then
        # compared the strings for determinism — 8 identical error messages
        # read as "deterministic". An inert instrument, mine, caught by
        # PROTOCOL 1. It raises now.
        return term.evaluate(None, s)

    print("\n--- ONE params node (the committed situation) ---")
    for _ in range(3):
        print("  Pick.name ->", read(pick_name))

    # Mint a SECOND params node, as a per-eye arm would have to.
    second = s.add_node("WaveParams", {"name": "right_eye", "propagate": 1.0,
                                       "oja": 1.0})
    print(f"\n--- TWO params nodes (minted {second}) ---")
    print(f"WaveParams nodes now: {list(s.nodes('WaveParams'))}")
    picks = [str(read(pick_name)) for _ in range(8)]
    print("  Pick.name x8 ->", picks)
    print(f"  DETERMINISTIC within a process: {len(set(picks)) == 1}")
    print(f"  picked values seen: {sorted(set(picks))}")

    # The question that actually matters: can a rule reach params BY TRAVERSAL
    # from its own hub instead? That requires an edge the production must allow.
    print("\n--- is a hub->params edge admissible today? ---")
    retina = s.add_node("Retina", {"h": 4.0, "w": 4.0, "step": 0.0})
    try:
        s.add_edge(retina, "has_params", second, None)
        print("  Retina -has_params-> WaveParams  ADMITTED "
              "(production already exists)")
    except Exception as e:                            # noqa: BLE001
        print(f"  Retina -has_params-> WaveParams  REJECTED by Gamma: "
              f"{type(e).__name__}: {e}")
        print("  => the per-eye fix needs ONE new production, which is "
              "exactly the shape rung 8's compose seed used.")


if __name__ == "__main__":
    main()
