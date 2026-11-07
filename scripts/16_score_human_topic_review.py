#!/usr/bin/env python3
"""Phase 16 — evaluate two INDEPENDENT human topic ratings (no fabricated coding).

Run after Phase15 sampling, first for readiness (blank forms allowed), then
after both researchers finish their protected CSV copies. All private document
examples, model keys, labels and reviewer comments stay on CEDIA. GitHub gets
aggregate statistics ONLY. No model is declared "best" automatically.

Uses pandas, numpy, sklearn; source project is never edited.
"""
from __future__ import annotations
import argparse
import collections
import datetime as dt
import json
import math
import os
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score

TOPIC_FIELDS = {
    "topic_name_proposed": "text",
    "topic_coherence_1_to_5": (1,2,3,4,5),
    "distinctiveness_1_to_5": (1,2,3,4,5),
    "direct_policy_relevance_0_to_3_or_9": (0,1,2,3,9),
    "confidence_1_to_5": (1,2,3,4,5),
}
DOC_FIELDS = {
    "belongs_to_one_coherent_theme_0_no_1_yes_9_uncertain": (0,1,9),
    "policy_relevance_0_to_3_or_9_uncertain": (0,1,2,3,9),
}
TOPIC_CODES = ("group_code",)
DOC_CODES = ("group_code","item_code")


def clean_numeric(s, allowed, file_kind):
    z=s.fillna("").astype(str).str.strip()
    n=pd.to_numeric(z.replace("",np.nan),errors="coerce")
    bad=z.ne("") & (~n.isin(allowed))
    if bad.any():
        # Never echo an entered label, text, item code or private filename.
        raise ValueError("Unexpected numeric rating outside agreed rubric in "+file_kind)
    return n


def read_ratings(private):
    frames={}
    for person in ("a","b"):
        for section,codes,fields in (
            ("topics",TOPIC_CODES,TOPIC_FIELDS),
            ("documents",DOC_CODES,DOC_FIELDS)
        ):
            path=private/("rater_"+person+"_"+section+".csv")
            if not path.is_file():
                raise FileNotFoundError("Missing protected rater "+person+" "+section+" sheet")
            tab=pd.read_csv(path,dtype=str,encoding="utf-8-sig").fillna("")
            required=set(codes)|set(fields)
            if not required.issubset(tab.columns):
                raise ValueError("Required rating columns absent from "+section+" workbook")
            for code in codes:
                if tab[code].astype(str).str.strip().eq("").any():
                    raise ValueError("Blank correspondence code in "+section+" workbook")
            if tab.duplicated(list(codes)).any():
                raise ValueError("Duplicated group or item codes in "+section+" workbook")
            for field,rules in fields.items():
                if rules != "text":
                    tab[field]=clean_numeric(tab[field],rules,section)
                else:
                    tab[field]=tab[field].astype(str).str.strip()
            frames[(person,section)]=tab
    return frames


def private_key_verify(private,frames,manifest):
    path=private/"private_sampling_key.csv"
    if not path.is_file():
        raise FileNotFoundError("Private sampling key unavailable")
    key=pd.read_csv(path,dtype=str,encoding="utf-8-sig").fillna("")
    for field in ("group_code","item_code","modality","k","cluster_label",
                  "phase14_row_index","openalex_id","sampling_role"):
        if field not in key:
            raise ValueError("Private key missing expected field")
    if key.duplicated(["group_code","item_code"]).any():
        raise ValueError("Duplicate group/item pairs in private key")
    groups=set(key["group_code"])
    if len(groups)!=int(manifest["n_groups"]) or \
       len(key)!=int(manifest["n_document_assessments_per_rater"]):
        raise ValueError("Private correspondence key does not match manifest counts")
    group_info=key.groupby("group_code").agg({
        "modality":"nunique","k":"nunique","cluster_label":"nunique"
    })
    if (group_info!=1).any().any():
        raise ValueError("Private key maps a blinded group to multiple models/topics")
    reference=set(zip(key["group_code"],key["item_code"]))
    for person in ("a","b"):
        docs=frames[(person,"documents")]
        topics=frames[(person,"topics")]
        if set(zip(docs["group_code"],docs["item_code"]))!=reference:
            raise ValueError("Document reviewer sheets differ from approved Phase15 items")
        if set(topics["group_code"])!=groups:
            raise ValueError("Reviewer topic sheets differ from approved Phase15 groups")
        if len(docs)!=len(reference) or len(topics)!=len(groups):
            raise ValueError("Unexpected row count in human rating sheet")
    # Expose the keys only inside runtime; no article IDs or group names in reports.
    return key


