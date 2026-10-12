"""Low-residency WordNet lemma membership for lexical recognition.

The conversation recognizer needs only the boolean question answered by
``wordnet.synsets(token)``.  NLTK's reader eagerly builds full synset maps for
that API, so this module builds a small SQLite index from the same WordNet
lemma and exception files and applies NLTK's own morphology substitutions.
It is a mechanical reference lookup, not a classifier or a source of meaning.

The derived database lives in the per-user temporary directory and is keyed
by the source corpus digest.  If the corpus is unavailable or the index cannot
be built, callers can fall back to NLTK's canonical reader.
"""
from __future__ import annotations

import hashlib
import os
import sqlite3
import sys
import tempfile
import threading
import zipfile
from pathlib import Path
from typing import Optional

_SCHEMA = 1
_INDEX_FILES = ("index.adj", "index.adv", "index.noun", "index.verb")
_EXCEPTION_FILES = ("adj.exc", "adv.exc", "noun.exc", "verb.exc")
_POS_BY_SUFFIX = {"adj": "a", "adv": "r", "noun": "n", "verb": "v"}
# WordNetCorpusReader.MORPHOLOGICAL_SUBSTITUTIONS. Kept here as the tiny
# membership boundary must not import NLTK's high-residency package merely to
# read these fixed WordNet inflection rules. Equivalence is pinned in tests.
_MORPHOLOGICAL_SUBSTITUTIONS = {
    "n": (("s", ""), ("ses", "s"), ("ves", "f"), ("xes", "x"),
          ("zes", "z"), ("ches", "ch"), ("shes", "sh"),
          ("men", "man"), ("ies", "y")),
    "v": (("s", ""), ("ies", "y"), ("es", "e"), ("es", ""),
          ("ed", "e"), ("ed", ""), ("ing", "e"), ("ing", "")),
    "a": (("er", ""), ("est", ""), ("er", "e"), ("est", "e")),
    "s": (("er", ""), ("est", ""), ("er", "e"), ("est", "e")),
    "r": (),
}
_LOCK = threading.Lock()
_CONNECTIONS: dict[str, sqlite3.Connection] = {}
_ACTIVE_CONNECTIONS: dict[tuple, sqlite3.Connection] = {}


def _find_corpus() -> tuple[Path, bool] | None:
    paths = [os.path.expanduser(path) for path in
             os.environ.get("NLTK_DATA", "").split(os.pathsep) if path]
    if "APPENGINE_RUNTIME" not in os.environ and os.path.expanduser("~/") != "~/":
        paths.append(os.path.expanduser("~/nltk_data"))
    if os.name == "nt":
        paths.extend((
            os.path.join(sys.prefix, "nltk_data"),
            os.path.join(sys.prefix, "share", "nltk_data"),
            os.path.join(sys.prefix, "lib", "nltk_data"),
            os.path.join(os.environ.get("APPDATA", "C:\\"), "nltk_data"),
            r"C:\nltk_data", r"D:\nltk_data", r"E:\nltk_data",
        ))
    else:
        paths.extend((
            os.path.join(sys.prefix, "nltk_data"),
            os.path.join(sys.prefix, "share", "nltk_data"),
            os.path.join(sys.prefix, "lib", "nltk_data"),
            "/usr/share/nltk_data", "/usr/local/share/nltk_data",
            "/usr/lib/nltk_data", "/usr/local/lib/nltk_data",
        ))
    for directory in paths:
        root = Path(directory)
        archive = root / "corpora" / "wordnet.zip"
        if archive.is_file():
            return archive, True
        corpus = root / "corpora" / "wordnet"
        if corpus.is_dir():
            return corpus, False
    return None


def _source_digest(source: Path, zipped: bool) -> str:
    digest = hashlib.sha256()
    if zipped:
        with source.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
    else:
        for name in (*_INDEX_FILES, *_EXCEPTION_FILES):
            digest.update(name.encode("ascii") + b"\0")
            with (source / name).open("rb") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(block)
    return digest.hexdigest()


