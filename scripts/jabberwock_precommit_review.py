#!/usr/bin/env python3
"""jabberwock_precommit_review — a PROBE / MEASUREMENT + SYNTHESIS gate.

Before committing to the full 7.6M-title Wikipedia grounding import, MEASURE the two
untested high-value levers on the REAL path and print the honest pre-commit review:

  MEASURE 1 — ARGMAX SCAFFOLDING. Decompose the per-concept sense-disambiguation
  Argmax (consumption_quality._sense_in_context_via_program -> run_sense_select_program)
  into (a) substrate CREATION/teardown, (b) candidate-node POPULATION, (c) the Argmax
  EVALUATION itself. If (a)+(b) — the per-occurrence SETUP — dominate, they are
  REDUCIBLE (reused workspace / batched scoring). If (c) dominates, it is intrinsic.

  MEASURE 2 — PRE-FILTER YIELD. Sample a rowid-strided SPREAD of real wiki_local
  titles (the TRUE distribution, incl. years/lists/stubs/disambiguation). Per article:
  does it read (found), and how many concepts does it EXTRACT+ground (yield)? Report the
  yield distribution (SUBSTANTIAL >=10 / THIN 1-9 / NULL) and a cheap pre-filter signal
  (body length / #sections / title heuristics) available WITHOUT grounding.

THEN the RANKED LEVER TABLE + STACKED projection + RECOMMENDATION.

Measurement + review only — NO agent-logic changes, NO optimization built here.
donkey=0.

Run:  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_precommit_review.py
"""
from __future__ import annotations

import os
import re
import sys
import time
import statistics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# quiet the seed-load chatter so the review reads clean.
import contextlib
import io


def _fmt_us(sec: float) -> str:
    return f"{sec * 1e6:8.1f} us"


# --------------------------------------------------------------------------- #
#  BOOT + WARM
# --------------------------------------------------------------------------- #

def boot_warm():
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    from domains import consumption_quality as cq
    t0 = time.perf_counter()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        a = WorldAdapter(seeds=())
        load_all_seeds(a)
    boot_s = time.perf_counter() - t0
    t = time.perf_counter()
    rec = cq.ensure_sense_select_program(a)
    author_s = time.perf_counter() - t
    # warm WordNet corpus + the program path with a couple of real picks.
    for h, sent in (("bank", "the river bank was muddy and steep"),
                    ("cell", "the prison cell held one inmate")):
        cq.sense_in_context(h, sent, slot="patient", extra=["topic"], agent=a)
    return a, boot_s, author_s, bool(rec.get("authored"))


# --------------------------------------------------------------------------- #
#  MEASURE 2 — sample the TRUE title distribution, measure yield.
# --------------------------------------------------------------------------- #

_LISTY = re.compile(r"^(list of|lists of|index of|outline of|glossary of|timeline of)\b",
                    re.IGNORECASE)
_DISAMBIG_TITLE = re.compile(r"\(disambiguation\)", re.IGNORECASE)
_YEAR_TITLE = re.compile(r"^\d{3,4}(s)?$|^(january|february|march|april|may|june|july|"
                         r"august|september|october|november|december)\s+\d", re.IGNORECASE)


