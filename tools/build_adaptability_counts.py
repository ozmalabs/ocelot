#!/usr/bin/env python3
r"""Generate the record figures 09a quotes, computed from the repository.

09a (\emph{Adaptability --- Implementation}) is a report from the engineering
record: how many rules the seed manifests carry, how many distinct recognisers
the rule corpus holds, which of the transform-algebra terms any rule actually
invokes, and how much of the analogy faculty lives in the host language. Written
by hand those drift, and drift silently --- and the paper's own abstract says
every count in it was obtained by running a command against the tree, which is
a promise a hand-held number cannot keep. So they are regenerated here, and the
header names the commit and the date they were read at.

This is the counterpart of tools/build_assessment_counts.py, which does the same
job for 06. Nothing here is agent logic: it is a mechanical read of the tree.

Two figures deserve their conditions stated.

  * The distinct-recogniser count is computed by the method the sizing record
    used: over every top-level seed manifest, every rule with a non-null match
    contributes the key json(match)|json(where), and the distinct keys are
    counted. That method is reproduced here rather than trusted, so the number
    below is TODAY's corpus. The record's own figure, taken against the corpus
    as it stood when the parallelogram transfer was measured, was larger; it is
    carried separately as \nRecognisersAtRecord with its date, because the
    novelty of the derived rule was established against that corpus and not
    against this one.

  * The per-term census is an EXACT term-node match --- a JSON object whose
    "type" is the term's name --- walked over the parsed manifest, not a
    substring search of its text. The distinction is load-bearing: the name of
    the witness-discarding operation is a substring of the witness-retaining
    one's, and the name of the substitution operation occurs in manifests that
    never invoke it. Both file counts and invocation counts are emitted, and a
    substring-only file count is emitted for substitution so the paper can say
    what the looser search would have found.

Usage:  tools/build_adaptability_counts.py
Output: papers/formal/09a.counts.tex, overwritten in place.
"""
import io
import json
import os
import re
import subprocess
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEEDS = os.path.join(ROOT, 'seeds')
OUT = os.path.join(ROOT, 'papers', 'formal', '09a.counts.tex')

# The faculty that calls the transform algebra from the host language.
FACULTY = os.path.join(ROOT, 'domains', 'analogical_thinking.py')

# Term name -> the macro stem the paper uses for it. The paper never prints a
# term name; these stems are what it prints counts of.
TERMS = [
    ('AntiUnifyWitness', 'WitnessRetaining'),
    ('AntiUnify',        'WitnessDiscarding'),
    ('Covers',           'Coverage'),
    ('CoversOpen',       'OpenCoverage'),
    ('Unify',            'Unification'),
    ('Substitute',       'Substitution'),
    ('StructSim',        'StructuralSimilarity'),
]

# The figure the sizing record established the transfer's novelty against, with
# the date that record was written. Read from the record, not recomputed: the
# seed corpus has grown since, so recomputing it would answer a different
# question from the one the transfer was checked against.
RECOGNISERS_AT_RECORD = 2851
RECORD_DATE = '2026-08-12'


def _run(*args):
    return subprocess.check_output(args, cwd=ROOT).decode('utf-8', 'replace')


def manifests():
    """Top-level seed manifests --- the agent's cognition as graph data."""
    return sorted(f for f in os.listdir(SEEDS) if f.endswith('.json'))


def _load(fn):
    try:
        blob = json.load(io.open(os.path.join(SEEDS, fn), encoding='utf-8'))
    except Exception:
        return None
    return blob if isinstance(blob, dict) else None


def rules_and_recognisers():
    """(rules carried by the manifests, distinct match|where recognisers).

    The recogniser key is the sizing record's: rules with a null match do not
    recognise anything and are not counted.
    """
    n, corpus = 0, set()
    for fn in manifests():
        blob = _load(fn)
        if blob is None:
            continue
        for r in blob.get('rules', []) or []:
            if not isinstance(r, dict):
                continue
            n += 1
            if r.get('match') is not None:
                corpus.add(json.dumps(r.get('match'), sort_keys=True) + '|'
                           + json.dumps(r.get('where'), sort_keys=True))
    return n, len(corpus)


