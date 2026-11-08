#!/usr/bin/env python3
"""Phase 19 — secure, aggregate-only analysis of completed human adjudication.

Does not create decisions. Strictly checks that the returned Phase18 workbook
preserves the original blinded group codes, article examples, A/B ratings and
format, and that the adjudicator has filled all requested consensus fields.
Only then unblinds group-to-model correspondence INSIDE private CEDIA runtime,
and publishes aggregated per-model scores. Original raters are never modified.

Run even before adjudication is complete to receive aggregate readiness counts.
No identifiers, titles, abstracts, snippets, topic names or individual scores
are exported to the public GitHub reports.
"""
from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import os
from pathlib import Path
import posixpath
import re
import zipfile
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd

GROUP_HEADERS = [
    "Grupo","Nombre propuesto A","Nombre propuesto B",
    "Coherencia A","Coherencia B","Diferenciación A","Diferenciación B",
    "Pertinencia A","Pertinencia B","Comentario A","Comentario B",
    "NOMBRE FINAL (editar)","COHERENCIA FINAL (1-5)",
    "DIFERENCIACIÓN FINAL (1-5)","PERTINENCIA FINAL (0-3,9)",
    "JUSTIFICACIÓN FINAL (editar)"
]
DOC_HEADERS = [
    "Grupo","Documento","Título","Resumen","Extracto cuerpo A","Extracto cuerpo B",
    "Pertenencia A","Pertenencia B","Pertinencia A","Pertinencia B"
]
DIFF_HEADERS = [
    "Grupo","Documento","Pertenencia A","Pertenencia B","Pertinencia A","Pertinencia B",
    "Título","Resumen","Extracto cuerpo A","Extracto cuerpo B",
    "Comentario A","Comentario B",
    "PERTENENCIA FINAL (0,1,9)","PERTINENCIA FINAL (0-3,9)",
    "JUSTIFICACIÓN FINAL (editar)"
]
SPECS = {
    "GRUPOS":{"headers":GROUP_HEADERS,"keys":[0],"edits":{
        11:None,12:{"1","2","3","4","5"},
        13:{"1","2","3","4","5"},
        14:{"0","1","2","3","9"},15:None}},
    "EJEMPLOS":{"headers":DOC_HEADERS,"keys":[0,1],"edits":{}},
    "DESACUERDOS":{"headers":DIFF_HEADERS,"keys":[0,1],"edits":{
        12:{"0","1","9"},13:{"0","1","2","3","9"},14:None}}
}
REQ = ["GRUPOS","EJEMPLOS","DESACUERDOS"]


def helper_load(filename, name):
    path=Path(__file__).resolve().parent/filename
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def workbook_read(file,helper):
    if not file.is_file() or file.stat().st_size>50_000_000:
        raise ValueError("Workbook missing or exceeds allowed XLSX size")
    result={}
    ns=helper.NS
    relns="http://schemas.openxmlformats.org/package/2006/relationships"
    with zipfile.ZipFile(file) as z:
        if sum(i.file_size for i in z.infolist())>150_000_000:
            raise ValueError("Excessive uncompressed XLSX size")
        wb=ET.fromstring(z.read("xl/workbook.xml"))
        rel=ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        relations={}
        for x in rel.findall(f"{{{relns}}}Relationship"):
            relations[x.get("Id")]=x.get("Target","")
        shared=[]
        if "xl/sharedStrings.xml" in z.namelist():
            sr=ET.fromstring(z.read("xl/sharedStrings.xml"))
            shared=["".join(t.text or "" for t in si.findall(f".//{{{ns}}}t"))
                    for si in sr.findall(f"{{{ns}}}si")]
        for sh in wb.findall(f".//{{{ns}}}sheets/{{{ns}}}sheet"):
            name=sh.get("name","")
            if name not in REQ:
                continue
            rid=sh.get(f"{{{helper.REL}}}id")
            target=relations.get(rid,"")
            if not target:
                raise ValueError("Missing workbook worksheet relationship")
            # Excel may store relative or absolute package member paths.
            path=(target.lstrip("/") if target.startswith("/")
                  else posixpath.normpath(posixpath.join("xl",target)))
            if not path.startswith("xl/worksheets/") or path not in z.namelist():
                raise ValueError("Invalid or missing worksheet XML target")
            root=ET.fromstring(z.read(path))
            if root.find(f".//{{{ns}}}f") is not None:
                raise ValueError("Formula found in adjudication/evidence sheet; use literal values")
            values=helper.xlsx_sheet(z,path,shared)
            result[name]=values
    if set(result)!=set(REQ):
        raise ValueError("Required adjudication sheets are missing or renamed")
    return result


