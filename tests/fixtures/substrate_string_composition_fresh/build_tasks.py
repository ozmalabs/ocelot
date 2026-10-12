#!/usr/bin/env python3
"""Build a fresh generated family of two-stage string-composition PBE tasks."""
from __future__ import annotations
import json, random
from pathlib import Path
HERE=Path(__file__).resolve().parent; OUT=HERE/'tasks.json'
SPECS=(
 ('casefold_count','casefolds the input and counts non-overlapping occurrences of {sub!r}',('ab','xy','cd')),
 ('casefold_split','lowercases the input and then splits it on {sep!r}, ignoring separator case',('A','B','C')),
 ('reverse_then_split','reverses the entire input string and then splits it on {sep!r}',('|',',',';')),
 ('remove_separator','splits the input on {sep!r} and concatenates the resulting pieces without a separator',('-', '_', ':')),
 ('reverse_then_replace','reverses the entire input and then replaces every {old!r} with {new!r}',(('a','X'),('e','Q'),('-','_'))),
 ('split_reverse_tokens','splits the input on {sep!r}, reverses the characters of each token, and preserves token order',(':','|',';')),
)
ALPHABET='abcdeABCDE xyz-_,!?'
def text(rng,n=None,alphabet=ALPHABET):
 n=n or rng.randint(8,18);return ''.join(rng.choice(alphabet) for _ in range(n))
def oracle(family,s,arg):
 if family=='casefold_count':return s.casefold().count(arg.casefold())
 if family=='casefold_split':return s.casefold().split(arg.casefold())
 if family=='reverse_then_split':return s[::-1].split(arg)
 if family=='remove_separator':return ''.join(s.split(arg))
 if family=='reverse_then_replace':return s[::-1].replace(arg[0],arg[1])
 if family=='split_reverse_tokens':return [x[::-1] for x in s.split(arg)]
 raise ValueError(family)
def make_rows(rng,family,arg):
 rows=[];seen=set()
 while len(rows)<7:
  if family in ('casefold_split','reverse_then_split','remove_separator','split_reverse_tokens'):
   alphabet='abcdeABCDE xyz' if family=='casefold_split' else 'abcdefXYZuvw'
   toks=[''.join(rng.choice(alphabet) for _ in range(rng.randint(2,7))) for _ in range(rng.randint(2,4))]
   sep=arg; value=sep.join(toks)
   if family=='casefold_split':
    value=''.join((sep.lower() if rng.random()<.5 else sep.upper()) if ch==sep else ch for ch in value)
  else:
   value=text(rng)
  if value in seen:continue
  seen.add(value);rows.append({'inputs':{'s':value},'expected':oracle(family,value,arg)})
 return rows
def fmt(family,arg):
 if family in ('casefold_count',):return {'sub':arg}
 if family in ('casefold_split','reverse_then_split','remove_separator','split_reverse_tokens'):return {'sep':arg}
 if family=='reverse_then_replace':return {'old':arg[0],'new':arg[1]}
def build():
 tasks=[];ordinal=0
 for family,template,params in SPECS:
  for j,arg in enumerate(params,1):
   ordinal+=1; rows=make_rows(random.Random(20261003+ordinal*7919),family,arg)
   tasks.append({'id':f'fresh_{family}_{j:02d}','family':family,'oracle_kind':family,'parameter':arg,
    'request_text':'Write a function that '+template.format(**fmt(family,arg))+'.',
    'example_rows':rows[:4],'held_out_rows':rows[4:]})
 return {'suite_id':'substrate-string-composition-fresh-v1','task_count':len(tasks),
  'design':'18 seeded tasks in six two-stage string-composition strata; four revealed and three held-out rows per task',
  'seed_rule':'random.Random(20261003 + one-based-task-index * 7919)','tasks':tasks}
def main():OUT.write_text(json.dumps(build(),indent=2,sort_keys=True)+'\n');print(OUT)
if __name__=='__main__':main()
