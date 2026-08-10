#!/usr/bin/env python
"""prog_construction_scan — P3's "training run" (PROGRAM_SYNTHESIS_PLAN.md
§4-P3, PROGRAM_SYNTHESIS_P3_PREREG.md).

Over the P2 emittable corpus (`results/prog_ir_python_coverage.json`, scope A
ids, SORTED — scan order is part of the claim), re-emit each function's hub IR
(`domains/prog_ir_emit`), extract statement-grain construction signatures
(`domains/prog_ir_signature` — the fixed walk), and push them through the
`prog_construction_loop` seed rules on ONE growing substrate. The rules decide
recognize / merge / mint at `run_rules` fixpoint; this driver only:

  * emits + extracts (mechanical cross-frame translation),
  * dedups identical signatures at the I/O boundary (frequency counting —
    the distributional-stats precedent),
  * ingests Observations and calls `run_rules`,
  * APPLIES marked merges one per round (`apply_marked_merge` — copying the
    rules' own verdict, prereg §2),
  * tallies + garbage-collects settled Observations (working-set GC, the
    flow-retire precedent; the codebook and epoch persist),
  * counts label bigrams with add-1 smoothing (mechanical arithmetic) and
    writes `ConstructionBigram` nodes + the results artifact.

No decisions over graph state. Run:

  PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 \
      OZMA_SEED_PERSIST_DISABLED=1 python scripts/prog_construction_scan.py

Env knobs (all recorded in the artifact — no silent caps):
  PC_SCAN_LIMIT=<n>   deterministic prefix of the sorted id list (prereg §6)
  PC_SCAN_BATCH=<n>   distinct-new-observation batch size (default 200)
  PC_SCAN_ONCE=1      skip the second (determinism-evidence) run
"""
from __future__ import annotations

import ast
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
from domains import prog_ir_signature as pis  # noqa: E402

COVERAGE_JSON = os.path.join(ROOT, "results", "prog_ir_python_coverage.json")
OUT_JSON = os.path.join(ROOT, "results", "prog_construction_scan.json")
BOUND_START, BOUND_END = "<s>", "</s>"

# The P2 cross-frame triple spellings (test_prog_read_rust_lua_migrated.py's
# _PY_TRIPLES — the python side of the registered triples).
PY_TRIPLES = {
    "max_of_two": ("def max_of_two(a, b):\n"
                   "    if a > b:\n"
                   "        return a\n"
                   "    return b\n"),
    "sum_list": ("def sum_list(xs):\n"
                 "    total = 0\n"
                 "    for x in xs:\n"
                 "        total += x\n"
                 "    return total\n"),
    "count_matching": ("def count_matching(xs, t):\n"
                       "    c = 0\n"
                       "    for x in xs:\n"
                       "        if x == t:\n"
                       "            c += 1\n"
                       "    return c\n"),
}


def log(*a):
    print("[pc-scan]", *a, flush=True)
    sys.stdout.flush()


# --------------------------------------------------------------------------- #
#  Corpus resolution (mechanical: id -> ast.FunctionDef -> IR).
# --------------------------------------------------------------------------- #
def load_corpus_ids(limit=None):
    with open(COVERAGE_JSON) as f:
        cov = json.load(f)
    ids = sorted(cov["scope_baseline_domains_toplevel"]["emittable"]["ids"])
    cut = None
    if limit is not None and limit < len(ids):
        ids = ids[:limit]
        cut = {"kind": "deterministic_prefix", "n": limit,
               "note": "PC_SCAN_LIMIT prefix of the sorted id list (prereg §6)"}
    return ids, cut


class _FileCache:
    """Parse each corpus file once; map top-level FunctionDef by name."""

    def __init__(self):
        self._by_file = {}

    def resolve(self, file_rel: str, name: str, lineno: int):
        if file_rel not in self._by_file:
            path = os.path.join(ROOT, file_rel)
            try:
                with open(path) as f:
                    tree = ast.parse(f.read())
                fns = {}
                for n in tree.body:
                    if isinstance(n, ast.FunctionDef):
                        fns.setdefault(n.name, []).append(n)
                self._by_file[file_rel] = fns
            except (OSError, SyntaxError) as e:
                self._by_file[file_rel] = {"__error__": str(e)}
        fns = self._by_file[file_rel]
        if "__error__" in fns:
            return None, fns["__error__"]
        cands = fns.get(name) or []
        if not cands:
            return None, "missing"
        for c in cands:
            if c.lineno == lineno:
                return c, None
        # drift-tolerant: (file, qualname) is the identity (the P2 rule);
        # duplicates resolve to the LAST definition (python binding semantics).
        return cands[-1], "lineno_drift"