def table(sheet,headers,keys,section):
    count=len(headers)
    if not sheet or [sheet[0].get(i,"") for i in range(count)]!=headers:
        raise ValueError("Headers changed in "+section)
    data={}
    for rec in sheet[1:]:
        if not any(str(v).strip() for v in rec.values()):
            continue
        if any(int(j)>=count and str(v).strip() for j,v in rec.items()):
            raise ValueError("Unexpected extra columns with values in "+section)
        record={i:str(rec.get(i,"")).strip() for i in range(count)}
        key=tuple(record[i] for i in keys)
        if not all(key) or key in data:
            raise ValueError("Missing/duplicated group or article code in "+section)
        data[key]=record
    return data


def read_compare(original,returned,info):
    checked={}
    final={}
    for section in REQ:
        cfg=SPECS[section]
        base=table(original[section],cfg["headers"],cfg["keys"],section)
        received=table(returned[section],cfg["headers"],cfg["keys"],section)
        if set(base)!=set(received):
            raise ValueError("Group/document membership changed in "+section)
        for key,row in received.items():
            for col in range(len(cfg["headers"])):
                if col not in cfg["edits"] and row[col]!=base[key][col]:
                    raise ValueError("Original evidence or A/B rating was edited in "+section)
                if col in cfg["edits"]:
                    permitted=cfg["edits"][col]
                    if permitted is not None and row[col] and row[col] not in permitted:
                        raise ValueError("Invalid numeric rating in "+section)
                    # Cannot replace source already-filled consensus without explicit
                    # version control; initial Phase18 has empty consensus fields.
                    if base[key][col]:
                        raise ValueError("Original adjudication workbook has pre-filled consensus")
        checked[section]={
            "records":len(base),
            "unchanged_keys_and_evidence":True,
        }
        final[section]=received
    if len(final["GRUPOS"])!=48 or len(final["EJEMPLOS"])!=336 or \
       len(final["DESACUERDOS"])!=int(info["counts"]["disputed_unique_document_cases"]):
        raise ValueError("Wrong Phase18 adjudication row count")
    return final,checked


def readiness(rows,edit_map):
    result={}
    complete=True
    for index,allowed in edit_map.items():
        filled=sum(bool(row[index]) for row in rows.values())
        result[str(index)]={"filled":filled,"total":len(rows)}
        if filled!=len(rows):
            complete=False
    return result,complete


def describe(a):
    x=np.asarray(a,dtype=float)
    x=x[np.isfinite(x)]
    if not len(x):
        return {"n":0}
    return {"n":len(x),"mean":round(float(x.mean()),5),
            "median":round(float(np.median(x)),5),
            "sd":round(float(x.std(ddof=1)),5) if len(x)>1 else None,
            "min":round(float(x.min()),5),
            "max":round(float(x.max()),5)}


