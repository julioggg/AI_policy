#!/usr/bin/env python3
"""Phase31 supplemental analysis: TWO Claude AI passes, NEVER human reviewers.

The two spreadsheets contain explicit independent AI-pass disclosures in their
INSTRUCCIONES sheet. This script refuses to score them as human observations.
It checks their immutable source data against the ORIGINAL blank Phase30
workbooks, validates coded responses, verifies private frozen SHA256 manifest
and publishes aggregate AI-to-AI reproducibility ONLY.

Does NOT evaluate algorithmic accuracy, precision, recall, human validity,
procedural AI independence, or adjudicate individual scores.
Private source text, codes, matching keys and AI decisions remain on CEDIA.
"""
from __future__ import annotations

import argparse
from collections import Counter
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import re

from sklearn.metrics import cohen_kappa_score, confusion_matrix

N=1200
FIELDS=[
 "validation_code","title","abstract","publication_year","type",
 "scope_code","relevance_code","primary_topic","primary_discipline",
 "policy_mechanism","evidence_excerpt","fulltext_required","reason"
]
ALLOWED={
 "scope_code":{"0","1","9"},
 "relevance_code":{"0","1","2","3","9"},
 "primary_topic":{
  "teaching_learning","assessment","ethics_integrity","governance_policy",
  "research_scholarship","ai_literacy_training","equity_access",
  "privacy_security","general_policy","not_applicable","uncertain"},
 "primary_discipline":{"ssh","engineering","health_sciences","general_he","uncertain"},
 "fulltext_required":{"yes","no"}
}
FIELDCOLS={name:j for j,name in enumerate(FIELDS)}
COMPARE=("scope_code","relevance_code","primary_topic",
         "primary_discipline","fulltext_required")


