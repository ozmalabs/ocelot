"""SAME-SURFACE INVERSION (endorse vs call-out) — the agent AUTHORS its own
reading rule, and the ONLY Python written is a GENERIC n-gram annotator.

Identical surface content can carry the OPPOSITE goal. Saying / quoting a slur
to CONDEMN or REPORT it is the inverse of endorsing it. The graph-native tell is
a DISTANCING cue (quotation, attribution, condemnation — "so-called", "in his
words", "the disgusting notion that", "supposedly", "he repeated the ..."): it
signals the speaker does NOT hold the surface content as their OWN stance, so the
goal is INVERTED (call-out / report), not endorsement.

THE HEADLINE PROVEN HERE: the agent AUTHORS the analysis rule ITSELF from a plain
English method + a TAUGHT codebook, through its OWN faculty
(procedural_reader.read_method -> binding_resolver.derive_binding ->
method_synthesis.synthesise_rule_from_method -> install). The ONLY Python written
for this slice is a GENERIC mechanical n-gram annotator
(domains/actor_goals.annotate_utterance_phrases, world-adapter I/O, emits EVERY
contiguous 2..6-word n-gram UNCONDITIONALLY — no decision, no `import re`), which
EVERY future phrase-cue layer reuses, plus codebook wiring and a reader. NO
hand-written rule.

This is the SAME recipe proven in tests/test_conflicting_goals_migrated.py, but
on a GENERIC annotator (UtterancePhrase, not the layer-specific DisclaimerCandidate)
so a subsequent phrase-cue layer needs ZERO new Python — teach + author only.

donkey=0: OZMA_NO_LLM=1, no model anywhere, no `import re` in the reading path.
"""
import json
import os
from pathlib import Path

os.environ.setdefault("OZMA_NO_LLM", "1")
# Never touch the real boot seeds — teach()'s live-graph add + category decision
# are unaffected; only the disk write to the REAL seed dir is skipped (an explicit
# tmp seeds_dir is still honoured — see the persistence test).
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
METHOD = ("When an utterance phrase's phrase matches a distancing cue's "
          "phrase, classify a surface inversion reading.")

# The taught codebook rows (the agent's OWN teach()) — distancing cues that mark
# the surface content as NOT the speaker's own stance.
CUES = [
    ("so-called", "surface-distanced-not-own-stance"),
    ("in his words", "surface-distanced-not-own-stance"),
    ("the disgusting notion that", "surface-distanced-not-own-stance"),
    ("supposedly", "surface-distanced-not-own-stance"),
    ("he repeated the", "surface-distanced-not-own-stance"),
]

# A distanced utterance: the speaker voices the surface content at a DISTANCE
# (attribution "he repeated the" + condemnation "the disgusting notion that").
INVERSION_UTTERANCE = "He repeated the disgusting notion that they are inferior."


def _agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


def _teach_cues(a, cues=CUES):
    for phrase, reading in cues:
        teach(a, "DistancingCue", {"phrase": phrase, "reading": reading})
    ag.ensure_distancing_codebook(a)


