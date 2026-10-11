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

Website output (--website DIR) is the same gate with a second product. It
carries the identical text the PDF does -- it is generated from the same .tex --
so every clearance above applies to it unchanged and runs BEFORE a single HTML
file is written. On top of the versioned PDF it emits, per cleared paper, a
rendered HTML page (via htlatex, with all cleared sources present so the
cross-document references resolve), a papers.json manifest, and an index.html.
The website directory obeys the same outside-the-repository rule as --out.

Usage:
    python3 tools/release_papers.py [--out DIR] [--website DIR] [--dry-run]
"""
import argparse, html, io, json, os, re, shutil, subprocess, sys, tempfile

from build_paper_metadata import INCLUDE, load_manifest, render, revision_for

CLEARED = ["00_is",
           "01_law_of_graphic_equalisation_theory_referenced",
           "01a_graphic_equalisation_physics_grounding",
           "01b_graphic_equalisation_mind_and_self_grounding",
           "01c_graphic_equalisation_cosmology_grounding",
           "01d_graphic_equalisation_born_recovery",
           "01e_graphic_equalisation_communication_grounding",
           "01f_graphic_equalisation_qualia_and_consciousness_grounding",
           "01g_graphic_equalisation_total_perspective_vortex_grounding",
           "01s_graphic_equalisation_statement",
           "02_seldon_manifolds_theory_referenced",
           "02a_seldon_manifolds_psychological_grounding",
           "02b_seldon_manifolds_social_and_psychological_application",
           "03_law_of_narrative_momentum_theory_referenced",
           "04_narrativium_theory_referenced",
           "05_frames_relation_and_the_empty_limit",
           "06_assessing_an_account_of_this_kind",
           "07_causal_attitude_networks_on_the_substrate",
           "08_certified_answers_as_an_audit",
           "10_applied_graphic_equalisation",
           "11_relational_information_ethics"]
# This is a deliberately fail-closed allowlist. The excluded adaptation theory
# and implementation papers (09 and 09a), together with the constructive
# realisation (A1), relate to autonomous-control capability or executable
# realisation and are not released. Any future document remains unreleased until
# explicitly added here; a denylist would fail in the opposite direction.

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


# ── Website output ──────────────────────────────────────────────────────────
# A second product, gated identically to the PDF release: it is generated from
# the same .tex the clearance checks read, so it carries the same text and the
# same gate covers it. Nothing here runs until every check in main() has passed.

TITLE_RE = re.compile(r"\\title\{(.*?)\}\s*(?:\n|%|\\author)", re.S)
ABSTRACT_RE = re.compile(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", re.S)

# LaTeX escapes that survive into a title or abstract, smallest useful set.
_TEX_SUBS = [
    (r"\\texorpdfstring\{(.*?)\}\{(.*?)\}", r"\2"),
    # Inline math: keep the inner token(s), drop the $ delimiters. Titles here
    # only carry trivial math like $c$; this is not a math renderer.
    (r"\$([^$]*)\$", r"\1"),
    # Citations are noise in a plain-text abstract: drop the whole command,
    # including any optional [..] argument and multi-key {a,b} argument. Must
    # run before the generic \cmd{...} rule, which would otherwise keep the key.
    (r"\\(?:citep|citet|citeauthor|citeyear|cite|autocite|parencite)\s*(?:\[[^\]]*\])*\s*\{[^}]*\}", ""),
    (r"\\emph\{(.*?)\}", r"\1"),
    (r"\\textbf\{(.*?)\}", r"\1"),
    (r"\\textit\{(.*?)\}", r"\1"),
    (r"\\text\{(.*?)\}", r"\1"),
    (r"\\[a-zA-Z]+\{(.*?)\}", r"\1"),
    (r"---", "\u2014"), (r"--", "\u2013"),
    (r"``", "\u201c"), (r"''", "\u201d"), (r"~", " "),
    (r"\\textemdash", "\u2014"), (r"\\textbullet", "\u2022"),
    (r"\\,", " "), (r"\\ ", " "), (r"\\[a-zA-Z]+", ""),
    (r"\{", ""), (r"\}", ""), (r"\\%", "%"),
]


def detex(s):
    """Reduce a title/abstract fragment to plain text. Not a LaTeX parser --
    just the escapes that actually occur in these documents' front matter."""
    s = s.strip()
    for pat, rep in _TEX_SUBS:
        s = re.sub(pat, rep, s)
    s = re.sub(r"\s+", " ", s)
    # Stripping an inline citation can leave a space before punctuation
    # ("helplessness , with") or a doubled space; tidy both.
    s = re.sub(r"\s+([.,;:!?])", r"\1", s)
    return s.strip()


def paper_meta(src):
    """(title, subtitle, abstract) from a paper's LaTeX source. Titles here are
    `Main\\\\large Subtitle`; the split is on that boundary."""
    m = TITLE_RE.search(src)
    title, subtitle = "", ""
    if m:
        raw = m.group(1)
        parts = re.split(r"\\\\\s*\\large\s*", raw, maxsplit=1)
        title = detex(parts[0])
        subtitle = detex(parts[1]) if len(parts) > 1 else ""
    m = ABSTRACT_RE.search(src)
    abstract = detex(m.group(1)) if m else ""
    return title, subtitle, abstract


def short_desc(abstract, limit=170):
    """A compact card description from the abstract: the first sentence (or two,
    if the first is very short), trimmed to ~limit chars on a word boundary.
    The full abstract is 800-1800 chars and unusable as a card blurb."""
    if not abstract:
        return ""
    # Take sentences until we have something substantial, then cap.
    text = abstract.strip()
    parts = re.split(r"(?<=[.!?])\s+", text)
    out = parts[0] if parts else text
    if len(out) < 60 and len(parts) > 1:
        out = (out + " " + parts[1]).strip()
    if len(out) <= limit:
        return out
    cut = out[:limit].rsplit(" ", 1)[0].rstrip(",;:—- ")
    return cut + "\u2026"


def pdf_pages(path):
    try:
        info = subprocess.run(["pdfinfo", path], capture_output=True, text=True).stdout
        return int(re.search(r"Pages:\s+(\d+)", info).group(1))
    except Exception:
        return None


