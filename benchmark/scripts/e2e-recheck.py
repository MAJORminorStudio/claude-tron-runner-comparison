"""Preserve first attempt and run an isolated, streamed native-suite verification."""
from pathlib import Path
from datetime import datetime,timezone
import json,subprocess,time,os,signal,shutil,sys
B=Path(__file__).resolve().parents[1]
key=sys.argv[1];folder={'sonnet-5.5':'sonnet55-runner','opus-5.5':'opus55-runner'}[key]
p=B/'validation/workspaces'/folder;out=B/'validation'/key
for name in ['e2e.json','e2e.log']:
 if (out/name).exists():shutil.copy2(out/name,out/name.replace('e2e.','e2e-attempt-1.'))
if (p/'test-results').exists():shutil.copytree(p/'test-results',out/'e2e-attempt-1-artifacts',dirs_exist_ok=True)
start=datetime.now(timezone.utc).isoformat();t=time.perf_counter();cmd=['npm','run','test:e2e','--','--workers=1']
with (out/'e2e-recheck.log').open('w') as f:
 proc=subprocess.Popen(cmd,cwd=p,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
 try:code=proc.wait(timeout=1200)
 except subprocess.TimeoutExpired:
  os.killpg(proc.pid,signal.SIGTERM);code=124;f.write('\nBenchmark timeout after 1200s; no project changes.\n');proc.wait()
result={'status':'passed' if code==0 else ('incomplete' if code==124 else 'failed'),'command':cmd,'started_at_utc':start,'elapsed_seconds':round(time.perf_counter()-t,3),'exit_code':code,'log':f'validation/{key}/e2e-recheck.log','reason':'Isolated rerun after concurrent browser checks finished. First attempt preserved.'}
(out/'e2e-recheck.json').write_text(json.dumps(result,indent=2)+'\n')
if (p/'test-results').exists():shutil.copytree(p/'test-results',out/'e2e-recheck-artifacts',dirs_exist_ok=True)
print(json.dumps(result),flush=True)
