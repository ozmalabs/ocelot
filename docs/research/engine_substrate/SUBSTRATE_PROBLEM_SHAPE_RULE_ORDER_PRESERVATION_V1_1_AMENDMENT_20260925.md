# Amendment: rule-order gate readback

The first order-preservation execution stopped after two pairs because it compared the absolute numeric indices of the five ProblemShape rules across separately loaded processes. Pair 1 had matching task semantics but a five-slot index offset; pair 2 had matching indices. A read-only same-process boot diagnostic loaded the default and transformed seed corpora with identical ProblemShape indices (1830–1834), and both reported the same 724 loaded seeds / 11 pre-existing load failures. The interrupted raw checkpoint is retained and is not a completed experiment.

Absolute indices are therefore an unnecessarily brittle gate when seed boot can vary the count/order of earlier active rules. V1.1 instead compares a SHA-256 fingerprint of the complete ordered sequence of active rule names, plus the relative indices of the five ProblemShape rules. The candidate passes the order gate only if its complete active rule-name sequence matches the paired baseline and the ProblemShape names have the same relative order. This still detects missing, reordered, or extra active rules without treating a global offset as a semantic order change.

The V1.1 runner, lock, and output use distinct paths; V1 artifacts remain unchanged. All other design conditions remain as preregistered.
