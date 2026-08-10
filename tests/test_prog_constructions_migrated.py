"""test_prog_constructions_migrated — P3 gates: the prog_construction sd loop
(seeds/prog_construction_loop.json), merge-at-mint, bounded naming, corpus
transition statistics (PROGRAM_SYNTHESIS_PLAN.md §4-P3,
PROGRAM_SYNTHESIS_P3_PREREG.md §5).

Gates:
  1. seed loads via load_seed_manifest with ZERO skipped rules/reflexes;
  2. mint-dedup: same shape twice (co-pending, worst case for the engine's
     snapshot-drain apply) -> EXACTLY ONE quantum — and this is also the
     recognized-after-epoch law: mint -> in-rule epoch bump -> pc_redecode
     re-arm -> literal re-decode covers, all inside ONE run_rules fixpoint;
  3. merge-at-mint both directions: two NEAR shapes (2/3-leaf-fix criterion)
     -> join, not a second mint (LGG signature, WILD exactly at the differing
     slot, provenance 'merged', floor: >= 2/3 of leaves stay fixed); two FAR
     shapes -> two quanta;
  4. name-boundedness: every codebook name matches the registered bounded
     pattern and never grows with signature size (incl. a real mini-scan);
  5. cross-language: the P2 sum-of-list-loop triple decodes to the SAME
     construction sequence in python + rust + lua on one shared codebook
     (lua carries exactly the one documented ipairs-counter assign extra);
  6. bigram sanity: counts sum, trans_logp finite, assign->return present;
  7. the scan artifact (results/prog_construction_scan.json) is internally
     consistent and its determinism twin is byte-identical.

Run (worktree engine discipline — the P1 note):
    pytest tests/test_prog_constructions_migrated.py --confcutdir=. -q
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

from domains import prog_ir_emit  # noqa: E402
from domains import prog_ir_signature as pis  # noqa: E402

WILD = "·?·"
NAME_RE = re.compile(r"^pc_[a-z0-9_]+_r[0-9]+_q[0-9]+$")
ARTIFACT = os.path.join(ROOT, "results", "prog_construction_scan.json")


def _shape_decode_live() -> bool:
    s = srs.Substrate()
    try:
        s._inner.evaluate({"type": "ShapeDecode", "goal": {"type": "Var", "name": "g"},
                           "beam": 1, "max_steps": 2, "cand_k": 1, "field": "",
                           "wild_objects": False}, {"g": [["p", "x"]]})
        return True
    except ValueError as e:
        if "UnknownTermType" in str(e):
            return False
        raise


if not _shape_decode_live():
    pytest.skip("ShapeDecode Term not present in the installed substrate_rs "
                "binary — rebuild runners/dsl. Honest skip, not a fake pass.",
                allow_module_level=True)


def boot():
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    pis.ensure_prog_construction_loop(s, s._inner, ag)
    return s, ag


def codebook_names(s):
    return [c["name"] for c in pis.prog_codebook(s)]


def leaves(sig):
    n = 0
    for rel in sig:
        for slot in rel:
            n += 1
    return n


def fixed_leaves(sig):
    n = 0
    for rel in sig:
        for slot in rel:
            if not (isinstance(slot, (list, tuple)) and list(slot) == [WILD]):
                n += 1
    return n


# ---------------------------------------------------------------------------
# 1) seed loads clean
# ---------------------------------------------------------------------------
def test_seed_loads_clean():
    from substrate.seed_loader import manifest_for
    manifest = manifest_for("prog_construction_loop")
    assert manifest["id"] == "prog_construction_loop"
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    summary = s._inner.load_seed_manifest(manifest, ag)
    assert summary["rules_skipped"] == []
    assert summary["reflexes_skipped"] == []
    assert len(manifest["rules"]) == 6


# ---------------------------------------------------------------------------
# 2) mint-dedup + recognized-after-epoch (one fixpoint)
# ---------------------------------------------------------------------------
def test_same_shape_twice_mints_exactly_one_quantum():
    s, ag = boot()
    sig = [["pstmt", "ProgAssignVar"], ["parg", "value", "Plus"]]
    o1 = pis.observe_construction(s, ag, sig)
    o2 = pis.observe_construction(s, ag, sig)   # co-pending: the worst case
    s._inner.run_rules()
    names = codebook_names(s)
    assert len(names) == 1, f"double mint: {names}"
    # recognized-after-epoch: the mint bumped prog_codebook_epoch in-rule,
    # pc_redecode re-armed, the literal re-decode covered — both recognized.
    r1, r2 = pis.read_observation(s, o1), pis.read_observation(s, o2)
    assert r1["status"] == "recognized" and r2["status"] == "recognized"
    assert r1["covered_by"] == names[0] and r2["covered_by"] == names[0]
    assert s.node(ag)["attrs"].get("prog_codebook_epoch") >= 1.0


def test_third_observation_recognizes_after_epoch_bump():
    s, ag = boot()
    sig = [["pstmt", "ProgReturn"], ["parg", "value", "VAR"]]
    pis.observe_construction(s, ag, sig)
    s._inner.run_rules()
    (name,) = codebook_names(s)
    epoch_after_mint = s.node(ag)["attrs"].get("prog_codebook_epoch")
    assert epoch_after_mint >= 1.0
    o3 = pis.observe_construction(s, ag, sig)
    s._inner.run_rules()
    r = pis.read_observation(s, o3)
    assert r["status"] == "recognized" and r["covered_by"] == name
    assert codebook_names(s) == [name], "recognition must not grow the codebook"


# ---------------------------------------------------------------------------
# 3) merge-at-mint — both directions
# ---------------------------------------------------------------------------
def test_near_shapes_join_not_double_mint():
    s, ag = boot()
    a = [["pstmt", "ProgAssignVar"], ["parg", "value", "Plus"]]
    b = [["pstmt", "ProgAssignVar"], ["parg", "value", "Times"]]
    pis.observe_construction(s, ag, a)
    s._inner.run_rules()
    (name,) = codebook_names(s)
    ob = pis.observe_construction(s, ag, b)
    s._inner.run_rules()
    r = pis.read_observation(s, ob)
    # the RULE decided the join (marked verdict), the driver applies it —
    # the prereg §2 split.
    assert r["status"] == "merge_marked"
    assert r["merge_with"] == name
    applied = pis.apply_marked_merge(s, ag, ob)
    assert applied == name
    s._inner.run_rules()
    r = pis.read_observation(s, ob)
    assert r["status"] == "recognized_merged"
    assert r["covered_by"] == name
    (q,) = pis.prog_codebook(s)
    assert q["provenance"] == "merged"
    assert q["merged_count"] == 1.0
    # WILD exactly at the one differing slot; the 2/3 floor holds.
    assert q["signature"] == [["pstmt", "ProgAssignVar"], ["parg", "value", [WILD]]]
    assert 3 * fixed_leaves(q["signature"]) >= 2 * leaves(q["signature"])


def test_far_shapes_mint_two_quanta():
    s, ag = boot()
    # different heads: never a merge candidate (head relation must be equal)
    a = [["pstmt", "ProgAssignVar"], ["parg", "value", "Plus"]]
    b = [["pstmt", "ProgIfStmt"], ["parg", "cond", "Gt"], ["pblock", "then"]]
    pis.observe_construction(s, ag, a)
    s._inner.run_rules()
    pis.observe_construction(s, ag, b)
    s._inner.run_rules()
    assert len(codebook_names(s)) == 2
    # same head but different relation COUNT: AntiUnify -> WILD -> FixedCount
    # 0 -> criterion fails -> a third quantum, not a join.
    c = [["pstmt", "ProgIfStmt"], ["parg", "cond", "Gt"], ["pblock", "then"],
         ["pblock", "orelse"]]
    oc = pis.observe_construction(s, ag, c)
    s._inner.run_rules()
    r = pis.read_observation(s, oc)
    assert r["merge_with"] is None
    assert len(codebook_names(s)) == 3


# ---------------------------------------------------------------------------
# 4) name-boundedness (incl. a real 30-function mini-scan)
# ---------------------------------------------------------------------------
def test_names_bounded_on_gate_quanta():
    s, ag = boot()
    for sig in ([["pstmt", "ProgAssignVar"], ["parg", "value", "Plus"]],
                [["pstmt", "ProgComprehensionList"], ["parg", "value", "EXTERN"]],
                [["pstmt", "ProgTupleUnpack"], ["parity", "targets", 2],
                 ["parg", "value", "EXTERN"]]):
        pis.observe_construction(s, ag, sig)
        s._inner.run_rules()
    for name in codebook_names(s):
        assert NAME_RE.match(name), name
        assert len(name) <= 40, name


def test_names_bounded_on_a_real_mini_scan():
    import prog_construction_scan as pcs
    ids, _ = pcs.load_corpus_ids(30)
    agent, _out = pcs.scan(ids, 200)
    names = codebook_names(agent.sub)
    assert names, "a 30-function scan must grow at least one quantum"
    for name in names:
        assert NAME_RE.match(name), name
        assert len(name) <= 40, name


# ---------------------------------------------------------------------------
# 5) cross-language — the shared-hub law on one codebook
# ---------------------------------------------------------------------------
def test_cross_language_sum_list_same_construction_sequence():
    try:
        import tree_sitter_lua  # noqa: F401
        import tree_sitter_rust  # noqa: F401
        from domains import prog_ir_lua, prog_ir_rust
    except ImportError:
        pytest.skip("tree_sitter_rust / tree_sitter_lua not installed — honest skip.")
    import prog_construction_scan as pcs
    fix = os.path.join(ROOT, "tests", "fixtures", "prog_ir_read_rs_lua")
    s, ag = boot()

    def settle(ir):
        seen = set()
        for st in pis.walk_statements(ir):
            sig = pis.statement_signature(st)
            key = pis.sig_key(sig)
            if key in seen:
                continue
            seen.add(key)
            pis.observe_construction(s, ag, sig)
        s._inner.run_rules()
        # apply any rule-marked merges (the driver's mechanical half)
        for _ in range(32):
            marked = [o for o in s.nodes("Observation")
                      if s.node(o)["attrs"].get("pc_status") == "merge_marked"]
            if not marked:
                break
            pis.apply_marked_merge(s, ag, marked[0])
            s._inner.run_rules()

    def labels(ir):
        out = []
        for st in pis.function_statements(ir):
            key_obs = None
            k = pis.sig_key(pis.statement_signature(st))
            for o in s.nodes("Observation"):
                if s.node(o)["attrs"].get("sig_key") == k:
                    key_obs = o
            assert key_obs is not None, k
            out.append(pis.construction_label(s, key_obs))
        return out

    py = prog_ir_emit.emit_prog_ir(pcs.PY_TRIPLES["sum_list"])
    assert py["ok"]
    rsub = srs.Substrate()
    rust = prog_ir_rust.read_function(rsub, open(os.path.join(fix, "rust", "sum_list.rs")).read())
    assert rust["ok"], rust.get("blockers")
    lsub = srs.Substrate()
    lua = prog_ir_lua.read_function(lsub, open(os.path.join(fix, "lua", "sum_list.lua")).read())
    assert lua["ok"], lua.get("blockers")

    settle(py["ir"])
    n_after_python = len(codebook_names(s))
    settle(rust["ir"])
    assert len(codebook_names(s)) == n_after_python, \
        "rust sum_list must decode into the SAME codebook — zero new quanta"
    settle(lua["ir"])
    assert len(codebook_names(s)) == n_after_python, \
        "lua sum_list must decode into the SAME codebook — zero new MINTS " \
        "(joins allowed per prereg §4.4)"

    py_seq = labels(py["ir"])
    rs_seq = labels(rust["ir"])
    lua_seq = labels(lua["ir"])
    assert py_seq == rs_seq, (py_seq, rs_seq)
    # lua: the documented ipairs-counter desugar adds exactly ONE extra
    # assign-family label (prereg §4.4) — otherwise the same sequence.
    assert len(lua_seq) == len(py_seq) + 1
    extra = list(lua_seq)
    extra.remove(py_seq[0])  # the counter assign shares the assign label
    assert extra == py_seq, (lua_seq, py_seq)


# ---------------------------------------------------------------------------
# 6) bigram sanity (unit-level, plus a known frequent pair)
# ---------------------------------------------------------------------------
def test_bigram_counts_sum_and_logp_finite():
    import prog_construction_scan as pcs
    seqs = [["assign", "foreach", "return"],
            ["assign", "return"],
            ["assign", "assign", "return"]]
    table, prev_totals, vocab = pcs.count_bigrams(seqs)
    # every sequence contributes len+1 transitions (<s> ... </s>)
    assert sum(r["count"] for r in table) == sum(len(s) + 1 for s in seqs)
    # per-prev consistency: counts for one prev sum to its prev_total
    for prev in prev_totals:
        assert sum(r["count"] for r in table if r["prev"] == prev) == prev_totals[prev]
    for r in table:
        assert math.isfinite(r["trans_logp"]) and r["trans_logp"] < 0.0
    assert any(r["prev"] == "assign" and r["next"] == "return" and r["count"] == 2
               for r in table)


# ---------------------------------------------------------------------------
# 7) the scan artifact — internal consistency + determinism evidence
# ---------------------------------------------------------------------------
def test_scan_artifact_consistent_and_deterministic():
    assert os.path.exists(ARTIFACT), \
        "run scripts/prog_construction_scan.py first (the P3 training run)"
    with open(ARTIFACT) as f:
        art = json.load(f)
    det = art["determinism"]
    if det.get("runs") == 2:
        assert det["byte_identical"] is True
        assert det["sha256_run1"] == det["sha256_run2"]
    # codebook: names bounded, merged signatures keep the 2/3 floor,
    # coverage counts positive for every quantum the scan kept.
    assert art["totals"]["codebook_size"] == len(art["codebook"])
    for row in art["codebook"]:
        assert NAME_RE.match(row["name"]), row["name"]
        assert len(row["name"]) <= 40
        assert 3 * fixed_leaves(row["signature"]) >= 2 * leaves(row["signature"]), \
            f"wild-flood floor violated: {row}"
    # bigrams: per-prev sums match prev_total; logp finite; the registered
    # frequent pair (an assign-family -> return-family transition) exists.
    by_prev = {}
    for r in art["bigrams"]:
        assert math.isfinite(r["trans_logp"])
        by_prev.setdefault(r["prev"], [0, r["prev_total"]])
        by_prev[r["prev"]][0] += r["count"]
    for prev, (total, expected) in by_prev.items():
        assert total == expected, (prev, total, expected)
    assert any("assign" in r["prev"] and "return" in r["next"] and r["count"] > 0
               for r in art["bigrams"]), "assign->return must be observed"
    # scan scope honesty: every non-scanned id is enumerated, never silent.
    assert isinstance(art["scan_scope"]["unresolved"], list)
    assert isinstance(art["scan_scope"]["no_longer_emittable"], list)
    # cross-language (skipped honestly if frames unavailable at scan time)
    x = art["cross_language"]
    if "skipped" not in x:
        sl = x["sum_list"]
        assert sl["python"]["labels"] == sl["rust"]["labels"]
        assert sl["rust"]["new_quanta_minted"] == 0
        assert sl["lua"]["new_quanta_minted"] == 0
        assert len(sl["lua"]["labels"]) == len(sl["python"]["labels"]) + 1
