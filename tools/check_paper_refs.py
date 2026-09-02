#!/usr/bin/env python3
r"""Fail if a numbered result is named in prose without a \ref to it.

C.5 of the r273 review: several load-bearing results were referred to by name
("the antecedent-state principle", "the reflection theorem") from a dozen sites
while carrying no \label at all, so nothing could have caught the drift. This is
the lint that would have.

Declaration sites are exempt, because that is where the name is being GIVEN
rather than used: section headings, an environment's own optional-argument
title, the bold lead-in of a falsifiability item, and the bibliography.

Usage: tools/check_paper_refs.py papers/formal/01_law_of_graphic_equalisation_theory_referenced.tex
"""
import io, re, sys

PHRASES = [
    'antecedent-state principle',
    'reflection theorem',
    'Graph Law',
    'Minimal graph sufficiency',
    'Discrete sufficiency',
]

DECL = re.compile(
    r'\\(?:sub)*section\{[^}]*\}'
    r'|\\paragraph\{(?:[^{}]|\{[^{}]*\})*\}'
    r'|\\begin\{[a-z]+\}\[[^\]]*\]'
    r'|\\textbf\{[^}]*\}')


def main(path):
    tex = io.open(path, encoding='utf-8').read()
    tex = tex.split(r'\begin{thebibliography}')[0]
    tex = DECL.sub(' ', tex)
    bad = []
    for sent in re.split(r'(?<=[.:;!?])\s', tex):
        if r'\ref{' in sent:
            continue
        for ph in PHRASES:
            if re.search(re.escape(ph), sent, re.I):
                bad.append((ph, ' '.join(sent.split())[:110]))
    for ph, s in bad:
        print('NO \\ref near "%s": %s' % (ph, s))
    print('%s: %d unreferenced by-name mention(s)' % (path, len(bad)))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else sys.exit(__doc__)))
