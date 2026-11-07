#!/usr/bin/env python3
"""Phase 7: inspect original inclusion rules and unresolved provenance anomalies.

The source project is read-only. Generated reports contain only aggregate
counts and metadata about explicitly whitelisted Python AST calls. They do
not contain source code, titles, abstracts, identifiers, paths to PDFs,
user credentials or copyrighted content.
"""
from __future__ import annotations

import argparse
import ast
import collections
import datetime as dt
import json
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

ORIGINAL_SCRIPTS = [
    "01_collect_openalex.py", "02_prepare_policy_corpus.py",
    "04_refine_q1_outputs.py", "05_article_ready_package.py",
    "07_ai_assisted_screening.py", "10_download_open_access_pdfs.py",
    "11_extract_fulltext_from_pdfs.py",
    "12_fulltext_screening_and_extraction.py",
    "16_fulltext_topic_modeling_umap_hdbscan.py",
    "18_fulltext_topic_modeling_kmeans_robust.py"
]
TRACK_CALLS = {
    "drop_duplicates", "duplicated", "dropna", "sort_values", "nlargest",
    "nsmallest", "head", "tail", "sample", "query", "isin", "contains",
    "read_parquet", "read_csv", "to_parquet", "to_csv", "KMeans", "UMAP",
    "HDBSCAN", "fit_predict", "encode", "filter", "where"
}
SAFE_KWS = {
    "subset", "keep", "ascending", "n", "n_clusters", "n_init",
    "random_state", "min_dist", "min_samples", "min_cluster_size",
    "n_neighbors", "n_components", "metric", "normalize_embeddings",
    "batch_size", "max_iter"
}
SAFE_COLUMNS = {"openalex_id", "doi", "title", "abstract",
                "publication_year", "type", "source_type", "is_oa",
                "relevance_hits", "q1_relevance_score", "audit_priority"}
SAFE_VALUES = {"first", "last", "cosine", "euclidean", "precomputed",
               "auto", "random", "k-means++", "lloyd", "elkan"}


def literal(node, key):
    try:
        value=ast.literal_eval(node)
    except (ValueError,TypeError,MemoryError,RecursionError):
        return "[expression]"
    if value is None or isinstance(value,(bool,int,float)):
        return value
    if isinstance(value,str):
        return value if value.lower() in SAFE_VALUES|SAFE_COLUMNS else "[string]"
    if isinstance(value,(list,tuple)):
        if key=="subset" and len(value)<=8 and all(
            isinstance(x,str) and x in SAFE_COLUMNS for x in value
        ):
            return value
        return "[collection]"
    return "[redacted]"


def script_signals(project):
    answers=[]
    for fname in ORIGINAL_SCRIPTS:
        path=project/"scripts"/fname
        if not path.is_file():
            answers.append({"filename":fname,"error":"not found"})
            continue
        try:
            root=ast.parse(path.read_text(encoding="utf-8",errors="replace"))
        except (OSError, SyntaxError, UnicodeError) as e:
            answers.append({"filename":fname,"parse_error":type(e).__name__})
            continue
        hits=[]
        for node in ast.walk(root):
            if not isinstance(node,ast.Call):
                continue
            if isinstance(node.func,ast.Attribute):
                method=node.func.attr
            elif isinstance(node.func,ast.Name):
                method=node.func.id
            else:
                continue
            if method not in TRACK_CALLS:
                continue
            args={kw.arg:literal(kw.value,kw.arg)
                  for kw in node.keywords if kw.arg in SAFE_KWS}
            hits.append({"line":node.lineno,"operation":method,"keywords":args})
        hits.sort(key=lambda x:x["line"])
        answers.append({"filename":fname,
                        "operations_detected":len(hits),
                        "operations":hits[:150],
                        "note":"AST lexical evidence only; not proof code paths were executed"})
    return answers