def _open_member(source: Path, zipped: bool, name: str):
    if zipped:
        archive = zipfile.ZipFile(source)
        return archive, archive.open(f"wordnet/{name}")
    return None, (source / name).open("rb")


def _iter_lines(source: Path, zipped: bool, name: str):
    archive, stream = _open_member(source, zipped, name)
    try:
        for raw in stream:
            yield raw.decode("utf-8").rstrip("\r\n")
    finally:
        stream.close()
        if archive is not None:
            archive.close()


def _build_database(source: Path, zipped: bool, digest: str,
                    database: Path) -> None:
    database.parent.mkdir(parents=True, exist_ok=True)
    temporary = database.with_name(
        f"{database.name}.{os.getpid()}.{threading.get_ident()}.part")
    try:
        temporary.unlink(missing_ok=True)
        connection = sqlite3.connect(temporary)
        try:
            connection.execute("PRAGMA journal_mode=OFF")
            connection.execute("PRAGMA synchronous=OFF")
            connection.execute("CREATE TABLE lemma(pos TEXT, word TEXT, PRIMARY KEY(pos, word))")
            connection.execute("CREATE TABLE exception(pos TEXT, form TEXT, lemma TEXT, PRIMARY KEY(pos, form, lemma))")
            for name in _INDEX_FILES:
                pos = _POS_BY_SUFFIX[name.removeprefix("index.")]
                batch = []
                for line in _iter_lines(source, zipped, name):
                    if not line or line[0].isspace():
                        continue
                    fields = line.split()
                    if len(fields) >= 2:
                        batch.append((pos, fields[0]))
                    if len(batch) >= 4096:
                        connection.executemany("INSERT OR IGNORE INTO lemma VALUES (?, ?)", batch)
                        batch.clear()
                if batch:
                    connection.executemany("INSERT OR IGNORE INTO lemma VALUES (?, ?)", batch)
            for name in _EXCEPTION_FILES:
                pos = _POS_BY_SUFFIX[name.removesuffix(".exc")]
                batch = []
                for line in _iter_lines(source, zipped, name):
                    fields = line.split()
                    if len(fields) >= 2:
                        batch.extend((pos, fields[0], lemma) for lemma in fields[1:])
                if batch:
                    connection.executemany("INSERT OR IGNORE INTO exception VALUES (?, ?, ?)", batch)
            connection.execute("CREATE INDEX exception_surface ON exception(pos, form)")
            connection.execute("CREATE TABLE metadata(schema INTEGER, digest TEXT)")
            connection.execute("INSERT INTO metadata VALUES (?, ?)", (_SCHEMA, digest))
            connection.commit()
        finally:
            connection.close()
        os.replace(temporary, database)
    finally:
        temporary.unlink(missing_ok=True)


def _connection() -> Optional[sqlite3.Connection]:
    corpus = _find_corpus()
    if corpus is None:
        return None
    source, zipped = corpus
    try:
        source_key: tuple = (str(source.resolve()), zipped)
        names = ("",) if zipped else (*_INDEX_FILES, *_EXCEPTION_FILES)
        for name in names:
            path = source if zipped else source / name
            stat = path.stat()
            source_key += (name, stat.st_size, stat.st_mtime_ns)
        active_key = (*source_key, threading.get_ident())
        # WordNet is an immutable corpus during a running process. Check cheap
        # file metadata per lookup and hash the source bytes only once for that
        # process snapshot; hashing the 11 MB zip per token erased the benefit
        # of the compact on-disk index.
        with _LOCK:
            active = _ACTIVE_CONNECTIONS.get(active_key)
            if active is not None:
                return active
        digest = _source_digest(source, zipped)
        user_id = getattr(os, "getuid", lambda: 0)()
        cache_dir = Path(tempfile.gettempdir()) / (
            f"ocelot-wordnet-membership-v{_SCHEMA}-{user_id}")
        database = cache_dir / f"{digest}.sqlite3"
        key = f"{database}:{threading.get_ident()}"
        with _LOCK:
            connection = _CONNECTIONS.get(key)
            if connection is not None:
                _ACTIVE_CONNECTIONS[active_key] = connection
                return connection
            valid = False
            if database.is_file():
                try:
                    probe = sqlite3.connect(
                        f"{database.as_uri()}?mode=ro", uri=True)
                    valid = probe.execute(
                        "SELECT schema, digest FROM metadata").fetchone() == (
                            _SCHEMA, digest)
                    probe.close()
                except sqlite3.Error:
                    valid = False
            if not valid:
                _build_database(source, zipped, digest, database)
            connection = sqlite3.connect(
                f"{database.as_uri()}?mode=ro", uri=True,
                check_same_thread=False)
            connection.execute("PRAGMA query_only=ON")
            _CONNECTIONS[key] = connection
            _ACTIVE_CONNECTIONS[active_key] = connection
            return connection
    except Exception:
        return None


