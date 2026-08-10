"""GALILEO / EQUIVALENCE PRINCIPLE — the robot discovers acc ⊥ mass by COMPRESSION.

The robot pushes N objects to discover their inertial MassScalar by action
(m = impulse/Δv, the landed mass_by_action primitive), and watches those same
objects fall (the eye tracks; the generic order-N loop mints the order-2 fall
generator). The NEW content is seeds/galileo.json: a GENERAL cross-object
generator codebook (recognize-or-mint keyed on the coeffs signature). Because
ONE fall generator explains EVERY object's fall regardless of mass, the REAL
world mints exactly ONE MotionGenerator{kind=fall} and RECOGNIZES it across all N
objects — while their MassScalars differ. "One generator across objects of
measured-different mass" IS acc ⊥ mass, read from the graph, un-seeded. The
ARISTOTLE control (heavier falls faster) mints N distinct generators
(mass-dependence). Same pipeline, same rules.

Every product is read from the run_rules graph state (the minted MotionGenerator
/ MassScalar / LatentDimension nodes) and the coeffs the TimeInfer Term produced
(tuples). No published mass; grouping by the eye's PERCEIVED Region.
"""
import domains.galileo_world as gwmod
from domains.falling_world import boot_falling

MASSES = [2, 3, 5]          # HIDDEN, untuned, never graphed; none is 1/4/9
MENU = [4, 6, 8, 10]        # impulse menu the robot probes (mass_by_action)
H, W, K = 120, 40, 3


def _real():
    wa = gwmod.boot_galileo()
    gw = gwmod.GalileoWorld(wa, H, W, K, MASSES, MENU, gravity_fn=lambda i: 1)
    gw.measure_masses(6)
    gw.watch_falls(6)
    return gw


def _aristotle():
    wa = gwmod.boot_galileo()
    # WRONG physics: fall acceleration DEPENDS on mass (heavier falls faster)
    gw = gwmod.GalileoWorld(wa, H, W, K, MASSES, MENU,
                            gravity_fn=lambda i: MASSES[i])
    gw.measure_masses(6)
    gw.watch_falls(6)
    return gw


def test_real_world_one_fall_generator_across_different_mass_objects():
    """REAL world: exactly ONE MotionGenerator{kind=fall} minted, RECOGNIZED
    across all N objects whose MassScalars are measured-different. acc ⊥ mass,
    read from the graph — un-seeded, no law predicate, no published mass."""
    gw = _real()

    masses = gw.minted_masses()
    assert masses == sorted(MASSES), masses            # 3 distinct masses, by push

    gens = gw.fall_generators()
    assert len(gens) == 1, gens                         # EXACTLY ONE fall generator
    sig, order = gens[0]
    assert order == 2                                   # uniform acceleration (order-2)
    assert sig == ((1, 0), (1, 0))                      # the shared coeffs (tuples)

    # one generator RECOGNIZED across N objects: 1 minted + (N-1) recognized
    statuses = sorted(s for s, _ in gw.fall_observation_status())
    assert statuses == ["minted", "recognized", "recognized"], statuses

    # acc ⊥ mass: ONE shared fall generator, N measured-DIFFERENT masses.
    assert len(gens) == 1 and len(set(masses)) == len(MASSES)


def test_aristotle_world_many_fall_generators_finds_mass_dependence():
    """ARISTOTLE control: fall acceleration DEPENDS on mass, so the objects fall
    at DIFFERENT accelerations -> N distinct MotionGenerators (no cross-object
    recognition) -> mass-DEPENDENCE correctly found. Same masses, same pipeline —
    only the world's gravity law differs. This is what makes the real-world
    result mean something: ONE (real) vs MANY (Aristotle)."""
    gw = _aristotle()

    masses = gw.minted_masses()
    assert masses == sorted(MASSES), masses             # SAME masses (push identical)

    gens = gw.fall_generators()
    assert len(gens) == len(MASSES), gens               # N distinct fall generators
    # each generator's acceleration equals that object's (mass-dependent) accel
    accels = sorted(sig[1][0] for sig, _ in gens)
    assert accels == sorted(MASSES), accels             # coeffs track the masses

    # every object MINTED its own generator (none recognized) — mass-dependence
    statuses = [s for s, _ in gw.fall_observation_status()]
    assert statuses.count("minted") == len(MASSES), statuses
    assert "recognized" not in statuses, statuses


