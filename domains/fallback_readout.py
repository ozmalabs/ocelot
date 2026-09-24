"""FALLBACK READOUT — a mechanical reader for the fallback vocabulary.

This module is a **world adapter** in the CLAUDE.md sense and nothing more. It
does exactly two things:

1. **Ingest** — translate the engine's own counters (`rule_costs()`,
   `defaulted_reads()`, `absence_branches()`) into graph nodes and edges.
   Mechanical translation, no conditionals over graph state.
2. **Emit** — read the resulting graph back out as plain dicts.

**Between the two it calls `run_rules()` and lets `seeds/fallback_vocabulary.json`
decide.** The three-way classification (`silent` / `degraded` / `healthy`) is
made by `fv_status_silent` / `fv_status_degraded` / `fv_status_healthy` — seed
rules reading graph state — never here. There is deliberately no `if` in this
file that inspects a counter and decides what it means; the only conditionals
present are loop guards and "did the caller ask for this".

Why the vocabulary exists at all is in `VISION_FALLBACK_VOCAB_PREREG.md` §0: a
layer is only a layer if it has defined behaviour in the absence of its
neighbours **and declares it**. The redundancy audit could not distinguish
"layer B genuinely operates without A" from "nothing in B was running", and
that is the distinction this reader surfaces.

**OFF by default (§9).** Nothing here runs unless a caller invokes it. Minting
adds nodes, which moves `node_count()`, so it can never be implicit.
"""
from __future__ import annotations

from typing import Any

# The node/edge vocabulary. Typed graph objects, NOT prose — the redundancy
# audit's own marker regex matched the seeds' documentation comments and would
# have inverted its Arm 4 result, so every marker here is a node TYPE or a
# numeric attribute and there is no free text for a regex to catch.
REPORT_TYPE = "FallbackReport"
ACTIVITY_TYPE = "RuleActivity"
DEFAULTED_TYPE = "DefaultedRead"
ABSENCE_TYPE = "AbsenceBranch"

EDGE_ACTIVITY = "has_rule_activity"
EDGE_DEFAULTED = "defaulted"
EDGE_ABSENCE = "absence_branch"


def engine_tallies(s) -> dict[str, Any]:
    """Read the engine's counters. Pure read-back, no graph mutation.

    Returns the three raw tallies plus the overhead pair. `attr_evals` is 0
    unless `fallback_count_totals(True)` was set for the whole run — a 0
    denominator means NOT MEASURED, never "no reads", and callers must not
    divide by it.
    """
    inner = s._inner
    attr_evals, attr_defaulted = inner.fallback_attr_totals()
    return {
        "rule_costs": [
            {"rule": n, "micros": m, "count": c, "progress": p}
            for (n, m, c, p) in inner.rule_costs()
        ],
        "defaulted_reads": [
            {"rule": r, "key": k, "hits": h} for (r, k, h) in inner.defaulted_reads()
        ],
        "absence_branches": [
            {"rule": r, "hits": h} for (r, h) in inner.absence_branches()
        ],
        "attr_evals": attr_evals,
        "attr_defaulted": attr_defaulted,
    }


