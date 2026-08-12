"""MULTIPLE / CONFLICTING GOALS — the agent AUTHORS its own reading rule.

A DISCLAIMER/hedge ("I'm not racist, but ...", "no offense, but ...", "with
all due respect, ...") signals TWO goals in tension: goal-A (express the
content) AND goal-B (avoid its social cost). This slice detects it as a
classify-by-codebook-JOIN.

THE HEADLINE PROVEN HERE: the agent AUTHORS the analysis rule ITSELF from a
plain English method + a TAUGHT codebook, through its OWN faculty
(procedural_reader.read_method -> binding_resolver.derive_binding ->
method_synthesis.synthesise_rule_from_method -> install). The ONLY Python
written for this slice is a MECHANICAL n-gram annotator (domains/actor_goals.py,
world-adapter I/O, emits EVERY contiguous word n-gram UNCONDITIONALLY — no
decision), the codebook wiring, and a reader. NO hand-written rule.

The recipe is the one proven in tests/test_authoring_join_rule_migrated.py
(test_agent_authors_compound_typed_join_rule_and_fires) reproduced for a real
goal layer with COMPOUND collection types (disclaimer candidate / disclaimer
cue / conflicting goals reading).

donkey=0: OZMA_NO_LLM=1, no model anywhere, no `import re` in the reading path.
"""
import json
import os
from pathlib import Path

os.environ.setdefault("OZMA_NO_LLM", "1")
# Never touch the real boot seeds — teach()'s live-graph add + category
# decision are unaffected; only the disk write to the REAL seed dir is skipped
# (an explicit tmp seeds_dir is still honoured — see the persistence test).
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

import pytest

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains import procedural_reader as pr
from domains import binding_resolver as br
from domains import method_synthesis as ms
from domains import actor_goals as ag
from domains.teach import teach


# The plain method the agent reads — NO rule syntax, ordinary English.
METHOD = ("When a disclaimer candidate's phrase matches a disclaimer cue's "
          "phrase, classify a conflicting goals reading.")

# The taught codebook rows (the agent's OWN teach()).
CUES = [
    ("not racist but", "express-vs-avoid-social-cost"),
    ("no offense but", "express-vs-avoid-social-cost"),
    ("with all due respect", "express-vs-avoid-social-cost"),
    ("some of my best friends", "express-vs-avoid-social-cost"),
]

DISCLAIMER_UTTERANCE = "I am not racist, but I do not want them here."


def _agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


def _teach_cues(a, cues=CUES):
    for phrase, tension in cues:
        teach(a, "DisclaimerCue", {"phrase": phrase, "tension": tension})
    ag.ensure_disclaimer_codebook(a)


def _author_rule(a, *, install):
    """The agent authors the rule from the plain method + grounded binding.
    Returns (model, binding, res). The codebook + at least one candidate must
    be present so derive_binding can GROUND the fact/codebook collections."""
    model = pr.read_method(a, METHOD, name="conflicting_goals")
    gb = br.derive_binding(a, model)
    res = ms.synthesise_rule_from_method(a, model, gb["binding"], install=install)
    return model, gb["binding"], res


# --------------------------------------------------------------------------- #
#  where-tree structural reads (mechanical) — same helpers as the authoring
#  join test, so the shape assertions are apples-to-apples.
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