def valid_count(tab,fields):
    output={}
    for field,choices in fields.items():
        if choices=="text":
            output[field]={"filled":int(tab[field].ne("").sum()),
                           "total":len(tab)}
        else:
            values=tab[field]
            output[field]={"filled":int(values.notna().sum()),
                           "total":len(tab),
                           "uncertain_9":int((values==9).sum()) if 9 in choices else None}
    return output


def kappa_safe(a,b,valid_labels,weights=None):
    x=np.asarray(a,dtype=float);y=np.asarray(b,dtype=float)
    eligible=np.isfinite(x)&np.isfinite(y)&np.isin(x,valid_labels)&np.isin(y,valid_labels)
    x=x[eligible].astype(int); y=y[eligible].astype(int)
    out={"paired_evaluable":int(len(x)),
         "differing_ratings":int((x!=y).sum())}
    if not len(x):
        out["cohen_kappa"]=None
        out["exact_agreement_fraction"]=None
        return out
    out["exact_agreement_fraction"]=round(float(np.mean(x==y)),5)
    with np.errstate(invalid="ignore",divide="ignore"):
        value=cohen_kappa_score(x,y,labels=list(valid_labels),weights=weights)
    out["cohen_kappa"]=round(float(value),5) if np.isfinite(value) else None
    return out


def series_summary(values):
    nums=pd.to_numeric(values,errors="coerce")
    nums=nums[np.isfinite(nums)]
    if nums.empty:
        return {"n":0,"mean":None,"median":None}
    return {"n":len(nums),
            "mean":round(float(nums.mean()),5),
            "median":round(float(nums.median()),5),
            "sd":round(float(nums.std(ddof=1)),5) if len(nums)>1 else None}


def modality_name(key):
    return key["modality"].astype(str)+"_k"+key["k"].astype(str)


def evaluate(frames,key):
    model_by_group=key[["group_code","modality","k"]].drop_duplicates("group_code")
    model_by_group["candidate"]=modality_name(model_by_group)
    # Never write per-group rows out; the joining key and article titles stay private.
    ta=frames[("a","topics")][["group_code"]+list(TOPIC_FIELDS)].copy()
    tb=frames[("b","topics")][["group_code"]+list(TOPIC_FIELDS)].copy()
    da=frames[("a","documents")][list(DOC_CODES)+list(DOC_FIELDS)].copy()
    db=frames[("b","documents")][list(DOC_CODES)+list(DOC_FIELDS)].copy()
    topics=ta.merge(tb,on="group_code",suffixes=("_a","_b"),validate="one_to_one")
    docs=da.merge(db,on=list(DOC_CODES),suffixes=("_a","_b"),validate="one_to_one")
    topics=topics.merge(model_by_group[["group_code","candidate"]],
                        on="group_code",validate="one_to_one")
    docs=docs.merge(model_by_group[["group_code","candidate"]],
                    on="group_code",validate="many_to_one")
    totals={}
    for field,rules in TOPIC_FIELDS.items():
        if rules!="text":
            valid=[k for k in rules if k!=9]
            totals["topic_"+field]=kappa_safe(topics[field+"_a"],topics[field+"_b"],
                    valid,weights="quadratic" if len(valid)>2 else None)
    for field,rules in DOC_FIELDS.items():
        valid=[k for k in rules if k!=9]
        totals["document_"+field]=kappa_safe(docs[field+"_a"],docs[field+"_b"],
                    valid,weights="quadratic" if len(valid)>2 else None)
    candidate_results={}
    for model in sorted(model_by_group["candidate"].unique()):
        t=topics.loc[topics["candidate"]==model]
        d=docs.loc[docs["candidate"]==model]
        summary={"groups":int(len(t)),"document_evaluations_per_rater":int(len(d)),
                 "topic_rater_means":{},"document_rater_means":{}}
        for field,rules in TOPIC_FIELDS.items():
            if rules=="text":
                summary["named_topics_by_rater"]={
                    "a":int(t[field+"_a"].ne("").sum()),
                    "b":int(t[field+"_b"].ne("").sum())}
                continue
            for person in ("a","b"):
                v=t[field+"_"+person]
                if 9 in rules:
                    v=v.where(v!=9)
                summary["topic_rater_means"][field+"_"+person]=series_summary(v)
            permitted=[n for n in rules if n!=9]
            summary["topic_rater_means"][field+"_kappa"]=kappa_safe(
                t[field+"_a"],t[field+"_b"],permitted,
                weights="quadratic" if len(permitted)>2 else None)
        for field,rules in DOC_FIELDS.items():
            for person in ("a","b"):
                v=d[field+"_"+person].where(d[field+"_"+person]!=9)
                summary["document_rater_means"][field+"_"+person]=series_summary(v)
            permitted=[n for n in rules if n!=9]
            summary["document_rater_means"][field+"_kappa"]=kappa_safe(
                d[field+"_a"],d[field+"_b"],permitted,
                weights="quadratic" if len(permitted)>2 else None)
        candidate_results[model]=summary
    return {"overall_inter_rater_agreement":totals,
            "candidate_descriptive_comparison":candidate_results}