def compare_models(ratings, normalized):
    key=pd.read_csv(normalized/"private_sampling_key.csv",
                    encoding="utf-8-sig",dtype=str).fillna("")
    if key.duplicated(["group_code","item_code"]).any() or len(key)!=336:
        raise ValueError("Incompatible or duplicated private group correspondence")
    if not {"group_code","item_code","modality","k"}.issubset(key):
        raise ValueError("Incomplete private group correspondence key")
    group_map=key[["group_code","modality","k"]].drop_duplicates()
    if len(group_map)!=48 or group_map["group_code"].duplicated().any():
        raise ValueError("Each group must map to exactly one model")
    group_model={row.group_code:row.modality+"_k"+str(row.k)
                 for row in group_map.itertuples(index=False)}
    groups=ratings["GRUPOS"]
    docs=ratings["EJEMPLOS"]
    differences=ratings["DESACUERDOS"]

    disputes={}
    for record in differences.values():
        disputes[(record[0],record[1])]=record
    field_results={}
    doc_count_from_adjudication=0
    doc_count_unanimous=0
    for keyid,document in docs.items():
        group,doc_code=keyid
        if group not in group_model:
            raise ValueError("Unrecognized blinded group code")
        if keyid in disputes:
            rec=disputes[keyid]
            memb=rec[12]
            policy=rec[13]
            doc_count_from_adjudication+=1
        else:
            if document[6]!=document[7] or document[8]!=document[9]:
                raise ValueError("Non-adjudicated document contains disagreement")
            memb=document[6]
            policy=document[8]
            doc_count_unanimous+=1
        if memb not in {"0","1","9"} or policy not in {"0","1","2","3","9"}:
            raise ValueError("Document-level consensus missing or malformed")
        field_results[keyid]=(int(memb),int(policy))
    if len(field_results)!=336:
        raise ValueError("Missing document consensus values")

    by_model={}
    for name in sorted(set(group_model.values())):
        group_codes={g for g,m in group_model.items() if m==name}
        glist=[groups[(g,)] for g in sorted(group_codes)]
        document_list=[values for (g,d),values in field_results.items()
                       if g in group_codes]
        coherence=[int(x[12]) for x in glist]
        distinct=[int(x[13]) for x in glist]
        policy_g=[int(x[14]) for x in glist]
        membership=[x[0] for x in document_list]
        policy_d=[x[1] for x in document_list]
        eligible_m=[x for x in membership if x!=9]
        eligible_p=[x for x in policy_d if x!=9]
        by_model[name]={
            "topic_groups":len(glist),
            "document_cases":len(document_list),
            "topic_coherence":describe(coherence),
            "topic_distinctiveness":describe(distinct),
            "topic_policy_relevance":describe([x for x in policy_g if x!=9]),
            "topic_policy_uncertain_n":sum(x==9 for x in policy_g),
            "document_membership_yes_fraction":round(
                sum(x==1 for x in eligible_m)/len(eligible_m),5)
                if eligible_m else None,
            "document_membership_evaluable":len(eligible_m),
            "document_membership_uncertain_n":len(membership)-len(eligible_m),
            "document_policy_relevance":describe(eligible_p),
            "document_policy_uncertain_n":len(policy_d)-len(eligible_p),
            "document_policy_direct_3_fraction":round(
                sum(x==3 for x in eligible_p)/len(eligible_p),5)
                if eligible_p else None,
            "document_policy_at_least_indirect_2plus_fraction":round(
                sum(x>=2 for x in eligible_p)/len(eligible_p),5)
                if eligible_p else None,
        }
    assert sum(v["topic_groups"] for v in by_model.values())==48
    assert sum(v["document_cases"] for v in by_model.values())==336
    return {
        "models":by_model,
        "document_consensus_source_counts":{
            "adjudicated_disputed_cases":doc_count_from_adjudication,
            "unanimous_A_B_cases_retained_without_adjudication":doc_count_unanimous
        },
        "decision":"no_automated_model_selection"
    }


