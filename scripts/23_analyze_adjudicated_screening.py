#!/usr/bin/env python3
"""Phase23 — audit completed human Phase22 adjudication; publish aggregates ONLY.

Protected CEDIA inputs:
- immutable original Phase22 XLSX blank adjudication packet,
- returned copy with 316 manually completed decisions,
- Phase20 normalized independent A/B CSVs and blinded sampling key.

Strictly verifies workbook originals, all 316 disputed records, independent
source judgments and key correspondence. After validation it unblinds strata
only INSIDE CEDIA, and reports per-stratum consensus distributions and
cautious design-weighted descriptive estimates for the FOUR final AI
screening strata (NOT the earlier bibliographic filter exclusions).

Never exports article IDs, titles, abstracts, reviewer/adjudicator comments,
sample keys, item-level decisions, per-row model predictions, or texts.
No automated human labels and no automatic claim of classification accuracy.
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
import re
import xml.etree.ElementTree as ET
import zipfile

REL="http://schemas.openxmlformats.org/package/2006/relationships"
XNS="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
VALID_RELEVANCE={"0","1","2","3","9"}
VALID_DISCIPLINE={"ssh","engineering","health_sciences","general_he","uncertain"}
VALID_POLICY={"teaching_learning","assessment","ethics_integrity",
              "governance_policy","research_scholarship","ai_literacy_training",
              "equity_access","privacy_security","general_policy",
              "not_applicable","uncertain"}
STRATA=("screen_include_core","screen_include_policy",
        "screen_include_context","screen_exclude",
        "q1_not_article_ready","core_not_q1")
SCREENING_STRATA=STRATA[:4]
BASE_FIELDS=("sample_id","title","abstract","publication_year","type")
RATING_FIELDS=("relevance_code","discipline_code","primary_policy_code")
HEADERS={
    "DISCREPANCIAS":[
        "Código","Título","Resumen","Año","Tipo",
        "Relevancia A","Relevancia B","Disciplina A","Disciplina B",
        "Política A","Política B","Justificación A","Justificación B",
        "RELEVANCIA FINAL (0,1,2,3,9)","DISCIPLINA FINAL",
        "DIMENSIÓN FINAL","JUSTIFICACIÓN DEL CONSENSO"],
    "TODOS":[
        "Código","Título","Resumen","Año","Tipo",
        "Relevancia A","Relevancia B","Disciplina A","Disciplina B",
        "Política A","Política B"]
}
VALID_COL={13:VALID_RELEVANCE,14:VALID_DISCIPLINE,15:VALID_POLICY}
INDICES={"relevance":(5,6,13),"discipline":(7,8,14),"policy":(9,10,15)}


def excel_helper():
    path=Path(__file__).resolve().parent/"17_excel_reviewer_packages.py"
    spec=importlib.util.spec_from_file_location("phase23_spreadsheet",path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sheet_data(path,helper):
    if not path.is_file() or path.stat().st_size>40_000_000:
        raise ValueError("Original or returned XLSX missing/excessive file size")
    needed={"INSTRUCCIONES","DISCREPANCIAS","TODOS","ESCALAS"}
    result={}
    with zipfile.ZipFile(path) as z:
        if sum(i.file_size for i in z.infolist())>190_000_000:
            raise ValueError("Uncompressed XLSX exceeds safe limit")
        if z.testzip() is not None:
            raise ValueError("Excel archive failed integrity check")
        workbook=ET.fromstring(z.read("xl/workbook.xml"))
        relationships=ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        by_id={x.get("Id"):x.get("Target") for x in relationships.findall(
            "{http://schemas.openxmlformats.org/package/2006/relationships}Relationship")}
        strings=[]
        if "xl/sharedStrings.xml" in z.namelist():
            root=ET.fromstring(z.read("xl/sharedStrings.xml"))
            strings=["".join(x.text or "" for x in si.findall(f".//{{{XNS}}}t"))
                     for si in root.findall(f"{{{XNS}}}si")]
        for sheet in workbook.findall(f".//{{{XNS}}}sheets/{{{XNS}}}sheet"):
            name=sheet.get("name","")
            if name not in needed:
                raise ValueError("Unexpected Excel worksheet")
            r_id=sheet.get(f"{{{REL}}}id")
            target=by_id.get(r_id,"")
            if not target:
                raise ValueError("Missing XLSX sheet relationship")
            member=target.lstrip("/") if target.startswith("/") else \
                posixpath.normpath(posixpath.join("xl",target))
            if not member.startswith("xl/worksheets/") or member not in z.namelist():
                raise ValueError("Unsupported or missing XLSX worksheet target")
            xml=ET.fromstring(z.read(member))
            if xml.find(f".//{{{XNS}}}f") is not None:
                raise ValueError("Formula cells in human-review workbook are forbidden")
            data=helper.xlsx_sheet(z,member,strings)
            result[name]=data
        if set(result)!=needed:
            raise ValueError("Required original worksheets are missing")
    return result


def parsed_rows(rows,headers,code_name):
    if not rows or [rows[0].get(j,"") for j in range(len(headers))]!=headers:
        raise ValueError("Screening worksheet headers were modified")
    data={}
    for r in rows[1:]:
        if not any(str(x).strip() for x in r.values()):
            continue
        if any(j>=len(headers) and str(x).strip() for j,x in r.items()):
            raise ValueError("Unexpected populated Excel columns")
        record=[str(r.get(j,"")).strip() for j in range(len(headers))]
        key=record[0]
        if not re.fullmatch(r"P\d{4}",key) or key in data:
            raise ValueError("Missing, duplicated or invalid blinded sample code")
        data[key]=record
    if code_name=="TODOS" and len(data)!=368:
        raise ValueError("Expected 368 initial sample rows")
    return data


def read_original_raters(private):
    frames={}
    for who in ("a","b"):
        path=private/f"rater_{who}.csv"
        if not path.is_file():
            raise ValueError("Missing original normalized independent human scores")
        with path.open(encoding="utf-8-sig",newline="") as f:
            rdr=csv.DictReader(f)
            fields=set((rdr.fieldnames or []))
            if not set(BASE_FIELDS+RATING_FIELDS+("reason",)).issubset(fields):
                raise ValueError("Reviewer source fields missing")
            records=list(rdr)
        if len(records)!=368 or len({r["sample_id"] for r in records})!=368:
            raise ValueError("Reviewer source sample IDs are missing/duplicated")
        frames[who]={r["sample_id"]:r for r in records}
    if set(frames["a"])!=set(frames["b"]):
        raise ValueError("Independent reviewer IDs do not match")
    return frames


def read_private_key(private,phase05):
    path=private/"sampling_key.csv"
    if not path.is_file():
        raise ValueError("Protected private sampling key missing")
    with path.open(encoding="utf-8-sig",newline="") as f:
        rdr=csv.DictReader(f)
        if not {"sample_id","stratum","openalex_id","ai_decision"}.issubset(
            rdr.fieldnames or []):
            raise ValueError("Sampling key fields missing")
        records=list(rdr)
    if len(records)!=368 or len({r["sample_id"] for r in records})!=368:
        raise ValueError("Key correspondence changed")
    codes={r["sample_id"]:r for r in records}
    counts=Counter(r["stratum"] for r in records)
    for stratum in STRATA:
        if counts[stratum]!=int(phase05["strata"][stratum]["sample_n"]):
            raise ValueError("Strata no longer match original Phase05 sample")
    if set(counts)!=set(STRATA):
        raise ValueError("Unrecognized sampling stratum")
    return codes


def validate_workbooks(original,returned,raters,phase22):
    result={}
    for section in ("DISCREPANCIAS","TODOS"):
        expected=parsed_rows(original[section],HEADERS[section],section)
        actual=parsed_rows(returned[section],HEADERS[section],section)
        if set(expected)!=set(actual):
            raise ValueError("Original sample records missing/added/renamed in "+section)
        allowed=set(VALID_COL)|{16} if section=="DISCREPANCIAS" else set()
        for key,old in expected.items():
            new=actual[key]
            for j in range(len(old)):
                if j not in allowed and new[j]!=old[j]:
                    raise ValueError("Source evidence or independent A/B ratings modified")
                if j in allowed and old[j]:
                    raise ValueError("Original blank adjudication template not blank")
        result[section]=actual
    everyone=result["TODOS"]
    disputed=result["DISCREPANCIAS"]
    if set(everyone)!=set(raters["a"]):
        raise ValueError("Returned worksheet differs from both reviewers")
    counts=Counter()
    for key,row in everyone.items():
        a,b=raters["a"][key],raters["b"][key]
        for j,f in enumerate(BASE_FIELDS):
            if row[j]!=a[f].strip() or row[j]!=b[f].strip():
                raise ValueError("Evidence mismatches Phase20 original reviewer sheets")
        original_scores=[a["relevance_code"],b["relevance_code"],
            a["discipline_code"],b["discipline_code"],
            a["primary_policy_code"],b["primary_policy_code"]]
        if row[5:11]!=original_scores:
            raise ValueError("Independent A/B ratings mismatched protected Phase20 files")
        flags=[row[5]!=row[6],row[7]!=row[8],row[9]!=row[10]]
        for field,flag in zip(("relevance","discipline","policy"),flags):
            counts[field]+=int(flag)
        if any(flags):
            counts["unique"]+=1
            if key not in disputed:
                raise ValueError("Disputed record missing from consensus workbook")
        elif key in disputed:
            raise ValueError("Unanimous record erroneously adjudicated")
        else:
            counts["original_no_disagreement"]+=1
    if len(disputed)!=int(phase22["counts"]["unique"]) or \
       any(counts[k]!=int(phase22["counts"][k]) for k in counts):
        raise ValueError("Returned screening does not match published Phase22 disagreement counts")
    for key,row in disputed.items():
        if row[:11]!=everyone[key]:
            raise ValueError("Disputed source evidence and independent ratings changed")
        for col,choices in VALID_COL.items():
            if row[col] and row[col] not in choices:
                raise ValueError("Consensus rating violates original rubric")
    return everyone,disputed,dict(counts)


def readiness(disputed):
    required={13:"relevance",14:"discipline",15:"policy",16:"reason"}
    result={}
    complete=True
    for col,name in required.items():
        filled=sum(bool(r[col]) for r in disputed.values())
        result[name]={"filled":filled,"total":len(disputed)}
        if filled<len(disputed):
            complete=False
    return result,complete


def assigned_consensus(everyone,disputed):
    all_scores={}
    counts=Counter()
    for key,row in everyone.items():
        if key in disputed:
            rec=disputed[key]
            fields=rec[13:16]
            counts["adjudicated"]+=1
        else:
            assert row[5]==row[6] and row[7]==row[8] and row[9]==row[10]
            fields=[row[5],row[7],row[9]]
            counts["unanimous_retained"]+=1
        if fields[0] not in VALID_RELEVANCE or \
           fields[1] not in VALID_DISCIPLINE or fields[2] not in VALID_POLICY:
            raise ValueError("Unrecognized adjudication classification")
        all_scores[key]=tuple(fields)
    return all_scores,dict(counts)


def stats_by_stratum(consensus,key,phase05):
    output={}
    for stratum in STRATA:
        values=[consensus[item["sample_id"]] for item in key.values()
                if item["stratum"]==stratum]
        n=len(values)
        output[stratum]={
            "n":n,
            "sampling_population_n":int(phase05["strata"][stratum]["population_n"]),
            "scope":("final_AI_screening_stratum" if stratum in SCREENING_STRATA
                else "earlier_bibliographic_filter_exclusion_NOT_AI_classifier_negative"),
            "relevance_counts":{k:sum(v[0]==k for v in values)
                                for k in ("0","1","2","3","9")},
            "discipline_counts":{k:sum(v[1]==k for v in values)
                                 for k in sorted(VALID_DISCIPLINE)},
            "policy_dimension_counts":{k:sum(v[2]==k for v in values)
                                       for k in sorted(VALID_POLICY)},
            "any_AI_higher_education_1plus_count":sum(v[0] in ("1","2","3") for v in values),
            "policy_at_least_indirect_2plus_count":sum(v[0] in ("2","3") for v in values),
            "direct_policy_3_count":sum(v[0]=="3" for v in values),
            "unresolved_9_count":sum(v[0]=="9" for v in values),
        }
    return output


def weighted_final_screening_prevalence(strata):
    # Planned Phase05 sampling is uniform SRS without replacement within
    # each of four final AI-screening decision classes, NOT the two
    # earlier bibliographic-filter exclusions.
    N=sum(strata[s]["sampling_population_n"] for s in SCREENING_STRATA)
    estimates={}
    for label,keys in {
        "outside_scope_0":["0"],
        "AI_education_non_policy_1":["1"],
        "policy_at_least_indirect_2plus":["2","3"],
        "direct_policy_3":["3"],
        "uncertain_9":["9"]
    }.items():
        fraction=0.0
        variance=0.0
        detail={}
        for s in SCREENING_STRATA:
            r=strata[s]
            n=r["n"]; pop=r["sampling_population_n"]
            if not (1<n<=pop):
                raise ValueError("Invalid sampling frame/population strata")
            y=sum(r["relevance_counts"][c] for c in keys)
            phat=y/n
            weight=pop/N
            fraction+=weight*phat
            variance+=weight*weight*(1-n/pop)*phat*(1-phat)/(n-1)
            detail[s]={"sample_n":n,"population_n":pop,
                       "observed_sample_cases":y}
        se=math.sqrt(max(variance,0))
        estimates[label]={
            "estimate":round(fraction,6),
            "approx_design_se":round(se,6),
            "approx_normal_95_ci_clipped":[round(max(0,fraction-1.96*se),6),
                                          round(min(1,fraction+1.96*se),6)],
            "denominator":"10,283 final-screening-pool records, including uncertain cases",
            "components":detail,
        }
    return {
        "status":"conditional_design_based_descriptive_estimate_NOT_classifier_accuracy",
        "target_final_screened_population_N":N,
        "assumptions":[
            "The four final AI-screening strata are disjoint and exhaustive over 10,283 screened records.",
            "The Phase05 samples were simple random samples without replacement within each stratum.",
            "Consensus reviewer codes measure title/abstract relevance, not an independent full-text truth standard.",
            "Unresolved 9 is a separate response class in the denominator; confidence intervals are approximate normal-design bounds, not formal claims of classifier performance.",
            "The earlier 11,393 q1_not_article_ready and 848 core_not_q1 records are NOT included in this screen-stage estimator and cannot be treated as machine negatives."
        ],
        "class_prevalence":estimates
    }


def quality_checks(everyone,disputed,consensus):
    by_field={}
    warnings=[]
    for name,(ca,cb,cf) in INDICES.items():
        conflicts=[r for r in disputed.values() if r[ca]!=r[cb]]
        choose_a=sum(r[cf]==r[ca] for r in conflicts)
        choose_b=sum(r[cf]==r[cb] for r in conflicts)
        third=len(conflicts)-choose_a-choose_b
        by_field[name]={"conflicting_cases":len(conflicts),
                        "adjudication_matches_A":choose_a,
                        "adjudication_matches_B":choose_b,
                        "adjudication_matches_neither":third}
        if len(conflicts)>=30 and choose_b/len(conflicts)>0.85:
            warnings.append("Large directional preference for reviewer B in "+name+
                           "; independent protocol/justification spot-check recommended")
    reasons=[r[16] for r in disputed.values()]
    unique=len(set(reasons))
    generic=sum(r.lower().startswith("relevancia coincidente") for r in reasons)
    all_out=[(key,v) for key,v in consensus.items() if v[0]=="0"]
    outscope_with_policy=sum(v[2] not in ("not_applicable","uncertain")
                             for _,v in all_out)
    if outscope_with_policy:
        warnings.append("Out-of-scope records have non-N/A policy labels; review taxonomy consistency")
    return {
        "conflicting_dimension_choice":by_field,
        "adjudicator_justification_unique_count":unique,
        "adjudicator_justifications_using_common_relevance_template_n":generic,
        "unresolved_relevance_9_count":sum(v[0]=="9" for v in consensus.values()),
        "outside_AI_HE_0_with_non_NA_policy_dimension":outscope_with_policy,
        "cautions":warnings,
        "interpretation":"Quality checks do not establish procedural independence, correctness or intentional bias."
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--original-xlsx",default=str(
        Path.home()/"ai_policy_screening_adjudicacion_privado/Adjudicacion_Cribado_Fase22.xlsx"))
    ap.add_argument("--returned-xlsx",required=True)
    ap.add_argument("--private-in",default=str(
        Path.home()/"ai_policy_screening_calificaciones_normalizadas_privado"))
    ap.add_argument("--phase05-report",default="reports/phase05/sample_aggregate.json")
    ap.add_argument("--phase21-report",default="reports/phase21/human_screening_agreement_aggregate.json")
    ap.add_argument("--phase22-report",default="reports/phase22/screening_adjudication_packet_aggregate.json")
    ap.add_argument("--out",default="reports/phase23")
    args=ap.parse_args()
    original=Path(args.original_xlsx).expanduser().resolve()
    returned=Path(args.returned_xlsx).expanduser().resolve()
    private=Path(args.private_in).expanduser().resolve()
    out=Path(args.out).expanduser().resolve()
    if original==returned or not original.is_file() or not returned.is_file() or not private.is_dir():
        ap.error("Original/returned private XLSX must be distinct, valid input files")
    for folder in (private,original.parent):
        if out==folder or folder in out.parents or out in folder.parents:
            ap.error("Public report destination must be separate from private sources")
    if out==returned.parent or out in returned.parent.parents:
        ap.error("Public output cannot be the same as or an ancestor of returned private files")
    phase05=json.loads(Path(args.phase05_report).read_text(encoding="utf8"))
    phase21=json.loads(Path(args.phase21_report).read_text(encoding="utf8"))
    phase22=json.loads(Path(args.phase22_report).read_text(encoding="utf8"))
    if phase05.get("sample_size")!=368 or \
       phase21.get("status")!="complete_independent_ratings_not_yet_adjudicated" or \
       phase22.get("status")!="screening_adjudication_packet_prepared_consensus_pending":
        raise ValueError("Previous validated Phase05,21,22 public reports not available")
    helper=excel_helper()
    base=sheet_data(original,helper)
    final=sheet_data(returned,helper)
    raters=read_original_raters(private)
    keys=read_private_key(private,phase05)
    everyone,disputed,counts=validate_workbooks(base,final,raters,phase22)
    if set(keys)!=set(everyone):
        raise ValueError("Private sampling keys differ from adjudicated sample")
    readiness_status,complete=readiness(disputed)
    report={
        "created_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
        "status":"completed_human_screening_adjudication_aggregate_QA_pending"
                 if complete else "awaiting_human_screening_adjudication",
        "integrity":{
            "original_template_unchanged":True,
            "reviewer_source_A_B_unchanged":True,
            "sample_and_strata_keys_verified_privately":True,
            "counts":counts,
        },
        "adjudication_readiness":readiness_status,
        "original_rater_agreement_reference":{
            "phase21_status":phase21.get("status"),
            "agreement_is_not_recomputed_or_overwritten":True,
        },
        "limitations":[
            "The adjudicator saw original A/B ratings; this reconciled result is NOT a third independent blinded evaluation.",
            "Descriptive human consensus on title/abstract does not constitute a definitive full-text inclusion truth standard.",
            "Sampling is intentionally stratified; unweighted pooled accuracy, precision/recall, or prevalence would be misleading.",
            "Early q1_not_article_ready/core_not_q1 filter exclusions are NOT machine classifier negatives.",
            "Unresolved relevance score 9 must not be silently forced into any binary class.",
            "Preferential selection of one reviewer may warrant independent quality review of decisions, rubric compliance and evidence before publication.",
            "No private identifiers, text, individual ratings, consensus reasons or per-item machine labels are published.",
        ]
    }
    if complete:
        consensus,origin_counts=assigned_consensus(everyone,disputed)
        stratum_table=stats_by_stratum(consensus,keys,phase05)
        report["results"]={
            "human_consensus_source":origin_counts,
            "per_stratum_descriptive_counts":stratum_table,
            "weighted_four_screening_strata":weighted_final_screening_prevalence(stratum_table),
            "adjudication_quality_diagnostics":quality_checks(everyone,disputed,consensus),
            "classifier_performance_status":"NOT_COMPUTED_no_silent_mapping_of_multi_class_screen_to_binary_truth"
        }
    out.mkdir(parents=True,exist_ok=True)
    filename=out/"adjudicated_screening_aggregate.json"
    filename.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    summary=[
        "# Phase 23 — Human adjudicated screening and stratified diagnostics",
        "","Status: "+report["status"],"",
        "## Completeness",json.dumps(readiness_status,indent=2),"",
        "## Input integrity",json.dumps(report["integrity"],indent=2)
    ]
    if "results" in report:
        summary+=["","## Public aggregate results only",
                  json.dumps(report["results"],indent=2)]
    summary+=["","## Limitations"]+["- "+x for x in report["limitations"]]
    (out/"summary.md").write_text("\n".join(summary)+"\n",encoding="utf8")
    print("PHASE23",report["status"])
    for label,stat in readiness_status.items():
        print("Human adjudicator",label,stat["filled"],"/",stat["total"])
    if "results" in report:
        print("Consensus records:",len(everyone),
              "adjudicated:",origin_counts["adjudicated"],
              "unanimous A/B retained:",origin_counts["unanimous_retained"])
        print("QA warnings:",
              len(report["results"]["adjudication_quality_diagnostics"]["cautions"]))
    print("PUBLIC AGGREGATE:",filename)
    print("NO individual records or private reviewer judgments were exported")


if __name__=="__main__":
    main()