# A readable "paper" theme layered on top of tex4ht's font-class CSS. tex4ht
# styles glyphs but not the page, so this supplies the reading column, measure,
# typography, and the styling for the structural classes tex4ht emits
# (.maketitle, .titleHead, .sectionHead, .newtheorem, .abstract, .fbox for the
# DRAFT notice, .thebibliography, math images). Light on purpose: the math is
# rendered as black vector SVG, which reads correctly on a paper-white ground
# and would need inverting on a dark one (breaking coloured figures).
PAPER_CSS = """
:root {
  --paper: #faf9f7; --ink: #1c1b19; --ink-soft: #444038; --rule: #e2ddd3;
  --accent: #1f7a54; --accent-soft: #eaf5ef; --link: #1f7a54;
  --measure: 52rem;
}
html { -webkit-text-size-adjust: 100%; }
body {
  margin: 0; background: #efece6; color: var(--ink);
  font-family: Georgia, 'Iowan Old Style', 'Palatino Linotype', 'Times New Roman', serif;
  font-size: 18px; line-height: 1.7;
  -webkit-font-smoothing: antialiased; text-rendering: optimizeLegibility;
}
/* Reading column: centre every top-level block on one measure. tex4ht emits a
   flat sequence of top-level blocks, so each is centred with an auto left/right
   margin and shares the same padding, so nothing (paragraphs, the draft box,
   headings) escapes or mis-aligns. */
body > * {
  max-width: var(--measure);
  margin-left: auto; margin-right: auto;
  padding-left: 24px; padding-right: 24px;
}
.paper-topbar { max-width: none; padding: 0;
  background: #fff; border-bottom: 1px solid var(--rule);
  font-family: 'Inter', system-ui, sans-serif;
}
.paper-topbar-inner {
  max-width: var(--measure); margin: 0 auto; padding: 14px 32px;
  display: flex; align-items: center; justify-content: space-between; gap: 16px;
}
.paper-topbar a { color: var(--accent); text-decoration: none; font-size: 14px; font-weight: 600; }
.paper-topbar a:hover { text-decoration: underline; }
.paper-topbar .brand { color: var(--ink); font-weight: 800; letter-spacing: -0.02em; }
.paper-topbar .brand span { color: var(--accent); }

body { padding-bottom: 80px; }

/* Typography. Horizontal centring/padding comes from `body > *`; paragraphs set
   only vertical rhythm and alignment here (a `margin` shorthand would wipe out
   the auto centring). */
p, p.indent, p.noindent {
  margin-top: 0; margin-bottom: 1.1em;
  text-align: justify; text-justify: inter-word; hyphens: auto;
}
/* The abstract and bibliography read better ragged-right */
.abstract p, .thebibliography p, .abstract p.indent, .abstract p.noindent {
  text-align: left; hyphens: manual;
}
.titleHead {
  font-size: 2em; line-height: 1.15; font-weight: 700; text-align: center;
  margin-top: 0.6em; margin-bottom: 0.2em; padding-top: 8px; letter-spacing: -0.01em;
}
h2.titleHead br + * { font-size: 0.6em; }
.author, .date { text-align: center; font-family: 'Inter', system-ui, sans-serif; }
.author { font-size: 0.9em; color: var(--ink-soft); margin-top: 0.6em; }
.date { font-size: 0.8em; color: var(--ink-soft); margin-top: 0.4em; }

.sectionHead, h3, .likesectionHead {
  font-family: 'Inter', system-ui, sans-serif; font-weight: 700;
  font-size: 1.3em; line-height: 1.25; margin-top: 1.8em; margin-bottom: 0.6em;
  color: var(--ink); letter-spacing: -0.01em;
  scroll-margin-top: 72px;
}
/* Section anchor: a faint '#' that appears on hover, giving the reader the
   section's link. The heading carries a readable id (e.g. #falsifiability). */
.headlink {
  margin-left: 0.4em; color: var(--accent); text-decoration: none;
  font-weight: 400; opacity: 0; transition: opacity 0.15s;
}
.sectionHead:hover .headlink, .subsectionHead:hover .headlink,
.subsubsectionHead:hover .headlink, .paragraphHead:hover .headlink,
.headlink:focus { opacity: 0.6; }
.headlink:hover { opacity: 1; text-decoration: underline; }

/* Abstract and DRAFT notice. Both are nested inside a tex4ht .center wrapper,
   which `body > *` already centres on the measure, so they fill their container
   (margin 0) rather than trying to re-centre on a narrower max-width -- that
   mismatch is what left the draft box off-centre. */
.abstracttitle { font-family: 'Inter', system-ui, sans-serif; font-weight: 700; text-align: center; }
.abstract {
  font-size: 0.96em; color: var(--ink-soft); background: var(--accent-soft);
  border: 1px solid var(--rule); border-radius: 10px;
  padding: 20px 28px; margin-top: 1.4em; margin-bottom: 2em; text-align: left;
}
.abstract p { text-align: left; }
.fbox, div.fbox {
  display: block; width: auto;
  font-family: 'Inter', system-ui, sans-serif; font-size: 0.8em; line-height: 1.55;
  color: var(--ink-soft); background: #fdf6e3; border: 1px solid #e6dcc0;
  border-radius: 10px; padding: 14px 20px; margin-top: 0; margin-bottom: 1.8em; text-align: left;
}
/* tex4ht wraps the notice/abstract in div.center (text-align:center,
   margin:1em) and its own thin border/table display; neutralise those so our
   card centres on the reading column and inter-word spaces are not eaten by the
   table box (that was the "companionto" fusion). Match tex4ht's specificity. */
div.center { text-align: left; margin-left: auto; margin-right: auto; }
div.center div.fbox { text-align: left; border: 1px solid #e6dcc0; }

/* Theorem-like environments */
.newtheorem {
  background: #fff; border-left: 3px solid var(--accent);
  padding: 2px 24px 2px 22px; margin-top: 1.2em; margin-bottom: 1.2em;
}

/* Links */
a { color: var(--link); text-decoration-thickness: 0.06em; text-underline-offset: 2px; }
a.xref-ext { font-weight: 600; white-space: nowrap; }

/* Math: display centred with horizontal scroll on overflow; inline baseline-aligned */
.math-display { text-align: center; margin-top: 1.3em; margin-bottom: 1.3em; overflow-x: auto; }
.math-display img, .math-display svg { max-width: 100%; height: auto; }
img { max-width: 100%; }
p img, td img, li img { vertical-align: middle; }

/* Figures */
/* Figures. tex4ht wraps the figure image in a <p class="noindent">, which the
   body-paragraph rule would justify (left-aligning a lone image); force figure
   content and its paragraphs back to centred, above that rule's specificity. */
.figure, figure { text-align: center; margin-top: 1.6em; margin-bottom: 1.6em; }
.figure p, figure p, .figure p.indent, .figure p.noindent { text-align: center; }
.figure img, figure img { max-width: 100%; height: auto; display: inline-block; }
.caption, figcaption, .figure .caption { font-family: 'Inter', system-ui, sans-serif; font-size: 0.82em; color: var(--ink-soft); text-align: center; }

/* Lists */
ul, ol { margin: 0 auto 1.1em; }
li { margin-bottom: 0.3em; }

/* Bibliography */
.thebibliography { font-size: 0.86em; color: var(--ink-soft); margin-top: 2.4em; border-top: 1px solid var(--rule); padding-top: 1.4em; }
.thebibliography p { text-align: left; }

/* Tables */
.tabular, table { border-collapse: collapse; margin: 1.4em auto; font-size: 0.9em; max-width: 100%; }
.tabular td, .tabular th, table td, table th { border: 1px solid var(--rule); padding: 6px 12px; }

@media (max-width: 640px) {
  body { font-size: 17px; }
  body > * { padding-left: 18px; padding-right: 18px; }
  .paper-topbar { padding: 0; }
  .paper-topbar-inner { padding: 12px 18px; }
}
"""

