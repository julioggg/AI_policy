#!/usr/bin/env python3
"""Phase33: integrity and readiness audit of returned 324-case PRIVATE adjudication.

No automated human decisions, no classifier accuracy, no full-text verification.
Checks the immutable original Phase32 casebook, the returned panel responses,
the frozen Phase30 codebook and original 1200-record provenance warning.
Only aggregate counts can be published, and only once 324 complete rows exist.

This stage does not transform a panel informed by A/B into independent rating.
Original A/B scores are frozen in Phase32; source evidence and article IDs
remain private. To claim completed full text, an independent private evidence
log with actual consulted full text must additionally be audited in a later
phase. Do NOT claim full text was consulted just because the flag is "yes".
"""
from __future__ import annotations

import argparse
from collections import Counter
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path

ALLOWED_SCOPE={"0","1","9"}
ALLOWED_RELEVANCE={"0","1","2","3","9"}
ALLOWED_TOPIC={"teaching_learning","assessment","ethics_integrity",
               "governance_policy","research_scholarship","ai_literacy_training",
               "equity_access","privacy_security","general_policy",
               "not_applicable","uncertain"}
ALLOWED_DISCIPLINE={"ssh","engineering","health_sciences","general_he","uncertain"}
ALLOWED_FULLTEXT={"yes","no"}
EDITOR_COLUMNS={22,23,24,25,26,27}
N=324

def load_module(filename,name):
    p=Path(__file__).resolve().parent/filename
    s=importlib.util.spec_from_file_location(name,p)
    m=importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m

def sha256(path):
    d=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1048576),b""):
            d.update(block)
    return d.hexdigest()

def load_table(path,headers):
    read=load_module("25_compare_independent_screening_qa.py","phase33_xlsx_reader")
    tables=read.xlsx_sheets(path,{"DISCREPANCIAS"})
    page=tables["DISCREPANCIAS"]
    if not page or [str(page[0].get(j,"")).strip() for j in range(len(headers))]!=headers:
        raise ValueError("Changed scientific reconciliation headers or source rubric")
    records={}
    sequence=[]
    for item in page[1:]:
        if not any(str(x).strip() for x in item.values()):
            continue
        if any(j>=len(headers) and str(v).strip() for j,v in item.items()):
            raise ValueError("Unexpected extra adjudication column")
        row=[str(item.get(j,"")).strip() for j in range(len(headers))]
        key=row[0]
        if not key.startswith("VAL") or len(key)!=7 or not key[3:].isdigit() or key in records:
            raise ValueError("Invalid or duplicated blinded case code")
        records[key]=row
        sequence.append(key)
    return records,sequence

def validate(pristine,returned,phase32):
    if set(pristine)!=set(returned):
        raise ValueError("Returned panel rows have missing or new identifiers")
    if len(pristine)!=phase32["records_needing_adjudication_or_fulltext"]:
        raise ValueError("Casebook size does not match Phase32 originally identified high-priority cases")
    missing=Counter()
    residual=Counter()
    reasons=set()
    changed=Counter()
    for key,old in pristine.items():
        new=returned[key]
        if old[:22]!=new[:22]:
            raise ValueError("Historical A/B data or source article text changed; original evidence must remain untouched")
        if any(old[col] for col in EDITOR_COLUMNS):
            raise ValueError("The baseline Phase32 panel output was already filled; do not overwrite an old panel round")
        for col,name,allowed in [
            (22,"scope",ALLOWED_SCOPE),(23,"relevance",ALLOWED_RELEVANCE),
            (24,"topic",ALLOWED_TOPIC),(25,"discipline",ALLOWED_DISCIPLINE),
            (27,"fulltext_escalation",ALLOWED_FULLTEXT)]:
            if not new[col]:
                missing[name]+=1
            elif new[col] not in allowed:
                raise ValueError("Invalid panel "+name+" in protected reconciliation")
        if not new[26]:
            missing["scientific_panel_justification"]+=1
        else:
            reasons.add(new[26])
        s,r=new[22],new[23]
        if s and r:
            if ((s=="0" and r!="0") or (s=="9" and r!="9") or
                (s=="1" and r=="0") or (r=="0" and s!="0")):
                raise ValueError("Inconsistent adjudicated scope and relevance codes")
        if r=="9":
            residual["uncertain_relevance_9"]+=1
            if new[27] and new[27]!="yes":
                raise ValueError("Uncertain final relevance R9 must escalate to full text")
        if r=="3":
            residual["direct_policy_3"]+=1
        if r in ("2","3"):
            residual["any_policy_2_or_3"]+=1
        if new[27]=="yes":
            residual["requested_fulltext_yes"]+=1
        if new[26]:
            if len(new[26])<14:
                missing["scientific_panel_justification_too_short"]+=1
        if new[23] and new[23]!=old[7] and new[23]!=old[8]:
            changed["relevance_differs_from_both_original_reviewers"]+=1
        if new[23] and new[23]!=old[7]:
            changed["relevance_differs_from_A"]+=1
        if new[23] and new[23]!=old[8]:
            changed["relevance_differs_from_B"]+=1
    return {
        "total":len(pristine),
        "missing_or_inadequate":dict(sorted(missing.items())),
        "adjudication_filled":len(pristine)-max(missing.values(),default=0),
        "distinct_scientific_justifications":len(reasons),
        "residual":dict(residual),
        "comparisons":dict(changed)
    }

