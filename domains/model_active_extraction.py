"""Extract structure from a generative LM into a substrate graph — BOTH by
reading the static weights AND by RUNNING the model, with the graph driving
what to extract.

The user's ask: *"we should be able to extract more by running some of the
model. we should be able to start a graph and have it analyse the model and
pull apart parts of it to build the bits it needs."*

See docs/research/psychology_affect/MODEL_ACTIVE_EXTRACTION_PREREG.md.

THREE CAPABILITIES:
  (A) STATIC — read the GGUF weights (no inference):
      * embedding matrix -> kNN graph (reuses `weight_distillation.distill`)
      * FFN value neurons -> typed concept nodes (Geva et al. key-value view:
        a neuron's value vector, projected through the embedding, names the
        tokens it promotes — its concept). The jabberwock_gemma_neurons
        pattern, minted as graph nodes.
  (B) RUNNING THE MODEL — prompt it and parse completions into typed edges
      (`IsA`, `AtLocation`, ...). This surfaces RELATIONAL structure the raw
      embedding geometry does not carry as explicit edges.
  (C) GRAPH-DRIVEN ACTIVE loop — the graph scores its OWN sparse/uncertain
      nodes, issues TARGETED probes to the model for exactly those, mints the
      returned edges, and remeasures. The graph pulls apart the model to build
      the bits IT needs.

HONEST CAPABILITY BOUND (stated plainly): the only way to run the model in
this environment is the ollama HTTP API, which returns COMPLETIONS, not hidden
activations (no torch / transformers / llama_cpp — only numpy). So "running
the model" here is BEHAVIOURAL PROBING (prompt -> text), NOT activation
tapping. Reading intermediate activations mid-forward-pass is a named
follow-on that needs a framework not installed here.
"""

from __future__ import annotations

import json
import os
import re
import urllib.request
from dataclasses import dataclass, field

import numpy as np

from . import model_reader as mr
from . import weight_distillation as wd

# Ollama's models live under the service user's home in this environment;
# model_reader.ollama_blob's root list does not include it, so resolve here.
_OLLAMA_ROOTS = (
    "/usr/share/ollama/.ollama/models",
    "/var/lib/ollama/.ollama/models",
    os.path.expanduser("~/.ollama/models"),
)


def resolve_gguf_blob(model_tag: str):
    """Resolve 'gemma3:4b' -> its GGUF blob path, searching the service-user
    roots model_reader.ollama_blob misses. Returns path or None."""
    name, _, tag = model_tag.partition(":")
    tag = tag or "latest"
    for root in _OLLAMA_ROOTS:
        man = os.path.join(root, "manifests/registry.ollama.ai/library", name, tag)
        if not os.path.isfile(man):
            continue
        with open(man) as f:
            m = json.load(f)
        for layer in m["layers"]:
            if "model" in layer["mediaType"]:
                dig = layer["digest"].replace("sha256:", "sha256-")
                blob = os.path.join(root, "blobs", dig)
                if os.path.isfile(blob):
                    return blob
    return None


# ---------------------------------------------------------------------------
# Sharded local HF safetensors reader — newer models (Qwen3, ...) ship a
# model.safetensors.index.json weight_map across several shard files.
# ---------------------------------------------------------------------------

def _shard_map(model_dir: str):
    """tensor_name -> shard file path, from model.safetensors.index.json, or a
    single-file map when the dir has one model.safetensors."""
    idx = os.path.join(model_dir, "model.safetensors.index.json")
    if os.path.isfile(idx):
        with open(idx) as f:
            wm = json.load(f)["weight_map"]
        return {k: os.path.join(model_dir, v) for k, v in wm.items()}
    single = os.path.join(model_dir, "model.safetensors")
    if os.path.isfile(single):
        return {n: single for n in mr.tensor_names(single)}
    raise FileNotFoundError("no safetensors index or single file in %s" % model_dir)


