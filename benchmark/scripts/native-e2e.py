from pathlib import Path
from datetime import datetime,timezone
import json,subprocess,time,os
B=Path(__file__).resolve().parents[1]
for key,folder in [('sonnet-5.5','sonnet55-runner'),('opus-5.5','opus55-runner')]:
 p=B/'validation/workspaces'/folder;out=B/'validation'/key;t=time.perf_counter()
 start=datetime.now(timezone.utc).isoformat()
 try:r=subprocess.run(['npm','run','test:e2e','--','--workers=1'],cwd=p,capture_output=True,text=True,timeout=500);text=r.stdout+r.stderr;code=r.returncode
 except subprocess.TimeoutExpired as e:text=(e.stdout.decode(errors='replace') if isinstance(e.stdout,bytes) else (e.stdout or ''))+(e.stderr.decode(errors='replace') if isinstance(e.stderr,bytes) else (e.stderr or ''))+'\n'+str(e);code=124
 (out/'e2e.log').write_text(text)
 (out/'e2e.json').write_text(json.dumps({'status':'passed' if code==0 else 'failed','command':['npm','run','test:e2e','--','--workers=1'],'started_at_utc':start,'elapsed_seconds':round(time.perf_counter()-t,3),'exit_code':code,'log':f'validation/{key}/e2e.log'},indent=2)+'\n')
 print(key,code,text[-2400:],flush=True)