def main():
    p=argparse.ArgumentParser()
    home=Path.home()
    p.add_argument("--original-panel-xlsx",default=str(home/"ai_policy_validacion1200_discrepancias_privado/Adjudicacion_Validacion_1200_Humana.xlsx"))
    p.add_argument("--returned-panel-xlsx",required=True)
    p.add_argument("--phase32-report",default="reports/phase32/human_expert_agreement_aggregate.json")
    p.add_argument("--codebook",default="docs/phase30_full_validation_codebook_v1.0.md")
    p.add_argument("--phase30-manifest",default=str(home/"ai_policy_validation1200_private/private_locked_manifest.json"))
    p.add_argument("--out",default="reports/phase33")
    args=p.parse_args()
    source=Path(args.original_panel_xlsx).expanduser().resolve()
    returned=Path(args.returned_panel_xlsx).expanduser().resolve()
    codebook=Path(args.codebook).expanduser().resolve()
    manifest=Path(args.phase30_manifest).expanduser().resolve()
    output=Path(args.out).expanduser().resolve()
    if not all(x.is_file() for x in (source,returned,codebook,manifest)):
        p.error("Original protected panel, completed panel, codebook or manifest missing")
    if source==returned or returned.parent==source.parent:
        p.error("Separate returned panel directory required; never overwrite original casebook")
    if any(output==x.parent or output in x.parents or x.parent in output.parents
           for x in (source,returned,manifest)):
        p.error("Do not write aggregate reports to protected data folders")
    if output.exists() and any(output.iterdir()):
        p.error("Phase33 report already exists; do not overwrite previous independent audit")
    phase32=json.loads(Path(args.phase32_report).read_text(encoding="utf8"))
    if phase32.get("status")!="PI_attributed_expert_ratings_scored_with_unresolved_legacy_AI_metadata_provenance":
        raise ValueError("Must use original PI-attributed Phase32 source; no AI pass can substitute")
    reference_manifest=json.loads(manifest.read_text(encoding="utf8"))
    if sha256(codebook)!=reference_manifest["codebook_sha256"]:
        raise ValueError("Source rubric changed after human scoring")
    p32=load_module("32_audit_pi_attested_human1200.py","phase33_source")
    pristine,ids=load_table(source,p32.HEADERS)
    candidate,candidate_ids=load_table(returned,p32.HEADERS)
    if candidate_ids!=ids:
        raise ValueError("Panel source row order changed; preserve pristine original order")
    stats=validate(pristine,candidate,phase32)
    # NOTE: only the scientific DATA columns are immutable. The returned
    # workbook may contain edited provenance/instructions: audit them
    # explicitly, rather than assuming human authorship or blindness.
    excel_reader=load_module("25_compare_independent_screening_qa.py","phase33_instruction_reader")
    orig_ins=excel_reader.xlsx_sheets(source,{"INSTRUCCIONES"})["INSTRUCCIONES"]
    ret_ins=excel_reader.xlsx_sheets(returned,{"INSTRUCCIONES"})["INSTRUCCIONES"]
    def first_two(rows):
        return [str(rows[i].get(0,"")).strip()+" : "+str(rows[i].get(1,"")).strip()
                for i in range(min(3,len(rows)))]
    prior_instructions=first_two(orig_ins)
    returned_instructions=first_two(ret_ins)
    instruction_metadata_modified=(prior_instructions!=returned_instructions)
    # A visible AI marker is NOT definitive proof of automated generation,
    # and an assertion of human work is NOT proof of genuine independent human
    # activity. Preserve both claims as an unresolved provenance conflict.
    ai_tagged=sum(str(x[26]).casefold().startswith("[adjudicación ia]")
                  for x in candidate.values())
    ciega_claim=any("tercera calificación ciega" in text.casefold()
                    for text in returned_instructions)
    provenance_flags={
        "returned_instructions_modified_from_original":instruction_metadata_modified,
        "panel_justifications_with_adjudicacion_IA_prefix_n":ai_tagged,
        "panel_sheet_claims_third_blinded_rating":ciega_claim,
        "actual_panel_was_informed_by_visible_AB_ratings":True,
        "human_authorship_verified_from_workbook":False,
        "human_authorship_documentation_required":True,
        "original_and_returned_workbook_SHA256_retained_privately":True,
        "source_original_sha256":sha256(source),
        "returned_original_sha256":sha256(returned)
    }
    if stats["missing_or_inadequate"]:
        raise ValueError("Returned 324-case panel is incomplete or has inadequate justifications: "+
                         json.dumps(stats["missing_or_inadequate"],sort_keys=True))
    result={
      "created_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
      "status":"completed_324_case_data_with_unresolved_panel_AI_provenance_and_fulltext",
      "phase32_original_expert_labels_immutable":True,
      "panel_derived_from_known_A_B_disagreements_not_blind":True,
      "original_1200_case_sample_preserved":True,
      "casebook_n":len(pristine),
      "panel_all_mandatory_fields_complete":True,
      "panel_scientific_reason_diagnostics":stats,
      "panel_provenance_diagnostics":provenance_flags,
      "prior_legacy_Claude_label_provenance_remains_unresolved":True,
      "source_lineage_proved_from_original_phase32_packet":True,
      "fulltext_actual_access_documented":False,
      "classifier_accuracy_calculated":False,
      "limitations":[
        "The panel saw earlier A/B ratings, so adjudication cannot be portrayed as another independent blind expert review.",
        "All returned panel reasons marked [Adjudicación IA], if observed, are explicitly disclosed as conflicting source provenance, not silently rebranded as independent human ratings.",
        "Instruction-sheet edits and claims of a third blind rating must be disclosed; the sheet visibly contains A/B ratings so this panel was not third-party blinded.",
        "PI states the two A/B labels were produced by new human experts despite original Excel stating Claude/AI; evidence of human authorship and independence must be obtained from both experts.",
        "A fulltext_escalation=yes label records a REQUEST for full text, not proof it was read.",
        "Still need a private auditable full-text consultation log, final eligible set definition, and design-weighted estimates for predeclared classifier-vs-reference outcomes.",
        "Only aggregate counts, not original titles/abstracts/codes, human reviews or panel rationales are public."
      ]
    }
    output.mkdir(parents=True,exist_ok=True)
    (output/"panel_adjudication_aggregate.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    (output/"summary.md").write_text(
        "# Phase33 — Completed panel adjudication integrity audit\n\n"
        "Status: "+result["status"]+"\n\n"
        "## Aggregate record counts\n\n"
        +json.dumps(stats,ensure_ascii=False,indent=2)+"\n\n"+
        "## Panel provenance warnings (NOT proof of expert authorship)\n\n"+json.dumps(provenance_flags,ensure_ascii=False,indent=2)+"\n\n"+
        "Original case-level records remain protected. Human authority, original metadata conflict and any actual full-text reading still require documentary evidence.\n",
        encoding="utf8")
    print("PHASE33",result["status"])
    print("Panel 324/324 structured fields checked; preserved historic A/B original ratings")
    print("Residual uncertainty R9:",stats["residual"].get("uncertain_relevance_9",0))
    print("PROVENANCE: IA-marked panel rationales",ai_tagged,"/324; edited instruction metadata",instruction_metadata_modified)
    print("PROVENANCE: cannot claim third blind adjudication or verified human authorship from these files")
    print("PUBLIC aggregate only:",output/"panel_adjudication_aggregate.json")
    print("STOP: no classifier precision, recall or full-text performance claimed")

if __name__=="__main__":
    main()
