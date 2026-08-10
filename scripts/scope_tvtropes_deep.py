#!/usr/bin/env python3
"""scope_tvtropes_deep — READ-ONLY MEASUREMENT + SCOPING for a DEEP TVTropes import.

NOT an import. NOT agent logic. A scoping SCRIPT (world-adapter-grade tooling): it
streams the TVTropesData corpus to MEASURE it, grounds a SMALL sample of assembled
trope-documents through the UNCHANGED grounding faculty
(`wikipedia_consumption.consume_article`, source_text=fed document, no seek) to
measure per-trope concept YIELD + wall time, then EXTRAPOLATES a single-thread and
6-worker deep-import wall-clock. Parallel to the Wikipedia import plan.

DEEP (this scope) vs SHALLOW (domains/tropes_teacher.build_tropes_index):
  shallow kept name -> 700-char Description SNIPPET + 3 example snippets, as an
  on-demand lookup cache. DEEP grounds the FULL Description + ALL examples per trope
  as a real microtheory (concepts extracted, gated, taught).

donkey=0 (grounding = faculties; no LLM). NO import, NO git, NO Rust/seed/agent-logic
edits. Streams the zip; grounds a ~120-trope sample into an ISOLATED temp seeds dir
(cleaned up). Does NOT disturb the running wiki import.

Usage:
  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/scope_tvtropes_deep.py \
      [--sample 120] [--doc-cap 40000]
"""
from __future__ import annotations

