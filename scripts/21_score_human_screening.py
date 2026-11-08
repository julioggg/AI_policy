#!/usr/bin/env python3
"""Phase21 — screening expert agreement and stratum diagnostics, AGGREGATES ONLY.

Reads two independent real Phase20 reviewer CSVs and the private Phase05
stratum/AI-screening key on CEDIA; emits aggregate agreement and per-stratum
descriptives to reports/phase21. No reviewer texts, item codes, article IDs,
machine decisions linked to an article, or titles are published.

Unresolved 9 is excluded from ordinal relevance Cohen kappa. Agreement does
NOT establish final screening validity, recall or classifier precision.
Early Q1/core-filter exclusion strata are NOT final AI-classifier negatives.
"""
from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import json
import math
from pathlib import Path

from sklearn.metrics import cohen_kappa_score

FIELDS=("sample_id","title","abstract","publication_year","type",
        "relevance_code","discipline_code","primary_policy_code","reason")
READONLY=("sample_id","title","abstract","publication_year","type")
RELEVANCE=("0","1","2","3","9")
DISCIPLINES=("ssh","engineering","health_sciences","general_he","uncertain")
POLICIES=("teaching_learning","assessment","ethics_integrity",
          "governance_policy","research_scholarship","ai_literacy_training",
          "equity_access","privacy_security","general_policy",
          "not_applicable","uncertain")
STRATA=("screen_include_core","screen_include_policy",
        "screen_include_context","screen_exclude",
        "q1_not_article_ready","core_not_q1")
KEY_FIELDS=("sample_id","stratum","openalex_id","ai_decision",
            "original_policy_dimension","original_disciplinary_area")


def read_csv(path,fields):
    if not path.is_file():
        raise FileNotFoundError("Private required input missing")
    with path.open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        if not set(fields).issubset(set(reader.fieldnames or [])):
            raise ValueError("Required Phase21 input columns are missing")
        raw=list(reader)
    if len(raw)!=368:
        raise ValueError("Expected exactly 368 Phase05 screening records")
    if len({r["sample_id"] for r in raw})!=368 or \
       any(not r["sample_id"] for r in raw):
        raise ValueError("Duplicate or blank blinded record keys")
    return {r["sample_id"]:r for r in raw}


def nint(x):
    return int(x) if x is not None else 0


def kappa(x,y,valid,weighted=None):
    paired=[(a,b) for a,b in zip(x,y) if a in valid and b in valid]
    out={"paired_evaluable":len(paired),
         "not_jointly_evaluable":len(x)-len(paired),
         "agreement":None,"disagreements":None,"cohen_kappa":None}
    if not paired:
        return out
    a,b=zip(*paired)
    out["agreement"]=round(sum(i==j for i,j in paired)/len(paired),5)
    out["disagreements"]=sum(i!=j for i,j in paired)
    try:
        score=float(cohen_kappa_score(a,b,labels=list(valid),
                         weights=weighted))
        if math.isfinite(score):
            out["cohen_kappa"]=round(score,5)
    except ValueError:
        pass
    return out


def countdict(xs,options):
    counter=collections.Counter(xs)
    return {k:counter.get(k,0) for k in options}


def rates(a,b,codes):
    return {
        "rater_a":countdict(a,codes),
        "rater_b":countdict(b,codes),
        "full_sample_exact_agreement":round(sum(x==y for x,y in zip(a,b))/len(a),5)
            if a else None,
        "all_including_uncertain_disagreements":sum(x!=y for x,y in zip(a,b)),
    }


def check_complete(reviews):
    result={}
    for label,data in reviews.items():
        status={}
        for field,allowed in (("relevance_code",RELEVANCE),
                              ("discipline_code",DISCIPLINES),
                              ("primary_policy_code",POLICIES)):
            vals=[r[field].strip() for r in data.values()]
            if any(value and value not in allowed for value in vals):
                raise ValueError("Screening rubric violation, in "+field)
            status[field]={"filled":sum(bool(v) for v in vals),
                           "total":len(vals)}
        status["reason"]={"filled":sum(bool(r["reason"].strip()) for r in data.values()),
                          "total":len(data)}
        result[label]=status
    return result


