#!/usr/bin/env python3
"""Phase 9 — forensic audit: do 'full-text' vectors really encode more text?

Reads ORIGINAL CEDIA parquet/NumPy files, never modifies them.
Writes ONLY aggregate numerical findings and whitelisted source-code signals.
No titles, abstracts, raw texts, filenames for PDFs, identifiers or embeddings
are written to the public report. Python >= 3.9, numpy, pandas, pyarrow.
"""
from __future__ import annotations
import argparse
import ast
import datetime as dt
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

KNOWN_FIELDS = {
    "title", "abstract", "text", "text_for_analysis", "topic_text",
    "full_text", "semantic_text", "screen_text", "combined_text"
}
SCRIPT_NAMES = [
    "03_embeddings_and_clusters.py",
    "12_fulltext_screening_and_extraction.py",
    "16_fulltext_topic_modeling_umap_hdbscan.py",
    "18_fulltext_topic_modeling_kmeans_robust.py"
]


def read_cols(file, wanted):
    available=set(pq.ParquetFile(file).schema_arrow.names)
    return pd.read_parquet(file, columns=[x for x in wanted if x in available])


def normalize_ids(col):
    return col.fillna("").astype(str).str.strip().str.lower().str.rstrip("/")


def text_stats(s):
    n=s.fillna("").astype(str).str.len().to_numpy(dtype=float)
    return {
        "rows":int(len(n)),
        "zero_length":int((n==0).sum()),
        "median_characters":int(np.median(n)),
        "p10_characters":int(np.quantile(n,.1)),
        "p90_characters":int(np.quantile(n,.9)),
        "max_characters":int(n.max())
    }


def simplified(v, limit=None):
    txt=" ".join(str(v or "").split()).casefold()
    return txt[:limit] if limit else txt


def text_overlap(core, ft, selected, mapped):
    result={}
    ft_idx=np.flatnonzero(selected)
    core_idx=mapped[ft_idx]
    if len(ft_idx)==0:
        return result
    pairs=[
        ("core_text_for_analysis","text_for_analysis","topic_text"),
        ("core_abstract","abstract","topic_text"),
        ("core_title","title","topic_text"),
        ("core_abstract","abstract","abstract"),
    ]
    for name,cname,fname in pairs:
        if cname not in core or fname not in ft:
            continue
        if name=="core_abstract" and fname=="abstract":
            continue
        left=core.iloc[core_idx][cname].fillna("").astype(str).tolist()
        right=ft.iloc[ft_idx][fname].fillna("").astype(str).tolist()
        exact=0
        prefix_256=0
        prefix_512=0
        first_contained=0
        for a,b in zip(left,right):
            a=simplified(a)
            b=simplified(b)
            if a==b:
                exact+=1
            if a[:256] and a[:256]==b[:256]:
                prefix_256+=1
            if a[:512] and a[:512]==b[:512]:
                prefix_512+=1
            if a[:128] and a[:128] in b[:1500]:
                first_contained+=1
        n=len(left)
        result[name+"_vs_"+fname]={
            "exact_text_match":exact,
            "identical_first_256_characters":prefix_256,
            "identical_first_512_characters":prefix_512,
            "core_first_128_characters_found_in_topic_head":first_contained,
            "compared_records":n
        }
    return result


