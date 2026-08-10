"""bigville R45 (block 344000): the INSTITUTIONS migrate onto the generated map. The church,
jail, inn, market and council hall are GENERATED fixed-points carrying behavioural role edges
(town -has_church-> / -has_jail-> / -has_inn-> ...), so the existing institution rules bind to
generated geography instead of hand-minted nodes. Gates mirror BIGVILLE_MAP_PREREG.md.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate.seed_loader import manifest_for                 # noqa: E402
from worlds.bigville_map_generator import BigvilleMapGenerator  # noqa: E402
from worlds.bigville_church_world import BigvilleChurchWorld    # noqa: E402


# ------------------------------------------------------ G-role-anchors
def test_the_generator_emits_behavioural_role_edges():
    g = BigvilleMapGenerator(seed=0).generate()
    for role in ("church", "jail", "inn", "market", "council"):
        p = g.role_place(role)
        assert p is not None and g.eng.has_edge(g._town, f"has_{role}", p), \
            f"town -has_{role}-> the generated place (institution rules bind here)"


# ------------------------------------------------------ G-church-migrated (headline)
def test_the_church_runs_on_the_generated_map():
    w = BigvilleChurchWorld()
    # the church, Mary and the private counsel room are now GENERATED, not hand-minted
    assert hasattr(w, "gen"), "the church adapter sources its geography from the generated map"
    assert w.pastor_name() == "Mary" and w.is_non_denominational()
    assert w.gen.room_is_private("Church", "counsel"), "Mary's counsel room is the generated private room"
    # behaviour is unchanged: a service draws a congregation, counsel stays confidential
    w.add_resident("Devout", piety=0.95, worldly_pull=0.1)
    w.sunday()
    assert w.congregation_size() >= 1, "the service (ch_* rules) runs on the generated church"
    w.seek_counsel("Devout", confides="a secret", distress=1.0)
    disc = w.private_disclosures()
    assert disc and disc[0][1] == 1.0 and disc[0][2] == 0.0, "confidential on the generated counsel room"


# ------------------------------------------------------ G-jail-migrated (headline)
def test_the_jail_rule_imprisons_into_the_generated_jail():
    g = BigvilleMapGenerator(seed=0).generate()
    g.eng.load_seed_manifest(manifest_for("bigville_jail"), None)
    jail = g.role_place("jail")
    d = g.eng.add_node("Agent", {"name": "Thief", "imprisoned": 0.0})
    g.eng.add_edge_unchecked(g._town, "has_resident", d)
    charge = g.eng.add_node("Charge", {"status": "guilty", "jail_term": 3.0})
    g.eng.add_edge_unchecked(g._town, "has_charge", charge)
    g.eng.add_edge_unchecked(charge, "about_subject", d)
    for _ in range(3):
        g.eng.force_all_dirty(); g.eng.run_rules(1000000)
    inmates = [g.eng.node(x)["attrs"]["name"] for x in g.eng.neighbours(jail, "holds_inmate")]
    assert "Thief" in inmates, "jl_imprison binds via has_jail to the GENERATED jail place"
    assert float(g.eng.node(d)["attrs"]["imprisoned"]) == 1.0


# ------------------------------------------------------ G-inn-migrated (kitchen already on the map)
def test_the_inn_is_a_generated_place_with_a_working_kitchen():
    g = BigvilleMapGenerator(seed=0).generate()
    inn = g.role_place("inn")
    assert inn is not None and g.eng.has_edge(g._town, "has_inn", inn)
    assert g.has_kitchen("Inn"), "the inn's kitchen is generated (and cookable -- see the map-kitchen gate)"