def analyze(reviews,key,sample_report):
    ia,ib=reviews["a"],reviews["b"]
    ids=set(ia)
    if set(ib)!=ids or set(key)!=ids:
        raise ValueError("Reviewer and private sampling IDs differ")
    if any(any(ia[id][f]!=ib[id][f] for f in READONLY)
           for id in ids):
        raise ValueError("Immutable sampling evidence differs between reviewers")
    if any(key[k]["stratum"] not in STRATA for k in key):
        raise ValueError("Unsupported private sampling stratum")
    expected=sample_report.get("strata",{})
    for stratum in STRATA:
        observed=sum(k["stratum"]==stratum for k in key.values())
        if stratum not in expected or observed!=int(expected[stratum]["sample_n"]):
            raise ValueError("Protected sample differs from Phase05 reported strata")

    readiness=check_complete(reviews)
    complete=all(x["filled"]==x["total"] for r in readiness.values() for x in r.values())
    return readiness,(scored(reviews,key) if complete else None)


def scored(reviews,key):
    ia,ib=reviews["a"],reviews["b"]
    ordered=sorted(key)
    def pair(field,subset):
        return ([ia[k][field].strip() for k in subset],
                [ib[k][field].strip() for k in subset])
    relevance=pair("relevance_code",ordered)
    discipline=pair("discipline_code",ordered)
    policy=pair("primary_policy_code",ordered)
    overview={
        "relevance":{
            **rates(*relevance,RELEVANCE),
            "ordinal_0_to_3_unweighted":kappa(*relevance,RELEVANCE[:4]),
            "ordinal_0_to_3_quadratic_weighted":kappa(
                *relevance,RELEVANCE[:4],weighted="quadratic"),
            "any_uncertain_9":sum(a=="9" or b=="9" for a,b in zip(*relevance))
        },
        "discipline":{
            **rates(*discipline,DISCIPLINES),
            "nominal_kappa_with_uncertain_as_category":kappa(*discipline,DISCIPLINES)
        },
        "primary_policy_dimension":{
            **rates(*policy,POLICIES),
            "nominal_kappa_with_uncertain_as_category":kappa(*policy,POLICIES)
        }
    }
    strata={}
    for stratum in STRATA:
        items=[id for id in ordered if key[id]["stratum"]==stratum]
        r=pair("relevance_code",items)
        d=pair("discipline_code",items)
        p=pair("primary_policy_code",items)
        strata[stratum]={
            "sample_n":len(items),
            "relevance_distribution":{
                "a":countdict(r[0],RELEVANCE),
                "b":countdict(r[1],RELEVANCE)},
            "relevance_agreement":kappa(*r,RELEVANCE[:4],weighted="quadratic"),
            "relevance_exact_with_9":round(
                 sum(a==b for a,b in zip(*r))/len(r[0]),5),
            "discipline_agreement":kappa(*d,DISCIPLINES),
            "policy_dimension_agreement":kappa(*p,POLICIES),
            "scope":("previous_bibliographic_filter_exclusion_NOT_AI_classifier_negative"
                     if stratum in ("q1_not_article_ready","core_not_q1")
                     else "final_AI_screening_stratum")
        }
    return {"overall_inter_rater":overview,
            "stratified_review_summary":strata,
            "flagged_for_human_adjudication":{
                "any_relevance_disagreement":overview["relevance"]["all_including_uncertain_disagreements"],
                "any_discipline_disagreement":overview["discipline"]["all_including_uncertain_disagreements"],
                "any_policy_dimension_disagreement":overview["primary_policy_dimension"]["all_including_uncertain_disagreements"],
                "unique_records_disagreeing_in_one_or_more_fields":sum(
                    any(ia[id][f].strip()!=ib[id][f].strip()
                        for f in ("relevance_code","discipline_code","primary_policy_code"))
                    for id in ordered)
            },
            "classifier_accuracy_status":"NO_GOLD_STANDARD_YET_independent_human_ratings_require_adjudication"}