def parse_id(fid: str):
    file_rel, rest = fid.split("::", 1)
    name, lineno = rest.rsplit("@", 1)
    return file_rel, name, int(lineno)


# --------------------------------------------------------------------------- #
#  The loop driver (ingest -> run_rules -> apply merges -> tally -> GC).
# --------------------------------------------------------------------------- #
class LoopAgent:
    def __init__(self):
        self.sub = srs.Substrate()
        self.native = self.sub._inner
        self.ag = self.sub.add_node("Agent", {})
        pis.ensure_prog_construction_loop(self.sub, self.native, self.ag)
        self.label_by_key = {}
        self.occurrences = {}
        self.merge_events = 0

    def epoch(self):
        return self.sub.node(self.ag)["attrs"].get("prog_codebook_epoch") or 0.0

    def settle_batch(self, items):
        """items: list of (sig_key, signature, occurrences). Returns
        {sig_key: outcome-dict}. Rules decide; merges applied one per round."""
        if not items:
            return {}
        obs_by_key = {}
        for key, sig, occ in items:
            obs_by_key[key] = pis.observe_construction(
                self.sub, self.ag, sig, key=key, occurrences=occ)
        self.native.run_rules()
        # merge rounds: apply ONE rule-marked merge per round (prereg §2),
        # in deterministic INGESTION order, until quiescent.
        for _ in range(len(items) * 4 + 8):
            marked = [
                o for o in obs_by_key.values()
                if self.sub.node(o)["attrs"].get("pc_status") == "merge_marked"]
            if not marked:
                break
            applied = pis.apply_marked_merge(self.sub, self.ag, marked[0])
            if applied is None:
                # incomplete verdict — honest stop, recorded by caller
                break
            self.merge_events += 1
            self.native.run_rules()
        out = {}
        for key, o in obs_by_key.items():
            r = pis.read_observation(self.sub, o)
            r["label"] = r["minted"] or r["covered_by"]
            out[key] = r
            self.label_by_key[key] = r["label"]
            # working-set GC (prereg §6): the codebook + epoch persist.
            self.sub.remove_node(o)
        return out

    def codebook(self):
        return pis.prog_codebook(self.sub)


def scan(ids, batch_size):
    cache = _FileCache()
    agent = LoopAgent()
    drift, unresolved, no_longer_emittable = [], [], []
    per_fn = {}          # fid -> {"labels_keys": [...]}
    pending = []         # (key, signature, occurrences) new distinct
    pending_keys = set()
    seen_keys = set()
    statuses = {}
    curve = []
    n_stmt_instances = 0
    t0 = time.time()

    def flush(pos):
        nonlocal pending
        if not pending:
            return
        outcomes = agent.settle_batch(pending)
        for k, r in outcomes.items():
            statuses[k] = r["status"]
        pending = []
        pending_keys.clear()
        curve.append({"corpus_position": pos,
                      "codebook_size": len(agent.codebook()),
                      "distinct_signatures": len(seen_keys),
                      "merge_events": agent.merge_events})

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
        ir = r["ir"]
        top_keys = []
        for s in pis.function_statements(ir):
            top_keys.append(pis.sig_key(pis.statement_signature(s)))
        per_fn[fid] = top_keys
        for s in pis.walk_statements(ir):
            sig = pis.statement_signature(s)
            key = pis.sig_key(sig)
            n_stmt_instances += 1
            agent.occurrences[key] = agent.occurrences.get(key, 0) + 1
            if key in seen_keys:
                continue
            seen_keys.add(key)
            if key not in pending_keys:
                pending_keys.add(key)
                pending.append((key, sig, 1))
        # flush on batch fill OR every 250 corpus positions (curve density —
        # distinct new signatures get rare fast, and the curve should still
        # sample codebook size along the corpus, not only at rare fills).
        if len(pending) >= batch_size or (pending and (pos + 1) % 250 == 0):
            flush(pos + 1)
            log("pos", pos + 1, "of", len(ids),
                "codebook", curve[-1]["codebook_size"],
                "distinct", len(seen_keys),
                "merges", agent.merge_events,
                "%.1fs" % (time.time() - t0))
    flush(len(ids))

    # ---- per-quantum coverage counts (mechanical tally) --------------------
    coverage = {}
    for key, label in agent.label_by_key.items():
        if label is None:
            continue
        coverage[label] = coverage.get(label, 0) + agent.occurrences.get(key, 0)

    # ---- function label sequences + bigrams --------------------------------
    sequences = {fid: [agent.label_by_key.get(k) or "?" for k in keys]
                 for fid, keys in per_fn.items()}
    bigrams, prev_totals, vocab = count_bigrams(sequences.values())
    write_bigram_nodes(agent, bigrams, prev_totals, len(vocab))

    return agent, {
        "ids_scanned": len(ids),
        "functions_emitted": len(per_fn),
        "unresolved": unresolved,
        "lineno_drift_n": len(drift),
        "no_longer_emittable": no_longer_emittable,
        "statement_instances": n_stmt_instances,
        "distinct_signatures": len(seen_keys),
        "statuses_by_key": statuses,
        "coverage_curve": curve,
        "coverage_by_label": dict(sorted(coverage.items())),
        "sequences": sequences,
        "bigrams": bigrams,
        "prev_totals": prev_totals,
        "vocab_size": len(vocab),
        "merge_events": agent.merge_events,
        "elapsed_s": round(time.time() - t0, 1),
    }


