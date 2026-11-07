#!/usr/bin/env python3
"""Phase 8b: paired analysis reusing BOTH already computed CEDIA embedding arrays.

This script NEVER loads a sentence-transformer, encodes text, downloads anything,
or writes document identifiers, embeddings, titles, abstracts or texts to GitHub.
It compares original short-text/core and fulltext vectors matched by OpenAlex ID.
The original code must be consulted before calling core vectors title+abstract.
"""
from __future__ import annotations

import argparse
import ast
import datetime as dt
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from sklearn.cluster import KMeans
from sklearn.metrics import (adjusted_rand_score, normalized_mutual_info_score,
                             silhouette_score)
from sklearn.preprocessing import normalize

WHITELIST = {"text_for_analysis", "text", "abstract", "title", "openalex_id"}
INCLUDE_FT = {"include_meta_candidate", "include_core_fulltext",
              "include_policy_fulltext"}


def schema_select(file, names):
    possible=set(pq.ParquetFile(file).schema_arrow.names)
    available=[c for c in names if c in possible]
    if "openalex_id" not in available:
        raise ValueError("openalex_id absent from "+file.name)
    return pd.read_parquet(file,columns=available)


def norm_ids(series):
    return series.fillna("").astype(str).str.strip().str.lower().str.rstrip("/")


def fp_ids(series):
    return hashlib.sha256("\n".join(series.astype(str).tolist()).encode("utf8")).hexdigest()


def source_indications(file):
    try:
        tree=ast.parse(file.read_text(encoding="utf-8",errors="replace"))
    except (OSError,UnicodeError,SyntaxError) as err:
        return {"status":"AST parse unavailable","error":type(err).__name__}
    field_mentions={x:0 for x in WHITELIST}
    encode_calls=[]
    for node in ast.walk(tree):
        if isinstance(node,ast.Constant) and isinstance(node.value,str):
            if node.value in field_mentions:
                field_mentions[node.value]+=1
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute):
            if node.func.attr=="encode":
                inp=node.args[0] if node.args else None
                if isinstance(inp,ast.Name):
                    source_name=inp.id if inp.id in {"texts","sentences","documents",
                      "text_data","corpus","text_list","input_texts"} else "[variable]"
                else:
                    source_name="[expression]"
                encode_calls.append({"line":node.lineno,
                                     "first_argument_variable":source_name})
    return {"file":file.name,"field_name_occurrences":field_mentions,
            "encode_calls":encode_calls,
            "interpretation":"Static indications only. Confirm actual feature construction in the original script."}


def percentile(x):
    return {"median":round(float(np.median(x)),5),
            "p10":round(float(np.quantile(x,.10)),5),
            "p90":round(float(np.quantile(x,.90)),5)}


def to_json(path,obj):
    path.write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding="utf-8")


