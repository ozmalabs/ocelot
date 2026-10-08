"""Small bounded, keep-alive HTTP(S) transport for the authored GET effector.

Retrieval chooses what to request; this module only transports GETs. Independent
requests can use separate same-origin sockets, while each socket is exclusively
checked out for its request/response lifetime.
"""
from __future__ import annotations

import http.client
import ssl
import threading
from collections import OrderedDict
from urllib.parse import urljoin, urlsplit

_ORIGIN_LIMIT = 8
_CONNECTIONS_PER_ORIGIN = 4
_POOL = OrderedDict()
_BUSY: set[int] = set()
_CONDITION = threading.Condition(threading.RLock())
_SSL_CONTEXT_LOCK = threading.Lock()
_SSL_CONTEXT = None
_REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})


def _client_ssl_context():
    """Reuse one immutable client trust context for this process.

    Context construction reads the platform certificate store and is
    needlessly expensive on each new/retried HTTPS socket. Trust roots are a
    process-start snapshot; restarting the service picks up certificate-store
    changes, as it does for other process-local TLS configuration.
    """
    global _SSL_CONTEXT
    if _SSL_CONTEXT is None:
        with _SSL_CONTEXT_LOCK:
            if _SSL_CONTEXT is None:
                _SSL_CONTEXT = ssl.create_default_context()
    return _SSL_CONTEXT


def _origin(url: str):
    parsed = urlsplit(url)
    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"}:
        raise ValueError(f"HTTP GET refuses URL scheme {scheme!r}")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("HTTP GET refuses credentials embedded in URL")
    host = parsed.hostname
    if not host:
        raise ValueError("HTTP GET requires a host")
    port = parsed.port or (443 if scheme == "https" else 80)
    target = parsed.path or "/"
    if parsed.query:
        target += "?" + parsed.query
    return (scheme, host.lower(), port), target


def _new_connection(key, timeout):
    scheme, host, port = key
    if scheme == "https":
        return http.client.HTTPSConnection(
            host, port, timeout=timeout,
            context=_client_ssl_context())
    return http.client.HTTPConnection(host, port, timeout=timeout)


def _evict_idle_origins():
    while len(_POOL) > _ORIGIN_LIMIT:
        old_key = next((key for key, pool in _POOL.items()
                        if all(id(conn) not in _BUSY for conn in pool)), None)
        if old_key is None:
            return
        for conn in _POOL.pop(old_key):
            conn.close()


def _checkout(key, timeout):
    with _CONDITION:
        while True:
            pool = _POOL.setdefault(key, [])
            for conn in pool:
                if id(conn) not in _BUSY:
                    _BUSY.add(id(conn))
                    if conn.sock is not None:
                        conn.sock.settimeout(timeout)
                    _POOL.move_to_end(key)
                    return conn
            if len(pool) < _CONNECTIONS_PER_ORIGIN:
                conn = _new_connection(key, timeout)
                pool.append(conn)
                _BUSY.add(id(conn))
                _POOL.move_to_end(key)
                _evict_idle_origins()
                return conn
            _CONDITION.wait()


def _checkin(key, conn, discard=False):
    with _CONDITION:
        pool = _POOL.get(key, [])
        if discard:
            if conn in pool:
                pool.remove(conn)
            conn.close()
        _BUSY.discard(id(conn))
        if not pool:
            _POOL.pop(key, None)
        _evict_idle_origins()
        _CONDITION.notify()


def close_idle_connections() -> None:
    """Close pooled sockets (used by tests and orderly process shutdown)."""
    with _CONDITION:
        for key in list(_POOL):
            pool = _POOL[key]
            idle = [conn for conn in pool if id(conn) not in _BUSY]
            _POOL[key] = [conn for conn in pool if id(conn) in _BUSY]
            for conn in idle:
                conn.close()
            if not _POOL[key]:
                del _POOL[key]
        _CONDITION.notify_all()


def http_get(url: str, *, timeout: float = 15,
             user_agent: str = "gamma-substrate-agent/0.1 (research; agent-authored world-adapter)",
             max_redirects: int = 5) -> dict:
    """GET a URL, retrying a stale keep-alive socket once (GET is idempotent)."""
    current_url = str(url)
    for redirect in range(max_redirects + 1):
        key, target = _origin(current_url)
        conn = _checkout(key, timeout)
        discard = False
        try:
            for attempt in range(2):
                try:
                    conn.request("GET", target,
                                 headers={"User-Agent": str(user_agent)})
                    response = conn.getresponse()
                    body = response.read()
                    status = int(response.status)
                    location = response.getheader("Location")
                    discard = bool(response.will_close)
                    break
                except Exception:
                    discard = True
                    if attempt:
                        raise
                    _checkin(key, conn, discard=True)
                    conn = _checkout(key, timeout)
                    discard = False
            _checkin(key, conn, discard=discard)
        except Exception:
            _checkin(key, conn, discard=True)
            raise

        if status in _REDIRECT_STATUSES and location:
            if redirect >= max_redirects:
                raise OSError("HTTP GET exceeded redirect limit")
            next_url = urljoin(current_url, location)
            old_scheme = urlsplit(current_url).scheme.lower()
            new_scheme = urlsplit(next_url).scheme.lower()
            if new_scheme not in {"http", "https"}:
                raise ValueError(f"HTTP GET refuses redirect scheme {new_scheme!r}")
            if old_scheme == "https" and new_scheme != "https":
                raise ValueError("HTTP GET refuses HTTPS-to-HTTP redirect")
            current_url = next_url
            continue

        return {"status": status, "length": len(body),
                "text": body.decode("utf-8", "replace"), "url": current_url}
    raise OSError("HTTP GET exceeded redirect limit")


__all__ = ["close_idle_connections", "http_get"]