def script_ast(file):
    try:
        root=ast.parse(file.read_text(encoding="utf8",errors="replace"))
    except (OSError,UnicodeError,SyntaxError) as e:
        return {"filename":file.name,"error":type(e).__name__}
    field_mentions={}
    encode_calls=[]
    variables={}
    for n in ast.walk(root):
        if isinstance(n,ast.Constant) and isinstance(n.value,str) and n.value in KNOWN_FIELDS:
            field_mentions[n.value]=field_mentions.get(n.value,0)+1
        if isinstance(n,ast.Assign):
            for target in n.targets:
                if isinstance(target,ast.Name):
                    refs={
                        z.value for z in ast.walk(n.value)
                        if isinstance(z,ast.Constant) and isinstance(z.value,str)
                        and z.value in KNOWN_FIELDS
                    }
                    if refs:
                        variables.setdefault(target.id,set()).update(refs)
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=="encode":
            arg=n.args[0] if n.args else None
            name=arg.id if isinstance(arg,ast.Name) else ""
            safe_refs=sorted(variables.get(name,set()))
            encode_calls.append({
                "line":n.lineno,
                "argument_is_named_variable":bool(name),
                "argument_variable_references_whitelisted_fields":safe_refs
            })
    return {
        "filename":file.name,
        "field_occurrence_counts":field_mentions,
        "encode_calls":sorted(encode_calls,key=lambda x:x["line"]),
        "caution":"Static AST indications do not reconstruct function-call dependencies or prove runtime provenance."
    }


