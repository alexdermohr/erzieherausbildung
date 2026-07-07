#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
schema = json.loads((root / 'schemas' / 'detail-backlog.v1.schema.json').read_text(encoding='utf-8'))
backlog = json.loads((root / 'data' / 'details' / 'backlog.v1.json').read_text(encoding='utf-8'))
learning = json.loads((root / 'data' / 'learning-map.v1.json').read_text(encoding='utf-8'))
detail_index = json.loads((root / 'data' / 'details' / 'index.v1.json').read_text(encoding='utf-8'))
excerpts = []
for path in sorted((root / 'data' / 'excerpts').glob('*.jsonl')):
    for line in path.read_text(encoding='utf-8').splitlines():
        if line.strip():
            excerpts.append(json.loads(line))

REQ = set(schema['required'])
ENTRY_REQ = set(schema['entryRequired'])
PRIORITIES = set(schema['priorities'])
STATUSES = set(schema['statuses'])
BLOCKED_UNTIL = set(schema['blockedUntilValues'])
BLOCKED_FIELDS = set(schema['blockedFields'])
ID = re.compile(r'^[a-z0-9][a-z0-9-]*$')

topic_by_id = {topic['id']: topic for axis in learning['axes'] for topic in axis['topics']}
axis_by_id = {axis['id']: axis for axis in learning['axes']}
detailed_topics = {topic for entry in detail_index['details'] for topic in entry['topicIds']}
missing_topics = sorted(set(topic_by_id) - detailed_topics)
excerpt_ids = {item['id'] for item in excerpts}
question_ids = {item['id'] for item in excerpts if item.get('claimType') == 'question'}
excerpted_ids = {item['id'] for item in excerpts if item.get('claimType') == 'excerpted'}


def nonempty_string(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def string_list(value) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) and item.strip() for item in value)


problems: list[str] = []
if backlog.get('schema') != schema['dataSchema']:
    problems.append('bad backlog schema')
missing = REQ - set(backlog)
if missing:
    problems.append(f'missing backlog fields {sorted(missing)}')
blocked = BLOCKED_FIELDS & set(backlog)
if blocked:
    problems.append(f'blocked top-level fields {sorted(blocked)}')
if set(backlog.get('blockedFields', [])) != BLOCKED_FIELDS:
    problems.append('backlog blockedFields must match schema')
coverage = backlog.get('coverageSnapshot', {})
for key in ['topicCount', 'detailedTopicCount', 'missingTopicCount', 'detailCoverageRatio']:
    if coverage.get(key) != detail_index['coverage'].get(key):
        problems.append(f'coverageSnapshot mismatch {key}')
entries = backlog.get('entries')
if not isinstance(entries, list) or not entries:
    problems.append('entries must be non-empty list')
else:
    seen = set()
    topic_ids = []
    for entry in entries:
        missing_entry = ENTRY_REQ - set(entry)
        if missing_entry:
            problems.append(f"{entry.get('id', '<unknown>')}: missing {sorted(missing_entry)}")
        blocked_entry = BLOCKED_FIELDS & set(entry)
        if blocked_entry:
            problems.append(f"{entry.get('id', '<unknown>')}: blocked fields {sorted(blocked_entry)}")
        if not nonempty_string(entry.get('id')) or not ID.match(entry.get('id', '')):
            problems.append(f"{entry.get('id', '<unknown>')}: bad id")
        if entry.get('id') in seen:
            problems.append(f"duplicate id {entry.get('id')}")
        seen.add(entry.get('id'))
        topic_id = entry.get('topicId')
        topic_ids.append(topic_id)
        if topic_id not in topic_by_id:
            problems.append(f"{entry.get('id')}: unknown topicId {topic_id}")
            continue
        topic = topic_by_id[topic_id]
        if topic_id in detailed_topics:
            problems.append(f"{entry.get('id')}: detailed topic must not be in backlog")
        if entry.get('title') != topic['title']:
            problems.append(f"{entry.get('id')}: title mismatch")
        if entry.get('axisId') not in axis_by_id:
            problems.append(f"{entry.get('id')}: unknown axisId")
        if not string_list(entry.get('sourceRefs')):
            problems.append(f"{entry.get('id')}: sourceRefs must be string list")
        elif sorted(entry['sourceRefs']) != sorted(topic.get('sources', [])):
            problems.append(f"{entry.get('id')}: sourceRefs mismatch topic sources")
        if not string_list(entry.get('relatedExcerptRefs')) and entry.get('relatedExcerptRefs') != []:
            problems.append(f"{entry.get('id')}: relatedExcerptRefs must be string list")
        for ref in entry.get('relatedExcerptRefs', []):
            if ref not in excerpt_ids:
                problems.append(f"{entry.get('id')}: unknown relatedExcerptRef {ref}")
        if entry.get('priority') not in PRIORITIES:
            problems.append(f"{entry.get('id')}: bad priority")
        if entry.get('status') not in STATUSES:
            problems.append(f"{entry.get('id')}: bad status")
        if entry.get('blockedUntil') not in BLOCKED_UNTIL:
            problems.append(f"{entry.get('id')}: bad blockedUntil")
        refs = set(entry.get('relatedExcerptRefs', []))
        if refs & question_ids and entry.get('status') != 'needs-source-location':
            problems.append(f"{entry.get('id')}: question refs require needs-source-location")
        if refs & excerpted_ids and not refs & question_ids and entry.get('status') != 'needs-own-excerpt':
            problems.append(f"{entry.get('id')}: excerpted refs require needs-own-excerpt")
    if sorted(topic_ids) != missing_topics:
        problems.append('backlog topicIds must equal current missing detail topics')

if problems:
    print('\n'.join(problems))
    raise SystemExit(1)
print('detail backlog validation passed')
