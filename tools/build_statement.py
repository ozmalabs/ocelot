#!/usr/bin/env python3
"""Generate the STATEMENT of a paper from the paper plus a spec of statement-only content.

The long paper is the single source of truth for every shared block: definitions,
propositions, corollaries, hypotheses, remarks and falsifiability items are PULLED
by label at build time, never copied. The spec supplies the statement's own prose
and its running order.

The long paper is the case for the theory; the generated document is the theory
stated. The split is demonstration versus statement, not full versus abridged --
which is why length is not a design goal here and never was a good name for it.

Usage:  tools/build_statement.py papers/formal/01s.spec
Output: the .tex named by the spec's @out directive, overwritten in place.

Exits non-zero if a pulled label is missing (a rename in the long paper must not
silently drop content), and reports every labelled block in the long paper that the
spec does not pull, so drift in the other direction stays visible.
"""
import io, os, re, sys

# 'axiom' and 'theorem' are pulled too. They were absent from this tuple while
# the long paper carried both, so the two axioms and the identity theorem were
# unreachable by @pull -- a spec asking for them got MISSING and the omission
# read as a decision rather than as the parser gap it was.
ENVS = ('definition', 'proposition', 'corollary', 'hypothesis', 'remark',
        'axiom', 'theorem')


def parse_blocks(tex):
    """label -> (env, full LaTeX source of the environment)."""
    out = {}
    for env in ENVS:
        for m in re.finditer(r'\\begin\{' + env + r'\}(\[[^\]]*\])?\\label\{([^}]+)\}',
                             tex):
            start = m.start()
            end = tex.index(r'\end{' + env + '}', start) + len(r'\end{' + env + '}')
            out[m.group(2)] = (env, tex[start:end])
    # Floating tables are pulled by their \label too (the ledger is one). The
    # label sits inside the caption rather than on the \begin line, so the
    # environment is found first and its label read from inside it.
    for m in re.finditer(r'\\begin\{table\}', tex):
        start = m.start()
        end = tex.index(r'\end{table}', start) + len(r'\end{table}')
        src = tex[start:end]
        lab = re.search(r'\\label\{([^}]+)\}', src)
        if lab:
            out[lab.group(1)] = ('table', src)
    return out


def parse_falsifiers(tex):
    r"""(short-name -> source, short-name -> display title), in the long paper's order.

    The display title is kept alongside the source because the statement now
    prints the commitments it does NOT carry, by title, and a lowercased lookup
    key is not a title. Insertion order is the long paper's order, which is the
    order that list is printed in.

    Two forms are recognised, because the section carries both: the numbered
    \item commitments inside the enumerate, and any \paragraph-form commitment
    stated BEFORE the list. The composition commitment is of the second kind and
    is the one the paper calls primary, so a parser that only saw \item silently
    omitted it from the statement -- which is how it went missing.
    """
    sec = re.search(r'\\section\{Falsifiability commitments\}(.*?)'
                    r'(?=\n\\section\{)', tex, re.S)
    items, titles = {}, {}
    if sec:
        # The mark may be wrapped in \textnormal, because bold small caps have no
        # shape in lmodern and the \paragraph head is bold. A parser that only
        # knew the bare form reported the composition commitment as MISSING.
        for pm in re.finditer(r'\\paragraph\{(?:\\textnormal\{)?'
                              r'\\textsc\{\[(?:shape|detail)\]\}\}?'
                              r'~?([^}]*?)\.?\}(.*?)(?=\n\\paragraph|\n\\begin|\Z)',
                              sec.group(1), re.S):
            body = pm.group(0).strip()
            items[pm.group(1).rstrip('.').lower()] = (
                r'\item \textsc{[shape]}~\textbf{%s.} %s'
                % (pm.group(1).rstrip('.'),
                   re.sub(r'^\\paragraph\{(?:\\textnormal\{)?\\textsc\{\[[a-z]*\]\}\}?'
                          r'~?[^}]*\}\s*', '', body).strip()))
            titles[pm.group(1).rstrip('.').lower()] = pm.group(1).rstrip('.')
    # EVERY enumerate in the section, not just the first. Commitments added
    # after the original list -- e.g. behind an explanatory paragraph, in a
    # \begin{enumerate}[resume] -- live in a second block, and a parser that
    # stopped at the first \end{enumerate} reported them as MISSING while they
    # sat in the paper. That is how the two postulate-level commitments added
    # with the ledger correction failed to reach the statement.
    if not sec:
        return items, titles
    for blk in re.finditer(r'\\begin\{enumerate\}(?:\[[^\]]*\])?(.*?)\\end\{enumerate\}',
                           sec.group(1), re.S):
        for it in re.split(r'\n(?=\\item )', blk.group(1)):
            it = it.strip()
            if not it.startswith(r'\item'):
                continue
            t = re.search(r'\\textbf\{([^}]*)\}', it)
            if t:
                items[t.group(1).rstrip('.').lower()] = it
                titles[t.group(1).rstrip('.').lower()] = t.group(1).rstrip('.')
    return items, titles