def mint_report(s, agent=None) -> dict[str, Any]:
    """Materialise the engine tallies as graph data, then let the RULES decide.

    Mechanical throughout: every node minted here is a transcription of a
    counter the engine already holds. The `status` attribute is deliberately
    NOT set — `seeds/fallback_vocabulary.json` sets it, which is the whole
    point (the decision is graph-resident).

    Returns the ingest counts so a caller can positive-control that anything
    was minted at all — a reader that mints nothing scores a perfect floor on
    every downstream question (§1 clause 4).
    """
    tallies = engine_tallies(s)

    rep = s.add_node(REPORT_TYPE, {"name": "fallback_report"})

    # One RuleActivity per rule the engine knows about. Transcription only.
    activity: dict[str, Any] = {}
    for rc in tallies["rule_costs"]:
        nid = s.add_node(
            ACTIVITY_TYPE,
            {"rule": rc["rule"], "progress": rc["progress"], "count": rc["count"]},
        )
        s.add_edge(rep, EDGE_ACTIVITY, nid)
        activity[rc["rule"]] = nid

    # One DefaultedRead per (rule, key) the engine recorded as missing.
    n_defaulted = 0
    for d in tallies["defaulted_reads"]:
        nid = s.add_node(
            DEFAULTED_TYPE,
            {"rule": d["rule"], "key": d["key"], "hits": d["hits"]},
        )
        owner = activity.get(d["rule"])
        # `owner is None` can only happen if the engine attributed a read to a
        # rule that is no longer installed. Transcribe it under the report
        # rather than inventing an owner.
        s.add_edge(owner if owner is not None else rep, EDGE_DEFAULTED, nid)
        n_defaulted += 1

    n_absence = 0
    for a in tallies["absence_branches"]:
        nid = s.add_node(ABSENCE_TYPE, {"rule": a["rule"], "hits": a["hits"]})
        owner = activity.get(a["rule"])
        s.add_edge(owner if owner is not None else rep, EDGE_ABSENCE, nid)
        n_absence += 1

    # Hand off to the graph. The seed rules classify; this adapter does not.
    # The tallies were transcribed into nodes ABOVE, so the report is a
    # snapshot: any further defaulted reads produced by this very fixpoint land
    # in the engine's live tally, not retroactively in the report. That keeps
    # the reader from measuring itself.
    s._inner.run_rules()
    s.add_node("NativeFallbackReadoutReceipt", {
        "schema": "native_fallback_readout_receipt_v1",
        "cluster": "fallback_readout.report_classification",
        "provenance": "native_rule_readback:fallback_vocabulary",
        "native_rule": "fallback_vocabulary_native_classification",
        "native_steps": ["transcribe_tallies", "run_rules"],
        "outcome_source": "native_rule_readback",
        "python_outcome_selection": False,
    })

    return {
        "report_node": rep,
        "n_activity": len(activity),
        "n_defaulted": n_defaulted,
        "n_absence": n_absence,
        "attr_evals": tallies["attr_evals"],
        "attr_defaulted": tallies["attr_defaulted"],
    }


def read_statuses(s) -> list[dict[str, Any]]:
    """Emit: read the classified RuleActivity nodes back out.

    Pure mechanical query. The `status` values were written by the seed rules,
    not here.
    """
    out = []
    for nid in s.nodes(ACTIVITY_TYPE):
        attrs = s.node(nid)["attrs"]
        out.append(
            {
                "rule": attrs.get("rule"),
                "progress": attrs.get("progress"),
                "count": attrs.get("count"),
                "status": attrs.get("status"),
            }
        )
    return out


def surface(s) -> dict[str, Any]:
    """The reader the rung ships: what did this substrate do, and on what?

    Groups the classified activity by the status the RULES assigned. This is
    the answer the redundancy audit could not get — it saw one undifferentiated
    "no test loss" where there are three materially different states.
    """
    rows = read_statuses(s)
    by_status: dict[str, list[str]] = {}
    for r in rows:
        by_status.setdefault(str(r["status"]), []).append(str(r["rule"]))
    for v in by_status.values():
        v.sort()

    defaulted = [
        {
            "rule": s.node(n)["attrs"].get("rule"),
            "key": s.node(n)["attrs"].get("key"),
            "hits": s.node(n)["attrs"].get("hits"),
        }
        for n in s.nodes(DEFAULTED_TYPE)
    ]
    defaulted.sort(key=lambda d: (-int(d["hits"] or 0), str(d["rule"]), str(d["key"])))

    return {
        "by_status": {k: sorted(v) for k, v in sorted(by_status.items())},
        "counts": {k: len(v) for k, v in sorted(by_status.items())},
        "defaulted_reads": defaulted,
        "absence_branches": sorted(
            (
                {
                    "rule": s.node(n)["attrs"].get("rule"),
                    "hits": s.node(n)["attrs"].get("hits"),
                }
                for n in s.nodes(ABSENCE_TYPE)
            ),
            key=lambda d: (-int(d["hits"] or 0), str(d["rule"])),
        ),
    }


def render(s) -> str:
    """Natural-language surfacing, for a human or a log.

    Mechanical formatting of `surface()`. The honest floor matters here: when
    nothing degraded, the reader says so explicitly rather than printing an
    empty section that reads the same as a reader that is broken.
    """
    v = surface(s)
    counts = v["counts"]
    lines = [
        "FALLBACK REPORT",
        f"  healthy  (ran on real inputs)      : {counts.get('healthy', 0)}",
        f"  degraded (ran on values nobody wrote): {counts.get('degraded', 0)}",
        f"  silent   (nothing ran)             : {counts.get('silent', 0)}",
    ]
    lines.append("  defaulted reads:")
    for d in v["defaulted_reads"][:20]:
        lines.append(f"    {d['rule']} read '{d['key']}' x{d['hits']} — nobody wrote it")
    lines.append(f"    (none)" if not v["defaulted_reads"] else "")
    return "\n".join(x for x in lines if x != "")