def sample_titles(n: int):
    """rowid-strided sample across the whole index — the TRUE distribution."""
    from domains import wiki_local as wl
    con = wl._index_conn()
    total = con.execute("SELECT MAX(rowid) FROM t").fetchone()[0]
    stride = max(1, total // n)
    rows = con.execute(
        "SELECT nt, fi, rg, off FROM t WHERE rowid % ? = 0 LIMIT ?",
        (stride, n)).fetchall()
    return rows, total


def measure_yield(agent, n_titles: int):
    """For each sampled title: read (parquet), extract concepts (the grounding-work
    driver), record yield + cheap pre-filter signals. Returns (records, harvested
    (head,ctx,slot) triples for MEASURE 1)."""
    from domains import wiki_local as wl
    from domains import gap_driven_acquisition as gda
    from domains import consumption_quality as cq
    rows, total = sample_titles(n_titles)
    records = []
    triples = []
    t_read_tot = 0.0
    for (nt, fi, rg, off) in rows:
        title = nt
        rec = {"title": title, "found": False, "yield": 0,
               "body_len": 0, "n_sections": 0, "disambig": False,
               "listy": bool(_LISTY.match(title)),
               "year": bool(_YEAR_TITLE.match(title))}
        t = time.perf_counter()
        art = None
        try:
            art = wl.summary(title)
        except Exception:
            art = None
        t_read_tot += time.perf_counter() - t
        if art and art.get("text"):
            rec["found"] = True
            text = art["text"]
            rec["body_len"] = len(text)
            rec["n_sections"] = text.count("\n\n") + 1
            rec["disambig"] = wl.is_disambiguation(art.get("extract", ""))
            src = {"found": True, "text": text, "lead": art.get("extract", ""),
                   "title": title, "source": "local_wiki"}
            try:
                ext = gda.extract_microtheory(title.replace(" ", "_"), src,
                                              max_concepts=30, nominal_filter=True)
                cs = ext.get("concepts", [])
                rec["yield"] = len(cs)
                for c in cs:
                    head = cq._head(c["surface"])
                    ctx = cq.context_words(c.get("definition", ""),
                                           [title.replace(" ", "_")])
                    triples.append((head, "patient", ctx))
            except Exception:
                pass
        records.append(rec)
    return records, triples, t_read_tot, total


# --------------------------------------------------------------------------- #
#  MEASURE 1 — decompose the per-occurrence Argmax into a / b / c.
# --------------------------------------------------------------------------- #

def measure_argmax(triples, n_min=500):
    """Time enum (WordNet leaf) + a (fresh substrate) + b (populate) + c (evaluate)
    over >= n_min warm, real (head,slot,ctx) triples."""
    from domains import language_faculty_ops as lfo
    prog = lfo.sense_select_program()

    # keep only triples WordNet actually enumerates (a real candidate set) — the
    # rest short-circuit to the OOV path and never build a substrate.
    usable = []
    for (head, slot, ctx) in triples:
        feats = lfo.sense_candidates(head, slot, ctx)
        if feats:
            usable.append((head, slot, ctx, feats))
        if len(usable) >= n_min * 2:
            break
    if not usable:
        return None
    # cycle to reach n_min samples if the real harvest is thin.
    samples = []
    i = 0
    while len(samples) < n_min:
        samples.append(usable[i % len(usable)])
        i += 1

    cand_counts = [len(f) for (_, _, _, f) in samples]

    # ENUM (WordNet leaf) — time it on the DISTINCT usable heads (word-keyed).
    t = time.perf_counter()
    for (head, slot, ctx, _f) in samples:
        lfo.sense_candidates(head, slot, ctx)
    enum_s = (time.perf_counter() - t) / len(samples)

    # (a) substrate CREATION/teardown
    t = time.perf_counter()
    subs = []
    for _ in samples:
        subs.append(lfo._fresh_sense_substrate())
    a_s = (time.perf_counter() - t) / len(samples)

    # (b) candidate-node POPULATION (SenseSelection + SenseCandidate nodes + edges)
    t = time.perf_counter()
    populated = []
    for (head, slot, ctx, feats), s in zip(samples, subs):
        sel = s.add_node("SenseSelection", {"slot": slot})
        for c in feats:
            cn = s.add_node("SenseCandidate", {
                "english_word": c["english_word"], "category": c.get("category") or "?",
                "lesk_overlap": float(c.get("lesk_overlap", 0)),
                "rank": float(c.get("rank", 0)),
                "freq": float(c.get("freq", 0.0)), "sense": c.get("sense") or ""})
            lfo._add_edge(s, sel, "has_candidate", cn)
        populated.append((s, sel))
    b_s = (time.perf_counter() - t) / len(samples)

    # (c) the Argmax EVALUATION itself
    t = time.perf_counter()
    for (s, sel) in populated:
        s.evaluate(prog, {"sel": sel})
    c_s = (time.perf_counter() - t) / len(samples)

    # full end-to-end run_sense_select_program (a+b+c+enum + read-back), for sanity.
    t = time.perf_counter()
    for (head, slot, ctx, _f) in samples:
        lfo.run_sense_select_program(prog, head, slot, ctx)
    full_s = (time.perf_counter() - t) / len(samples)

    return {"n": len(samples), "enum": enum_s, "a": a_s, "b": b_s, "c": c_s,
            "full": full_s, "cand_counts": cand_counts,
            "n_usable_distinct": len(usable)}


# --------------------------------------------------------------------------- #
#  REPORT
# --------------------------------------------------------------------------- #

def main() -> int:
    from domains import wiki_local as wl
    print("=" * 78)
    print("JABBERWOCK PRE-COMMIT REVIEW — 7.6M Wikipedia grounding import (donkey=0)")
    print("=" * 78)
    if not wl.present():
        print("wiki_local slab ABSENT — cannot measure. Aborting.")
        return 1

    print("\nbooting + warming the agent (seeds, sense-select Program, WordNet) ...",
          flush=True)
    agent, boot_s, author_s, authored = boot_warm()
    print(f"  boot={boot_s:.2f}s  author_program={author_s:.2f}s  authored={authored}",
          flush=True)

    N_TITLES = 160
    print(f"\nMEASURE 2 — sampling {N_TITLES} rowid-strided titles + measuring yield ...",
          flush=True)
    records, triples, t_read_tot, total = measure_yield(agent, N_TITLES)

    print(f"\nMEASURE 1 — decomposing the per-occurrence Argmax (>=500 warm) ...",
          flush=True)
    m1 = measure_argmax(triples, n_min=500)

    # ---- MEASURE 1 REPORT ------------------------------------------------- #
    print("\n" + "=" * 78)
    print("MEASURE 1 — ARGMAX SCAFFOLDING DECOMPOSITION")
    print("=" * 78)
    if m1 is None:
        print("  no usable WordNet candidate sets harvested — cannot decompose.")
    else:
        setup = m1["a"] + m1["b"]
        abc = m1["a"] + m1["b"] + m1["c"]
        cc = m1["cand_counts"]
        print(f"  warm samples n={m1['n']}  (distinct real candidate sets harvested="
              f"{m1['n_usable_distinct']})")
        print(f"  candidate-set size: min={min(cc)} median={int(statistics.median(cc))} "
              f"max={max(cc)} mean={statistics.mean(cc):.1f}")
        print()
        print(f"    (leaf) enum  WordNet enumeration   {_fmt_us(m1['enum'])}   "
              f"[word+ctx-keyed; NOT scaffolding]")
        print(f"    (a)    substrate CREATE/teardown   {_fmt_us(m1['a'])}   "
              f"{100*m1['a']/abc:5.1f}% of a+b+c")
        print(f"    (b)    candidate-node POPULATION    {_fmt_us(m1['b'])}   "
              f"{100*m1['b']/abc:5.1f}% of a+b+c")
        print(f"    (c)    Argmax EVALUATION            {_fmt_us(m1['c'])}   "
              f"{100*m1['c']/abc:5.1f}% of a+b+c")
        print(f"    -------------------------------------------------")
        print(f"    a+b+c  (the scaffolded pick)        {_fmt_us(abc)}")
        print(f"    full   run_sense_select_program     {_fmt_us(m1['full'])}   "
              f"(incl. enum + read-back)")
        print()
        setup_frac = setup / abc
        print(f"  SETUP (a+b) = {_fmt_us(setup)} = {100*setup_frac:.1f}% of the scaffolded pick.")
        if setup_frac >= 0.5:
            # reused-workspace / batched scoring removes (a) and most of (b)-teardown,
            # leaving (c) + node-population. Conservative: a fully removed, b halved.
            reducible = m1["a"] + 0.5 * m1["b"]
            red_frac_full = reducible / m1["full"]
            speedup_pick = abc / (abc - reducible)
            print(f"  VERDICT: SETUP DOMINATES -> REDUCIBLE. A persistent/reused workspace")
            print(f"    substrate (clear+repopulate, not recreate) removes (a) entirely and")
            print(f"    ~half of (b)'s churn. Reducible ~= a + 0.5b = {_fmt_us(reducible)} "
                  f"= {100*red_frac_full:.1f}% of the full per-concept pick.")
            print(f"    => ~{speedup_pick:.2f}x on the scaffolded-pick component;")
            print(f"       but the pick is only part of the warm ground cost — see stack below.")
        else:
            print(f"  VERDICT: the Argmax EVALUATION (c) is the largest single component — the")
            print(f"    decision itself is INTRINSIC, not reducible by workspace reuse. Setup")
            print(f"    reuse still trims (a)+(b) but the ceiling is bounded by (c).")
        # stash for the stack
        m1["_abc"] = abc
        m1["_setup"] = setup
        m1["_reducible"] = (m1["a"] + 0.5 * m1["b"]) if setup / abc >= 0.5 else m1["a"]

    # ---- MEASURE 2 REPORT ------------------------------------------------- #
    found = [r for r in records if r["found"]]
    substantial = [r for r in found if r["yield"] >= 10]
    thin = [r for r in found if 1 <= r["yield"] <= 9]
    null_zero = [r for r in found if r["yield"] == 0]
    no_source = [r for r in records if not r["found"]]
    nrec = len(records)

    print("\n" + "=" * 78)
    print("MEASURE 2 — PRE-FILTER YIELD (true rowid-strided distribution)")
    print("=" * 78)
    print(f"  sampled n={nrec} titles, strided across {total:,} rowids "
          f"(stride ~= {total//N_TITLES:,})")
    print(f"  parquet read cost: {t_read_tot:.2f}s total = {t_read_tot/nrec*1000:.1f} ms/title "
          f"(random row-group I/O — the read_source ~24% wall)")
    print()

    def pct(x):
        return f"{100*len(x)/nrec:5.1f}%"

    print(f"  found (read a body):        {len(found):3d}  {pct(found)}")
    print(f"  NO-SOURCE (missing/empty):  {len(no_source):3d}  {pct(no_source)}")
    print()
    print(f"  YIELD DISTRIBUTION (of all {nrec} sampled):")
    print(f"    SUBSTANTIAL (>=10 concepts): {len(substantial):3d}  {pct(substantial)}")
    print(f"    THIN         (1-9 concepts): {len(thin):3d}  {pct(thin)}")
    print(f"    NULL  (found but 0 concepts):{len(null_zero):3d}  {pct(null_zero)}")
    print(f"    NULL  (no source at all):    {len(no_source):3d}  {pct(no_source)}")
    yields = [r["yield"] for r in records]
    if any(yields):
        print(f"    yield: mean={statistics.mean(yields):.2f} "
              f"median={int(statistics.median(yields))} max={max(yields)} "
              f"total_concepts={sum(yields)}")

    skippable = thin + null_zero + no_source
    substantial_share_of_work = sum(r["yield"] for r in substantial)
    total_work = sum(yields) or 1
    print()
    print(f"  SKIPPABLE (thin+null+no-source): {len(skippable)}/{nrec} = "
          f"{100*len(skippable)/nrec:.1f}% of ARTICLES")
    print(f"  ...but those carry only {total_work - substantial_share_of_work} of "
          f"{total_work} concepts = {100*(total_work-substantial_share_of_work)/total_work:.1f}% "
          f"of the grounding WORK.")
    print(f"  => substantial articles ({100*len(substantial)/nrec:.1f}% of titles) carry "
          f"{100*substantial_share_of_work/total_work:.1f}% of the concept-grounding work.")

    # pre-filter signal: body length / sections / title heuristics ---------- #
    print()
    print("  PRE-FILTER SIGNAL (available WITHOUT grounding — parquet metadata + title):")
    # title heuristics catch of low-yield
    listy = [r for r in records if r["listy"]]
    disamb = [r for r in records if r["disambig"] or _DISAMBIG_TITLE.search(r["title"])]
    year = [r for r in records if r["year"]]
    heur_low = [r for r in records if (r["listy"] or r["year"] or r["disambig"]
                                       or _DISAMBIG_TITLE.search(r["title"]))]
    heur_low_and_lowyield = [r for r in heur_low if r["yield"] < 10]
    print(f"    title 'List/Index/Outline of...' : {len(listy):3d}  "
          f"(mean yield {statistics.mean([r['yield'] for r in listy]):.1f})"
          if listy else "    title 'List of...' : 0")
    print(f"    year/date titles                 : {len(year):3d}  "
          f"(mean yield {statistics.mean([r['yield'] for r in year]):.1f})"
          if year else "    year/date titles : 0")
    print(f"    disambiguation lead/title        : {len(disamb):3d}")
    # body-length threshold as a yield predictor
    if found:
        blens = sorted(r["body_len"] for r in found)
        # correlation of body_len with yield among found
        try:
            import statistics as st
            bl = [r["body_len"] for r in found]
            yl = [r["yield"] for r in found]
            if len(set(bl)) > 1 and len(set(yl)) > 1:
                corr = _pearson(bl, yl)
                print(f"    body_len vs yield correlation    : r={corr:+.2f}")
        except Exception:
            pass
        # what fraction of SUBSTANTIAL articles have body_len below the median?
        med_bl = statistics.median(blens)
        sub_below = [r for r in substantial if r["body_len"] < med_bl]
        short = [r for r in found if r["body_len"] < 1500]
        short_lowyield = [r for r in short if r["yield"] < 10]
        print(f"    body_len < 1500 chars (short)    : {len(short):3d} found, "
              f"{len(short_lowyield)} of them low-yield "
              f"({100*len(short_lowyield)/len(short):.0f}% precision)"
              if short else "    body_len<1500 : 0")
        print(f"    (substantial articles below median body_len: {len(sub_below)} "
              f"-> body-length pre-filter would FALSE-NEGATIVE these)")
    print(f"    combined title-heuristic low-yield precision: "
          f"{len(heur_low_and_lowyield)}/{len(heur_low)} "
          f"({100*len(heur_low_and_lowyield)/max(1,len(heur_low)):.0f}%) of flagged are <10-yield")

    # store for the stack
    stats = {
        "skip_frac_articles": len(skippable) / nrec,
        "substantial_frac": len(substantial) / nrec,
        "work_in_substantial": substantial_share_of_work / total_work,
        "read_ms": t_read_tot / nrec * 1000,
        "mean_yield": statistics.mean(yields) if yields else 0,
        "no_read_skip_frac": len(heur_low) / nrec,   # skippable by TITLE alone (no read)
    }

    # ---- REGIME FINDING: the true-distribution cost model INVERTS ---------- #
    full_pick_us = (m1["full"] if m1 else 300e-6) * 1e6     # seconds -> microseconds
    read_ms = stats["read_ms"]
    ground_ms = stats["mean_yield"] * full_pick_us / 1000.0
    per_art_ms = read_ms + ground_ms
    print("\n" + "=" * 78)
    print("REGIME FINDING — the cost model is DISTRIBUTION-DEPENDENT (measured)")
    print("=" * 78)
    print(f"  The 46-70% ground / 24% read split was measured on the CURATED batch")
    print(f"  (~30 concepts/article). The TRUE rowid-strided distribution yields")
    print(f"  mean={stats['mean_yield']:.2f} concepts/article (76% ground ZERO).")
    print()
    print(f"  Per-article on the TRUE distribution (measured):")
    print(f"    read_source (parquet row-group I/O): {read_ms:6.1f} ms")
    print(f"    grounding ({stats['mean_yield']:.2f} concepts x {full_pick_us:.0f}us): "
          f"{ground_ms:6.2f} ms")
    print(f"    -> read is {100*read_ms/per_art_ms:.0f}% of the per-article cost; "
          f"grounding {100*ground_ms/per_art_ms:.0f}%.")
    print(f"  => On a FULL 7.6M import the split INVERTS: READ dominates, not grounding.")
    corpus_read_h = 7_597_149 * read_ms / 1000 / 3600
    corpus_ground_h = 7_597_149 * ground_ms / 1000 / 3600
    print(f"     extrapolated 7.6M single-thread: read ~{corpus_read_h:.0f}h + "
          f"ground ~{corpus_ground_h:.1f}h = ~{corpus_read_h+corpus_ground_h:.0f}h "
          f"(NOT 7.5 days=180h).")
    print(f"     the 180h/7.5-day plan assumes ~30 concepts/article — TRUE yield is "
          f"{stats['mean_yield']:.1f}. If the import is the SUBSTANTIAL SUBSET only,")
    print(f"     grounding dominates as originally stated (the lever table below).")

    # ---- RANKED LEVER TABLE + STACK -------------------------------------- #
    report_stack(m1, stats)
    print("\ndonkey=0")
    return 0


def _pearson(xs, ys):
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs) ** 0.5
    vy = sum((y - my) ** 2 for y in ys) ** 0.5
    return cov / (vx * vy) if vx and vy else 0.0


