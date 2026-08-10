"""Paper reader — Jabberwock reads a paper directly + ingests its
structure as graph data.

Per user: 'or just have it read the paper'.

The paper Jabberwock was built to prove (Paper 1 — The Law of
Graphic Equalisation) is held as THEORY, not as foundation. The
distinction: a foundational Mt is something Jabberwock builds FROM;
a theory Mt is something Jabberwock can introspect, reason about,
and potentially test or refute.

Marker attrs on the resulting Mt + nodes:
  is_theory_under_test = True
  is_foundation = False

Jabberwock can answer:
  Q: What is this paper?
  A: The theory I was built to test/demonstrate.

  Q: Do I assume the theory is true?
  A: No. The paper is held as theory. My operational behavior is
     the empirical test. If I operate as Paper 1 predicts, that is
     evidence for the paper, not proof; if I operate against its
     predictions, that is evidence against it.

The reader parses markdown structure: sections, axioms, theorems,
hypotheses, falsifiability commitments. Each becomes a typed node.
The paper's own text is preserved verbatim — no paraphrase, no my-
interpretation.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def _read(path: Path) -> str:
    return path.read_text()


def _parse_sections(text: str) -> list[dict]:
    """Parse markdown into sections by header level."""
    lines = text.split("\n")
    sections = []
    current = None
    for line in lines:
        m = re.match(r"^(#+)\s+(.*?)$", line)
        if m:
            if current is not None:
                sections.append(current)
            level = len(m.group(1))
            title = m.group(2).strip()
            current = {"level": level, "title": title,
                       "content_lines": [], "raw_header": line}
        else:
            if current is not None:
                current["content_lines"].append(line)
    if current is not None:
        sections.append(current)
    return sections


_FORMAL_PATTERNS = [
    (r"\*\*Axiom\s+(\d+|\w+)\s*\(([^)]+)\)\.\*\*",
     "PaperAxiom"),
    (r"\*\*Theorem\s+(\w+)\s*\(([^)]+)\)\.\*\*",
     "PaperTheorem"),
    (r"\*\*Conjecture\s+(\w+)\s*\(([^)]+)\)\.\*\*",
     "PaperConjecture"),
    (r"\*\*Hypothesis\s+([\w-]+)\s*\(?([^)]*)\)?\.\*\*",
     "PaperHypothesis"),
    (r"\*\*Hypothesis\.\*\*",
     "PaperHypothesis"),
]

# Pattern for formal objects in SECTION HEADERS (Paper 1 puts most
# theorems in headers: '### 4.1 Theorem A (Monotone improvement...)')
_HEADER_FORMAL_PATTERNS = [
    (r"Axiom\s+(\d+|\w+)\s*\(([^)]+)\)",       "PaperAxiom"),
    (r"Theorem\s+(\w+)\s*\(([^)]+)\)",         "PaperTheorem"),
    (r"Conjecture\s+(\w+)\s*\(([^)]+)\)",      "PaperConjecture"),
    (r"Hypothesis\s+([\w-]+)\s*\(?([^)]*)\)?", "PaperHypothesis"),
]


def _extract_formal_objects(content: str) -> list[dict]:
    """Find Axiom / Theorem / Conjecture / Hypothesis in a section."""
    out = []
    paragraphs = re.split(r"\n\s*\n", content)
    for para in paragraphs:
        ps = para.strip()
        if not ps:
            continue
        for pattern, node_type in _FORMAL_PATTERNS:
            m = re.search(pattern, ps)
            if m:
                label = m.group(1) if m.lastindex else ""
                title = m.group(2) if m.lastindex and m.lastindex >= 2 else ""
                out.append({
                    "node_type": node_type,
                    "label": str(label),
                    "title": str(title),
                    "text": ps[:2500],
                })
                break
    return out


def install_paper_as_theory(substrate, paper_path: Path,
                              paper_id: str,
                              paper_title: str = "") -> Any | None:
    """Read a paper from markdown + install it as a graph subgraph
    rooted at a PaperTheory Mt. The Mt is marked is_theory_under_test
    so Jabberwock holds it as theory, not foundation."""
    text = _read(paper_path)
    sections = _parse_sections(text)

    # Determine title from first H1 if not given.
    if not paper_title and sections:
        for s in sections:
            if s["level"] == 1:
                paper_title = s["title"]
                break

    # Mt for the paper as theory-under-test
    try:
        paper_mt = substrate.add_node("Microtheory", {
            "name": f"paper_{paper_id}_theory",
            "definition": (
                f"Paper '{paper_title}' as theory Jabberwock was built "
                f"to test/demonstrate. Held as THEORY, not as "
                f"foundation. Jabberwock's operational behavior is the "
                f"empirical test of this paper's predictions. Loading "
                f"this Mt does NOT commit Jabberwock to the paper's "
                f"truth — it commits Jabberwock to knowing what the "
                f"paper claims so it can be tested. Path: "
                f"{paper_path.name}."
            ),
            "category": "theory_under_test",
            "update_policy": "frozen",
            "is_theory_under_test": True,
            "is_foundation": False,
            "paper_id": paper_id,
            "paper_title": paper_title,
            "paper_path": str(paper_path),
        })
    except Exception:
        return None

    # Paper node
    try:
        paper_node = substrate.add_node("Paper", {
            "paper_id": paper_id,
            "title": paper_title,
            "path": str(paper_path),
            "total_lines": len(text.split("\n")),
            "n_sections": len(sections),
            "is_theory_under_test": True,
        })
        substrate.add_edge(paper_mt, "owns_paper", paper_node, {})
    except Exception:
        paper_node = None

    # Section nodes (preserved verbatim)
    section_nodes = []
    for s in sections:
        try:
            content_text = "\n".join(s["content_lines"]).strip()
            sn = substrate.add_node("PaperSection", {
                "title": s["title"],
                "level": s["level"],
                "paper_id": paper_id,
                "text": content_text[:5000],
                "full_length": len(content_text),
            })
            substrate.add_edge(paper_mt, "has_section", sn, {})
            section_nodes.append((s, sn))

            # Extract formal objects within section
            formal_objects = _extract_formal_objects(content_text)
            # Also check the section TITLE for formal objects
            # (Paper 1 puts many theorems in section headers)
            for pattern, node_type in _HEADER_FORMAL_PATTERNS:
                m = re.search(pattern, s["title"])
                if m:
                    label = m.group(1) if m.lastindex else ""
                    title = (m.group(2) if m.lastindex and
                              m.lastindex >= 2 else "")
                    formal_objects.append({
                        "node_type": node_type,
                        "label": str(label),
                        "title": str(title),
                        "text": content_text[:2500],
                        "from_header": True,
                    })
                    break
            for obj in formal_objects:
                try:
                    on = substrate.add_node(obj["node_type"], {
                        "label": obj["label"],
                        "title": obj["title"],
                        "text": obj["text"],
                        "paper_id": paper_id,
                        "section_title": s["title"],
                        "is_theory_under_test": True,
                    })
                    substrate.add_edge(sn, "states", on, {})
                    substrate.add_edge(paper_mt, "contains_claim",
                                       on, {})
                except Exception:
                    pass
        except Exception:
            continue

    # Rules — the paper-as-theory commits the substrate to one
    # thing: knowing the paper exists + that it's held as theory.
    for rule_data in [
        {
            "name": "paper_held_as_theory_not_foundation",
            "head": f"Jabberwock is asked about paper '{paper_title}'",
            "body": ("the paper is held as theory under test, NOT as "
                     "foundational truth. Jabberwock's operational "
                     "behavior is what tests it."),
        },
        {
            "name": "operating_as_predicted_is_evidence_not_proof",
            "head": f"Jabberwock operates in accordance with paper '{paper_title}'",
            "body": ("that constitutes empirical evidence for the "
                     "paper's predictions, not proof of the paper's "
                     "axioms."),
        },
        {
            "name": "operating_against_prediction_is_falsification",
            "head": f"Jabberwock operates against paper '{paper_title}'",
            "body": ("that constitutes evidence against the paper. "
                     "The paper's section on Falsifiability "
                     "Commitments names what such evidence would "
                     "look like."),
        },
    ]:
        try:
            rn = substrate.add_node("Rule", rule_data)
            substrate.add_edge(paper_mt, "has_rule", rn, {})
        except Exception:
            pass

    return paper_mt


def install_paper1_as_theory(substrate) -> Any | None:
    """Install Paper 1 — The Law of Graphic Equalisation —
    as theory Jabberwock was built to test."""
    paths = [
        Path("/home/matt/ozma/internal/research/docs/"
             "graphs_paper_1_theory_only.md"),
        Path("/home/matt/ozma/internal/research/docs/paper1-cut.md"),
    ]
    for p in paths:
        if p.exists():
            return install_paper_as_theory(
                substrate, p, paper_id="paper1",
                paper_title="The Law of Graphic Equalisation")
    return None


__all__ = ["install_paper_as_theory", "install_paper1_as_theory"]
