#!/usr/bin/env python3
"""Read-only GitHub snapshot from gh API pagination; never modifies roadmap/localStorage."""
import json, sys, datetime
from pathlib import Path
root=Path(__file__).resolve().parents[2]
board=json.loads((root/'21_alpha6/data/roadmap.json').read_text(encoding='utf-8'))
pages=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
issues={i['number']:i for page in pages for i in page if 'pull_request' not in i}
mapped={t['githubIssue'] for t in board['tasks'] if 'githubIssue' in t}
missing=sorted(mapped-issues.keys())
if missing: raise SystemExit(f'Mapped GitHub issues missing: {missing}')
snapshot={'schemaVersion':1,'repository':'disxlab/Taktera-Design-System','capturedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'issues':[{'number':n,'state':issues[n]['state'],'title':issues[n]['title'],'updatedAt':issues[n]['updated_at']} for n in sorted(mapped)],'taskLinks':[{'id':t['id'],'number':t['githubIssue'],'boardStatus':t['status'],'issueState':issues[t['githubIssue']]['state']} for t in board['tasks'] if 'githubIssue' in t]}
Path(sys.argv[2]).write_text(json.dumps(snapshot,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f"GitHub snapshot: {len(mapped)} issues, {len(snapshot['taskLinks'])} task links; local task status not changed")