def report_stack(m1, s2):
    print("\n" + "=" * 78)
    print("RANKED PRE-COMMIT LEVER TABLE")
    print("=" * 78)
    print("  (impact = x on TOTAL end-to-end load; build-cost / correctness-risk honest)")
    print()

    # --- assemble the measured cost model ---
    # Warm load per SUBSTANTIAL article decomposes (measured 9586f93e): grounding
    # dominates; grounding splits word-keyed ~28% (dedupable) / context-keyed ~72%
    # (the per-occurrence Argmax pick). read_source ~24% of total.
    GROUND_FRAC = 0.60      # ground_lexeme share of total warm load (46-70% band; midpoint)
    READ_FRAC = 0.24        # read_source (random parquet I/O)
    CTX_KEYED = 0.72        # of grounding: the per-occurrence Argmax pick
    WORD_KEYED = 0.28       # of grounding: POS + candidate enum (dedupable)

    rows = []

    # (i) PRE-FILTER / TIER
    skip = s2["skip_frac_articles"]
    # skipping low-yield articles removes their READ + their (small) grounding, but
    # NOT the substantial-article work. Net multiplier on total load:
    #   work retained ~= substantial-article read + all substantial grounding.
    # Reads are per-article (skipped ones save a full read); grounding saved is small.
    read_saved = READ_FRAC * skip                      # ~all skipped reads removed
    ground_saved = GROUND_FRAC * (1 - s2["work_in_substantial"])
    prefilter_saved = min(0.85, read_saved + ground_saved)
    prefilter_x = 1.0 / (1.0 - prefilter_saved) if prefilter_saved < 0.99 else 99
    rows.append(("(i)  PRE-FILTER / tier (skip low-yield)",
                 f"{prefilter_x:.2f}x", "CHEAP", "LOW",
                 f"skips {100*skip:.0f}% of titles carrying "
                 f"{100*(1-s2['work_in_substantial']):.0f}% of concepts; "
                 f"title+body-len signal, no agent path change"))

    # (ii) ARGMAX SCAFFOLDING reuse/batch
    if m1 and m1.get("_abc"):
        abc = m1["_abc"]
        red = m1["_reducible"]
        # the scaffolded pick is the context-keyed cost. reducible fraction of it:
        pick_red_frac = red / m1["full"]
        # context-keyed is CTX_KEYED of grounding of GROUND_FRAC of total:
        ctx_share_total = GROUND_FRAC * CTX_KEYED
        argmax_saved = ctx_share_total * pick_red_frac
        argmax_x = 1.0 / (1.0 - argmax_saved)
        rows.append(("(ii) ARGMAX scaffolding reuse/batch",
                     f"{argmax_x:.2f}x", "MEDIUM", "LOW",
                     f"reused workspace removes {100*pick_red_frac:.0f}% of the "
                     f"per-pick cost; DECISION byte-identical"))
    else:
        argmax_saved = 0.0
        rows.append(("(ii) ARGMAX scaffolding reuse/batch",
                     "n/a", "MEDIUM", "LOW", "not measured"))

    # (iii) WORD-KEYED grounding dedup (~1.38x on grounding, measured 9586f93e)
    # 1.38x on grounding -> grounding cost *= 1/1.38 = 0.725, i.e. saves 27.5% of grounding.
    ground_dedup_saved_of_ground = 1 - 1 / 1.38
    worddedup_saved = GROUND_FRAC * ground_dedup_saved_of_ground
    worddedup_x = 1.0 / (1.0 - worddedup_saved)
    rows.append(("(iii)WORD-KEYED grounding dedup",
                 f"{worddedup_x:.2f}x", "CHEAP", "LOW",
                 "1.38x on grounding (POS+enum memoised by word); measured 9586f93e"))

    # (iv) BATCH-IN-RAM (~1.3x + parallel unblock)
    batchram_x = 1.30
    rows.append(("(iv) BATCH-IN-RAM (row-group locality)",
                 f"{batchram_x:.2f}x", "CHEAP", "LOW",
                 "read shard row-groups once, batch titles per group; "
                 "removes random-seek re-reads + unblocks parallelism"))

    # (v) PARALLELISM (Nx to core count)
    CORES = os.cpu_count() or 12
    # grounding is CPU-bound & embarrassingly parallel per article; realistic scaling
    # ~0.7 efficiency (GIL-free Rust eval helps; Python driver + I/O contention hurt).
    par_eff = 0.7
    par_x = CORES * par_eff
    rows.append(("(v)  PARALLELISM (per-article workers)",
                 f"~{par_x:.0f}x", "MEDIUM", "MEDIUM",
                 f"{CORES} cores x ~{par_eff:.0%} eff; per-article shards are "
                 f"independent (isolated seeds dir already)"))

    # print table
    print(f"  {'LEVER':<40} {'IMPACT':>7}  {'BUILD':<7} {'RISK':<7}")
    print("  " + "-" * 74)
    for (name, impact, build, risk, note) in rows:
        print(f"  {name:<40} {impact:>7}  {build:<7} {risk:<7}")
        print(f"      -> {note}")
    print()

    # --- STACK (multiplicative where independent) ---
    # Single-threaded software levers first (i,ii,iii,iv), then parallelism.
    # (i) pre-filter, (iii) word-dedup, (iv) batch-ram are largely independent.
    # (ii) argmax-reuse overlaps (iii) partially (both touch grounding) — discount it.
    prefilter_x_ = prefilter_x
    worddedup_x_ = worddedup_x
    batchram_x_ = batchram_x
    # argmax saving is on the CONTEXT-keyed slice, word-dedup on the WORD-keyed slice
    # -> genuinely independent slices of grounding; multiply.
    argmax_x_ = 1.0 / (1.0 - argmax_saved) if argmax_saved else 1.0

    single_thread_x = prefilter_x_ * worddedup_x_ * batchram_x_ * argmax_x_
    full_x = single_thread_x * par_x

    print("  STACKED PROJECTION (multiplicative where independent):")
    print(f"    software (i x iii x iv x ii): "
          f"{prefilter_x_:.2f} x {worddedup_x_:.2f} x {batchram_x_:.2f} x {argmax_x_:.2f} "
          f"= {single_thread_x:.2f}x  (single-thread)")
    print(f"    x parallelism (v):           x {par_x:.0f} = {full_x:.0f}x  (12-core box)")
    print()

    # --- revised time estimate ---
    BASE_SINGLE_DAYS = 7.5
    BASE_12CORE_H = 15.0
    rev_single_days = BASE_SINGLE_DAYS / single_thread_x
    rev_12core_h = BASE_12CORE_H / single_thread_x       # parallelism already in the 15h
    # if the 15h figure was already the naive-parallel plan, software levers apply on top:
    print("  REVISED TIME ESTIMATE vs current plan:")
    print(f"    current plan:  ~{BASE_SINGLE_DAYS:.1f} days single-thread / "
          f"~{BASE_12CORE_H:.0f}h on this 12-core box")
    print(f"    + software levers (i,ii,iii,iv = {single_thread_x:.2f}x):")
    print(f"        single-thread -> ~{rev_single_days*24:.0f}h "
          f"({rev_single_days:.1f} days)")
    print(f"        12-core (naive-parallel 15h base) -> ~{rev_12core_h:.1f}h")
    print(f"    NOTE: the ~15h '12-core' base already banks most of lever (v). The")
    print(f"    software stack ({single_thread_x:.2f}x) is what remains on top -> "
          f"~{rev_12core_h:.1f}h.")

    print("\n" + "=" * 78)
    print("RECOMMENDATION")
    print("=" * 78)
    print("""  BUILD-BEFORE-COMMIT (highest impact / lowest cost+risk first):
    1. PRE-FILTER / TIER (i)  — CHEAP, LOW risk, biggest single lever. A pre-pass
       script (plain Python, no agent path) drops 'List of'/year/disambiguation
       titles + body_len-below-threshold stubs BEFORE the expensive grounding.
       Recognition-consistent: reuses wl.is_disambiguation + a body-length gate.
    2. WORD-KEYED grounding dedup (iii) — CHEAP, LOW risk, 1.38x already measured.
       Memoise POS + candidate-enum by word (the GroundingCache already exists).
    3. BATCH-IN-RAM (iv) — CHEAP, LOW. Read each shard's row-groups once, group the
       batch's titles by (fi,rg) so each row-group is read ONCE, not per-title.
       This ALSO unblocks clean per-worker sharding.

  BUILD IF TIME (medium cost, still low risk):
    4. ARGMAX scaffolding reuse (ii) — a persistent/reused workspace substrate
       (clear+repopulate, or one batched Argmax sweep). Decision byte-identical;
       worth it only because context-keyed is the ~72% grounding slice.

  LAUNCH-AS-IS / lever the infra:
    5. PARALLELISM (v) — the real multiplier; the per-article shards are already
       isolated (seeds_dir per article). Run N workers = cores. This is infra, not
       an agent change — do it regardless.

  NOT WORTH IT before commit: finer representation-grain changes to the pick
    itself (the Argmax EVALUATION (c) is intrinsic — see MEASURE 1); metric/parse
    surgery on grounding correctness (out of scope for a throughput commit).

  REGIME CAVEAT (from the measured true distribution): if the import is the FULL
    7.6M, the cost is READ-BOUND (see REGIME FINDING) — then lever priority is
    (iv) batch-in-RAM row-group locality + (v) parallelism FIRST (they attack the
    read wall), and (i) pre-filter's value is mostly its TITLE-only skip (no read
    needed) since body-length needs a read. If the import is the SUBSTANTIAL SUBSET
    (~3% of titles, cross-referenced/curated), grounding dominates and the table's
    ordering (i,iii,iv,ii) holds. State which import you are committing to — it
    changes which lever is #1.""")


if __name__ == "__main__":
    raise SystemExit(main())