def read_local_tensor(model_dir: str, name: str) -> np.ndarray:
    """Read a named tensor from a (possibly sharded) local HF safetensors dir."""
    return mr.read_tensor(_shard_map(model_dir)[name], name)


def _first_present(shardmap, candidates):
    for c in candidates:
        if c in shardmap:
            return c
    return None


# ---------------------------------------------------------------------------
# (A) STATIC — embedding geometry + FFN concept neurons.
# ---------------------------------------------------------------------------

@dataclass
class LoadedModel:
    """Static handle to a generative LM's readable weights (no inference).
    `kind` is 'gguf' (ollama tag) or 'hf' (local sharded safetensors dir);
    `src` is the blob path (gguf) or model dir (hf)."""
    blob: str
    vec_fn: object
    vocab: dict
    inv: dict
    shape: tuple
    marker: str
    work_ids: list           # the working-vocab token ids (frequency window)
    kind: str = "gguf"
    src: str = ""
    _ffn_prefix: str = "model.layers"
    _M: np.ndarray = field(default=None, repr=False)   # unit embeddings of work_ids
    _Mout: np.ndarray = field(default=None, repr=False)  # unit UNEMBED rows (untied lm_head), else None
    _pos: dict = field(default=None, repr=False)


def load_model(model_tag: str = "gemma3:4b", work_vocab: int = 40000) -> LoadedModel:
    """Load a model's static weights. `model_tag` is either an ollama tag
    (e.g. 'gemma3:4b' -> GGUF) or a local HF dir path (e.g.
    '/applications/data/model_graph_work/Qwen3-1.7B' -> sharded safetensors)."""
    if os.path.isdir(model_tag):
        return _load_hf(model_tag, work_vocab)
    blob = resolve_gguf_blob(model_tag)
    if blob is None:
        raise FileNotFoundError("no GGUF blob for %r" % model_tag)
    vec_fn, vocab, shape = mr.gguf_embedding(blob)
    inv = {i: t for t, i in vocab.items()}
    marker = mr.ModelTensors.marker(vocab)
    work = list(range(min(work_vocab, shape[0])))
    M = np.array([vec_fn(i) for i in work], dtype=np.float32)
    M = M / (np.linalg.norm(M, axis=1, keepdims=True) + 1e-9)
    pos = {t: j for j, t in enumerate(work)}
    return LoadedModel(blob=blob, vec_fn=vec_fn, vocab=vocab, inv=inv,
                       shape=shape, marker=marker, work_ids=work,
                       kind="gguf", src=blob, _M=M, _pos=pos)


def _load_hf(model_dir: str, work_vocab: int) -> LoadedModel:
    smap = _shard_map(model_dir)
    emb_name = _first_present(smap, ("model.embed_tokens.weight",
                                     "model.language_model.embed_tokens.weight",
                                     "transformer.wte.weight"))
    if emb_name is None:
        emb_name = next(n for n in smap if "embed" in n.lower()
                        and "vision" not in n.lower() and "visual" not in n.lower())
    W = mr.read_tensor(smap[emb_name], emb_name)      # (vocab, dim)
    vocab = mr.read_vocab(model_dir)
    inv = {i: t for t, i in vocab.items()}
    marker = mr.ModelTensors.marker(vocab)
    shape = W.shape
    work = list(range(min(work_vocab, shape[0])))
    M = W[work].astype(np.float32)
    M = M / (np.linalg.norm(M, axis=1, keepdims=True) + 1e-9)
    pos = {t: j for j, t in enumerate(work)}

    def vec_fn(i):
        return W[i]

    # detect the FFN down_proj naming prefix for this model (varies: bare, or
    # 'model.language_model.' for multimodal-wrapped LMs).
    ffn_prefix = _detect_ffn_prefix(smap)

    lm = LoadedModel(blob=model_dir, vec_fn=vec_fn, vocab=vocab, inv=inv,
                     shape=shape, marker=marker, work_ids=work,
                     kind="hf", src=model_dir, _M=M, _pos=pos)
    lm._ffn_prefix = ffn_prefix
    # UNTIED output embedding: an FFN neuron writes into the residual read by
    # lm_head, so the "tokens it promotes" projection must use lm_head, not the
    # input embedding. Detect + load the unembed rows for the working vocab.
    head_name = _first_present(smap, ("lm_head.weight",
                                      "model.language_model.lm_head.weight"))
    if head_name is not None:
        H = mr.read_tensor(smap[head_name], head_name)   # (vocab, dim)
        if H.shape[0] >= max(work) + 1 and H.shape[1] == shape[1]:
            Hm = H[work].astype(np.float32)
            lm._Mout = Hm / (np.linalg.norm(Hm, axis=1, keepdims=True) + 1e-9)
    return lm