# --------------------------------------------------------------------------- #
#  1. THE AUTHORSHIP PROOF — the rule is produced by the synthesiser from the
#     READ method, not hand-written; it has the target classify-by-join shape.
# --------------------------------------------------------------------------- #
def test_agent_authors_conflicting_goals_rule():
    a = _agent()
    _teach_cues(a)
    ag.annotate_disclaimer_candidates(a, DISCLAIMER_UTTERANCE)   # candidates to ground on

    # the reader reads a plain sentence into a join+classify model
    model = pr.read_method(a, METHOD, name="conflicting_goals")
    step = model["steps"][0]
    trig, main = step["trigger"], step["main"]
    assert trig and trig["kind"] == "join", trig
    assert trig["fact_type"] == "disclaimer candidate" and trig["fact_key"] == "phrase"
    assert trig["codebook_type"] == "disclaimer cue" and trig["codebook_key"] == "phrase"
    assert main["effect"] == "classify"
    assert main["node_type"] == "conflicting goals reading", main

    # the agent grounds the binding against ITS OWN domain graph
    gb = br.derive_binding(a, model)
    binding = gb["binding"]
    assert binding["fact_edge"] == "has_disclaimer_candidate", binding
    assert binding["codebook_edge"] == "has_disclaimer_cue", binding
    assert binding["classification_edge"] == "has_conflicting_goals_reading", binding
    assert binding["node_types"]["conflicting goals reading"] == "ConflictingGoalsReading"
    assert binding.get("codebook_carry"), binding      # a field carried from BOTH sides

    # the SYNTHESISER produces the rule — NOT hand-written (name is the
    # synthesiser's own `synth_classify_*`, and no such rule ships in a seed).
    res = ms.synthesise_rule_from_method(a, model, binding, install=False)
    assert not res.get("wall"), res
    rule = res["rules"][0]
    assert rule["name"] == "synth_classify_conflicting_goals", rule["name"]
    assert _no_shipped_conflicting_goals_rule(), "a ConflictingGoalsReading rule must NOT ship in a seed"

    # SHAPE: two has_ matches on the agent hub, on the fact + codebook edges
    match = rule["match"]
    assert match == [["agent", "has_disclaimer_candidate", "f"],
                     ["agent", "has_disclaimer_cue", "c"]], match

    # the Eq-JOIN f.phrase == c.phrase + a Not-Exists dedup over the mint type
    assert _cross_var_eq_join(rule["where"], "f", "c") is not None, rule["where"]
    assert _not_exists_dedup(rule["where"], "ConflictingGoalsReading") is not None

    # EFFECT: mint ConflictingGoalsReading carrying phrase FROM f + tension FROM c
    effs = rule["effects"]
    add_node = next(e for e in effs if e[0] == "add_node")
    assert add_node[2] == "ConflictingGoalsReading", add_node
    attrs = add_node[3]
    from_f = [k for k, v in attrs.items()
              if isinstance(v, dict) and _is_attr_of(v.get("__term__"), "f")]
    from_c = [k for k, v in attrs.items()
              if isinstance(v, dict) and _is_attr_of(v.get("__term__"), "c")]
    assert "phrase" in from_f, attrs
    assert "tension" in from_c, attrs
    assert any(e == ["add_edge", "agent", "has_conflicting_goals_reading", "cls"]
               for e in effs), effs


def _no_shipped_conflicting_goals_rule():
    """No seed file ships a rule that mints ConflictingGoalsReading — proving
    the ONLY such rule is the one the agent authored."""
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
                        eff[0] == "add_node" and eff[2] == "ConflictingGoalsReading":
                    return False
    return True


# --------------------------------------------------------------------------- #
#  2. FIRES — the agent-authored rule joins the taught cue and mints a reading.
# --------------------------------------------------------------------------- #
def test_authored_rule_fires_on_disclaimer():
    a = _agent()
    _teach_cues(a)
    ag.annotate_disclaimer_candidates(a, DISCLAIMER_UTTERANCE)
    _, _, res = _author_rule(a, install=True)
    assert not res.get("wall") and res.get("installed"), res

    a.inner.run_rules(10000)
    readings = ag.held_conflicting_goals(a)
    assert len(readings) == 1, readings
    assert readings[0]["phrase"] == "not racist but"
    assert readings[0]["tension"] == "express-vs-avoid-social-cost"

    # dedup: a second fixpoint mints no duplicate
    a.inner.run_rules(10000)
    assert len(ag.held_conflicting_goals(a)) == 1


# --------------------------------------------------------------------------- #
#  3. DISCRIMINATION (the value) — no disclaimer, and a near-miss, both null.
# --------------------------------------------------------------------------- #
def test_plain_utterance_flags_nothing():
    a = _agent()
    _teach_cues(a)
    ag.annotate_disclaimer_candidates(a, "The weather is nice today.")   # candidates to ground on
    _, _, res = _author_rule(a, install=True)
    assert not res.get("wall") and res.get("installed"), res
    a.inner.run_rules(10000)
    assert ag.held_conflicting_goals(a) == []           # no n-gram matches a taught cue


def test_near_miss_flags_nothing():
    a = _agent()
    _teach_cues(a)
    # 'not hungry but' IS emitted as an n-gram but matches NO taught cue —
    # the codebook is specific; honest null.
    ag.annotate_disclaimer_candidates(a, "I am not hungry, but I will eat.")
    _, _, res = _author_rule(a, install=True)
    assert not res.get("wall") and res.get("installed"), res
    a.inner.run_rules(10000)
    assert ag.held_conflicting_goals(a) == []


