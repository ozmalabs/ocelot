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
import argparse, io, os, re, shutil, subprocess, sys

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

READING_ORDER = """Graphic Equalisation --- what is claimed, and where (%(draft)s)

One assumption: that to be is to stand in relation and to cohere in it, with no
time, no cause, no rule and no observer added. What follows is claimed to
descend from it. Each entry names where it is argued, so that it can be checked
there rather than taken on anyone's word.

WHAT IS CLAIMED, AND WHERE IT IS ARGUED

  the invariance of c is a theorem given the substrate's own units, not a
  postulate
      01a, "c as the change-to-time rate"

  special and general relativity are one change-budget spent two ways, on
  motion or on change-load
      01a, "Special and general relativity reconciled"

  the Born rule is recovered from closure, no-privilege and free continuation
  rather than assumed
      01a, "Amplitudes are a rule on Narrative; recovering the Born rule"

  the measure problem of eternal inflation is ill-posed rather than unsolved,
  which predicts that the regularisations will not converge
      01c, "The measure problem is the no-prior-free proposition"

  "a typical universe" names two different objects, and neither supports the
  inference usually drawn from it
      01c, "Anthropic reasoning inherits the same defect"

  the route from isotropy to homogeneity is exact and conditional on a
  quantifier with no referent, which Ehlers-Geren-Sachs states in its own
  antecedent
      01c, "The cosmological principle divides"

Each of those is stated as a proposition with its grounds attached, and each
carries falsifiability commitments in its paper's closing section. They are
meant to be attacked at those locations.

IF YOU CAME FOR ONE OF THEM

Go to it. The papers are cross-referenced and each states its own dependencies;
nothing above requires the others to have been read first.

IF YOU ARE STARTING COLD

  1.  00_is  --- %(p0)s
      The one claim, with no machinery: what it commits to and what it does
      not.

  2.  01a_graphic_equalisation_physics_grounding  --- %(p1)s
      The first three claims above, with the constants, the second law and
      entanglement besides.

  3.  01c_graphic_equalisation_cosmology_grounding  --- %(p2)s
      The last three. Short because the in-frame half of cosmology is in 01a;
      the division is deliberate and stated.

  4.  01_law_of_graphic_equalisation_theory_referenced  --- %(p3)s
      The monograph, which grounds everything asserted in 1-3.

%(cost)s

Read first, the monograph gives no reason to continue; read fourth, it is what
the first three are drawing on. That is the only reason for the order.

The remaining documents extend the same account and depend on none of the four.
"""

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
        # Ships with the papers because a covering note sent separately gets
        # separated from them. Written as an index rather than a pitch: a
        # reader who sought this out has already decided, and persuasion aimed
        # at them reads as apology. Naming where each claim is argued works
        # whoever the reader is, and does not lean on the author's standing.
        pages = {}
        for pdf, dest in plan:
            try:
                info = subprocess.run(["pdfinfo", os.path.join(out, dest)],
                                      capture_output=True, text=True).stdout
                pages[dest.split("_draft")[0]] = int(
                    re.search(r"Pages:\s+(\d+)", info).group(1))
            except Exception:
                pass
        order = ["00_is", "01a_graphic_equalisation_physics_grounding",
                 "01c_graphic_equalisation_cosmology_grounding",
                 "01_law_of_graphic_equalisation_theory_referenced"]
        pp = ["%d pages" % pages[k] if k in pages else "" for k in order]
        first3 = sum(pages[k] for k in order[:3] if k in pages)
        last = pages.get(order[3], 0)
        cost = ("The first three come to %d pages. The fourth is %d on its own."
                % (first3, last)) if first3 and last else ""
        io.open(os.path.join(out, "WHAT_IS_CLAIMED.txt"), "w",
                encoding="utf-8").write(READING_ORDER % {
                    "draft": list(drafts.values())[0], "cost": cost,
                    "p0": pp[0], "p1": pp[1], "p2": pp[2], "p3": pp[3]})

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
