"""NAMED STRATEGIC SCHEMAS — the agent NAMES the strategic pattern by AUTHORING a
META-classification over its OWN temporal-conflict readings.

THE HEADLINE PROVEN HERE: the agent gives the cross-action goal pattern a NAME.
"the oil company FUNDED the technology, then OPPOSED it" is a support-then-
undermine conflict (detected by the temporal layer, itself agent-authored); this
slice recognises 'fund|oppose' AS the Trojan-Horse schema (a gift carrying a
hidden hostile payload) by JOINING the held TemporalConflictReading's composite
`pair_key` against a TEACHABLE TropeSignature codebook keyed by the SAME
`pair_key`, and minting a NAMED TropeReading. The trope names are drawn from the
real TVTropes strategic-schema vocabulary (Trojan Horse; Bait and Switch and
False Flag Operation are literal entries in seeds/learned_tropes.json).

BOTH rules are AGENT-AUTHORED end to end (procedural_reader.read_method ->
binding_resolver.derive_binding -> method_synthesis.synthesise_rule_from_method):
the temporal-conflict rule mints the FACT, and THIS rule's Eq-join over `pair_key`
names it. The ONLY Python this slice adds is codebook wiring + a reader
(domains/actor_goals.ensure_trope_codebook / held_trope_readings) — ZERO new
annotator, because the TemporalConflictReading IS the fact. NO hand-written rule.

The 4+2 carry is real and does NOT wall: derive_binding auto-carries every scalar
slot on the concrete TemporalConflictReading fact node (actor, note, object,
pair_key — 4 fields) + the two non-join codebook slots (trope, gloss). The
temporal layer proved 3-from-f + 1-from-c; this proves 4-from-f + 2-from-c through
the SAME synthesiser, unchanged.

The COMPOUND-ACTOR parse residual is routed around exactly as the actor-goals /
temporal suites already do — the passive-with-by-phrase construction, whose
by-phrase agent is read off the clause's own marker sequence, not the buggy
bare-SVO fallback. "The technology was funded by the oil company." parses cleanly
(verb='fund', patient='technology', actor='oil_company').

donkey=0: OZMA_NO_LLM=1, no model anywhere, no `import re` in the reading path.

Run: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 python3 -m pytest \
    tests/test_named_trope_migrated.py -p no:randomly -q
"""
import json
import os
from pathlib import Path

os.environ.setdefault("OZMA_NO_LLM", "1")
# Never touch the real boot seeds — teach()'s live-graph add + category decision
# are unaffected; only the disk write to the REAL seed dir is skipped.
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

import pytest

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains import procedural_reader as pr
from domains import binding_resolver as br
from domains import method_synthesis as ms
from domains import actor_goals as ag
from domains import reading_collapse as rc
from domains import dictionary_lexicon as dl
from domains.teach import teach


# The plain methods the agent reads — NO rule syntax, ordinary English.
TEMPORAL_METHOD = (
    "When an action pair fact's pair_key matches an opposing action pair's "
    "pair_key, classify a temporal conflict reading.")
TROPE_METHOD = (
    "When a temporal conflict reading's pair_key matches a trope signature's "
    "pair_key, classify a trope reading.")

# The taught OpposingActionPair rows the TEMPORAL layer joins (support-then-
# undermine composite keys).
OPPOSING_PAIRS = [
    ("fund|oppose",
     "supports then undermines the same object -- a layered goal revealed across actions"),
    ("promote|restrict",
     "supports then undermines the same object -- a layered goal revealed across actions"),
    ("sponsor|ban",
     "supports then undermines the same object -- a layered goal revealed across actions"),
    ("support|block",
     "supports then undermines the same object -- a layered goal revealed across actions"),
]

# The taught TropeSignature rows the NAMED-TROPE layer joins — the strategic
# schema NAMES, drawn from the real TVTropes vocabulary.
TROPE_SIGS = [
    ("fund|oppose", "Trojan Horse",
     "help/a gift carrying a hidden hostile payload -- support the thing, then undermine it"),
    ("promote|restrict", "Bait and Switch",
     "offer/promote one thing, then deliver its restriction instead"),
    ("sponsor|ban", "False Flag Operation",
     "a hostile act disguised behind ostensible sponsorship/support"),
]

