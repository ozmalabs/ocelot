"""Normal runtime guard imports must not load evaluator-only crypto code."""
from __future__ import annotations

import subprocess
import sys


def test_legacy_io_guard_import_does_not_load_evaluator_broker_or_crypto():
    code = (
        "from evaluation.p0a.legacy_io_guard import active; "
        "import sys; "
        "assert not active(); "
        "assert 'evaluation.p0a.broker' not in sys.modules; "
        "assert 'evaluation.p0a.manifest' not in sys.modules; "
        "assert 'cryptography' not in sys.modules"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], check=False, capture_output=True,
        text=True, timeout=15,
    )
    assert result.returncode == 0, result.stderr
