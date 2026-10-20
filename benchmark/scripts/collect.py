#!/usr/bin/env python3
"""Recover benchmark evidence without writing into the original projects."""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, shutil, subprocess, collections, re
ROOT=Path(__file__).resolve().parents[2]
B=ROOT/'benchmark'
MODELS=[('sonnet-5','sonnet5-runner','Sonnet 5'),('sonnet-5.5','sonnet55-runner','Sonnet 5.5'),('opus-5','opus5-runner','Opus 5'),('opus-5.5','opus55-runner','Opus 5.5')]
EXCLUDE={'node_modules','.git','dist','test-results','playwright-report','.DS_Store'}
CODE={'.ts','.js','.mjs','.css','.html','.svg'}
def dump(p,v):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')
def stamp(s):return datetime.fromisoformat(s.replace('Z','+00:00'))
results=[]
for key,folder,label in MODELS:
 repo=ROOT/folder
 logs=list((Path.home()/'.claude/projects'/('-'+str(repo).strip('/').replace('/','-'))).glob('*.jsonl'))
 assert len(logs)==1,(folder,logs)
 log=logs[0];rows=[(i+1,json.loads(l)) for i,l in enumerate(log.open())]
 assistants=[(i,r) for i,r in rows if r.get('type')=='assistant']
 byid={}
 for i,r in assistants:byid.setdefault(r['message']['id'],[]).append((i,r))
 usage=[]
 for mid,g in byid.items():
  i,r=g[-1];u=r['message'].get('usage')
  assert all(x['message'].get('usage')==u for _,x in g),'inconsistent stream usage'
  if u:usage.append({'message_id':mid,'request_id':r.get('requestId'),'source_lines':[i for i,_ in g],'timestamp':r.get('timestamp'),'raw_usage':u})
 totals={k:sum(x['raw_usage'].get(k,0) for x in usage) for k in ['input_tokens','output_tokens','cache_creation_input_tokens','cache_read_input_tokens']}
 totals['cached_tokens']=totals['cache_read_input_tokens']
 totals['input_tokens_including_cache']=totals['input_tokens']+totals['cache_creation_input_tokens']+totals['cache_read_input_tokens']
 totals['total_tokens']=totals['input_tokens_including_cache']+totals['output_tokens']
 userline,user=next((i,r) for i,r in rows if r.get('type')=='user' and isinstance(r.get('message',{}).get('content'),str))
 raw_prompt=user['message']['content'];prompt=re.sub(r'<\/?pasted_content[^>]*>','',raw_prompt).strip()
 endline,end=assistants[-1];start=user['timestamp'];finish=end['timestamp']
 efforts=sorted(set(r.get('effort') for _,r in assistants if r.get('effort') is not None))
 perturn=sorted(set(r.get('perTurnEffort') for _,r in assistants if r.get('perTurnEffort') is not None))
 files=[];fullbytes=0;fullcount=0;srcbytes=0;source_loc=0;test_loc=0;code_loc=0
 fullhash={}
 for f in sorted(repo.rglob('*')):
  if not f.is_file():continue
  rel=str(f.relative_to(repo));n=f.stat().st_size;fullbytes+=n;fullcount+=1
  # Hash artifact content, excluding dependencies and Git internals, including existing generated outputs.
  if not any(x in f.relative_to(repo).parts for x in ['node_modules','.git']):fullhash[rel]=hashlib.sha256(f.read_bytes()).hexdigest()
  if any(x in f.relative_to(repo).parts for x in EXCLUDE):continue
  data=f.read_bytes();lines=len(data.splitlines()) if f.suffix in CODE else None
  files.append({'path':rel,'bytes':n,'sha256':hashlib.sha256(data).hexdigest(),'loc':lines})
  srcbytes+=n
  if lines is not None:
   code_loc+=lines
   if f.relative_to(repo).parts[0] in ['tests','test']:test_loc+=lines
   elif rel.startswith('src/') or rel in ['index.html','style.css']:source_loc+=lines
 pkg=json.loads((repo/'package.json').read_text())
 git={}
 for name,args in {'status':['status','--short'],'commits':['log','--all','--format=%H|%aI|%cI|%s'],'tracked':['ls-files']}.items():
  c=subprocess.run(['git','-C',str(repo),*args],capture_output=True,text=True);git[name]={'exit_code':c.returncode,'stdout':c.stdout,'stderr':c.stderr}
 # Direct Write/Edit tool calls, deduplicated by tool-use id; Bash mutation count cannot be fully recovered.
 calls={}
 for i,r in assistants:
  for c in r['message'].get('content',[]):
   if isinstance(c,dict) and c.get('type')=='tool_use':calls[c['id']]={'source_line':i,'name':c['name'],'input':c.get('input',{})}
 direct_files=sorted(set(x['input']['file_path'] for x in calls.values() if x['name'] in ['Write','Edit'] and 'file_path' in x['input']))
 recovery={'source_log':str(log),'source_log_sha256':hashlib.sha256(log.read_bytes()).hexdigest(),'model_evidence':[{'line':i,'model':r['message']['model'],'effort':r.get('effort'),'perTurnEffort':r.get('perTurnEffort')} for i,r in assistants], 'prompt':{'line':userline,'raw':raw_prompt,'normalized':prompt},'timing':{'start_line':userline,'end_line':endline,'start':start,'end':finish,'definition':'First human user prompt to final assistant message; includes setup, implementation, tests and final response. Excludes stop hooks.'},'usage_records':usage,'token_totals':totals,'assistant_rows':len(assistants),'unique_message_ids':len(byid),'usage_consistent_within_messages':True,'tool_names':dict(collections.Counter(x['name'] for x in calls.values())),'direct_write_edit_paths':direct_files,'git':git}
 dump(B/'evidence'/f'{key}-session.json',recovery)
 dump(B/'evidence'/f'{key}-inventory.json',{'source_repo':str(repo),'files':files,'artifact_hashes':fullhash,'full_repo_logical_bytes':fullbytes,'full_repo_file_count':fullcount})
 for n in ['README.md','BUILD_LOG.md','BUILD_STATS.md','scripts/build-meta.json','package.json','package-lock.json']:
  f=repo/n
  if f.exists():out=B/'evidence'/key/n;out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,out)
 target=B/'validation/workspaces'/folder
 if target.exists():raise RuntimeError(f'Workspace already exists: {target}')
 shutil.copytree(repo,target,ignore=lambda d,n:[x for x in n if x in EXCLUDE])
 lock=json.loads((repo/'package-lock.json').read_text()) if (repo/'package-lock.json').exists() else {}
 deps={'runtime':pkg.get('dependencies',{}),'development':pkg.get('devDependencies',{}),'locked_direct_versions':{n:lock.get('packages',{}).get('node_modules/'+n,{}).get('version','unavailable') for n in {**pkg.get('dependencies',{}),**pkg.get('devDependencies',{})}},'scripts':pkg['scripts']}
 result={'id':key,'model':label,'model_id':sorted(set(r['message']['model'] for _,r in assistants))[0],'repo':folder,'reasoning_effort':efforts[0] if len(efforts)==1 else efforts,'per_turn_effort_raw':perturn or 'unavailable','original_prompt':prompt,'run':{'start_timestamp':start,'end_timestamp':finish,'wall_clock_build_seconds':(stamp(finish)-stamp(start)).total_seconds(),'scope':'observed session: first user prompt to final assistant response','queue_start_timestamp':next(r['timestamp'] for _,r in rows if r.get('type')=='queue-operation'),'stop_hook_timestamp':next((r['timestamp'] for _,r in reversed(rows) if r.get('type')=='system'),'unavailable')},'tokens':totals,'files':{'artifact_file_count':len(files),'files_created_during_run':'unavailable','files_changed_during_run':'unavailable','direct_write_edit_unique_paths':len(direct_files),'loc_production':source_loc,'loc_tests':test_loc,'loc_code_and_config':code_loc,'size_source_bytes':srcbytes,'size_repo_logical_bytes':fullbytes,'full_repo_file_count':fullcount},'dependencies':deps,'validation':{},'implementation':{},'quality_review':{k:{'manual_rating':None,'manual_notes':None,'reviewer':None,'evidence':[]} for k in ['prompt_compliance','feature_completeness','controls_gameplay_correctness','visual_polish','ui_completeness','bugs','crashes','responsiveness','implementation_defects']},'sources':{'session':f'evidence/{key}-session.json','inventory':f'evidence/{key}-inventory.json','package':f'{folder}/package.json'},'unavailable':['Exact files created/changed across original run (no committed baseline; Bash writes not fully enumerated)','Original release-ready instant independent of session endpoint','Model training/version equivalence and original hardware load']}
 results.append(result)
 print(label,result['run']['wall_clock_build_seconds'],totals,'LOC',source_loc,'FILES',len(files),'effort',efforts)
assert len(set(x['original_prompt'] for x in results))==1,'prompts differ'
(B/'evidence/original-prompt.txt').write_text(results[0]['original_prompt']+'\n')
dump(B/'benchmark-summary.json',{'schema_version':'1.0.0','collected_at_utc':datetime.now(timezone.utc).isoformat(),'benchmark_date_local':'2026-10-01','models':results,'quality_review_scale':None,'overall_quality_score':None})
