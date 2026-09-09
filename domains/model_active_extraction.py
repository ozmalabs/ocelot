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
# (A) STATIC — embedding geometry + FFN concept neurons.
# ---------------------------------------------------------------------------

@dataclass
class LoadedModel:
    """Static handle to a generative LM's readable weights (no inference)."""
    blob: str
    vec_fn: object
    vocab: dict
    inv: dict
    shape: tuple
    marker: str
    work_ids: list           # the working-vocab token ids (frequency window)
    _M: np.ndarray = field(default=None, repr=False)   # unit embeddings of work_ids
    _pos: dict = field(default=None, repr=False)


def load_model(model_tag: str = "gemma3:4b", work_vocab: int = 40000) -> LoadedModel:
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
                       shape=shape, marker=marker, work_ids=work, _M=M, _pos=pos)


def distill_embedding_graph(lm: LoadedModel, *, k: int = 16, quant: float = 0.05):
    """Distil the embedding geometry into a `weight_distillation.DistilledGraph`
    over the working vocab (reuses the block-304000 distiller)."""
    W = lm._M                       # already unit rows over work_ids
    # build a vocab dict over the working slice using the readable token strings
    slice_vocab = {lm.inv[t]: j for j, t in enumerate(lm.work_ids)}
    return wd.distill(W, slice_vocab, token_ids=list(range(len(lm.work_ids))),
                      k=k, quant=quant)


def ffn_concepts(lm: LoadedModel, seed_words, *, layer: int = 20, top: int = 8):
    """Find the FFN value neuron in `layer` most aligned with the concept
    direction (mean embedding of `seed_words`), and return the tokens it
    PROMOTES — a typed concept read straight from the weights. Returns
    (neuron_index, alignment, [promoted_tokens])."""
    name = "blk.%d.ffn_down.weight" % layer
    D = mr.read_gguf_tensor(lm.blob, name)
    d_model = lm.shape[1]
    Dn = D if D.shape[1] == d_model else D.T           # rows = neurons, len d_model
    Dnu = Dn / (np.linalg.norm(Dn, axis=1, keepdims=True) + 1e-9)
    sv = _concept_direction(lm, seed_words)
    align = Dnu @ sv
    best = int(np.argmax(align))
    nb = Dn[best] / (np.linalg.norm(Dn[best]) + 1e-9)
    promoted_pos = np.argsort(-(lm._M @ nb))[:top]
    promoted = [lm.inv[lm.work_ids[int(j)]] for j in promoted_pos]
    return best, float(align[best]), promoted


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
