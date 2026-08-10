"""Generic on-disk, mmap'd, index-addressed key→value SLAB store.

This is the COLD-REFERENCE layer the substrate's own architecture
prescribes (the agent's concepts that drive it: page_cache,
shared_memory, virtual_memory_area / mmap demand-paging, interned keys
+ small-int addressing via a sorted B_tree-style index, and the
cache_aside_pattern / tiered_compilation split where grounded graph
nodes are the HOT tier and this slab is consulted only on a miss).

The references the substrate ingests (Wiktionary/kaikki, UniMorph) are
LARGE and mostly COLD. Loading them into RAM as Python dicts makes the
query-time working set proportional to the corpus size — exactly the
wrong shape. A slab instead keeps the corpus on disk and lets the OS
page_cache decide residency: a lookup touches only O(log n) index pages
plus one value page, so query-time RSS is the WORKING SET, not the
corpus.

Slab format (two files per slab, under data/slabs/<name>.{keys,vals}):
  <name>.vals : concatenated UTF-8 records, each = ``key \\x00 value``.
                The key is stored alongside the value so a hash
                collision can be VERIFIED (and rejected) at query time.
                For a multi-valued key, ``value`` is a ``\\x1f``-joined
                list.
  <name>.keys : a sorted array of fixed 20-byte index records, each
                  [8-byte LE u64 key-hash][8-byte LE u64 vals-offset][4-byte LE u32 length]
                sorted ascending by key-hash. Binary-searchable directly
                over the mmap — no scan, no in-RAM index.

  key-hash = first 8 bytes of blake2b(normalized_key, digest_size=8) as
             a little-endian u64. STABLE across runs and processes (NOT
             Python's salted builtin hash). normalize = NFC + casefold.

This module is a pure mechanical store — no agent state, no decisions
over graph state. It is infrastructure the world-adapter ingesters
(wiktionary_reference, morphology_reference) build on. See CLAUDE.md:
external reference I/O lives at the Python boundary; this only moves the
bytes from disk to a verified value, the substrate stays the source of
truth (grounded graph nodes are the hot tier).
"""
from __future__ import annotations

import hashlib
import mmap
import os
import struct
import unicodedata
from pathlib import Path
from typing import Iterable, Iterator, Optional

# Slabs live under the gitignored data/ dir alongside the other caches.
_ROOT = Path(__file__).resolve().parent.parent
SLAB_DIR = _ROOT / "data" / "slabs"

# Index record: u64 key-hash, u64 vals-offset, u32 length. Fixed 20 bytes,
# little-endian, so the .keys file is a flat sorted array we can bisect over
# the mmap by record index.
_REC = struct.Struct("<QQI")
_REC_SIZE = _REC.size  # 20
assert _REC_SIZE == 20

# Field separators inside a .vals record.
_KV_SEP = b"\x00"        # key \x00 value
_LIST_SEP = "\x1f"       # value0 \x1f value1 \x1f ... (multivalue)


def normalize_key(key: str) -> str:
    """Canonical key form: NFC then casefold. Stable across runs."""
    return unicodedata.normalize("NFC", key).casefold()


def key_hash(key: str) -> int:
    """Stable 8-byte (u64 LE) blake2b hash of the normalized key.

    Deliberately NOT Python's builtin hash (which is salted per process):
    the .keys file is written once and read by later runs, so the hash
    must be identical everywhere."""
    digest = hashlib.blake2b(
        normalize_key(key).encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "little", signed=False)


def _paths(name: str) -> tuple[Path, Path]:
    return SLAB_DIR / f"{name}.keys", SLAB_DIR / f"{name}.vals"


def slab_exists(name: str) -> bool:
    keys_path, vals_path = _paths(name)
    return keys_path.exists() and vals_path.exists()


# ---------------------------------------------------------------------------
# Build — stream (key, value) pairs → sorted slab files.
# ---------------------------------------------------------------------------


