#!/usr/bin/env python3
r"""Make a paper round cheap, because the round is not avoidable.

Three operations, each of which was hand-rolled once per round until it wasn't:

  grep   Flattened, whitespace-agnostic search over sources AND rendered PDFs.
         Line-based grep cannot see a phrase that wraps, and this set wraps
         constantly. Measured cost of not having this: five false negatives in
         one session, one of which reported the whole set clean while three
         sites remained. Searching the PDF as well is the other half -- source
         and render disagree via hyphenation, curly quotes and page footers,
         and all three have produced phantom findings.

  build  Compile named papers three passes, fail loudly on the first error,
         report pages and words. Three passes because cross-references need
         them; the count is not negotiable and was forgotten by hand at least
         once.

  round  build + the draft-consistency checker, which is the whole
         pre-commit gate. One command instead of five.

Usage:
    python3 tools/papers.py grep "some phrase" [--src|--pdf] [--re]
    python3 tools/papers.py build [stem ...]        (default: all changed)
    python3 tools/papers.py round [stem ...]
"""
import argparse, hashlib, io, json, re, subprocess, sys
from pathlib import Path

FORMAL = Path(__file__).resolve().parent.parent / "papers" / "formal"
FOOTER = re.compile(r"\d+ draft-[\d.\-]+ r\d+ ")

def flatten(text, pdf=False):
    """Normalise so a phrase matches whether it wrapped, hyphenated, or not."""
    text = text.replace("-\n", "").replace("’", "'").replace("‘", "'")
    text = re.sub(r"\s+", " ", text)
    return FOOTER.sub("", text) if pdf else text

def pdf_text(p):
    r = subprocess.run(["pdftotext", "-nopgbrk", str(p), "-"],
                       capture_output=True, text=True)
    return r.stdout

def cmd_grep(a):
    pat = re.compile(a.pattern if a.re else r"\s+".join(
        re.escape(w) for w in a.pattern.split()))
    want_src = a.src or not a.pdf
    want_pdf = a.pdf or not a.src
    hits = 0
    for f in sorted(list(FORMAL.glob("*.tex")) + list(FORMAL.glob("*.spec"))):
        if not want_src:
            break
        flat = flatten(f.read_text(encoding="utf-8", errors="replace"))
        for m in pat.finditer(flat):
            hits += 1
            print(f"SRC {f.name}\n    ...{flat[max(0,m.start()-90):m.end()+90]}...")
    for f in sorted(FORMAL.glob("*.pdf")):
        if not want_pdf:
            break
        flat = flatten(pdf_text(f), pdf=True)
        for m in pat.finditer(flat):
            hits += 1
            print(f"PDF {f.name}\n    ...{flat[max(0,m.start()-90):m.end()+90]}...")
    print(f"\n{hits} hit(s)")
    return 0 if hits else 1

def stems(names):
    if names:
        return names
    out = subprocess.run(["git", "diff", "--name-only", "HEAD", "--", "papers/formal"],
                         capture_output=True, text=True, cwd=FORMAL.parent.parent).stdout
    return sorted({Path(l).stem for l in out.split() if l.endswith(".tex")})

def cmd_build(a):
    metadata = subprocess.run([sys.executable, str(Path(__file__).parent / "build_paper_metadata.py")])
    if metadata.returncode:
        return metadata.returncode
    todo = stems(a.stems)
    if not todo:
        print("nothing changed; nothing to build")
        return 0
    bad = 0
    for stem in todo:
        tex = FORMAL / f"{stem}.tex"
        if not tex.exists():
            print(f"FAIL {stem}: no such .tex"); bad += 1; continue
        for i in (1, 2, 3):
            r = subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error",
                                tex.name], cwd=FORMAL, capture_output=True, text=True)
            if r.returncode:
                bad += 1
                print(f"FAIL {stem} pass {i}")
                for line in r.stdout.splitlines():
                    if line.startswith("!"):
                        print("   " + line)
                break
        else:
            pdf = FORMAL / f"{stem}.pdf"
            info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
            pages = next((l.split()[1] for l in info.splitlines() if l.startswith("Pages")), "?")
            words = len(pdf_text(pdf).split())
            refs = flatten(pdf_text(pdf), pdf=True).count("??")
            warn = f"  [{refs} UNRESOLVED REF]" if refs else ""
            print(f"ok   {stem}  {pages}pp  {words}w{warn}")
            bad += bool(refs)
    return 1 if bad else 0

def cmd_round(a):
    rc = cmd_build(a)
    print()
    rc |= subprocess.run([sys.executable, str(Path(__file__).parent / "check_draft_consistency.py")]).returncode
    return rc

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("grep"); g.add_argument("pattern")
    g.add_argument("--src", action="store_true"); g.add_argument("--pdf", action="store_true")
    g.add_argument("--re", action="store_true", help="treat pattern as a regex")
    g.set_defaults(fn=cmd_grep)
    b = sub.add_parser("build"); b.add_argument("stems", nargs="*"); b.set_defaults(fn=cmd_build)
    r = sub.add_parser("round"); r.add_argument("stems", nargs="*"); r.set_defaults(fn=cmd_round)
    args = ap.parse_args()
    sys.exit(args.fn(args))