def public_write(out,report):
    out.mkdir(parents=True,exist_ok=True)
    (out/"human_screening_agreement_aggregate.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    lines=[
        "# Phase 21 — Human screening agreement, before adjudication",
        "","Status: "+report["status"],
        "UTC: "+report["created_utc"],
        "","## Rating completeness",
        json.dumps(report["readiness"],indent=2),
    ]
    if "results" in report:
        lines+=["","## Agreement and strata (aggregate only)",
                json.dumps(report["results"],indent=2)]
    lines+=["","## Limits"]+["- "+x for x in report["limitations"]]
    (out/"summary.md").write_text("\n".join(lines)+"\n",encoding="utf8")


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--private-in",default=str(
       Path.home()/"ai_policy_screening_calificaciones_normalizadas_privado"))
    parser.add_argument("--phase05-report",default="reports/phase05/sample_aggregate.json")
    parser.add_argument("--out",default="reports/phase21")
    args=parser.parse_args()
    root=Path(args.private_in).expanduser().resolve()
    out=Path(args.out).expanduser().resolve()
    repo=Path.home()/"AI_policy"
    if not root.is_dir() or root==repo or repo in root.parents or \
       out==root or root in out.parents or out in root.parents:
        parser.error("Public report and private human ratings require disjoint directories")
    sample=json.loads(Path(args.phase05_report).read_text(encoding="utf8"))
    if sample.get("sample_size")!=368:
        raise ValueError("Original Phase05 report did not describe 368 items")
    reviews={r:read_csv(root/("rater_"+r+".csv"),FIELDS) for r in ("a","b")}
    key=read_csv(root/"sampling_key.csv",KEY_FIELDS)
    readiness,results=analyze(reviews,key,sample)
    status=("complete_independent_ratings_not_yet_adjudicated"
            if results is not None else "awaiting_two_human_screening_ratings")
    report={
        "created_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
        "status":status,
        "sample":{"n":368,"strata":{k:int(sample["strata"][k]["sample_n"]) for k in STRATA}},
        "readiness":readiness,
        "limitations":[
            "The two screening forms are computationally comparable, but independence of human judgment is a procedural assertion that code cannot verify.",
            "Agreement between human coders does not establish an external gold standard, an unbiased classifier recall, precision, or screening validity.",
            "Ordinal relevance κ excludes 9=uncertain. All-record exact agreement includes 9 as a scored category and is shown separately.",
            "Discipline and policy dimension are nominal with uncertain treated as a category; their kappa must not be compared numerically to ordinal weighted relevance kappa as if identical.",
            "The 368-record sample deliberately oversamples minority classes and early-filter exclusions. Aggregate per-stratum distributions are NOT population prevalences.",
            "The Q1/refinement and core-to-Q1 exclusion strata are bibliographic-filter exclusions, NOT final AI-screening negatives.",
            "Machine labels are excluded from this independent agreement report. A subsequent human adjudication should precede any model-vs-human validity analysis.",
            "Assessing title/abstract alone is not a full-text relevance or risk-of-bias judgment.",
            "Only counts and agreement are published; raw titles, abstracts, comments, decisions linked to records, identifiers and private sampling keys remain on CEDIA."
        ]}
    if results is not None:
        report["results"]=results
    public_write(out,report)
    print("PHASE21",status)
    for person in ("a","b"):
        for field,value in readiness[person].items():
            print("Rater",person,field,value["filled"],"/",value["total"])
    if results is not None:
        print("Unique records with any rater disagreement:",
           results["flagged_for_human_adjudication"]["unique_records_disagreeing_in_one_or_more_fields"])
    print("Public aggregated results:",out/"human_screening_agreement_aggregate.json")
    print("Never push private CSV ratings or sample key to GitHub")


if __name__=="__main__":
    main()