def save(public,result):
    public.mkdir(parents=True,exist_ok=True)
    to_json(public/"reused_embedding_comparison.json",result)
    lines=["# Phase 8b — Existing core vs full-text embedding comparison",
           "","Status: "+result.get("status","unknown"),
           "UTC: "+result.get("created_utc",""),
           "","## Alignment and provenance"]
    for k,v in result.get("audit",{}).items():
        lines.append("- "+str(k)+": "+str(v))
    for k,v in result.get("analyses",{}).items():
        lines+=["","## "+k,"- "+str(v)]
    lines+=["","## Interpretation limits"]
    lines+=["- "+x for x in result.get("limitations",[])]
    (public/"summary.md").write_text("\n".join(lines)+"\n",encoding="utf8")


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--project",default=str(Path.home()/"ai_policy_he"))
    parser.add_argument("--out",default="reports/phase08b")
    parser.add_argument("--seed",type=int,default=42)
    parser.add_argument("--threads",type=int,default=8)
    args=parser.parse_args()
    root=Path(args.project).expanduser().resolve()
    out=Path(args.out).expanduser().resolve()
    if not root.is_dir() or out==root or root in out.parents:
        parser.error("Original source project must exist and report folder must be external")
    if args.threads<1:
        parser.error("threads must be positive")
    out.mkdir(parents=True,exist_ok=True)
    core_file=root/"data/processed/openalex_ai_policy_he_core_50k_embedded.parquet"
    ft_file=root/"data/processed/fulltext_topic_model_documents_with_kmeans.parquet"
    source_matrix=root/"data/processed/embeddings_core_50k_minilm.npy"
    ft_matrix=root/"data/processed/fulltext_topic_embeddings_minilm.npy"
    core=schema_select(core_file,["openalex_id","abstract","text_for_analysis","title"])
    ft=schema_select(ft_file,["openalex_id","abstract","text_length","ft_decision",
                               "policy_dimension","disciplinary_area"])
    x_core=np.load(source_matrix,allow_pickle=False,mmap_mode="r")
    x_ft=np.load(ft_matrix,allow_pickle=False,mmap_mode="r")
    if len(core)!=len(x_core) or len(ft)!=len(x_ft) or \
       x_core.ndim!=2 or x_ft.ndim!=2 or x_core.shape[1]!=x_ft.shape[1]:
        raise ValueError("Embedding array / Parquet sizes or dimensions incompatible")
    ci=norm_ids(core["openalex_id"])
    fi=norm_ids(ft["openalex_id"])
    if ci.eq("").any() or fi.eq("").any() or ci.duplicated().any() or fi.duplicated().any():
        raise ValueError("Missing/duplicate OpenAlex IDs prevent reliable one-to-one mapping")
    lookup=pd.Index(ci)
    mapped=lookup.get_indexer(fi)
    if "ft_decision" not in ft or "text_length" not in ft or "abstract" not in core:
        raise ValueError("Required metadata fields absent")
    status=ft["ft_decision"].fillna("").astype(str).str.strip().str.lower()
    lens=pd.to_numeric(ft["text_length"],errors="coerce")
    eligible=status.isin(INCLUDE_FT)&(lens>0)
    available=mapped>=0
    paired=eligible.to_numpy() & available
    rows=np.flatnonzero(paired)
    core_idx=mapped[rows]
    abslen=core.iloc[core_idx]["abstract"].fillna("").astype(str).str.len().to_numpy()
    rows=rows[abslen>=20]
    core_idx=mapped[rows]
    result={
        "created_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
        "status":"preflight",
        "audit":{
            "original_core_parquet_rows":len(core),
            "original_core_embedding_shape":list(x_core.shape),
            "original_fulltext_parquet_rows":len(ft),
            "original_fulltext_embedding_shape":list(x_ft.shape),
            "fulltext_ids_available_in_core":int(available.sum()),
            "fulltext_explicit_eligible":int(eligible.sum()),
            "eligible_with_core_vectors_and_abstract_len_ge_20":len(rows),
            "core_id_order_hash":fp_ids(ci),
            "fulltext_id_order_hash":fp_ids(fi),
            "core_embedding_source_signals":source_indications(
                root/"scripts/03_embeddings_and_clusters.py")
        },
        "limitations":[
            "Core vector provenance must be checked in the original scripts before asserting a title/abstract-only encoding.",
            "Row order inside each NPY is inferred from corresponding Parquet and checked indirectly by matched-vs-shuffled similarities; no source index file is known.",
            "Analysis uses only common explicitly accepted full-text publications, avoiding sample-size confounding.",
            "An embedding comparison cannot independently validate the topical labels or establish policy usefulness.",
            "No embeddings, copyright text, article metadata or identifiers are published."
        ]
    }
    if len(rows)<1000:
        result["status"]="blocked_insufficient_overlap"
        save(out,result)
        print("PHASE 8B: insufficient paired corpus; see report")
        return
    short=np.asarray(x_core[core_idx],dtype=np.float32)
    full=np.asarray(x_ft[rows],dtype=np.float32)
    if not np.isfinite(short).all() or not np.isfinite(full).all():
        raise ValueError("Nonfinite embedding values")
    short=normalize(short)
    full=normalize(full)
    matched=np.einsum("ij,ij->i",short,full)
    rng=np.random.default_rng(args.seed)
    shuffled=np.einsum("ij,ij->i",short,full[rng.permutation(len(full))])
    gap=float(np.median(matched)-np.median(shuffled))
    result["audit"].update({
        "matching_cosine":percentile(matched),
        "shuffled_cosine":percentile(shuffled),
        "matched_minus_shuffled_median":round(gap,5),
        "alignment_signal":"positive" if gap>0.05 else "inconclusive"
    })
    if gap<=0.05:
        result["status"]="blocked_no_alignment_signal"
        save(out,result)
        print("PHASE 8B: row correspondence remains unverified; see report")
        return
    # Both matrices use the SAME set of accepted documents and same seeds.
    comp={}
    for k in (12,18,25):
        from sklearn.cluster import KMeans
        a=KMeans(n_clusters=k,random_state=args.seed,n_init=10,max_iter=300).fit_predict(short)
        b=KMeans(n_clusters=k,random_state=args.seed,n_init=10,max_iter=300).fit_predict(full)
        comp[str(k)]={
            "number_of_documents":len(rows),
            "ari_between_core_and_fulltext":round(float(adjusted_rand_score(a,b)),5),
            "nmi_between_core_and_fulltext":round(float(normalized_mutual_info_score(a,b)),5),
            "core_cosine_silhouette":round(float(silhouette_score(
                short,a,metric="cosine",sample_size=min(1000,len(rows)),random_state=args.seed)),5),
            "fulltext_cosine_silhouette":round(float(silhouette_score(
                full,b,metric="cosine",sample_size=min(1000,len(rows)),random_state=args.seed)),5)
        }
        print("k",k,"ARI core-vs-fulltext",comp[str(k)]["ari_between_core_and_fulltext"],flush=True)
    result["status"]="completed_with_provenance_caveat"
    result["analyses"]={"paired_embedding_comparison":comp}
    save(out,result)
    print("PHASE 8B COMPLETE. Matched rows:",len(rows))
    print("Reports:",out/"summary.md",out/"reused_embedding_comparison.json")


if __name__=="__main__":
    main()
