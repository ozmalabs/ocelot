#!/usr/bin/env python3
"""Export locked per-model Qwen3 mode coefficients for cross-model transport v1."""
from __future__ import annotations
import argparse, hashlib, json, os, platform, resource, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
CORPUS=ROOT/'evaluation/substrate_capability/fixtures/llm_cross_model_transport_v1_corpus.json'

def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
    return h.hexdigest()

def file_record(path):
    p=Path(path);return {'path':str(p.resolve()),'bytes':p.stat().st_size,'sha256':sha256(p)}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--model-dir',required=True)
    ap.add_argument('--label',required=True,choices=['qwen3_0_6b','qwen3_1_7b'])
    ap.add_argument('--output',required=True)
    a=ap.parse_args(); model_dir=Path(a.model_dir).resolve(); out=Path(a.output).resolve()
    if any(p.exists() for p in (out,out.with_suffix('.tokenization.json'),out.with_suffix('.provenance.json'))):raise SystemExit('refusing to overwrite existing export artifacts')
    import numpy as np
    from transformers import AutoTokenizer, __version__ as transformers_version
    from domains import model_reader as mr, llm_structure_recovery as lsr, llm_native_graph as lng
    data=json.loads(CORPUS.read_text()); rows=data['examples']
    train=[r for r in rows if r['split']=='train']; held=[r for r in rows if r['split']=='heldout']
    if len(train)!=60 or len(held)!=10 or len({r['id'] for r in rows})!=70:raise SystemExit('invalid corpus/split')
    tok=AutoTokenizer.from_pretrained(str(model_dir),local_files_only=True,use_fast=True)
    train_ids=[tok.encode(r['text'],add_special_tokens=True) for r in train]
    held_ids=[tok.encode(r['text'],add_special_tokens=True) for r in held]
    cfg=model_dir/'config.json';index=model_dir/'model.safetensors.index.json'
    if index.exists():
        weight_map=json.loads(index.read_text())['weight_map']
        shards=sorted(set(weight_map.values()))
    else:
        weight_map=None;shards=['model.safetensors']
    source_files=[cfg,model_dir/'tokenizer.json',model_dir/'tokenizer_config.json']
    if index.exists():source_files.append(index)
    source_files.extend(model_dir/s for s in shards)
    sources=[file_record(p) for p in source_files]
    m=lsr.NumpyQwen3(str(model_dir))
    if weight_map is not None:
        def read_indexed(self,name):
            if name not in self._cache:
                shard=weight_map.get(name)
                if shard is None:raise KeyError(f'{name} absent from Safetensors index')
                self._cache[name]=mr.read_tensor(str(model_dir/shard),name).astype(np.float32)
            return self._cache[name]
        import types;m._t=types.MethodType(read_indexed,m)
    t0=time.perf_counter()
    lng.export_chain_structure(m,train_ids,held_ids,str(out),layers=[10,11,12,13,14],k=32,ridge=1.0,all_positions=False)
    elapsed=time.perf_counter()-t0
    sources_after=[file_record(p) for p in source_files]
    tokenization={'schema':'LlmCrossModelTransportTokenizationV1','model_label':a.label,'model_dir':str(model_dir),'corpus_sha256':sha256(CORPUS),'train_ids':[r['id'] for r in train],'heldout_ids':[r['id'] for r in held],'train_token_ids':train_ids,'heldout_token_ids':held_ids,'tokenizer_class':type(tok).__name__,'tokenizer_name_or_path':tok.name_or_path,'add_special_tokens':True}
    token_path=out.with_suffix('.tokenization.json');token_path.write_text(json.dumps(tokenization,indent=2,sort_keys=True)+'\n')
    side={'schema':'LlmCrossModelTransportV1Export','label':a.label,'model_config':json.loads(cfg.read_text()),'model_sources_before':sources,'model_sources_after':sources_after,'sources_stable':sources==sources_after,'corpus':file_record(CORPUS),'tokenization':file_record(token_path),'export':file_record(out),'export_seconds':elapsed,'layers':[10,11,12,13,14],'training_examples':len(train),'heldout_examples':len(held),'modes':32,'ridge':1.0,'all_positions':False,'python':sys.version,'numpy':np.__version__,'transformers':transformers_version,'platform':platform.platform(),'max_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    out.with_suffix('.provenance.json').write_text(json.dumps(side,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'label':a.label,'export':str(out),'seconds':elapsed,'max_rss_kib':side['max_rss_kib'],'layers':[10,11,12,13,14],'train':len(train),'heldout':len(held),'tokenization':str(token_path)},sort_keys=True))
if __name__=='__main__':main()
