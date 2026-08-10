#!/usr/bin/env python
"""prog_chunk_mine — P7-C: mine the IDIOM-GRAIN chunk codebook from the
P2/P3 corpus (PROGRAM_SYNTHESIS_P7C.md §1 — the registered rules; written
before this script first ran).

Over the 4099-identity emittable corpus (sorted ids — scan order is part of
the claim; resolution/emission via the P3 scan's OWN plumbing, imported),
extract candidate chunks (2-4-statement windows + single compound
statements, role/slot-abstracted — domains/prog_chunk_growth.chunk_record,
the ONE fixed walk shared with the self-teach adapter), count support,
apply the REGISTERED threshold rule (§1.3: the 1%-quantile heavy tail of
recurring types, floor 8), dedup by the engine's own AntiUnify (§1.4:
measured at 2/3 AND 5/6 within identical label-sequence+shape groups;
adoption per the registered collapse test), and mint the survivors as
proposable write-codebook rows with engine-computed bounded names.

Deterministic: a FULL second run is compared byte-for-byte (the P3
determinism-evidence protocol). No silent caps: the whole support curve is
in the artifact; totals derive from rows.

Run:
  PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 \
      OZMA_SEED_PERSIST_DISABLED=1 python scripts/prog_chunk_mine.py

Env knobs (recorded in the artifact — no silent caps):
  CKM_LIMIT=<n>   deterministic prefix of the sorted id list
  CKM_ONCE=1      skip the second (determinism-evidence) run
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import substrate_rs as srs  # noqa: E402

from domains import prog_ir_emit  # noqa: E402
from domains import prog_chunk_growth as pcg  # noqa: E402
from prog_construction_scan import _FileCache, load_corpus_ids, parse_id  # noqa: E402

OUT_JSON = os.path.join(ROOT, "results", "prog_chunk_mine.json")


def log(*a):
    print("[ck-mine]", *a, flush=True)


# --------------------------------------------------------------------------- #
#  Engine calls (AntiUnify / FixedCount via evaluate — the criterion is the
#  engine's, never re-implemented in Python).
# --------------------------------------------------------------------------- #
class Engine:
    def __init__(self):
        self.native = srs.Substrate()._inner

    def anti_unify(self, rels_a, rels_b):
        out = self.native.evaluate(
            {"type": "AntiUnify", "values": {"type": "SetT", "items": [
                {"type": "Lit", "value": rels_a},
                {"type": "Lit", "value": rels_b}]}}, {})
        return _plain(out)

    def fixed_count(self, rels) -> int:
        return int(self.native.evaluate(
            {"type": "FixedCount",
             "pattern": {"type": "Lit", "value": rels}}, {}))

    def name(self, head_label, n_stmts, idx) -> str:
        return pcg.chunk_entry_name(self.native, head_label, n_stmts, idx)


def _plain(v):
    if isinstance(v, (list, tuple)):
        return [_plain(x) for x in v]
    return v


# --------------------------------------------------------------------------- #
#  Pass 1 — extraction + support counting over the corpus.
# --------------------------------------------------------------------------- #
def extract(ids):
    cache = _FileCache()
    types = {}          # chunk_key -> {"rec", "support", "lits": {json: n}}
    unresolved, no_longer_emittable, drift = [], [], []
    n_functions = 0
    n_candidates = 0
    t0 = time.time()
    for pos, fid in enumerate(ids):
        file_rel, name, lineno = parse_id(fid)
        node, note = cache.resolve(file_rel, name, lineno)
        if node is None:
            unresolved.append({"id": fid, "reason": note})
            continue
        if note == "lineno_drift":
            drift.append(fid)
        r = prog_ir_emit.emit_prog_ir(node)
        if not r.get("ok"):
            no_longer_emittable.append({"id": fid, "blockers": r.get("blockers")})
            continue
        n_functions += 1
        for rec in pcg.chunk_candidates(r["ir"]):
            n_candidates += 1
            k = rec["chunk_key"]
            row = types.get(k)
            if row is None:
                row = {"rec": rec, "support": 0, "lits": {}}
                types[k] = row
            row["support"] += 1
            lit_key = json.dumps(rec["lit_values"], sort_keys=True,
                                 separators=(",", ":"))
            row["lits"][lit_key] = row["lits"].get(lit_key, 0) + 1
        if (pos + 1) % 1000 == 0:
            log("pos", pos + 1, "types", len(types),
                "candidates", n_candidates, "%.1fs" % (time.time() - t0))
    return types, {
        "ids_scanned": len(ids),
        "functions_emitted": n_functions,
        "unresolved": unresolved,
        "lineno_drift_n": len(drift),
        "no_longer_emittable": no_longer_emittable,
        "candidate_instances": n_candidates,
        "distinct_chunk_types": len(types),
        "elapsed_s": round(time.time() - t0, 1),
    }


# --------------------------------------------------------------------------- #
#  Registered threshold rule (§1.3) — derived from the distribution.
# --------------------------------------------------------------------------- #
def support_curve(types):
    """Exact histogram: [{support, n_types}] ascending — the full curve."""
    hist = {}
    for row in types.values():
        s = row["support"]
        hist[s] = hist.get(s, 0) + 1
    return [{"support": s, "n_types": hist[s]} for s in sorted(hist)]


def apply_threshold_rule(curve):
    """§1.3 verbatim: recurring = support>=2; target = ceil(1% of recurring
    type count); s* = smallest s with |{support>=s}| <= target; floor: if
    that keeps < 8, lower s* to the largest s keeping >= 8."""
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
        s_star = supports[-1] if supports else 2
    floor_engaged = False
    if kept_at(s_star) < 8:
        floor_engaged = True
        for s in reversed(supports):
            if kept_at(s) >= 8:
                s_star = s
                break
    return {"recurring_types": recurring, "quantile_target": target,
            "s_star": int(s_star), "kept_at_s_star": kept_at(s_star),
            "floor_engaged": floor_engaged}


# --------------------------------------------------------------------------- #
#  AntiUnify dedup (§1.4) — engine Terms; measured at 2/3 and 5/6.
# --------------------------------------------------------------------------- #
def dedup(kept, eng, num, den):
    """Greedy join by descending support within (label-seq, rel-count)
    groups. Criterion: den*FixedCount(LGG) >= num*FixedCount(concrete).
    Returns (survivors, join_events). Survivor keeps its own concrete
    record; chunk_rels becomes the LGG; supports sum."""
    survivors = []
    joins = 0
    groups = {}
    for row in kept:
        gk = (tuple(row["labels"]), len(row["rels"]))
        groups.setdefault(gk, []).append(row)
    for row in kept:                      # kept is already in canonical order
        gk = (tuple(row["labels"]), len(row["rels"]))
        joined = False
        for surv in survivors:
            if surv["_group"] != gk:
                continue
            lgg = eng.anti_unify(surv["chunk_rels"], row["rels"])
            if not isinstance(lgg, list):
                continue
            fc_l = eng.fixed_count(lgg)
            fc_c = eng.fixed_count(row["rels"])
            if den * fc_l >= num * fc_c:
                surv["chunk_rels"] = lgg
                surv["support"] += row["support"]
                surv["merged_keys"].append(row["chunk_key"])
                joins += 1
                joined = True
                break
        if not joined:
            survivors.append({
                "_group": gk,
                "chunk_key": row["chunk_key"],
                "labels": list(row["labels"]),
                "rels": row["rels"],
                "chunk_rels": [list(r) for r in row["rels"]],
                "support": row["support"],
                "rec": row["rec"],
                "lits": row["lits"],
                "merged_keys": [],
            })
    return survivors, joins


def family_counts(rows, key=lambda r: tuple(r["labels"])):
    fams = {}
    for r in rows:
        fams[" + ".join(key(r))] = fams.get(" + ".join(key(r)), 0) + 1
    return dict(sorted(fams.items()))


def median(xs):
    xs = sorted(xs)
    if not xs:
        return None
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2.0


# --------------------------------------------------------------------------- #
#  Minting rows (modal slot fills; engine-computed names).
# --------------------------------------------------------------------------- #
def modal_lits(lits_counter):
    best_key, best_n = None, -1
    for k in sorted(lits_counter):        # ties → smallest canonical JSON
        n = lits_counter[k]
        if n > best_n:
            best_key, best_n = k, n
    return json.loads(best_key) if best_key is not None else []


def mint_rows(survivors, eng):
    rows = []
    for idx, surv in enumerate(survivors):
        rec = surv["rec"]
        fills = modal_lits(surv["lits"])
        tmpl = pcg.ground_template_for(rec, fills)
        name = eng.name(rec["labels"][0], rec["n_stmts"], idx)
        rows.append({
            "name": name,
            "chunk_key": surv["chunk_key"],
            "labels": list(surv["labels"]),
            "n_stmts": rec["n_stmts"],
            "support": int(surv["support"]),
            "args": list(rec["args"]),
            "trigger_tokens": list(rec["triggers"]),
            "derived_tokens": list(rec["derived_tokens"]),
            "cueable": bool(rec["triggers"]),
            "cue_excluded": rec["cue_excluded"],
            "slot_fills": fills,
            "chunk_rels": surv["chunk_rels"],
            "merged_keys": surv["merged_keys"],
            "ground_template": tmpl,
            "provenance": "chunk_mined",
        })
    return rows


# --------------------------------------------------------------------------- #
#  One full run → canonical artifact dict.
# --------------------------------------------------------------------------- #
def one_run(ids):
    eng = Engine()
    types, scope = extract(ids)
    # wall-clock is not part of the determinism claim (the P3 `date` rule):
    # reported via the log + main()'s post-hash annotation, never the blob.
    scope.pop("elapsed_s", None)
    curve = support_curve(types)
    thr = apply_threshold_rule(curve)
    s_star = thr["s_star"]

    kept = []
    for k in sorted(types):
        row = types[k]
        if row["support"] >= s_star:
            kept.append({"chunk_key": k, "labels": row["rec"]["labels"],
                         "rels": row["rec"]["rels"], "support": row["support"],
                         "rec": row["rec"], "lits": row["lits"]})
    kept.sort(key=lambda r: (-r["support"], r["chunk_key"]))

    fam_pre = family_counts(kept)
    surv23, joins23 = dedup(kept, eng, num=2, den=3)
    surv56, joins56 = dedup(kept, eng, num=5, den=6)
    fam23 = family_counts(surv23)
    fam56 = family_counts(surv56)

    # registered adoption rule (§1.4): adopt 2/3 unless, among families with
    # >=3 kept members pre-join, the MEDIAN post-join member count under 2/3
    # is 1 (the P3 collapse signature).
    multi = [f for f, n in fam_pre.items() if n >= 3]
    med23 = median([fam23.get(f, 0) for f in multi]) if multi else None
    adopted = "2/3"
    if multi and med23 == 1:
        adopted = "5/6"
    survivors = surv23 if adopted == "2/3" else surv56

    chunks = mint_rows(survivors, eng)

    # family-collapse comparison vs P3 (chunks per first-statement variant).
    per_variant = {}
    for row in chunks:
        per_variant[row["labels"][0]] = per_variant.get(row["labels"][0], 0) + 1

    grain_dist = {}
    for row in chunks:
        gk = "compound_1" if row["n_stmts"] == 1 else "window_%d" % row["n_stmts"]
        grain_dist[gk] = grain_dist.get(gk, 0) + 1

    return {
        "task": "PROGRAM_SYNTHESIS P7-C idiom-grain chunk mine",
        "registered": "PROGRAM_SYNTHESIS_P7C.md par.1 (written before this ran)",
        "version": "1.0.0",
        "grain": "contiguous 2-4 statement windows + single compound "
                 "statements with bodies; roles/slots abstracted; extern/"
                 "attr/op names concrete (par.1.2)",
        "scan_scope": scope,
        "support_curve": curve,
        "threshold": thr,
        "dedup": {
            "criterion_23": {"join_events": joins23, "survivors": len(surv23),
                             "families_post": fam23},
            "criterion_56": {"join_events": joins56, "survivors": len(surv56),
                             "families_post": fam56},
            "families_pre": fam_pre,
            "multi_member_families": len(multi),
            "median_post_23_multi": med23,
            "adopted": adopted,
        },
        "totals": {
            "candidate_instances": scope["candidate_instances"],
            "distinct_chunk_types": scope["distinct_chunk_types"],
            "kept_pre_dedup": len(kept),
            "kept_final": len(chunks),
            "cueable": sum(1 for c in chunks if c["cueable"]),
            "grain_distribution": dict(sorted(grain_dist.items())),
            "chunks_per_first_variant": dict(sorted(per_variant.items())),
        },
        "chunks": chunks,
    }


def main():
    limit = os.environ.get("CKM_LIMIT")
    limit = int(limit) if limit else None
    ids, cut = load_corpus_ids(limit)
    log("corpus:", len(ids), "ids", ("CUT: %r" % (cut,)) if cut else "full")

    art1 = one_run(ids)
    if cut:
        art1["scan_scope"]["cut"] = cut
    blob1 = json.dumps(art1, sort_keys=True, separators=(",", ":"))
    h1 = hashlib.sha256(blob1.encode()).hexdigest()

    if os.environ.get("CKM_ONCE"):
        determinism = {"runs": 1, "sha256": h1,
                       "note": "CKM_ONCE set — single run, no twin"}
    else:
        log("second run (determinism evidence)…")
        art2 = one_run(ids)
        if cut:
            art2["scan_scope"]["cut"] = cut
        blob2 = json.dumps(art2, sort_keys=True, separators=(",", ":"))
        h2 = hashlib.sha256(blob2.encode()).hexdigest()
        determinism = {"runs": 2, "sha256_run1": h1, "sha256_run2": h2,
                       "byte_identical": blob1 == blob2}
        log("determinism:", determinism)

    art1["determinism"] = determinism
    art1["date"] = "2026-07-31"     # fixed label, excluded from twin compare
    with open(OUT_JSON, "w") as f:
        json.dump(art1, f, indent=1, sort_keys=True)
        f.write("\n")
    log("kept", art1["totals"]["kept_final"],
        "of", art1["totals"]["distinct_chunk_types"], "types; s* =",
        art1["threshold"]["s_star"], "->", OUT_JSON)


if __name__ == "__main__":
    main()