def count_bigrams(sequences):
    """Consecutive pairs over top-level label sequences with <s>/</s>
    boundaries; add-1 smoothing over V = observed labels + </s> (prereg §4.5).
    Pure counting — P4's rules will READ these."""
    counts, prev_totals, labels = {}, {}, set()
    for seq in sequences:
        toks = [BOUND_START] + list(seq) + [BOUND_END]
        labels.update(seq)
        for a, b in zip(toks, toks[1:]):
            counts[(a, b)] = counts.get((a, b), 0) + 1
            prev_totals[a] = prev_totals.get(a, 0) + 1
    vocab = labels | {BOUND_END}
    table = []
    v = len(vocab)
    for (a, b), c in sorted(counts.items()):
        table.append({"prev": a, "next": b, "count": c,
                      "prev_total": prev_totals[a],
                      "trans_logp": math.log((c + 1) / (prev_totals[a] + v))})
    return table, dict(sorted(prev_totals.items())), vocab


def write_bigram_nodes(agent, bigrams, prev_totals, vocab_size):
    for row in bigrams:
        agent.sub.add_node("ConstructionBigram", {
            "prev": row["prev"], "next": row["next"],
            "count": int(row["count"]), "prev_total": int(row["prev_total"]),
            "vocab_size": int(vocab_size),
            "trans_logp": float(row["trans_logp"]),
        })


# --------------------------------------------------------------------------- #
#  Cross-language: the P2 triples through the SAME loop / codebook.
# --------------------------------------------------------------------------- #
def cross_language(agent):
    try:
        import tree_sitter_lua  # noqa: F401
        import tree_sitter_rust  # noqa: F401
        from domains import prog_ir_lua, prog_ir_rust
    except ImportError as e:
        return {"skipped": f"tree-sitter frames unavailable: {e}"}
    fix = os.path.join(ROOT, "tests", "fixtures", "prog_ir_read_rs_lua")
    out = {}
    for name in ("sum_list", "max_of_two", "count_matching"):
        entry = {}
        irs = {}
        py = prog_ir_emit.emit_prog_ir(PY_TRIPLES[name])
        if py.get("ok"):
            irs["python"] = py["ir"]
        for lang, reader, ext in (("rust", prog_ir_rust, ".rs"),
                                  ("lua", prog_ir_lua, ".lua")):
            try:
                with open(os.path.join(fix, lang, name + ext)) as f:
                    src = f.read()
                rsub = srs.Substrate()
                r = reader.read_function(rsub, src)
                if r.get("ok"):
                    irs[lang] = r["ir"]
                else:
                    entry[lang + "_blockers"] = r.get("blockers")
            except OSError as e:
                entry[lang + "_error"] = str(e)
        for lang, ir in irs.items():
            before = len(agent.codebook())
            merges_before = agent.merge_events
            items, keys = [], []
            for s in pis.walk_statements(ir):
                sig = pis.statement_signature(s)
                key = pis.sig_key(sig)
                if key not in agent.label_by_key and \
                        key not in {k for k, _, _ in items}:
                    items.append((key, sig, 1))
            agent.settle_batch(items)
            top = [agent.label_by_key.get(pis.sig_key(pis.statement_signature(s)))
                   for s in pis.function_statements(ir)]
            entry[lang] = {
                "labels": top,
                "new_quanta_minted": len(agent.codebook()) - before,
                "merge_events": agent.merge_events - merges_before,
            }
        out[name] = entry
    return out