def _forms(token: str, substitutions: tuple[tuple[str, str], ...]) -> set[str]:
    forms = {token}
    for old, new in substitutions:
        if token.endswith(old):
            forms.add(token[:-len(old)] + new if old else token + new)
    return forms


def has_synset(token: str) -> Optional[bool]:
    """Return WordNet's English ``bool(synsets(token))`` without loading it.

    ``None`` means the low-residency index is unavailable; otherwise the
    boolean is equivalent to NLTK's no-POS, English ``synsets`` membership.
    """
    connection = _connection()
    if connection is None:
        return None
    try:
        word = token.lower()
        positions = (("n", _MORPHOLOGICAL_SUBSTITUTIONS["n"]),
                     ("v", _MORPHOLOGICAL_SUBSTITUTIONS["v"]),
                     ("a", _MORPHOLOGICAL_SUBSTITUTIONS["a"]),
                     ("s", _MORPHOLOGICAL_SUBSTITUTIONS["s"]),
                     ("r", _MORPHOLOGICAL_SUBSTITUTIONS["r"]))
        for pos, substitutions in positions:
            exceptions = connection.execute(
                "SELECT lemma FROM exception WHERE pos=? AND form=?",
                (pos if pos != "s" else "a", word),
            ).fetchall()
            if exceptions:
                candidates = {row[0] for row in exceptions}
            else:
                candidates = _forms(word, substitutions)
            for candidate in candidates:
                lemma_pos = "a" if pos == "s" else pos
                if connection.execute(
                    "SELECT 1 FROM lemma WHERE pos=? AND word=? LIMIT 1",
                    (lemma_pos, candidate),
                ).fetchone():
                    return True
        return False
    except Exception:
        return None


def lemmas(token: str, pos: str) -> Optional[tuple[str, ...]]:
    """Return WordNet morphology lemmas for one token and part of speech.

    ``None`` means the low-residency WordNet index is unavailable. An empty
    tuple means the token has no lemma for this POS. This exposes morphology
    only; it does not select a sense or ground a referent.
    """
    connection = _connection()
    if connection is None:
        return None
    token = str(token or "").strip().lower()
    pos = str(pos or "").strip().lower()
    index_pos = {"a": "a", "s": "a", "r": "r", "n": "n", "v": "v"}.get(pos)
    if not token or index_pos is None:
        return ()
    try:
        rows = connection.execute(
            "SELECT lemma FROM exception WHERE pos=? AND form=?",
            (index_pos, token),
        ).fetchall()
        if rows:
            candidates = {str(row[0]) for row in rows}
        else:
            substitutions = _MORPHOLOGICAL_SUBSTITUTIONS.get(pos, ())
            candidates = _forms(token, substitutions)
        found = []
        for candidate in candidates:
            row = connection.execute(
                "SELECT 1 FROM lemma WHERE pos=? AND word=? LIMIT 1",
                (index_pos, candidate),
            ).fetchone()
            if row:
                found.append(candidate)
        return tuple(sorted(set(found)))
    except Exception:
        return None
