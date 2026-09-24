"""Capability graph — the agent's measured, dynamic self-model of competence.

Gates seeds/capability_graph.json + domains/capability_graph.py. Core-ness is not an
enum: it's recursive leverage-centrality on the composes_on graph, and it MOVES. And
capability is multiplicative composition — a skill is bottlenecked by the product of
its foundations — which is why mastered core competencies multiply into new domains
(the generalist approaches the expert), and why the shape-matching faculty that forms
the 'this is like X but Y' edges is the highest-leverage skill of all.
"""
from __future__ import annotations

import json
import os

from substrate_rs import _native
from domains.capability_graph import (
    mint_root, add_capability, compose, like_but, settle,
    leverage, eff_cap, sufficiency, stage, most_leveraged, genericity,
    add_shaped, add_agent, owns, model_attempt, magic, legibility,
    hold, add_frame, acquire, new_skill_fraction, acquisition_split,
    judge_trial, correctness, own_proficiency,
)

_SEED = os.path.join(os.path.dirname(__file__), "..", "seeds", "capability_graph.json")
_NODE = ("CapabilityRoot", "Capability", "CapabilityPolicy", "Agent", "ModelAttempt",
         "Frame", "FrameAcquisition", "CapabilityTrial")
_EDGE = ("has_capability", "composes_on", "owns", "observer", "target",
         "requires", "by", "into", "trial_of")


def _fresh():
    s = _native.Substrate()
    for a in _NODE:
        for b in _NODE:
            for et in _EDGE:
                s.add_production({"src": {"type": a, "var": "s"}, "edge_type": et,
                                  "tgt": {"type": b, "var": "t"}, "where": None,
                                  "weight": {"type": "Lit", "value": 1.0}, "provenance": "t"})
    for r in json.load(open(_SEED))["rules"]:
        s.add_rule(r)
    return s, mint_root(s)


def test_leverage_is_recursive_centrality_not_an_enum():
    """A foundational capability that four domains compose_on accrues high leverage;
    the leaf domains stay at 1. Core-ness is this measured centrality, and the stage
    label (blob/peripheral/core) is a derived region on it, never a set flag."""
    s, root = _fresh()
    core = add_capability(s, root, "graph_collapse", 0.9)
    doms = [add_capability(s, root, f"d{i}", 0.7) for i in range(4)]
    for d in doms:
        compose(s, d, core)
    settle(s)
    assert abs(leverage(s, core) - (1 + 0.6 * 4)) < 1e-6, "1 + damping*sum(dependents)=3.4"
    assert leverage(s, doms[0]) == 1.0, "a leaf depends-on nothing -> leverage 1"
    assert stage(s, core) == "core" and stage(s, doms[0]) == "blob"
    receipts = list(s.nodes("NativeCapabilityGraphReceipt"))
    assert len(receipts) == 1
    attrs = s.node(receipts[0])["attrs"]
    assert attrs["provenance"] == "native_rule_readback:capability_graph"
    assert attrs["outcome_source"] == "native_rule_readback"
    assert attrs["python_outcome_selection"] is False


def test_effective_capability_is_multiplicative():
    """eff_cap(A) = own_prof(A) * PROD of foundations' eff_cap. Composed capability is
    the product, not the sum — a weak link drags the whole."""
    s, root = _fresh()
    a = add_capability(s, root, "foundation", 0.8)   # composes on nothing -> eff 0.8
    b = add_capability(s, root, "built_on_a", 0.5)
    compose(s, b, a)
    settle(s)
    assert abs(eff_cap(s, a) - 0.8) < 1e-6
    assert abs(eff_cap(s, b) - 0.5 * 0.8) < 1e-6, "0.5 * 0.8 = 0.40"


def _specialist(s, root, tag, core_prof, domain_prof, k):
    cores = [add_capability(s, root, f"{tag}_c{i}", core_prof) for i in range(k)]
    dom = add_capability(s, root, f"{tag}_dom", domain_prof)
    for c in cores:
        compose(s, dom, c)
    return dom


def test_generalist_with_mastered_core_approaches_then_overtakes_expert():
    """The headline. A generalist (mastered core ~0.98, THIN domain 0.5) vs a domain
    expert (mastered domain 0.95, ordinary core ~0.8). Because capability is a product,
    the expert's ordinary core decays as 0.8^k while the generalist's mastered core holds
    — so the deeper the composition, the more the generalist overtakes the specialist."""
    # shallow task (k=1): the expert's mastered domain still wins
    s, root = _fresh()
    g1 = _specialist(s, root, "gen1", 0.98, 0.5, 1)
    e1 = _specialist(s, root, "exp1", 0.80, 0.95, 1)
    settle(s)
    assert eff_cap(s, e1) > eff_cap(s, g1), "at depth 1 the specialist's mastered domain leads"

    # deep task (k=5): mastered core multiplies; the generalist overtakes from thin familiarity
    s, root = _fresh()
    g5 = _specialist(s, root, "gen5", 0.98, 0.5, 5)
    e5 = _specialist(s, root, "exp5", 0.80, 0.95, 5)
    settle(s)
    assert eff_cap(s, g5) > eff_cap(s, e5), \
        f"deep composition: generalist {eff_cap(s,g5):.3f} overtakes expert {eff_cap(s,e5):.3f}"


