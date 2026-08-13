#!/usr/bin/env python3
"""scripts/a6_discover_probes.py — DISCOVERY, not measurement, for A6
(`domains/reflective_faculty.py::_compose_rule_literal_variant`).

Boots a full agent, runs `_ensure_where_literal_rule_provenance` (mints/
upgrades the real `writes_where_literal==1.0` RuleSummary pool) +
`domains.rule_signature.ensure_where_signature` (mints `where_signature_json`
on that same pool -- NOT filtered to `writes_chosen_action`, since
`ensure_where_signature` mints for every RuleSummary carrying a `rule_json`),
then mechanically searches for genuine Class A / Class B probe words over the
REAL, full-corpus candidate pool this site's Argmax actually iterates,
mirroring `scripts/seed_signature_discover_probes.py`'s own discovery
method exactly, one grain down (per (rule, where-literal) pair instead of
per seed).

Class A word: NOT a member of ANY (rule, candidate)'s own LOCAL
`_collect_vocab_tokens(cand)` set anywhere in the pool (so the PRIMARY
Argmax, which requires >=2 such local-vocab hits, abstains system-wide for
any 2-word combination drawn only from Class A words) but IS a substring
of some candidate rule's `where_signature_json` blob (so a structural
fallback keyed on that blob could recover it).

Class B word: a member of SOME (rule, candidate)'s own local vocab (so the
primary already has real signal there).

Read-only. No production file touched or imported for writing.
"""
from __future__ import annotations

import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from domains.engine_provenance import engine_preamble  # noqa: E402
engine_preamble(strict=False)

from substrate.boot_core import boot_core  # noqa: E402
from substrate.boot_all import load_all_seeds  # noqa: E402
import domains.reflective_faculty as rf  # noqa: E402
from domains import rule_signature as rsig  # noqa: E402


class _Agent:
    def __init__(self, s, agent_node):
        self.s = s
        self.inner = s._inner
        self.agent = agent_node


def main():
    t0 = time.time()
    print("Booting full agent (load_all_seeds) ...", flush=True)
    s, agent_node = boot_core()
    ag = _Agent(s, agent_node)
    rep = load_all_seeds(ag)
    print(f"  loaded {rep['loaded']}/{rep['total']} in {time.time()-t0:.1f}s", flush=True)

    sub, native, _ag2 = rf._resolve_agent(ag)
    rf._ensure_where_literal_rule_provenance(sub, native)
    n_touched = rsig.ensure_where_signature(sub)
    print(f"ensure_where_signature: minted {n_touched} new attrs in {time.time()-t0:.1f}s", flush=True)

    # Gather the REAL candidate pool: (rule_name, cand_index, local_vocab,
    # where_signature_json) for every writes_where_literal==1.0 &
    # skippable==1.0 RuleSummary.
    rule_rows = []   # [(rule_name, [vocab_per_cand], sig_json_lc)] -- ONE entry per rule
    pair_count = 0
    local_vocab_union: set[str] = set()
    n_rules = 0
    t_pool0 = time.time()
    for n in sub.nodes("RuleSummary"):
        at = sub.node(n)["attrs"]
        if at.get("writes_where_literal") != 1.0 or at.get("skippable") != 1.0:
            continue
        n_rules += 1
        try:
            rule_json = json.loads(at.get("rule_json") or "{}")
        except Exception:
            continue
        cands = rf._find_where_lits(rule_json.get("where"))
        cand_vocabs = [rf._collect_vocab_tokens(c) for c in cands]
        for v in cand_vocabs:
            local_vocab_union |= v
        pair_count += len(cand_vocabs)
        sig_json_lc = (at.get("where_signature_json") or "").lower()
        rule_rows.append((at.get("name"), cand_vocabs, sig_json_lc))

    print(f"Candidate pool: {n_rules} rules, {pair_count} (rule, literal) pairs, "
          f"{len(local_vocab_union)} distinct local-vocab words "
          f"(gathered in {time.time()-t_pool0:.1f}s)", flush=True)

    # Class A: words present in SOME rule's where_signature_json, absent from
    # the GLOBAL local_vocab_union entirely (so no (rule,cand) pair anywhere
    # can ever score on it under the primary). Tokenize each rule's sig_json
    # ONCE (not once per candidate pair -- that redundancy is what made the
    # first version of this script pathologically slow on the real corpus).
    # Generic JSON row-shape / Term-scaffolding vocabulary -- not rule
    # CONTENT, excluded from candidacy (mirrors
    # scripts/seed_signature_discover_probes.py's own exclusion note).
    _SCAFFOLD = frozenset({
        "type", "node", "attr", "key", "value", "var", "name", "path",
        "items", "source", "predicate", "cond", "then", "other", "arg",
        "args", "exists", "filter", "neighbours", "null", "plus", "minus",
        "count", "lit", "eq", "gte", "gt", "lte", "lt", "not", "and", "or",
        "ra", "rt", "wild",
    })
    t_a0 = time.time()
    class_a = []  # (word, rule_name) -- rule whose sig_json contains it
    seen_words = set()
    for rule_name, _cand_vocabs, sig_json_lc in rule_rows:
        if not sig_json_lc:
            continue
        for tok in _tokenize(sig_json_lc):
            if len(tok) < 4 or tok in seen_words or tok in _SCAFFOLD:
                continue
            seen_words.add(tok)
            if tok in local_vocab_union:
                continue
            class_a.append((tok, rule_name))
    print(f"Class A pass: {time.time()-t_a0:.1f}s", flush=True)

    # Class B: words present in the local vocab of some (rule, cand) pair --
    # trivially plentiful (e.g. every attr-key word).
    class_b = []
    for rule_name, cand_vocabs, _sig in rule_rows:
        for vocab in cand_vocabs:
            for tok in vocab:
                if len(tok) >= 4:
                    class_b.append((tok, rule_name))

    print(f"Class A candidates (never locally reachable, sig-reachable): {len(class_a)}", flush=True)
    print(f"Class B candidates (locally reachable): {len(class_b)}", flush=True)

    out = {
        "n_rules": n_rules, "n_pairs": pair_count,
        "n_local_vocab_words": len(local_vocab_union),
        "class_a_sample": class_a[:60],
        "class_a_count": len(class_a),
        "class_b_sample": class_b[:30],
        "class_b_count": len(class_b),
    }
    out_path = os.path.join(ROOT, "scripts", "a6_discover_probes_results.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"\nWritten to {out_path}")
    print(f"Total wall time: {time.time()-t0:.1f}s")


def _tokenize(text: str) -> list[str]:
    """Underscore-split word PARTS -- matching how a real content sentence
    is actually written (no human writes 'babble_idx' in prose; they write
    'babble') and how `_collect_vocab_tokens` itself already tokenizes an
    Attr key (`key.split('_')`). Production's own fallback check is a plain
    substring test against the raw JSON text, so this is the same word form
    a genuine probe sentence would supply."""
    import re
    raw = re.findall(r"[a-z][a-z_]{2,}", text)
    out = []
    for tok in raw:
        out.extend(p for p in tok.split("_") if p)
    return out


if __name__ == "__main__":
    main()
