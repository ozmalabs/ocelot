"""test_prog_chunks_migrated — P7-C gates: the IDIOM-GRAIN chunk codebook
(PROGRAM_SYNTHESIS_P7C.md; registered rules in its §1, written before the
mine ran).

Gates:
  1. seed loads clean (zero skipped rules/reflexes);
  2. mining artifact: recorded twin-run determinism + every aggregate
     re-derived from the per-chunk rows (a baseline is a list, never a
     count);
  3. support-threshold honesty: s* re-derived from the artifact's OWN
     support curve by the registered §1.3 rule — the curve covers the whole
     type population (no silent caps);
  4. install: idempotent (Seed-marker), bounded engine-computed names,
     proposable entry shape (kind/trigger_tokens/ground_template/spine);
  5. PROPOSABILITY end-to-end (headline): a synthetic request built from a
     high-support chunk's own trigger tokens + ProgEval-consistent rows —
     the starter codebook alone GAPS (control arm), the chunk-installed arm
     ACCEPTS at rung 1, through domains/prog_synthesis.py's public entry,
     synthesis seed unmodified;
  6. SELF-TEACH end-to-end: an accepted 2-statement program with exactly
     ONE candidate chunk → the ckg_mint rule mints exactly one entry,
     provenance self_taught, bounded name, epoch bumped; a second identical
     accept is RECOGNIZED (deduped) — no second entry, no second bump;
  7. no-Python-decision source audit (the ink-suite pattern).

Run (worktree engine discipline):
    pytest tests/test_prog_chunks_migrated.py --confcutdir=. -q
"""
from __future__ import annotations

import json
import math
import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import substrate_rs as srs  # noqa: E402

from domains import prog_chunk_growth as pcg  # noqa: E402
from domains import prog_synthesis as psy  # noqa: E402

ARTIFACT = os.path.join(ROOT, "results", "prog_chunk_mine.json")


def _term_live(term, env) -> bool:
    s = srs.Substrate()
    try:
        s._inner.evaluate(term, env)
        return True
    except ValueError as e:
        if "UnknownTermType" in str(e):
            return False
        raise


if not _term_live({"type": "ShapeDecode", "goal": {"type": "Var", "name": "g"},
                   "beam": 1, "max_steps": 2, "cand_k": 1, "field": "",
                   "wild_objects": False}, {"g": [["p", "x"]]}) or \
   not _term_live({"type": "ProgEval",
                   "prog": {"type": "ProgSeq", "stmts": []},
                   "env": None, "oracles": None, "fuel": 5, "field": ""}, {}):
    pytest.skip("ShapeDecode/ProgEval not present in the installed "
                "substrate_rs binary — rebuild runners/dsl. Honest skip.",
                allow_module_level=True)


def art():
    with open(ARTIFACT) as f:
        return json.load(f)


def boot():
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    psy.ensure_program_synthesis(s, s._inner, ag)
    return s, ag


_NAME_MINED = re.compile(r"^ck_[a-z0-9_]+_n[0-9]+_q[0-9]+$")
_NAME_TAUGHT = re.compile(r"^ckt_[a-z0-9_]+_q[0-9]+$")


# ---------------------------------------------------------------------------
# 1) seed loads clean
# ---------------------------------------------------------------------------
def test_seed_loads_clean():
    from substrate.seed_loader import manifest_for
    manifest = manifest_for("prog_chunk_growth")
    assert manifest["id"] == "prog_chunk_growth"
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    summary = s._inner.load_seed_manifest(manifest, ag)
    assert summary["rules_skipped"] == []
    assert summary["reflexes_skipped"] == []
    assert len(manifest["rules"]) == 3


# ---------------------------------------------------------------------------
# 2) mining artifact: determinism + rows-are-the-baseline derivations
# ---------------------------------------------------------------------------
def test_mining_determinism_recorded():
    a = art()
    det = a["determinism"]
    assert det["runs"] == 2, "the twin run is part of the claim"
    assert det["byte_identical"] is True
    assert det["sha256_run1"] == det["sha256_run2"]