def build_slab(name: str, pairs_iterable: Iterable[tuple[str, str]],
               source_path: Optional[os.PathLike] = None,
               force: bool = False) -> bool:
    """Build the ``name`` slab from ``pairs_iterable`` of (key, value).

    A caller may yield repeats for a multi-valued key; we GROUP them, so
    the same key with several values becomes one \\x1f-joined record (the
    first value per (key,value) wins de-dup, order preserved). The caller
    may instead pre-join and yield each key once — both work.

    Build is one-time and may transiently hold the (hash, key, value)
    tuples in RAM to sort them (1M short tuples is fine under ulimit);
    the QUERY path never does. Sort by key-hash, write .vals, then the
    .keys index.

    Skips the rebuild when the slab files exist and are newer than
    ``source_path`` (mtime check) unless ``force``. Returns True if it
    (re)built, False if it skipped.
    """
    keys_path, vals_path = _paths(name)
    if not force and keys_path.exists() and vals_path.exists():
        if source_path is None:
            return False
        try:
            src_m = os.stat(source_path).st_mtime
            if (keys_path.stat().st_mtime >= src_m
                    and vals_path.stat().st_mtime >= src_m):
                return False
        except OSError:
            return False

    SLAB_DIR.mkdir(parents=True, exist_ok=True)

    # Group values per normalized key, preserving first-seen order and
    # de-duplicating identical values. We keep the ORIGINAL (normalized)
    # key string to store for collision verification.
    grouped: dict[str, list[str]] = {}
    for key, value in pairs_iterable:
        if not key:
            continue
        nk = normalize_key(key)
        bucket = grouped.get(nk)
        if bucket is None:
            grouped[nk] = [value]
        elif value not in bucket:
            bucket.append(value)

    # (hash, normalized_key, joined_value) — sorted by hash for bisect.
    records: list[tuple[int, str, str]] = []
    for nk, values in grouped.items():
        joined = _LIST_SEP.join(values)
        records.append((key_hash(nk), nk, joined))
    records.sort(key=lambda r: r[0])

    # Write atomically via .part files, then rename.
    keys_tmp = keys_path.with_suffix(keys_path.suffix + ".part")
    vals_tmp = vals_path.with_suffix(vals_path.suffix + ".part")
    index_rows: list[tuple[int, int, int]] = []
    with open(vals_tmp, "wb") as vf:
        offset = 0
        for h, nk, joined in records:
            rec = nk.encode("utf-8") + _KV_SEP + joined.encode("utf-8")
            vf.write(rec)
            index_rows.append((h, offset, len(rec)))
            offset += len(rec)
    with open(keys_tmp, "wb") as kf:
        for h, off, length in index_rows:
            kf.write(_REC.pack(h, off, length))
    os.replace(vals_tmp, vals_path)
    os.replace(keys_tmp, keys_path)
    return True


# ---------------------------------------------------------------------------
# Query — mmap + binary search. Nothing loads into RAM but the working set.
# ---------------------------------------------------------------------------


class Slab:
    """Read-only mmap'd view over a built slab. Lazily maps both files on
    first lookup; the OS page_cache governs residency from there.

    lookup(key)      -> the value string (first value if multivalued), or None
    lookup_list(key) -> the full list of values (empty list on miss)
    """

    def __init__(self, name: str):
        self.name = name
        self.keys_path, self.vals_path = _paths(name)
        self._keys_fh = None
        self._vals_fh = None
        self._keys_mm: Optional[mmap.mmap] = None
        self._vals_mm: Optional[mmap.mmap] = None
        self._n_records = 0

    # -- lifecycle ----------------------------------------------------------

    def _ensure_open(self) -> bool:
        if self._keys_mm is not None:
            return True
        if not (self.keys_path.exists() and self.vals_path.exists()):
            return False
        self._keys_fh = open(self.keys_path, "rb")
        self._vals_fh = open(self.vals_path, "rb")
        # PROT_READ — demand-paged, never copied into the process eagerly.
        self._keys_mm = mmap.mmap(
            self._keys_fh.fileno(), 0, prot=mmap.PROT_READ)
        self._vals_mm = mmap.mmap(
            self._vals_fh.fileno(), 0, prot=mmap.PROT_READ)
        self._n_records = len(self._keys_mm) // _REC_SIZE
        return True

    def close(self) -> None:
        for mm in (self._keys_mm, self._vals_mm):
            if mm is not None:
                try:
                    mm.close()
                except Exception:
                    pass
        for fh in (self._keys_fh, self._vals_fh):
            if fh is not None:
                try:
                    fh.close()
                except Exception:
                    pass
        self._keys_mm = self._vals_mm = None
        self._keys_fh = self._vals_fh = None
        self._n_records = 0

    def __del__(self):
        self.close()

    # -- index access -------------------------------------------------------

    def _record_at(self, i: int) -> tuple[int, int, int]:
        """The (hash, offset, length) index record at row ``i``."""
        base = i * _REC_SIZE
        return _REC.unpack(self._keys_mm[base:base + _REC_SIZE])

    def _read_value_record(self, offset: int, length: int) -> tuple[str, str]:
        """Read + split the .vals record at offset/len → (stored_key, value)."""
        raw = self._vals_mm[offset:offset + length]
        sep = raw.find(_KV_SEP)
        if sep < 0:
            return "", raw.decode("utf-8", "replace")
        stored_key = raw[:sep].decode("utf-8", "replace")
        value = raw[sep + 1:].decode("utf-8", "replace")
        return stored_key, value

    def _bisect_first(self, target_hash: int) -> int:
        """Index of the FIRST record whose hash >= target_hash."""
        lo, hi = 0, self._n_records
        while lo < hi:
            mid = (lo + hi) // 2
            h, _, _ = self._record_at(mid)
            if h < target_hash:
                lo = mid + 1
            else:
                hi = mid
        return lo

    # -- public lookup ------------------------------------------------------

    def lookup_list(self, key: str) -> list[str]:
        """Return the list of values for ``key`` (empty on miss).

        Binary-search the key-hash, then scan the run of equal-hash
        records (both directions implicitly, via the sorted-first index)
        and VERIFY the stored key matches the normalized query key — so a
        hash collision returns the right value, never a wrong one."""
        if not self._ensure_open() or self._n_records == 0:
            return []
        nk = normalize_key(key)
        h = key_hash(key)
        i = self._bisect_first(h)
        # Walk forward over every record sharing this hash; verify the
        # stored key. (_bisect_first lands on the first equal-hash record,
        # so a forward scan covers all collisions — no backward scan
        # needed, but we stop as soon as the hash differs.)
        n = self._n_records
        while i < n:
            rh, off, length = self._record_at(i)
            if rh != h:
                break
            stored_key, value = self._read_value_record(off, length)
            if stored_key == nk:
                return value.split(_LIST_SEP) if value != "" else [""]
            i += 1
        return []

    def lookup(self, key: str) -> Optional[str]:
        """Return the first value for ``key``, or None on a miss."""
        vals = self.lookup_list(key)
        return vals[0] if vals else None

    # -- diagnostics --------------------------------------------------------

    def __len__(self) -> int:
        self._ensure_open()
        return self._n_records