def sha256(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for buf in iter(lambda:f.read(1048576),b""):
            h.update(buf)
    return h.hexdigest()


def reader():
    import importlib.util
    p=Path(__file__).resolve().parent/"25_compare_independent_screening_qa.py"
    spec=importlib.util.spec_from_file_location("phase31_reader",p)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def load_book(path,phase30,provenance=None):
    tabs=reader().xlsx_sheets(path,{"INSTRUCCIONES","VALIDACION"})
    ins=tabs["INSTRUCCIONES"]
    statement=str(ins[0].get(1,"")).strip() if ins else ""
    if provenance is not None:
        if (f"PASADA IA-{provenance}" not in statement or
            "Claude" not in statement or
            "NO es una evaluación humana" not in statement):
            raise ValueError("AI pass provenance is missing or misleading")
    else:
        if "EVALUADOR" not in statement.upper() or "PASADA IA" in statement.upper():
            raise ValueError("The original source workbook is not a pristine human-review form")
    raw=tabs["VALIDACION"]
    if not raw or [str(raw[0].get(i,"")).strip() for i in range(13)]!=phase30.HEADERS:
        raise ValueError("Nonstandard Phase30 screen headers")
    keys={}
    for line in raw[1:]:
        if not any(str(x).strip() for x in line.values()): continue
        if any(j>=13 and str(v).strip() for j,v in line.items()):
            raise ValueError("Unexpected additional source/label columns")
        row=[str(line.get(i,"")).strip() if line.get(i) is not None else ""
             for i in range(13)]
        key=row[0]
        if not re.fullmatch(r"VAL\d{4}",key) or key in keys:
            raise ValueError("Duplicate/invalid masked validation identifier")
        keys[key]=row
    if len(keys)!=N:
        raise ValueError("A complete Phase30 AI-pass file must have exactly 1200 codes")
    return keys


def validate(run,source):
    if set(run)!=set(source):
        raise ValueError("AI run does not match original masked sample codes")
    count=Counter()
    for key,row in run.items():
        if row[:5]!=source[key][:5]:
            raise ValueError("Source title, abstract, year, type or validation code modified")
        if any(source[key][j] for j in range(5,13)):
            raise ValueError("Original human review template was not blank")
        for field,allowed in ALLOWED.items():
            if row[FIELDCOLS[field]] not in allowed:
                raise ValueError("AI run has missing/out-of-rubric "+field)
        if not row[10] or not row[12]:
            raise ValueError("AI rationale or source evidence missing")
        s,r=row[5:7]
        if (s=="0" and r!="0" or s=="9" and r!="9" or
            s=="1" and r=="0" or r=="0" and s!="0"):
            raise ValueError("Inconsistent scope/relevance codes")
        if r in ("2","3") and not row[9]:
            raise ValueError("Relevance R2/R3 without required institutional mechanism")
        if r=="9" and row[11]!="yes":
            raise ValueError("Uncertain R9 requires full-text escalation")
        count["uncertain_relevance_9"]+=int(r=="9")
        count["policy_mechanism_filled"]+=int(bool(row[9]))
        count["evidence_filled"]+=int(bool(row[10]))
        count["justification_filled"]+=int(bool(row[12]))
    return dict(count)


def kappa(x,y,labels,weights=None):
    v=float(cohen_kappa_score(x,y,labels=labels,weights=weights))
    return round(v,5) if math.isfinite(v) else None


def comparison(run1,run2):
    keys=sorted(run1)
    result={}
    for name in COMPARE:
        pos=FIELDCOLS[name]
        a=[run1[key][pos] for key in keys]
        b=[run2[key][pos] for key in keys]
        same=sum(x==y for x,y in zip(a,b))
        labels=sorted(set(a)|set(b))
        res={
            "n":N,
            "exact_agreement_n":same,
            "disagreement_n":N-same,
            "exact_agreement_fraction":round(same/N,5),
            "cohen_kappa_including_uncertainty_as_nominal_category":kappa(a,b,labels),
            "distribution_AI1":dict(sorted(Counter(a).items())),
            "distribution_AI2":dict(sorted(Counter(b).items())),
        }
        if name=="relevance_code":
            valid=[(x,y) for x,y in zip(a,b) if x!="9" and y!="9"]
            xx=[x for x,_ in valid]; yy=[y for _,y in valid]
            res.update({
                "jointly_ordinal_0_3_n":len(valid),
                "excluded_if_either_uncertain_9_n":N-len(valid),
                "exact_agreement_in_ordinal_n":sum(x==y for x,y in valid),
                "kappa_ordinal_unweighted":kappa(xx,yy,["0","1","2","3"]),
                "kappa_ordinal_quadratic":kappa(xx,yy,["0","1","2","3"],"quadratic"),
                "contingency_matrix_0_1_2_3_9":confusion_matrix(
                    a,b,labels=["0","1","2","3","9"]).tolist()
            })
        result[name]=res
    result["any_difference_in_five_fields_n"]=sum(
        any(run1[key][FIELDCOLS[c]]!=run2[key][FIELDCOLS[c]] for c in COMPARE)
        for key in keys)
    result["any_difference_in_four_scientific_fields_n"]=sum(
        any(run1[key][FIELDCOLS[c]]!=run2[key][FIELDCOLS[c]]
            for c in COMPARE if c!="fulltext_required")
        for key in keys)
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--original-a",default=str(Path.home()/"ai_policy_validation1200_private/Validacion_1200_A.xlsx"))
    p.add_argument("--original-b",default=str(Path.home()/"ai_policy_validation1200_private/Validacion_1200_B.xlsx"))
    p.add_argument("--ai1",required=True)
    p.add_argument("--ai2",required=True)
    p.add_argument("--manifest",default=str(Path.home()/"ai_policy_validation1200_private/private_locked_manifest.json"))
    p.add_argument("--codebook",default="docs/phase30_full_validation_codebook_v1.0.md")
    p.add_argument("--phase30-report",default="reports/phase30/full_validation_packet_aggregate.json")
    p.add_argument("--out",default="reports/phase31")
    args=p.parse_args()
    paths={
        "original_a":Path(args.original_a).expanduser().resolve(),
        "original_b":Path(args.original_b).expanduser().resolve(),
        "ai1":Path(args.ai1).expanduser().resolve(),
        "ai2":Path(args.ai2).expanduser().resolve(),
        "manifest":Path(args.manifest).expanduser().resolve(),
        "codebook":Path(args.codebook).expanduser().resolve(),
    }
    dest=Path(args.out).expanduser().resolve()
    if len({str(paths[x]) for x in ("original_a","original_b","ai1","ai2")})!=4:
        p.error("AI uploads must be distinct from two original blank human forms")
    if any(not x.is_file() for x in paths.values()):
        p.error("Original template, two AI runs, codebook or private manifest missing")
    for x in paths.values():
        if dest==x.parent or x.parent in dest.parents or dest in x.parents:
            p.error("No public report in an input's private directory")
    if dest.exists() and any(dest.iterdir()):
        p.error("Phase31 has already been published; never overwrite historical audit")
    manifest=json.loads(paths["manifest"].read_text(encoding="utf8"))
    phase30=json.loads(Path(args.phase30_report).read_text(encoding="utf8"))
    if (manifest.get("status")!="prepared_full1200_two_blind_expert_workbooks_NO_human_ratings" or
        phase30.get("sample_n")!=1200 or phase30.get("human_assessments_completed")!=0):
        raise ValueError("Invalid original Phase30 protocol")
    if sha256(paths["codebook"])!=manifest.get("codebook_sha256"):
        raise ValueError("Original validation codebook checksum changed")
    for k in ("A","B"):
        if sha256(paths["original_"+k.lower()])!=manifest["pristine_workbook_sha256"][k]:
            raise ValueError("Original blank reviewer form checksum differs from locked manifest")
    import importlib.util
    spec=importlib.util.spec_from_file_location("phase30_source",
        Path(__file__).resolve().parent/"30_prepare_full1200_validation.py")
    phase30_source=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(phase30_source)
    original_a=load_book(paths["original_a"],phase30_source)
    original_b=load_book(paths["original_b"],phase30_source)
    if set(original_a)!=set(original_b) or any(
        original_a[k][:5]!=original_b[k][:5] for k in original_a):
        raise ValueError("Frozen Phase30 original A/B books have inconsistent source evidence")
    a=load_book(paths["ai1"],phase30_source,provenance="1")
    b=load_book(paths["ai2"],phase30_source,provenance="2")
    integrity1=validate(a,original_a)
    integrity2=validate(b,original_a)
    stats=comparison(a,b)
    report={
        "generated_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
        "status":"two_Claude_AI_passes_audited_NOT_independent_human_validation",
        "n_records":N,
        "source_original_phase30_template_verified":True,
        "source_data_immutable_against_original":True,
        "original_codebook_hash_verified":True,
        "runs":{
            "AI1":{"self_declared_source":"Claude-generated AI classification, not human","rubric_validity":integrity1},
            "AI2":{"self_declared_source":"Claude-generated AI classification, not human","rubric_validity":integrity2},
        },
        "ai_to_ai_agreement":stats,
        "limitations":[
            "Both documents explicitly self-identify as separate Claude AI classification passes, NOT human expert validation.",
            "The actual model invocation, independence of execution, context leakage and human-free production cannot be established computationally.",
            "High agreement between two passes of a related model is reproducibility/consistency, NOT ground-truth accuracy, precision, recall or validity.",
            "No comparison with adjudicated human reference is performed.",
            "The 1,200 records were probability-sampled from four final AI-screening strata; AI-pass agreement in this deliberately disproportionate sample is descriptive and not population-weighted.",
            "No article-level ratings, texts, bibliographic identifiers, confidential sample keys or original AI predictions are published."
        ],
        "next":"Obtain two actually human-completed reviewer forms and compare them independently against the frozen Phase30 source; only then adjudicate and calculate design-weighted classifier validation."
    }
    dest.mkdir(parents=True,exist_ok=True)
    (dest/"two_ai_runs_agreement_aggregate.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    (dest/"summary.md").write_text(
        "# Phase31 — Supplemental two-Claude-pass reproducibility audit (NOT human validation)\n\n"+
        "**Status:** "+report["status"]+"\n\n"+
        "## Public aggregate concordance\n\n"+
        json.dumps(stats,ensure_ascii=False,indent=2)+"\n\n"+
        "## Limits\n\n"+"\n".join("- "+x for x in report["limitations"])+"\n",
        encoding="utf8")
    print("PHASE31",report["status"])
    for key,value in stats.items():
        if isinstance(value,dict) and "exact_agreement_n" in value:
            print(key,value["exact_agreement_n"],"/1200, kappa",value[
                "cohen_kappa_including_uncertainty_as_nominal_category"])
    print("All five field differences:",stats["any_difference_in_five_fields_n"])
    print("PUBLIC aggregate:",dest/"two_ai_runs_agreement_aggregate.json")
    print("Original two human review templates remain blank; NO HUMAN VALIDATION implied.")


if __name__=="__main__":
    main()
