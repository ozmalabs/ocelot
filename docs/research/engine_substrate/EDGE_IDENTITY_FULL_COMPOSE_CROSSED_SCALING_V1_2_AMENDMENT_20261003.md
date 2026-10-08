# Edge identity crossed scaling v1.2 amendment (2026-10-03)

The v1 and v1.1 captures are retained as diagnostics and are not valid
measurements. Version 1.1 corrected private-copy instrumentation, but its
synthetic field count included the source rule's preexisting `object` field.
Version 1.2 removes `object` from the synthetic output rule before adding the
preregistered fields. The resulting candidate rule has exactly the requested
number of eligible identity attributes, while preserving `actor+verb` as the
unique cue maximum. No other design parameters change. This amendment is
source-frozen in a new lock and the analyzer checks both arithmetic and
materialization counts.
