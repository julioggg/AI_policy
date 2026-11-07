#!/usr/bin/env python3
"""Phase 6: auditable provenance without re-downloading or re-embedding.

Read-only access to the original CEDIA project. Outputs aggregate counts,
dates and non-sensitive OpenAlex search terms, not document identifiers,
titles, abstracts, article texts, original scripts or credentials.
Requires pandas, numpy, pyarrow. Python >=3.9.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

BASE = {
    "raw": "data/processed/openalex_ai_policy_he_checkpoint.parquet",
    "unique": "data/processed/openalex_ai_policy_he_works.parquet",
    "core": "data/processed/openalex_ai_policy_he_core.parquet",
    "refined": "data/processed/openalex_ai_policy_he_q1_refined.parquet",
    "ready": "data/processed/openalex_ai_policy_he_article_ready_strict.parquet",
    "screening": "data/processed/ai_assisted_screening_decisions.parquet",
    "fulltext": "data/processed/fulltext_topic_model_documents.parquet",
    "extracted": "data/processed/fulltext/fulltext_extracted_texts.parquet",
}

COLS = ["openalex_id", "doi", "retrieved_at", "publication_year",
        "type", "source_type", "q1_relevance_score", "ai_decision",
        "ft_decision", "status", "text_length"]


def read_parquet(root, name):
    path = root / BASE[name]
    if not path.is_file():
        raise FileNotFoundError(str(path))
    cols = set(pq.ParquetFile(path).schema_arrow.names)
    return pd.read_parquet(path, columns=[c for c in COLS if c in cols])


def normalized(series, doi=False):
    s = series.fillna("").astype(str).str.strip().str.lower()
    if doi:
        s = s.str.replace(r"^(https?://(dx\.)?doi\.org/|doi:)", "", regex=True)
    else:
        s = s.str.rstrip("/")
    s = s.where(~s.isin(["", "nan", "none", "null"]), "")
    return s


def stage_summary(df):
    r = {"rows": int(len(df))}
    if "openalex_id" in df:
        ids = normalized(df["openalex_id"])
        r["unique_ids"] = int(ids[ids!=""].nunique())
        r["duplicate_ids"] = int(len(ids[ids != ""]) - r["unique_ids"])
        r["missing_ids"] = int((ids=="").sum())
    if "doi" in df:
        dois = normalized(df["doi"], doi=True)
        r["unique_dois"] = int(dois[dois!=""].nunique())
        r["duplicate_doi_rows"] = int(len(dois[dois != ""]) - r["unique_dois"])
        r["missing_doi_rows"] = int((dois=="").sum())
    for col in ["ai_decision","ft_decision","status"]:
        if col in df:
            values = df[col].fillna("[missing]").astype(str).str.strip().str.lower()
            counter = collections.Counter(values)
            r[col+"_counts"] = dict(sorted(counter.items()))
    if "text_length" in df:
        sizes = pd.to_numeric(df["text_length"], errors="coerce")
        r["text_length_nonpositive"] = int((sizes.fillna(0)<=0).sum())
        r["text_length_missing"] = int(sizes.isna().sum())
    if "q1_relevance_score" in df:
        score = pd.to_numeric(df["q1_relevance_score"], errors="coerce")
        if score.notna().any():
            r["relevance_score_quantiles"] = {
                str(x): round(float(score.quantile(x)),5)
                for x in [0,.05,.25,.5,.75,.95,1]
            }
    return r


def quantify_dropped_ids(raw, unique):
    a = raw[["openalex_id","doi"]].copy()
    b = unique[["openalex_id","doi"]].copy()
    a["openalex_id"] = normalized(a["openalex_id"])
    a["doi"] = normalized(a["doi"], doi=True)
    b["openalex_id"] = normalized(b["openalex_id"])
    b["doi"] = normalized(b["doi"], doi=True)
    raw_ids = set(a["openalex_id"])-{""}
    unique_ids = set(b["openalex_id"])-{""}
    deleted = raw_ids-unique_ids
    missing_rows = a[a["openalex_id"].isin(deleted)].drop_duplicates("openalex_id")
    retain_doi = set(b["doi"])-{""}
    same_doi = int(missing_rows["doi"].isin(retain_doi).sum())
    empty_doi = int((missing_rows["doi"]=="").sum())
    return {
        "raw_distinct_openalex_ids":len(raw_ids),
        "retained_distinct_openalex_ids":len(unique_ids),
        "distinct_ids_not_retained":len(deleted),
        "not_retained_with_doi_matching_kept_id":same_doi,
        "not_retained_with_missing_doi":empty_doi,
        "not_retained_with_distinct_nonempty_doi":len(deleted)-same_doi-empty_doi,
        "caution":"Matching DOI is not conclusive proof of the filtering/deduplication rule."
    }


def count_manifest(path, cols):
    if not path.is_file():
        return {"error":"manifest missing"}, None
    df = pd.read_csv(path,usecols=lambda x:x in cols,low_memory=False)
    if "doi" in df:
        df["_doi"] = normalized(df["doi"], doi=True)
    if "pdf_path" in df:
        df["_file"] = df["pdf_path"].fillna("").astype(str).str.strip().str.lower()
    r = {"rows":len(df)}
    if "status" in df:
        r["status_counts"] = dict(sorted(collections.Counter(
            df["status"].fillna("[missing]").astype(str).str.lower().str.strip()).items()))
    if "_doi" in df:
        d = df["_doi"]
        r["unique_dois"] = int(d[d!=""].nunique())
        r["missing_doi"] = int((d=="").sum())
    if "_file" in df:
        p = df["_file"]
        r["unique_nonempty_pdf_paths"] = int(p[p!=""].nunique())
        r["missing_pdf_path"] = int((p=="").sum())
    return r,df


def query_inventory(path):
    if not path.is_file():
        return {"error":"OpenAlex query-statistics file missing"}
    table=pd.read_csv(path,usecols=lambda x:x in {"query","rows_raw"})
    output=[]
    for row in table.to_dict("records"):
        phrase=str(row.get("query") or "").strip()
        # Safe search terms only, never arbitrary URLs, tokens or path contents.
        safe=bool(re.fullmatch(r"[a-zA-Z0-9 ,;:()_./+\-&]{1,150}",phrase)
                  and not re.search(r"(?i)(token|secret|api.key|password|https?://)",phrase))
        output.append({
            "search_term":phrase if safe else "[redacted]",
            "term_sha256":hashlib.sha256(phrase.encode("utf8")).hexdigest()[:12],
            "raw_rows":int(row["rows_raw"]) if pd.notna(row.get("rows_raw")) else None
        })
    return {"queries_logged":len(output),"query_log":output,
            "warning":"This query log is not a full API request history; API fields, filters and dates must be corroborated from original code."}


def date_span(series):
    try:
        parsed=pd.to_datetime(series,errors="coerce",utc=True,format="mixed")
    except TypeError:
        parsed=pd.to_datetime(series,errors="coerce",utc=True)
    valid=parsed.dropna()
    if not len(valid):
        return {"valid_dates":0,"total_rows":len(series)}
    dates=valid.dt.strftime("%Y-%m-%d")
    return {"valid_dates":len(valid), "total_rows":len(series),
            "first_utc_date":str(dates.min()),"last_utc_date":str(dates.max()),
            "distinct_utc_dates":int(dates.nunique()),
            "daily_counts":dict(sorted(collections.Counter(dates).items()))}


def selection_proxy(screen, attempt_df):
    if attempt_df is None or "doi" not in attempt_df:
        return {"error":"DOI not available in attempt manifest"}
    a=screen.loc[screen["ai_decision"].fillna("").astype(str).str.lower().isin(
        ["include_core","include_policy","include_context"])].copy()
    a["_doi"]=normalized(a["doi"],doi=True)
    selected=set(attempt_df["_doi"])-{""}
    marker=a["_doi"].isin(selected) & a["_doi"].ne("")
    result={
        "screen_included_rows":len(a),
        "attempt_manifest_rows":len(attempt_df),
        "attempt_manifest_distinct_dois":len(selected),
        "included_rows_matching_attempt_doi":int(marker.sum()),
        "included_rows_unmatched_or_no_doi":int((~marker).sum()),
        "matching_is_a_proxy":True,
        "caution":"A DOI-based match does not reconstruct the exact 5000 selected OpenAlex records when DOIs are duplicated or missing."
    }
    if "q1_relevance_score" in a:
        vals=pd.to_numeric(a["q1_relevance_score"],errors="coerce")
        selected_score=vals.loc[marker].dropna()
        other_score=vals.loc[~marker].dropna()
        result["relevance_score_median_attempt_doi_match"]=(
            round(float(selected_score.median()),5) if len(selected_score) else None)
        result["relevance_score_median_unmatched"]=(
            round(float(other_score.median()),5) if len(other_score) else None)
    return result


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--project",default=str(Path.home()/"ai_policy_he"))
    ap.add_argument("--out",default="reports/phase06")
    args=ap.parse_args()
    root,out=Path(args.project).expanduser().resolve(),Path(args.out).expanduser().resolve()
    if not root.is_dir() or out==root or root in out.parents:
        ap.error("Source must exist and output must not be inside original project")
    out.mkdir(parents=True,exist_ok=True)
    dfs={}
    stage_summaries={}
    for key in BASE:
        dfs[key]=read_parquet(root,key)
        stage_summaries[key]=stage_summary(dfs[key])
    dropped=quantify_dropped_ids(dfs["raw"],dfs["unique"])
    try:
        retrieval_dates=date_span(dfs["raw"]["retrieved_at"])
    except Exception as e:
        retrieval_dates={"error_type":type(e).__name__}

    manifest_path=root/"outputs/tables/fulltext_pdf_download_manifest.csv"
    success_path=root/"outputs/tables/fulltext_pdf_download_success.csv"
    extraction_path=root/"outputs/tables/fulltext_extraction_manifest.csv"
    attempts,raw_attempts=count_manifest(manifest_path,{"doi","status","pdf_path"})
    success,raw_success=count_manifest(success_path,{"doi","status","pdf_path"})
    extraction,raw_extraction=count_manifest(extraction_path,{
        "doi","status","pdf_path","text_length"})
    cross={}
    if raw_attempts is not None and raw_success is not None:
        for field in ["_doi","_file"]:
            if field in raw_attempts and field in raw_success:
                x=set(raw_attempts[field])-{""}
                y=set(raw_success[field])-{""}
                cross[field]={
                    "distinct_attempt_keys":len(x),
                    "distinct_success_keys":len(y),
                    "success_keys_not_in_attempts":len(y-x),
                    "success_keys_matching_attempts":len(y&x)}
    if raw_extraction is not None and raw_success is not None:
        if "_file" in raw_extraction and "_file" in raw_success:
            a=set(raw_extraction["_file"])-{""}
            b=set(raw_success["_file"])-{""}
            cross["extraction_vs_success_pdf_paths"]={
                "extracted_unique_paths":len(a),
                "success_unique_paths":len(b),
                "extracted_paths_not_in_success":len(a-b)}
    if raw_extraction is not None and "text_length" in raw_extraction:
        t=pd.to_numeric(raw_extraction["text_length"],errors="coerce")
        extraction["nonpositive_text_length"]=int((t.fillna(0)<=0).sum())
    fulltext=dfs["fulltext"]
    validity={}
    if "ft_decision" in fulltext and "text_length" in fulltext:
        flag=fulltext["ft_decision"].fillna("").astype(str).str.strip().str.lower().str.startswith("exclude")
        lengths=pd.to_numeric(fulltext["text_length"],errors="coerce")
        zero=lengths.fillna(0)<=0
        validity={
            "excluded_fulltext":int(flag.sum()),
            "text_length_nonpositive":int(zero.sum()),
            "both":int((flag & zero).sum()),
            "retained_after_both_filters":int((~flag&~zero).sum())
        }
    lookup=query_inventory(root/"data/processed/openalex_query_stats.csv")
    selection=selection_proxy(dfs["screening"],raw_attempts)
    result={
        "created_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
        "stages":stage_summaries,
        "raw_to_unique_missing_ids":dropped,
        "retrieval_dates":retrieval_dates,
        "retrieval_queries":lookup,
        "fulltext_attempts":attempts,
        "fulltext_success_table":success,
        "fulltext_extraction_table":extraction,
        "manifest_set_comparison":cross,
        "fulltext_screening_concordance":validity,
        "five_thousand_selection_doi_proxy":selection,
        "limitations":[
            "Recorded query labels and retrieval timestamps do not specify the full API endpoints and filter parameters.",
            "Full-text extraction record, successful download, usable text, and assigned embedding are separate units.",
            "DOI-based selected-record matching is incomplete when DOI is missing or duplicated.",
            "The 786 missing OpenAlex IDs cannot be called duplicates until their removals are attributed to executable rules.",
            "This analysis does not perform new expert assessment or rerun NLP models.",
            "All published findings are aggregate. The original research project is unmodified."
        ]
    }
    (out/"provenance_reconciliation.json").write_text(
        json.dumps(result,indent=2,ensure_ascii=False,default=str),encoding="utf-8")
    lines=["# Phase 6 — Search provenance and full-text denominator audit",
           "","Generated: "+result["created_utc"],
           "","## Corpus stages"]
    for name,info in stage_summaries.items():
        lines.append("- "+name+": "+str(info["rows"])+" rows, "+
                     str(info.get("unique_ids","n/a"))+" unique OpenAlex IDs")
    lines+=["","## Raw to unique OpenAlex IDs","- "+str(dropped),
            "","## Retrieval window","- "+str({
                key:value for key,value in retrieval_dates.items() if key!="daily_counts"}),
            "","## Search query log","- "+str(lookup.get("queries_logged"))+
            " recorded queries; see JSON (not yet verified against exact script parameters)",
            "","## Download and extraction",
            "- Attempts: "+str(attempts),
            "- Success table: "+str(success),
            "- Extraction table: "+str(extraction),
            "- Cross-manifest comparison: "+str(cross),
            "- Fulltext eligibility: "+str(validity),
            "","## Five-thousand-selection proxy","- "+str(selection),
            "","## Methodological warnings"]
    lines+=["- "+msg for msg in result["limitations"]]
    (out/"summary.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print("PHASE 6 COMPLETE")
    print("Dropped distinct OpenAlex IDs:",dropped["distinct_ids_not_retained"])
    print("Download statuses:", attempts.get("status_counts"))
    print("Full-text eligibility:",validity)
    print("Reports:",out/"summary.md",out/"provenance_reconciliation.json")


if __name__=="__main__":
    main()
