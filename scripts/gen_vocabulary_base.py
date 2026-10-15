#!/usr/bin/env python3
"""Emit seeds/vocabulary_base_en.json (2026-10-10): an English VOCABULARY BASE
held as graph data -- the agent's reading and its reply-quality criterion
were both judging language without one.

Evidence it is missing (P5/P6):
  * the POS faculty (construction_grammar._pos_token) had no class for a
    contraction or an interjection, so "I'm", "What's", "Wow", "hmm" became
    untyped by-position gaps and the agent asked "what's 'I'm'?";
  * on a fresh checkout the English POS slab (wikt_pos_en, gitignored) is
    absent, and nearly every word is untyped;
  * ReplyQuality's content-word test is a 107-word hand stoplist that holds
    "fun" and "like", so "Fun is defined ..." shares nothing with "What do
    you do for fun?".

Derivation (mechanical, from reference corpora; no hand word lists):
  * the Brown corpus (NLTK, 1.16M POS-tagged tokens): per lowercase form, its
    tag distribution. Brown tags map to a part of speech; a form is CLOSED
    when >= 90% of its tokens carry a closed-class tag (determiner, pronoun,
    preposition, conjunction, auxiliary, modal, particle, qualifier,
    interjection, contraction), OPEN at >= 90% open-class (noun, verb, adj,
    adv), otherwise MIXED. A contraction is a compound tag (PPSS+BEM "i'm",
    WDT+BEZ "what's") or a negated auxiliary (DO* "don't"); its parts are
    kept (`expands`). Possessives (NN$) are not vocabulary entries.
  * every closed form is kept (closed classes are small); open and mixed
    forms are kept to the top OPEN_TOP by frequency (`rank` = Brown rank);
  * a conversational supplement: forms in persona_chat_8938 dialogues 300+
    (never an evaluation stream: those are drawn from the first 50) seen
    >= SUPP_MIN times and absent from Brown, typed by the Wiktionary POS slab
    when it is present (interjection / contraction / noun / verb / adj / adv).

Each entry is a VocabEntry{form, pos, klass, share, rank, expands, source}.
Consumers: construction_grammar._pos_token types a token it could not type
otherwise; reply_quality (criterion edit op `vocabulary`, P6, human-adopted)
reads its function words. Idempotent; requires nltk + the brown corpus.
"""
import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "seeds/vocabulary_base_en.json"
OPEN_TOP = 6000
SUPP_MIN = 20
CLOSED_SHARE = 0.9
FORM = re.compile(r"[a-z][a-z']*")

# Brown tag (base, suffixes -TL/-HL/-NC stripped) -> (pos, closed?)
CLOSED_TAGS = {
    "AT": "determiner", "DT": "determiner", "DTI": "determiner", "DTS": "determiner", "DTX": "determiner",
    "ABN": "determiner", "ABX": "determiner", "AP": "determiner", "WDT": "determiner",
    "IN": "preposition", "CC": "conjunction", "CS": "conjunction",
    "PPS": "pronoun", "PPSS": "pronoun", "PPO": "pronoun", "PPL": "pronoun", "PPLS": "pronoun",
    "PP$": "pronoun", "PP$$": "pronoun", "PN": "pronoun", "WPS": "pronoun", "WPO": "pronoun",
    "WP$": "pronoun", "EX": "pronoun",
    "MD": "modal", "TO": "particle", "RP": "particle", "QL": "qualifier", "QLP": "qualifier",
    "WQL": "qualifier", "WRB": "adverb", "UH": "interjection", "*": "negation",
    "BE": "auxiliary", "BED": "auxiliary", "BEDZ": "auxiliary", "BEG": "auxiliary", "BEM": "auxiliary",
    "BEN": "auxiliary", "BER": "auxiliary", "BEZ": "auxiliary", "HV": "auxiliary", "HVD": "auxiliary",
    "HVG": "auxiliary", "HVN": "auxiliary", "HVZ": "auxiliary", "DO": "auxiliary", "DOD": "auxiliary",
    "DOZ": "auxiliary",
}
OPEN_PREFIX = (("NN", "noun"), ("NP", "noun"), ("NR", "noun"), ("VB", "verb"), ("JJ", "adj"), ("RB", "adv"))
WIKT_MAP = {"intj": ("interjection", "closed"), "contraction": ("contraction", "closed"),
            "noun": ("noun", "open"), "verb": ("verb", "open"), "adj": ("adj", "open"), "adv": ("adv", "open"),
            "pron": ("pronoun", "closed"), "det": ("determiner", "closed"), "prep": ("preposition", "closed"),
            "conj": ("conjunction", "closed"), "particle": ("particle", "closed")}