def test_leverage_is_dynamic_blob_to_core():
    """A capability climbs blob->core as dependents accrue — 'graph-collapse was a vague
    blob six months ago, core now'. Not a relabel: the measured centrality moves."""
    s, root = _fresh()
    x = add_capability(s, root, "graph_collapse", 0.9)
    settle(s)
    assert stage(s, x) == "blob" and leverage(s, x) == 1.0, "isolated skill: a blob"
    for i in range(4):                                   # things start composing on it
        compose(s, add_capability(s, root, f"user{i}", 0.7), x)
    settle(s)
    assert leverage(s, x) > 3.0 and stage(s, x) == "core", \
        f"as dependents accrue it climbs to core: leverage {leverage(s,x):.2f}"


def test_sufficiency_throttle_is_leverage_modulated():
    """The competent-man '~90% then move on' cutoff is f(leverage): ~0.9 for a low-leverage
    blob, toward 1.0 for a high-leverage core — never 'done' with a core skill."""
    s, root = _fresh()
    core = add_capability(s, root, "language", 0.9)
    for i in range(6):
        compose(s, add_capability(s, root, f"use{i}", 0.7), core)
    leaf = add_capability(s, root, "trivia", 0.9)
    settle(s)
    assert abs(sufficiency(s, leaf) - 0.9) < 1e-6, "low leverage -> move on at ~0.9"
    assert sufficiency(s, core) > 0.95, "high-leverage core -> never done (threshold toward 1)"


def test_expert_advantage_is_brittle_off_domain():
    """Well-observed: an expert's competency drops massively the moment they drift into a
    SURROUNDING area. The model predicts it — the expert mastered LOW-leverage domain-private
    skills (no composes_on edge into the neighbour), so off-domain they fall back to ordinary
    core and collapse below the generalist, who mastered high-leverage core that reaches the
    neighbour too. And leverage MEASURES the cause: the expert mastered low-leverage nodes."""
    s, root = _fresh()
    # EXPERT: ordinary core + a tall mastered tower of DOMAIN-PRIVATE skills.
    ec = [add_capability(s, root, f"ec{i}", 0.80) for i in range(4)]        # ordinary core
    tower = [add_capability(s, root, f"priv{i}", 0.97) for i in range(4)]   # mastered, domain-private
    home_e = add_capability(s, root, "expert_home", 0.95)
    for n in tower + ec[:1]:                       # home leans on the mastered private tower
        compose(s, home_e, n)
    adj_e = add_capability(s, root, "expert_adjacent", 0.40)                # a surrounding area
    for n in ec:                                   # the tower does NOT reach it — only ordinary core
        compose(s, adj_e, n)

    # GENERALIST: mastered high-leverage core, thin on both the home domain and its neighbour.
    gc = [add_capability(s, root, f"gc{i}", 0.98) for i in range(4)]        # mastered core
    home_g = add_capability(s, root, "gen_home", 0.50)
    adj_g = add_capability(s, root, "gen_adjacent", 0.40)
    for d in (home_g, adj_g):
        for n in gc:
            compose(s, d, n)
    settle(s)

    # On the expert's home turf, the expert wins.
    assert eff_cap(s, home_e) > eff_cap(s, home_g), "expert dominates their own domain"
    # One step out, the expert collapses — massively, and below the generalist.
    assert eff_cap(s, adj_e) < 0.4 * eff_cap(s, home_e), \
        f"expert drops massively off-domain: {eff_cap(s,home_e):.3f} -> {eff_cap(s,adj_e):.3f}"
    assert eff_cap(s, adj_g) > eff_cap(s, adj_e), \
        "in the surrounding area the generalist's mastered core beats the collapsed expert"
    # The measured cause: the expert mastered LOW-leverage nodes; the generalist HIGH-leverage.
    assert leverage(s, tower[0]) < leverage(s, gc[0]), \
        "leverage predicts brittleness: the expert's mastery sat on low-leverage private skills"