def term_census():
    """{term: (manifests invoking it, invocations)} by exact term-node match."""
    names = {t for t, _ in TERMS}
    files = {t: set() for t in names}
    uses = {t: 0 for t in names}

    def walk(o, fn):
        if isinstance(o, dict):
            t = o.get('type')
            if isinstance(t, str) and t in names:
                files[t].add(fn)
                uses[t] += 1
            for v in o.values():
                walk(v, fn)
        elif isinstance(o, list):
            for v in o:
                walk(v, fn)

    for fn in manifests():
        blob = _load(fn)
        if blob is not None:
            walk(blob, fn)
    return {t: (len(files[t]), uses[t]) for t in names}


def substring_files(term):
    """Manifests whose TEXT carries the term's name, invoked or not."""
    n = 0
    for fn in manifests():
        if term in io.open(os.path.join(SEEDS, fn), encoding='utf-8',
                           errors='replace').read():
            n += 1
    return n


def faculty():
    """(occurrences of the witness-retaining term, lines) in the host module."""
    src = io.open(FACULTY, encoding='utf-8').read()
    return len(re.findall(r'\bAntiUnifyWitness\b', src)), len(src.splitlines())


def _texdate(iso):
    y, m, d = iso.split('-')
    months = ('January', 'February', 'March', 'April', 'May', 'June', 'July',
              'August', 'September', 'October', 'November', 'December')
    return '%d %s %s' % (int(d), months[int(m) - 1], y)


def main():
    n_rules, n_recog = rules_and_recognisers()
    census = term_census()
    n_witness, n_lines = faculty()
    head = _run('git', 'rev-parse', 'HEAD').strip()
    read_on = time.strftime('%Y-%m-%d')

    counts = [
        ('nRules', n_rules),
        ('nManifests', len(manifests())),
        ('nRecognisers', n_recog),
        ('nRecognisersAtRecord', RECOGNISERS_AT_RECORD),
        ('nWitnessInFaculty', n_witness),
        ('nFacultyLines', n_lines),
    ]
    for term, stem in TERMS:
        f, u = census[term]
        counts.append(('n%sFiles' % stem, f))
        counts.append(('n%sUses' % stem, u))
    counts.append(('nSubstitutionNamedFiles', substring_files('Substitute')))

    lines = [
        '%% GENERATED by tools/build_adaptability_counts.py --- DO NOT EDIT.',
        '%%%% Read from the repository at commit %s on %s.' % (head, read_on),
        '%% Every figure is the working tree at that commit, computed by an'
        ' exact term-node',
        '%% match over the parsed manifests, EXCEPT nRecognisersAtRecord, which'
        ' is read from',
        '%%%% the sizing record of %s: the transfer\'s novelty was established'
        % RECORD_DATE,
        '%% against the corpus as it stood then, and the corpus has grown since'
        ' (nRecognisers',
        '%% is the same command run today).',
    ]
    for k, v in counts:
        lines.append('\\newcommand{\\%s}{%s}'
                     % (k, '{:,}'.format(v).replace(',', '{,}')))
    lines.append('\\newcommand{\\countsCommit}{\\texttt{%s}}' % head[:12])
    lines.append('\\newcommand{\\countsReadOn}{%s}' % _texdate(read_on))
    lines.append('\\newcommand{\\recogniserRecordOn}{%s}' % _texdate(RECORD_DATE))
    io.open(OUT, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    for k, v in counts:
        print('%-28s %s' % (k, v))
    print('%-28s %s' % ('commit', head))
    print('wrote', os.path.relpath(OUT, ROOT))


if __name__ == '__main__':
    main()
