#!/usr/bin/env python3
"""Metadata-only deterministic project selector and source/license snapshotter."""
from __future__ import annotations
import hashlib, json, re, shutil
from importlib import metadata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'data/independent_python_projects_v1_1'
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
    options.sort(key=lambda x:(x[1]['normalized_name'],x[1]['name']))
    if DEST.exists():shutil.rmtree(DEST)
    projects=[]
    for dist,chosen in options:
        base=DEST/chosen['normalized_name']; source_root=base/'source'; license_root=base/'licenses'
        source_root.mkdir(parents=True); license_root.mkdir(parents=True)
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
        if not licenses:raise SystemExit('eligible metadata license paths were not materialized for '+chosen['name'])
        projects.append({'name':chosen['name'],'normalized_name':chosen['normalized_name'],'version':dist.version,
                         'license_id':chosen['license_id'],'python_file_count':len(copied),'license_file_count':len(licenses),
                         'python_files':copied,'license_files':licenses,
                         'selection_digest':sha(PREFIX+chosen['normalized_name'].encode())})
    manifest={'schema':'independent-python-project-set-v1.1','selection_rule':'all installed distributions meeting preregistered exact-license, license-file and production-python-file thresholds',
              'eligible_project_count':len(projects),'projects':projects}
    DEST.mkdir(parents=True,exist_ok=True)
    (DEST/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    (DEST/'SOURCE.md').write_text('Deterministic snapshot of every installed distribution matching the preregistered metadata and license thresholds. All listed Python files and packaged license texts were copied byte-for-byte; see manifest.json.\n')
    print(json.dumps({'snapshot':DEST.relative_to(ROOT).as_posix(),'eligible_projects':len(projects),
                      'python_files':sum(p['python_file_count'] for p in projects),
                      'license_files':sum(p['license_file_count'] for p in projects)},indent=2))
if __name__=='__main__':main()