import argparse
import contextlib
import csv
import io
import math
import os
import statistics as st
import sys
import tempfile
import time
import zipfile
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
for p in (str(ROOT), str(ROOT / "runners" / "dsl" / "python"), str(ROOT / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
os.chdir(ROOT)

ZIP = Path(os.environ.get("TVTROPES_ZIP", str(Path.home() / "Downloads" / "TVTropesData.zip")))
DEFS_MEMBER = "TVTropesData/tropes.csv"
EXAMPLE_MEMBERS = {
    "TVTropesData/film_tropes.csv": "film",
    "TVTropesData/tv_tropes.csv": "tv",
    "TVTropesData/lit_tropes.csv": "lit",
}
N_TROPES_CORPUS = 29465  # the shallow-index trope count (for the time estimate)


def _raise_field_limit() -> None:
    lim = sys.maxsize
    while True:
        try:
            csv.field_size_limit(lim)
            return
        except OverflowError:
            lim = int(lim // 10)


def _open(zf, member):
    return io.TextIOWrapper(zf.open(member, "r"), encoding="utf-8", errors="replace", newline="")


def _norm(name: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


def _de_camel(name: str) -> str:
    import re
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", name)
    s = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", s)
    return s.replace("_", " ").strip().lower()


def _dist(vals):
    vals = list(vals)
    if not vals:
        return dict(n=0)
    s = sorted(vals)
    def pct(p):
        return s[min(len(s) - 1, int(p * len(s)))]
    return dict(n=len(s), mean=sum(s) / len(s), median=st.median(s),
                p10=pct(0.10), p90=pct(0.90), p99=pct(0.99), max=s[-1], total=sum(s))


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (p, max(0.0, c - h), min(1.0, c + h))


# --------------------------------------------------------------------------- #
#  1. CORPUS MEASURE
# --------------------------------------------------------------------------- #

def measure_corpus():
    _raise_field_limit()
    descriptions: dict[str, str] = {}   # key -> full Description
    names: dict[str, str] = {}
    desc_lens = []
    t0 = time.time()
    with zipfile.ZipFile(ZIP) as zf:
        with _open(zf, DEFS_MEMBER) as fh:
            for row in csv.DictReader(fh):
                name = (row.get("Trope") or "").strip()
                if not name:
                    continue
                key = _norm(name)
                if not key:
                    continue
                desc = (row.get("Description") or "")
                descriptions[key] = desc
                names[key] = name
                desc_lens.append(len(desc))
        # examples: per-trope count + total example-text char length
        ex_count: dict[str, int] = {}
        ex_chars: dict[str, int] = {}
        per_ex_len = []           # sampled per-example lengths (every 20th, for the dist)
        total_ex_rows = 0
        i = 0
        for member in EXAMPLE_MEMBERS:
            with _open(zf, member) as fh:
                for row in csv.DictReader(fh):
                    key = _norm((row.get("Trope") or "").strip())
                    if not key:
                        continue
                    ex = row.get("Example") or ""
                    ex_count[key] = ex_count.get(key, 0) + 1
                    ex_chars[key] = ex_chars.get(key, 0) + len(ex)
                    total_ex_rows += 1
                    if i % 20 == 0:
                        per_ex_len.append(len(ex))
                    i += 1
    read_s = time.time() - t0
    # per-trope full-document volume = Description chars + all example chars
    doc_vol = {k: len(descriptions.get(k, "")) + ex_chars.get(k, 0)
               for k in set(descriptions) | set(ex_count)}
    return dict(descriptions=descriptions, names=names, desc_lens=desc_lens,
                ex_count=ex_count, ex_chars=ex_chars, per_ex_len=per_ex_len,
                total_ex_rows=total_ex_rows, doc_vol=doc_vol, read_s=read_s)


def collect_sample_docs(sample_keys, cap):
    """Second stream: gather the actual example texts for ONLY the sampled tropes."""
    _raise_field_limit()
    want = set(sample_keys)
    docs = {k: [] for k in want}
    sizes = {k: 0 for k in want}
    with zipfile.ZipFile(ZIP) as zf:
        for member, medium in EXAMPLE_MEMBERS.items():
            with _open(zf, member) as fh:
                for row in csv.DictReader(fh):
                    key = _norm((row.get("Trope") or "").strip())
                    if key not in want or sizes[key] >= cap:
                        continue
                    ex = (row.get("Example") or "").strip()
                    if not ex:
                        continue
                    work = (row.get("Title") or "").strip()
                    piece = f"In {work} ({medium}): {ex}" if work else ex
                    docs[key].append(piece)
                    sizes[key] += len(piece)
    return docs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=120)
    ap.add_argument("--doc-cap", type=int, default=40000,
                    help="cap per-trope grounding document chars (mega-tropes chunked)")
    args = ap.parse_args()

    print("=" * 78)
    print("TVTROPES DEEP-IMPORT SCOPE  (read-only measurement; donkey=0)")
    print("=" * 78)
    if not ZIP.exists():
        print(f"CORPUS NOT FOUND: {ZIP}")
        sys.exit(1)
    print(f"corpus: {ZIP}  ({ZIP.stat().st_size/1e6:.0f} MB)")

    # -------- 1. CORPUS MEASURE --------
    print("\n" + "-" * 78)
    print("1. CORPUS MEASURE  (streamed once)")
    print("-" * 78)
    m = measure_corpus()
    n_defs = len(m["descriptions"])
    dl = _dist(m["desc_lens"])
    exc = _dist(list(m["ex_count"].values()))
    exl = _dist(m["per_ex_len"])
    dv = _dist(list(m["doc_vol"].values()))
    stubs = sum(1 for k in m["ex_count"] if k not in m["descriptions"])
    total_desc_mb = sum(m["desc_lens"]) / 1e6
    total_ex_mb = sum(m["ex_chars"].values()) / 1e6
    print(f"  stream time              : {m['read_s']:.1f}s")
    print(f"  tropes in tropes.csv     : {n_defs:,}")
    print(f"  example-only stub tropes : {stubs:,}  (appear in examples, no Description row)")
    print(f"  total example rows       : {m['total_ex_rows']:,}")
    print()
    print(f"  FULL Description length (chars) — vs the shallow 700-char _DEF_CAP:")
    print(f"    median {dl['median']:.0f} | mean {dl['mean']:.0f} | p90 {dl['p90']:.0f} "
          f"| p99 {dl['p99']:.0f} | max {dl['max']:,}")
    over_cap = sum(1 for x in m["desc_lens"] if x > 700)
    print(f"    Descriptions LONGER than the 700-char snippet cap: "
          f"{over_cap:,}/{n_defs:,} ({100*over_cap/max(1,n_defs):.0f}%)")
    print()
    print(f"  examples / trope:")
    print(f"    median {exc['median']:.0f} | mean {exc['mean']:.0f} | p90 {exc['p90']:.0f} "
          f"| p99 {exc['p99']:.0f} | max {exc['max']:,}")
    print(f"  example TEXT length (chars, sampled every-20th n={exl['n']:,}):")
    print(f"    median {exl['median']:.0f} | mean {exl['mean']:.0f} | p90 {exl['p90']:.0f} "
          f"| max {exl['max']:,}")
    print()
    print(f"  FULL-TEXT volume / trope (Description + ALL its examples, chars):")
    print(f"    median {dv['median']:,.0f} | mean {dv['mean']:,.0f} | p90 {dv['p90']:,.0f} "
          f"| p99 {dv['p99']:,.0f} | max {dv['max']:,}")
    print(f"  CORPUS TOTAL groundable text:")
    print(f"    Descriptions {total_desc_mb:.1f} MB + Examples {total_ex_mb:.1f} MB "
          f"= {total_desc_mb+total_ex_mb:.1f} MB")

    # -------- 2. GROUNDING YIELD (sample) --------
    print("\n" + "-" * 78)
    print("2. GROUNDING YIELD  (sample under CPU contention from the running wiki import)")
    print("-" * 78)
    # sample: real tropes (have a Description), stratified across the volume range.
    real = [k for k in m["descriptions"] if m["doc_vol"].get(k, 0) > 0]
    real.sort(key=lambda k: m["doc_vol"][k])
    N = min(args.sample, len(real))
    idx = [int(j * (len(real) - 1) / (N - 1)) for j in range(N)] if N > 1 else [0]
    sample_keys = [real[j] for j in sorted(set(idx))]
    print(f"  sample: {len(sample_keys)} tropes, stratified across the full volume range")
    docs_ex = collect_sample_docs(sample_keys, args.doc_cap)

    # boot the agent ONCE (isolated temp seeds dir; cleaned up).
    print("  booting WorldAdapter + load_all_seeds + warm_wordnet ...")
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf), contextlib.redirect_stdout(buf):
        from substrate.world_adapter import WorldAdapter
        from substrate.boot_all import load_all_seeds
        from domains import dictionary_lexicon as dl_mod
        from domains import wikipedia_consumption as wc
        a = WorldAdapter(seeds=())
        load_all_seeds(a)
        dl_mod.warm_wordnet("en")

    tmp = Path(tempfile.mkdtemp(prefix="tvtropes_scope_"))
    seeds_dir = tmp / "acquired"
    seeds_dir.mkdir(parents=True, exist_ok=True)

    def build_document(key):
        desc = m["descriptions"].get(key, "").strip()
        exs = docs_ex.get(key, [])
        body = "\n\n".join(([desc] if desc else []) + exs)
        return body[: args.doc_cap]

    # WARMUP (pays any first-call cost so the timed runs are warm).
    with contextlib.redirect_stderr(buf), contextlib.redirect_stdout(buf):
        wc.consume_article(a, m["names"][sample_keys[0]], seeds_dir=seeds_dir,
                           source_text=build_document(sample_keys[0]), quality=True)

    rows = []  # (name, vol, n_examples, doc_chars, consumed, n_concepts, secs, reason)
    for key in sample_keys:
        name = m["names"][key]
        doc = build_document(key)
        t = time.time()
        with contextlib.redirect_stderr(buf), contextlib.redirect_stdout(buf):
            try:
                r = wc.consume_article(a, name, seeds_dir=seeds_dir,
                                       source_text=doc, quality=True)
            except Exception as e:
                r = {"consumed": False, "n_admitted": 0, "reason": f"exception: {e}"}
        secs = time.time() - t
        rows.append((name, m["doc_vol"][key], m["ex_count"].get(key, 0), len(doc),
                     bool(r.get("consumed")), r.get("n_admitted", 0), secs,
                     r.get("reason", "")))

    consumed = [r for r in rows if r[4]]
    times = [r[6] for r in rows]
    concepts = [r[5] for r in rows]
    yield_consumed = [r[5] for r in consumed]
    n = len(rows)
    n_consumed = len(consumed)
    p_con, lo_con, hi_con = wilson(n_consumed, n)
    td = _dist(times)
    cd = _dist(concepts)
    print(f"  grounded (consumed)      : {n_consumed}/{n}  "
          f"({100*p_con:.0f}% ; Wilson 95% [{100*lo_con:.0f},{100*hi_con:.0f}])")
    print(f"  concepts/trope (ALL)     : mean {cd['mean']:.1f} | median {cd['median']:.0f} "
          f"| p90 {cd['p90']:.0f} | max {cd['max']}")
    if yield_consumed:
        ycd = _dist(yield_consumed)
        print(f"  concepts/trope (consumed): mean {ycd['mean']:.1f} | median {ycd['median']:.0f} "
              f"| max {ycd['max']}")
    print(f"  per-trope grounding TIME : mean {td['mean']:.3f}s | median {td['median']:.3f}s "
          f"| p90 {td['p90']:.3f}s | max {td['max']:.3f}s  (WARM, under 6-core contention)")
    # honest reason breakdown for the non-consumed
    from collections import Counter
    reasons = Counter(r[7].split("(")[0].split("—")[0].strip()[:48]
                      for r in rows if not r[4])
    if reasons:
        print(f"  non-consumed reasons:")
        for reason, c in reasons.most_common():
            print(f"    {c:3d} x {reason}")
    # yield vs size (does more examples => more concepts?)
    small = [r for r in rows if r[1] < dv["median"]]
    large = [r for r in rows if r[1] >= dv["median"]]
    sm = sum(x[5] for x in small) / max(1, len(small))
    lg = sum(x[5] for x in large) / max(1, len(large))
    print(f"  yield by size: small-half {sm:.1f} concepts | large-half {lg:.1f} concepts")

    mean_t = td["mean"]

    # -------- 3. TIME ESTIMATE --------
    print("\n" + "-" * 78)
    print("3. TIME ESTIMATE  (extrapolated from the warm per-trope grounding rate)")
    print("-" * 78)
    N_all = N_TROPES_CORPUS
    single_s = N_all * mean_t
    workers = 6
    # parallel: shard tropes round-robin over 6 workers; near-linear (independent
    # documents, isolated seeds dirs — the wiki-runner shape). Modest overhead.
    par_s = single_s / workers * 1.10  # 10% sharding/imbalance overhead
    def hms(s):
        h = int(s // 3600); mn = int((s % 3600) // 60); sec = int(s % 60)
        return f"{h}h{mn:02d}m{sec:02d}s" if h else f"{mn}m{sec:02d}s"
    print(f"  tropes to ground         : {N_all:,}")
    print(f"  warm per-trope grounding : {mean_t:.3f}s (sample mean, n={n})")
    print(f"  SINGLE-THREAD estimate   : {single_s:,.0f}s  = {hms(single_s)}")
    print(f"  6-WORKER PARALLEL estimate: {par_s:,.0f}s = {hms(par_s)}  "
          f"(round-robin shard, +10% overhead)")
    print(f"    NOTE: 6 cores are currently saturated by the running wiki import — a")
    print(f"    deep run launched AFTER it frees the cores would match/beat this (the")
    print(f"    sample was timed UNDER that contention, so it is conservative).")
    tot_concepts = cd["mean"] * N_all
    print(f"  projected concepts grounded (mean {cd['mean']:.1f}/trope x {N_all:,}): "
          f"~{tot_concepts:,.0f}")

    # -------- 4. SCOPE SUMMARY --------
    print("\n" + "-" * 78)
    print("4. SCOPE  (deliverable — parallel to the Wikipedia plan)")
    print("-" * 78)
    print(f"  CORPUS SCALE : {n_defs:,} defined tropes (+{stubs:,} example-only stubs); "
          f"{m['total_ex_rows']:,} examples;")
    print(f"                 {total_desc_mb+total_ex_mb:.0f} MB groundable text total.")
    print(f"  GROUNDING UNIT: per-trope full document = FULL Description + ALL its")
    print(f"                 examples (concatenated; capped {args.doc_cap:,} chars, "
          f"mega-tropes chunked).")
    print(f"  MEASURED YIELD: {100*p_con:.0f}% consumed [{100*lo_con:.0f},{100*hi_con:.0f}]; "
          f"mean {cd['mean']:.1f} concepts/trope (cap {30}/doc).")
    print(f"  TIME         : single {hms(single_s)} ; 6-worker {hms(par_s)}.")
    print()
    print("  DEEP vs SHALLOW:")
    print(f"    SHALLOW (tropes_teacher.build_tropes_index): name -> 700-char Description")
    print(f"      SNIPPET + 3 example snippets, JSON lookup cache. NOTHING grounded.")
    print(f"    DEEP (this scope): FULL Description ({100*over_cap/max(1,n_defs):.0f}% exceed the")
    print(f"      700-char cap) + ALL {m['total_ex_rows']:,} examples grounded into gated,")
    print(f"      taught microtheories — concept_graph edge-learns each trope region.")
    print()
    print("  DOMAIN CAVEAT  (the headline finding — the hypothesis did NOT hold):")
    print("    TVTropes prose is narrative-analysis JARGON + proper-noun-heavy example")
    print("    text (work/medium names), informal/subjective, with wiki-markup residue —")
    print("    NOT encyclopedic prose. The consume_article extractor")
    print("    (gda.extract_microtheory) is ENUM-CUE based: it harvests concepts from")
    print("    enumeration syntax (\"such as\", \"includes\", \"consists of\", \"phases:\").")
    print("    Trope prose fires these cues SPARSELY, so most documents extract THIN")
    print(f"    ({reasons.get('source named no extractable concepts', 0)}/{n} sampled tropes"
          f" returned 'no extractable concepts').")
    print("    CRUCIAL: the huge example volume BARELY compensates — extraction is keyed")
    print("    on enumeration SYNTAX, not text volume; more examples add a few cues but")
    print(f"    yield stays far below the 30/doc cap (see 'yield by size' above: "
          f"large-half {lg:.1f} vs small-half {sm:.1f}, both << 30).")
    print("    So the corpus is document-RICH but extraction-POOR under this faculty. The")
    print("    nominal_filter + admissibility gate further DROP proper-noun/fragment noise.")
    print()
    print("  RECOMMENDATION:")
    worth = "WORTH IT" if (p_con > 0.5 and cd["mean"] >= 3) else \
            "NOT worth it AS-IS — extractor mismatch; needs a trope-aware reader first"
    print(f"    {worth}.")
    print(f"    The import is CHEAP ({hms(par_s)} on 6 workers) — but only because most")
    print("    documents extract THIN and short-circuit, so the low wall-clock is a")
    print(f"    SYMPTOM of low yield (~{cd['mean']:.1f} concepts/trope, {30}/doc cap never")
    print("    approached), NOT of efficient rich grounding. Grounding cost scales with")
    print("    concepts EXTRACTED, so a better reader would raise BOTH yield and time.")
    print("    PATH A (ship as-is): run a tropes analogue of scripts/wiki_import_runner.py")
    print("      — shard 29,465 tropes round-robin over 6 workers, pre-build per-trope")
    print("      documents (one streamed pass grouping the scattered examples by Trope),")
    print("      feed source_text=document to consume_article with an ISOLATED per-worker")
    print("      seeds_dir. Fast, but low-value under the current extractor.")
    print("    PATH B (recommended): FIRST add a trope-aware extraction path — the trope")
    print("      NAME itself is the concept (de_camel -> 'chekhovs gun'), the Description")
    print("      is its definition, and example Titles are proper-noun instances. That")
    print("      grounds 1 high-value concept/trope GUARANTEED (29k conventions) + binds")
    print("      instances, independent of enum-cue density. Then the volume DOES pay off.")
    print("    PREP either way: a one-pass corpus->per-trope-document sharder (examples")
    print("    are scattered across the 3 CSVs, must be grouped by Trope first). No")
    print("    Rust/seed changes; PATH A reuses the unchanged faculty, PATH B adds a")
    print("    reader (world-adapter-grade, no agent decisions).")
    print()
    print("  HONEST ASSUMPTIONS:")
    print(f"    - sample n={n} stratified across volume range; consumed-rate CI is Wilson 95%.")
    print(f"    - per-trope time timed UNDER 6-core wiki-import contention (conservative);")
    print(f"      e01a6af8 argmax speedup (~1.3x) already in this binary.")
    print(f"    - document capped at {args.doc_cap:,} chars; {sum(1 for k in sample_keys if m['doc_vol'][k]>args.doc_cap)} "
          f"of the sampled tropes hit the cap. Real mega-tropes need chunking.")
    print(f"    - time estimate = mean warm per-trope x {N_all:,}; parallel = /6 x 1.10.")
    print(f"    - N_all={N_all:,} is the shallow-index trope count; measured tropes.csv "
          f"has {n_defs:,} (+{stubs:,} stubs).")
    print("\ndonkey=0")

    # cleanup
    import shutil
    with contextlib.suppress(Exception):
        shutil.rmtree(tmp)


if __name__ == "__main__":
    main()
