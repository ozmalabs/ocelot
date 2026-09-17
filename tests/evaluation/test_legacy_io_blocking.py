import builtins
import os
from pathlib import Path
import socket
import subprocess
import urllib.request

import pytest

from evaluation.p0a.entrypoint import intercept_legacy_process_io
from evaluation.p0a.legacy_io_guard import DirectIODenied, activated, deny_direct_io


def test_registered_legacy_routes_fail_before_effect():
    routes = ("world.dispatch_pending_io", "fetch.materialize", "experiment.spawn", "browser.launch_apply",
              "voice.capture_playback", "seed.arbitrary_load", "raw.host.dispatch")
    with activated():
        for route in routes:
            with pytest.raises(DirectIODenied):
                deny_direct_io(route)


def test_host_compatibility_guard_executes_hostile_operations_in_process(tmp_path):
    """Defense-in-depth only: these executions are not OS-containment proof."""
    source = tmp_path / "source"; source.write_text("source")
    descriptor = os.open(source, os.O_RDONLY)
    attempts = {
        "socket.socket": lambda: socket.socket(),
        "urllib.urlopen": lambda: urllib.request.urlopen("https://example.invalid"),
        "subprocess.Popen": lambda: subprocess.Popen(["true"]),
        "builtins.open": lambda: builtins.open(source, "rb"),
        "pathlib.Path.read_text": lambda: Path(source).read_text(),
        "os.read": lambda: os.read(descriptor, 1),
        "os.system": lambda: os.system("true"),
        "os.execv": lambda: os.execv("/bin/true", ["true"]),
        "os.execve": lambda: os.execve("/bin/true", ["true"], {}),
    }
    reports = []
    try:
        with activated(reporter=reports.append), intercept_legacy_process_io():
            for route, operation in attempts.items():
                with pytest.raises(DirectIODenied):
                    operation()
    finally:
        os.close(descriptor)
    assert source.read_text() == "source"
    assert {"socket", "urllib.urlopen", "subprocess.Popen", "builtins.open", "io.open", "os.read",
            "os.system", "os.execv", "os.execve"} <= set(reports)
