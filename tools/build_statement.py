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

ENVS = ('definition', 'proposition', 'corollary', 'hypothesis', 'remark')


def parse_blocks(tex):
    """label -> (env, full LaTeX source of the environment)."""
    out = {}
    for env in ENVS:
        for m in re.finditer(r'\\begin\{' + env + r'\}(\[[^\]]*\])?\\label\{([^}]+)\}',
                             tex):
            start = m.start()
            end = tex.index(r'\end{' + env + '}', start) + len(r'\end{' + env + '}')
            out[m.group(2)] = (env, tex[start:end])
    return out


def parse_falsifiers(tex):
    r"""short-name -> source, from the falsifiability section.

    Two forms are recognised, because the section carries both: the numbered
    \item commitments inside the enumerate, and any \paragraph-form commitment
    stated BEFORE the list. The composition commitment is of the second kind and
    is the one the paper calls primary, so a parser that only saw \item silently
    omitted it from the statement -- which is how it went missing.
    """
    sec = re.search(r'\\section\{Falsifiability commitments\}(.*?)'
                    r'(?=\n\\section\{)', tex, re.S)
    items = {}
    if sec:
        for pm in re.finditer(r'\\paragraph\{\\textsc\{\[(?:shape|detail)\]\}'
                              r'~?([^}]*?)\.?\}(.*?)(?=\n\\paragraph|\n\\begin|\Z)',
                              sec.group(1), re.S):
            body = pm.group(0).strip()
            items[pm.group(1).rstrip('.').lower()] = (
                r'\item \textsc{[shape]}~\textbf{%s.} %s'
                % (pm.group(1).rstrip('.'),
                   re.sub(r'^\\paragraph\{\\textsc\{\[[a-z]*\]\}~?[^}]*\}\s*',
                          '', body).strip()))
    # EVERY enumerate in the section, not just the first. Commitments added
    # after the original list -- e.g. behind an explanatory paragraph, in a
    # \begin{enumerate}[resume] -- live in a second block, and a parser that
    # stopped at the first \end{enumerate} reported them as MISSING while they
    # sat in the paper. That is how the two postulate-level commitments added
    # with the ledger correction failed to reach the statement.
    if not sec:
        return items
    for blk in re.finditer(r'\\begin\{enumerate\}(?:\[[^\]]*\])?(.*?)\\end\{enumerate\}',
                           sec.group(1), re.S):
        for it in re.split(r'\n(?=\\item )', blk.group(1)):
            it = it.strip()
            if not it.startswith(r'\item'):
                continue
            t = re.search(r'\\textbf\{([^}]*)\}', it)
            if t:
                items[t.group(1).rstrip('.').lower()] = it
    return items


def preamble_of(tex):
    """The long paper's preamble, minus anything the spec supplies itself.

    Title, author and date are the short paper's own; leaving the long paper's
    in place emits two of each and makes the identity depend on which came last.
    The running footer is rewritten to name the source revision, because a
    generated file should say what it was generated from.
    """
    pre = tex.split(r'\begin{document}')[0]
    out = []
    for line in pre.split('\n'):
        if re.match(r'\\(title|author|date)\{', line):
            continue
        out.append(line)
    pre = '\n'.join(out)

    rev = re.search(r'document revision (\d+)', tex)
    src = re.search(r'\\textsc\{(draft-\S*?)[\\}]', tex)
    stamp = (src.group(1) if src else 'draft') + ' / statement / from long r' + \
            (rev.group(1) if rev else '?')
    pre = re.sub(r'\\textsc\{draft-[^}]*\}', lambda m: '\\textsc{' + stamp + '}', pre)
    return pre


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
    falsifiers = parse_falsifiers(long_tex)

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
    text = re.sub(r'~?\\ref\{([^}]+)\}',
                  lambda m: m.group(0) if m.group(1) in have else '~(long form)',
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
        m = re.match(r'^(.*?)\((\d{4}[a-z]?)\)$', lab.strip())
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
            refs = ['', r'\begin{thebibliography}{99}', r'\itemsep=2pt',
                    r'\item[] \small\emph{The works named above, listed from the long paper so the two cannot disagree.}',
                    '']
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
        '%% Regenerate: tools/build_statement.py %s\n'
        '%% ==========================================================\n'
        % (src_rel, os.path.basename(spec_path), os.path.relpath(spec_path,
           os.path.dirname(os.path.dirname(os.path.abspath(spec_path)))))
    )
    out_path = os.path.join(root, out_rel)
    io.open(out_path, 'w', encoding='utf-8').write(
        banner + preamble_of(long_tex) + '\n'.join(body) + '\n')

    unpulled = sorted(set(blocks) - pulled)
    # Falsifier drift is reported in BOTH directions. A spec asking for a
    # falsifier the paper no longer has is a hard error above; a paper carrying
    # a commitment the spec does not pull is a silent gap, because the short
    # form's own framing implies it lists what the account fails on. Same
    # asymmetry that let a stale spec title through once already.
    unpulled_fals = sorted(k for k in falsifiers
                           if ('falsifier:' + k) not in pulled)
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