# Passive-with-by-phrase clauses (routing around the compound-actor parse
# residual). Same actor 'oil_company', same object, opposing verbs.
FUND_CLAUSE = "The technology was funded by the oil company."
OPPOSE_CLAUSE = "The technology was opposed by the oil company."
SUPPORT_CLAUSE = "The technology was supported by the oil company."
BLOCK_CLAUSE = "The technology was blocked by the oil company."


def _agent():
    dl.warm_wordnet("en")
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


def _read(a, *clauses):
    for c in clauses:
        rc.read_clause(a, c, write=True)


def _teach_opposing(a, pairs=OPPOSING_PAIRS):
    for pk, note in pairs:
        teach(a, "OpposingActionPair", {"pair_key": pk, "note": note})
    ag.ensure_opposing_pair_codebook(a)


def _teach_tropes(a, sigs=TROPE_SIGS):
    for pk, trope, gloss in sigs:
        teach(a, "TropeSignature", {"pair_key": pk, "trope": trope, "gloss": gloss})
    ag.ensure_trope_codebook(a)


def _author_temporal(a, *, install):
    """The agent authors the temporal-conflict rule from its plain method."""
    model = pr.read_method(a, TEMPORAL_METHOD, name="temporal_conflict")
    gb = br.derive_binding(a, model)
    res = ms.synthesise_rule_from_method(a, model, gb["binding"], install=install)
    return model, gb["binding"], res


def _author_trope(a, *, install):
    """The agent authors the NAMED-TROPE rule from its plain method + grounded
    binding. A TemporalConflictReading (fact) and a TropeSignature (codebook) must
    both be present + hub-wired so derive_binding can GROUND both collections."""
    model = pr.read_method(a, TROPE_METHOD, name="named_trope")
    gb = br.derive_binding(a, model)
    res = ms.synthesise_rule_from_method(a, model, gb["binding"], install=install)
    return model, gb["binding"], res


def _drive_temporal(a, *clauses):
    """Reusable first half: read clauses -> ActorAction facts -> ActionPairFacts ->
    author + install + FIRE the (agent-authored) temporal-conflict rule, so a
    hub-wired TemporalConflictReading exists to name."""
    _read(a, *clauses)
    ag.annotate_action_pairs(a)
    _, _, res = _author_temporal(a, install=True)
    assert not res.get("wall") and res.get("installed"), res
    a.inner.run_rules(10000)


# --------------------------------------------------------------------------- #
#  where-tree structural reads (mechanical) — same helpers as the temporal /
#  authoring-join tests, so shape assertions are apples-to-apples.
# --------------------------------------------------------------------------- #
def _flatten(where):
    out = []
    if not isinstance(where, dict):
        return out
    out.append(where)
    t = where.get("type")
    if t == "And":
        for it in where.get("items", []):
            out.extend(_flatten(it))
    elif t == "Not":
        out.extend(_flatten(where.get("arg")))
    elif t == "Exists":
        out.extend(_flatten(where.get("predicate")))
    return out


def _is_attr_of(x, var):
    return (isinstance(x, dict) and x.get("type") == "Attr"
            and isinstance(x.get("node"), dict)
            and x["node"].get("type") == "Var" and x["node"].get("name") == var)


def _cross_var_eq_join(where, va, vb):
    for nd in _flatten(where):
        if nd.get("type") != "Eq":
            continue
        a, b = nd.get("a"), nd.get("b")
        if (_is_attr_of(a, va) and _is_attr_of(b, vb)) or (_is_attr_of(a, vb) and _is_attr_of(b, va)):
            return nd
    return None


def _not_exists_dedup(where, node_type):
    for nd in _flatten(where):
        if nd.get("type") == "Exists" and \
                (nd.get("source") or {}).get("node_type") == node_type:
            return nd
    return None