# --------------------------------------------------------------------------- #
#  Artifact (determinism-comparable canonical form).
# --------------------------------------------------------------------------- #
def canonical_artifact(agent, scan_out, xlang):
    codebook = agent.codebook()
    for row in codebook:
        row["coverage_count"] = scan_out["coverage_by_label"].get(row["name"], 0)
    prov = {"minted": 0, "merged": 0}
    for row in codebook:
        prov[row["provenance"] or "minted"] = prov.get(row["provenance"] or "minted", 0) + 1
    return {
        "task": "PROGRAM_SYNTHESIS P3 construction scan",
        "prereg": "PROGRAM_SYNTHESIS_P3_PREREG.md",
        "seed": "seeds/prog_construction_loop.json v1.0.0",
        "grain": "statement (depth-1, params excluded, blocks presence-only), "
                 "function label sequences for bigrams — prereg §1",
        "scan_scope": {
            "corpus": "results/prog_ir_python_coverage.json "
                      "scope_baseline_domains_toplevel.emittable.ids, sorted",
            "ids_scanned": scan_out["ids_scanned"],
            "functions_emitted": scan_out["functions_emitted"],
            "unresolved": scan_out["unresolved"],
            "lineno_drift_n": scan_out["lineno_drift_n"],
            "no_longer_emittable": scan_out["no_longer_emittable"],
            "cut": scan_out.get("cut"),
        },
        "totals": {
            "statement_instances": scan_out["statement_instances"],
            "distinct_signatures": scan_out["distinct_signatures"],
            "codebook_size": len(codebook),
            "provenance": prov,
            "merge_events": scan_out["merge_events"],
            "vocab_size": scan_out["vocab_size"],
            "bigram_rows": len(scan_out["bigrams"]),
        },
        "prereg_prediction": {
            "codebook_band": [40, 220],
            "merge_events_min": 30,
            "in_band": 40 <= len(codebook) <= 220,
            "merges_met": scan_out["merge_events"] >= 30,
        },
        "codebook": codebook,
        "coverage_curve": scan_out["coverage_curve"],
        "bigrams": scan_out["bigrams"],
        "bigram_smoothing": "add-1 over V = observed labels + </s>; "
                            "trans_logp = ln((c+1)/(prev_total+|V|))",
        "cross_language": xlang,
    }


def one_run(ids, batch_size):
    agent, scan_out = scan(ids, batch_size)
    xlang = cross_language(agent)
    return canonical_artifact(agent, scan_out, xlang)


def main():
    limit = os.environ.get("PC_SCAN_LIMIT")
    limit = int(limit) if limit else None
    batch_size = int(os.environ.get("PC_SCAN_BATCH") or 200)
    ids, cut = load_corpus_ids(limit)
    log("corpus:", len(ids), "ids; batch", batch_size,
        ("CUT: %r" % (cut,)) if cut else "full")

    art1 = one_run(ids, batch_size)
    if cut:
        art1["scan_scope"]["cut"] = cut
    blob1 = json.dumps(art1, sort_keys=True, separators=(",", ":"))
    h1 = hashlib.sha256(blob1.encode()).hexdigest()

    if os.environ.get("PC_SCAN_ONCE"):
        determinism = {"runs": 1, "sha256": h1,
                       "note": "PC_SCAN_ONCE set — single run, no twin"}
    else:
        log("second run (determinism evidence)…")
        art2 = one_run(ids, batch_size)
        if cut:
            art2["scan_scope"]["cut"] = cut
        blob2 = json.dumps(art2, sort_keys=True, separators=(",", ":"))
        h2 = hashlib.sha256(blob2.encode()).hexdigest()
        determinism = {"runs": 2, "sha256_run1": h1, "sha256_run2": h2,
                       "byte_identical": blob1 == blob2}
        log("determinism:", determinism)

    art1["determinism"] = determinism
    art1["date"] = "2026-07-31"   # fixed label, excluded from the twin compare
    with open(OUT_JSON, "w") as f:
        json.dump(art1, f, indent=1, sort_keys=True)
        f.write("\n")
    log("codebook", art1["totals"]["codebook_size"],
        "merges", art1["totals"]["merge_events"],
        "distinct", art1["totals"]["distinct_signatures"],
        "-> ", OUT_JSON)


if __name__ == "__main__":
    main()
