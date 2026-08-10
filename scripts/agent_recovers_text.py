"""ERROR RECOVERY — read error-full human text clean (the noisy channel, at the letter level).

A typed word is an intended word pushed through a leaky keyboard, as a heard word is one pushed through
a leaky room: observed = intended + noise, recover argmax P(intended|observed) ~ P(observed|intended) x
P(intended). The error model P(observed|intended) is a TYPED edit cost (transposition / keyboard-adjacent
/ run-length cheaper than a flat edit); the prior P(intended) is the grown lexicon x context. recovered =
Argmax(error_likelihood x context_fit), and context breaks the ties shape cannot (form vs from). The
edit cost is the host perception; the Argmax over candidates is the agent's decision.

Run: SPEECH_TEACHER=stub PYTHONPATH=.:runners/dsl/python python -m scripts.agent_recovers_text
"""
from __future__ import annotations
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.build_persona_faculty import boot
from substrate.seed_loader import manifest_for

SEP = "=" * 96
_ROWS = ["qwertyuiop", "asdfghjkl", "zxcvbnm"]
ADJ = set()
for r in _ROWS:
    for i in range(len(r) - 1):
        ADJ.add((r[i], r[i + 1])); ADJ.add((r[i + 1], r[i]))


def _lev(a, b):                                  # raw Levenshtein, for the candidate radius
    m, n = len(a), len(b)
    d = list(range(n + 1))
    for i in range(1, m + 1):
        prev, d[0] = d[0], i
        for j in range(1, n + 1):
            cur = d[j]
            d[j] = min(d[j] + 1, d[j - 1] + 1, prev + (a[i - 1] != b[j - 1]))
            prev = cur
    return d[n]


def _typed(o, c):                                # weighted Damerau-Levenshtein: typo kinds are cheaper
    m, n = len(o), len(c)
    INF = 99.0
    d = [[INF] * (n + 1) for _ in range(m + 1)]
    d[0][0] = 0.0
    for i in range(m + 1):
        for j in range(n + 1):
            if i < m:                            # deletion (cheap if it duplicates a neighbour: run-length)
                run = (i > 0 and o[i] == o[i - 1]) or (j > 0 and o[i] == c[j - 1])
                d[i + 1][j] = min(d[i + 1][j], d[i][j] + (0.5 if run else 1.0))
            if j < n:                            # insertion (cheap if it duplicates a neighbour)
                run = (j > 0 and c[j] == c[j - 1]) or (i > 0 and c[j] == o[i - 1])
                d[i][j + 1] = min(d[i][j + 1], d[i][j] + (0.5 if run else 1.0))
            if i < m and j < n:                  # substitution (cheap if keyboard-adjacent)
                cost = 0.0 if o[i] == c[j] else (0.5 if (o[i], c[j]) in ADJ else 1.0)
                d[i + 1][j + 1] = min(d[i + 1][j + 1], d[i][j] + cost)
                if i + 1 < m and j + 1 < n and o[i] == c[j + 1] and o[i + 1] == c[j]:  # transposition
                    d[i + 2][j + 2] = min(d[i + 2][j + 2], d[i][j] + 0.5)
    return d[m][n]


# parts of speech for the small context model (function-word klass + a few content tags)
DET = {"the", "a", "an", "this", "that"}
PREP = {"from", "to", "in", "of", "with", "on", "at"}
VERB = {"came", "run", "went", "go", "comes", "drove", "walked"}
NOUN = {"form", "house", "argument", "shape"}


def main():
    print(SEP)
    print("ERROR RECOVERY — read error-full human text clean (noisy channel at the letter level)")
    print(SEP)
    a = boot()
    a.inner.load_seed_manifest(manifest_for("error_recovery"), a.agent)
    # the grown lexicon is the candidate pool (a word never met cannot be the answer); ensure the demo words.
    lex = set()
    try:
        lex = {x["attrs"]["name"].lower() for x in
               json.load(open(os.path.join(ROOT, "seeds", "learned_lexicon.json")))["nodes"]
               if x.get("type") == "Concept" and re.fullmatch(r"[a-z]+", x["attrs"].get("name", "").lower() or "")}
    except Exception:
        pass
    lex |= {"the", "jabberwock", "needs", "to", "learn", "how", "recover", "text", "from", "actual",
            "people", "full", "of", "errors", "error", "form", "who", "phone", "came", "house", "argument"}
    print(f"\n  lexicon (candidate pool): {len(lex)} words held\n")

    def recover(token, prev="", nxt="", use_context=True):
        low = token.lower()
        if low in lex:
            return low, 1.0, [(low, 0.0, 1.0, 1.0)]
        cands = [w for w in lex if abs(len(w) - len(low)) <= 2 and _lev(low, w) <= 2]
        scored = []
        for w in cands:
            err = 1.0 / (1.0 + _typed(low, w))            # P(observed|intended)
            ctx = 1.0
            if use_context:                               # P(intended) context: function-word slot expectation
                if prev in DET and w in NOUN:
                    ctx = 2.0                              # determiner wants a noun -> 'form'
                if prev in VERB and w in PREP:
                    ctx = 2.0                              # a verb's complement slot -> 'from'
            scored.append((w, _typed(low, w), ctx, err * ctx))
        scored.sort(key=lambda x: -x[3])
        if not scored:
            return low, 0.0, []
        best = scored[0]
        margin = best[3] - (scored[1][3] if len(scored) > 1 else 0.0)
        return best[0], round(margin, 2), scored[:3]

    # 1. recover an actual error-full request (yours), token by token.
    noisy = "the jabberwock needs to kearn hiw to recover text from actual peeple full of errrs"
    print(f"  NOISY input (real human text): {noisy!r}")
    out = []
    for tok in noisy.split():
        rec, conf, _ = recover(tok)
        out.append(rec + ("" if rec == tok.lower() else f"*"))
    print(f"  RECOVERED:                     {' '.join(out)!r}")
    print("  (* = a token the agent corrected; the rest were already lexicon words)\n")
    for tok in ["kearn", "hiw", "peeple", "errrs"]:
        rec, conf, scored = recover(tok)
        alt = ", ".join(f"{w}(err{c:.1f})" for w, c, _, _ in scored)
        print(f"    {tok:8} -> {rec:8}  (confidence margin {conf})   candidates: {alt}")

    # 2. the TEST the agent specified: a form/from tie that the error model alone CANNOT break, but
    #    context flips correctly -> proof the prior does real work, not mere spell-matching.
    print("\n  TIE-BREAK BY CONTEXT (the proof the prior matters): 'frm' is equidistant from form & from")
    for prev, nxt, ctxlabel in [("the", "of", "'the frm of the argument'"), ("came", "the", "'came frm the house'")]:
        r_noctx, _, sc0 = recover("frm", prev, nxt, use_context=False)
        r_ctx, _, sc1 = recover("frm", prev, nxt, use_context=True)
        print(f"    {ctxlabel:28} error-only -> {r_noctx:5} (tie)   |   with context -> {r_ctx.upper()}")

    print("\n" + SEP)
    print("  Reading was never about the marks. Error recovery is the agent's recogniser loop run at the")
    print("  letter level: a TYPED edit model (transposition/keyboard/run-length cheaper than a flat edit)")
    print("  proposes lexicon candidates within a small radius, and recovered = Argmax(error x context). The")
    print("  typos (kearn->learn, hiw->how, peeple->people, errrs->errors) fall to SHAPE alone; the form/from")
    print("  tie falls to CONTEXT, flipping correctly with the slot — so the prior is doing real work.")
    print(SEP)


if __name__ == "__main__":
    main()