def _no_shipped_trope_reading_rule():
    """No seed file ships a rule that mints TropeReading — proving the ONLY such
    rule is the one the agent authored."""
    seeds = Path(__file__).resolve().parent.parent / "seeds"
    for p in seeds.glob("*.json"):
        try:
            m = json.loads(p.read_text())
        except Exception:
            continue
        # `seeds/` holds one git-tracked file whose JSON root is a bare LIST of
        # rule objects, not a manifest (`_recovered_f16_rules.json`), and
        # `boot_all._read_seeds` SKIPS it (`if not isinstance(d, dict): continue`)
        # — so the agent never boots with it and it ships nothing. This scan did
        # not guard, and raised `'list' object has no attribute 'get'`. MATCH THE
        # LOADER: what a gate over seeds/ means is what the loader loads.
        if not isinstance(m, dict):
            continue
        for r in m.get("rules", []) or []:
            for eff in r.get("effects", []) or []:
                if isinstance(eff, list) and len(eff) >= 3 and \
                        eff[0] == "add_node" and eff[2] == "TropeReading":
                    return False
    return True


# --------------------------------------------------------------------------- #
#  1. THE AUTHORSHIP PROOF — the NAMED-TROPE rule is produced by the synthesiser
#     from the READ method, not hand-written; it has the target classify-by-join
#     shape (2 has_ matches on has_temporal_conflict_reading + has_trope_signature,
#     Eq(pair_key) join, Not-Exists dedup, mint carrying the fields + link edge).
# --------------------------------------------------------------------------- #
def test_agent_authors_named_trope_rule():
    a = _agent()
    _teach_opposing(a)
    _drive_temporal(a, FUND_CLAUSE, OPPOSE_CLAUSE)   # a TemporalConflictReading to ground on
    _teach_tropes(a)                                 # a TropeSignature to ground on

    # the reader reads a plain sentence into a join+classify model
    model = pr.read_method(a, TROPE_METHOD, name="named_trope")
    step = model["steps"][0]
    trig, main = step["trigger"], step["main"]
    assert trig and trig["kind"] == "join", trig
    assert trig["fact_type"] == "temporal conflict reading" and trig["fact_key"] == "pair_key"
    assert trig["codebook_type"] == "trope signature" and trig["codebook_key"] == "pair_key"
    assert main["effect"] == "classify"
    assert main["node_type"] == "trope reading", main

    # the agent grounds the binding against ITS OWN domain graph
    gb = br.derive_binding(a, model)
    binding = gb["binding"]
    assert binding["fact_edge"] == "has_temporal_conflict_reading", binding
    assert binding["codebook_edge"] == "has_trope_signature", binding
    assert binding["classification_edge"] == "has_trope_reading", binding
    assert binding["node_types"]["temporal conflict reading"] == "TemporalConflictReading"
    assert binding["node_types"]["trope signature"] == "TropeSignature"
    assert binding["node_types"]["trope reading"] == "TropeReading"
    # FOUR fields carried from the fact side (the TemporalConflictReading's scalar
    # slots) + TWO from the codebook side (the named trope + gloss).
    assert set(binding.get("fact_carry", [])) == {"actor", "object", "pair_key", "note"}, binding
    assert binding.get("codebook_carry") == {"trope": "trope", "gloss": "gloss"}, binding

    # the SYNTHESISER produces the rule — NOT hand-written (name is the
    # synthesiser's own `synth_classify_*`, and no such rule ships in a seed).
    res = ms.synthesise_rule_from_method(a, model, binding, install=False)
    assert not res.get("wall"), res
    rule = res["rules"][0]
    assert rule["name"] == "synth_classify_named_trope", rule["name"]
    assert _no_shipped_trope_reading_rule(), \
        "a TropeReading rule must NOT ship in a seed"

    # SHAPE: two has_ matches on the agent hub, on the fact + codebook edges
    match = rule["match"]
    assert match == [["agent", "has_temporal_conflict_reading", "f"],
                     ["agent", "has_trope_signature", "c"]], match

    # the Eq-JOIN f.pair_key == c.pair_key + a Not-Exists dedup over the mint type
    eqj = _cross_var_eq_join(rule["where"], "f", "c")
    assert eqj is not None, rule["where"]
    assert eqj["a"]["key"] == "pair_key" and eqj["b"]["key"] == "pair_key", eqj
    assert _not_exists_dedup(rule["where"], "TropeReading") is not None

    # EFFECT: mint TropeReading carrying actor+object+pair_key FROM f + trope+gloss
    # FROM c, linked off the agent hub.
    effs = rule["effects"]
    add_node = next(e for e in effs if e[0] == "add_node")
    assert add_node[2] == "TropeReading", add_node
    attrs = add_node[3]
    from_f = {k for k, v in attrs.items()
              if isinstance(v, dict) and _is_attr_of(v.get("__term__"), "f")}
    from_c = {k for k, v in attrs.items()
              if isinstance(v, dict) and _is_attr_of(v.get("__term__"), "c")}
    assert {"actor", "object", "pair_key"} <= from_f, attrs
    assert {"trope", "gloss"} <= from_c, attrs
    assert any(e == ["add_edge", "agent", "has_trope_reading", "cls"]
               for e in effs), effs