def counts_safe(values):
    freq=collections.Counter(
        "[missing]" if pd.isna(x) else str(x).strip().lower()
        for x in values
    )
    out={}
    sparse=0
    for key,n in freq.items():
        if key not in {"article","preprint","review","book","book-chapter",
                       "editorial","conference-paper","dissertation","report",
                       "journal","repository","other","[missing]"}:
            key="[other]"
        if n>=5:
            out[key]=out.get(key,0)+int(n)
        else:
            sparse+=int(n)
    if sparse:
        out["[rare combined]"]=sparse
    return dict(sorted(out.items()))


def omitted_unique_ids(project):
    p=project/"data/processed"
    raw=pd.read_parquet(p/"openalex_ai_policy_he_checkpoint.parquet",
                        columns=["openalex_id","doi","publication_year","type","abstract"])
    keep=pd.read_parquet(p/"openalex_ai_policy_he_works.parquet",
                        columns=["openalex_id","doi","publication_year","type","abstract"])
    for df in (raw,keep):
        df["_id"]=df["openalex_id"].fillna("").astype(str).str.strip().str.lower()
        df["_doi"]=df["doi"].fillna("").astype(str).str.strip().str.lower()
        df["_has_abstract"]=df["abstract"].fillna("").astype(str).str.strip().str.len()>0
    retained=set(keep["_id"])
    first=raw.drop_duplicates("_id")
    missing=first.loc[~first["_id"].isin(retained)]
    included=first.loc[first["_id"].isin(retained)]
    def aggregate(x):
        year=pd.to_numeric(x["publication_year"],errors="coerce")
        return {"distinct_openalex_records":int(len(x)),
                "with_nonempty_abstract":int(x["_has_abstract"].sum()),
                "no_abstract":int((~x["_has_abstract"]).sum()),
                "publication_year_counts":{
                    str(int(k)) if pd.notna(k) else "[missing]":int(v)
                    for k,v in year.value_counts(dropna=False).items()
                    if pd.notna(k) and v>=5
                },
                "type_counts":counts_safe(x["type"])}
    result={"not_retained":aggregate(missing),
            "retained_from_initial_distinct_ids":aggregate(included),
            "note":"Classification of the 786 lost IDs by metadata does NOT establish the causal filter or why it was applied."}
    return result


def pdf_collisions(project):
    p=project/"outputs/tables/fulltext_pdf_download_success.csv"
    cols={"status","pdf_path","doi","title"}
    df=pd.read_csv(p,usecols=lambda c:c in cols,dtype=str).fillna("")
    paths=df["pdf_path"].astype(str).str.strip()
    populated=paths.ne("")
    grouped=df.loc[populated].assign(_key=paths.loc[populated]).groupby("_key",sort=False)
    duplicates=[]
    for key,g in grouped:
        if len(g)>1:
            doi=g["doi"].str.strip().str.lower() if "doi" in g else pd.Series(dtype=str)
            titles=g["title"].str.strip().str.lower() if "title" in g else pd.Series(dtype=str)
            duplicates.append({
                "records":int(len(g)),
                "all_dois_identical":bool(doi.nunique(dropna=False)==1),
                "all_titles_identical":bool(titles.nunique(dropna=False)==1),
                "statuses":dict(collections.Counter(
                    g["status"].astype(str).str.strip().str.lower()))
            })
    return {
        "success_rows":int(len(df)),
        "unique_nonempty_pdf_paths":int(paths[populated].nunique()),
        "duplicated_pdf_path_groups":int(len(duplicates)),
        "duplicated_pdf_path_group_properties":duplicates,
        "note":"No PDF paths or document identifiers are disclosed. Shared path does not prove independent PDF contents."
    }


