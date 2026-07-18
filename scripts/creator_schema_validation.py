#!/usr/bin/env python3
"""Schema 0.4.0 validation and cross-file consistency for Creator workspace state."""
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from typing import Any
try:
    from creator_state_store import STATE_FILES, StateStoreError, load_json, safe_path
    from json_schema_lite import JsonSchemaError, load_schema, validate as validate_json_schema
except ImportError:
    from scripts.creator_state_store import STATE_FILES, StateStoreError, load_json, safe_path
    from scripts.json_schema_lite import JsonSchemaError, load_schema, validate as validate_json_schema
ROOT=Path(__file__).resolve().parents[1]
SCHEMA_VERSION='0.4.0'
NAMES={p:Path(p).stem for p in STATE_FILES}
OWNERS={p:('creator-rule-router' if p=='.creator/rules.json' else 'creator-workspace-manager') for p in STATE_FILES}
PRIVACY={'.creator/workspace.json':'publishable_template','.creator/projects.json':'repository_workflow_state','.creator/entities.json':'private','.creator/state.json':'repository_workflow_state','.creator/session-insights.json':'private','.creator/operator.json':'private','.creator/backlog.json':'repository_workflow_state','.creator/surfaces.json':'publishable_template','.creator/decisions.json':'repository_workflow_state','.creator/rules.json':'repository_contract'}
SCHEMAS={p:f'schemas/workspace/{NAMES[p]}.schema.json' for p in STATE_FILES}
REGISTRY={p:{'surface_id':NAMES[p],'path':p,'schema':SCHEMAS[p],'owner_skill':OWNERS[p],'privacy_class':PRIVACY[p],'required':True,'mutable':True,'archive_policy':'retain'} for p in STATE_FILES}
ID_FIELDS={'.creator/projects.json':('projects','project_id'),'.creator/entities.json':('entities','entity_id'),'.creator/session-insights.json':('entries','insight_id'),'.creator/backlog.json':('items','item_id'),'.creator/decisions.json':('decisions','decision_id')}

def _time(v:Any)->bool:
    if not isinstance(v,str) or not v:return False
    try:datetime.fromisoformat(v.replace('Z','+00:00'));return True
    except ValueError:return False

def validate_values(root:Path,values:dict[str,dict[str,Any]],*,schema_root:Path|None=None)->list[str]:
    root=Path(root).resolve(); schema_root=(schema_root or ROOT).resolve(); findings=[]
    for relative in STATE_FILES:
        value=values.get(relative)
        if value is None: findings.append(f'missing state surface: {relative}'); continue
        try: findings.extend(f'{relative}: {x}' for x in validate_json_schema(value,load_schema(schema_root/SCHEMAS[relative])))
        except JsonSchemaError as exc: findings.append(str(exc))
        if value.get('owner_skill')!=OWNERS[relative]: findings.append(f'{relative}: owner_skill must be {OWNERS[relative]}')
        if value.get('privacy_class')!=PRIVACY[relative]: findings.append(f'{relative}: privacy_class must be {PRIVACY[relative]}')
        for field in ('created_at','updated_at'):
            if not _time(value.get(field)): findings.append(f'{relative}: {field} must be ISO-8601')
        spec=ID_FIELDS.get(relative)
        if spec:
            collection,id_field=spec; items=value.get(collection,[])
            ids=[i.get(id_field) for i in items if isinstance(i,dict) and isinstance(i.get(id_field),str)] if isinstance(items,list) else []
            if len(ids)!=len(set(ids)): findings.append(f'{relative}: duplicate {id_field}')
    surfaces=values.get('.creator/surfaces.json',{}).get('surfaces',[])
    by_path={i.get('path'):i for i in surfaces if isinstance(i,dict)} if isinstance(surfaces,list) else {}
    if set(by_path)!=set(STATE_FILES): findings.append('surface registry must declare exactly ten state surfaces')
    for p,e in REGISTRY.items():
        if by_path.get(p)!=e: findings.append(f'surface registry mismatch: {p}')
    workspace=values.get('.creator/workspace.json',{})
    for field in ('architecture_map','active_plan'):
        pointer=workspace.get(field)
        if pointer is None and field=='active_plan':continue
        if not isinstance(pointer,str):findings.append(f'workspace {field} must be a string or null');continue
        try:
            if not safe_path(root,pointer).is_file():findings.append(f'workspace {field} is missing: {pointer}')
        except StateStoreError as exc: findings.append(str(exc))
    projects=values.get('.creator/projects.json',{}).get('projects',[])
    pids={i.get('project_id') for i in projects if isinstance(i,dict) and isinstance(i.get('project_id'),str)} if isinstance(projects,list) else set()
    state=values.get('.creator/state.json',{})
    refs=set(i for key in ('active_projects','blocked_projects') for i in state.get(key,[]) if isinstance(i,str))
    unknown=sorted(refs-pids)
    if unknown: findings.append(f'unknown state project IDs: {unknown}')
    decisions=values.get('.creator/decisions.json',{}).get('decisions',[])
    dids={i.get('decision_id') for i in decisions if isinstance(i,dict) and isinstance(i.get('decision_id'),str)} if isinstance(decisions,list) else set()
    domains=values.get('.creator/rules.json',{}).get('domains',[])
    domain_ids=[];rule_ids=[];command_ids=[]
    for d in domains if isinstance(domains,list) else []:
        if not isinstance(d,dict):continue
        domain_ids.append(d.get('domain_id'))
        missing=sorted(set(i for i in d.get('decision_refs',[]) if isinstance(i,str))-dids)
        if missing:findings.append(f"domain {d.get('domain_id')} has unknown decision refs: {missing}")
        rule_ids.extend(i.get('rule_id') for i in d.get('rules',[]) if isinstance(i,dict))
        command_ids.extend(i.get('command_id') for i in d.get('commands',[]) if isinstance(i,dict))
    for label,ids in (('domain_id',domain_ids),('rule_id',rule_ids),('command_id',command_ids)):
        clean=[i for i in ids if isinstance(i,str)]
        if len(clean)!=len(set(clean)):findings.append(f'duplicate {label}')
    return sorted(set(findings))

def load_values(root:Path)->tuple[dict[str,bytes],dict[str,dict[str,Any]]]:
    root=Path(root).resolve();raw={};values={}
    for relative in STATE_FILES:
        path=safe_path(root,relative)
        if not path.is_file():raise StateStoreError(f'missing state file: {relative}')
        raw[relative]=path.read_bytes();values[relative]=load_json(path)
    return raw,values

def validate_workspace(root:Path,*,schema_root:Path|None=None)->list[str]:
    try:_,values=load_values(root)
    except StateStoreError as exc:return [str(exc)]
    return validate_values(root,values,schema_root=schema_root)
