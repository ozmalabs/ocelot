# Factored operator search v1 preregistration

## Question

On the same four-task panels where a shared 13-operator search timed out, does
searching four smaller one-operator grammar branches and merging their
hypotheses recover exact candidates within a bounded budget?

## Paired design

Reuse the exact 20 panel inputs from multi-operator family search v1. For each
panel, search separately with base `Neg/Eq/And` plus one of `Plus`, `Times`,
`Abs`, or `Min`, using maximum size 7, 3-second per-branch timeout, and a
128-solution cap. Each branch receives identical initial examples and query
pool; no task identity or target operator is passed to synthesis. Merge
canonical-Term-unique candidates across branches, preserving branch
provenance. Run the native maximum-entropy selector over the union for at most
six labels from the frozen selection order. Do not resynthesize after labels
in v1.

The paired baseline is the source-locked shared 13-operator capture on those
same panels (12-second timeout). This is an organization comparison, not an
equal total-time comparison: the factored route has a 12-second maximum
synthesis budget per panel (four 3-second branches), plus selection.

## Measures and gates

Lock current source/native fingerprints, upstream panels/capture/analysis, all
four grammars, and analyzer before running. Independently replay candidate fit,
query selection, labels, survivor transitions, and the 1,296-case holdout.
Report timeout and exact-candidate rates per branch/task; merged exact-candidate
coverage; correct resolution, false singleton, empty and unresolved outcomes;
candidate counts; branch and total synthesis wall/CPU; explored terms; and
selector evaluation counts. Retain every panel and all timeout/empty outcomes.

## Limits

The four-operator menu and numeric task families are authored and closed. This
tests whether factoring the declared candidate space helps under fixed caps;
it does not establish autonomous grammar construction, open-ended induction,
or natural-task tractability. No new oracle labels are used beyond those in
the paired frozen training and query pools.