def _strip_tex_comments(s):
    return "\n".join(re.sub(r"(?<!\\)%.*", "", line) for line in s.split("\n"))


def build_label_map(root):
    """{stem: {label: number}} from every paper's pdflatex .aux. These are the
    authoritative resolved reference numbers -- the same ones the PDF prints."""
    formal = os.path.join(root, PAPERS)
    labels = {}
    for f in os.listdir(formal):
        if not f.endswith(".aux"):
            continue
        stem = f[:-4]
        m = {}
        aux = open(os.path.join(formal, f), encoding="utf-8", errors="replace").read()
        for mo in re.finditer(r"\\newlabel\{([^}]*)\}\{\{([^}]*)\}", aux):
            m[mo.group(1)] = mo.group(2)
        labels[stem] = m
    return labels


def resolve_xrefs(htmltext, name, root, labels, slug_for):
    """Replace tex4ht's unresolved `??` cross-references with the real numbers,
    linked to the target paper.

    tex4ht cannot resolve \\externaldocument (xr-hyper) references -- they render
    as `??` -- and the xr-hyper/tex4ht combination crashes if fed the referenced
    documents' .aux. But those references are exactly the ones the PDF resolves,
    and the pdflatex .aux files hold the numbers. The `??` in the HTML occur in
    the same order as the external \\ref commands in the source, and their counts
    match, so we can substitute in order. Local refs tex4ht already resolved are
    untouched (they are not `??`)."""
    src = _strip_tex_comments(
        open(os.path.join(root, PAPERS, name + ".tex"), encoding="utf-8").read())
    prefix_to_stem = {mo.group(1): mo.group(2) for mo in
                      re.finditer(r"\\externaldocument\[([^\]]*)\]\{([^}]*)\}", src)}
    if not prefix_to_stem:
        return htmltext

    ordered = re.findall(r"\\(?:ref|autoref|cref|Cref|eqref|pageref)\{([^}]*)\}", src)
    external = [r for r in ordered
                if any(r.startswith(p) for p in prefix_to_stem)]

    resolved = []
    for r in external:
        for pfx, stem in prefix_to_stem.items():
            if r.startswith(pfx):
                num = labels.get(stem, {}).get(r[len(pfx):])
                resolved.append((num, stem))
                break
        else:
            resolved.append((None, None))

    qq = list(re.finditer(r"(<span\b[^>]*>)\s*\?\?\s*(</span>)", htmltext))
    if len(qq) != len(resolved):
        # Order/count no longer line up (source changed shape); leave the page
        # rather than risk substituting the wrong numbers. Surfaces as remaining
        # `??`, which is visible and honest, not a silent wrong reference.
        return htmltext

    out, last = [], 0
    for m, (num, stem) in zip(qq, resolved):
        out.append(htmltext[last:m.start()])
        if num is None:
            out.append(m.group(0))  # keep ?? if unresolved
        else:
            target = slug_for.get(stem)
            body = html.escape(num)
            if target:
                out.append('%s<a class="xref-ext" href="../%s/%s.html">%s</a>%s'
                            % (m.group(1), target, target, body, m.group(2)))
            else:
                out.append("%s%s%s" % (m.group(1), body, m.group(2)))
        last = m.end()
    out.append(htmltext[last:])
    return "".join(out)


def fix_span_spacing(htmltext):
    """tex4ht sometimes emits `word</span><span ...>word` with only a newline
    between the spans, and where the source had a line break inside a run the
    two words render fused ("activerevision"). Insert a space when a span closes
    on a word character and the next span opens on one, with only whitespace
    between. Conservative: only touches the </span>\\s*<span ...> boundary."""
    return re.sub(
        r"(?<=[A-Za-z0-9,;:])(</span>)\s*\n\s*(<span\b)",
        r"\1 \2", htmltext)


def slugify(text):
    """A stable, readable URL fragment from heading text. Lowercase, spaces to
    hyphens, drop anything else. 'Objectivity as a direction' -> objectivity-as-
    a-direction."""
    text = re.sub(r"<[^>]+>", "", text)          # strip any tags
    text = re.sub(r"&[a-zA-Z]+;|&#\d+;", " ", text)  # entities to space
    # tex4ht emits typographic ligatures; normalise so 'Falsifiability' does not
    # slug to 'falsi-ability'.
    for lig, plain in (("\ufb01", "fi"), ("\ufb02", "fl"), ("\ufb00", "ff"),
                       ("\ufb03", "ffi"), ("\ufb04", "ffl"), ("\ufb05", "st")):
        text = text.replace(lig, plain)
    text = text.replace("\u2014", " ").replace("\u2013", " ")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text