# --------------------------------------------------------------------------- #
#  4. AGENT-GROWS-IT — teach a NEW cue row; a new utterance now flags, with
#     NO code and NO rule change (the authored rule already joins the codebook).
# --------------------------------------------------------------------------- #
def test_teaching_a_cue_grows_coverage():
    a = _agent()
    _teach_cues(a)
    ag.annotate_disclaimer_candidates(a, DISCLAIMER_UTTERANCE)
    _, _, res = _author_rule(a, install=True)
    assert not res.get("wall") and res.get("installed"), res
    a.inner.run_rules(10000)
    base = {r["phrase"] for r in ag.held_conflicting_goals(a)}
    assert base == {"not racist but"}

    # a NEW disclaimer utterance the current codebook does NOT cover -> null
    grow_utt = "I have nothing against them but they should leave."
    ag.annotate_disclaimer_candidates(a, grow_utt)
    a.inner.run_rules(10000)
    assert {r["phrase"] for r in ag.held_conflicting_goals(a)} == {"not racist but"}

    # teach the new cue (the agent's OWN teach()) + reconcile-wire it — NO rule
    # or code change — and the SAME authored rule now flags it.
    teach(a, "DisclaimerCue",
          {"phrase": "i have nothing against them but",
           "tension": "express-vs-avoid-social-cost"})
    ag.ensure_disclaimer_codebook(a)
    a.inner.run_rules(10000)
    grown = {r["phrase"] for r in ag.held_conflicting_goals(a)}
    assert grown == {"not racist but", "i have nothing against them but"}, grown


# --------------------------------------------------------------------------- #
#  5. SOURCE AUDIT — no `import re`; the annotator makes NO decision (emits
#     EVERY n-gram, codebook-independent); the DECISION is the AUTHORED rule.
# --------------------------------------------------------------------------- #
def test_source_audit_no_regex_no_annotator_decision():
    src = (Path(__file__).resolve().parent.parent / "domains" / "actor_goals.py").read_text()
    # line-precise: no bare `import re` / `import re, ...` statement (substring
    # matches inside `import reading_collapse` must NOT trip this).
    for line in src.splitlines():
        s = line.strip()
        assert not (s == "import re" or s.startswith("import re ")
                    or s.startswith("import re,")), ("regex import in reading path: %r" % line)
        assert not s.startswith("import re;"), line

    # the annotator emits candidates UNCONDITIONALLY — identical output whether
    # or not any cue is taught (no codebook-conditional decision).
    a1 = _agent()
    n1 = len(ag.annotate_disclaimer_candidates(a1, DISCLAIMER_UTTERANCE))
    a2 = _agent()
    _teach_cues(a2)                                   # a full codebook present
    n2 = len(ag.annotate_disclaimer_candidates(a2, DISCLAIMER_UTTERANCE))
    assert n1 == n2 and n1 > 0, (n1, n2)              # the codebook never gates emission

    # and it emits the exact contiguous-n-gram set (mechanical str work only)
    phrases = {a1.s.node(nd)["attrs"]["phrase"] for nd in a1.s.nodes("DisclaimerCandidate")}
    assert "not racist but" in phrases                # the real disclaimer 3-gram
    assert "i am" in phrases and "am not racist" in phrases   # ordinary n-grams too


# --------------------------------------------------------------------------- #
#  6. PERSISTENCE — teach() writes the cue to its own seed (agent's own file),
#     to an explicit tmp dir (the real boot seeds are never touched).
# --------------------------------------------------------------------------- #
def test_taught_cue_persists_to_a_seed(tmp_path):
    a = _agent()
    r = teach(a, "DisclaimerCue",
              {"phrase": "no offense but", "tension": "express-vs-avoid-social-cost"},
              seeds_dir=tmp_path)
    assert r["saved"] and r["persisted"], r
    seed = json.loads(Path(r["seed"]).read_text())
    rows = [n for n in seed["nodes"]
            if n["type"] == "DisclaimerCue" and n["attrs"]["phrase"] == "no offense but"]
    assert len(rows) == 1, seed["nodes"]
    # idempotent: re-teaching the same row is a no-op
    r2 = teach(a, "DisclaimerCue",
               {"phrase": "no offense but", "tension": "express-vs-avoid-social-cost"},
               seeds_dir=tmp_path)
    assert not r2["saved"], r2


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-q"]))