def parse_aux(aux_path):
    r"""label -> printed number, from the long paper's .aux.

    A title tells a reader what to look for; a number tells them where it is.
    The numbers are read rather than computed, because the statement renumbers
    everything it pulls and only the long paper's own compile knows what the
    long paper calls a block. Absent aux (a clean tree, a first build) is not an
    error -- the caller falls back to the title-only form.
    """
    try:
        aux = io.open(aux_path, encoding='utf-8').read()
    except IOError:
        return {}
    out = {}
    for m in re.finditer(r'\\newlabel\{([^}]+)\}\{\{([^{}]*)\}\{', aux):
        lab, num = m.group(1), m.group(2).strip()
        if lab.endswith('@cref') or not num:
            continue
        out.setdefault(lab, num)
    return out


def preamble_of(tex, body_text=''):
    r"""The long paper's preamble, minus anything the spec supplies itself.

    Title, author and date are the short paper's own; leaving the long paper's
    in place emits two of each and makes the identity depend on which came last.
    The running footer is rewritten to name the source revision, because a
    generated file should say what it was generated from.

    The \input of the generated counts file goes too, unless the statement
    actually uses one of its macros: the counts are claims about the LONG
    paper's size, and a generated document carrying a dependency it never reads
    is a file that fails to build for a reason it has no stake in.
    """
    pre = tex.split(r'\begin{document}')[0]
    uses_counts = any(('\\' + macro) in body_text for macro, _ in COUNT_MACROS) \
        or '\\nResults' in body_text or '\\nBibitems' in body_text \
        or '\\nCited' in body_text or '\\nSections' in body_text \
        or '\\nParts' in body_text
    out = []
    for line in pre.split('\n'):
        if re.match(r'\\(title|author|date)\{', line):
            continue
        if not uses_counts and re.match(r'\s*\\input\{[^}]*counts[^}]*\}\s*$', line):
            continue
        out.append(line)
    pre = '\n'.join(out)

    # The copied long-paper metadata include resolves its values against the
    # generated statement's jobname. Replace the ordinary footer presentation
    # with the statement form; its revision is then derived from the manifest's
    # declared long-paper parent rather than scraped from source text.
    pre = pre.replace(
        r'\fancyfoot[R]{\scriptsize\textsc{\PaperDraft\,r\PaperRevision}}',
        r'\fancyfoot[R]{\scriptsize\PaperFooterStamp}')
    return pre


COUNT_MACROS = (
    ('nDefinitions', 'definition'), ('nPropositions', 'proposition'),
    ('nRemarks', 'remark'), ('nCorollaries', 'corollary'),
    ('nHypotheses', 'hypothesis'), ('nTheorems', 'theorem'),
    ('nAxioms', 'axiom'),
)


