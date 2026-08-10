#!/bin/bash
cd /home/matt/ozma/internal/research/experiments/gamma-substrate
export PYTHONPATH=runners/dsl/python:.
export NW=10
python3 -u -c "import substrate_rs._native as N,os,time;print('ENGINE:',N.__file__,time.strftime('%Y-%m-%d %H:%M',time.localtime(os.path.getmtime(N.__file__))))"
python3 -u scratchpad3/r3b_confirm.py 100 1e-2
