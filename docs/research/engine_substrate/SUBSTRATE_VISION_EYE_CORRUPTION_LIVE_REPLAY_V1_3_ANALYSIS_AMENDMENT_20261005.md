# Post-hoc analysis v1.3 amendment

The v1.3 analysis correctly regenerated deterministic masks and recovered seven native winners that were one ULP below the reconstructed maxima. Its strict exact-max numerator of 2,873 was correct, but it reported a denominator of 3,456 by including 576 clean probes. The corruption analysis contains 2,880 probes (12 workers × 240); the clean parity set is separate.

The v1.4 analysis corrects the denominator and check labels, retains all prior source and scorer checks, and has its own analysis lock. Use v1.4 for the final post-hoc numerical summary. The v1.3 report remains preserved with this error disclosed.
