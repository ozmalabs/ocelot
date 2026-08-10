#!/usr/bin/env python3
"""Generate the imagination trace retention rule — the graph's OOM, closed.

THE MEASUREMENT (2026-08-07). Three growth daemons died; one was killed by the
kernel OOM killer at 8.4 GB anon-rss. The graphs were not diffusely large, they
were one node type:

    growth7   1,000,067 nodes  ->  960,663  (96.1%)  ImaginedConclusion
    growth9     541,773 nodes  ->  513,578  (94.8%)  ImaginedConclusion

`imagine()` mints ONE `ImaginedConclusion` per entry of the detached collapse's
graph_diff, as a durable trace on the LIVE graph, and nothing ever removes them.
The diff scales with the graph, so the trace is QUADRATIC in the graph it is
recording and permanent. Measured over growth9's 483 imaginations: median 1,057
conclusions each, max 2,123, and the first was 66 — the fanout grows visibly as
the graph does. By the end the imaginations were also exhausting their step
budget (`steps_run == steps_budget == 100000`, `converged: false`), so the
runaway was degrading the reasoning it was recording.

WHAT THE TRACE ACTUALLY CONTAINED: of 513,578 conclusions, **513,578 survived
and 0 were discarded**, nearly all reading `kind: edge_added`, `reason: "novel
structure -- nothing live to contradict by identity"`. That is the NULL verDICT.
A conclusion about structure with no live counterpart cannot be contradicted by
construction, so `_judge_conclusion` returns True for it every time. The
informative record is the DISCARDED one — a caught fantasy, the whole point of
regrounding — and there were none to lose.

SO THIS IS A SIGNAL FILTER, NOT A RETENTION WINDOW. Three things keep it honest:

  1. The `Imagination` node ALREADY carries `n_conclusions` / `n_survived` /
     `n_discarded`, so the counts are never lost — only the individual null
     records are, and the parent's summary is what any future reader of "an
     imagination happened, here is what it concluded" would consult first.
  2. Every DISCARDED conclusion is kept, forever. Caught fantasies are the
     evidence; unchallenged novelty is the noise.
  3. Only SUPERSEDED imaginations are compacted (a strictly newer regrounded
     `Imagination` must exist). The most recent trace is always intact, which is
     what keeps this clear of `commit_imagination` — that writes SURVIVORS'
     content into the live graph, and it always operates on the imagination just
     made, which is by definition the newest and therefore never compacted here.

`trace_compacted` is stamped on the parent so the compaction is visible rather
than silent: a reader can tell "this imagination's null records were retired"
apart from "this imagination concluded nothing".

Nothing in any seed MATCHES `ImaginedConclusion` — every occurrence of the type
name across the seed set is inside a rule comment. The only consumer is
`reground()`, within the same `imagine()` call, and it already tolerates a
missing conclusion node (`if not sub.has_node(cid): continue`).
"""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def V(name): return {"type": "Var", "name": name}
def L(value): return {"type": "Lit", "value": value}
def A(name, key): return {"type": "Attr", "node": V(name), "key": key}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def And(*items): return {"type": "And", "items": list(items)}
def Not(arg): return {"type": "Not", "arg": arg}
def NodesOfType(node_type): return {"type": "NodesOfType", "node_type": node_type}
def Exists(source, var, predicate): return {
    "type": "Exists", "source": source, "var_name": var, "predicate": predicate}


def superseded(imagination="imagination"):
    """A strictly newer REGROUNDED imagination exists.

    Strictly newer by `ts`, so the newest trace is never in scope. This is the
    guard that keeps compaction clear of `commit_imagination`, which writes the
    survivors' CONTENT into the live graph and always operates on the
    imagination just made.
    """
    return Exists(
        NodesOfType("Imagination"), "newer",
        And(
            Eq(A("newer", "status"), L("regrounded")),
            Gt(A("newer", "ts"), A(imagination, "ts")),
        ),
    )


def compact_superseded_trace_rule():
    return {
        "name": "itr_retire_null_conclusions_of_superseded_imagination",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": True,
        "comment": (
            "A conclusion that survived because nothing live could contradict it "
            "carries no information once its imagination is superseded; the "
            "parent's n_survived already records how many there were. Discarded "
            "conclusions -- the caught fantasies -- are never retired, and the "
            "newest imagination's trace is never touched."
        ),
        "match": [
            ["imagination", "imagined", "conclusion"],
        ],
        "where": And(
            Eq(A("imagination", "status"), L("regrounded")),
            # THE NULL VERDICT, and only it. `discarded` is the informative
            # outcome and is kept; an UNJUDGED conclusion (no status yet) is not
            # this rule's business either.
            Eq(A("conclusion", "status"), L("survived")),
            superseded(),
        ),
        "effects": [
            ["set_attr", "imagination", "trace_compacted", 1],
            ["del_node", "conclusion"],
        ],
    }


def manifest() -> dict:
    return {
        "id": "imagination_trace_retention",
        "version": "1.0.0",
        "depends_on": [],
        "productions": [
            {"provenance": "seed:imagination_trace_retention:imagined-1",
             "src": {"type": "Imagination", "var": "s"},
             "edge_type": "imagined",
             "tgt": {"type": "ImaginedConclusion", "var": "t"}},
        ],
        "rules": [
            compact_superseded_trace_rule(),
        ],
    }


def main() -> int:
    output = ROOT / "seeds" / "imagination_trace_retention.json"
    output.write_text(json.dumps(manifest(), indent=1) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
