# Lexical hybrid code search

**Status:** landed 2026-11-14 as Workstream F of
[`ADVANCED_CODING_AGENT_PLAN.md`](ADVANCED_CODING_AGENT_PLAN.md).
**Files:** `scripts/ocelot_code_search.py`,
`tests/test_code_search_migrated.py`, this document.

`ocelot_code_search` is the lexical half of hybrid code retrieval: BM25 over
the repo-map tag cache and source files, fused with repo-map PageRank by
Reciprocal Rank Fusion. It uses **no embeddings, no model, no network, and no
new dependencies**. Semantic/embedding retrieval remains deferred; see
[`GRAPH_CODING_LANDSCAPE.md`](GRAPH_CODING_LANDSCAPE.md) P2.

## API

```python
from scripts.ocelot_code_search import code_search

result = code_search(
    root,
    query,
    limit=20,
    cache_path=None,
    files=None,
    include_snippet=True,
    k1=1.5,
    b=0.75,
    rrf_k=60,
)
```

`root` is the repository root; `query` is natural language or an identifier.
The first four keyword arguments are the integration surface; `k1`, `b`, and
`rrf_k` expose the scoring constants.

```python
{
    "ok": True,
    "query": "repo map pagerank",
    "results": [
        {
            "path": "scripts/ocelot_dev_memory.py",
            "score": 0.024415,       # fused RRF score
            "bm25": 13.03624,       # BM25 component
            "graph": 0.001474,      # PageRank component
            "symbols": [
                {"name": "repo_map", "line": 123, "detail":
                 "definition.function", "score": 5.2}
            ],
            "line": 47,
            "snippet": '"""Ranked, token-budgeted repo map ...'
        }
    ],
    "n": 1,
    "bm25": {"k1": 1.5, "b": 0.75},   # configuration, not a score
    "rrf_k": 60,
    "index": {"files": 6825, "terms": 218398},
}
```

- `results[].score` is the fused RRF score. `bm25` and `graph` are the raw
  component scores, so a caller can see why a file ranked where it did.
- `symbols` contains matched definition tags from the repo-map cache, ranked
  by summed term IDF, then source line and name. It is capped at 8.
- `line` and `snippet` are present only when `include_snippet=True` and a
  matching non-empty source line exists. `snippet` is one stripped line,
  bounded to 240 characters.
- `cache_path=None` resolves to `<root>/var/ocelot_dev_tags.json`, so searching
  a fixture or second checkout cannot clobber the main tree's tag cache.
  `files` is an optional list of repo-relative source files to index. Because
  `update_tag_cache` treats that list as the complete indexed set, use a
  dedicated `cache_path` when passing `files` (as the tests do); otherwise the
  shared tag cache loses its other entries.
- Results are ordered by fused score, then BM25 score, then path.

### Empty and degenerate queries

An empty or whitespace-only query is a normal result, not an error:

```python
{"ok": True, "query": "   ", "results": [], "n": 0,
 "empty": True, "note": "empty query; nothing to search"}
```

No index or tag-cache work is done in that case. A non-empty query that
tokenizes to no searchable terms (only stopwords or one-character tokens)
returns `ok=True`, `empty=False`, an explanatory `note`, and no results.
`limit=0` also returns no results. A missing root directory returns
`ok=False` with an `error`.

## Index and scoring

### Corpus

`update_tag_cache` supplies the file set, content hashes, and definition tags.
When the default repo-map scan finds no files (for example a flat temporary
fixture), `code_search` falls back to supported files anywhere under `root`,
skipping the repo-map skip directories. The real repository uses the normal
`SOURCE_DIRS` scan because its cache is non-empty. `code_search` then reads
each indexed source file and builds an in-memory inverted index. One file is
one BM25 document with three weighted fields:

| Field | Source | Weight |
|---|---|---|
| path | repo-relative path, tokenized | 3.0 |
| symbol | definition names from the tag cache | 4.0 |
| line | every source line | 1.0 |

Path and symbol hits are stronger signals than the same term in a comment or
string. Files are read in sorted order; files larger than the repo-map
`MAX_FILE_BYTES` (2 MiB) contribute path/symbol terms but no source terms.
Unreadable files still contribute path/symbol terms.

### Tokenization

Text is lower-cased and split into identifiers. Each identifier contributes
its whole lower-case form plus camel-case and underscore parts, so
`semantic_search`, `SemanticSearch`, and the query `semantic search` all meet.
Stopwords (`the`, `and`, `for`, ...) and one-character terms are dropped.
There is no stemming, phrase matching, or synonym expansion.

Postings are parallel `array` objects (`file_id`, weighted term frequency)
rather than nested dicts. That keeps the full-tree index in the low hundreds
of megabytes instead of gigabytes; snippets are found by scanning the source
of the returned files, not by storing a line posting for every term.

### BM25

Defaults are **k1 = 1.5** and **b = 0.75**, both keyword arguments.
Per-file document length is the sum of weighted term frequencies; `avgdl` is
the mean over indexed files. IDF is the positive BM25 form:

```
idf(t) = ln(1 + (N - df(t) + 0.5) / (df(t) + 0.5))
score  = Σ_t idf(t) · tf · (k1 + 1) / (tf + k1 · (1 - b + b · dl / avgdl))
```

`k1` is clamped to `>= 0`, `b` to `[0, 1]`, and `rrf_k` to `>= 1`.

### PageRank component

The existing repo-map reference graph is built with
`build_reference_graph`; `personalized_pagerank(graph, task="")` supplies a
query-independent structural prior. Edges are sorted before the power
iteration so float summation is stable across processes. `graph` in a result
is this raw PageRank value; 0 means the file has no tag-graph node (for
example a file with no definitions or references).

PageRank only **reranks lexical candidates**. It does not add graph-only files
to the result set: search still requires a positive BM25 score.

### Reciprocal Rank Fusion

RRF is computed with **k = 60** over the BM25 file ranking and the PageRank
file ranking:

```
score(file) = 1 / (60 + bm25_rank(file))
            + 1 / (60 + pagerank_rank(file))   # if the file has a graph rank
```

Ranks start at 1. A lexical hit with no graph node gets only the BM25 term.
The graph ranking is taken in its deterministic `(-score, path)` order.

### Determinism and caching

File paths are sorted at index time, query terms are sorted and deduplicated,
graph edges are sorted, and final ties break on BM25 then path. Scores are
rounded to six decimals. Repeated calls with unchanged inputs therefore return
identical JSON.

The inverted index is held in a **one-entry process cache** keyed by
`(root, cache_path, tag_cache_root_hash)`. The repo-map root hash changes when
any indexed file's content changes, so a repeated MCP/CLI search in a quiet
tree reuses the index; a content edit rebuilds it. Only one index is retained
to bound memory.

## Integration notes (MCP / CLI)

The central integrator owns the shared wiring; this module exports one
function.

- **MCP:** expose `dev_code_search(query, limit=20, include_snippet=True)`
  returning the result dict. Keep `path`, `score`, `bm25`, `graph`, `symbols`,
  `line`, and `snippet`; agents need the snippet and the matched symbol, not
  just a path. Pass the shared `var/ocelot_dev_tags.json` cache path or rely on
  the `<root>/var` default.
- **CLI:** a `code-search QUERY` verb with `--limit`, `--no-snippet`, and
  `--json`; text mode can print `path:line  snippet` plus the per-component
  scores. Do not make it a write path.
- **Workflow:** use `dev_code_search` to locate a concept or name, then
  `dev_repo_map` / `dev_context` to expand context, and LSP/SCIP tools for
  compiler-accurate definitions and references. Search is a candidate
  generator, not a replacement for the reference graph.
- **No runtime coupling:** search is dev tooling. It does not touch
  `runners/dsl/`, seeds, or the agent runtime.

## Tests

```bash
.venv/bin/python -m pytest tests/test_code_search_migrated.py -q
```

The migrated test file covers:

- a symbol (`alpha`) and a docstring term (`frobnicated`) both hit the right
  file, with matched symbols and line/snippet;
- fusion ordering: a lexically stronger file loses to a graph-central file
  under RRF, with the exact expected fused score;
- whitespace-only query returns a clear empty result;
- a flat temporary fixture with no repo-map `SOURCE_DIRS` still discovers its
  root-level source files;
- repeated calls and a cache built from reversed file order return identical
  JSON;
- snippets stay within `MAX_SNIPPET_CHARS` and `include_snippet=False` omits
  `line`/`snippet`;
- documented defaults and configurable `k1`/`b`/`rrf_k`.

## Honest limitations

- **Lexical only.** This is the no-embedding half of hybrid retrieval. It does
  not find conceptually related code unless the query terms (or their
  camel/snake parts) occur in a path, symbol, or source line. Embeddings and a
  local model are deliberately deferred.
- **Syntactic, file-level graph.** PageRank uses the existing tree-sitter/AST
  reference graph. Its documented limits apply: references are not
  scope-resolved, generic high-fan-out names are skipped, and the graph is
  file-level. LSP/SCIP remains the precise layer.
- **No phrase, stem, or synonym handling.** Tokenization is deterministic
  identifier splitting plus stopword removal. A natural-language term must
  literally appear (case-insensitively) in the indexed fields.
- **BM25 is one weighted document per file.** Field weights are fixed and not
  tuned per language. It is a retrieval heuristic, not an evaluated benchmark.
- **Corpus scope.** Only files present in the repo-map tag cache are searched
  (`SOURCE_DIRS` and the repo-map `LANGUAGES` set). Markdown/docs and
  unsupported extensions are not indexed by this path.
- **Cost.** The tag cache on this tree is large (roughly 194 MB JSON), and the
  first search in a process must read/tokenize every indexed source file.
  Later searches reuse the one-entry index cache until file content changes.
  Snippets add a scan of only the returned files.
- **No persisted search index.** The inverted index is process memory only;
  restarting the MCP server rebuilds it. The tag cache remains the durable
  incremental layer.