def public_write(out,result):
    out.mkdir(parents=True,exist_ok=True)
    (out/"human_topic_review_aggregate.json").write_text(
        json.dumps(result,indent=2,ensure_ascii=False),encoding="utf8")
    lines=["# Phase 16 — Human topic review and inter-rater reliability",
           "","Status: "+result["status"],
           "UTC: "+result["created_utc"],"",
           "## Human rating readiness",
           json.dumps(result["readiness"],ensure_ascii=False,indent=2)]
    if "results" in result:
        lines+=["","## Evaluations (completed forms only)",
                json.dumps(result["results"],ensure_ascii=False,indent=2)]
    lines+=["","## Interpretation limits"]
    lines+=["- "+x for x in result["limitations"]]
    (out/"summary.md").write_text("\n".join(lines)+"\n",encoding="utf8")


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--private-in",default=str(Path.home()/"ai_policy_topic_validation_private"))
    ap.add_argument("--out",default="reports/phase16")
    args=ap.parse_args()
    private=Path(args.private_in).expanduser().resolve()
    out=Path(args.out).expanduser().resolve()
    repo=Path.home()/"AI_policy"
    if not private.is_dir() or private==repo or repo in private.parents:
        ap.error("Protected Phase15 forms not found outside GitHub")
    if private==out or private in out.parents or out in private.parents:
        ap.error("Public and protected results must be in separate directories")
    manifest_file=private/"private_validation_manifest.json"
    if not manifest_file.is_file():
        raise FileNotFoundError("Phase15 private manifest absent")
    manifest=json.loads(manifest_file.read_text(encoding="utf8"))
    frames=read_ratings(private)
    key=private_key_verify(private,frames,manifest)
    readiness={}
    complete=True
    for person in ("a","b"):
        readiness[person]={}
        for section,fields in (("topics",TOPIC_FIELDS),("documents",DOC_FIELDS)):
            frame=frames[(person,section)]
            report=valid_count(frame,fields)
            readiness[person][section]=report
            if any(x["filled"]!=x["total"] for x in report.values()):
                complete=False
    result={
        "created_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
        "status":"complete_independent_ratings_not_yet_adjudicated" if complete
                 else "awaiting_independent_human_ratings",
        "readiness":readiness,
        "sample":{"n_blinded_groups":int(manifest["n_groups"]),
                  "documents_per_rater":int(manifest["n_document_assessments_per_rater"]),
                  "two_raters_expected":True},
        "limitations":[
            "No automated text or rating is generated by this script.",
            "Two completed forms are independent only if the raters worked without sharing responses; scripts cannot verify that procedural requirement.",
            "Cohen's kappa may be undefined for uniform ratings; null is reported instead of a fabricated value.",
            "Uncertain category 9 is excluded from kappa and summary means; denominators and uncertainty counts must be reported.",
            "Topic display intentionally oversamples centroid prototypes and peripheral cases. Descriptive agreement/scores apply to the sample, not to population-wide accuracy.",
            "Group names are qualitative and require expert adjudication; text labels are not published.",
            "The reviewer sample does not establish whether topics are policy-relevant without actual human scores.",
            "Results must be independently adjudicated after agreement calculation before manuscript claims are finalized.",
            "The earlier Phase 5 screening validation is separate and remains unfinished.",
            "Private document titles, abstracts, article IDs, reviewer comments and group matching codes are never exported."
        ]
    }
    if complete:
        result["results"]=evaluate(frames,key)
    public_write(out,result)
    print("PHASE 16",result["status"])
    for person in ("a","b"):
        for section in ("topics","documents"):
            row=readiness[person][section]
            n=min(v["total"] for v in row.values())
            done=min(v["filled"] for v in row.values())
            print("Rater",person,section,"complete rows (lower bound)",done,"/",n)
    print("Public aggregate:",out/"human_topic_review_aggregate.json")
    print("Original protected sheets remain in",private)


if __name__=="__main__":
    main()
