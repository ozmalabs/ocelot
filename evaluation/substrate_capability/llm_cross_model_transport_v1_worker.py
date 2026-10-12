#!/usr/bin/env python3
"""Fresh-process adapter for the locked chain fan-in worker."""
import importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
runner=ROOT/'evaluation/substrate_capability/llm_chain_transport_fanin_v1.py'
spec=importlib.util.spec_from_file_location('locked_chain_fanin',runner)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
mod.EXPORT=Path(sys.argv[1]).resolve()
print(json.dumps(mod.worker(int(sys.argv[2])),sort_keys=True,separators=(',',':')))