def _detect_ffn_prefix(smap) -> str:
    """Return the layer-tensor prefix such that
    '<prefix>.<L>.mlp.down_proj.weight' exists (bare 'model.layers' or the
    multimodal 'model.language_model.layers')."""
    for prefix in ("model.language_model.layers", "model.layers"):
        if any(k.startswith(prefix + ".") and "mlp.down_proj.weight" in k
               for k in smap):
            return prefix
    return "model.layers"


def distill_embedding_graph(lm: LoadedModel, *, k: int = 16, quant: float = 0.05):
    """Distil the embedding geometry into a `weight_distillation.DistilledGraph`
    over the working vocab (reuses the block-304000 distiller)."""
    W = lm._M                       # already unit rows over work_ids
    # build a vocab dict over the working slice using the readable token strings
    slice_vocab = {lm.inv[t]: j for j, t in enumerate(lm.work_ids)}
    return wd.distill(W, slice_vocab, token_ids=list(range(len(lm.work_ids))),
                      k=k, quant=quant)


def _read_ffn_down(lm: LoadedModel, layer: int) -> np.ndarray:
    """Read layer `layer`'s FFN down-projection (value-neuron bank), routing by
    source format."""
    if lm.kind == "gguf":
        return mr.read_gguf_tensor(lm.blob, "blk.%d.ffn_down.weight" % layer)
    name = "%s.%d.mlp.down_proj.weight" % (getattr(lm, "_ffn_prefix",
                                                    "model.layers"), layer)
    return read_local_tensor(lm.src, name)


def ffn_concepts(lm: LoadedModel, seed_words, *, layer: int = 20, top: int = 8):
    """Find the FFN value neuron in `layer` most aligned with the concept
    direction (mean embedding of `seed_words`), and return the tokens it
    PROMOTES — a typed concept read straight from the weights. Returns
    (neuron_index, alignment, [promoted_tokens])."""
    D = _read_ffn_down(lm, layer)
    d_model = lm.shape[1]
    Dn = D if D.shape[1] == d_model else D.T           # rows = neurons, len d_model
    Dnu = Dn / (np.linalg.norm(Dn, axis=1, keepdims=True) + 1e-9)
    sv = _concept_direction(lm, seed_words)
    align = Dnu @ sv
    best = int(np.argmax(align))
    nb = Dn[best] / (np.linalg.norm(Dn[best]) + 1e-9)
    # project through the OUTPUT embedding (lm_head) when untied, else the
    # input embedding (tied) — a neuron promotes tokens in the UNEMBED space.
    Mproj = lm._Mout if getattr(lm, "_Mout", None) is not None else lm._M
    promoted_pos = np.argsort(-(Mproj @ nb))[:top]
    promoted = [lm.inv[lm.work_ids[int(j)]] for j in promoted_pos]
    return best, float(align[best]), promoted


