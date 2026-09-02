#!/usr/bin/env python3
r"""Check the formal paper set for draft-string and revision inconsistencies.

Six defects this catches, all of which have actually occurred:

  1. Two documents on different draft strings (the set is bumped together, so a
     reader comparing two papers is never comparing two drafts).
  2. A document whose per-page footer or boxed DRAFT notice carries a revision
     that disagrees with its title block --- the footer is hand-maintained and a
     revision bump can miss it.
  3. A document carrying no footer or notice at all, while README says all of
     them do.
  4. Typesetting overflow: a display or line running more than 20pt past the
     margin, which is visible in the PDF and has shipped before.
  6. Text changed under an UNCHANGED revision number. Every paper's notice tells
     a reader to cite its version string, so two different texts sharing one
     string is the defect that string exists to prevent. Neither this checker
     nor the release gate could see it before: both compared a document against
     ITSELF (title block vs footer, PDF footer vs source) and those agreed. It
     took a manifest of content hashes to ask the question that mattered --
     "is this the same text r27 named yesterday?" Cost: five cleared papers
     edited without a bump, caught by hand while preparing a release.
  5. Revision-history language: a document narrating its own drafting ("an
     earlier version of this remark claimed ..."). A paper is what it says
     now; what a draft used to say subtracts. Scanned on FLATTENED text,
     because line-based grep for these phrases missed 3 of 12 real sites ---
     "an earlier\ndraft" and "and earlier\nversions" are invisible to it.

Not a defect, and deliberately not checked: the generated statement carries
\bibitem entries with no \cite commands, because the generator flattens
citations to author-year text and then emits the reference list so a reader can
resolve them. Every one of its entries is an "orphan" by a naive check and all
of them are correct.

Exits non-zero on any finding. Run from anywhere:
    python3 tools/check_draft_consistency.py
"""
import hashlib
import json
import re
import sys
from pathlib import Path

FORMAL = Path(__file__).resolve().parent.parent / "papers" / "formal"
DRAFT_RE = re.compile(r"draft-\d{4}-\d{2}-\d{2}(?:\.\d+)?")
DATE_REV_RE = re.compile(r"document revision (\d+)")
FOOT_REV_RE = re.compile(r"draft-\d{4}-\d{2}-\d{2}(?:\.\d+)?[\s,/\\]*r(\d+)")

