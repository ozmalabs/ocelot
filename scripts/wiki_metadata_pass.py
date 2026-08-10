"""Wiki metadata pass — READ-ONLY MEASUREMENT for the import cost model.

Sequentially scans the structured-wikipedia enwiki parquet shards reading only
the title + abstract + sections columns, computes per-article body_len /
n_sections / title flags, reports the body_len histogram + tier
counts/fractions, calibrates a body_len threshold against the grounding concept
YIELD (extract_microtheory) on a stratified sub-sample, and prints the revised
two-regime (read-bound full vs substantial-subset) time tables.

NO grounding of the corpus, NO agent logic, NO Rust/seed changes. Plain
pyarrow measurement. Usage:

  python3 scripts/wiki_metadata_pass.py                # full 7.6M pass
  python3 scripts/wiki_metadata_pass.py --stride 30    # strided sample
  python3 scripts/wiki_metadata_pass.py --calib 250    # calibration sample size
"""
from __future__ import annotations

import argparse
import glob
import math
import os
import random
import re
import time

import pyarrow.parquet as pq

import domains.wiki_local as wl
import domains.gap_driven_acquisition as gda

DATA = "data/wiki/structured/enwiki/data"

# body_len histogram bucket upper bounds (chars of parsed text).
BUCKETS = [0, 1, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000, 10**9]
BUCKET_LABELS = [
    "0 (null)", "1-199", "200-499", "500-999", "1k-2k", "2k-5k",
    "5k-10k", "10k-20k", "20k-50k", "50k+",
]

_YEAR_PAREN = re.compile(r"\(\d{4}\)")
_BARE_YEAR = re.compile(r"^\d{3,4}$")
_LIST_PREFIX = re.compile(r"^(List of|Index of|Outline of|Lists of)\b", re.I)

# calibration: SUBSTANTIAL := grounding concept yield >= this.
SUBSTANTIAL_YIELD = 10


def bucket_of(n: int) -> int:
    for i in range(len(BUCKETS) - 1):
        lo, hi = BUCKETS[i], BUCKETS[i + 1]
        if i == 0 and n == 0:
            return 0
        if lo <= n < hi:
            return i
    return len(BUCKET_LABELS) - 1


