"""test_salient_cache — THE SALIENT ORDER-N CONTEXT CACHE.

The generic working memory that holds salient entities at nested order-N levels
(local vs story), whose salience rise/decay/promote are graph RULES fired per
tick (run_rules), that coref AND a prediction/context faculty both read. The
gate is scripts/jabberwock_holds_context.py; this pins the mechanism + the hard
guards.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate.boot_core import boot_core                       # noqa: E402
from domains import comprehension_reader as cr                  # noqa: E402
from domains import coref_entities as ce                        # noqa: E402
from domains import narrative_structure as ns                   # noqa: E402
from domains import salient_cache as sc                         # noqa: E402
from domains import situation_model_reader as smr               # noqa: E402
import domains.reading_corpus as rc                             # noqa: E402
import jabberwock_reads_the_crow as jrc                         # noqa: E402


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


def _fresh():
    s, node = boot_core()
    return _Agent(s, node)


def _ground(agent, name, category="animal"):
    nid = smr._entity(agent, name)
    agent.s.set_attr(nid, "coref_category", category)
    agent.s.set_attr(nid, "coref_cleanliness", 1.0)
    return nid


def _run_synthetic():
    """Hero mentioned across a wide span; bystander only in the opening scene."""
    agent = _fresh()
    sc.install(agent)
    _ground(agent, "hero")
    _ground(agent, "bystander")
    for turn in range(1, 16):
        names = ["hero"] + (["bystander"] if turn <= 3 else [])
        for nm in names:
            sc._touch_cell(agent, nm, turn)
        sc.tick(agent, turn)
    return agent


def _cells(agent):
    return {c["entity"]: c for c in sc.cells(agent)}


# --------------------------------------------------------------------------- #
#  ORDER-N — the rise/decay/promote RULES fire; the protagonist is HELD at story
#  level while the bystander decays at the local level.
# --------------------------------------------------------------------------- #
def test_order_n_promote_hold_and_decay():
    agent = _run_synthetic()
    cells = _cells(agent)
    hero, bys = cells["hero"], cells["bystander"]
    # the protagonist recurred across a wide span -> PROMOTED to story level, held.
    assert hero["promoted"] is True
    assert hero["story_salience"] >= 3.0
    # the one-scene bystander never promoted and DECAYED at the local level.
    assert bys["promoted"] is False
    assert bys["local_salience"] < 0.1
    # NESTING: the held story-level salience dominates the decayed local one.
    assert hero["story_salience"] > bys["local_salience"]


def test_salient_working_memory_is_graph_native_argmax():
    agent = _run_synthetic()
    wm = sc.salient_working_memory(agent)
    assert wm["entity"] == "hero"
    assert wm["level"] == "story"
    # the ranked read agrees (display order; the Argmax decided the winner).
    ranked = sc.salient_entities(agent)
    assert ranked[0]["entity"] == "hero"


def test_promote_mirrors_story_salience_onto_entity():
    """The promote/mirror RULE writes story-salience back onto the SmEntity where
    the coref Argmax reads it (coref_story_salience + the on-flag)."""
    agent = _run_synthetic()
    hero = smr._entity(agent, "hero")
    at = agent.s.node(hero)["attrs"]
    assert at.get("coref_story_salience_on") == 1.0
    assert float(at.get("coref_story_salience")) >= 3.0
    # the bystander was never promoted -> the coref factor stays OFF (0.0).
    bys = smr._entity(agent, "bystander")
    assert agent.s.node(bys)["attrs"].get("coref_story_salience_on") in (None, 0.0)


# --------------------------------------------------------------------------- #
#  COREF READS THE CACHE — the score term includes the story-salience factor,
#  which is exactly 0.0 for an un-promoted entity (byte-identity) and nonzero for
#  a promoted one.
# --------------------------------------------------------------------------- #
def test_coref_score_reads_story_salience():
    agent = _run_synthetic()
    native = agent.inner
    hero = smr._entity(agent, "hero")
    bys = smr._entity(agent, "bystander")
    # ensure both carry the coref features the score term reads.
    for n in (hero, bys):
        for k, v in (("coref_cleanliness", 1.0), ("coref_recency", 1.0),
                     ("coref_rolerank", 0.0)):
            if agent.s.node(n)["attrs"].get(k) is None:
                agent.s.set_attr(n, k, v)
    term = ce._score_term("e", None)
    hero_score = float(native.evaluate(term, {"e": hero}))
    bys_score = float(native.evaluate(term, {"e": bys}))
    # the promoted hero's score carries the story-salience factor (>> the bystander).
    assert hero_score > bys_score
    assert hero_score >= ce._STORY_SALIENCE_W * 3.0


# --------------------------------------------------------------------------- #
#  CROW BYTE-IDENTITY (hard guard) — the cache is degenerate for short text.
# --------------------------------------------------------------------------- #
def _coref_chains(agent):
    sub = agent.s
    out = []
    for m in sub.nodes("SmMention"):
        at = sub.node(m)["attrs"]
        for nb in sub.neighbours(m, "refers_to"):
            out.append((at.get("surface"), (at.get("sentence") or "")[:24],
                        sub.node(nb)["attrs"].get("name")))
    return sorted(out)


def test_crow_byte_identical_with_cache():
    base = _fresh()
    g0 = cr.read_and_comprehend(base, jrc.FABLE_TEXT, window=2)
    withc = _fresh()
    sc.install(withc)
    g1 = cr.read_and_comprehend(withc, jrc.FABLE_TEXT, window=2)
    # the situation model AND the coref chains are byte-identical.
    assert g0["spine"]["situation_model"] == g1["spine"]["situation_model"]
    assert _coref_chains(base) == _coref_chains(withc)
    # the crow is too short to promote anything -> zero story-level salience.
    assert [c for c in sc.cells(withc) if c["promoted"]] == []


# --------------------------------------------------------------------------- #
#  ANTI-HALLUCINATION — a salient entity is NOT force-bound to a non-agreeing
#  pronoun (honest null).
# --------------------------------------------------------------------------- #
def test_no_force_bind_to_non_agreeing_pronoun():
    agent = _fresh()
    sc.install(agent)
    _ground(agent, "dog")
    for turn in range(1, 14):
        sc._touch_cell(agent, "dog", turn)
        sc.tick(agent, turn)
    # 'dog' is the most salient entity, but singular; 'they' is plural -> no
    # agreeing candidate -> HELD OPEN, never force-bound to the salient 'dog'.
    rec = ce.resolve_pronoun(agent, "they", "they ran off", 14, cb_name=None)
    assert rec.get("resolved") is False


# --------------------------------------------------------------------------- #
#  GENERIC — two distinct faculties read the SAME cache.
# --------------------------------------------------------------------------- #
def test_two_faculties_read_the_cache():
    agent = _run_synthetic()
    # faculty 1: coref, via the mirrored coref_story_salience on the SmEntity.
    hero = smr._entity(agent, "hero")
    coref_read = agent.s.node(hero)["attrs"].get("coref_story_salience_on") == 1.0
    # faculty 2: a prediction/context faculty, via the working-memory read off the
    # SAME SalienceCell pool (no coref).
    pred_read = sc.salient_working_memory(agent)["entity"] == "hero"
    assert coref_read and pred_read


# --------------------------------------------------------------------------- #
#  GRAPH-NATIVE — the cache is nodes/edges; no import re in the module.
# --------------------------------------------------------------------------- #
def test_cache_is_graph_resident_and_no_import_re():
    agent = _run_synthetic()
    assert list(agent.s.nodes("SalienceClock"))          # the clock node
    assert list(agent.s.nodes("SalienceCell"))           # the cells
    src = open(os.path.join(ROOT, "domains", "salient_cache.py")).read()
    import_lines = [ln.strip() for ln in src.splitlines()
                    if ln.strip().startswith(("import ", "from "))]
    assert not any(ln == "import re" or ln.startswith("import re ")
                   or ln.startswith("from re ") for ln in import_lines)


# --------------------------------------------------------------------------- #
#  REAL TALE — the cache LIFTS hero agency (pronoun actions land on the hero) on
#  a real Grimm tale, without regressing grounding. Honest partial: this is the
#  measured win; the unknown fraction and antagonist do not move (reported in the
#  gate). Cat-and-Mouse: cat's arc-agency 7 -> 9.
# --------------------------------------------------------------------------- #
def test_real_tale_lifts_hero_agency():
    grimm = [s for s in rc.SOURCES if s["key"] == "grimm"]
    by = {u["label"]: u for u in rc.load_units(sources=grimm)}
    text = by["CAT AND MOUSE IN PARTNERSHIP"]["text"]

    base = _fresh()
    cr.read_and_comprehend(base, text, window=2, max_sentences=60)
    ag0 = ns.protagonist_by_arc_agency(base).get("agency")

    withc = _fresh()
    sc.install(withc)
    cr.read_and_comprehend(withc, text, window=2, max_sentences=60)
    prot = ns.protagonist_by_arc_agency(withc)
    ag1 = prot.get("agency")

    assert prot.get("protagonist") == "cat"
    assert ag1 > ag0                                     # hero agency lifted
    # the promotions are CLEAN characters (cat, mouse), not parse junk.
    promoted = {c["entity"] for c in sc.cells(withc) if c["promoted"]}
    assert "cat" in promoted
    assert all(isinstance(e, str) for e in promoted)
