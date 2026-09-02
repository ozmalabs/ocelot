#!/usr/bin/env python3
r"""Generate the record figures 06 quotes, computed from the repository.

06 (\emph{Assessing an Account of This Kind}) reports figures from the
engineering record --- the size of the Rust core, the number of seed manifests,
how much of the results directory is tracked, the enumerated failure baseline,
the pre-registration backlog, the size of the term language. Written by hand
those drift, and drift silently: a reader checking the prose cannot recount a
repository, and the paper's own \texttt{sec:record-wrong} is an argument against
exactly that habit. So they are regenerated here from the record itself, and the
header names the commit and the date they were read at, because a figure without
its measurement conditions is the defect this paper spends a section on.

This is the counterpart of \texttt{tools/build\_statement.py}'s
\texttt{write\_counts}, which does the same job for the figures 01 quotes about
itself. Nothing here is agent logic: it is a mechanical read of the working tree.

Usage:  tools/build_assessment_counts.py
Output: papers/formal/06.counts.tex, overwritten in place.
"""
import io
import json
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'papers', 'formal', '06.counts.tex')


def _run(*args):
    return subprocess.check_output(args, cwd=ROOT).decode('utf-8', 'replace')


def rust_source_files():
    """Files of Rust source under the engine's src tree."""
    n = 0
    for r, _d, fs in os.walk(os.path.join(ROOT, 'runners', 'dsl', 'src')):
        n += sum(1 for f in fs if f.endswith('.rs'))
    return n


def seed_manifests():
    """Top-level seed manifests --- the agent's cognition as graph data."""
    d = os.path.join(ROOT, 'seeds')
    return sum(1 for f in os.listdir(d) if f.endswith('.json'))


def results_tracked_and_on_disk():
    """(tracked under version control, present in the working tree).

    The gap between the two is the paper's `most of the evidence is untracked'.
    """
    tracked = len([ln for ln in _run('git', 'ls-files', 'results').split('\n') if ln.strip()])
    disk = len(os.listdir(os.path.join(ROOT, 'results')))
    return tracked, disk


def term_variants():
    r"""Variants of the term language's enum in runners/dsl/src/term.rs.

    The enum is `pub enum TermNode' (not `Term'); its variants are the
    graph-resident primitives the agent composes. Counted by walking the enum
    body and taking every identifier at brace depth zero, so struct-variant
    fields and doc comments are not miscounted as variants.
    """
    src = io.open(os.path.join(ROOT, 'runners', 'dsl', 'src', 'term.rs'),
                  encoding='utf-8').read()
    i = src.index('pub enum TermNode')
    j = src.index('{', i)
    depth = 0
    end = None
    for k in range(j, len(src)):
        if src[k] == '{':
            depth += 1
        elif src[k] == '}':
            depth -= 1
            if depth == 0:
                end = k
                break
    if end is None:
        sys.exit('term.rs: unterminated `pub enum TermNode`')
    variants, depth = [], 0
    for ln in src[j + 1:end].split('\n'):
        s = ln.strip()
        if depth == 0 and not s.startswith('//'):
            m = re.match(r'^([A-Z][A-Za-z0-9_]*)\s*(\{|\(|,|$)', s)
            if m:
                variants.append(m.group(1))
        depth += ln.count('{') - ln.count('}')
    if len(variants) != len(set(variants)):
        sys.exit('term.rs: duplicate variant names in TermNode')
    return len(variants)


def prereg_without_results():
    """Pre-registration stems under docs/research with no matching results file.

    A stem is `X' in `X_PREREG.md'; it is satisfied by an `X_RESULTS.md'
    anywhere under docs/research, since the two are not always filed together.
    """
    stems, res = set(), set()
    for r, _d, fs in os.walk(os.path.join(ROOT, 'docs', 'research')):
        for f in fs:
            if f.endswith('_PREREG.md'):
                stems.add(f[:-len('_PREREG.md')])
            elif f.endswith('_RESULTS.md'):
                res.add(f[:-len('_RESULTS.md')])
    return len(stems - res), len(stems)


def failure_baseline():
    r"""The enumerated failure baseline: the list, not a count of it.

    `total' is derived from `entries' and the file says so; it is recomputed
    here rather than trusted, and the two must agree. `files_swept' is the
    coverage figure and is NOT green + red: a swept file may also be
    NOT_ESTABLISHED (exceeded the per-file time budget) or ALL_SKIPPED (every
    test in it guarded out by a missing optional dependency).
    """
    d = json.load(io.open(os.path.join(ROOT, 'results', 'failure_baseline.json'),
                          encoding='utf-8'))
    entries = len(d['entries'])
    if d['total'] != entries:
        sys.exit('failure_baseline.json: total %d != len(entries) %d'
                 % (d['total'], entries))
    cov = d['coverage']
    green, red = d['files_green'], d['files_red']
    swept = cov['files_swept']
    other = sum(len(v) for k, v in cov.items() if isinstance(v, list))
    if green + red + other != swept:
        sys.exit('failure_baseline.json: %d green + %d red + %d unestablished '
                 '!= %d swept' % (green, red, other, swept))
    return {
        'entries': entries,
        'green': green,
        'red': red,
        'swept': swept,
        'other': other,
        'measured_at': d['measured_at'].split('T')[0],
    }


def _texdate(iso):
    y, m, dd = iso.split('-')
    months = ('January', 'February', 'March', 'April', 'May', 'June', 'July',
              'August', 'September', 'October', 'November', 'December')
    return '%d %s %s' % (int(dd), months[int(m) - 1], y)


def main():
    tracked, disk = results_tracked_and_on_disk()
    prereg_missing, prereg_total = prereg_without_results()
    base = failure_baseline()
    head = _run('git', 'rev-parse', 'HEAD').strip()
    read_on = time.strftime('%Y-%m-%d')

    counts = [
        ('nRustFiles', rust_source_files()),
        ('nTermVariants', term_variants()),
        ('nSeedManifests', seed_manifests()),
        ('nResultsTracked', tracked),
        ('nResultsOnDisk', disk),
        ('nPreregNoResults', prereg_missing),
        ('nPreregTotal', prereg_total),
        ('nBaselineRed', base['entries']),
        ('nFilesSwept', base['swept']),
        ('nFilesGreen', base['green']),
        ('nFilesRed', base['red']),
        ('nFilesUnestablished', base['other']),
    ]
    lines = [
        '%% GENERATED by tools/build_assessment_counts.py --- DO NOT EDIT.',
        '%%%% Read from the repository at commit %s on %s.' % (head, read_on),
        '%%%% The failure baseline was measured at %s under the conditions its'
        % base['measured_at'],
        '%% own file records; every other figure is the working tree at the'
        ' commit above.',
    ]
    for k, v in counts:
        lines.append('\\newcommand{\\%s}{%s}' % (k, '{:,}'.format(v).replace(',', '{,}')))
    lines.append('\\newcommand{\\countsCommit}{\\texttt{%s}}' % head[:12])
    lines.append('\\newcommand{\\countsReadOn}{%s}' % _texdate(read_on))
    lines.append('\\newcommand{\\baselineMeasuredOn}{%s}' % _texdate(base['measured_at']))
    io.open(OUT, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    for k, v in counts:
        print('%-22s %s' % (k, v))
    print('%-22s %s' % ('commit', head))
    print('%-22s %s' % ('baseline measured', base['measured_at']))
    print('wrote', os.path.relpath(OUT, ROOT))


if __name__ == '__main__':
    main()