def write_report(out,report):
    out.mkdir(parents=True,exist_ok=True)
    (out/"adjudicated_topic_comparison_aggregate.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False),encoding="utf8")
    md=[
        "# Phase 19 — Post-adjudication blinded topic comparison",
        "","Status: "+report["status"],
        "UTC: "+report["generated_utc"],
        "","## Input integrity",json.dumps(report["input_integrity"],indent=2),
        "","## Adjudication readiness",json.dumps(report["readiness"],indent=2)
    ]
    if "aggregate_results" in report:
        md+=["","## Aggregates ONLY (completed human adjudication)",
             json.dumps(report["aggregate_results"],indent=2)]
    md+=["","## Limits"]+["- "+v for v in report["limitations"]]
    (out/"summary.md").write_text("\n".join(md)+"\n",encoding="utf8")


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--original-xlsx",default=str(
        Path.home()/"ai_policy_adjudicacion_privado/Adjudicacion_Ciega_Fase18.xlsx"))
    ap.add_argument("--returned-xlsx",required=True)
    ap.add_argument("--phase18-report",default="reports/phase18/adjudication_preparation_aggregate.json")
    ap.add_argument("--normalized-ratings",default=str(
        Path.home()/"ai_policy_calificaciones_normalizadas_privado"))
    ap.add_argument("--out",default="reports/phase19")
    args=ap.parse_args()
    original=Path(args.original_xlsx).expanduser().resolve()
    returned=Path(args.returned_xlsx).expanduser().resolve()
    normalized=Path(args.normalized_ratings).expanduser().resolve()
    out=Path(args.out).expanduser().resolve()
    if not normalized.is_dir() or not original.is_file() or not returned.is_file():
        ap.error("Missing original template, returned workbook or private phase16 sheets")
    if returned==original:
        ap.error("Do not overwrite original blank adjudication template: save completed copy in a new location")
    repo=Path.home()/"AI_policy"
    if out==normalized or normalized in out.parents or \
       out==original.parent or original.parent in out.parents or \
       out==returned.parent or returned.parent in out.parents:
        ap.error("Public report must be separate from private files")
    helper=helper_load("17_excel_reviewer_packages.py","phase17_excel_private")
    phase18=json.loads(Path(args.phase18_report).read_text(encoding="utf8"))
    if phase18.get("status")!="adjudication_packet_prepared_human_consensus_pending":
        raise ValueError("Phase18 public sample preparation report missing or not completed")
    base=workbook_read(original,helper)
    final=workbook_read(returned,helper)
    forms,integrity=read_compare(base,final,phase18)
    topic_state,topic_done=readiness(forms["GRUPOS"],SPECS["GRUPOS"]["edits"])
    diff_state,diff_done=readiness(forms["DESACUERDOS"],SPECS["DESACUERDOS"]["edits"])
    complete=bool(topic_done and diff_done)
    public={
        "generated_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
        "status":"completed_human_adjudication_unblinded_aggregate" if complete
                 else "awaiting_human_adjudication",
        "input_integrity":integrity,
        "readiness":{"topic_groups":topic_state,"disputed_documents":diff_state},
        "limitations":[
            "Only human-completed adjudication values are reported. No automatic filling or third-party ratings are fabricated.",
            "Adjudication is a consensus decision after viewing A/B scores; it does NOT change the original independent inter-rater kappa or act as a third independent rater.",
            "On documents with identical A/B scores, the common original judgment is retained, not re-adjudicated.",
            "The group examples are a deliberately centroid-skewed sample. Group means and document scores are descriptive for those cases, not population-wide accuracy.",
            "Model groups are unblinded from the private key only AFTER completeness and workbook integrity checks; group names and per-record decisions are never published.",
            "Small numbers of groups (12 or 18 per model) and dependence among samples preclude automatic significance or winner declarations.",
            "The Phase5 inclusion/eligibility human-review workflow remains separate and pending.",
            "The full-text source was character-truncated for many PDFs; results do not imply complete-document coverage."
        ]
    }
    if complete:
        public["aggregate_results"]=compare_models(forms,normalized)
    write_report(out,public)
    print("PHASE19",public["status"])
    print("Groups:",integrity["GRUPOS"]["records"],
          "document exemplars:",integrity["EJEMPLOS"]["records"],
          "adjudication cases:",integrity["DESACUERDOS"]["records"])
    for label,rows in public["readiness"].items():
        values=list(rows.values())
        print(label,"fields complete:",sum(x["filled"] for x in values),
              "of",sum(x["total"] for x in values))
    print("Only aggregate reports generated:",out)
    print("No private workbook or human ratings were exported.")


if __name__=="__main__":
    main()
