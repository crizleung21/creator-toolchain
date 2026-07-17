#!/usr/bin/env python3
"""Transactional Creator Toolchain migration from state schema 0.3.0 to 0.4.0."""
from __future__ import annotations
import argparse, hashlib, json, os, shutil, stat, sys, tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
try:
    from creator_state_store import StateStoreError,load_json,safe_path
    from creator_schema_validation import STATE_FILES,REGISTRY as SURFACE_REGISTRY,validate_workspace,validate_values as validate_workspace_values
    from creator_transactions import atomic_write_bytes,atomic_write_json
except ImportError:
    from scripts.creator_state_store import StateStoreError,load_json,safe_path
    from scripts.creator_schema_validation import STATE_FILES,REGISTRY as SURFACE_REGISTRY,validate_workspace,validate_values as validate_workspace_values
    from scripts.creator_transactions import atomic_write_bytes,atomic_write_json
SOURCE_SCHEMA="0.3.0"; TARGET_SCHEMA="0.4.0"
PRIVACY_MAP={"local_private":"private","local/private":"repository_workflow_state"}
class MigrationError(RuntimeError): pass

def _now()->str: return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
def _sha(data:bytes)->str: return hashlib.sha256(data).hexdigest()
def _json_bytes(value:Any)->bytes: return (json.dumps(value,indent=2,ensure_ascii=False,sort_keys=True)+"\n").encode()

def _domain_scope(domain_id:str)->str:
    if domain_id=="GLOBAL": return "workspace-wide safety and integrity"
    if domain_id=="creator-toolchain": return "creator-toolchain repository, skill, plugin, package, and validation work"
    return f"{domain_id} domain rules"

def migrate_value(relative:str,value:dict[str,Any],*,timestamp:str)->dict[str,Any]:
    if value.get("schema_version")!=SOURCE_SCHEMA: raise MigrationError(f"{relative}: expected schema {SOURCE_SCHEMA}")
    migrated=json.loads(json.dumps(value)); migrated["schema_version"]=TARGET_SCHEMA
    migrated["privacy_class"]=PRIVACY_MAP.get(migrated.get("privacy_class"),migrated.get("privacy_class"))
    migrated.setdefault("created_at",timestamp); migrated["updated_at"]=timestamp
    if relative==".creator/surfaces.json":
        current={i.get("path"):i for i in migrated.get("surfaces",[]) if isinstance(i,dict)}
        migrated["surfaces"]=[]
        for path in STATE_FILES:
            record=dict(SURFACE_REGISTRY[path]); old=current.get(path,{})
            if isinstance(old,dict) and old.get("surface_id"): record["surface_id"]=old["surface_id"]
            migrated["surfaces"].append(record)
    elif relative==".creator/rules.json":
        domains=[]
        for domain in migrated.get("domains",[]):
            if not isinstance(domain,dict): continue
            item=dict(domain); did=str(item.get("domain_id","domain"))
            item.setdefault("scope",_domain_scope(did)); item.setdefault("owner","creator-rule-router"); item["updated_at"]=timestamp
            domains.append(item)
        migrated["domains"]=domains
    elif relative==".creator/state.json":
        migrated["last_health_check"]=timestamp
        divergence=migrated.get("state_divergence")
        if not isinstance(divergence,dict): divergence={}
        divergence.update({"score":0,"level":"green","notes":"Repository state migrated to schema 0.4.0 and validated."})
        migrated["state_divergence"]=divergence
    return migrated

def load_source_values(root:Path)->tuple[dict[str,bytes],dict[str,dict[str,Any]]]:
    root=Path(root).resolve(); raw={}; values={}
    for relative in STATE_FILES:
        path=safe_path(root,relative)
        if not path.is_file(): raise MigrationError(f"missing state file: {relative}")
        data=path.read_bytes(); raw[relative]=data
        try: value=json.loads(data)
        except json.JSONDecodeError as exc: raise MigrationError(f"{relative}: invalid JSON: {exc}") from exc
        if not isinstance(value,dict): raise MigrationError(f"{relative}: root must be an object")
        values[relative]=value
    return raw,values

def transform_workspace(root:Path,*,timestamp:str)->tuple[dict[str,bytes],dict[str,dict[str,Any]]]:
    raw,values=load_source_values(root)
    migrated={relative:migrate_value(relative,values[relative],timestamp=timestamp) for relative in STATE_FILES}
    errors=validate_workspace_values(Path(root),migrated)
    if errors: raise MigrationError("pre-commit validation failed: "+"; ".join(errors))
    return raw,migrated

def build_migration_plan(root:Path,*,timestamp:str|None=None)->dict[str,Any]:
    timestamp=timestamp or _now(); raw,migrated=transform_workspace(root,timestamp=timestamp)
    files=[]
    for relative in STATE_FILES:
        before=json.loads(raw[relative]); after=migrated[relative]
        files.append({"path":relative,"source_sha256":_sha(raw[relative]),"target_sha256":_sha(_json_bytes(after)),"changed_fields":sorted(k for k in set(before)|set(after) if before.get(k)!=after.get(k))})
    return {"schema_version":"1.0.0","source_schema":SOURCE_SCHEMA,"target_schema":TARGET_SCHEMA,"generated_at":timestamp,"write_enabled":True,"files":files}