def test_totals_derive_from_rows():
    a = art()
    rows = a["chunks"]
    t = a["totals"]
    assert t["kept_final"] == len(rows)
    assert t["cueable"] == sum(1 for r in rows if r["cueable"])
    # cueable == has trigger tokens == no exclusion reason (one fact).
    for r in rows:
        assert r["cueable"] == bool(r["trigger_tokens"])
        assert r["cueable"] == (r["cue_excluded"] is None)
    grain = {}
    for r in rows:
        k = "compound_1" if r["n_stmts"] == 1 else "window_%d" % r["n_stmts"]
        grain[k] = grain.get(k, 0) + 1
    assert t["grain_distribution"] == grain
    per_variant = {}
    for r in rows:
        per_variant[r["labels"][0]] = per_variant.get(r["labels"][0], 0) + 1
    assert t["chunks_per_first_variant"] == per_variant
    # every row's support clears the registered threshold (merged rows sum
    # component supports, each of which cleared it).
    s_star = a["threshold"]["s_star"]
    for r in rows:
        assert r["support"] >= s_star


def test_support_threshold_honesty():
    """s* re-derived from the artifact's own curve by the registered §1.3
    rule; the curve covers the whole type population (no silent caps)."""
    a = art()
    curve = a["support_curve"]
    assert sum(r["n_types"] for r in curve) == a["totals"]["distinct_chunk_types"]
    recurring = sum(r["n_types"] for r in curve if r["support"] >= 2)
    target = max(1, math.ceil(0.01 * recurring))
    supports = sorted({r["support"] for r in curve if r["support"] >= 2})

    def kept_at(s):
        return sum(r["n_types"] for r in curve if r["support"] >= s)

    s_star = None
    for s in supports:
        if kept_at(s) <= target:
            s_star = s
            break
    if s_star is None:
        s_star = supports[-1]
    floor_engaged = False
    if kept_at(s_star) < 8:
        floor_engaged = True
        for s in reversed(supports):
            if kept_at(s) >= 8:
                s_star = s
                break
    thr = a["threshold"]
    assert thr["s_star"] == s_star
    assert thr["recurring_types"] == recurring
    assert thr["quantile_target"] == target
    assert thr["floor_engaged"] == floor_engaged
    assert thr["kept_at_s_star"] == kept_at(s_star) == a["totals"]["kept_pre_dedup"]