def add_heading_anchors(htmltext):
    """Give every section heading a stable, human-readable id so sections can be
    linked (paper.html#objectivity-as-a-direction).

    tex4ht already emits an opaque anchor (id="x1-30003") inside each heading for
    its own cross-references; those are kept. This adds a readable id ON the
    heading element itself, derived from its visible title text, with numeric
    suffixes for collisions. Also makes the heading a hover-to-get-link target."""
    heading_re = re.compile(
        r'(<(h[1-6])\s+class="(?:section|subsection|subsubsection|paragraph)Head"[^>]*>)(.*?)(</\2>)',
        re.S)
    seen = {}

    def repl(m):
        open_tag, tag, inner, close_tag = m.group(1), m.group(2), m.group(3), m.group(4)
        if " id=" in open_tag:            # already has one, leave it
            return m.group(0)
        # visible text = inner minus the titlemark number span and any tags
        text = re.sub(r'<span class="titlemark">.*?</span>', "", inner, flags=re.S)
        slug = slugify(text)
        if not slug:
            return m.group(0)
        n = seen.get(slug, 0)
        seen[slug] = n + 1
        if n:
            slug = "%s-%d" % (slug, n + 1)
        new_open = open_tag[:-1] + ' id="%s">' % slug
        # A small anchor link on hover, so a reader can grab the section URL.
        link = '<a class="headlink" href="#%s" aria-label="Link to this section">#</a>' % slug
        return new_open + inner + link + close_tag

    return heading_re.sub(repl, htmltext)


PAPER_TOPBAR = (
    '<div class="paper-topbar"><div class="paper-topbar-inner">'
    '<a class="brand" href="/">ozma<span>labs</span></a>'
    '<a href="/papers/">\u2190 All papers</a>'
    '</div></div>\n'
)


def style_page(htmltext, name):
    """Layer the readable paper theme onto a tex4ht page: link paper.css after
    the paper's own generated CSS (so it overrides), and drop a back-link topbar
    in at the top of the body."""
    link = '<link rel="stylesheet" type="text/css" href="paper.css" />'
    # Place ours AFTER the tex4ht stylesheet link so cascade order favours it.
    if re.search(r'<link[^>]+\.css"[^>]*/?>', htmltext):
        htmltext = re.sub(r'(<link[^>]+\.css"[^>]*/?>)', r'\1\n' + link, htmltext, count=1)
    else:
        htmltext = htmltext.replace("</head>", link + "\n</head>", 1)
    # Topbar immediately after <body ...>
    htmltext = re.sub(r'(<body\b[^>]*>)', r'\1\n' + PAPER_TOPBAR, htmltext, count=1)
    return htmltext


def build_html(names, root, workdir):
    """Render each cleared paper to HTML with htlatex, each in its OWN isolated
    subdirectory of workdir. Every cleared source is copied into each subdir so
    the \\externaldocument cross-references resolve.

    Isolation per paper is not optional. htlatex rewrites the .aux files it
    touches into a tex4ht-specific form; a later paper that \\externaldocument's
    an earlier one then reads that rewritten .aux with pdflatex's xr-hyper and
    dies at \\begin{document} (\\sys:sp ... Emergency stop). Sharing one working
    directory makes the build order-dependent and it fails for exactly the
    papers that cite others. A fresh directory per paper gives each run clean
    pdflatex-style .aux files to resolve against.

    Returns {name: (subdir, [asset files])} -- the files that make up each page
    (html, css, and any figure svg/png). Raises on any paper that fails to
    produce HTML: a partial website is a stale-build failure of exactly the kind
    this gate refuses for PDFs."""
    src_formal = os.path.join(root, PAPERS)
    sources = [f for f in os.listdir(src_formal)
               if f.endswith((".tex", ".spec", ".bib", ".sty"))]

    # Some papers \input figures by the relative path ../figures/<fig>-body. The
    # per-paper subdir is workdir/<name>/, so that resolves to workdir/figures/.
    # Mirror the figures tree there once for every paper to find.
    figures_src = os.path.join(root, "papers", "figures")
    if os.path.isdir(figures_src):
        figures_dst = os.path.join(workdir, "figures")
        if not os.path.isdir(figures_dst):
            shutil.copytree(figures_src, figures_dst)

    produced = {}
    # Authoritative resolved reference numbers, and a stem->slug map (slug==name
    # here) so cross-references can link to the target paper's page.
    labels = build_label_map(root)
    slug_for = {n: n for n in names}
    for name in names:
        subdir = os.path.join(workdir, name)
        os.makedirs(subdir, exist_ok=True)
        for f in sources:
            shutil.copy2(os.path.join(src_formal, f), os.path.join(subdir, f))

        r = subprocess.run(
            ["htlatex", name + ".tex", "xhtml,svg,charset=utf-8", " -cunihtf -utf8"],
            cwd=subdir, capture_output=True, text=True)
        page = os.path.join(subdir, name + ".html")
        if not os.path.exists(page):
            tail = "\n".join(r.stdout.splitlines()[-12:])
            fail("htlatex produced no HTML for %s. tail:\n%s" % (name, tail))

        # tex4ht's default config renders display math as PNG via dvipng, which
        # is not installed here -- so the math images silently never appear. The
        # `svg` option above renders math (and figures) as SVG via dvisvgm, which
        # is present, and gives crisp vector math besides. Guard against a
        # regression: if the page references an image that was not produced, the
        # math renderer failed and the page would ship broken.
        htmltext = open(page, encoding="utf-8", errors="replace").read()
        for ref in set(re.findall(r'src="([^"]+\.(?:svg|png))"', htmltext)):
            if not os.path.exists(os.path.join(subdir, ref)):
                fail("%s references %s which was not generated (math renderer "
                     "failed -- is dvisvgm installed?)" % (name, ref))

        # tex4ht's own CSS only maps TeX font classes; it sets nothing for the
        # page itself, so the browser default (full-width, pure black on white)
        # is unreadable. Give every paper a readable reading column and a
        # back-link to the index. Also resolve the cross-paper `??` references
        # from the pdflatex .aux, and repair fused words at span boundaries.
        htmltext = resolve_xrefs(htmltext, name, root, labels, slug_for)
        htmltext = fix_span_spacing(htmltext)
        htmltext = add_heading_anchors(htmltext)
        htmltext = style_page(htmltext, name)
        open(page, "w", encoding="utf-8").write(htmltext)

        # Write the shared readable theme next to the page and ship it.
        open(os.path.join(subdir, "paper.css"), "w", encoding="utf-8").write(PAPER_CSS)

        assets = [name + ".html", "paper.css"]
        if os.path.exists(os.path.join(subdir, name + ".css")):
            assets.append(name + ".css")
        # Figures/math: tex4ht names them <stem><n>x.svg and references them from
        # the html. Ship whatever the page actually points at.
        for ref in set(re.findall(r'src="([^"]+\.(?:svg|png))"', htmltext)):
            if os.path.exists(os.path.join(subdir, ref)) and ref not in assets:
                assets.append(ref)
        produced[name] = (subdir, assets)
    return produced


