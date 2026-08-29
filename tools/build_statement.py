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
    r"""short-name -> \item source, from the falsifiability enumerate."""
    m = re.search(r'\\section\{Falsifiability commitments\}.*?\\begin\{enumerate\}'
                  r'(.*?)\\end\{enumerate\}', tex, re.S)
    if not m:
        return {}
    items = {}
    for it in re.split(r'\n(?=\\item )', m.group(1)):
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
    text = re.sub(r'\s*\\citep\{[^}]+\}', ' (long form)', text)
    text = re.sub(r'\\citet\{[^}]+\}', 'the long form', text)
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
