"""Historical compatibility entry point for the retired Whisper strong-teacher gate.

The old gate supplied each candidate as a CTranslate2 generation prompt and
treated the returned continuation score as P(candidate|audio). Prompt tokens
are unscored, so that result was invalid. This script now fails loudly instead
of regenerating a scientifically misleading milestone. Use
scripts/whisper_grounding_measure.py for the corrected graph-native method.

See WHISPER_GROUNDING_PREREG.md.
"""
from __future__ import annotations

MESSAGE = (
    "RETIRED: the historical forced-decode gate scored generated "
    "continuations after unscored prompt tokens, not candidate words. "
    "Run scripts/whisper_grounding_measure.py instead."
)


def main() -> int:
    print(MESSAGE)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
