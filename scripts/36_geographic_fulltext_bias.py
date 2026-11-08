#!/usr/bin/env python3
"""Phase36: geographic representativeness and 5,000-record retrieval-bias diagnostics.

Read existing frozen CEDIA metadata; no PDF downloads, text-model calls or
changes to original corpus. This *does not* claim full reconstruction of
the original 5,000 high-priority selection rule. OpenAlex IDs are absent
from the attempt manifest; DOI-based matching is only a proxy.

Privacy: aggregate country incidences >=20, missingness, source categories;
never publish article identifiers, titles, abstracts, original scripts,
full source snippets or documents.
"""
from __future__ import annotations
import argparse
import ast
from collections import Counter,defaultdict
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
import re

MIN_REPORTED=20
SOURCE_COLUMNS=[
 "openalex_id","doi","ai_decision","countries","publication_year",
 "disciplinary_area","policy_dimension","type","source_type","is_oa","oa_status"
]

def load_parquet(path,columns):
    import pandas as pd
    import pyarrow.parquet as pq
    found=set(pq.ParquetFile(path).schema.names)
    fields=[c for c in columns if c in found]
    if "openalex_id" not in fields or "countries" not in fields:
        raise ValueError(str(path)+": missing openalex_id or countries metadata")
    return pd.read_parquet(path,columns=fields).fillna("")

def norm(v):
    return str(v or "").strip()

def countries(value):
    if value is None:return None
    if isinstance(value,list):
        obj=value
    else:
        t=norm(value)
        if t in ("","null","None","nan","[]"):return []
        if len(t)>100000:return None
        try:
            obj=json.loads(t)
        except (ValueError,TypeError):
            try:
                obj=ast.literal_eval(t)
            except (ValueError,TypeError,MemoryError,SyntaxError):
                # Recognize unambiguously a single plain country name/ISO code
                if re.fullmatch(r"[A-Za-zÀ-ÿ .,'()-]{2,70}",t):
                    obj=[t]
                else:return None
    if isinstance(obj,dict):
        if "countries" in obj and isinstance(obj["countries"],list):
            obj=obj["countries"]
        else:
            return None
    if isinstance(obj,str):obj=[obj]
    if not isinstance(obj,list):return None
    out=set()
    for x in obj:
        if isinstance(x,dict):
            x=x.get("country_code",x.get("country",x.get("name","")))
        label=norm(x)
        if 1<len(label)<=70 and not any(ch in label for ch in "[]{}|;"):
            out.add(label)
    return sorted(out)

def doi(s):
    value=norm(s).lower()
    value=re.sub(r"^https?://(?:dx\.)?doi\.org/","",value)
    value=re.sub(r"^doi:\s*","",value)
    return value

def country_index(df):
    mapping={}
    byid={}
    malformed=0
    for row in df.to_dict("records"):
        key=norm(row["openalex_id"])
        if not key:raise ValueError("Missing OpenAlex ID in original source")
        if key in byid:raise ValueError("Duplicate OpenAlex ID in source")
        parsed=countries(row.get("countries"))
        if parsed is None:malformed+=1
        byid[key]=parsed
    return byid,malformed

def share_metrics(parent,child,name):
    pa=Counter()
    ch=Counter()
    pa_missing=0;ch_missing=0;pa_bad=0;ch_bad=0
    for arr,ctr,where in ((parent,pa,"parent"),(child,ch,"child")):
        for cs in arr:
            if cs is None:
                if where=="parent":pa_bad+=1
                else:ch_bad+=1
                continue
            if not cs:
                if where=="parent":pa_missing+=1
                else:ch_missing+=1
                continue
            ctr.update(cs)
    npa=len(parent);nch=len(child)
    codes=[c for c,v in pa.items() if v>=MIN_REPORTED]
    rows=[]
    for c in sorted(codes,key=lambda c:(-pa[c],c)):
        a=pa[c]/npa*100
        b=ch[c]/nch*100
        rows.append({
            "country":c,"parent_records_with_country":pa[c],
            "subset_records_with_country":ch[c],
            "parent_percent":round(a,3),
            "subset_percent":round(b,3),
            "difference_percentage_points":round(b-a,3)
        })
    return {
      "comparison":name,
      "parent_records_n":npa,
      "subset_records_n":nch,
      "parent_missing_country_n":pa_missing,
      "subset_missing_country_n":ch_missing,
      "parent_malformed_country_n":pa_bad,
      "subset_malformed_country_n":ch_bad,
      "multi_country_incidence":"A paper may have multiple countries: percentages and differences need not total 100%, not a multinomial composition.",
      "country_reports_min_parent_count":MIN_REPORTED,
      "suppressed_country_count":sum(v<MIN_REPORTED for v in pa.values()),
      "frequent_country_incidence":rows,
      "largest_absolute_differences":sorted(rows,key=lambda x:-abs(x["difference_percentage_points"]))[:12]
    }

