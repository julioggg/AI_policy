#!/usr/bin/env python3
"""Phase25: audit independent Phase24 QA ratings vs protected Phase23 consensus.

Two separate processes are strictly distinguished:
1) Actual independent human QA: 80 ratings of RELEVANCE and DISCIPLINE.
2) Post-review normalization of nonstandard POLICY categories: some automatic
   one-to-one semantic proposals plus expert resolution of ambiguous cases.
Policy outcomes cannot be called independently rated original-codebook labels.

No article IDs, titles, abstracts, QA/sample codes, reviewer comments, or
individual decisions can appear in public reports. Risk-enriched 80-item
sample is NOT representative. No classifier precision, recall or population
performance is estimated.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import datetime as dt
import importlib.util
import json
import math
from pathlib import Path
import posixpath
import xml.etree.ElementTree as ET
import zipfile
from sklearn.metrics import cohen_kappa_score

NS="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
RNS="http://schemas.openxmlformats.org/package/2006/relationships"
DOCREL="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
QA_HEADERS=[
    "Código QA","Título","Resumen","Año","Tipo",
    "Relevancia independiente (0,1,2,3,9)",
    "Disciplina independiente",
    "Dimensión principal de política","Justificación científica"
]
NORMAL_HEADERS=["Código QA","Relevancia QA","Título","Resumen",
                "Categoría original","Propuesta técnica","CÓDIGO FINAL",
                "Estado","Justificación QA","Nota del validador"]
RELEVANCE={"0","1","2","3","9"}
DISCIPLINE={"ssh","engineering","health_sciences","general_he","uncertain"}
POLICY={"teaching_learning","assessment","ethics_integrity","governance_policy",
        "research_scholarship","ai_literacy_training","equity_access",
        "privacy_security","general_policy","not_applicable","uncertain"}
MAPPING={
    "Ninguna (Uso General)":"not_applicable",
    "Marco Político/Regulatorio":"governance_policy",
    "Ética y Plagio":"ethics_integrity",
    "N/A":"not_applicable",
    "Ética y Gobernanza":None,
}

def helper():
    path=Path(__file__).resolve().parent/"17_excel_reviewer_packages.py"
    spec=importlib.util.spec_from_file_location("phase25_excel_helper",path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def xlsx_sheets(path,names):
    if not path.is_file() or path.stat().st_size>40_000_000:
        raise ValueError("Private QA or mapping workbook not found, or too large")
    result={}
    ext=helper()
    with zipfile.ZipFile(path) as z:
        if sum(i.file_size for i in z.infolist())>160_000_000 or z.testzip() is not None:
            raise ValueError("Invalid or oversized XLSX ZIP package")
        wb=ET.fromstring(z.read("xl/workbook.xml"))
        rel=ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        targets={r.get("Id"):r.get("Target") for r in
                 rel.findall(f"{{{RNS}}}Relationship")}
        shared=[]
        if "xl/sharedStrings.xml" in z.namelist():
            st=ET.fromstring(z.read("xl/sharedStrings.xml"))
            shared=["".join(v.text or "" for v in si.findall(f".//{{{NS}}}t"))
                    for si in st.findall(f"{{{NS}}}si")]
        for s in wb.findall(f".//{{{NS}}}sheets/{{{NS}}}sheet"):
            name=s.get("name","")
            if name not in names:
                continue
            target=targets.get(s.get(f"{{{DOCREL}}}id"),"")
            member=(target.lstrip("/") if target.startswith("/") else
                    posixpath.normpath(posixpath.join("xl",target)))
            if not member.startswith("xl/worksheets/") or member not in z.namelist():
                raise ValueError("Missing or unsupported worksheet relationship")
            root=ET.fromstring(z.read(member))
            if root.find(f".//{{{NS}}}f") is not None:
                raise ValueError("Formula cells are not permitted in reviewed sheets")
            result[name]=ext.xlsx_sheet(z,member,shared)
    if set(result)!=set(names):
        raise ValueError("Expected worksheet missing or renamed")
    return result


def sheet_records(rows,headers,count,what):
    if not rows or [rows[0].get(i,"") for i in range(len(headers))]!=headers:
        raise ValueError(what+" workbook headers differ from original codebook")
    data={}
    for row in rows[1:]:
        if not any(str(x).strip() for x in row.values()):
            continue
        if any(k>=len(headers) and str(v).strip() for k,v in row.items()):
            raise ValueError("Unexpected data in extra workbook column")
        values=[str(row.get(i,"")).strip() for i in range(len(headers))]
        code=values[0]
        if code in data or not code.startswith("Q") or not code[1:].isdigit():
            raise ValueError("Duplicated or invalid QA sample code")
        data[code]=values
    if len(data)!=count:
        raise ValueError("Wrong QA sample size")
    return data


def load_key(path):
    if not path.is_file():
        raise ValueError("Private Phase24 correspondence key unavailable")
    with path.open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        fields={"qa_code","sample_id","selection_reason","stratum",
                "consensus_relevance","consensus_discipline","consensus_policy"}
        if not fields.issubset(reader.fieldnames or []):
            raise ValueError("Incomplete QA correspondence key")
        records=list(reader)
    if len(records)!=80 or len({r["qa_code"] for r in records})!=80 or \
       len({r["sample_id"] for r in records})!=80:
        raise ValueError("QA private key has duplicate/missing records")
    return {r["qa_code"]:r for r in records}


def ordinal_agreement(a,b):
    result={"paired_all_including_9":len(a),
            "exact_agreement_all_including_9":round(sum(x==y for x,y in zip(a,b))/len(a),5),
            "uncertain_consensus_n":sum(x=="9" for x in b),
            "uncertain_qa_n":sum(x=="9" for x in a)}
    pairs=[(x,y) for x,y in zip(a,b) if x!="9" and y!="9"]
    result["paired_evaluable_excluding_9"]=len(pairs)
    for weighted,label in [(None,"kappa_unweighted"),("quadratic","kappa_quadratic")]:
        if pairs:
            xa,xb=zip(*pairs)
            value=float(cohen_kappa_score(xa,xb,labels=["0","1","2","3"],weights=weighted))
            result[label]=round(value,5) if math.isfinite(value) else None
        else:
            result[label]=None
    return result


def nominal_agreement(a,b,categories):
    result={"n":len(a),"exact_agreement":round(sum(x==y for x,y in zip(a,b))/len(a),5)}
    value=float(cohen_kappa_score(a,b,labels=sorted(categories)))
    result["cohen_kappa"]=round(value,5) if math.isfinite(value) else None
    return result


def compare(qa,key,policy):
    ordered=sorted(qa)
    qr=[qa[q][5] for q in ordered]
    cr=[key[q]["consensus_relevance"] for q in ordered]
    qd=[qa[q][6] for q in ordered]
    cd=[key[q]["consensus_discipline"] for q in ordered]
    outcome={
        "independent_QA_relevance_vs_prior_human_consensus":ordinal_agreement(qr,cr),
        "independent_QA_discipline_vs_prior_human_consensus":nominal_agreement(qd,cd,DISCIPLINE),
        "relevance_distribution":{
            "qa":dict(Counter(qr)),
            "prior_consensus":dict(Counter(cr))
        },
        "consensus_9_selected_for_QA_n":sum(v=="9" for v in cr),
        "consensus_9_QA_reclassified_as_0_to_3_n":sum(
            p=="9" and q!="9" for p,q in zip(cr,qr)),
        "relevance_mismatch_cases":sum(x!=y for x,y in zip(qr,cr)),
        "discipline_mismatch_cases":sum(x!=y for x,y in zip(qd,cd)),
        "qa_policy_codebook_status":"not_fully_normalized",
        "policy_original_QA_labels_outside_rubric_n":sum(qa[q][7] not in POLICY for q in ordered)
    }
    if policy is not None:
        qp=[policy[q] for q in ordered]
        cp=[key[q]["consensus_policy"] for q in ordered]
        if any(x not in POLICY for x in cp):
            raise ValueError("Private Phase24 key includes non-codebook consensus policy category")
        outcome["qa_policy_codebook_status"]="post_hoc_normalized_mixed_analyst_and_expert"
        outcome["post_hoc_normalized_policy_vs_prior_consensus"]=nominal_agreement(qp,cp,POLICY)
        outcome["post_hoc_policy_mismatch_cases"]=sum(x!=y for x,y in zip(qp,cp))
        outcome["post_hoc_policy_distribution"]={
            "normalized_qa":dict(Counter(qp)),
            "prior_consensus":dict(Counter(cp))
        }
    # No item-level detail, codes, risk groups or previous individual labels published.
    return outcome


def read_normalization(path,qa):
    rec=sheet_records(xlsx_sheets(path,{"NORMALIZACION"})["NORMALIZACION"],
                      NORMAL_HEADERS,80,"Mapping")
    if set(rec)!=set(qa):
        raise ValueError("QA and normalization workbook sample codes differ")
    canonical={}
    pending=0
    prefilled=0
    reviewer_adjusted=0
    for code,row in rec.items():
        origin=qa[code]
        if row[0]!=code or row[1]!=origin[5] or \
           row[2]!=origin[1] or row[3]!=origin[2] or \
           row[4]!=origin[7] or row[8]!=origin[8]:
            raise ValueError("Original QA source evidence/ratings modified in normalization workbook")
        if row[4] not in MAPPING:
            raise ValueError("Unrecognized raw QA policy category for declared mapping")
        proposal=MAPPING[row[4]]
        if row[5]!=(proposal or ""):
            raise ValueError("Mapping proposal was modified; only FINAL column may change")
        val=row[6]
        if val and val not in POLICY:
            raise ValueError("Invalid human/analyst normalized policy category")
        if not val:
            pending+=1
        else:
            canonical[code]=val
        if proposal is not None:
            prefilled+=1
            reviewer_adjusted+=int(bool(val) and val!=proposal)
    status={
        "normalization_rows":80,
        "validated_final_codes":80-pending,
        "pending_ambiguous_or_revised_codes":pending,
        "proposed_semantic_equivalences_n":prefilled,
        "changes_to_proposed_equivalence_n":reviewer_adjusted,
        "post_hoc_normalization_does_not_constitute_independent_QA_policy_scoring":True
    }
    return (canonical if not pending else None),status


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--qa-original-xlsx",default=str(
      Path.home()/"ai_policy_screening_qa_independent_privado/Control_Independiente_Cribado_Fase24.xlsx"))
    parser.add_argument("--qa-returned-xlsx",required=True)
    parser.add_argument("--qa-private-key",default=str(
      Path.home()/"ai_policy_screening_qa_independent_privado/correspondencia_qa_privada.csv"))
    parser.add_argument("--normalization-xlsx")
    parser.add_argument("--phase24-report",default="reports/phase24/quality_audit_packet_aggregate.json")
    parser.add_argument("--out",default="reports/phase25")
    args=parser.parse_args()
    original=Path(args.qa_original_xlsx).expanduser().resolve()
    returned=Path(args.qa_returned_xlsx).expanduser().resolve()
    keyfile=Path(args.qa_private_key).expanduser().resolve()
    out=Path(args.out).expanduser().resolve()
    if original==returned:
        parser.error("Keep the original blank QA workbook separate from human completed workbook")
    for folder in (original.parent,returned.parent,keyfile.parent):
        if out==folder or folder in out.parents:
            parser.error("Do not save public aggregate reports in protected private workbook directories")
    p24=json.loads(Path(args.phase24_report).read_text(encoding="utf8"))
    if p24.get("status")!="private_blinded_quality_audit_packet_prepared_human_QA_pending" or \
       p24.get("review_sample_n")!=80:
        raise ValueError("Missing authoritative Phase24 preparation report")
    original_raw=sheet_records(
        xlsx_sheets(original,{"CONTROL_QA"})["CONTROL_QA"],QA_HEADERS,80,"Original")
    qa=sheet_records(xlsx_sheets(returned,{"CONTROL_QA"})["CONTROL_QA"],
                     QA_HEADERS,80,"Independent")
    if set(original_raw)!=set(qa):
        raise ValueError("Sample Q codes in reviewer response were changed")
    for code in qa:
        src=original_raw[code]
        entered=qa[code]
        if src[:5]!=entered[:5] or any(src[j] for j in range(5,9)):
            raise ValueError("Source bibliographic evidence or initial blank template was altered")
        if entered[5] not in RELEVANCE or entered[6] not in DISCIPLINE or \
           not entered[7] or not entered[8]:
            raise ValueError("Incomplete or non-codebook independent QA rating/justification")
    key=load_key(keyfile)
    if set(key)!=set(qa):
        raise ValueError("Private correspondence key does not match original QA sample")
    if any(key[k]["consensus_relevance"] not in RELEVANCE or
           key[k]["consensus_discipline"] not in DISCIPLINE for k in key):
        raise ValueError("QA protected correspondence key has illegal prior ratings")
    normalized_policy=None
    map_status={"status":"not_supplied","reason":"Original QA policy free-text categories did not follow the official codebook."}
    if args.normalization_xlsx:
        normalized_policy,map_status=read_normalization(
            Path(args.normalization_xlsx).expanduser().resolve(),qa)
        map_status["status"]="complete" if normalized_policy is not None else "pending"
    results=compare(qa,key,normalized_policy)
    report={
       "created_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
       "status":("independent_qa_scored_with_posthoc_policy_normalization"
                 if normalized_policy is not None else
                 "independent_qa_relevance_discipline_scored_policy_normalization_pending"),
       "sample_n":80,
       "audit_sample_type":"purposefully_risk_enriched_NOT_random_or_population_representative",
       "source_integrity":{
           "original_evidence_unchanged":True,
           "original_blank_rubric_unchanged":True,
           "private_QA_correspondence_key_matched":True,
           "independent_reviewer_labels_not_rewritten":True
       },
       "policy_normalization":map_status,
       "results":results,
       "limitations":[
           "Independent QA assessor must have been procedurally blind to A/B, prior consensus, model labels and sample stratification; script cannot prove this.",
           "This 80-item audit was deliberately enriched for uncertain, reviewer-disputed and policy-sensitive cases; any agreement is descriptive for the selected sample only.",
           "Risk-selected QA disagreement proportions are not unbiased corpus classification accuracy, precision or recall.",
           "The 80 QA policy labels were originally nonstandard and cannot be treated as codebook-compliant until normalization is complete and reviewed.",
           "The normalized policy dimension (if completed) mixes transparent analyst equivalence proposals and expert decisions: do not present it as originally independently coded using the official taxonomy.",
           "The Phase23 original human consensus is not automatically overwritten by the QA review.",
           "Code 9 is uncertainty and should not be silently counted as an inclusion or exclusion.",
           "No publication identifier, title/abstract text, reviewer/adjudicator rationale or record-level rating is disclosed."
       ]
    }
    out.mkdir(parents=True,exist_ok=True)
    (out/"independent_screening_qa_aggregate.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    (out/"summary.md").write_text(
        "# Phase25 — Independent Phase24 QA versus prior human consensus\n\n"
        "Status: "+report["status"]+"\n\n"
        "## Agreement, aggregate only\n"+
        json.dumps(results,ensure_ascii=False,indent=2)+"\n\n"+
        "## Policy normalization readiness\n"+
        json.dumps(map_status,ensure_ascii=False,indent=2)+"\n\n"+
        "## Restrictions\n"+"\n".join("- "+x for x in report["limitations"])+"\n",
        encoding="utf8")
    print("PHASE25",report["status"])
    print("Independent QA:",len(qa),"/80, source evidence verified")
    print("Policy normalization:",map_status["status"])
    print("Aggregate results:",out/"independent_screening_qa_aggregate.json")
    print("Original QA responses and all private sampling/consensus data remain protected")


if __name__=="__main__":
    main()