def fulltext_decisions(project):
    file=project/"data/processed/fulltext_topic_model_documents.parquet"
    cols=set(pq.ParquetFile(file).schema_arrow.names)
    wanted=[x for x in ("ft_decision","text_length","ai_decision") if x in cols]
    df=pd.read_parquet(file,columns=wanted)
    status=df["ft_decision"].fillna("").astype(str).str.strip().str.lower()
    numbers=pd.to_numeric(df["text_length"],errors="coerce")
    accepted=status.isin({"include_meta_candidate","include_core_fulltext",
                          "include_policy_fulltext"})
    unclear=status.eq("unclear_fulltext")
    excluded=status.str.startswith("exclude")
    bad_length=numbers.isna()|(numbers<=0)
    return {
        "records":len(df),
        "ft_decisions":{k:int(v) for k,v in status.value_counts().items()},
        "explicit_acceptances":int(accepted.sum()),
        "unclear_needs_manual_review":int(unclear.sum()),
        "explicit_exclusions":int(excluded.sum()),
        "nonpositive_text_length":int(bad_length.sum()),
        "accepted_with_nonpositive_text_length":int((accepted&bad_length).sum()),
        "unclear_with_nonpositive_text_length":int((unclear&bad_length).sum()),
        "unrecognized_other":int((~accepted & ~unclear & ~excluded).sum()),
        "note":"Unclear cases are NOT validated eligible; only a human evaluation can adjudicate them."
    }


def query_history(project):
    path=project/"data/processed/openalex_query_stats.csv"
    df=pd.read_csv(path,usecols=["rows_raw"])
    rows=pd.to_numeric(df["rows_raw"],errors="coerce").fillna(0)
    return {
        "number_of_logged_queries":int(len(rows)),
        "queries_with_positive_results":int((rows>0).sum()),
        "queries_with_zero_results":int((rows==0).sum()),
        "sum_raw_hits_across_queries":int(rows.sum()),
        "note":"Summing query hits double-counts overlaps; 24,000 may reflect a per-query cap."
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--project",default=str(Path.home()/"ai_policy_he"))
    parser.add_argument("--out",default="reports/phase07")
    args=parser.parse_args()
    root=Path(args.project).expanduser().resolve()
    out=Path(args.out).expanduser().resolve()
    if not root.is_dir() or out==root or root in out.parents:
        parser.error("Project must exist; reports outside project")
    out.mkdir(parents=True,exist_ok=True)
    evidence={
        "created_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
        "original_scripts_ast":script_signals(root),
        "initial_unique_id_attrition":omitted_unique_ids(root),
        "pdf_path_collisions":pdf_collisions(root),
        "fulltext_screening":fulltext_decisions(root),
        "query_log_counts":query_history(root),
        "privacy":"only aggregate counts, whitelisted AST operation names, line numbers, and safe numeric keywords"
    }
    (out/"rule_and_collision_audit.json").write_text(
        json.dumps(evidence,ensure_ascii=False,indent=2),encoding="utf-8")
    omitted=evidence["initial_unique_id_attrition"]
    pdf=evidence["pdf_path_collisions"]
    ft=evidence["fulltext_screening"]
    summary=["# Phase 7 — Original program rule and edge-case audit","",
        "UTC: "+evidence["created_utc"],"",
        "## OpenAlex attrition","- "+str(omitted),"",
        "## PDF path collision","- "+str(pdf),"",
        "## Fulltext quality decisions","- "+str(ft),"",
        "## Query counts","- "+str(evidence["query_log_counts"]),"",
        "## Static inspection of original scripts (operations only)"]
    for s in evidence["original_scripts_ast"]:
        summary.append("- "+s["filename"]+": "+str(s.get("operations_detected","not parsed"))+
                       " whitelisted operations")
    summary+=["","Operations and line numbers are static source-code indications, not proof of executed decisions.",
        "All user-authored source files remain in the original CEDIA project.",""]
    (out/"summary.md").write_text("\n".join(summary),encoding="utf-8")
    print("PHASE 7 COMPLETE")
    print("786 IDs with metadata compared; duplicate PDF path groups:",pdf["duplicated_pdf_path_groups"])
    print("Explicit full-text acceptances:",ft["explicit_acceptances"],
          "unclear:",ft["unclear_needs_manual_review"])
    print("Reports:",out/"summary.md",out/"rule_and_collision_audit.json")


if __name__=="__main__":
    main()