def test_dedup_adoption_rule():
    """The registered §1.4 adoption rule, re-applied to the artifact's own
    family tables — and the P3 family-collapse comparison is measurable:
    idiom grain keeps > 1 chunk per multi-member family."""
    a = art()
    dd = a["dedup"]
    fam_pre = dd["families_pre"]
    multi = sorted(f for f, n in fam_pre.items() if n >= 3)
    assert dd["multi_member_families"] == len(multi)
    post23 = [dd["criterion_23"]["families_post"].get(f, 0) for f in multi]
    med = sorted(post23)[len(post23) // 2] if len(post23) % 2 else \
        (sorted(post23)[len(post23) // 2 - 1] + sorted(post23)[len(post23) // 2]) / 2.0
    assert dd["median_post_23_multi"] == med
    expected = "5/6" if (multi and med == 1) else "2/3"
    assert dd["adopted"] == expected
    # the headline reconciliation vs P3: the adopted codebook does NOT
    # collapse every family to one member (P3's depth-1 signature).
    adopted_fams = dd["criterion_%s" % dd["adopted"].replace("/", "")]["families_post"]
    assert any(n > 1 for n in adopted_fams.values()), \
        "idiom grain reproduced the P3 family collapse — investigate"


# ---------------------------------------------------------------------------
# 4) install: idempotent, bounded names, proposable entry shape
# ---------------------------------------------------------------------------
def test_install_idempotent_and_names_bounded():
    s, ag = boot()
    n1 = pcg.install_mined_chunks(s)
    a = art()
    assert n1 == a["totals"]["kept_final"]
    n2 = pcg.install_mined_chunks(s)      # Seed-marker: a no-op
    assert n2 == 0
    entries = pcg.held_chunk_entries(s)
    assert len(entries) == n1, "no duplicate entries on double install"
    for e in entries:
        assert _NAME_MINED.match(e["name"]), e["name"]
        assert len(e["name"]) <= 40
        assert e["provenance"] == "chunk_mined"
    # entry shape is the proposable one (what ps_propose actually reads).
    for q in s.nodes("ShapeSignature"):
        at = s.node(q)["attrs"]
        if at.get("provenance") != "chunk_mined":
            continue
        assert at["kind"] == "code_write_construction"
        assert at.get("trigger_tokens") is not None
        assert at.get("spine") == 1.0
        tmpl = json.loads(at["ground_template"])
        assert tmpl["mode"] == "code_write_stmts"
        assert isinstance(tmpl["stmts"], list) and tmpl["stmts"]


# ---------------------------------------------------------------------------
# 5) PROPOSABILITY — the headline end-to-end gate
# ---------------------------------------------------------------------------
REQ = "write a function guard_none that yields nothing if the input is missing"
ROWS = [({"v0": None}, None), ({"v0": 5}, None), ({"v0": 0}, None)]


def _expected_winners():
    """Derive from the artifact which cueable chunks the request can cue
    (ps_propose semantics: eligible = any trigger token among the request's
    content tokens; winner = max trigger-token count). The request carries
    the token IF."""
    a = art()
    elig = [r for r in a["chunks"] if r["cueable"] and "IF" in r["trigger_tokens"]]
    assert elig, "artifact drifted: no cueable IF chunk — re-pin this gate"
    top = max(len(r["trigger_tokens"]) for r in elig)
    return {r["name"] for r in elig if len(r["trigger_tokens"]) == top}


def test_proposability_control_starter_codebook_gaps():
    s, ag = boot()
    r = psy.synthesize_from_request(s, ag, REQ, ROWS)
    assert r["status"] == "gapped"
    assert r["rungs"]["codebook"] is None, \
        "control arm must never reach rung 1 (no trigger match)"


def test_proposability_chunk_arm_accepts_at_rung_1():
    s, ag = boot()
    assert pcg.install_mined_chunks(s) > 0
    r = psy.synthesize_from_request(s, ag, REQ, ROWS)
    assert r["status"] == "accepted"
    assert r["rungs"]["codebook"] == 1.0
    assert r["rungs"]["enumerate"] is None
    assert r["construction"] in _expected_winners()
    assert r["attempts"] == 1.0
    # held-out inputs (never in the spec rows), via the reflected subgraph:
    # the guard idiom returns None on both branches.
    roots = s.neighbours(r["program"], "ir_subgraph")
    assert len(roots) == 1
    for env in ({"v0": 9}, {"v0": None}):
        out = s._inner.evaluate(
            {"type": "ProgEval", "prog": {"type": "Var", "name": "p"},
             "env": {"type": "Var", "name": "e"}, "oracles": None,
             "fuel": 10000, "field": ""}, {"e": env, "p": roots[0]})
        assert out["halted"] is True and out["trap"] is None
        assert out["result"] is None


# ---------------------------------------------------------------------------
# 6) SELF-TEACH — accepted program → exactly one deduped self_taught chunk
# ---------------------------------------------------------------------------
COMBINE_REQ = "write a function combine that yields the combine of a and b"
COMBINE_ROWS = [({"a": 1, "b": 2}, 3), ({"a": 4, "b": 5}, 9), ({"a": 0, "b": 0}, 0)]
COMBINE_TMPL = {
    "desc": "returns a and b combined", "mode": "code_write_stmts",
    "args": ["a", "b"],
    "stmts": [{"type": "ProgReturn", "value": {"type": "Var", "name": "t"}},
              {"type": "ProgAssignVar", "name": "t",
               "value": {"type": "Plus", "items": [
                   {"type": "Var", "name": "a"}, {"type": "Var", "name": "b"}]}}]}


def _boot_selfteach():
    s, ag = boot()
    pcg.ensure_chunk_growth(s, s._inner, ag)
    # gate setup: a 2-statement spine template (mechanical graph data) whose
    # accepted IR has exactly ONE candidate chunk (one 2-window, no
    # compounds) — the "exactly one" shape of the registered gate.
    s.add_node("ShapeSignature", {
        "name": "gate_combine_spine", "kind": "code_write_construction",
        "signature": json.dumps([["COMBINE"]]), "trigger_tokens": ["COMBINE"],
        "spine": 1.0, "ground_template": json.dumps(COMBINE_TMPL)})
    return s, ag


def test_self_teach_mints_exactly_one_then_dedups():
    s, ag = _boot_selfteach()
    r = psy.synthesize_from_request(s, ag, COMBINE_REQ, COMBINE_ROWS)
    assert r["status"] == "accepted"
    assert pcg.held_chunk_entries(s) == []
    ep0 = s.node(ag)["attrs"].get("write_codebook_epoch") or 0.0
    pcg.chunk_pump(s, ag)
    entries = pcg.held_chunk_entries(s)
    assert len(entries) == 1, "exactly one chunk minted from the accept"
    e = entries[0]
    assert e["provenance"] == "self_taught"
    assert _NAME_TAUGHT.match(e["name"]), e["name"]
    assert len(e["name"]) <= 40
    ep1 = s.node(ag)["attrs"].get("write_codebook_epoch")
    assert ep1 == ep0 + 1.0, "the three-line epoch move, in-rule"
    obs = pcg.read_chunk_observations(s)
    assert [o["status"] for o in obs] == ["minted"]
    assert obs[0]["minted"] == e["name"]

    # DEDUP: a second identical accept is recognized, never re-minted.
    r2 = psy.synthesize_from_request(s, ag, COMBINE_REQ, COMBINE_ROWS)
    assert r2["status"] == "accepted"
    pcg.chunk_pump(s, ag)
    entries2 = pcg.held_chunk_entries(s)
    assert len(entries2) == 1
    assert s.node(ag)["attrs"].get("write_codebook_epoch") == ep1, \
        "no epoch bump on a recognized (deduped) chunk"
    statuses = sorted(o["status"] for o in pcg.read_chunk_observations(s))
    assert statuses == ["minted", "recognized"]
    rec = [o for o in pcg.read_chunk_observations(s)
           if o["status"] == "recognized"][0]
    assert rec["covered_by"] == e["name"]


def test_self_teach_ignores_foreign_programs():
    """The ckg_mark_scan rule's provenance guard: a Program not minted by
    the synthesis pipeline never enters the chunk flow."""
    s, ag = boot()
    pcg.ensure_chunk_growth(s, s._inner, ag)
    g = s.add_node("Goal", {"kind": "other"})
    p = s.add_node("Program", {"name": "x", "provenance": "hand_authored",
                               "program": "{}"})
    s.add_edge_unchecked(g, "accepted_program", p)
    pcg.chunk_pump(s, ag)
    assert s.node(p)["attrs"].get("ck_scan_marked") is None
    assert pcg.held_chunk_entries(s) == []


# ---------------------------------------------------------------------------
# 7) no-Python-decision source audit (the ink-suite pattern)
# ---------------------------------------------------------------------------
def test_no_python_decision_source_audit():
    src = open(os.path.join(ROOT, "domains", "prog_chunk_growth.py")).read()
    for forbidden in ("graph_rewrite", "gr.run(", "gr._match", "gr._apply",
                      "make_rule("):
        assert forbidden not in src, forbidden
    # the module never branches on a goal/observation STATUS to decide an
    # outcome — the only status writes in Python set the INITIAL pending
    # facts; recognize/mint/mark transitions are seed rules.
    assert "pk_status\", \"recognized\"" not in src
    assert "pk_status\", \"minted\"" not in src
    assert "ck_scan_marked\", 1.0" not in src.replace("ck_chunks_scanned", "")