def title_flags(name: str) -> tuple:
    nm = name or ""
    is_list = bool(_LIST_PREFIX.match(nm))
    is_year = bool(_BARE_YEAR.match(nm.strip())) or bool(_YEAR_PAREN.search(nm))
    return is_list, is_year


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stride", type=int, default=1,
                    help="row-group stride (1 = full pass)")
    ap.add_argument("--calib", type=int, default=250,
                    help="calibration sub-sample target size")
    ap.add_argument("--per-bucket", type=int, default=30,
                    help="max calibration texts kept per body_len bucket")
    args = ap.parse_args()

    files = sorted(glob.glob(f"{DATA}/*.parquet"))
    assert files, f"no shards under {DATA}"

    # footer-only total (cheap, exact).
    total_rows = 0
    total_rg = 0
    total_bytes = 0
    for f in files:
        md = pq.ParquetFile(f).metadata
        total_rows += md.num_rows
        total_rg += md.num_row_groups
        total_bytes += os.path.getsize(f)

    hist = [0] * len(BUCKET_LABELS)
    n_sections_sum = 0
    n_list = n_year = n_disambig = 0
    seen = 0
    # stratified RANDOM reservoir for calibration: up to per-bucket texts/bucket,
    # sampled uniformly across the WHOLE corpus (reservoir sampling) so the
    # calibration set is not biased to the first shards.
    rng = random.Random(1234)
    calib = {i: [] for i in range(len(BUCKET_LABELS))}
    calib_seen = [0] * len(BUCKET_LABELS)

    t0 = time.time()
    rg_read = 0
    for path in files:
        pf = pq.ParquetFile(path)
        for rg in range(pf.num_row_groups):
            if args.stride > 1 and (rg_read % args.stride) != 0:
                rg_read += 1
                continue
            rg_read += 1
            tb = pf.read_row_group(rg, columns=["name", "abstract", "sections"])
            names = tb.column("name").to_pylist()
            absts = tb.column("abstract").to_pylist()
            secs = tb.column("sections").to_pylist()
            for i in range(tb.num_rows):
                abst = absts[i] or ""
                body = wl._section_text(secs[i])
                text = (abst + ("\n\n" + body if body else "")).strip()
                blen = len(text)
                nsec = (body.count("\n\n") + 1) if body else 0
                b = bucket_of(blen)
                hist[b] += 1
                n_sections_sum += nsec
                seen += 1
                il, iy = title_flags(names[i])
                n_list += il
                n_year += iy
                if wl.is_disambiguation(abst):
                    n_disambig += 1
                calib_seen[b] += 1
                if len(calib[b]) < args.per_bucket:
                    calib[b].append((names[i], abst, text, blen, nsec))
                else:
                    j = rng.randint(0, calib_seen[b] - 1)
                    if j < args.per_bucket:
                        calib[b][j] = (names[i], abst, text, blen, nsec)
    wall = time.time() - t0

    # bytes actually swept (proportional to row groups read).
    swept_bytes = total_bytes * (rg_read_actual := _rg_actual(files, args.stride)) / total_rg \
        if args.stride > 1 else total_bytes
    mb_s = (swept_bytes / 1e6) / wall if wall else 0
    art_s = seen / wall if wall else 0

    full = args.stride == 1

    print("=" * 70)
    print("WIKI METADATA PASS  (read-only measurement)")
    print("=" * 70)
    print(f"corpus: {total_rows:,} rows | {total_rg:,} row-groups | "
          f"{total_bytes/1e9:.2f} GB parquet | {len(files)} shards")
    if full:
        print(f"COVERAGE: FULL PASS  ({seen:,} articles read)")
    else:
        print(f"COVERAGE: STRIDED SAMPLE  stride={args.stride}  "
              f"n={seen:,} articles ({100*seen/total_rows:.1f}% of corpus)")
    print(f"WALL-CLOCK: {wall:.1f}s  ({wall/60:.2f} min)")
    print(f"SEQUENTIAL SCAN RATE: {mb_s:.1f} MB/s | {art_s:,.0f} articles/s")
    print()

    # --- histogram ---
    print("BODY_LEN HISTOGRAM (chars of parsed abstract+body text)")
    for i, lab in enumerate(BUCKET_LABELS):
        frac = hist[i] / seen if seen else 0
        ext = round(frac * total_rows)
        bar = "#" * int(frac * 50)
        print(f"  {lab:>10} : {hist[i]:>9,}  {frac*100:5.1f}%  "
              f"~{ext:>11,}  {bar}")
    print(f"  mean n_sections/article: {n_sections_sum/seen:.2f}")
    print(f"  title 'List/Index/Outline of': {n_list:,} "
          f"({100*n_list/seen:.1f}%)  ~{round(n_list/seen*total_rows):,}")
    print(f"  title bare-year / (YYYY):      {n_year:,} "
          f"({100*n_year/seen:.1f}%)  ~{round(n_year/seen*total_rows):,}")
    print(f"  disambiguation lead:           {n_disambig:,} "
          f"({100*n_disambig/seen:.1f}%)  ~{round(n_disambig/seen*total_rows):,}")
    print()

    # --- calibration: fit body_len threshold vs grounding yield ---
    sample = []
    for b in calib:
        for (name, abst, text, blen, nsec) in calib[b]:
            src = {"text": text, "lead": abst, "title": name,
                   "source": "local_wiki"}
            dom = wl._norm(name)
            gt0 = time.time()
            ex = gda.extract_microtheory(dom, src)
            gt = time.time() - gt0
            yld = len(ex["concepts"])
            sample.append((blen, nsec, yld, gt))
    n_cal = len(sample)
    ground_ms = 1000 * sum(s[3] for s in sample) / n_cal if n_cal else 0

    print("THRESHOLD CALIBRATION  (extract_microtheory concept yield)")
    print(f"  calibration sample: n={n_cal} articles (stratified across body_len")
    print(f"    buckets -> range coverage; NOT corpus base rate)")
    print(f"  extract_microtheory cost: {ground_ms:.1f} ms/article "
          f"(regex enumeration parse; NOT full teach)")
    print()
    # yield distribution on the stratified sample.
    ybins = [(0, 0), (1, 2), (3, 4), (5, 9), (10, 19), (20, 10**9)]
    ylab = ["0", "1-2", "3-4", "5-9", "10-19", "20+"]
    print("  concept-yield distribution (stratified sample):")
    for (lo, hi), lab in zip(ybins, ylab):
        c = sum(1 for s in sample if lo <= s[2] <= hi)
        print(f"    yield {lab:>6}: {c:>4} ({100*c/n_cal:4.1f}%)")
    n_subst = sum(1 for s in sample if s[2] >= SUBSTANTIAL_YIELD)
    print(f"  SUBSTANTIAL := yield >= {SUBSTANTIAL_YIELD}: "
          f"{n_subst}/{n_cal} of sample")
    print()

    # sweep BUCKET-BOUNDARY thresholds so tier extrapolation is EXACT (no straddle).
    cand = [200, 500, 1000, 2000, 5000, 10000, 20000]
    rows_pr = []
    print("  body_len threshold sweep (predict yield >= "
          f"{SUBSTANTIAL_YIELD}):")
    print(f"  {'thr':>7} {'prec':>6} {'rec':>6} {'F1':>6} {'FN':>4} {'FP':>4}")
    for thr in cand:
        tp = fp = fn = 0
        for (blen, nsec, yld, _) in sample:
            pred = blen >= thr
            act = yld >= SUBSTANTIAL_YIELD
            if pred and act:
                tp += 1
            elif pred and not act:
                fp += 1
            elif not pred and act:
                fn += 1
        prec = tp / (tp + fp) if (tp + fp) else 0
        rec = tp / (tp + fn) if (tp + fn) else 0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0
        rows_pr.append((thr, prec, rec, f1, fn, fp))
        print(f"  {thr:>7} {prec:>6.2f} {rec:>6.2f} {f1:>6.2f} {fn:>4} {fp:>4}")
    # n_sections as an alternative predictor.
    print("  n_sections threshold sweep (predict yield >= "
          f"{SUBSTANTIAL_YIELD}):")
    print(f"  {'thr':>7} {'prec':>6} {'rec':>6} {'F1':>6}")
    for thr in (2, 4, 6, 10, 15, 20):
        tp = fp = fn = 0
        for (blen, nsec, yld, _) in sample:
            pred = nsec >= thr
            act = yld >= SUBSTANTIAL_YIELD
            if pred and act:
                tp += 1
            elif pred and not act:
                fp += 1
            elif not pred and act:
                fn += 1
        prec = tp / (tp + fp) if (tp + fp) else 0
        rec = tp / (tp + fn) if (tp + fn) else 0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0
        print(f"  {thr:>7} {prec:>6.2f} {rec:>6.2f} {f1:>6.2f}")
    print()
    # SELECT: the tier BOUNDARY is a safe upper-bound filter — pick the highest
    # threshold that still keeps recall >= 0.90 (misses <=10% of substantial).
    # body_len bounds substantial from below (long is necessary, not sufficient),
    # so precision is inherently capped; we choose for RECALL (don't drop value).
    safe = [r for r in rows_pr if r[2] >= 0.90]
    thr, prec, rec, f1, fn, fp = (safe[-1] if safe else rows_pr[0])
    n_sub_actual = max(1, sum(1 for s in sample if s[2] >= SUBSTANTIAL_YIELD))
    fn_rate = fn / n_sub_actual
    print(f"  SELECTED THRESHOLD (recall>=0.90, safe upper-bound filter): "
          f"body_len >= {thr}")
    print(f"    precision {prec:.2f}  recall {rec:.2f}  F1 {f1:.2f}")
    print(f"    false-negative rate on substantial: {fn_rate:.2f} "
          f"({fn} of {n_sub_actual} missed)")
    print(f"    NOTE: precision is low by construction — body_len is a LOWER")
    print(f"    bound on yield (enumeration-driven), not a tight predictor.")
    print()

    # --- extrapolate tier counts to 7.6M using calibrated threshold ---
    # substantial = body_len >= thr ; thin = 1..thr ; stub/null = 0.
    # thr is a bucket boundary -> exact split, no straddle.
    n_stub = hist[0]
    n_thin = sum(hist[i] for i in range(1, len(BUCKET_LABELS))
                 if BUCKETS[i + 1] <= thr)
    n_subst_meta = sum(hist[i] for i in range(1, len(BUCKET_LABELS))
                       if BUCKETS[i] >= thr)
    scale = total_rows / seen
    print("TIER EXTRAPOLATION to 7,597,149 articles "
          f"(threshold body_len >= {thr})")
    print(f"  {'tier':>12} {'sample':>10} {'frac':>7} {'~7.6M':>13}")
    for lab, c in [("SUBSTANTIAL", n_subst_meta), ("THIN", n_thin),
                   ("STUB/NULL", n_stub)]:
        print(f"  {lab:>12} {c:>10,} {100*c/seen:6.1f}% "
              f"{round(c*scale):>13,}")
    sub_ext = round(n_subst_meta * scale)
    thin_ext = round(n_thin * scale)
    stub_ext = round(n_stub * scale)
    true_sub_ext = round(sub_ext * prec)   # precision-corrected true yield>=10
    print(f"  metadata tier 'body_len>={thr}' is a SAFE SUPERSET (recall {rec:.2f}).")
    print(f"  precision-corrected TRUE substantial (yield>={SUBSTANTIAL_YIELD}): "
          f"~{true_sub_ext:,}  ({prec:.2f} x {sub_ext:,})")
    print()

    # --- REVISED TWO-REGIME TIME TABLES ---
    # mean grounding yield -> teach cost. Task-supplied warm grounding rate.
    WARM_S_PER_DENSE = 0.11        # s/article on a DENSE (~30-concept) article
    DENSE_YIELD = 30.0
    # stratified-sample mean OVER-weights long buckets -> CORPUS-weight it:
    # per-bucket mean yield x that bucket's histogram fraction.
    by_bucket = {i: [] for i in range(len(BUCKET_LABELS))}
    for (blen, nsec, yld, _) in sample:
        by_bucket[bucket_of(blen)].append(yld)
    mean_yield_strat = sum(s[2] for s in sample) / n_cal if n_cal else 0
    mean_yield_corpus = 0.0
    for i in range(len(BUCKET_LABELS)):
        if by_bucket[i]:
            bm = sum(by_bucket[i]) / len(by_bucket[i])
            mean_yield_corpus += bm * (hist[i] / seen)
    mean_yield_all = mean_yield_corpus     # use corpus-representative mean
    # yield on substantial subset only (calibration sample restricted).
    sub_ys = [s[2] for s in sample if s[2] >= SUBSTANTIAL_YIELD]
    mean_yield_sub = sum(sub_ys) / len(sub_ys) if sub_ys else 0
    # scale teach cost linearly by yield/DENSE (grounding work ~ #concepts).
    g_all = WARM_S_PER_DENSE * (mean_yield_all / DENSE_YIELD)
    g_sub = WARM_S_PER_DENSE * (mean_yield_sub / DENSE_YIELD)
    read_s = wall * scale        # sequential read+parse time for full corpus

    print("=" * 70)
    print("REVISED TWO-REGIME TIME ESTIMATES (measured)")
    print("=" * 70)
    print(f"  measured sequential read+parse (full 7.6M): {read_s/3600:.2f} h "
          f"({read_s/60:.0f} min) @ {mb_s:.0f} MB/s")
    print(f"  mean grounding yield: corpus-weighted {mean_yield_corpus:.2f} "
          f"(stratified-sample {mean_yield_strat:.2f}) concepts")
    print(f"  -> full-corpus warm-teach {g_all*1000:.1f} ms/article "
          f"(corpus-weighted yield)")
    print(f"  mean grounding yield (substantial): {mean_yield_sub:.1f} concepts "
          f"-> {g_sub*1000:.0f} ms/article warm-teach")
    print()

    def table(label, n_articles, per_article_ground, read_time_s):
        ground = n_articles * per_article_ground
        print(f"  {label}")
        print(f"    articles grounded: {n_articles:,}")
        print(f"    read (seq)   : {read_time_s/3600:6.2f} h")
        print(f"    grounding    : {ground/3600:6.2f} h  "
              f"(@ {per_article_ground*1000:.0f} ms/article)")
        for w in (1, 8, 12, 16, 32):
            # read+ground both parallelize; single-thread = 1.
            tot = (read_time_s + ground) / w
            tag = " (this box)" if w == 12 else ""
            print(f"    {w:>2}-thread total: {tot/3600:6.2f} h{tag}")
        print()

    print("REGIME A — FULL 7.6M, READ-BOUND (batch-in-RAM sequential):")
    table("all articles (tiny grounding on mean yield):",
          total_rows, g_all, read_s)

    print("REGIME B — SUBSTANTIAL SUBSET (tier to substantial+thin that carry value):")
    # read is still the full sequential sweep (must scan to find them), but
    # grounding only the substantial subset at the substantial warm rate.
    sub_read = read_s   # must sweep corpus to select; report both variants
    table("substantial only (grounded), full sweep to select:",
          sub_ext, g_sub, sub_read)
    print("  variant: substantial+thin grounded (thin cheap, near-zero yield):")
    combined_ground = sub_ext * g_sub + thin_ext * g_all
    print(f"    grounding (subst {g_sub*1000:.0f}ms + thin {g_all*1000:.1f}ms): "
          f"{combined_ground/3600:.2f} h")
    for w in (1, 12):
        print(f"    {w:>2}-thread total (+read): "
              f"{(read_s+combined_ground)/w/3600:.2f} h")
    print()

    # --- crossover ---
    # grounding overtakes reading when n_grounded * g > read_s.
    cross_all = read_s / g_all if g_all else float("inf")
    cross_sub = read_s / g_sub if g_sub else float("inf")
    print("CROSSOVER (grounding time overtakes read time):")
    print(f"  at mean yield ({mean_yield_all:.1f} concepts, {g_all*1000:.1f} ms): "
          f"grounding > reading beyond {cross_all:,.0f} articles "
          f"({100*cross_all/total_rows:.1f}% of corpus)")
    print(f"  at substantial yield ({mean_yield_sub:.0f} concepts, {g_sub*1000:.0f} ms): "
          f"beyond {cross_sub:,.0f} articles "
          f"({100*cross_sub/total_rows:.1f}% of corpus)")
    print(f"  -> substantial subset (~{sub_ext:,}) is "
          f"{'GROUNDING' if sub_ext>cross_sub else 'READ'}-bound; "
          f"full corpus grounding is {'GROUNDING' if total_rows>cross_all else 'READ'}-bound")
    print()
    print("donkey=0")


def _rg_actual(files, stride):
    if stride <= 1:
        return None
    n = 0
    idx = 0
    for f in files:
        pf = pq.ParquetFile(f)
        for rg in range(pf.num_row_groups):
            if idx % stride == 0:
                n += 1
            idx += 1
    return n


if __name__ == "__main__":
    main()