def main() -> int:
    problems = []
    drafts = {}
    for tex in sorted(FORMAL.glob("*.tex")):
        src = tex.read_text(encoding="utf-8")
        name = tex.name

        found = set(DRAFT_RE.findall(src))
        if not found:
            problems.append(f"{name}: carries no draft string at all")
            continue
        if len(found) > 1:
            problems.append(f"{name}: mixed draft strings within one file: {sorted(found)}")
        drafts[name] = sorted(found)[0]

        # 01s is generated and tracks the long paper's revision, not its own.
        if name.startswith("01s"):
            continue

        date_rev = DATE_REV_RE.search(src)
        if not date_rev:
            problems.append(f"{name}: title block carries no 'document revision N'")
            continue
        want = date_rev.group(1)

        foot_revs = set(FOOT_REV_RE.findall(src))
        if not foot_revs:
            problems.append(
                f"{name}: no footer/notice revision found "
                f"(title says r{want}) --- missing fancyhdr footer or DRAFT box?"
            )
        elif foot_revs != {want}:
            problems.append(
                f"{name}: title says r{want} but footer/notice says "
                f"{', '.join('r' + r for r in sorted(foot_revs))}"
            )

    # The title block and the notice box each carry a date, and a bump that
    # rewrites one form and not the other leaves a document showing two.
    # Nothing above catches it: the draft string and the revision both agree.
    # Cost one defect, which shipped.
    dates = {}
    for tex in sorted(FORMAL.glob("*.tex")):
        src = tex.read_text(encoding="utf-8")
        # Front matter only. Dates in the body are citations and are content:
        # scanning the whole file flags a paper for quoting a report's date.
        head = src.split(r"\begin{abstract}")[0].split(r"\section{")[0]
        found = set(re.findall(r"\d{1,2} (?:January|February|March|April|May|June|July|"
                              r"August|September|October|November|December) \d{4}", head))
        if len(found) > 1:
            problems.append(f"{tex.name}: shows more than one date: {sorted(found)}")
        elif found:
            dates[tex.name] = found.pop()
    if len(set(dates.values())) > 1:
        by_date = {}
        for n, d in dates.items():
            by_date.setdefault(d, []).append(n)
        problems.append("the set is not on one date: "
                        + "; ".join(f"{d} -> {len(v)} file(s)"
                                    for d, v in sorted(by_date.items())))

    # Generator inputs carry the draft string too, and are not .tex, so a
    # set-wide bump done over *.tex leaves them behind. That stays invisible
    # until somebody regenerates, at which point the stale string comes back
    # into a document that was already checked and passed. Cost one defect.
    for other in sorted(FORMAL.iterdir()):
        if other.suffix in (".tex", ".pdf", ".log", ".aux", ".out", ".toc") or other.is_dir():
            continue
        found = set(DRAFT_RE.findall(other.read_text(encoding="utf-8", errors="replace")))
        if found and (len(found) > 1 or (drafts and found != {sorted(drafts.values())[0]})):
            problems.append(
                f"{other.name}: generator input carries {sorted(found)} "
                f"but the documents are on {sorted(set(drafts.values()))} "
                f"--- regenerating from it would reintroduce the old string"
            )

    if len(set(drafts.values())) > 1:
        by_draft = {}
        for n, d in drafts.items():
            by_draft.setdefault(d, []).append(n)
        problems.append(
            "the set is not on one draft string: "
            + "; ".join(f"{d} -> {len(v)} file(s): {', '.join(sorted(v))}"
                        for d, v in sorted(by_draft.items()))
        )

    # A paper is what it says now. Narrating a superseded draft ("an earlier
    # version of this remark claimed ...") reads as candour and is errata: the
    # distinction it was marking is always statable directly, and stating it
    # directly is shorter. Flattened, because these phrases wrap: a line-based
    # sweep reported the set clean while three sites remained, and the PDFs
    # caught what the source scan had missed. Cost twelve sites across seven
    # documents.
    HIST = re.compile(
        r"earlier\s+versions?|earlier\s+drafts?|previous\s+versions?|"
        r"previous\s+drafts?|revised\s+label|older\s+reading|"
        r"earlier\s+statement\s+of\s+this|an\s+earlier\s+remark"
    )
    for doc in sorted(list(FORMAL.glob("*.tex")) + list(FORMAL.glob("*.spec"))):
        flat = re.sub(r"\s+", " ", doc.read_text(encoding="utf-8", errors="replace"))
        for m in HIST.finditer(flat):
            problems.append(
                f"{doc.name}: revision-history language --- "
                f"\"...{flat[max(0, m.start() - 45):m.end() + 45]}...\""
            )

    for log in sorted(FORMAL.glob("*.log")):
        txt = log.read_text(encoding="utf-8", errors="replace")
        bad = [float(x) for x in re.findall(r"Overfull \\hbox \((\d+\.?\d*)pt", txt)]
        bad = [x for x in bad if x > 20]
        if bad:
            problems.append(
                f"{log.stem}: {len(bad)} display(s) over the margin by more than 20pt "
                f"(worst {max(bad):.0f}pt) --- visible in the PDF"
            )

    # Content-vs-revision. The manifest records what each revision NAMED; a
    # bump updates it silently, an edit without one does not. Only the
    # offending entry is withheld from the update, so the guard keeps firing
    # until the revision moves rather than forgiving itself on the next run.
    man_path = FORMAL / ".revisions.json"
    try:
        manifest = json.loads(man_path.read_text(encoding="utf-8"))
    except Exception:
        manifest = {}
    for tex in sorted(FORMAL.glob("*.tex")):
        src = tex.read_text(encoding="utf-8")
        rev = DATE_REV_RE.search(src)
        rev = rev.group(1) if rev else None
        # Hash the text with every version string normalised out, so a bump
        # alone is never mistaken for a content change.
        body = DRAFT_RE.sub("", re.sub(r"document revision \d+", "", src))
        body = re.sub(r"\br\d+\b", "", body)
        digest = hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]
        prev = manifest.get(tex.name)
        if prev and prev.get("rev") == rev and prev.get("hash") != digest:
            problems.append(
                f"{tex.name}: text changed but revision stayed at r{rev} "
                f"--- two different texts now answer to one version string; bump it"
            )
            continue
        manifest[tex.name] = {"rev": rev, "hash": digest}
    man_path.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n", encoding="utf-8")

    if problems:
        print(f"draft consistency: {len(problems)} problem(s)\n")
        for p in problems:
            print("  " + p)
        return 1
    print(f"draft consistency: OK ({len(drafts)} documents, all on {sorted(set(drafts.values()))[0]})")
    return 0

if __name__ == "__main__":
    sys.exit(main())