def write_backup(root:Path,destination:Path)->dict[str,Any]:
    root=Path(root).resolve(); destination=Path(destination).resolve()
    if destination.exists(): raise MigrationError(f"backup destination already exists: {destination}")
    destination.mkdir(parents=True)
    records=[]
    for relative in STATE_FILES:
        source=safe_path(root,relative); data=source.read_bytes(); target=destination/Path(relative).name
        target.write_bytes(data); os.chmod(target,stat.S_IMODE(source.stat().st_mode))
        records.append({"path":relative,"backup_file":target.name,"sha256":_sha(data),"mode":stat.S_IMODE(source.stat().st_mode)})
    manifest={"schema_version":"1.0.0","source_schema":SOURCE_SCHEMA,"created_at":_now(),"files":records}
    (destination/"manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return manifest

def restore_backup(root:Path,backup:Path)->None:
    root=Path(root).resolve(); backup=Path(backup).resolve()
    manifest=load_json(backup/"manifest.json")
    records=manifest.get("files",[])
    if not isinstance(records,list) or len(records)!=len(STATE_FILES): raise MigrationError("backup manifest does not cover all state files")
    expected={i.get("path") for i in records if isinstance(i,dict)}
    if expected!=set(STATE_FILES): raise MigrationError("backup manifest path set is invalid")
    for record in records:
        relative=record["path"]; source=backup/record["backup_file"]; data=source.read_bytes()
        if _sha(data)!=record["sha256"]: raise MigrationError(f"backup checksum mismatch: {relative}")
    for record in records:
        relative=record["path"]; data=(backup/record["backup_file"]).read_bytes()
        atomic_write_bytes(safe_path(root,relative),data,mode=int(record.get("mode",0o600)))
    for record in records:
        data=safe_path(root,record["path"]).read_bytes()
        if _sha(data)!=record["sha256"]: raise MigrationError(f"byte-equivalent rollback failed: {record['path']}")

def migrate_workspace(root:Path,backup:Path,*,timestamp:str|None=None,fail_after:int|None=None)->dict[str,Any]:
    root=Path(root).resolve(); timestamp=timestamp or _now(); raw,migrated=transform_workspace(root,timestamp=timestamp)
    manifest=write_backup(root,backup); written=0
    try:
        for relative in STATE_FILES:
            atomic_write_json(safe_path(root,relative),migrated[relative],mode=0o600)
            written+=1
            if fail_after is not None and written>=fail_after* raise MigrationError(f"injected failure after {written} writes")
        errors=validate_workspace(root)
        if errors: raise MigrationError("post-write validation failed: "+"; ".join(errors))
    except Exception:
        restore_backup(root,backup)
        raise
    report=build_migration_plan_from_bytes(raw,migrated,timestamp=timestamp)
    report.update({"backup":str(Path(backup).resolve()),"backup_manifest_sha256":_sha((Path(backup)/"manifest.json").read_bytes()),"status":"PASS"})
    return report

def build_migration_plan_from_bytes(raw:dict[str,bytes],migrated:dict[str,dict[str,Any]],*,timestamp:str)->dict[str,Any]:
    files=[]
    for relative in STATE_FILES:
        before=json.loads(raw[relative]); after=migrated[relative]
        files.append({"path":relative,"source_sha256":_sha(raw[relative]),"target_sha256":_sha(_json_bytes(after)),"changed_fields":sorted(k for k in set(before)|set(after) if before.get(k)!=after.get(k))})
    return {"schema_version":"1.0.0","source_schema":SOURCE_SCHEMA,"target_schema":TARGET_SCHEMA,"generated_at":timestamp,"write_enabled":True,"files":files}

def _args(argv=None):
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--root",type=Path,default=Path.cwd()); p.add_argument("--plan",type=Path); p.add_argument("--backup",type=Path); p.add_argument("--write",action="store_true"); p.add_argument("--rollback",type=Path); p.add_argument("--timestamp"); return p.parse_args(argv)
def main(argv=None)->int:
    a=_args(argv)
    try:
        if a.rollback: restore_backup(a.root,a.rollback); print("Creator state rollback completed with byte-equivalent verification."); return 0
        if a.write:
            if not a.backup: raise MigrationError("--write requires --backup")
            report=migrate_workspace(a.root,a.backup,timestamp=a.timestamp)
        else: report=build_migration_plan(a.root,timestamp=a.timestamp)
        text=json.dumps(report,indent=2,ensure_ascii=False,sort_keys=True)+"\n"
        if a.plan: a.plan.parent.mkdir(parents=True,exist_ok=True); a.plan.write_text(text,encoding="utf-8")
        else: print(text,end="")
    except (MigrationError,StateStoreError,OSError) as exc:
        print(f"Migration failed: {exc}",file=sys.stderr); return 1
    return 0
if __name__=="__main__": raise SystemExit(main())
