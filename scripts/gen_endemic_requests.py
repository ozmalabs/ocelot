#!/usr/bin/env python3
"""Emit evaluation/fixtures/endemic_requests_v1.json (tranche 20): natural
requests for the endemic RSI measurement, derived mechanically from
data/corpus/persona_chat_8938.json, with no hand-picked verbs.

1. Verbs: every word of length >= 4 that occurs >= 5 times in the corpus and
   whose WordNet lemmas (domain_data/wordnet_senses.sqlite) are verb-only (no
   noun or adjective reading), excluding -ing/-ed/-es surface forms.
2. Object: the noun the verb most often takes in the corpus, in the patterns
   "<verb> the|a|my|your|some|an <noun>". Verbs with fewer than 2 such uses
   are dropped. The request is "<Verb> the <noun>." ('the' unless the corpus
   determiner was 'the' already).
3. Order: a seeded shuffle (seed 20261010) of the sorted verb list.
"""
import collections, json, random, re, sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/fixtures/endemic_requests_v1.json"


def main():
    d = json.loads((ROOT / "data/corpus/persona_chat_8938.json").read_text())
    con = sqlite3.connect("file:%s?mode=ro" % (ROOT / "domain_data/wordnet_senses.sqlite"), uri=True)
    cnt = collections.Counter()
    for dlg in d:
        for _, t in dlg["turns"]:
            cnt.update(re.findall(r"[a-z]+", t.lower()))
    verbs = []
    for w, c in cnt.items():
        if c < 5 or len(w) < 4 or w.endswith(("ing", "ed", "es")):
            continue
        poss = {p for (p,) in con.execute("SELECT pos FROM lemma WHERE form=?", (w,))}
        if "v" in poss and not poss & {"n", "a", "s"}:
            verbs.append(w)
    verbs.sort()
    random.seed(20261010)
    random.shuffle(verbs)
    vs = set(verbs)
    objs = collections.defaultdict(collections.Counter)
    for dlg in d:
        for _, t in dlg["turns"]:
            ws = re.findall(r"[a-z']+", t.lower())
            for i, w in enumerate(ws[:-2]):
                if w in vs and ws[i + 1] in ("the", "a", "my", "your", "some", "an"):
                    o = ws[i + 2]
                    r = con.execute("SELECT pos FROM lemma WHERE form=? ORDER BY rank LIMIT 1", (o,)).fetchone()
                    if r and r[0] == "n" and len(o) > 2:
                        objs[w][(ws[i + 1], o)] += 1
    reqs = []
    for w in verbs:
        if sum(objs[w].values()) >= 2:
            (_det, o), n = objs[w].most_common(1)[0]
            reqs.append({"verb": w, "object": o, "corpus_uses": sum(objs[w].values()),
                         "text": "%s the %s." % (w.capitalize(), o)})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"description": __doc__, "source": "data/corpus/persona_chat_8938.json",
                               "seed": 20261010, "requests": reqs}, indent=1) + "\n")
    print("wrote", OUT.relative_to(ROOT), len(reqs))


if __name__ == "__main__":
    main()
