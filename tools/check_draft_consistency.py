#!/usr/bin/env python3
"""Check generated paper metadata, structural use, and release-facing hygiene.

paper_metadata.json is the only editable version authority. The checked
paper_metadata.tex include renders that authority into every formal paper; this
checker rejects stale generated metadata, handwritten version strings, missing
macro use, unbumped text changes, visible overflow, revision-history prose, and
new bibliography ordering defects.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

from build_paper_metadata import FORMAL, INCLUDE, MANIFEST, load_manifest, render, revision_for

DRAFT_RE = re.compile(r"draft-\d{4}-\d{2}-\d{2}(?:\.\d+)?")
DATE_REV_RE = re.compile(r"document revision \d+")
HIST = re.compile(
    r"earlier\s+versions?|earlier\s+drafts?|previous\s+versions?|"
    r"previous\s+drafts?|revised\s+label|older\s+reading|"
    r"earlier\s+statement\s+of\s+this|an\s+earlier\s+remark"
)


def head_manifest():
    old = subprocess.run(
        ["git", "show", "HEAD:papers/formal/paper_metadata.json"],
        cwd=FORMAL.parent.parent, capture_output=True, text=True,
    )
    if old.returncode:
        return None
    try:
        return json.loads(old.stdout)
    except json.JSONDecodeError:
        return None


def normalise_version(text):
    text = DRAFT_RE.sub("<draft>", text)
    text = DATE_REV_RE.sub("document revision <revision>", text)
    text = re.sub(r"\br\d+\b", "r<revision>", text)
    text = text.replace(r"\PaperDraft", "<draft>")
    text = text.replace(r"\PaperDisplayDate", "<date>")
    text = text.replace(r"\PaperRevision", "<revision>")
    return text


def surname(label):
    lead = label.split("(")[0].replace("~", " ")
    lead = re.split(r" and | et al\.", lead)[0]
    lead = re.sub(r"\\[A-Za-z]+", "", lead)
    return re.sub(r"[^A-Za-z]", "", lead).lower()


def main() -> int:
    problems = []
    try:
        data = load_manifest()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print("draft consistency: invalid manifest: %s" % exc)
        return 1

    expected = render(data)
    if not INCLUDE.exists() or INCLUDE.read_text(encoding="utf-8") != expected:
        problems.append("paper_metadata.tex is missing or stale; run tools/build_paper_metadata.py")

    expected_stems = set(data["papers"])
    source_stems = {
        p.stem for p in FORMAL.glob("*.tex")
        if p.name not in {"paper_metadata.tex", "01.counts.tex"}
        and not p.name.endswith(".counts.tex")
    }
    missing, extra = expected_stems - source_stems, source_stems - expected_stems
    if missing:
        problems.append("manifest papers missing source(s): " + ", ".join(sorted(missing)))
    if extra:
        problems.append("formal source(s) missing manifest entry: " + ", ".join(sorted(extra)))

    for stem in sorted(expected_stems & source_stems):
        path = FORMAL / (stem + ".tex")
        src = path.read_text(encoding="utf-8")
        if r"\input{paper_metadata.tex}" not in src:
            problems.append("%s: does not input paper_metadata.tex" % path.name)
        if DRAFT_RE.search(src) or DATE_REV_RE.search(src):
            problems.append("%s: retains handwritten draft or revision metadata" % path.name)
        for line_number, line in enumerate(src.splitlines(), 1):
            if r"\PaperDisplayDate" in line and not (
                line.lstrip().startswith(r"\date{") or r"\PaperDraft" in line
            ):
                problems.append("%s:%d: document date macro used as a source/event date" %
                                (path.name, line_number))
        required = (r"\PaperDraft", r"\PaperDisplayDate", r"\PaperRevision")
        if stem == "01s_graphic_equalisation_statement":
            required = (r"\PaperFooterStamp",)
        absent = [macro for macro in required if macro not in src]
        if absent:
            problems.append("%s: does not use generated metadata macro(s): %s" %
                            (path.name, ", ".join(absent)))

    spec = FORMAL / "01s.spec"
    if DRAFT_RE.search(spec.read_text(encoding="utf-8")) or r"\PaperStatementDateLine" not in spec.read_text(encoding="utf-8"):
        problems.append("01s.spec: must use generated PaperStatementDateLine, not a handwritten draft")

    # The global draft is a declared release boundary. Within an unchanged global
    # draft, document text may change only when that document's manifest revision
    # changes. The first manifest migration has no HEAD manifest and is exempt.
    old_data = head_manifest()
    if old_data and old_data.get("draft") == data["draft"]:
        for stem in sorted(expected_stems & source_stems):
            if stem not in old_data.get("papers", {}):
                continue
            try:
                old_rev = revision_for(old_data, stem)
            except (KeyError, ValueError):
                continue
            if old_rev != revision_for(data, stem):
                continue
            rel = "papers/formal/%s.tex" % stem
            old = subprocess.run(["git", "show", "HEAD:" + rel], cwd=FORMAL.parent.parent,
                                 capture_output=True, text=True)
            if old.returncode:
                continue
            current = (FORMAL / (stem + ".tex")).read_text(encoding="utf-8")
            if normalise_version(current) != normalise_version(old.stdout):
                problems.append("%s: text differs from HEAD but manifest revision remains r%s" %
                                (stem + ".tex", old_rev))

    for doc in sorted(list(FORMAL.glob("*.tex")) + list(FORMAL.glob("*.spec"))):
        if doc.name == "paper_metadata.tex":
            continue
        flat = re.sub(r"\s+", " ", doc.read_text(encoding="utf-8", errors="replace"))
        for match in HIST.finditer(flat):
            problems.append('%s: revision-history language --- "...%s..."' %
                            (doc.name, flat[max(0, match.start() - 45):match.end() + 45]))

    for log in sorted(FORMAL.glob("*.log")):
        values = [float(value) for value in re.findall(r"Overfull \\hbox \((\d+\.?\d*)pt", log.read_text(encoding="utf-8", errors="replace"))]
        values = [value for value in values if value > 20]
        if values:
            problems.append("%s: %d display(s) over the margin by more than 20pt (worst %.0fpt)" %
                            (log.stem, len(values), max(values)))

    baseline_path = FORMAL / "bib_order_baseline.txt"
    baseline = set()
    if baseline_path.exists():
        baseline = {line.strip() for line in baseline_path.read_text(encoding="utf-8").splitlines()
                    if line.strip() and not line.startswith("#")}
    for tex in sorted(FORMAL.glob("*.tex")):
        labels = re.findall(r"\\bibitem\[([^\]]*)\]", tex.read_text(encoding="utf-8"))
        keys = [surname(label) for label in labels]
        for index in range(1, len(keys)):
            if keys[index] and keys[index - 1] and keys[index] < keys[index - 1]:
                entry = "%s::%s" % (tex.name, labels[index])
                if entry not in baseline:
                    problems.append("%s: bibliography out of order --- '%s' follows '%s' (new; not in baseline)" %
                                    (tex.name, labels[index], labels[index - 1]))

    if problems:
        print("draft consistency: %d problem(s)\n" % len(problems))
        for problem in problems:
            print("  " + problem)
        return 1
    print("draft consistency: OK (%d documents, generated %s)" %
          (len(expected_stems), data["draft"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