def _author_rule(a, *, install):
    """The agent authors the rule from the plain method + grounded binding.
    Returns (model, binding, res). The codebook + at least one utterance phrase
    must be present so derive_binding can GROUND the fact/codebook collections."""
    model = pr.read_method(a, METHOD, name="surface_inversion")
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
def test_agent_authors_surface_inversion_rule():
    a = _agent()
    _teach_cues(a)
    ag.annotate_utterance_phrases(a, INVERSION_UTTERANCE)   # phrases to ground on

    # the reader reads a plain sentence into a join+classify model
    model = pr.read_method(a, METHOD, name="surface_inversion")
    step = model["steps"][0]
    trig, main = step["trigger"], step["main"]
    assert trig and trig["kind"] == "join", trig
    assert trig["fact_type"] == "utterance phrase" and trig["fact_key"] == "phrase"
    assert trig["codebook_type"] == "distancing cue" and trig["codebook_key"] == "phrase"
    assert main["effect"] == "classify"
    assert main["node_type"] == "surface inversion reading", main

    # the agent grounds the binding against ITS OWN domain graph
    gb = br.derive_binding(a, model)
    binding = gb["binding"]
    assert binding["fact_edge"] == "has_utterance_phrase", binding
    assert binding["codebook_edge"] == "has_distancing_cue", binding
    assert binding["classification_edge"] == "has_surface_inversion_reading", binding
    assert binding["node_types"]["surface inversion reading"] == "SurfaceInversionReading"
    assert binding.get("codebook_carry"), binding      # a field carried from the codebook

    # the SYNTHESISER produces the rule — NOT hand-written (name is the
    # synthesiser's own `synth_classify_*`, and no such rule ships in a seed).
    res = ms.synthesise_rule_from_method(a, model, binding, install=False)
    assert not res.get("wall"), res
    rule = res["rules"][0]
    assert rule["name"] == "synth_classify_surface_inversion", rule["name"]
    assert _no_shipped_surface_inversion_rule(), \
        "a SurfaceInversionReading rule must NOT ship in a seed"

    # SHAPE: two has_ matches on the agent hub, on the fact + codebook edges
    match = rule["match"]
    assert match == [["agent", "has_utterance_phrase", "f"],
                     ["agent", "has_distancing_cue", "c"]], match

    # the Eq-JOIN f.phrase == c.phrase + a Not-Exists dedup over the mint type
    assert _cross_var_eq_join(rule["where"], "f", "c") is not None, rule["where"]
    assert _not_exists_dedup(rule["where"], "SurfaceInversionReading") is not None

    # EFFECT: mint SurfaceInversionReading carrying phrase FROM f + reading FROM c
    effs = rule["effects"]
    add_node = next(e for e in effs if e[0] == "add_node")
    assert add_node[2] == "SurfaceInversionReading", add_node
    attrs = add_node[3]
    from_f = [k for k, v in attrs.items()
              if isinstance(v, dict) and _is_attr_of(v.get("__term__"), "f")]
    from_c = [k for k, v in attrs.items()
              if isinstance(v, dict) and _is_attr_of(v.get("__term__"), "c")]
    assert "phrase" in from_f, attrs
    assert "reading" in from_c, attrs
    assert any(e == ["add_edge", "agent", "has_surface_inversion_reading", "cls"]
               for e in effs), effs


def _no_shipped_surface_inversion_rule():
    """No seed file ships a rule that mints SurfaceInversionReading — proving the
    ONLY such rule is the one the agent authored."""
    seeds = Path(__file__).resolve().parent.parent / "seeds"
    for p in seeds.glob("*.json"):
        try:
            m = json.loads(p.read_text())
        except Exception:
            continue
        for r in m.get("rules", []) or []:
            for eff in r.get("effects", []) or []:
                if isinstance(eff, list) and len(eff) >= 3 and \
                        eff[0] == "add_node" and eff[2] == "SurfaceInversionReading":
                    return False
    return True


# --------------------------------------------------------------------------- #
#  2. FIRES — the agent-authored rule joins the taught cue and mints a reading.
# --------------------------------------------------------------------------- #
def test_authored_rule_fires_on_distanced_utterance():
    a = _agent()
    _teach_cues(a)
    ag.annotate_utterance_phrases(a, INVERSION_UTTERANCE)
    _, _, res = _author_rule(a, install=True)
    assert not res.get("wall") and res.get("installed"), res

    a.inner.run_rules(10000)
    readings = ag.held_surface_inversions(a)
    phrases = {r["phrase"] for r in readings}
    # both distancing cues present in the utterance fire (attribution + condemnation)
    assert phrases == {"he repeated the", "the disgusting notion that"}, readings
    assert all(r["reading"] == "surface-distanced-not-own-stance" for r in readings)

    # dedup: a second fixpoint mints no duplicate
    a.inner.run_rules(10000)
    assert {r["phrase"] for r in ag.held_surface_inversions(a)} == phrases


# --------------------------------------------------------------------------- #
#  3. DISCRIMINATION (the value) — the SAME-TYPE content WITHOUT a distancing
#     cue is NOT flagged; a plain sentence is null.
# --------------------------------------------------------------------------- #
def test_bare_assertion_of_same_content_flags_nothing():
    a = _agent()
    _teach_cues(a)
    # a BARE assertion of the SAME surface content — no distancing cue, so the
    # speaker DOES hold it as their own stance: NOT a surface inversion.
    ag.annotate_utterance_phrases(a, "They are inferior.")
    _, _, res = _author_rule(a, install=True)
    assert not res.get("wall") and res.get("installed"), res
    a.inner.run_rules(10000)
    assert ag.held_surface_inversions(a) == []   # no n-gram matches a taught cue


def test_plain_sentence_flags_nothing():
    a = _agent()
    _teach_cues(a)
    ag.annotate_utterance_phrases(a, "The sky is blue.")
    _, _, res = _author_rule(a, install=True)
    assert not res.get("wall") and res.get("installed"), res
    a.inner.run_rules(10000)
    assert ag.held_surface_inversions(a) == []