def test_expertise_is_how_not_whether():
    """Two experts with IDENTICAL competence in their domain — but one consolidated the
    domain onto generic high-leverage stacks (the user: 'expert at being an expert'), the
    other built a domain-private tower. Same eff_cap(D); opposite genericity; opposite
    off-domain behaviour. The domain label is not enough — you must know HOW."""
    s, root = _fresh()
    # GENERIC expert: domain skill sits on a shared, high-leverage generic stack (g0..g2),
    # which many other fields also use (that shared use is what makes it high-leverage).
    g = [add_capability(s, root, f"g{i}", 0.9) for i in range(3)]
    for j in range(4):                                   # other fields lean on the same stack
        other = add_capability(s, root, f"other{j}", 0.7)
        for n in g:
            compose(s, other, n)
    home_generic = add_capability(s, root, "home_generic", 0.7)
    for n in g:
        compose(s, home_generic, n)
    adj_generic = add_capability(s, root, "adj_generic", 0.7)      # a surrounding area
    for n in g:                                          # the generic stack reaches it too
        compose(s, adj_generic, n)

    # PRIVATE expert: identical own_prof and identical mastered-foundation values, but the
    # foundations are domain-PRIVATE (only this domain depends on them) -> low leverage.
    p = [add_capability(s, root, f"p{i}", 0.9) for i in range(3)]
    home_private = add_capability(s, root, "home_private", 0.7)
    for n in p:
        compose(s, home_private, n)
    oc = [add_capability(s, root, f"oc{i}", 0.8) for i in range(3)]  # ordinary (un-mastered) fallback
    adj_private = add_capability(s, root, "adj_private", 0.7)        # same surrounding area
    for n in oc:                                         # the private tower does NOT reach it
        compose(s, adj_private, n)
    settle(s)

    # Same domain competence — the label 'expert in D' is identical.
    assert abs(eff_cap(s, home_generic) - eff_cap(s, home_private)) < 1e-9, \
        "identical effective capability at home"
    # But genericity — HOW they are expert — is sharply different.
    assert genericity(s, home_generic) > 3.0 > genericity(s, home_private), \
        f"generic stack {genericity(s,home_generic):.2f} vs private tower {genericity(s,home_private):.2f}"
    # And it predicts the boundary: the generic expert transfers, the private one collapses.
    assert eff_cap(s, adj_generic) > eff_cap(s, adj_private), \
        "equal home competence, opposite off-domain outcome — you had to know HOW"


def test_magic_is_asymmetric_tom_residual():
    """'Magic' is the residual of a failed theory-of-mind, and it's asymmetric. A generalist
    holds the mind-modelling core (ToM/shape-matching), so they can model a specialist
    PARTIALLY (structural credit, little shared content). A tower expert consolidated that
    core away, so the generalist is near-pure magic to them — 'I can't even represent how
    you do that'. The tower expert finds the generalist MORE magical than the reverse."""
    s, root = _fresh()
    gen, tow = add_agent(s, "generalist"), add_agent(s, "tower_expert")

    # Generalist: a strong mind-modelling core + generic stacks; competence built on them.
    g_meta = add_shaped(s, root, "gen_modelling", 0.95, "modelling_core")
    g_stack = [add_shaped(s, root, f"gs{i}", 0.9, f"generic{i}") for i in range(3)]
    g_comp = add_capability(s, root, "gen_competence", 0.7)
    owns(s, gen, g_meta)                                # holds the modelling core (used to read others)
    for n in g_stack:
        owns(s, gen, n)
        compose(s, g_comp, n)                           # competence built on the generic stacks

    # Tower expert: the modelling core ATROPHIED (0.2) + a domain-private tower.
    t_meta = add_shaped(s, root, "tow_modelling", 0.2, "modelling_core")
    t_tower = [add_shaped(s, root, f"tp{i}", 0.9, f"private{i}") for i in range(3)]
    t_comp = add_capability(s, root, "tow_competence", 0.7)
    owns(s, tow, t_meta)                                # holds an atrophied modelling core
    for n in t_tower:
        owns(s, tow, n)
        compose(s, t_comp, n)                           # competence built on the private tower

    m_gen_reads_tower = model_attempt(s, gen, t_comp)   # generalist models the specialist
    m_tow_reads_gen = model_attempt(s, tow, g_comp)     # specialist models the generalist
    settle(s)

    assert magic(s, m_tow_reads_gen) > magic(s, m_gen_reads_tower), (
        f"the tower expert finds the generalist more magical "
        f"({magic(s,m_tow_reads_gen):.2f}) than the reverse ({magic(s,m_gen_reads_tower):.2f})")
    assert magic(s, m_tow_reads_gen) > 0.85, "with no modelling core, the generalist is near-pure magic"
    assert legibility(s, m_gen_reads_tower) > 0.25, "the generalist can at least model the STRUCTURE"