def ffn_concepts_best_layer(lm: LoadedModel, seed_words, *, layers=None,
                            top: int = 8):
    """Search a set of layers for the FFN neuron MOST aligned with the concept,
    returning (layer, neuron_index, alignment, promoted). Different
    architectures localise concept-neurons at different depths (measured: gemma3
    mid-stack, Qwen3 late-stack), so a fair concept read searches rather than
    assuming a fixed layer. `layers` defaults to a spread across the stack."""
    n_layers = _n_layers(lm)
    if layers is None:
        layers = sorted(set(int(f * (n_layers - 1)) for f in
                            (0.15, 0.3, 0.45, 0.6, 0.75, 0.9)))
    best = (None, None, -1.0, [])
    for L in layers:
        try:
            idx, align, promoted = ffn_concepts(lm, seed_words, layer=L, top=top)
        except Exception:
            continue
        if align > best[2]:
            best = (L, idx, align, promoted)
    return best


def _n_layers(lm: LoadedModel) -> int:
    if lm.kind == "gguf":
        try:
            mt = mr.ModelTensors("ollama:" + _tag_from_blob(lm.blob))
            return mt.n_layers
        except Exception:
            return 34            # gemma3:4b default
    # HF: count from config.json
    try:
        cfg = json.load(open(os.path.join(lm.src, "config.json")))
        tc = cfg.get("text_config", cfg)
        return int(tc["num_hidden_layers"])
    except Exception:
        return 28


def _tag_from_blob(blob):
    # best-effort; only used for gguf layer count
    return "gemma3:4b"


# ---------------------------------------------------------------------------
# GRAPH-LIKENESS metrics — model-agnostic, over the embedding + FFN.
# A "graph-like" representation has: sharp, on-concept FFN neurons; crisp
# RECIPROCAL kNN neighbourhoods (mutual nearest neighbours = clean edges); and
# a geometry that SURVIVES sparsification/quantisation (distils to a graph
# without collapsing). Every metric is computed identically across models.
# ---------------------------------------------------------------------------

def ffn_concept_score(lm: LoadedModel, concept_seed_sets, *, top: int = 10):
    """Mean best-layer FFN concept ALIGNMENT + PURITY across a set of concepts.
    alignment = cosine of the most-aligned neuron to the concept direction;
    purity = fraction of the neuron's top promoted tokens whose embedding is
    itself on-concept (cosine to the seed direction > 0.15). Higher = the model
    packs concepts into cleaner single directions = more graph-like.
    Returns {'alignment': float, 'purity': float, 'per': {...}}."""
    aligns, purities, per = [], [], {}
    for name, seeds in concept_seed_sets.items():
        try:
            L, idx, align, promoted = ffn_concepts_best_layer(lm, seeds, top=top)
        except Exception:
            continue
        sv = _concept_direction(lm, seeds)
        onc = 0
        for t in promoted:
            tid = lm.vocab.get(t)
            if tid is None:
                continue
            v = lm.vec_fn(tid)
            if float(v @ sv / (np.linalg.norm(v) + 1e-9)) > 0.15:
                onc += 1
        purity = onc / max(len(promoted), 1)
        aligns.append(align)
        purities.append(purity)
        per[name] = {"layer": L, "align": round(align, 3),
                     "purity": round(purity, 3)}
    return {"alignment": float(np.mean(aligns)) if aligns else 0.0,
            "purity": float(np.mean(purities)) if purities else 0.0,
            "per": per}


def knn_reciprocity(lm: LoadedModel, *, sample: int = 3000, k: int = 8,
                    rng=None):
    """Fraction of directed kNN edges that are RECIPROCAL (mutual nearest
    neighbours) over a random sample of the working vocab. A graph-like space
    has crisp, mutual neighbourhoods (i in kNN(j) iff j in kNN(i)); a diffuse
    space has asymmetric hub-dominated neighbourhoods. Higher = more graph-like.
    """
    import random as _random
    rng = rng or _random.Random(0)
    n = len(lm.work_ids)
    idx = rng.sample(range(n), min(sample, n))
    S = lm._M[idx]                       # unit rows
    sims = S @ S.T
    np.fill_diagonal(sims, -2.0)
    knn = np.argsort(-sims, axis=1)[:, :k]     # positions within the sample
    knn_sets = [set(row.tolist()) for row in knn]
    recip = tot = 0
    for i in range(len(idx)):
        for j in knn[i]:
            tot += 1
            if i in knn_sets[j]:
                recip += 1
    return recip / max(tot, 1)


