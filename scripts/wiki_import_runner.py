#!/usr/bin/env python3
"""wiki_import_runner — PARALLEL, RESUMABLE, SEQUENTIAL-READ Wikipedia import.

This is NEW TOOLING (a script), NOT agent logic. It is a world-adapter-grade
ORCHESTRATOR: it reads the structured-enwiki parquet shards SEQUENTIALLY (never
the random sqlite title-index seek — that was the old 27h artifact), applies a
cheap structural PRE-FILTER (skip the ~76% zero-yield stub/list/disambiguation
tail so the grounded lexicon stays high-value), and hands each surviving
article's ALREADY-READ text to the UNCHANGED grounding faculty
(`wikipedia_consumption.consume_article`, `source_text=` fed → source
"fed_document", the exact-source path, so NO seek). Memory is bounded by the
agent's OWN OS paging (`graph_virtual_memory`); each worker persists to its OWN
isolated `seeds/acquired/import_wNN/` dir (which `load_all_seeds` does NOT glob,
so the global boot graph is unperturbed) and its OWN corpus mmap slab.

Design (the four properties the task asks for):

  1. PARALLEL WORKERS (multiprocessing) — the 86 shards are partitioned across
     N workers ROUND-ROBIN (worker w owns shard indices where idx % N == w).
     Each worker boots a WorldAdapter + load_all_seeds + warm_wordnet ONCE.

  2. SEQUENTIAL READ + PRE-FILTER — per worker, iterate its shards' row-groups
     in order via `pyarrow ParquetFile.read_row_group` (columns name/abstract/
     sections only). Per article: parse text, compute body_len; SKIP if
     body_len < --min-body OR title is List/Index/Outline-of / bare-year /
     (YYYY) / a disambiguation lead. Survivors are grounded via consume_article
     with the sequentially-read text FED IN (no seek). page_consumed + enforce
     bounds the live graph.

  3. RESUMABLE — a per-worker JSON progress file records every COMPLETED
     (shard_idx, row_group). On restart, a completed row-group is skipped (not
     re-ground). Checkpoint is written after every row-group (atomic replace).

  4. RESOURCE-SAFE — GraphVirtualMemory caps the live graph (budget = base
     kernel + --headroom working-set nodes); cold consumed clusters page OUT to
     the worker's mmap corpus slab. Per-worker stats (articles/s, concepts, RSS,
     corpus bytes) are logged to the progress file every row-group.

donkey=0 (the grounding path is the faculties; no LLM). NO git, NO seed/Rust
edits, NO agent-decision logic — this file only reads shards, filters, and calls
the existing faculty.

Usage:
  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/wiki_import_runner.py \
      --workers 6 [--first-shards K] [--max-articles-per-worker M] \
      [--min-body 2000] [--headroom 800] [--run-tag import]

  # verify (few shards, cap, small workers):
  ... --workers 2 --first-shards 4 --max-articles-per-worker 400 --run-tag verify
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import re
import resource
import sys
import time
import contextlib
import multiprocessing as mp
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
for p in (str(ROOT), str(ROOT / "runners" / "dsl" / "python"), str(ROOT / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
os.chdir(ROOT)

DATA = ROOT / "data" / "wiki" / "structured" / "enwiki" / "data"
TOTAL = 7_597_149

# where per-worker checkpoints + logs live (NOT under seeds/; not globbed).
PROG_DIR = ROOT / "var" / "wiki_import"
# per-worker isolated acquired-seeds dir root (load_all_seeds globs seeds/*.json
# + seeds/generated/*.json ONLY — NOT seeds/acquired/**, verified).
ACQ_ROOT = ROOT / "seeds" / "acquired"
# per-worker isolated corpus-slab dir root (the mmap page-out target).
SLAB_ROOT = ROOT / "var" / "wiki_import_slabs"

# ---- pre-filter signals (reuse the metadata-pass heuristics) ----------------
_YEAR_PAREN = re.compile(r"\(\d{4}\)")
_BARE_YEAR = re.compile(r"^\d{3,4}$")
_LIST_PREFIX = re.compile(r"^(List of|Index of|Outline of|Lists of)\b", re.I)


def _title_flagged(name: str) -> bool:
    nm = (name or "").strip()
    if _LIST_PREFIX.match(nm):
        return True
    if _BARE_YEAR.match(nm) or _YEAR_PAREN.search(nm):
        return True
    return False


# --------------------------------------------------------------------------- #
#  checkpoint helpers (atomic, per worker)
# --------------------------------------------------------------------------- #

def _prog_path(run_tag: str, wid: int) -> Path:
    return PROG_DIR / f"{run_tag}_w{wid:02d}.json"


def _load_progress(run_tag: str, wid: int) -> dict:
    p = _prog_path(run_tag, wid)
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            pass
    return {"run_tag": run_tag, "worker": wid, "done_rgs": [],
            "articles_seen": 0, "articles_grounded": 0, "articles_skipped": 0,
            "concepts": 0, "no_source": 0, "wall_s": 0.0}


def _save_progress(run_tag: str, wid: int, prog: dict) -> None:
    p = _prog_path(run_tag, wid)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(prog))
    tmp.replace(p)  # atomic


# --------------------------------------------------------------------------- #
#  worker
# --------------------------------------------------------------------------- #

def worker(wid: int, shard_indices: list, files: list, args) -> None:
    """One worker: boot once, iterate its shards' row-groups sequentially,
    pre-filter + ground survivors, checkpoint per row-group. Isolated seeds +
    corpus slab. Resumable via the per-worker progress file."""
    import pyarrow.parquet as pq
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf), contextlib.redirect_stdout(buf):
        from substrate.world_adapter import WorldAdapter
        from substrate.boot_all import load_all_seeds
        from domains import dictionary_lexicon as dl
        from domains import wiki_local as wl
        from domains import wikipedia_consumption as wc
        from domains import graph_virtual_memory as gvmmod
        a = WorldAdapter(seeds=())
        load_all_seeds(a)
        base = a.inner.node_count()
        dl.warm_wordnet("en")

    run_tag = args.run_tag
    seeds_dir = ACQ_ROOT / f"{run_tag}_w{wid:02d}"
    seeds_dir.mkdir(parents=True, exist_ok=True)
    slab_dir = SLAB_ROOT / f"{run_tag}_w{wid:02d}"
    slab_dir.mkdir(parents=True, exist_ok=True)
    budget = base + int(args.headroom)
    with contextlib.redirect_stderr(buf), contextlib.redirect_stdout(buf):
        gvm = gvmmod.GraphVirtualMemory(
            a.inner, corpus=f"{run_tag}_w{wid:02d}",
            budget_nodes=budget, slab_dir=slab_dir)

    prog = _load_progress(run_tag, wid)
    done = set(tuple(x) for x in prog["done_rgs"])
    t0 = time.time()
    cap = args.max_articles_per_worker
    stop = False

    for si in shard_indices:
        if stop:
            break
        path = files[si]
        pf = pq.ParquetFile(path)
        for rg in range(pf.num_row_groups):
            key = (si, rg)
            if key in done:
                continue
            tb = pf.read_row_group(rg, columns=["name", "abstract", "sections"])
            names = tb.column("name").to_pylist()
            absts = tb.column("abstract").to_pylist()
            secs = tb.column("sections").to_pylist()
            for i in range(tb.num_rows):
                prog["articles_seen"] += 1
                name = names[i]
                abst = absts[i] or ""
                # cheap title pre-filter FIRST (no body parse needed).
                if _title_flagged(name) or wl.is_disambiguation(abst):
                    prog["articles_skipped"] += 1
                    continue
                body = wl._section_text(secs[i])
                text = (abst + ("\n\n" + body if body else "")).strip()
                if len(text) < args.min_body:
                    prog["articles_skipped"] += 1
                    continue
                # GROUND: feed the sequentially-read text (source_text ->
                # fed_document, exact-source path, NO seek). Faculty unchanged.
                try:
                    with contextlib.redirect_stderr(buf), contextlib.redirect_stdout(buf):
                        r = wc.consume_article(a, name, seeds_dir=seeds_dir,
                                               source_text=text)
                        if r.get("consumed"):
                            prog["articles_grounded"] += 1
                            prog["concepts"] += r.get("n_admitted", 0)
                            if gvmmod.page_consumed(gvm, a, r):
                                gvm.enforce()
                        else:
                            prog["no_source"] += 1
                except Exception:
                    prog["no_source"] += 1
                if cap and (prog["articles_grounded"] >= cap):
                    stop = True
                    break
            # CHECKPOINT after every row-group (even on cap-break, record partial
            # progress but DON'T mark this rg done if we broke mid-rg).
            if not stop:
                done.add(key)
                prog["done_rgs"].append(list(key))
            prog["wall_s"] = round(time.time() - t0, 2)
            prog["rss_mb"] = round(resource.getrusage(
                resource.RUSAGE_SELF).ru_maxrss / 1024.0, 1)
            prog["resident_nodes"] = a.inner.node_count()
            prog["corpus_records"] = gvm.corpus_records()
            prog["corpus_bytes"] = gvm.corpus_bytes()
            prog["base_nodes"] = base
            prog["budget_nodes"] = budget
            _save_progress(run_tag, wid, prog)
            if stop:
                break
    prog["wall_s"] = round(time.time() - t0, 2)
    prog["done"] = True
    _save_progress(run_tag, wid, prog)


# --------------------------------------------------------------------------- #
#  driver
# --------------------------------------------------------------------------- #

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--first-shards", type=int, default=0,
                    help="only process the first K shards (0 = all 86)")
    ap.add_argument("--max-articles-per-worker", type=int, default=0,
                    help="cap grounded articles per worker (0 = no cap)")
    ap.add_argument("--min-body", type=int, default=2000,
                    help="skip articles with parsed body_len < this")
    ap.add_argument("--headroom", type=int, default=800,
                    help="working-set nodes above the base kernel (GVM budget)")
    ap.add_argument("--run-tag", default="import")
    args = ap.parse_args()

    PROG_DIR.mkdir(parents=True, exist_ok=True)
    ACQ_ROOT.mkdir(parents=True, exist_ok=True)
    SLAB_ROOT.mkdir(parents=True, exist_ok=True)

    files = sorted(glob.glob(str(DATA / "*.parquet")))
    assert files, f"no shards under {DATA}"
    n_shards = len(files)
    active = list(range(n_shards))
    if args.first_shards > 0:
        active = active[:args.first_shards]

    W = max(1, min(args.workers, len(active)))
    # round-robin partition of the active shards across W workers.
    assign = {w: [active[k] for k in range(len(active)) if k % W == w]
              for w in range(W)}

    print(f"wiki_import_runner: {n_shards} shards, using {len(active)} "
          f"(first_shards={args.first_shards or 'all'}), {W} workers")
    for w in range(W):
        print(f"  worker {w}: shards {assign[w]}")
    print(f"  min_body={args.min_body}  headroom={args.headroom}  "
          f"cap/worker={args.max_articles_per_worker or 'none'}  run_tag={args.run_tag}")
    sys.stdout.flush()

    ctx = mp.get_context("fork")
    procs = []
    for w in range(W):
        p = ctx.Process(target=worker, args=(w, assign[w], files, args))
        p.start()
        procs.append(p)
    for p in procs:
        p.join()

    # aggregate
    tot = {"articles_seen": 0, "articles_grounded": 0, "articles_skipped": 0,
           "concepts": 0, "no_source": 0}
    wall = 0.0
    for w in range(W):
        pr = _load_progress(args.run_tag, w)
        for k in tot:
            tot[k] += pr.get(k, 0)
        wall = max(wall, pr.get("wall_s", 0.0))
    print("\n=== IMPORT RUN COMPLETE ===")
    print(f"  workers={W}  wall={wall:.1f}s")
    seen = tot["articles_seen"]
    skip = tot["articles_skipped"]
    print(f"  articles seen     : {seen:,}")
    print(f"  pre-filter skipped: {skip:,}  ({100*skip/max(1,seen):.1f}%)")
    print(f"  grounded          : {tot['articles_grounded']:,}")
    print(f"  no-source/thin    : {tot['no_source']:,}")
    print(f"  concepts grounded : {tot['concepts']:,}")
    if wall > 0:
        print(f"  throughput        : {seen/wall:.1f} articles-seen/s | "
              f"{tot['articles_grounded']/wall:.2f} grounded/s (aggregate)")
    print("donkey=0")


if __name__ == "__main__":
    main()