def test_correctness_is_measured_from_judged_trials():
    """The success oracle, generalised. A capability accrues judged trials (supported/refuted
    against an oracle — the reflex-net judge lifted to any capability); its correctness is the
    supported-rate, and that becomes its own_proficiency so effective capability reflects
    RIGHT answers, not just cheap ones."""
    s, root = _fresh()
    good = add_capability(s, root, "reliable_skill", 0.5)   # own_prof starts at an efficiency guess
    poor = add_capability(s, root, "shaky_skill", 0.5)
    for _ in range(8):
        judge_trial(s, good, "supported")
    for _ in range(2):
        judge_trial(s, good, "refuted")                     # 8/10 supported
    for _ in range(3):
        judge_trial(s, poor, "supported")
    for _ in range(7):
        judge_trial(s, poor, "refuted")                     # 3/10 supported
    settle(s)

    assert abs(correctness(s, good) - 0.8) < 1e-9, "supported-rate 8/10"
    assert abs(correctness(s, poor) - 0.3) < 1e-9, "supported-rate 3/10"
    assert own_proficiency(s, good) == 0.8, "correctness becomes own_prof once judged"
    assert eff_cap(s, good) > eff_cap(s, poor), \
        "effective capability now reflects measured rightness, not the efficiency guess"


def test_new_frame_is_dimensional_transform_for_the_metaskilled():
    """The real finding: for a sufficiently meta-skilled agent, a new frame requires only
    DIMENSIONAL TRANSFORMS of held generic shapes (rung 2) and almost NO new actual skills
    (rung 4). A narrow agent, lacking the base-shapes, must mint most of them anew."""
    s, root = _fresh()
    frame = add_frame(s, "new_field", ["compose", "invert", "map", "search", "abstract"])

    # Meta-skilled agent: holds all the generic base-shapes, just in OTHER frames.
    meta = add_agent(s, "metaskilled")
    for b in ["compose", "invert", "map", "search", "abstract"]:
        hold(s, meta, b, frame="some_other_field")
    # Narrow agent: holds only two of the base-shapes.
    narrow = add_agent(s, "narrow")
    for b in ["compose", "search"]:
        hold(s, narrow, b, frame="home")

    a_meta = acquire(s, meta, frame)
    a_narrow = acquire(s, narrow, frame)
    settle(s)

    nm, tm = acquisition_split(s, a_meta)
    assert nm == 0 and tm == 5, "the meta-skilled agent needs ZERO new skills — all transforms"
    assert new_skill_fraction(s, a_meta) == 0.0
    assert new_skill_fraction(s, a_narrow) == 0.6, "the narrow agent must mint 3 of 5 anew"
    assert new_skill_fraction(s, a_narrow) > new_skill_fraction(s, a_meta), \
        "a new frame is a change of coordinates for the generic, new structure for the narrow"


def test_shape_matching_is_the_meta_skill():
    """'This is like X but Y' — the meta-skill. New domains enter by shape-matching to a
    mastered analogue X (inherit its mastered decomposition) plus the shape faculty that
    saw the analogy. Two payoffs: (1) recognizing 'like X but Y' vastly beats rebuilding
    the domain from thin novel parts; (2) shape-matching, being what every analogy composes
    on, is the HIGHEST-leverage capability — the thing worth mastering first."""
    s, root = _fresh()
    shape = add_capability(s, root, "shape_matching", 0.97)     # the meta-skill, mastered
    subs = [add_capability(s, root, f"s{i}", 0.95) for i in range(4)]
    x = add_capability(s, root, "domain_X", 0.97)               # a mastered analogue domain
    for sub in subs:
        compose(s, x, sub)
    compose(s, x, shape)
    # enter three new fields as "like X but Y" (thin novel proficiency, recognized via shape)
    news = [like_but(s, root, f"like_X_{i}", x, 0.5, shape_cap=shape) for i in range(3)]
    # a control: the SAME kind of field learned from scratch — 4 thin novel sub-skills
    nsub = [add_capability(s, root, f"n{i}", 0.5) for i in range(4)]
    scratch = add_capability(s, root, "from_scratch", 0.9)
    for n in nsub:
        compose(s, scratch, n)
    settle(s)

    assert eff_cap(s, news[0]) > 5 * eff_cap(s, scratch), (
        f"'like X but Y' ({eff_cap(s,news[0]):.3f}) >> building from scratch "
        f"({eff_cap(s,scratch):.3f}): the analogy reuses mastered structure")
    top = most_leveraged(s, root)
    assert top is not None and s.node(top)["attrs"]["name"] == "shape_matching", (
        "shape-matching is the highest-leverage skill — every analogy composes on it")
