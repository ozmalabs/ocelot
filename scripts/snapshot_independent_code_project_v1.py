#!/usr/bin/env python3
"""Metadata-only deterministic project selector and source/license snapshotter."""
from __future__ import annotations
import hashlib, json, re, shutil
from importlib import metadata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'data/independent_python_project_v1'
ALLOWED={'mit','apache-2.0','bsd-3-clause'}
PREFIX=b'ocelot-independent-code-transfer-v1\0'

def sha(b):return hashlib.sha256(b).hexdigest()
def norm(s):return re.sub(r'[-_.]+','-',s.strip().lower())
def is_test(path):
    parts={x.lower() for x in Path(str(path)).parts}
    base=Path(str(path)).name.lower()
    return bool(parts & {'test','tests'}) or base.startswith('test_')
def is_license(path):
    base=Path(str(path)).name.lower()
    return any(x in base for x in ('license','copying','notice'))
def license_id(d):
    expr=(d.metadata.get('License-Expression') or '').strip().lower()
    lic=(d.metadata.get('License') or '').strip().lower()
    return expr if expr in ALLOWED else lic if lic in ALLOWED else ''
def candidates():
    out=[]
    for d in metadata.distributions():
        name=d.metadata.get('Name','').strip()
        if not name:continue
        fs=list(d.files or [])
        py=sorted({str(f) for f in fs if str(f).endswith('.py') and not is_test(f) and '.dist-info/' not in str(f) and '.egg-info/' not in str(f)})
        licfiles=sorted({str(f) for f in fs if is_license(f)})
        lid=license_id(d)
        if lid in ALLOWED and len(py)>=10 and licfiles:
            out.append((d,{'name':name,'normalized_name':norm(name),'version':d.version,'license_id':lid,'python_file_count':len(py),'license_files':licfiles,'python_files':py}))
    return out
def main():
    options=candidates()
    if not options:raise SystemExit('no distribution meets the frozen metadata/license/file-count rule')
    options.sort(key=lambda x:(sha(PREFIX+x[1]['normalized_name'].encode()),x[1]['normalized_name']))
    dist,chosen=options[0]
    if DEST.exists():shutil.rmtree(DEST)
    source_root=DEST/'source'; license_root=DEST/'licenses'; source_root.mkdir(parents=True); license_root.mkdir(parents=True)
    copied=[]
    for rel in chosen['python_files']:
        src=Path(dist.locate_file(rel)); dst=source_root/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(src,dst)
        data=dst.read_bytes(); copied.append({'path':rel,'sha256':sha(data),'bytes':len(data)})
    licenses=[]
    for rel in chosen['license_files']:
        src=Path(dist.locate_file(rel))
        if not src.is_file():continue
        dst=license_root/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(src,dst)
        data=dst.read_bytes(); licenses.append({'path':rel,'sha256':sha(data),'bytes':len(data)})
    if not licenses:raise SystemExit('metadata license paths were not materialized')
    manifest={'schema':'independent-python-project-snapshot-v1','selection_rule':'minimum SHA256(name-prefix + normalized distribution name) among exact permissive-license distributions with >=10 production .py files and packaged license documents','selected_distribution':{k:v for k,v in chosen.items() if k not in ('python_files','license_files')},'selection_digest':sha(PREFIX+chosen['normalized_name'].encode()),'eligible_distribution_count':len(options),'eligible_distributions':[{'name':x[1]['name'],'normalized_name':x[1]['normalized_name'],'version':x[1]['version'],'license_id':x[1]['license_id'],'python_file_count':x[1]['python_file_count'],'selection_digest':sha(PREFIX+x[1]['normalized_name'].encode())} for x in options],'python_files':copied,'license_files':licenses}
    (DEST/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    (DEST/'SOURCE.md').write_text(f"Deterministically selected installed distribution {chosen['name']} {dist.version}; source files and packaged license texts were copied byte-for-byte according to snapshot manifest. Do not import or execute this source during selection or scoring.\n")
    print(json.dumps({'snapshot':DEST.relative_to(ROOT).as_posix(),'distribution':chosen['name'],'version':dist.version,'license_id':chosen['license_id'],'eligible_distributions':len(options),'python_files':len(copied),'license_files':len(licenses),'selection_digest':manifest['selection_digest']},indent=2))
if __name__=='__main__':main()
