from pathlib import Path
import hashlib,json
B=Path(__file__).resolve().parents[1];root=B.parent;results=[]
for inv in sorted((B/'evidence').glob('*-inventory.json')):
 data=json.loads(inv.read_text());repo=root/Path(data['source_repo']).name
 actual={}
 for p in repo.rglob('*'):
  if p.is_file() and not any(x in p.relative_to(repo).parts for x in ['node_modules','.git']):actual[str(p.relative_to(repo))]=hashlib.sha256(p.read_bytes()).hexdigest()
 expected=data['artifact_hashes'];changed=[p for p in expected if actual.get(p)!=expected[p]];added=sorted(set(actual)-set(expected))
 results.append({'repo':repo.name,'unchanged':not changed and not added,'changed_or_removed':changed,'added':added,'scope':'All original files including existing dist and test results, excluding node_modules and .git internals.'})
(B/'validation/original-integrity.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
assert all(x['unchanged'] for x in results)