INDEX_TMPL = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Ozma Labs \u2014 Papers</title>
<meta name="description" content="Formal preprints from Ozma Labs: one claim about relation, and the account that follows from it. Circulated for comment." />
<link rel="icon" href="/logo-square.svg" type="image/svg+xml" />
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
<style>
  :root {{ --bg:#050505; --surface:rgba(20,20,20,0.92); --surface-hover:rgba(26,26,26,0.95);
           --text:#f0fdf6; --muted:#8aaa97; --emerald:#4ae0a4; --emerald-bright:#6ef5bc;
           --border:rgba(74,224,164,0.12); --border-hover:rgba(74,224,164,0.30); }}
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  html {{ -webkit-font-smoothing:antialiased; }}
  body {{ font-family:'Inter',system-ui,-apple-system,sans-serif; background:var(--bg);
          color:var(--text); line-height:1.65; }}
  body::before {{ content:""; position:fixed; inset:0; z-index:0; pointer-events:none;
    background:
      radial-gradient(ellipse 70% 55% at 65% 0%, rgba(74,224,164,0.10), transparent),
      radial-gradient(ellipse 45% 35% at 90% 70%, rgba(91,154,255,0.06), transparent); }}
  .wrap {{ position:relative; z-index:1; max-width:1080px; margin:0 auto; padding:0 32px; }}
  nav {{ display:flex; align-items:center; justify-content:space-between; padding:24px 0; }}
  nav .logo {{ font-size:20px; font-weight:800; letter-spacing:-0.03em; color:var(--text); text-decoration:none; }}
  nav .logo span {{ color:var(--emerald); }}
  nav .nav-links {{ display:flex; gap:20px; align-items:center; }}
  nav a.nav-link {{ color:var(--muted); text-decoration:none; font-size:14px; font-weight:500; transition:color .2s; }}
  nav a.nav-link:hover {{ color:var(--text); }}

  header.page {{ padding:48px 0 8px; }}
  .kicker {{ font-size:12px; font-weight:700; letter-spacing:0.08em; text-transform:uppercase;
             color:var(--emerald); margin-bottom:12px; }}
  h1 {{ font-size:clamp(32px,6vw,52px); font-weight:800; letter-spacing:-0.035em; line-height:1.05; margin-bottom:20px; }}
  h1 span {{ color:var(--emerald); }}
  .intro p {{ color:#cfe6da; font-size:17px; max-width:660px; margin-bottom:16px; }}
  .intro p.muted {{ color:var(--muted); font-size:15px; }}
  .intro strong {{ color:var(--text); }}

  .starthere {{ margin:28px 0 8px; padding:24px 28px; border-radius:16px;
    background:rgba(74,224,164,0.05); border:1px solid var(--border); }}
  .starthere h2 {{ font-size:15px; font-weight:700; letter-spacing:0.01em; margin-bottom:12px; color:var(--text); }}
  .starthere .lead {{ color:var(--text); font-size:15px; font-weight:600; margin-bottom:14px; }}
  .starthere .path {{ color:var(--muted); font-size:14.5px; line-height:1.6; margin-bottom:14px; max-width:760px; }}
  .starthere .path strong {{ color:var(--emerald); font-weight:700; }}
  .starthere .path em {{ color:var(--text); font-style:italic; }}
  .starthere a {{ color:var(--emerald); text-decoration:none; font-weight:600; }}
  .starthere a:hover {{ text-decoration:underline; }}
  .starthere .note {{ color:var(--muted); font-size:13.5px; margin-top:4px; opacity:0.85; }}

  .llmbox {{ margin:16px 0 8px; padding:18px 22px; border-radius:14px;
    background:rgba(91,154,255,0.06); border:1px solid rgba(91,154,255,0.22); }}
  .llmbox h2 {{ font-size:14px; font-weight:700; letter-spacing:0.01em; margin-bottom:8px; color:var(--text); }}
  .llmbox p {{ color:var(--muted); font-size:14px; line-height:1.6; margin:0; max-width:760px; }}
  .llmbox code {{ font-size:13px; color:var(--emerald-bright); background:rgba(74,224,164,0.08);
    padding:1px 6px; border-radius:6px; word-break:break-all; }}
  .llmbox a {{ color:var(--emerald); text-decoration:none; font-weight:600; }}
  .llmbox a:hover {{ text-decoration:underline; }}

  .family {{ margin-top:44px; }}
  .family > .fam-head {{ border-bottom:1px solid var(--border); padding-bottom:10px; margin-bottom:18px; }}
  .family h2 {{ font-size:22px; font-weight:800; letter-spacing:-0.02em; }}
  .family .fam-desc {{ color:var(--muted); font-size:14px; margin-top:4px; max-width:720px; }}
  .cards {{ display:grid; grid-template-columns:repeat(2, minmax(0, 1fr)); gap:14px; }}

  .paper {{ display:flex; flex-direction:column; background:var(--surface);
            border:1px solid var(--border); border-radius:14px; padding:20px 22px;
            transition:border-color .2s, background .2s, transform .2s; }}
  .paper:hover {{ border-color:var(--border-hover); background:var(--surface-hover); transform:translateY(-2px); }}
  .paper.primary {{ border-color:rgba(74,224,164,0.28); background:rgba(74,224,164,0.04); }}
  .paper .start-badge {{ display:inline-block; align-self:flex-start; font-size:10.5px; font-weight:700;
            letter-spacing:0.06em; text-transform:uppercase; color:#050505; background:var(--emerald);
            border-radius:999px; padding:3px 9px; margin-bottom:10px; }}
  .paper .kind-row {{ display:flex; gap:7px; flex-wrap:wrap; margin-bottom:10px; }}
  .paper .kind {{ display:inline-block; font-size:10.5px; font-weight:700; letter-spacing:0.06em;
            text-transform:uppercase; border-radius:999px; padding:3px 9px; }}
  .paper .kind.theory {{ color:var(--emerald-bright); background:rgba(74,224,164,0.10);
            border:1px solid rgba(74,224,164,0.30); }}
  .paper .kind.grounding {{ color:#a9c4ff; background:rgba(91,154,255,0.10);
            border:1px solid rgba(91,154,255,0.28); }}
  .paper .kind.condensed {{ color:var(--muted); background:rgba(120,120,130,0.08);
            border:1px solid rgba(255,255,255,0.10); }}
  .paper .kind.meta {{ color:#e6c78a; background:rgba(230,199,138,0.09);
            border:1px solid rgba(230,199,138,0.26); }}
  .paper .kind.implementation {{ color:#d59ae0; background:rgba(213,154,224,0.09);
            border:1px solid rgba(213,154,224,0.26); }}
  .paper .kind.application {{ color:#f0a878; background:rgba(240,168,120,0.09);
            border:1px solid rgba(240,168,120,0.26); }}
  .paper .note {{ color:var(--muted); font-size:12.5px; line-height:1.5; margin:-4px 0 12px;
            font-style:italic; }}
  .paper .note a {{ color:var(--emerald); text-decoration:none; font-weight:600; font-style:normal; }}
  .paper .note a:hover {{ text-decoration:underline; }}
  .paper a.title {{ text-decoration:none; color:inherit; }}
  .paper h3 {{ font-size:16.5px; font-weight:700; letter-spacing:-0.01em; line-height:1.3; margin-bottom:4px; }}
  .paper a.title:hover h3 {{ color:var(--emerald-bright); }}
  .paper .sub {{ color:var(--emerald); font-size:12.5px; font-weight:600; margin-bottom:10px; line-height:1.35; }}
  .paper .abs {{ color:var(--muted); font-size:13.5px; line-height:1.55; margin-bottom:14px; flex:1; }}
  .paper .meta {{ font-size:12px; color:var(--muted);
                  display:flex; gap:14px; align-items:center; flex-wrap:wrap;
                  padding-top:12px; border-top:1px solid var(--border); }}
  .paper .meta .tag {{ opacity:0.7; }}
  .paper .meta .spacer {{ flex:1; }}
  .paper .meta a {{ color:var(--emerald); text-decoration:none; font-weight:600; }}
  .paper .meta a:hover {{ text-decoration:underline; }}

  footer {{ margin-top:56px; padding:28px 0 80px; border-top:1px solid var(--border);
            font-size:13px; color:var(--muted); opacity:0.7; }}
  footer a {{ color:var(--emerald); text-decoration:none; }}
  @media (max-width:720px) {{
    .wrap {{ padding:0 20px; }}
    .cards {{ grid-template-columns:1fr; }}
    nav .nav-links {{ gap:14px; }}
  }}
</style></head><body>
<div class="wrap">
  <nav>
    <a href="/" class="logo">ozma<span>labs</span></a>
    <div class="nav-links">
      <a href="/papers/" class="nav-link">Papers</a>
      <a href="/blog/" class="nav-link">Blog</a>
      <a href="/software/" class="nav-link">Software</a>
      <a href="https://github.com/ozmalabs" class="nav-link">GitHub</a>
    </div>
  </nav>

  <header class="page">
    <div class="kicker">Research \u00b7 formal papers</div>
    <h1>One claim about relation, <span>and what follows from it.</span></h1>
  </header>

  <section class="intro">
    <p>These papers start from a single claim \u2014 <strong>to be is to stand in relation and to
    cohere in it</strong>, with no time, cause, rule, or observer added \u2014 and work out what
    that forces. From it the set recovers the invariance of light speed, a reading of relativity,
    the Born rule, and accounts of frames, minds, and reachable futures. The claim is the
    arrangement, not the parts: the components are established science, cited as such.</p>
    <p class="muted">They are drafts, circulated for comment rather than as finished results.
    Each paper states what it claims, what earns it, and what would falsify it \u2014 the
    falsifiability sections are the intended points of attack. Definitions and numbering may
    change between drafts, so cite the draft string ({draft}) when referring to one.</p>
  </section>

  <div class="starthere">
    <h2>Where to start</h2>
    <p class="lead">There are two ways in, depending on what you want.</p>
    <p class="path"><strong>For the narrative.</strong> The short papers build the momentum that
    carries you into the main theory. <a href="00_is/00_is.html">Is</a> settles the one premise \u2014
    that relation is the core \u2014 and the
    <a href="01a_graphic_equalisation_physics_grounding/01a_graphic_equalisation_physics_grounding.html">Physics
    Grounding</a> shows the premise doing real work: light speed, relativity, and the Born rule as
    results rather than postulates. Read those and
    <a href="01_law_of_graphic_equalisation_theory_referenced/01_law_of_graphic_equalisation_theory_referenced.html">The
    Law \u2014 Theory</a> arrives as the thing they were drawing on.</p>
    <p class="path"><strong>Straight to the argument.</strong> If you already grant that relation is
    the core \u2014 the single claim <em>Is</em> makes \u2014 you do not need <em>Is</em> or the groundings
    first. Go directly to
    <a href="01_law_of_graphic_equalisation_theory_referenced/01_law_of_graphic_equalisation_theory_referenced.html">The
    Law \u2014 Theory</a>; it states its own dependencies, and the groundings are there when you want
    to see the claim tested against a specific field.</p>
    <p class="note">Came for one specific result? Every paper states its own dependencies; go straight to it. The full set is below, grouped by thread.</p>
  </div>

  <div class="llmbox">
    <h2>If you are using an LLM, or you are an LLM, use this</h2>
    <p>There is a single plain-text entry point built for machine reading:
    <a href="graphic-equalisation-for-llms.md">graphic-equalisation-for-llms.md</a>.
    Hand that URL to a language model to give it a compact, faithful operating model of the
    theory; it links a markdown rendering of every paper below so the model can open a source
    before asserting a result. Many people will meet this work through a model, and this is the
    front door for that.</p>
  </div>

{families}

  <footer>
    Released {draft}. Every document listed here is cleared for release; this list is exhaustive.
    Source and build: <a href="https://github.com/ozmalabs">github.com/ozmalabs</a>.
  </footer>
</div>
</body></html>
"""

CARD_TMPL = """    <div class="paper{primary}">
      {badge}<a class="title" href="{slug}/{name}.html"><h3>{title}</h3></a>
      {sub}
      {kindrow}{note}<p class="abs">{abstract}</p>
      <div class="meta"><span class="tag">{pages}</span><span class="tag">{rev}</span>
        <span class="spacer"></span>
        <a href="{slug}/{name}.html">Read</a>
        <a href="{slug}/{pdf}">PDF</a></div>
    </div>"""

FAMILY_TMPL = """  <section class="family">
    <div class="fam-head"><h2>{title}</h2><div class="fam-desc">{desc}</div></div>
    <div class="cards">
{cards}
    </div>
  </section>"""

# The set groups into threads by the number before any letter suffix: the base
# claim, the Law and its groundings, Seldon Manifolds, the two further laws, and
# the companions. Descriptions are one line each, in the register of the writing
# standard: what the thread does, not a pitch for it. Order here is the display
# order; unlisted prefixes fall through to "Further work".
PAPER_FAMILIES = [
    ("00", "The claim",
     "One sentence, argued with no machinery: what it commits to, and what it does not."),
    ("01", "The Law of Graphic Equalisation",
     "The recursive dynamics that follow from the claim. One Theory paper states the law; "
     "the Grounding papers test it against physics, cosmology, mind, communication, and "
     "consciousness. The Statement is a condensed restatement of the Theory."),
    ("02", "Seldon Manifolds",
     "The geometry of reachable futures, with its psychological and social applications."),
    ("03", "The Law of Narrative Momentum",
     "History as first-class, and persistence conditioned on cost."),
    ("04", "Narrativium",
     "What carries a story forward, treated as a quantity."),
    ("05", "Frames, Relation, and the Empty Limit",
     "Two questions the Law raises and should not answer, deflated."),
    ("06", "Assessing an Account of This Kind",
     "What a universal framework can risk, what it earns instead, and what the record shows."),
    ("07", "Causal Attitude Networks",
     "An established attitude model rebuilt as native graph rules."),
    ("08", "Certified Answers as an Audit",
     "A system that answers only when it can certify the answer, and otherwise misses honestly."),
    ("09", "Adaptability",
     "What adaptation costs, and how it is implemented."),
    ("10", "Applied Graphic Equalisation",
     "The account applied to one frame to make a separate point, rather than bridged to a "
     "field: the geopolitical and civilisational future."),
]
_FAMILY_ORDER = [p for p, _, _ in PAPER_FAMILIES]
_FAMILY_META = {p: (t, d) for p, t, d in PAPER_FAMILIES}


def family_of(name):
    """The thread a paper belongs to: the leading digits of its stem, so 01,
    01a..01f and 01s all share family '01'. Non-numeric stems (A1) get their own."""
    m = re.match(r"(\d+)", name)
    return m.group(1) if m else name.split("_")[0]


def kind_of(name):
    """Classify a paper as 'theory', 'grounding', 'condensed', 'meta',
    'implementation', or None, from its stem. This drives the labels that tell a
    reader, at a glance, what role a card plays in its thread. Most kinds follow
    the filename convention; the papers that don't carry an explicit override."""
    if name in KIND_OVERRIDE:
        return KIND_OVERRIDE[name]
    if name in GENERATED_FROM:
        return "condensed"
    if "grounding" in name or "recovery" in name:
        return "grounding"
    if "application" in name or "applied" in name:
        return "application"
    if "theory_referenced" in name:
        return "theory"
    return None


# Papers whose kind is not derivable from the filename convention. The base
# claim and the metaphysical companion are theory; the assessment is meta
# (about the account rather than part of it); the substrate rebuilds are
# implementation.
KIND_OVERRIDE = {
    "00_is": "theory",
    "05_frames_relation_and_the_empty_limit": "theory",
    "06_assessing_an_account_of_this_kind": "meta",
    "07_causal_attitude_networks_on_the_substrate": "implementation",
    "08_certified_answers_as_an_audit": "implementation",
    # Filename contains "application" but this is a bridge to a field (four
    # classical experiments put to the substrate), so it is a grounding.
    "02b_seldon_manifolds_social_and_psychological_application": "grounding",
}

# Human-readable label for each kind badge.
KIND_LABEL = {"theory": "Theory", "grounding": "Grounding", "condensed": "Condensed",
              "meta": "Meta", "implementation": "Implementation",
              "application": "Application"}


def write_website(webdir, root, plan, drafts, dry_run):
    """Emit the website bundle: per-paper folder (html + assets + versioned pdf),
    a papers.json manifest, and an index.html. Called only after every gate in
    main() has passed."""
    draft = list(drafts.values())[0]
    if dry_run:
        print("dry run -- would render %d papers to website %s" % (len(plan), webdir))
        for name, _, _ in plan:
            print("  " + name)
        return

    with tempfile.TemporaryDirectory(prefix="ocelot-web-") as work:
        rendered = build_html([n for n, _, _ in plan], root, work)

        os.makedirs(webdir, exist_ok=True)
        manifest = []
        cards_by_family = {}
        # Papers that lead the "where to start" path get a highlighted card.
        primary = {"00_is", "01a_graphic_equalisation_physics_grounding",
                   "01_law_of_graphic_equalisation_theory_referenced"}
        for name, pdf_dest, rev in plan:
            slug = name
            pdir = os.path.join(webdir, slug)
            os.makedirs(pdir, exist_ok=True)
            subdir, assets = rendered[name]
            for asset in assets:
                shutil.copy2(os.path.join(subdir, asset), os.path.join(pdir, asset))
            shutil.copy2(os.path.join(root, PAPERS, name + ".pdf"),
                         os.path.join(pdir, pdf_dest))

            src = open(os.path.join(root, PAPERS, name + ".tex"), encoding="utf-8").read()
            title, subtitle, abstract = paper_meta(src)
            pages = pdf_pages(os.path.join(pdir, pdf_dest))
            fam = family_of(name)
            kind = kind_of(name)
            # A label pill (Theory / Grounding / Condensed) so a reader can tell
            # at a glance what role a paper plays in its thread.
            kindrow = ('<div class="kind-row"><span class="kind %s">%s</span></div>\n      '
                       % (kind, KIND_LABEL[kind])) if kind else ""
            # The statement is a cut-down version of a theory paper, not a
            # separate result. Say so, and link the paper it condenses.
            note = ""
            if name in GENERATED_FROM:
                src_stem = GENERATED_FROM[name]
                src_title = paper_meta(open(os.path.join(root, PAPERS, src_stem + ".tex"),
                                            encoding="utf-8").read())[0]
                note = ('<p class="note">A condensed restatement of '
                        '<a href="%s/%s.html">%s</a> \u2014 the same paper cut down to its '
                        'claims, not a separate result.</p>\n      '
                        % (src_stem, src_stem, html.escape(src_title)))
            manifest.append({
                "name": name, "slug": slug, "title": title, "subtitle": subtitle,
                "abstract": abstract, "draft": draft, "revision": rev, "family": fam,
                "kind": kind,
                "pages": pages, "html": name + ".html", "pdf": pdf_dest,
            })
            cards_by_family.setdefault(fam, []).append(CARD_TMPL.format(
                slug=slug, name=name, pdf=pdf_dest,
                primary=(" primary" if name in primary else ""),
                badge=('<span class="start-badge">Start here</span>'
                       if name in primary else ""),
                title=html.escape(title),
                kindrow=kindrow, note=note,
                sub=('<div class="sub">%s</div>' % html.escape(subtitle)) if subtitle else "",
                abstract=html.escape(short_desc(abstract)),
                pages=("%d pages" % pages) if pages else "",
                rev=html.escape(rev)))

        # Emit families in the declared order, then any unlisted ones (e.g. A1)
        # under a catch-all so nothing is dropped.
        seen = set()
        family_blocks = []
        for fam in _FAMILY_ORDER:
            if fam in cards_by_family:
                title, desc = _FAMILY_META[fam]
                family_blocks.append(FAMILY_TMPL.format(
                    title=html.escape(title), desc=html.escape(desc),
                    cards="\n".join(cards_by_family[fam])))
                seen.add(fam)
        leftover = [f for f in cards_by_family if f not in seen]
        if leftover:
            cards = []
            for fam in sorted(leftover):
                cards.extend(cards_by_family[fam])
            family_blocks.append(FAMILY_TMPL.format(
                title="Further work", desc="", cards="\n".join(cards)))

        json.dump({"draft": draft, "papers": manifest},
                  io.open(os.path.join(webdir, "papers.json"), "w", encoding="utf-8"),
                  indent=2, ensure_ascii=False)
        io.open(os.path.join(webdir, "index.html"), "w", encoding="utf-8").write(
            INDEX_TMPL.format(draft=html.escape(draft), families="\n".join(family_blocks)))

    print("\nwebsite rendered (%s) to %s:" % (draft, webdir))
    for name, _, _ in plan:
        print("  %s/  (html + pdf)" % name)
    print("  papers.json, index.html")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.expanduser("~/ocelot-release"))
    ap.add_argument("--website", default=None,
                    help="also render the cleared papers as a website (html + "
                         "pdf + manifest) into this directory, outside the repo")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    out = os.path.abspath(a.out)
    if out == root or out.startswith(root + os.sep):
        fail("output directory %s is inside the repository" % out)
    webdir = None
    if a.website:
        webdir = os.path.abspath(a.website)
        if webdir == root or webdir.startswith(root + os.sep):
            fail("website directory %s is inside the repository" % webdir)

    try:
        metadata = load_manifest()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        fail("paper metadata is invalid: %s" % exc)
    if not INCLUDE.exists() or INCLUDE.read_text(encoding="utf-8") != render(metadata):
        fail("paper_metadata.tex is missing or stale; regenerate before releasing")
    if not set(CLEARED) <= set(metadata["papers"]):
        fail("CLEARED contains paper(s) missing from paper_metadata.json")

    drafts, plan = {}, []
    draft = metadata["draft"]
    for name in CLEARED:
        tex = os.path.join(root, PAPERS, name + ".tex")
        pdf = os.path.join(root, PAPERS, name + ".pdf")
        for p in (tex, pdf):
            if not os.path.exists(p):
                fail("%s is missing" % os.path.relpath(p, root))

        src = open(tex, encoding="utf-8").read()
        if r"\input{paper_metadata.tex}" not in src:
            fail("%s does not use generated paper metadata" % name)
        if DRAFT_RE.search(src) or REV_TEX_RE.search(src):
            fail("%s retains handwritten release metadata" % name)
        drafts[name] = draft
        text = pdftext(pdf)
        entry = metadata["papers"][name]

        if "generated_from" in entry:
            parent = entry["generated_from"]
            parent_rev = str(revision_for(metadata, parent))
            expected_stamp = "%s / statement / from long r%s" % (draft, parent_rev)
            if expected_stamp not in text:
                fail("%s.pdf is STALE or was not generated from %s r%s" %
                     (name, parent, parent_rev))
            rev = "from-r" + parent_rev
        else:
            revision = str(revision_for(metadata, name))
            expected_stamp = "%s r%s" % (draft, revision)
            if expected_stamp not in text:
                fail("%s.pdf is STALE: expected generated footer %s" %
                     (name, expected_stamp))
            rev = "r" + revision

        low = text.lower()
        for phrase in FORBIDDEN:
            if phrase in low:
                fail("%s.pdf contains %r, which sets out the excluded document's contents"
                     % (name, phrase))

        plan.append((name, pdf, "%s_%s_%s.pdf" % (name, draft, rev), rev))

    if len(set(drafts.values())) != 1:
        fail("cleared set spans several drafts: %s" % sorted(set(drafts.values())))

    # Versioned filenames mean a second run ADDS rather than replaces, so the
    # directory accumulates superseded revisions and someone sending "the papers"
    # can send a mixed set. That is the failure this gate exists to prevent,
    # reintroduced by the naming. Supersedes are moved aside, not deleted.
    keep = {dest for _, _, dest, _ in plan}
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
        for name_, pdf, dest, rev_ in plan:
            shutil.copy2(pdf, os.path.join(out, dest))
        # Ships with the papers because a covering note sent separately gets
        # separated from them. Written as an index rather than a pitch: a
        # reader who sought this out has already decided, and persuasion aimed
        # at them reads as apology. Naming where each claim is argued works
        # whoever the reader is, and does not lean on the author's standing.
        pages = {}
        for name_, pdf, dest, rev_ in plan:
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
    for _, _, dest, _ in plan:
        print("  " + dest)
    if stale:
        print("\nmoved to superseded/ (%d):" % len(stale))
        for f in stale:
            print("  " + f)
    print("\nNOT released: every other document in this repository, and the "
          "repository itself.")

    if webdir:
        # Same gate, second product. The plan carried here has already passed
        # every clearance above; write_website only renders and copies.
        web_plan = [(name, dest, rev) for name, _, dest, rev in plan]
        write_website(webdir, root, web_plan, drafts, a.dry_run)


if __name__ == "__main__":
    main()
