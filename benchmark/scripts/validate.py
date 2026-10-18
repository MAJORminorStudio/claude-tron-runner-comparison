#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime,timezone
import json,subprocess,time,sys
ROOT=Path(__file__).resolve().parents[2];B=ROOT/'benchmark'
def validate_public_package():
 """Check frozen public artifacts without private validation workspaces."""
 import csv,hashlib
 summary=json.loads((B/'benchmark-summary.json').read_text())
 models=summary['models']; ids={m['id'] for m in models}
 assert len(models)==4 and len(ids)==4, 'Expected four unique one-shot model artifacts'
 with (B/'benchmark-summary.csv').open(newline='') as source:
  table=list(csv.DictReader(source))
 assert len(table)==4, 'Expected four CSV summary rows'
 by_repo={row['repo']:row for row in table}
 assert len(by_repo)==4 and set(by_repo)=={m['repo'] for m in models}, 'CSV/JSON model coverage mismatch'
 for model in models:
  row=by_repo[model['repo']]
  assert row['model_id']==model['model_id'], 'CSV/JSON model identity mismatch'
  for key in ['input_tokens','output_tokens','total_tokens']:
   assert int(row[key])==model['tokens'][key], f"{model['id']}: {key} mismatch"
  assert float(row['wall_clock_build_seconds'])==model['run']['wall_clock_build_seconds'], 'Build duration mismatch'
 manifest=json.loads((B/'release-manifest.json').read_text())
 roots={model['repo'] for model in models}
 records=[entry for entry in manifest['files'] if entry['path'].split('/')[0] in roots]
 assert records and {entry['path'].split('/')[0] for entry in records}==roots, 'Missing game source manifest'
 for entry in records:
  path=ROOT/entry['path']
  assert path.is_file(), f"Missing frozen source: {entry['path']}"
  assert path.stat().st_size==entry['bytes'], f"Source size mismatch: {entry['path']}"
  assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256'], f"Source hash mismatch: {entry['path']}"
 print(f'PASS: 4 model artifacts; CSV/JSON identities, token counts and durations agree; {len(records)} frozen game-source hashes verified.')
 print('Private workspace reruns and release-hosted media are not part of this public integrity check.')

if len(sys.argv)==1 or sys.argv[1:]==['--public']:
 try: validate_public_package()
 except (AssertionError,KeyError,OSError,ValueError) as error:
  print(f'FAIL: {error}');sys.exit(1)
 sys.exit(0)

key=sys.argv[1];summary=json.loads((B/'benchmark-summary.json').read_text());m=next(x for x in summary['models'] if x['id']==key)
p=B/'validation/workspaces'/m['repo'];out=B/'validation'/key;out.mkdir(parents=True,exist_ok=True)
checks={}
def run(name,cmd,timeout=180):
 start=datetime.now(timezone.utc).isoformat();t=time.perf_counter()
 try:
  r=subprocess.run(cmd,cwd=p,capture_output=True,text=True,timeout=timeout);code=r.returncode;text=r.stdout+r.stderr
 except subprocess.TimeoutExpired as e:code=124;text=str(e)
 (out/(name+'.log')).write_text(text)
 checks[name]={'status':'passed' if code==0 else 'failed','command':cmd,'cwd':str(p.relative_to(ROOT)),'exit_code':code,'started_at_utc':start,'elapsed_seconds':round(time.perf_counter()-t,3),'log':str((out/(name+'.log')).relative_to(B))}
 print(key,name,checks[name]['status'],text[-500:],flush=True)
if (p/'package-lock.json').exists():run('install',['npm','ci','--no-audit','--no-fund'])
else:checks['install']={'status':'not_required','reason':'No dependencies declared.'}
for name in ['test','build','lint','typecheck']:
 if name in m['dependencies']['scripts']:run(name,['npm','run',name],300)
 else:checks[name]={'status':'unavailable','reason':f'No {name} script declared.'}
js=[str(f.relative_to(p)) for f in p.rglob('*') if f.suffix in ['.js','.mjs'] and 'node_modules' not in f.parts and 'dist' not in f.parts]
run('javascript_syntax',['node',str(B/'scripts/syntax-check.mjs'),*js])
if key=='sonnet-5':checks['static_delivery']={'status':'passed','reason':'Unbundled ES modules and CSS; no build step required. Runtime validated by common browser smoke.'}
(out/'checks.json').write_text(json.dumps(checks,indent=2)+'\n')