def write_counts(long_tex, out_path, src_rel):
    r"""Emit \newcommand counts computed from the paper itself.

    A count written by hand drifts, and drifts silently, because a reader
    checking the prose has no way to recount 3000 lines. The counts here are
    regenerated on every build from the same file the prose sits in, so the
    claim and the thing claimed cannot come apart.
    """
    counts = {}
    for macro, env in COUNT_MACROS:
        counts[macro] = len(re.findall(r'\\begin\{' + env + r'\}', long_tex))
    counts['nResults'] = sum(counts[m] for m, _ in COUNT_MACROS)
    counts['nBibitems'] = len(re.findall(r'\\bibitem', long_tex))
    keys = set()
    for m in re.finditer(r'\\cite[a-z]*(?:\[[^\]]*\])*\{([^}]+)\}', long_tex):
        for k in m.group(1).split(','):
            keys.add(k.strip())
    counts['nCited'] = len(keys)
    counts['nSections'] = len(re.findall(r'(?m)^\\section\{', long_tex))
    counts['nParts'] = len(re.findall(r'(?m)^\\part\{', long_tex))
    lines = ['%% GENERATED by tools/build_statement.py from %s --- DO NOT EDIT.' % src_rel]
    for k in ('nDefinitions', 'nPropositions', 'nRemarks', 'nCorollaries',
              'nHypotheses', 'nTheorems', 'nAxioms', 'nResults', 'nBibitems',
              'nCited', 'nSections', 'nParts'):
        lines.append('\\newcommand{\\%s}{%d}' % (k, counts[k]))
    io.open(out_path, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    return counts


def main(spec_path):
    root = os.path.dirname(os.path.abspath(spec_path))
    spec = io.open(spec_path, encoding='utf-8').read().split('\n')

    src_rel = out_rel = None
    for ln in spec:
        if ln.startswith('@source '):
            src_rel = ln[8:].strip()
        elif ln.startswith('@out '):
            out_rel = ln[5:].strip()
    if not src_rel or not out_rel:
        sys.exit('spec must declare @source and @out')

    src_path = os.path.join(root, src_rel)
    long_tex = io.open(src_path, encoding='utf-8').read()
    blocks = parse_blocks(long_tex)
    falsifiers, fals_titles = parse_falsifiers(long_tex)
    aux_numbers = parse_aux(os.path.splitext(src_path)[0] + '.aux')

    counts_rel = os.path.splitext(src_rel)[0].split('_')[0] + '.counts.tex'
    counts = write_counts(long_tex, os.path.join(root, counts_rel), src_rel)

    body, pulled, missing = [], set(), []
    for ln in spec:
        if ln.startswith('#') or ln.startswith('@source') or ln.startswith('@out'):
            continue
        if ln.startswith('@preamble'):
            continue
        m = re.match(r'@pull\s+(\S+)', ln)
        if m:
            key = m.group(1)
            if key in blocks:
                body.append(blocks[key][1]); pulled.add(key)
            else:
                missing.append(key)
            continue
        m = re.match(r'@falsifier\s+(.+)', ln)
        if m:
            key = m.group(1).strip().lower()
            if key in falsifiers:
                body.append(falsifiers[key]); pulled.add('falsifier:' + key)
            else:
                missing.append('falsifier:' + key)
            continue
        body.append(ln)

    if missing:
        sys.exit('MISSING in %s:\n  %s' % (src_rel, '\n  '.join(missing)))

    # Cross-references and citations that the abridgement does not carry are
    # rewritten to point at the long form rather than left to dangle. A short
    # paper full of undefined-reference warnings is a short paper nobody checks.
    text = '\n'.join(body)
    have = set(re.findall(r'\\label\{([^}]+)\}', text))
    # An unpulled target is NAMED rather than blanked. "(long form)" told a reader
    # nothing and appeared 31 times; the environment's own title tells them what to
    # look for. Titles come from the long paper's optional argument.
    titles = dict(re.findall(
        r'\\begin\{(?:definition|proposition|corollary|hypothesis|remark|axiom|theorem)\}'
        r'\[([^\]]*)\]\\label\{([^}]+)\}', long_tex))
    titles = {lab: t for t, lab in titles.items()}
    sects = dict(re.findall(r'\\section\{([^}]*)\}\\label\{([^}]+)\}', long_tex))
    sects = {lab: t for t, lab in sects.items()}

    # And it carries the long paper's NUMBER wherever the long paper's own .aux
    # has one. A title is findable by search; a number is where to turn to. The
    # environment name comes from the block table, so "Proposition 12.4" is read
    # off the same parse that would have pulled the block.
    def _envname(lab):
        env = blocks.get(lab, (None,))[0]
        return env.capitalize() if env else None

    def _refname(lab):
        num = aux_numbers.get(lab)
        if lab in titles:
            env = _envname(lab)
            # The source already names the kind ("Remark~\ref{..}"), so the
            # rendering supplies only the number and the title, not the kind
            # again: "Remark~3.11 of the long paper (\emph{...})".
            if num and env:
                return '~%s of the long paper (\\emph{%s})' % (num, titles[lab])
            return '~(\\emph{%s}, long form)' % titles[lab]
        if lab in sects:
            if num:
                return '~%s of the long paper (\\emph{%s})' % (num, sects[lab])
            return '~(\\emph{%s}, long form)' % sects[lab]
        return '~(long form)'

    # Labels reached through xr's \externaldocument[prefix]{...} resolve in the
    # statement exactly as in the long paper (the preamble is copied), so they
    # are kept rather than rewritten.
    ext = tuple(re.findall(r'\\externaldocument\[([^\]]+)\]', long_tex))

    def _keep(lab):
        return lab in have or lab.startswith(ext)

    text = re.sub(r'~?\\ref\{([^}]+)\}',
                  lambda m: m.group(0) if _keep(m.group(1)) else _refname(m.group(1)),
                  text)
    # Citations are rendered as plain author-year text taken from the long
    # paper's own bibitem labels. The previous behaviour rewrote every \citet
    # to "the long form", which silently ATTRIBUTED cited work to this
    # programme -- Bochvar's 1938 calculus was printed as "the long form's
    # three-valued calculus". Erasing a citation is not a neutral abridgement.
    biblabels = dict(re.findall(r'\\bibitem\[([^\]]*)\]\{([^}]+)\}',
                                long_tex))
    biblabels = {k: v for v, k in biblabels.items()}

    def _label(key, textual):
        lab = biblabels.get(key.strip())
        if not lab:
            return None
        # No trailing anchor: natbib's full label form carries the author list
        # AFTER the year -- "Osvik et~al.(2006)Osvik, Shamir, and Tromer" -- so a
        # regex anchored at the end failed to match and the whole raw label was
        # emitted verbatim into the text. The year in parentheses is the split
        # point wherever it falls.
        m = re.match(r'^(.*?)\((\d{4}[a-z]?)\)', lab.strip())
        if not m:
            return lab.strip()
        who, year = m.group(1).strip(), m.group(2)
        return '%s (%s)' % (who, year) if textual else '%s, %s' % (who, year)

    # Keys actually named in the statement, in first-appearance order. The
    # flattened text carries no \cite commands, so without this the document
    # made ~16 named attributions a reader could not resolve to anything --
    # erasing the bibliography is not a neutral abridgement either.
    cited = []

    def _cite(m, textual):
        keys = [k.strip() for k in m.group(1).split(',')]
        out = [_label(k, textual) for k in keys]
        if any(o is None for o in out):
            return 'the long form' if textual else ' (long form)'
        for k in keys:
            if k not in cited:
                cited.append(k)
        joined = '; '.join(out)
        return joined if textual else ' (%s)' % joined

    text = re.sub(r'\s*\\citep(?:\[[^\]]*\])?\{([^}]+)\}',
                  lambda m: _cite(m, False), text)
    text = re.sub(r'\\citet(?:\[[^\]]*\])?\{([^}]+)\}',
                  lambda m: _cite(m, True), text)
    text = re.sub(r'\\citealp\{([^}]+)\}', lambda m: _cite(m, False).strip(' ()'), text)

    # The spec's own sentence says the omitted commitments are listed below by
    # title. Reporting them to the builder's terminal made that true of the
    # build log and not of the artefact, and the reader of the PDF is who the
    # sentence addresses. Generated from the same parse the @falsifier pulls
    # use, in the long paper's order, so it cannot drift from either.
    not_carried = [fals_titles[k] for k in falsifiers
                   if ('falsifier:' + k) not in pulled and k in fals_titles]
    if not_carried:
        ix = text.find(r'\section{Falsifiability}')
        j = text.rfind(r'\end{enumerate}') if ix < 0 else \
            text.rfind(r'\end{enumerate}', ix)
        if j >= 0:
            j += len(r'\end{enumerate}')
            text = (text[:j]
                    + '\n\n\\medskip\\noindent\\emph{Not carried in this '
                      'statement:} ' + '; '.join(not_carried) + '.\n'
                    + text[j:])

    # Emit a reference list for exactly the works the statement names, lifted
    # verbatim from the long paper so the two can never disagree. Sorted by
    # the author-year label, since the flattened text gives the reader a name
    # and a year to look up rather than a number.
    if cited:
        entries = {}
        for k in cited:
            m = re.search(r'\\bibitem\[[^\]]*\]\{' + re.escape(k) + r'\}.*?(?=\n\n|\n\\bibitem|\n\\end\{thebibliography\})',
                          long_tex, re.S)
            if m:
                entries[k] = m.group(0).rstrip()
        if entries:
            # The note is ABOUT the list, so it sits before it. As an \item[]
            # inside the environment it typeset correctly and was, structurally,
            # a bibliography entry.
            refs = ['',
                    r'\noindent\small\emph{The works named above, listed from the long paper so the two cannot disagree.}',
                    '', r'\begin{thebibliography}{99}', r'\itemsep=2pt', '']
            for k in sorted(entries, key=lambda k: biblabels.get(k, k)):
                refs.append(entries[k]); refs.append('')
            refs.append(r'\end{thebibliography}')
            text = text.replace(r'\end{document}', '\n'.join(refs) + '\n' + r'\end{document}', 1)
    body = [text]

    banner = (
        '%% ==========================================================\n'
        '%% GENERATED FILE --- DO NOT EDIT.\n'
        '%% Source of truth: %s\n'
        '%% Statement-only content: %s\n'
        '%% Regenerate, from the repository root:\n'
        '%% python3 tools/build_statement.py %s\n'
        '%% ==========================================================\n'
        # The path as the command is actually typed, from the repository
        # root, so the spec's own regeneration note and this header name one
        # command rather than two that differ in their base directory.
        % (src_rel, os.path.basename(spec_path),
           os.path.relpath(os.path.abspath(spec_path), os.getcwd()))
    )
    out_path = os.path.join(root, out_rel)
    text = banner + preamble_of(long_tex, '\n'.join(body)) + '\n'.join(body) + '\n'

    # Anything emitted after \end{document} is in the file and not in the PDF.
    # The generator reported success and the falsifiability list looked whole,
    # because "did the spec name resolve" and "did the content get typeset" are
    # different questions and only the first was being asked. A spec directive
    # placed after the one that closes the document is enough to cause it.
    tail = text.split(r'\end{document}')
    if len(tail) > 1 and tail[-1].strip():
        stray = [ln for ln in tail[-1].splitlines() if ln.strip()]
        raise SystemExit(
            'ERROR: %d line(s) emitted after \\end{document} and would not be '
            'typeset.\n  First: %s\n  Cause is usually a spec directive placed '
            'below the one that closes the document; move it into its own '
            'block.' % (len(stray), stray[0][:90]))

    io.open(out_path, 'w', encoding='utf-8').write(text)

    unpulled = sorted(set(blocks) - pulled)
    # Falsifier drift is reported in BOTH directions. A spec asking for a
    # falsifier the paper no longer has is a hard error above; a paper carrying
    # a commitment the spec does not pull is a silent gap, because the short
    # form's own framing implies it lists what the account fails on. Same
    # asymmetry that let a stale spec title through once already.
    unpulled_fals = sorted(k for k in falsifiers
                           if ('falsifier:' + k) not in pulled)
    print('wrote %s  (%s)' % (counts_rel, ', '.join(
        '%s=%d' % (k, counts[k]) for k in sorted(counts))))
    print('wrote %s  (%d blocks pulled, %d falsifiers)'
          % (out_rel, len([p for p in pulled if not p.startswith('falsifier:')]),
             len([p for p in pulled if p.startswith('falsifier:')])))
    if unpulled_fals:
        print('\nfalsifiers NOT pulled (%d of %d) --- the statement implies it '
              'lists what the account fails on:' % (len(unpulled_fals),
                                                    len(falsifiers)))
        for k in unpulled_fals:
            print('  %s' % k)
    if unpulled:
        print('\nnot pulled (%d) --- review when the long paper gains material:'
              % len(unpulled))
        for k in unpulled:
            print('  %-28s %s' % (k, blocks[k][0]))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else sys.exit(__doc__))
