"""Exact benchmark for the definition GENUS reader (tranche 18).

Tranche 17 grounds a held word that has no WordNet sense through the genus of
its held definition (domains/lexical_qualia.definition_genus). Those words
have no ground truth by construction, so tranche 17's precision (~77%) was a
manual reading. This benchmark measures the same reader EXACTLY on the held
words that DO have WordNet noun senses and a held definition:

  a genus pick is a HIT iff one of the genus's noun senses lies in the
  hypernym closure of one of the word's own noun senses (the word's senses
  included -- a synonym genus is a correct gloss head) AND that sense is
  specific at the steering aperture's grain:
      extent * 1000 <= max_extent_per_mille * words
  GENERAL iff a genus sense is in the closure but none is that specific
  ("person.n.01" for "secretary": correct, but it never decides a match);
  a MISS iff the reader picked a genus and no genus sense is in the closure;
  NONE iff the reader picked no genus.

  precision = (hit + general) / picked;  specific_precision = hit / picked;
  coverage = picked / n

The benchmark is a LOWER BOUND on true precision: WordNet often lacks the
technical sense a free-text definition is about ("thread: execution context"
is not WordNet's thread.n.01), so a correct gloss head can score a miss. It
is exact and reproducible, which is what comparing readers needs.

Definitions are split by style, because a "(noun) ..." definition is a
WordNet gloss quoted verbatim (easy, and unlike the jargon definitions the
reader is used on), while a FREE-TEXT definition (substrate glossary, wiki
lead, tvtropes) is the kind the identity-only words carry. The headline is
FREE-TEXT. Words are split deterministically into DEV and TEST halves (by a
stable hash of the word) so a reader tuned on DEV is reported on TEST.

Mechanical measurement only; reads seeds/lexical_qualia.json for extents and
the cached held-word table (scripts/gen_lexical_qualia_index.held_words).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Callable, Optional

ROOT = Path(__file__).resolve().parents[1]
APERTURE_PER_MILLE = 50


def split_of(word: str) -> str:
    return "dev" if int(hashlib.sha256(word.encode()).hexdigest(), 16) % 2 == 0 else "test"


def style_of(definition: str) -> str:
    return "gloss" if definition.lstrip().startswith("(") else "free"


def _extents() -> tuple[dict, int]:
    d = json.loads((ROOT / "seeds" / "lexical_qualia.json").read_text())
    ext = {n["attrs"]["name"]: int(n["attrs"].get("extent") or 0) for n in d["nodes"] if n["type"] == "Quale"}
    words = next(n["attrs"]["words"] for n in d["nodes"] if n["type"] == "QualiaIndex")
    return ext, int(words)


def _closure(names, cache: dict) -> set:
    from domains import wordnet_table as wt
    out, stack = set(), list(names)
    while stack:
        q = stack.pop()
        if q in out:
            continue
        out.add(q)
        if q not in cache:
            cache[q] = wt.hypernyms(q)
        stack.extend(cache[q])
    return out


def cases(held: dict) -> list:
    """[(word, definition, style, split, word_noun_senses)] for every held
    word with a WordNet noun sense and a held definition."""
    from domains import wordnet_table as wt
    out = []
    for w, d in sorted(held.items()):
        if not d:
            continue
        ns = sorted({s for s in wt.synsets(w) if s.split(".")[-2] == "n"})
        if ns:
            out.append((w, d, style_of(d), split_of(w), ns))
    return out


def score(reader: Callable[[str, str], Optional[dict]], held: dict) -> dict:
    """reader(word, definition) -> {"genus", "senses"} | None."""
    ext, words = _extents()
    hyp: dict = {}
    res: dict = {}
    rows = []
    for w, d, style, split, ns in cases(held):
        g = reader(w, d)
        if not g:
            verdict = "none"
        else:
            clos = _closure(ns, hyp)
            inside = [s for s in g["senses"] if s in clos]
            ok = [s for s in inside if ext.get(s, 0) * 1000 <= APERTURE_PER_MILLE * words]
            # hit: a specific correct genus; general: correct but too general to
            # discriminate at the aperture (harmless, useless); miss: wrong.
            verdict = "hit" if ok else ("general" if inside else "miss")
        rows.append({"word": w, "style": style, "split": split, "verdict": verdict,
                     "genus": (g or {}).get("genus")})
        for key in (style + ":" + split, style + ":all", "all:" + split):
            b = res.setdefault(key, {"n": 0, "hit": 0, "general": 0, "miss": 0, "none": 0})
            b["n"] += 1
            b[verdict] += 1
    for b in res.values():
        picked = b["hit"] + b["general"] + b["miss"]
        b["precision"] = round((b["hit"] + b["general"]) / picked, 4) if picked else None
        b["specific_precision"] = round(b["hit"] / picked, 4) if picked else None
        b["coverage"] = round(picked / b["n"], 4) if b["n"] else None
    return {"buckets": dict(sorted(res.items())), "rows": rows}


FIXTURE = ROOT / "evaluation" / "fixtures" / "genus_benchmark_definitions.json"


def held_words_cached(path: Path = FIXTURE) -> dict:
    """{word: definition} for the benchmark. Defaults to the committed fixture
    (captured from a full boot at tranche 18, so the benchmark is reproducible
    without a boot); a non-fixture path is a cache of a fresh capture."""
    if path == FIXTURE and path.exists():
        return json.loads(path.read_text())["benchmark"]
    if path.exists():
        return json.loads(path.read_text())
    import sys
    sys.path[:0] = [str(ROOT), str(ROOT / "scripts"), str(ROOT / "runners/dsl/python")]
    import gen_lexical_qualia_index as g
    held = g.held_words()
    path.write_text(json.dumps(held))
    return held


def manual_audit(reader: Callable[[str, str], Optional[dict]]) -> dict:
    """Score a reader on the tranche-17 identity-only words against the
    tranche-17 MANUAL audit (evaluation/fixtures/genus_manual_audit_t17.json).
    Only words whose pick is UNCHANGED from the audited tranche-17 pick have a
    label; changed picks are listed for (re-)judgement, not scored."""
    defs = json.loads(FIXTURE.read_text())["identity_t17"]
    audit = json.loads((ROOT / "evaluation" / "fixtures" / "genus_manual_audit_t17.json").read_text())
    wrong = set(audit["wrong"])
    t17 = audit.get("picks") or {}
    same = changed = labelled_wrong = 0
    changes = []
    for w, d in sorted(defs.items()):
        if w not in t17:
            continue
        g = reader(w, d) if d else None
        gen = g["genus"] if g else None
        if gen == t17[w]:
            same += 1
            labelled_wrong += w in wrong
        else:
            changed += 1
            changes.append({"word": w, "t17": t17[w], "now": gen, "t17_wrong": w in wrong})
    return {"unchanged": same, "unchanged_wrong": labelled_wrong, "changed": changed, "changes": changes}


if __name__ == "__main__":
    from domains import lexical_qualia as lq
    r = score(lq.definition_genus, held_words_cached())
    print(json.dumps(r["buckets"], indent=1))