def distill_survival(lm: LoadedModel, *, probes=None, k: int = 8, bits=(8, 4, 3)):
    """kNN recall@k retained after VECTOR QUANTISATION at each bit depth vs the
    full-precision neighbours (block-304000 distillation-survival, per model).
    A more graph-like geometry survives compression better. Returns
    {bits: recall}."""
    if probes is None:
        probes = list(range(0, min(len(lm.work_ids), 2000), 200))  # ~10 probes
    M = lm._M
    lo, hi = float(M.min()), float(M.max())
    # full-precision gold neighbours (positions)
    gold = {}
    for p in probes:
        sims = M @ M[p]
        sims[p] = -2.0
        gold[p] = set(np.argsort(-sims)[:k].tolist())
    out = {}
    for b in bits:
        step = (hi - lo) / (2 ** b - 1)
        Mq = lo + np.round((M - lo) / step) * step
        Mq = Mq / (np.linalg.norm(Mq, axis=1, keepdims=True) + 1e-9)
        rr = []
        for p in probes:
            sims = Mq @ Mq[p]
            sims[p] = -2.0
            got = set(np.argsort(-sims)[:k].tolist())
            rr.append(len(gold[p] & got) / max(len(gold[p]), 1))
        out[b] = float(np.mean(rr))
    return out


def graphlike_report(lm: LoadedModel, concept_seed_sets, *, rng=None) -> dict:
    """Full graph-likeness battery for one model."""
    ffn = ffn_concept_score(lm, concept_seed_sets)
    recip = knn_reciprocity(lm, rng=rng)
    surv = distill_survival(lm)
    return {"ffn_alignment": ffn["alignment"], "ffn_purity": ffn["purity"],
            "knn_reciprocity": recip, "distill_survival": surv,
            "ffn_per": ffn["per"]}


def _concept_direction(lm: LoadedModel, seed_words):
    vecs = []
    for w in seed_words:
        tid = lm.vocab.get(lm.marker + w, lm.vocab.get(w))
        if tid is not None:
            vecs.append(lm.vec_fn(tid))
    if not vecs:
        raise ValueError("no seed words in vocab: %r" % (seed_words,))
    v = np.mean(vecs, axis=0)
    return v / (np.linalg.norm(v) + 1e-9)


# ---------------------------------------------------------------------------
# (B) RUNNING THE MODEL — ollama behavioural probing (completions only).
# ---------------------------------------------------------------------------

_OLLAMA_URL = "http://localhost:11434/api/generate"

# relation -> (probe template, edge_type). Instruction-framed so the model
# returns a BARE answer (gemma echoes+continues a bare cloze and wraps answers
# in markdown; the "one word" instruction yields a clean single token).
RELATION_TEMPLATES = {
    "IsA": ("Complete with one word. A {s} is a kind of:", "is_a"),
    "AtLocation": ("Complete with one word. You usually find a {s} in a:", "at_location"),
    "UsedFor": ("Complete with one word. A {s} is used for:", "used_for"),
    "HasProperty": ("Complete with one word. A {s} is typically:", "has_property"),
    "PartOf": ("Complete with one word. A {s} is part of a:", "part_of"),
}

_STOP = {"a", "an", "the", "of", "to", "in", "on", "at", "for", "and", "or",
         "is", "are", "very", "usually", "kind", "part", "used", "with",
         "your", "you", "it", "that", "this", "some", "any", "most", "people"}


def ollama_available(model_tag: str = "gemma3:4b", timeout: float = 3.0) -> bool:
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            tags = json.load(r)
        return any(m.get("name", "").startswith(model_tag.split(":")[0])
                   for m in tags.get("models", []))
    except Exception:
        return False


def _generate(prompt: str, model_tag: str, *, n_predict: int = 8,
              timeout: float = 60.0) -> str:
    body = json.dumps({
        "model": model_tag, "prompt": prompt, "stream": False,
        "options": {"num_predict": n_predict, "temperature": 0.0},
    }).encode()
    req = urllib.request.Request(_OLLAMA_URL, data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r).get("response", "")


