#!/usr/bin/env python3
"""Validate the repository board and its offline HTML seed; no writes to user data."""
import json, re
from pathlib import Path
root=Path(__file__).resolve().parents[2]
board=json.loads((root/'21_alpha6/data/roadmap.json').read_text(encoding='utf-8'))
html=(root/'21_alpha6/dashboard.html').read_text(encoding='utf-8')
match=re.search(r'<script id="seed" type="application/json">([\s\S]*?)</script>',html)
assert match and json.loads(match.group(1))==board, "Embedded board seed differs from roadmap"
tasks=board['tasks']
ids={t['id'] for t in tasks}
assert len(ids)==len(tasks), "Duplicate task ID"
for task in tasks:
    assert task['status'] in board['statuses'], task['id']
    assert task['phase'] in board['phases'], task['id']
    assert task['priority'] in ('P0','P1','P2'), task['id']
    assert set(task['dependencies'])<=ids and task['id'] not in task['dependencies'], task['id']
    assert 'githubIssue' not in task or isinstance(task['githubIssue'],int) and task['githubIssue']>0,task['id']
print(f'Project Board seed and task references: PASS ({len(tasks)} tasks)')
