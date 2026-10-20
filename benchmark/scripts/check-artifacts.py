from pathlib import Path
import json,csv,platform,subprocess
B=Path(__file__).resolve().parents[1]
s=json.loads((B/'benchmark-summary.json').read_text());models=s['models'];checks={}
assert len(models)==4
assert len(set(m['original_prompt'] for m in models))==1
assert all(m['reasoning_effort']=='high' for m in models)
assert all(set(m)==set(models[0]) for m in models)
for m in models:
 t=m['tokens'];assert t['cached_tokens']==t['cache_read_input_tokens'];assert t['input_tokens_including_cache']==t['input_tokens']+t['cache_creation_input_tokens']+t['cache_read_input_tokens'];assert t['total_tokens']==t['input_tokens_including_cache']+t['output_tokens']
 for d in m['quality_review'].values():assert d['manual_rating'] is None and d['manual_notes'] is None and d['reviewer'] is None and d['evidence']==[]
 assert (B/'repo-analysis'/f'{m["id"]}.md').exists()
 assert (B/m['sources']['session']).exists() and (B/m['sources']['inventory']).exists()
 checks[m['id']]={'tokens_arithmetic':'passed','schema_fields_consistent':'passed','manual_reviews_empty':'passed','sources_present':'passed'}
with (B/'benchmark-summary.csv').open() as f:rows=list(csv.DictReader(f))
assert len(rows)==4
for row,m in zip(rows,models):assert int(row['total_tokens'])==m['tokens']['total_tokens'] and row['repo']==m['repo']
manifest=json.loads((B/'video/manifest.json').read_text());assert {c['id'] for c in manifest['clips']}=={m['id'] for m in models}
assert not list((B/'video/gameplay').glob('*.mp4')),'Unexpected gameplay media: no fabricated clips are allowed'
for name in ['README.md','methodology.md','quality-review-schema.json','video/remotion/package-lock.json']:assert (B/name).exists()
json.loads((B/'quality-review-schema.json').read_text())
(B/'validation/benchmark-artifacts.json').write_text(json.dumps({'checks':checks,'csv_json_consistent':True,'real_gameplay_files_supplied':False,'requested_reports_present':True},indent=2)+'\n')
versions={}
for name,cmd in {'node':['node','--version'],'npm':['npm','--version'],'ffprobe':['ffprobe','-version'],'ffmpeg':['ffmpeg','-version']}.items():versions[name]=subprocess.run(cmd,capture_output=True,text=True).stdout.splitlines()[0]
(B/'validation/environment.json').write_text(json.dumps({'platform':platform.platform(),'machine':platform.machine(),'versions':versions,'common_browser':'Google Chrome 154.0.8037.59, installed application','common_browser_args':['--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'],'performance_ranking_performed':False},indent=2)+'\n')
print('Artifact consistency checks passed; original gameplay MP4s are correctly absent.')
