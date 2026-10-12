"""
sensitivity_wordboundary — POST-HOC, clearly labelled. NOT the preregistered number.

The prereg rules_typer uses the PoC's substring `cue in low` matching, inherited verbatim.
Measurement surfaced a real bug: 'ease' matches inside 'incr-ease-s', 'easing' inside
'incr-easing'. This script re-runs the SAME lexicon + flip rules but with word-boundary
matching, to quantify how much of the rules-only miss is the substring artifact vs the deeper
extraction ceiling. Reported as a sensitivity check in PHASE3_DERISK_RESULTS.md, explicitly
separate from the frozen prereg result.
"""
from __future__ import annotations
import json, os, re, sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rules_typer as rt  # noqa: E402

LABELS = ["up", "down", "none"]


def _wb_tally(low, lex):
    score, hits = 0, []
    for cue, w in lex.items():
        if " ... " in cue:
            a, b = cue.split(" ... ")
            if re.search(rf"\b{re.escape(a)}\b", low) and re.search(rf"\b{re.escape(b)}\b", low):
                score += w; hits.append(cue)
        else:
            # word-boundary; multiword cues match as phrase with \b at ends
            if re.search(rf"\b{re.escape(cue)}\b", low):
                score += w; hits.append(cue)
    return score, hits


def type_wb(text):
    low = rt._norm(text)
    for rx, forced in rt.FLIP_RULES:
        if rx.search(low):
            return forced
    h, _ = _wb_tally(low, rt.HAWKISH)
    d, _ = _wb_tally(low, rt.DOVISH)
    n, _ = _wb_tally(low, rt.NEUTRAL)
    if n > 0 and n >= h and n >= d:
        return "none"
    if h == 0 and d == 0:
        return "none"
    if h > d:
        return "up"
    if d > h:
        return "down"
    return "none"


def main():
    snips = json.load(open(os.path.join(HERE, "study_set.json")))["snippets"]
    gold = [s["gold"] for s in snips]
    pred = [type_wb(s["text"]) for s in snips]
    n = len(snips)
    acc = sum(1 for g, p in zip(gold, pred) if g == p) / n
    conf = {g: Counter() for g in LABELS}
    for g, p in zip(gold, pred):
        conf[g][p] += 1
    dir_idx = [i for i, g in enumerate(gold) if g in ("up", "down")]
    usable = sum(1 for i in dir_idx if pred[i] == gold[i]) / len(dir_idx)
    wrong = sum(1 for i in dir_idx if pred[i] in ("up", "down") and pred[i] != gold[i]) / len(dir_idx)
    print(json.dumps({
        "label": "POST-HOC sensitivity (word-boundary match); NOT the prereg number",
        "overall_accuracy": round(acc, 3),
        "usable_directional_recall": round(usable, 3),
        "wrong_direction_rate": round(wrong, 3),
        "confusion": {g: dict(conf[g]) for g in LABELS},
    }, indent=2))


if __name__ == "__main__":
    main()
