# MetaShape downstream categorisation v1.1 amendment (2026-09-26)

V1 is preserved as inadmissible: its query runner encoded two MotionRule gold labels as `None`, although the preregistered oracle assigned `spatial_dynamics` to the positive and extra-field cases. V1.1 corrects those two gold labels to match the original protocol, keeps the same 20 inputs, source mechanism, training sequence, metrics, and all other labels, and locks the corrected runner and source bytes before execution. No system code or classifier behavior is changed.