def _parse_target(completion: str, prompt: str = ""):
    """First content word of the completion = the relation target. Strips any
    echoed prompt prefix and markdown (** __ etc.) that gemma wraps answers in."""
    text = completion
    if prompt and text.startswith(prompt):
        text = text[len(prompt):]
    text = text.replace("*", " ").replace("_", " ").replace("`", " ")
    for tok in re.findall(r"[A-Za-z][A-Za-z\-]+", text.lower()):
        if tok not in _STOP and len(tok) > 1:
            return tok
    return None


def probe_relation(subject: str, relation: str, *, model_tag: str = "gemma3:4b",
                   timeout: float = 60.0):
    """Run the model on a relation template and parse the target. Returns
    (edge_type, target) or None. The edge comes from the MODEL'S output, not
    authored."""
    tmpl, edge_type = RELATION_TEMPLATES[relation]
    prompt = tmpl.format(s=subject)
    comp = _generate(prompt, model_tag, timeout=timeout)
    tgt = _parse_target(comp, prompt)
    if tgt is None or tgt == subject:
        return None
    return edge_type, tgt


# ---------------------------------------------------------------------------
# (C) GRAPH-DRIVEN ACTIVE loop — the graph pulls apart the model.
# ---------------------------------------------------------------------------

def relational_degree(inner, node, edge_types) -> int:
    """How many RELATIONAL (typed) edges a node already has — the graph's own
    measure of how well-connected/known this concept is."""
    tot = 0
    for et in edge_types:
        try:
            tot += len(list(inner.neighbours(node, et)))
        except Exception:
            pass
    return tot


def active_extract(substrate, node_map, *, model_tag: str = "gemma3:4b",
                   relations=None, budget: int = 20, targeted: bool = True,
                   rng=None):
    """The graph drives extraction: score nodes by relational sparsity, pick
    the WEAKEST (targeted) or RANDOM (baseline), probe the model for the
    missing relations, mint the returned typed edges. Returns a report dict
    {probes, edges_added, per_relation, targets_hit}.

    `node_map` -> {concept_name: node}. `targeted=True` picks the sparsest
    nodes (the graph's self-diagnosed gaps); `targeted=False` picks random
    nodes (the control). The edge weights/targets come from the MODEL, not
    authored.
    """
    import random as _random
    rng = rng or _random.Random(0)
    inner = substrate._inner if hasattr(substrate, "_inner") else substrate
    relations = relations or list(RELATION_TEMPLATES)
    edge_types = [RELATION_TEMPLATES[r][1] for r in relations]

    names = list(node_map)
    if targeted:
        names.sort(key=lambda n: relational_degree(inner, node_map[n], edge_types))
    else:
        rng.shuffle(names)

    probes = edges_added = 0
    per_relation = {r: 0 for r in relations}
    targets = {}
    for name in names:
        if probes >= budget:
            break
        for rel in relations:
            if probes >= budget:
                break
            probes += 1
            try:
                res = probe_relation(name, rel, model_tag=model_tag)
            except Exception:
                res = None
            if res is None:
                continue
            edge_type, tgt = res
            # mint the target node if new, then the typed edge
            if tgt not in node_map:
                node_map[tgt] = inner.add_node(
                    "Concept", {"name": tgt, "state": 0.0,
                                "external_field": 0.0, "identity_field": 0.0})
            try:
                inner.add_edge(node_map[name], edge_type, node_map[tgt], {})
            except Exception:
                try:
                    inner.add_edge_unchecked(node_map[name], edge_type, node_map[tgt])
                except Exception:
                    continue
            edges_added += 1
            per_relation[rel] += 1
            targets.setdefault(name, []).append((edge_type, tgt))
    return {"probes": probes, "edges_added": edges_added,
            "per_relation": per_relation, "targets": targets}
