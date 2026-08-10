"""INGEST a REAL sample of arXiv MATH source (.tex) — the mechanical WORLD-ADAPTER
half of the arXiv pipeline. Mirrors the established corpus-connection pattern
(data/nlab, data/stacks): fetch bulk LaTeX, store on disk, GITIGNORED (code only).

The arXiv .tex source is the SAME SHAPE as the Stacks Project repo — bulk LaTeX
with \\begin{theorem}/\\begin{definition}/\\begin{lemma}/\\begin{proof}
environments. So the agent's EXISTING reader (research-register comprehension +
LaTeX-preserving loader) reads it unchanged; the only new mechanical piece is the
INGEST: arXiv's real endpoints ->  .tex on disk.

Two real arXiv endpoints (both public, no key):
  1. LIST   — the arXiv API (http://export.arxiv.org/api/query) returns paper ids
              in a category (math.AT / math.NT / math.AG / math.GT / math.KT —
              where computed invariants live). A category query, paged.
  2. SOURCE — the e-print endpoint (https://arxiv.org/e-print/<id>) returns the
              LaTeX SOURCE tarball (gzipped tar, or a single gzipped .tex). The
              .tex files are extracted to data/arxiv/<id>/.

This is a WORLD ADAPTER (CLAUDE.md): mechanical translation of an external form
(arXiv tar) into files the loader reads. No reasoning, no agent state, no LLM.

POLITE: a fixed delay between requests (arXiv asks ~3s); a descriptive
User-Agent with a contact; a BOUNDED sample (the demo proves the mechanism +
measures the per-paper rate — full arXiv is the SAME pipeline pointed at more
ids). If a fetch path is blocked, it reports the failure honestly and keeps
whatever real source it got.

  python scripts/fetch_arxiv.py [--per-cat N] [--cats math.AT,math.NT,...]
"""
from __future__ import annotations

import argparse
import gzip
import io
import re
import sys
import tarfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / "data" / "arxiv"

# the HLE-relevant math categories — where COMPUTED INVARIANTS + IDENTIFICATIONS
# live (algebraic topology, number theory, algebraic geometry, geometric
# topology, K-theory). The strategic finding: the detail is spread across the
# frontier literature; these are the categories nLab under-covers for invariants.
DEFAULT_CATS = ["math.AT", "math.NT", "math.AG", "math.GT", "math.KT"]

_UA = "ozma-research/0.1 (arxiv math ingest; mailto:hrdwrbob@gmail.com)"
_API = "http://export.arxiv.org/api/query"
_EPRINT = "https://arxiv.org/e-print/"
_DELAY = 3.0  # arXiv's polite delay between requests (seconds).


def _get(url: str, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    return urllib.request.urlopen(req, timeout=timeout).read()


def list_ids(category: str, count: int, start: int = 0) -> list[str]:
    """LIST paper ids in a category via the arXiv API. Returns bare ids (no
    version suffix). A mechanical query — the API speaks Atom XML; we pull the
    <id> entries out."""
    out: list[str] = []
    page = 0
    while len(out) < count:
        n = min(50, count - len(out))
        url = (f"{_API}?search_query=cat:{category}"
               f"&start={start + page * 50}&max_results={n}"
               f"&sortBy=submittedDate&sortOrder=descending")
        try:
            xml = _get(url, timeout=40).decode("utf-8", "replace")
        except Exception as e:
            print(f"    [list {category}] ERR {type(e).__name__}: {e}",
                  file=sys.stderr)
            break
        ids = re.findall(r"<id>https?://arxiv\.org/abs/([^<]+)</id>", xml)
        ids = [i.rsplit("v", 1)[0] if re.search(r"v\d+$", i) else i for i in ids]
        if not ids:
            break
        out.extend(ids)
        page += 1
        time.sleep(_DELAY)
        if len(ids) < n:
            break
    return out[:count]


def _extract_tex(raw: bytes) -> dict[str, str]:
    """Pull the .tex file(s) out of an e-print payload. arXiv source is a gzipped
    tar (multi-file) OR a single gzipped .tex. Mechanical decode — no decision."""
    texs: dict[str, str] = {}
    try:
        tf = tarfile.open(fileobj=io.BytesIO(raw))
        for m in tf.getmembers():
            if m.isfile() and m.name.endswith(".tex"):
                f = tf.extractfile(m)
                if f is not None:
                    texs[Path(m.name).name] = f.read().decode("utf-8", "replace")
        return texs
    except tarfile.ReadError:
        pass
    try:
        dec = gzip.decompress(raw).decode("utf-8", "replace")
        if "\\begin{" in dec or "\\documentclass" in dec:
            texs["main.tex"] = dec
    except Exception:
        pass
    return texs


def fetch_source(arxiv_id: str) -> dict[str, str]:
    """SOURCE: fetch + extract the .tex file(s) for one paper id."""
    try:
        raw = _get(_EPRINT + arxiv_id, timeout=90)
    except Exception as e:
        print(f"    [src {arxiv_id}] ERR {type(e).__name__}: {e}",
              file=sys.stderr)
        return {}
    return _extract_tex(raw)


def ingest(cats: list[str], per_cat: int) -> dict:
    """The full INGEST: for each category, list ids, fetch each paper's .tex
    source, write it under data/arxiv/<id>/. Returns a summary {papers, files,
    by_cat}. Polite (rate-limited). A pure world adapter."""
    DEST.mkdir(parents=True, exist_ok=True)
    summary = {"papers": 0, "files": 0, "by_cat": {}, "ids": []}
    for cat in cats:
        print(f"[list] {cat} — requesting {per_cat} ids ...")
        ids = list_ids(cat, per_cat)
        print(f"[list] {cat} — got {len(ids)} ids")
        got = 0
        for aid in ids:
            safe = aid.replace("/", "_")
            pdir = DEST / safe
            if pdir.exists() and any(pdir.glob("*.tex")):
                # already on disk (resume-friendly) — count it, skip the fetch.
                summary["papers"] += 1
                summary["files"] += len(list(pdir.glob("*.tex")))
                summary["ids"].append(safe)
                got += 1
                continue
            texs = fetch_source(aid)
            time.sleep(_DELAY)
            if not texs:
                continue
            pdir.mkdir(parents=True, exist_ok=True)
            for fname, body in texs.items():
                (pdir / fname).write_text(body, encoding="utf-8")
            # record the source category on disk (a tiny provenance marker file).
            (pdir / "_cat.txt").write_text(cat, encoding="utf-8")
            summary["papers"] += 1
            summary["files"] += len(texs)
            summary["ids"].append(safe)
            got += 1
        summary["by_cat"][cat] = got
        print(f"[done] {cat} — {got} papers fetched")
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-cat", type=int, default=40,
                    help="papers to fetch per category (bounded sample)")
    ap.add_argument("--cats", type=str, default=",".join(DEFAULT_CATS))
    args = ap.parse_args()
    cats = [c.strip() for c in args.cats.split(",") if c.strip()]
    print(f"INGEST arXiv math source -> {DEST}")
    print(f"  categories: {cats}")
    print(f"  per-category: {args.per_cat}  (polite delay {_DELAY}s)")
    s = ingest(cats, args.per_cat)
    print("\n" + "=" * 60)
    print(f"INGESTED {s['papers']} papers, {s['files']} .tex files")
    for c, n in s["by_cat"].items():
        print(f"  {c}: {n}")
    print(f"stored under {DEST} (GITIGNORED)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
