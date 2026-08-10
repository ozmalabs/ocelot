"""ArchitectureCortex — the agent's faculty for assessing its own
(or any) architectural shape.

Same shape as `SpeechCortex` and `CodeWritingCortex`: a Cortex graph
node, ownership edges to an Mt + concepts, a small reflex loop,
intrinsic `tick()`. The reasoning is the qualities and smells stored
as `ArchitecturalQuality`/`ArchitecturalSmell` graph nodes; the
cortex orchestrates queries against them.

  assess_subject(subject_nid):
    cw_choose_subject   — pick what to assess (default: caller-supplied)
    cw_score_qualities  — run every quality's graph query → QualityScore
    cw_detect_smells    — pattern-match every smell → SmellInstance
    cw_synthesize_report — bundle into an `Assessment` node with edges

Output is graph-resident: an `Assessment` node with `scored_on` edges
to each `QualityScore`, `detected_smell` edges to each `SmellInstance`,
and an `assesses` edge to the subject. The agent (or the code-writing
cortex) reads the assessment to decide what to fix next.
"""
from __future__ import annotations

import time
from pathlib import Path

from .architecture_assessment import (
    detect_all_smells,
    install_architecture_mt,
    score_all_qualities,
)


_AC_PRODUCTIONS = [
    ("ArchitectureCortex", "owns_microtheory", "Microtheory",
     "architecture_cortex:owns_mt"),
    ("ArchitectureCortex", "assesses", "CodeWritingCortex",
     "architecture_cortex:assesses_cw"),
    ("ArchitectureCortex", "assesses", "SpeechCortex",
     "architecture_cortex:assesses_speech"),
    ("ArchitectureCortex", "produced", "Assessment",
     "architecture_cortex:produced"),
    ("Assessment", "assesses", "CodeWritingCortex",
     "architecture_cortex:assess_subject_cw"),
    ("Assessment", "assesses", "SpeechCortex",
     "architecture_cortex:assess_subject_speech"),
    ("Assessment", "assesses", "ArchitectureCortex",
     "architecture_cortex:assess_subject_self"),
    ("Assessment", "scored_on", "QualityScore",
     "architecture_cortex:scored_on"),
    ("Assessment", "detected_smell", "SmellInstance",
     "architecture_cortex:detected_smell"),
    ("QualityScore", "for_quality", "ArchitecturalQuality",
     "architecture_cortex:for_quality"),
    ("SmellInstance", "for_smell", "ArchitecturalSmell",
     "architecture_cortex:for_smell"),
]


class ArchitectureCortex:
    """The agent's intrinsic architecture-assessment faculty."""

    def __init__(self, substrate):
        self.s = substrate
        self.cortex_nid: int | None = None
        self._installed = False

    def install(self) -> "ArchitectureCortex":
        for src_t, et, tgt_t, prov in _AC_PRODUCTIONS:
            try:
                self.s.add_production({
                    "src": {"type": src_t, "var": "src"},
                    "edge_type": et,
                    "tgt": {"type": tgt_t, "var": "tgt"},
                    "where": None,
                    "weight": {"type": "Lit", "value": 1.0},
                    "provenance": prov,
                })
            except Exception:
                pass

        existing = None
        for n in self.s.nodes("ArchitectureCortex"):
            existing = n
            break
        if existing is None:
            self.cortex_nid = self.s.add_node("ArchitectureCortex", {
                "origin": "architecture_cortex",
            })
        else:
            self.cortex_nid = existing

        mt = install_architecture_mt(self.s)
        try:
            self.s.add_edge(self.cortex_nid, "owns_microtheory", mt, {})
        except Exception:
            pass
        self._installed = True
        return self

    def assess(self, subject_nid: int) -> int:
        """Run the assessment loop on `subject_nid`. Returns the
        Assessment NodeID. The Assessment + its QualityScore +
        SmellInstance children + the `scored_on` / `detected_smell`
        edges are all graph-resident."""
        if not self._installed:
            raise RuntimeError("ArchitectureCortex.install() not called")

        # Score every quality.
        scores = score_all_qualities(self.s, subject_nid)
        # Detect every smell.
        smells = detect_all_smells(self.s, subject_nid)

        # Synthesise: an Assessment node + edges.
        total = sum(int(s["score"]) for s in scores)
        max_total = sum(int(s["max_score"]) for s in scores)
        overall_pct = (total / max_total * 100) if max_total else 0.0
        assessment = self.s.add_node("Assessment", {
            "total_score": total,
            "max_total_score": max_total,
            "overall_pct": round(overall_pct, 1),
            "smell_count": len(smells),
            "n_qualities": len(scores),
            "assessed_at": time.time(),
            "origin": "architecture_cortex",
        })
        try:
            self.s.add_edge(self.cortex_nid, "produced", assessment, {})
            self.s.add_edge(assessment, "assesses", subject_nid, {})
        except Exception:
            pass

        for sc in scores:
            qs = self.s.add_node("QualityScore", {
                "quality_name": sc["quality_name"],
                "score": sc["score"],
                "max_score": sc["max_score"],
                "rationale": sc["rationale"],
                "origin": "architecture_cortex",
            })
            try:
                self.s.add_edge(assessment, "scored_on", qs, {})
                self.s.add_edge(qs, "for_quality", sc["quality_nid"], {})
            except Exception:
                pass

        for sm in smells:
            si = self.s.add_node("SmellInstance", {
                "smell_name": sm["smell_name"],
                "location": sm["location"],
                "rationale": sm["rationale"],
                "origin": "architecture_cortex",
            })
            try:
                self.s.add_edge(assessment, "detected_smell", si, {})
                self.s.add_edge(si, "for_smell", sm["smell_nid"], {})
            except Exception:
                pass

        return assessment

    def render_assessment(self, assessment_nid: int) -> str:
        """Format an assessment for human inspection — read from the
        graph, not from local state."""
        a = self.s.node(assessment_nid)["attrs"]
        lines = [
            f"=== Architecture Assessment ===",
            f"overall: {a['total_score']}/{a['max_total_score']}  "
            f"({a['overall_pct']}%)",
            f"qualities scored: {a['n_qualities']}  "
            f"smells detected: {a['smell_count']}",
            "",
            "--- quality scores ---",
        ]
        for qs in self.s.neighbours(assessment_nid, "scored_on"):
            x = self.s.node(qs)["attrs"]
            lines.append(
                f"  {x['quality_name']:<28} "
                f"{x['score']:>2}/{x['max_score']}  "
                f"{x['rationale']}"
            )
        smells = list(self.s.neighbours(assessment_nid, "detected_smell"))
        lines.append("")
        lines.append(f"--- smells ---")
        if not smells:
            lines.append("  (none)")
        for si in smells:
            x = self.s.node(si)["attrs"]
            lines.append(
                f"  [{x['smell_name']}] {x['location']} — {x['rationale']}")
        return "\n".join(lines)


__all__ = ["ArchitectureCortex"]