# --------------------------------------------------------------------------- #
#  4. AGENT-GROWS-IT — teach a NEW distancing cue; a new utterance now flags,
#     with NO code and NO rule change (the authored rule already joins the codebook).
# --------------------------------------------------------------------------- #
def test_teaching_a_cue_grows_coverage():
    a = _agent()
    _teach_cues(a)
    ag.annotate_utterance_phrases(a, INVERSION_UTTERANCE)
    _, _, res = _author_rule(a, install=True)
    assert not res.get("wall") and res.get("installed"), res
    a.inner.run_rules(10000)
    base = {r["phrase"] for r in ag.held_surface_inversions(a)}
    assert base == {"he repeated the", "the disgusting notion that"}

    # a NEW distanced utterance the current codebook does NOT cover -> null delta
    grow_utt = "The report cited the false claim that the earth is flat."
    ag.annotate_utterance_phrases(a, grow_utt)
    a.inner.run_rules(10000)
    assert {r["phrase"] for r in ag.held_surface_inversions(a)} == base

    # teach the new cue (the agent's OWN teach()) + reconcile-wire it — NO rule
    # or code change — and the SAME authored rule now flags it.
    teach(a, "DistancingCue",
          {"phrase": "the false claim that",
           "reading": "surface-distanced-not-own-stance"})
    ag.ensure_distancing_codebook(a)
    a.inner.run_rules(10000)
    grown = {r["phrase"] for r in ag.held_surface_inversions(a)}
    assert grown == base | {"the false claim that"}, grown


# --------------------------------------------------------------------------- #
#  5. SOURCE AUDIT — no `import re`; the GENERIC annotator makes NO decision
#     (emits EVERY n-gram, codebook-independent); the DECISION is the AUTHORED rule.
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

    # the GENERIC annotator emits phrases UNCONDITIONALLY — identical output
    # whether or not any cue is taught (no codebook-conditional decision).
    a1 = _agent()
    n1 = len(ag.annotate_utterance_phrases(a1, INVERSION_UTTERANCE))
    a2 = _agent()
    _teach_cues(a2)                                   # a full codebook present
    n2 = len(ag.annotate_utterance_phrases(a2, INVERSION_UTTERANCE))
    assert n1 == n2 and n1 > 0, (n1, n2)              # the codebook never gates emission

    # and it emits the exact contiguous-n-gram set (mechanical str work only)
    phrases = {a1.s.node(nd)["attrs"]["phrase"] for nd in a1.s.nodes("UtterancePhrase")}
    assert "he repeated the" in phrases                       # a real distancing cue
    assert "the disgusting notion that" in phrases            # the 4-gram cue
    assert "he repeated" in phrases and "they are inferior" in phrases  # ordinary n-grams too


# --------------------------------------------------------------------------- #
#  6. GENERIC REUSE — the annotator is layer-agnostic: it emits the SAME
#     UtterancePhrase facts with ZERO reference to the distancing codebook, so a
#     future phrase-cue layer reuses it with no new Python.
# --------------------------------------------------------------------------- #
def test_annotator_is_generic_no_codebook_coupling():
    a = _agent()   # NO codebook taught at all
    created = ag.annotate_utterance_phrases(a, "so-called experts said so.")
    assert created, created
    phrases = {a.s.node(nd)["attrs"]["phrase"] for nd in a.s.nodes("UtterancePhrase")}
    assert "so-called experts" in phrases            # emitted with no DistancingCue present
    # no reading is minted without an authored rule + codebook — the annotator
    # ONLY writes facts, it makes no classification decision.
    assert ag.held_surface_inversions(a) == []


# --------------------------------------------------------------------------- #
#  7. PERSISTENCE — teach() writes the cue to its own seed (agent's own file),
#     to an explicit tmp dir (the real boot seeds are never touched).
# --------------------------------------------------------------------------- #
def test_taught_cue_persists_to_a_seed(tmp_path):
    a = _agent()
    r = teach(a, "DistancingCue",
              {"phrase": "in his words", "reading": "surface-distanced-not-own-stance"},
              seeds_dir=tmp_path)
    assert r["saved"] and r["persisted"], r
    seed = json.loads(Path(r["seed"]).read_text())
    rows = [n for n in seed["nodes"]
            if n["type"] == "DistancingCue" and n["attrs"]["phrase"] == "in his words"]
    assert len(rows) == 1, seed["nodes"]
    # idempotent: re-teaching the same row is a no-op
    r2 = teach(a, "DistancingCue",
               {"phrase": "in his words", "reading": "surface-distanced-not-own-stance"},
               seeds_dir=tmp_path)
    assert not r2["saved"], r2


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-q"]))