def trace_source_operations(path):
    try:
        s=path.read_text(encoding="utf-8")
        tree=ast.parse(s)
    except (OSError,SyntaxError,UnicodeError) as e:
        return {"available":False,"reason":type(e).__name__}
    wanted={"sort_values","nlargest","nsmallest","head","sample","drop_duplicates",
            "query","rank","sort","argsort","to_csv","to_parquet"}
    events=[]
    for node in ast.walk(tree):
        if not isinstance(node,ast.Call) or not isinstance(node.func,ast.Attribute):
            continue
        method=node.func.attr
        if method not in wanted:continue
        literals=[]
        for kw in node.keywords:
            if kw.arg in ("by","ascending","subset","keep","random_state","n","frac"):
                try:
                    v=ast.literal_eval(kw.value)
                    if type(v) in (str,int,float,bool,list,tuple):
                        rep=str(v)
                        if len(rep)<180 and not re.search(r"(?:@|https?://|secret|token)",rep,re.I):
                            literals.append({"key":kw.arg,"value":v})
                except (ValueError,TypeError):
                    pass
        if method=="head" and node.args:
            try:
                n=ast.literal_eval(node.args[0])
                if isinstance(n,int):literals.append({"key":"head_arg","value":n})
            except (ValueError,TypeError):pass
        events.append({"line":node.lineno,"method":method,"literal_args":literals})
    return {
      "available":True,"filename":path.name,
      "statements_lexically_detected":events,
      "status":"STATIC AST HINTS ONLY: not verified to be executed; original code must be manually checked.",
      "original_script_sha256_kept_private":False
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--project",default=str(Path.home()/"ai_policy_he"))
    p.add_argument("--out",default="reports/phase36")
    a=p.parse_args()
    root=Path(a.project).expanduser().resolve()
    out=Path(a.out).expanduser().resolve()
    if out==root or out in root.parents or root in out.parents:
        p.error("Never export aggregate reports into original project or its descendants")
    if out.exists() and any(out.iterdir()):
        p.error("Phase36 already exists; do not overwrite")
    data=root/"data/processed"
    sc=data/"ai_assisted_screening_decisions.parquet"
    ft=data/"fulltext_topic_model_documents.parquet"
    manifest=root/"outputs/tables/fulltext_pdf_download_manifest.csv"
    script=root/"scripts/10_download_open_access_pdfs.py"
    if not all(x.is_file() for x in (sc,ft,manifest)):
        p.error("Frozen original data or 5000-attempt manifest missing")
    screened=load_parquet(sc,SOURCE_COLUMNS)
    fulltext=load_parquet(ft,SOURCE_COLUMNS)
    for table in (screened,fulltext):
        for f in ("doi","openalex_id"):
            if f not in table.columns:raise ValueError("Source missing "+f)
    if len(screened)!=10283 or len(fulltext)!=3656:
        raise ValueError("Original CEDIA frame does not match 10283/3656 reference")
    if "ai_decision" not in screened.columns:
        raise ValueError("Original screening table missing exact included/excluded flags")
    mask=screened["ai_decision"].astype(str).str.lower().isin(
        {"include_core","include_policy","include_context"})
    main=screened.loc[mask].copy()
    if len(main)!=10265:
        raise ValueError("Frozen included OpenAlex table is not 10265 records")
    parent,m1=country_index(main)
    child,m2=country_index(fulltext)
    if not set(child).issubset(parent):
        raise ValueError("Unexpected fulltext articles outside frozen 10265-included frame")
    matched_sources=Counter()
    doi_to_ids=defaultdict(set)
    for row in main.to_dict("records"):
        d=doi(row.get("doi"))
        if d:doi_to_ids[d].add(norm(row["openalex_id"]))
    attempted_dois=[]
    statuses=Counter()
    with manifest.open("r",encoding="utf-8-sig",newline="") as f:
        for x in csv.DictReader(f):
            attempted_dois.append(doi(x.get("doi")))
            statuses[norm(x.get("status"))]+=1
    if len(attempted_dois)!=5000:
        raise ValueError("Source attempt manifest must contain exactly 5000 entries")
    matched_ids=set()
    missing_doi=0;unmatched_doi=0;ambiguous=0;repeated_doi=0
    seen=set()
    for d in attempted_dois:
        if not d:missing_doi+=1;continue
        if d in seen:repeated_doi+=1
        seen.add(d)
        ids=doi_to_ids.get(d,set())
        if len(ids)==1:
            matched_ids.update(ids)
        elif not ids:unmatched_doi+=1
        else:ambiguous+=1
    attempts=[parent[k] for k in sorted(matched_ids)]
    subset=[child[k] for k in sorted(child)]
    parents=[parent[k] for k in sorted(parent)]
    if not attempts:
        raise ValueError("No unambiguous DOI links for attempt-based bias analysis")
    audit={
      "created_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
      "status":"country_incidence_bias_fulltext_and_DOI_proxy_attempts_NOT_exact_5000_selection_proof",
      "original_counts":{
         "screening_final_n":len(screened),
         "screening_included_n":len(main),
         "fulltext_downloaded_or_preexisting_n":len(fulltext),
         "attempts_n":len(attempted_dois),
         "original_source_bad_country_strings_in_parent":m1,
         "original_source_bad_country_strings_in_fulltext":m2,
      },
      "attempt_DOI_linkage_diagnostics":{
          "manifest_records":len(attempted_dois),
          "distinct_nonblank_attempt_dois":len(seen),
          "missing_doi":missing_doi,"unmatched_doi":unmatched_doi,
          "ambiguous_multiple_included_OpenAlex_ids":ambiguous,
          "repeated_dois_in_attempt_manifest":repeated_doi,
          "unambiguously_linked_unique_included_records":len(matched_ids),
          "linked_DOI_records_are_NOT_exact_original_5000_membership":True,
          "manifest_status_counts":dict(sorted(statuses.items()))
      },
      "country_parent_vs_fulltext":share_metrics(parents,subset,"included_10265_vs_extracted_3656"),
      "country_parent_vs_DOI_linked_attempt_proxy":share_metrics(
          parents,attempts,"included_10265_vs_unambiguous_attempt_DOI_proxy"),
      "selection_script_AST":trace_source_operations(script),
      "limitations":[
          "Parent-to-attempt comparison is DOI-linked PROXY, not exact 5000 selection, because manifest lacks OpenAlex IDs.",
          "Country counts are multi-affiliation incidence, not exclusive national shares or fractionalized author credit; non-geocoded entries remain explicitly missing.",
          "No new source documents were retrieved. Download availability and initial selection are distinct bias mechanisms.",
          "AST detection identifies possible ranking and head/selection statements; does not prove these statements were executed or all inputs preserved.",
          "This script does not assert a true stratified geographic probability estimator or causal explanation of selection bias.",
          "Do not claim this report proves full-text eligibility or policy relevance, and do not extrapolate it to pre-filter OpenAlex search hits."
      ]
    }
    out.mkdir(parents=True,exist_ok=True)
    (out/"five_thousand_geographic_bias_aggregate.json").write_text(
        json.dumps(audit,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (out/"summary.md").write_text(
       "# Phase36 — geographic availability bias and 5000 selection trace\n\n"
       +json.dumps({
        "status":audit["status"],"original_counts":audit["original_counts"],
        "attempt_DOI_linkage_diagnostics":audit["attempt_DOI_linkage_diagnostics"],
        "fulltext_largest_differences":audit["country_parent_vs_fulltext"]["largest_absolute_differences"],
        "attempt_proxy_largest_differences":audit["country_parent_vs_DOI_linked_attempt_proxy"]["largest_absolute_differences"],
        "selection_script_AST":audit["selection_script_AST"],
        "limitations":audit["limitations"]
       },ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PHASE36",audit["status"])
    print("Original 10265 included, 5000 attempted, 3656 fulltext; country incidence audit complete.")
    print("Attempt DOI proxy linked:",len(matched_ids),"records; NOT a reconstructed exact 5000 selection.")
    print("Read original selection script manually before claiming exact high-priority rule.")
    print("Public aggregate:",out/"five_thousand_geographic_bias_aggregate.json")

if __name__=="__main__":
    main()
