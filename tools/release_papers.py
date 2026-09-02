#!/usr/bin/env python3
r"""Copy the cleared papers out of the repository, and refuse to do anything else.

This repository houses the substrate. The papers are 51 files inside roughly
seven and a half thousand, and the two clearances are different: the theory is
freely releasable, the realisation is not. Before this gate existed there was no
mechanism for the first without the second -- "send someone paper 00" had no
implementation that did not also hand over the substrate.

So this is a gate rather than a copy script, and it fails closed:

  1. Only CLEARED documents are ever copied. The allowlist is a constant below
     and is the whole content of the tool; changing it is the decision.
  2. A PDF whose own footer revision disagrees with its source is REFUSED.
     A stale build is the failure mode that ships the wrong text while every
     other check passes.
  3. The cleared set must agree on one draft string, for the reason the
     draft-consistency checker exists: a reader comparing two papers must never
     be comparing two drafts.
  4. A released document containing any FORBIDDEN phrase is REFUSED. These name
     the excluded document's contents rather than its existence. Naming that it
     exists is intended; setting out what is in it is not.
  5. The output directory must be outside the repository.

Usage:
    python3 tools/release_papers.py [--out DIR] [--dry-run]
"""
import argparse, os, re, shutil, subprocess, sys

CLEARED = ["00_is",
           "01_law_of_graphic_equalisation_theory_referenced",
           "01a_graphic_equalisation_physics_grounding",
           "01b_graphic_equalisation_mind_and_self_grounding",
           "01c_graphic_equalisation_cosmology_grounding",
           "01s_graphic_equalisation_statement",
           "02_seldon_manifolds_theory_referenced",
           "02a_seldon_manifolds_psychological_grounding",
           "03_law_of_narrative_momentum_theory_referenced",
           "04_narrativium_theory_referenced",
           "05_frames_relation_and_the_empty_limit",
           "06_assessing_an_account_of_this_kind"]
# This is the whole series and A1 is the only exclusion, which makes an inverted
# rule tempting: release everything except A1. It stays an ALLOWLIST because the
# two fail in opposite directions. A document added to this repository tomorrow
# is, under an allowlist, not released until somebody clears it; under a
# denylist it is released until somebody remembers to stop it.

# Phrases that set out the excluded document's contents rather than naming it.
FORBIDDEN = ["proposal closure", "execution semantics", "reference execution"]

PAPERS = "papers/formal"
DRAFT_RE = re.compile(r"draft-\d{4}-\d{2}-\d{2}(?:\.\d+)?")
REV_TEX_RE = re.compile(r"document revision (\d+)")
REV_PDF_RE = re.compile(r"draft-\d{4}-\d{2}-\d{2}(?:\.\d+)?\s*r(\d+)", re.I)
# The statement is generated and carries its SOURCE's revision, not its own.
GEN_RE = re.compile(r"from long r(\d+)", re.I)
GENERATED_FROM = {"01s_graphic_equalisation_statement":
                  "01_law_of_graphic_equalisation_theory_referenced"}


def fail(msg):
    print("REFUSED: " + msg, file=sys.stderr)
    sys.exit(1)


def pdftext(path):
    return subprocess.run(["pdftotext", path, "-"], capture_output=True,
                          text=True, check=True).stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.expanduser("~/ocelot-release"))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    out = os.path.abspath(a.out)
    if out == root or out.startswith(root + os.sep):
        fail("output directory %s is inside the repository" % out)

    drafts, plan = {}, []
    for name in CLEARED:
        tex = os.path.join(root, PAPERS, name + ".tex")
        pdf = os.path.join(root, PAPERS, name + ".pdf")
        for p in (tex, pdf):
            if not os.path.exists(p):
                fail("%s is missing" % os.path.relpath(p, root))

        src = open(tex, encoding="utf-8").read()
        m_d = DRAFT_RE.search(src)
        if not m_d:
            fail("%s carries no draft string" % name)
        draft = m_d.group(0)
        drafts[name] = draft
        text = pdftext(pdf)

        if name in GENERATED_FROM:
            # A generated document tracks its source. Check it was generated from
            # the CURRENT source, which is the way this one goes stale.
            parent = GENERATED_FROM[name]
            psrc = open(os.path.join(root, PAPERS, parent + ".tex"), encoding="utf-8").read()
            m_par = REV_TEX_RE.search(psrc)
            if not m_par:
                fail("%s carries no revision, so %s cannot be checked against it" % (parent, name))
            m_s, m_p = GEN_RE.search(src), GEN_RE.search(text)
            if not (m_s and m_p):
                fail("%s does not record the source revision it was generated from" % name)
            if m_p.group(1) != m_s.group(1):
                fail("%s.pdf is STALE against its own source (pdf from r%s, tex from r%s)"
                     % (name, m_p.group(1), m_s.group(1)))
            if m_s.group(1) != m_par.group(1):
                fail("%s was generated from %s r%s, which is now r%s. Regenerate before releasing."
                     % (name, parent, m_s.group(1), m_par.group(1)))
            rev = "from-r" + m_s.group(1)
        else:
            m_r = REV_TEX_RE.search(src)
            if not m_r:
                fail("%s carries no revision" % name)
            rev = m_r.group(1)
            m_p = REV_PDF_RE.search(text)
            if not m_p:
                fail("%s.pdf carries no footer revision" % name)
            if m_p.group(1) != rev:
                fail("%s.pdf is STALE: source is r%s, built PDF is r%s. Rebuild before releasing."
                     % (name, rev, m_p.group(1)))
            rev = "r" + rev

        low = text.lower()
        for phrase in FORBIDDEN:
            if phrase in low:
                fail("%s.pdf contains %r, which sets out the excluded document's contents"
                     % (name, phrase))

        plan.append((pdf, "%s_%s_%s.pdf" % (name, draft, rev)))

    if len(set(drafts.values())) != 1:
        fail("cleared set spans several drafts: %s" % sorted(set(drafts.values())))

    # Versioned filenames mean a second run ADDS rather than replaces, so the
    # directory accumulates superseded revisions and someone sending "the papers"
    # can send a mixed set. That is the failure this gate exists to prevent,
    # reintroduced by the naming. Supersedes are moved aside, not deleted.
    keep = {d for _, d in plan}
    stale = []
    if os.path.isdir(out):
        for f in sorted(os.listdir(out)):
            if not f.endswith(".pdf") or f in keep:
                continue
            if any(f.startswith(name + "_") for name in CLEARED):
                stale.append(f)

    if a.dry_run:
        print("dry run -- would write %d files to %s" % (len(plan), out))
        for f in stale:
            print("  would supersede: " + f)
    else:
        os.makedirs(out, exist_ok=True)
        if stale:
            sup = os.path.join(out, "superseded")
            os.makedirs(sup, exist_ok=True)
            for f in stale:
                shutil.move(os.path.join(out, f), os.path.join(sup, f))
        for pdf, dest in plan:
            shutil.copy2(pdf, os.path.join(out, dest))

    print("cleared and released (%s):" % list(drafts.values())[0])
    for _, dest in plan:
        print("  " + dest)
    if stale:
        print("\nmoved to superseded/ (%d):" % len(stale))
        for f in stale:
            print("  " + f)
    print("\nNOT released: every other document in this repository, and the "
          "repository itself.")


if __name__ == "__main__":
    main()