# A tiny per-process cache so reopening the same slab name reuses one mmap.
_OPEN_SLABS: dict[str, Slab] = {}


def open_slab(name: str) -> Optional[Slab]:
    """Return a cached, lazily-mmap'd Slab for ``name`` (None if absent)."""
    s = _OPEN_SLABS.get(name)
    if s is None:
        if not slab_exists(name):
            return None
        s = Slab(name)
        _OPEN_SLABS[name] = s
    return s


def resident_probe() -> dict[str, int]:
    """Best-effort process memory snapshot (KB), for the measurement
    script to contrast RSS against corpus size. Reads /proc/self/statm
    (Linux) — size / resident pages × page size."""
    out: dict[str, int] = {}
    try:
        import resource
        out["ru_maxrss_kb"] = resource.getrusage(
            resource.RUSAGE_SELF).ru_maxrss
    except Exception:
        pass
    try:
        page = os.sysconf("SC_PAGE_SIZE")
        with open("/proc/self/statm") as fh:
            fields = fh.read().split()
        out["vsize_kb"] = int(fields[0]) * page // 1024
        out["rss_kb"] = int(fields[1]) * page // 1024
    except Exception:
        pass
    return out


__all__ = [
    "SLAB_DIR",
    "Slab",
    "build_slab",
    "open_slab",
    "slab_exists",
    "normalize_key",
    "key_hash",
    "resident_probe",
]


# ---------------------------------------------------------------------------
# Inline unit test — build a synthetic slab, reopen, verify lookups, a miss,
# and a forced hash collision. Run: python domains/reference_slab.py
# ---------------------------------------------------------------------------

def _selftest() -> None:
    import random
    import tempfile

    global SLAB_DIR
    saved = SLAB_DIR
    tmp = Path(tempfile.mkdtemp(prefix="slab_selftest_"))
    SLAB_DIR = tmp
    try:
        # A few hundred synthetic pairs, some multivalue.
        pairs: list[tuple[str, str]] = []
        truth: dict[str, list[str]] = {}
        for i in range(400):
            k = f"word_{i}_{random.randint(0, 9)}"
            v = f"val_{i}"
            pairs.append((k, v))
            truth.setdefault(normalize_key(k), []).append(v)
            if i % 7 == 0:  # second value for some keys → multivalue
                v2 = f"alt_{i}"
                pairs.append((k, v2))
                truth[normalize_key(k)].append(v2)
        # Casefold collision case: "Hello" and "hello" normalize identically.
        pairs.append(("Hello", "greeting"))
        truth[normalize_key("Hello")] = truth.get(
            normalize_key("Hello"), []) + ["greeting"]

        assert build_slab("selftest", iter(pairs), force=True)
        # Reopen fresh (no in-RAM dict) and verify.
        s = Slab("selftest")
        for k, expected in list(truth.items())[:50]:
            got = s.lookup_list(k)
            assert got == expected, (k, got, expected)
        # Casefold: querying "HELLO" must hit the "Hello" record.
        assert s.lookup("HELLO") == "greeting", s.lookup("HELLO")
        # Missing key.
        assert s.lookup("definitely_absent_key") is None
        assert s.lookup_list("definitely_absent_key") == []
        s.close()

        # Hash-collision safety: force distinct keys to the same hash by
        # monkeypatching the module-global key_hash (both build and query
        # resolve it via globals()), then verify each resolves to its OWN
        # value (stored-key verification kicks in).
        g = globals()
        orig = g["key_hash"]
        g["key_hash"] = lambda key: 12345  # everything collides
        try:
            build_slab("collide", iter([("alpha", "A"), ("beta", "B"),
                                        ("gamma", "C")]), force=True)
            s2 = Slab("collide")
            assert s2.lookup("alpha") == "A", s2.lookup("alpha")
            assert s2.lookup("beta") == "B", s2.lookup("beta")
            assert s2.lookup("gamma") == "C", s2.lookup("gamma")
            assert s2.lookup("delta") is None
            s2.close()
        finally:
            g["key_hash"] = orig
        print("reference_slab self-test: PASS")
    finally:
        SLAB_DIR = saved


if __name__ == "__main__":
    _selftest()