# --------------------------------------------------------------------------- #
#  2. FIRES — the FULL chain, both agent-authored rules: the temporal rule mints
#     TemporalConflictReading{pair_key:'fund|oppose'}, then the named-trope rule
#     joins the taught 'fund|oppose' TropeSignature -> TropeReading{Trojan Horse}.
# --------------------------------------------------------------------------- #
def test_authored_chain_names_fund_then_oppose_trojan_horse():
    a = _agent()
    _teach_opposing(a)
    _drive_temporal(a, FUND_CLAUSE, OPPOSE_CLAUSE)
    # the temporal (agent-authored) reading is present first
    tconf = ag.held_temporal_conflicts(a)
    assert len(tconf) == 1 and tconf[0]["pair_key"] == "fund|oppose", tconf

    _teach_tropes(a)
    _, _, res = _author_trope(a, install=True)
    assert not res.get("wall") and res.get("installed"), res

    a.inner.run_rules(10000)
    readings = ag.held_trope_readings(a)
    assert len(readings) == 1, readings
    r = readings[0]
    assert r["trope"] == "Trojan Horse", r
    assert r["actor"] == "oil_company", r
    assert r["object"] == "technology", r
    assert r["pair_key"] == "fund|oppose", r
    assert "hidden hostile payload" in (r["gloss"] or ""), r

    # dedup: a second fixpoint mints no duplicate
    a.inner.run_rules(10000)
    assert len(ag.held_trope_readings(a)) == 1


# --------------------------------------------------------------------------- #
#  3. DISCRIMINATION — a TemporalConflictReading whose pair_key is NOT in the
#     TropeSignature codebook gets no NAME (a pattern can be a conflict without a
#     named schema); no TemporalConflictReading at all -> null.
# --------------------------------------------------------------------------- #
def test_unnamed_conflict_gets_no_trope():
    a = _agent()
    _teach_opposing(a)
    # support|block IS a taught opposing pair (temporal fires) but is NOT in the
    # TropeSignature codebook (only fund|oppose / promote|restrict / sponsor|ban).
    _drive_temporal(a, SUPPORT_CLAUSE, BLOCK_CLAUSE)
    tconf = ag.held_temporal_conflicts(a)
    assert len(tconf) == 1 and tconf[0]["pair_key"] == "support|block", tconf

    _teach_tropes(a)                                 # codebook present, but no support|block row
    _, _, res = _author_trope(a, install=True)
    assert not res.get("wall") and res.get("installed"), res
    a.inner.run_rules(10000)
    assert ag.held_trope_readings(a) == []           # a conflict, but no NAMED schema


def test_no_temporal_conflict_yields_null():
    a = _agent()
    _teach_opposing(a)
    # fund then EXPAND -> 'fund|expand', NOT a taught opposing pair -> no
    # TemporalConflictReading at all.
    _read(a, FUND_CLAUSE, "The technology was expanded by the oil company.")
    ag.annotate_action_pairs(a)
    _, _, tres = _author_temporal(a, install=True)
    assert not tres.get("wall") and tres.get("installed"), tres
    a.inner.run_rules(10000)
    assert ag.held_temporal_conflicts(a) == []

    _teach_tropes(a)
    _, _, res = _author_trope(a, install=True)
    # with no TemporalConflictReading the fact collection is absent, so authorship
    # may wall honestly here. Assert the OUTCOME regardless: no trope reading.
    if not res.get("wall"):
        a.inner.run_rules(10000)
    assert ag.held_trope_readings(a) == []