def test_the_discriminator_one_vs_many():
    """The whole proof in one line: the SAME pipeline yields ONE fall generator in
    the real world and MANY in the Aristotle world, over the SAME measured masses.
    The number of fall generators IS the mass-(in)dependence verdict."""
    real, arist = _real(), _aristotle()
    assert len(real.fall_generators()) == 1
    assert len(arist.fall_generators()) == len(MASSES)
    assert real.minted_masses() == arist.minted_masses() == sorted(MASSES)


def test_cross_object_recognition_is_a_real_general_addition_not_free():
    """FALSIFY-avoidance evidence: the RAW order-N machinery (no galileo seed)
    mints a SEPARATE latent:time generator per Observation with NO cross-object
    recognition — two identical-acceleration falls -> two identical
    LatentDimension nodes. So the one-generator-for-all is NOT free; it needs the
    general recognize/dedup seeds/galileo.json adds. This test pins that the
    addition does real work (and is general — it dedups by the coeffs signature,
    never a physics acc==acc law)."""
    s, ag, native = boot_falling()   # eye + order-N + time_axis, but NO galileo seed
    DT = ["pred", "coord:r", "coord:c", "val"]

    def fall(a, n=6):
        cy, y, v = [], 0.0, 0.0
        for _ in range(n):
            cy.append(y); v += a; y += v
        return cy

    for _ in range(3):               # three IDENTICAL falls (same accel)
        cy = fall(1)
        frames = [[["obj", int(round(y)), 5, "obj"]] for y in cy]
        o = s.add_node("Observation", {"frames": frames, "dim_types": DT,
                                       "status": "motion_seq", "key": ["motion"]})
        s.add_edge(ag, "observed", o)
    native.run_rules()

    lds = [tuple(map(tuple, s.node(n)["attrs"].get("coeffs") or ()))
           for n in s.nodes("LatentDimension")
           if s.node(n)["attrs"].get("name") == "latent:time"]
    # THREE identical generators, NOT deduped — the raw loop has no cross-object
    # recognition; that is exactly what seeds/galileo.json supplies, generically.
    assert len(lds) == 3, lds
    assert len(set(lds)) == 1, lds


def test_no_published_mass_and_grouping_is_perceived():
    """No world node publishes mass/position/velocity/gravity/object-id. The
    MassScalar is reached ONLY through Region -has_mass-> (perceived grouping),
    and the fall MotionGenerator's signature is the perceived-trajectory coeffs —
    both DISCOVERED inferences, not world-published truths."""
    gw = _real()
    forbidden = {"mass", "position", "pos", "velocity", "vel", "vy", "vx",
                 "row", "col", "gravity", "g", "object_id", "obj_id", "oid",
                 "true_mass", "hidden_mass"}
    leaked = set()
    for n in gw.s.nodes("WorldInstance"):          # game hubs, cells, Body nodes
        leaked |= set(gw.s.node(n)["attrs"].keys()) & forbidden
    assert not leaked, f"world graph leaked forbidden attr(s): {leaked}"

    # every MassScalar is reached through a Region -has_mass-> edge (perceived)
    reached = 0
    for r in gw.s.nodes("Region"):
        for mn in gw.native.neighbours(r, "has_mass"):
            attrs = gw.s.node(mn)["attrs"]
            assert "object_id" not in attrs and "oid" not in attrs
            reached += 1
    assert reached >= len(MASSES), reached

    # the fall generator's identity is the perceived-trajectory coeffs (discovered)
    for sig, _ in gw.fall_generators():
        assert isinstance(sig, tuple) and sig                 # a coeffs signature