def nstats(a):
    return {
        "median":round(float(np.median(a)),7),
        "p10":round(float(np.quantile(a,.10)),7),
        "p90":round(float(np.quantile(a,.90)),7),
        "min":round(float(np.min(a)),7),
        "max":round(float(np.max(a)),7)
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--project",default=str(Path.home()/"ai_policy_he"))
    parser.add_argument("--out",default="reports/phase09")
    args=parser.parse_args()
    root=Path(args.project).expanduser().resolve()
    out=Path(args.out).expanduser().resolve()
    if not root.is_dir() or out==root or root in out.parents:
        parser.error("Source must exist and reports must be outside original project")
    out.mkdir(parents=True,exist_ok=True)

    base=root/"data/processed"
    core=read_cols(base/"openalex_ai_policy_he_core_50k_embedded.parquet",
                   ["openalex_id","title","abstract","text_for_analysis","text"])
    ft=read_cols(base/"fulltext_topic_model_documents_with_kmeans.parquet",
                 ["openalex_id","title","abstract","full_text","topic_text",
                  "semantic_text","combined_text","text_length","ft_decision"])
    x_core=np.load(base/"embeddings_core_50k_minilm.npy",mmap_mode="r",allow_pickle=False)
    x_full=np.load(base/"fulltext_topic_embeddings_minilm.npy",mmap_mode="r",allow_pickle=False)
    if len(core)!=len(x_core) or len(ft)!=len(x_full) or x_core.shape[1]!=x_full.shape[1]:
        raise ValueError("Embedding and parquet row counts/dimensions do not align")
    ci=normalize_ids(core["openalex_id"])
    fi=normalize_ids(ft["openalex_id"])
    if ci.eq("").any() or fi.eq("").any() or ci.duplicated().any() or fi.duplicated().any():
        raise ValueError("IDs are empty or duplicate; cannot join reliably")
    mapped=pd.Index(ci).get_indexer(fi)
    flags=ft["ft_decision"].fillna("").astype(str).str.strip().str.lower()
    length=pd.to_numeric(ft["text_length"],errors="coerce")
    accepted=flags.isin({"include_meta_candidate","include_core_fulltext",
                          "include_policy_fulltext"}) & (length>0)
    paired=accepted.to_numpy() & (mapped>=0)
    i=np.flatnonzero(paired)
    j=mapped[i]
    if len(i)<1000:
        raise ValueError("Not enough accepted paired items")

    a=np.asarray(x_core[j],dtype=np.float64)
    b=np.asarray(x_full[i],dtype=np.float64)
    if not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError("Nonfinite embeddings")
    raw_delta=np.max(np.abs(a-b),axis=1)
    l2_delta=np.linalg.norm(a-b,axis=1)
    na=np.linalg.norm(a,axis=1)
    nb=np.linalg.norm(b,axis=1)
    if np.any(na==0) or np.any(nb==0):
        raise ValueError("Zero-vector embeddings")
    cos=np.sum(a*b,axis=1)/(na*nb)
    report={
        "created_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
        "scope":"Existing vectors on common records; forensic provenance, NOT model validation",
        "n_paired_explicitly_accepted":len(i),
        "vector_dimensions":x_core.shape[1],
        "vector_comparison":{
            "exact_all_components_equal":int(np.sum(np.all(a==b,axis=1))),
            "max_component_abs_difference_le_1e-7":int((raw_delta<=1e-7).sum()),
            "max_component_abs_difference_le_1e-5":int((raw_delta<=1e-5).sum()),
            "cosine_ge_0_999999":int((cos>=.999999).sum()),
            "cosine_ge_0_999":int((cos>=.999).sum()),
            "cosine_ge_0_99":int((cos>=.99).sum()),
            "cosine_below_0_90":int((cos<.90).sum()),
            "cosine_summary":nstats(cos),
            "raw_max_component_difference_summary":nstats(raw_delta),
            "raw_l2_difference_summary":nstats(l2_delta),
            "core_norm_summary":nstats(na),
            "fulltext_norm_summary":nstats(nb)
        },
        "text_lengths":{},
        "text_relationships":text_overlap(core,ft,paired,mapped),
        "script_provenance_signals":[script_ast(root/"scripts"/name) for name in SCRIPT_NAMES],
        "limitations":[
            "High cosine similarity alone does not imply identical vectors; raw component equality is tested separately.",
            "Identical embeddings can arise from identical or truncated inputs; these summaries do not prove which mechanism occurred.",
            "Full-text extraction can exist without full-text representation in the model; both pipeline stages must be audited.",
            "The original sentence-transformer model, tokenizer and max_seq_length must be verified locally before making a truncation claim.",
            "The script exports no document identifiers, full texts, abstracts, vectors or article titles."
        ]
    }
    for name in ["abstract","full_text","topic_text","semantic_text","combined_text"]:
        if name in ft:
            report["text_lengths"][name]=text_stats(ft.iloc[i][name])
    for name in ["abstract","text_for_analysis","text"]:
        if name in core:
            report["text_lengths"]["core_"+name]=text_stats(core.iloc[j][name])
    (out/"embedding_forensics.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False),encoding="utf8")
    m=report["vector_comparison"]
    lines=[
        "# Phase 9 — Forensic examination of embedding provenance","",
        "UTC: "+report["created_utc"],"",
        "Paired accepted records: "+str(len(i)),"",
        "## Numerical identity of existing vectors",
        "- Component-wise exact equality: "+str(m["exact_all_components_equal"]),
        "- max absolute component difference <= 1e-7: "+str(m["max_component_abs_difference_le_1e-7"]),
        "- cosine >= 0.999999: "+str(m["cosine_ge_0_999999"]),
        "- cosine >= 0.999: "+str(m["cosine_ge_0_999"]),
        "- cosine < 0.90: "+str(m["cosine_below_0_90"]),
        "- cosine quantiles: "+str(m["cosine_summary"]),
        "- raw-vector L2-distance quantiles: "+str(m["raw_l2_difference_summary"]),
        "","## Text-length summaries"]
    for k,v in report["text_lengths"].items():
        lines.append("- "+k+": "+str(v))
    lines+=["","## Text-prefix overlap"]
    for k,v in report["text_relationships"].items():
        lines.append("- "+k+": "+str(v))
    lines+=["","## Original script inspection (static indications)"]
    for item in report["script_provenance_signals"]:
        lines.append("- "+item["filename"]+": "+str(item.get("encode_calls",[])))
    lines+=["","## Limitations"]+["- "+x for x in report["limitations"]]
    (out/"summary.md").write_text("\n".join(lines)+"\n",encoding="utf8")
    print("PHASE 9 COMPLETE")
    print("Exact identical embeddings",m["exact_all_components_equal"],"/",len(i))
    print("Cosine >= .999999",m["cosine_ge_0_999999"],"/",len(i))
    print("topic_text median characters",report["text_lengths"].get("topic_text",{}).get("median_characters"))
    print("Reports:",out/"summary.md",out/"embedding_forensics.json")


if __name__=="__main__":
    main()