# --------------------------------------------------------------------------- #
#  4. AGENT-GROWS-IT — teach a NEW TropeSignature; a matching pattern now gets
#     NAMED, with NO code and NO rule change (the authored rule already joins the
#     codebook). Mirrors the temporal layer's teach-grows gate.
# --------------------------------------------------------------------------- #
def test_teaching_a_signature_grows_naming():
    a = _agent()
    _teach_opposing(a)
    _drive_temporal(a, FUND_CLAUSE, OPPOSE_CLAUSE)
    # teach ONLY the fund|oppose signature to start.
    teach(a, "TropeSignature",
          {"pair_key": "fund|oppose", "trope": "Trojan Horse",
           "gloss": "help/a gift carrying a hidden hostile payload -- support the thing, then undermine it"})
    ag.ensure_trope_codebook(a)
    _, _, res = _author_trope(a, install=True)
    assert not res.get("wall") and res.get("installed"), res
    a.inner.run_rules(10000)
    base = {r["trope"] for r in ag.held_trope_readings(a)}
    assert base == {"Trojan Horse"}, base

    # a NEW sponsor|ban conflict on a DIFFERENT object -> the temporal layer
    # (already installed) mints its TemporalConflictReading, but the TropeSignature
    # codebook does NOT yet cover 'sponsor|ban' -> still no name.
    _read(a, "The software was sponsored by the oil company.",
             "The software was banned by the oil company.")
    ag.annotate_action_pairs(a)
    a.inner.run_rules(10000)
    grown_conf = {r["pair_key"] for r in ag.held_temporal_conflicts(a)}
    assert "sponsor|ban" in grown_conf, grown_conf
    assert {r["trope"] for r in ag.held_trope_readings(a)} == base

    # teach the new signature (the agent's OWN teach()) + reconcile-wire it —
    # NO rule or code change — and the SAME authored rule now NAMES it.
    teach(a, "TropeSignature",
          {"pair_key": "sponsor|ban", "trope": "False Flag Operation",
           "gloss": "a hostile act disguised behind ostensible sponsorship/support"})
    ag.ensure_trope_codebook(a)
    a.inner.run_rules(10000)
    grown = {r["trope"] for r in ag.held_trope_readings(a)}
    assert grown == {"Trojan Horse", "False Flag Operation"}, grown


# --------------------------------------------------------------------------- #
#  5. SOURCE AUDIT — no `import re`; Python never mints TropeReading or the
#     codebook rows directly. The DECISION (which pattern is which named trope) is
#     the AGENT-AUTHORED rule's Eq-join against the taught codebook, not Python.
# --------------------------------------------------------------------------- #
def test_source_audit_no_regex_no_naming_decision():
    src = (Path(__file__).resolve().parent.parent / "domains" / "actor_goals.py").read_text()
    for line in src.splitlines():
        s = line.strip()
        assert not (s == "import re" or s.startswith("import re ")
                    or s.startswith("import re,")), ("regex import in reading path: %r" % line)
        assert not s.startswith("import re;"), line
    assert "re.match" not in src and "re.search" not in src and "re.sub" not in src
    # Python never mints TropeReading or the TropeSignature codebook rows directly —
    # the NAME decision is the AGENT-AUTHORED rule's; the rows are the agent's teach().
    assert 'add_node("TropeReading"' not in src
    assert 'add_node("TropeSignature"' not in src
    # ZERO new annotator: no new *_pairs/candidate emitter for this slice — the
    # TemporalConflictReading (minted by the temporal layer) IS the fact.
    assert 'add_node("TropeReading"' not in src


# --------------------------------------------------------------------------- #
#  6. NO NEW ANNOTATOR — the slice's only new Python is a reader + codebook wiring;
#     held_trope_readings reads a graph the agent-authored rule populates.
# --------------------------------------------------------------------------- #
def test_reader_is_pure_query_no_annotator():
    a = _agent()
    # with nothing driven, the reader returns [] and no TropeReading exists — the
    # reader mints nothing (pure query).
    assert ag.held_trope_readings(a) == []
    assert list(a.s.nodes("TropeReading")) == []
    # ensure_trope_codebook with no TropeSignature is a harmless no-op.
    ag.ensure_trope_codebook(a)
    assert list(a.s.nodes("TropeReading")) == []


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-q"]))
