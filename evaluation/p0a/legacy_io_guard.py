"""Evaluation-active fail-closed guards for legacy host-I/O routes.

These guards are defense-in-depth instrumentation only.  They do not provide
an OS security boundary and are deliberately dormant unless the isolated
P0-A entrypoint activates them.
"""
from __future__ import annotations

from contextlib import contextmanager
import contextvars
from typing import Callable


class DirectIODenied(RuntimeError):
    code = "P0A_DIRECT_IO_DENIED"


_active: contextvars.ContextVar[bool] = contextvars.ContextVar("p0a_active", default=False)
_reporter: contextvars.ContextVar[Callable[[str], None] | None] = contextvars.ContextVar(
    "p0a_reporter", default=None)

ROUTE_INVENTORY = {
    "world.dispatch_pending_io": "substrate.world_adapter.WorldAdapter._dispatch_pending_io",
    "fetch.dispatch": "domains.fetch_dispatch.scan_and_fetch",
    "fetch.materialize": "domains.fetch_dispatch._materialize_http_get",
    "experiment.spawn": "domains.experiment_dispatch._spawn",
    "browser.launch_apply": "domains.worlds.browser.BrowserWorld",
    "voice.capture_playback": "domains.voice_world",
    "seed.arbitrary_load": "substrate.seed_loader",
    "raw.host.dispatch": "scripts.jabberwock_daemon host-action dispatch",
}


def active() -> bool:
    return _active.get()


def deny_direct_io(route: str) -> None:
    if not active():
        return
    reporter = _reporter.get()
    if reporter is not None:
        try:
            reporter(route)
        except Exception:
            # A guard that cannot record becomes a real fail-closed impasse.
            raise DirectIODenied("P0A_DIRECT_IO_DENIED:receipt_impasse") from None
    raise DirectIODenied(f"P0A_DIRECT_IO_DENIED:{route}")


@contextmanager
def activated(*, reporter: Callable[[str], None] | None = None):
    """Activate guard state before legacy adapters are imported or called."""
    active_token = _active.set(True)
    reporter_token = _reporter.set(reporter)
    try:
        yield
    finally:
        _reporter.reset(reporter_token)
        _active.reset(active_token)