def base_tag(t):
    return re.split(r"-(?:TL|HL|NC)", t)[0]


def map_part(t):
    """A single (non-compound) Brown tag -> (pos, closed) or None."""
    if t in CLOSED_TAGS:
        return CLOSED_TAGS[t], True
    if t.endswith("*") and t[:-1] in CLOSED_TAGS:          # negated auxiliary/modal: don't, can't
        return "contraction", True
    for pre, pos in OPEN_PREFIX:
        if t.startswith(pre) and not t.endswith("$"):
            return pos, False
    return None


def map_tag(t):
    """(pos, closed, expands) for a Brown tag; None for possessives / unknown."""
    t = base_tag(t)
    if "+" in t:
        parts = [map_part(x) for x in t.split("+")]
        if any(p is None for p in parts):
            return None
        return "contraction", True, [p[0] for p in parts]
    if t.endswith("*") and len(t) > 1:
        inner = map_part(t[:-1])
        return ("contraction", True, [inner[0], "negation"]) if inner else None
    m = map_part(t)
    return (m[0], m[1], []) if m else None


def brown_entries():
    from nltk.corpus import brown
    dist = collections.defaultdict(collections.Counter)
    for w, t in brown.tagged_words():
        lw = w.lower()
        if FORM.fullmatch(lw):
            m = map_tag(t)
            if m is not None:
                dist[lw][(m[0], m[1], tuple(m[2]))] += 1
    freq = collections.Counter({w: sum(c.values()) for w, c in dist.items()})
    rank = {w: i + 1 for i, (w, _n) in enumerate(freq.most_common())}
    out = {}
    for w, c in dist.items():
        n = sum(c.values())
        closed = sum(v for (p, cl, e), v in c.items() if cl) / n
        (pos, _cl, exp), _v = c.most_common(1)[0]
        klass = "closed" if closed >= CLOSED_SHARE else "open" if closed <= 1 - CLOSED_SHARE else "mixed"
        if klass != "closed" and rank[w] > OPEN_TOP:
            continue
        if klass == "closed":           # the dominant CLOSED reading names the entry
            (pos, _cl, exp), _v = max(((k, v) for k, v in c.items() if k[1]), key=lambda kv: kv[1])
        out[w] = {"form": w, "pos": pos, "klass": klass, "share": round(closed, 3), "rank": rank[w],
                  "expands": list(exp), "source": "brown"}
    return out


def supplement(have):
    corpus = json.loads((ROOT / "data/corpus/persona_chat_8938.json").read_text())
    freq = collections.Counter()
    for dlg in corpus[300:]:
        for _spk, text in dlg["turns"]:
            freq.update(FORM.findall(text.lower()))
    sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
    try:
        from domains import wiktionary_reference as wr
    except Exception:  # noqa: BLE001
        return {}, "wiktionary module unavailable"
    out = {}
    for w, n in freq.most_common():
        if n < SUPP_MIN:
            break
        if w in have:
            continue
        ps = wr.wiktionary_pos(w, "en")
        if not ps or ps[0] not in WIKT_MAP:
            continue
        pos, klass = WIKT_MAP[ps[0]]
        out[w] = {"form": w, "pos": pos, "klass": klass, "share": 1.0 if klass == "closed" else 0.0,
                  "rank": None, "conv_freq": n, "expands": [], "source": "persona_chat+wiktionary"}
    return out, ("slab present" if out else "slab absent or no new forms")


def main():
    entries = brown_entries()
    supp, note = supplement(entries)
    entries.update(supp)
    rows = sorted(entries.values(), key=lambda e: (e["rank"] is None, e["rank"] or 0, e["form"]))
    nodes = [{"local_id": i, "type": "VocabEntry", "attrs": {k: v for k, v in e.items() if v is not None}}
             for i, e in enumerate(rows)]
    counts = collections.Counter((e["klass"], e["pos"]) for e in rows)
    seed = {"id": "vocabulary_base_en", "version": "1.0.0", "depends_on": [],
            "description": __doc__ + f"\nBuilt: {len(rows)} entries ({note}).",
            "nodes": nodes, "edges": [], "productions": [], "rules": []}
    P.write_text(json.dumps(seed, separators=(",", ":"), ensure_ascii=True) + "\n")
    print("vocabulary_base_en", len(rows), "entries;", dict(collections.Counter(e["klass"] for e in rows)),
          "; supplement", len(supp), note)
    print(sorted(counts.items(), key=lambda kv: -kv[1])[:20])


if __name__ == "__main__":
    main()
