#!/usr/bin/env python3
"""Phase 3: reproducibility and robustness of semantic KMeans partitions.

Reads cached MiniLM embeddings; does NOT re-download PDF or re-embed texts.
Uploads only aggregate metrics, no per-document labels/identifiers or texts.
"""
from __future__ import annotations
import argparse
import datetime as dt
import itertools
import json
import os
from pathlib import Path

os.environ.setdefault("OPENBLAS_NUM_THREADS", "8")
os.environ.setdefault("OMP_NUM_THREADS", "8")
os.environ.setdefault("MKL_NUM_THREADS", "8")

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from sklearn.cluster import KMeans
from sklearn.metrics import (adjusted_rand_score, normalized_mutual_info_score,
                             silhouette_score, davies_bouldin_score,
                             calinski_harabasz_score)

try:
    from threadpoolctl import threadpool_limits
except ImportError:
    threadpool_limits = None


def describe(x):
    x = np.asarray(x, dtype=float)
    return {
        "mean": round(float(x.mean()), 5),
        "median": round(float(np.median(x)), 5),
        "min": round(float(x.min()), 5),
        "max": round(float(x.max()), 5),
        "std": round(float(x.std()), 5)
    } if len(x) else {}


def load_meta(file, n):
    cols = set(pq.ParquetFile(file).schema_arrow.names)
    requested = ["openalex_id", "text_length", "ft_decision"] + [
        f"kmeans_{k}" for k in (12, 18, 25)]
    requested = [c for c in requested if c in cols]
    frame = pd.read_parquet(file, columns=requested)
    if len(frame) != n:
        raise ValueError("Metadata/embedding row count mismatch")
    return frame


def original_label_agreement(frame, name, new):
    if name not in frame:
        return {"status": "Original labels unavailable"}
    raw = pd.to_numeric(frame[name], errors="coerce")
    mask = raw.notna().to_numpy()
    if sum(mask) < len(raw)*.99:
        return {"status": "Original labels missing for some rows",
                "nonempty_label_count": int(sum(mask))}
    lab = raw.to_numpy()[mask].astype(int)
    if len(np.unique(lab)) <= 1:
        return {"status": "Original labels have <=1 cluster"}
    return {
        "original_clusters": int(len(np.unique(lab))),
        "adjusted_rand_original_vs_refit": round(
            float(adjusted_rand_score(lab, new[mask])), 5),
        "nmi_original_vs_refit": round(
            float(normalized_mutual_info_score(lab, new[mask])), 5)
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default=str(Path.home()/"ai_policy_he"))
    parser.add_argument("--out", default="reports/phase03")
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--subsamples", type=int, default=5)
    parser.add_argument("--fraction", type=float, default=.8)
    parser.add_argument("--n-init", type=int, default=10)
    parser.add_argument("--threads", type=int, default=8)
    parser.add_argument("--space", choices=["raw","l2"], default="raw")
    args = parser.parse_args()
    if args.seeds < 2 or args.subsamples < 2 or not .5 <= args.fraction < 1:
        parser.error("Need >=2 seeds, >=2 subsamples and 0.5<=fraction<1")
    root = Path(args.project).expanduser().resolve()
    out = Path(args.out).expanduser().resolve()
    if not root.is_dir() or out == root or root in out.parents:
        parser.error("Project must exist and output must be outside original project")
    out.mkdir(parents=True, exist_ok=True)

    embeddings_path = root/"data/processed/fulltext_topic_embeddings_minilm.npy"
    x = np.load(embeddings_path, allow_pickle=False)
    if x.ndim != 2 or x.shape[1] < 2 or not np.isfinite(x).all():
        raise ValueError("Invalid embedding matrix")
    x = np.asarray(x, dtype=np.float32)
    if args.space == "l2":
        norm = np.linalg.norm(x, axis=1, keepdims=True)
        if (norm == 0).any():
            raise ValueError("Zero embedding cannot be L2 normalized")
        x = x/np.maximum(norm, 1e-12)
    metadata = load_meta(
        root/"data/processed/fulltext_topic_model_documents_with_kmeans.parquet",
        len(x))
    original = load_meta(
        root/"data/processed/fulltext_topic_model_documents.parquet",
        len(x))
    if "openalex_id" in original and "openalex_id" in metadata:
        left = original["openalex_id"].fillna("").astype(str)
        right = metadata["openalex_id"].fillna("").astype(str)
        order_verified = bool((left==right).all())
    else:
        order_verified = False
    if not order_verified:
        raise ValueError("Cannot verify document row alignment across fulltext tables")

    text_lens = pd.to_numeric(metadata["text_length"], errors="coerce") if "text_length" in metadata else None
    no_text = (text_lens.fillna(0)<=0).to_numpy() if text_lens is not None else np.zeros(len(x),dtype=bool)
    flags = metadata["ft_decision"].fillna("").astype(str).str.strip().str.lower() if "ft_decision" in metadata else pd.Series([""]*len(x))
    excluded = flags.str.startswith("exclude").to_numpy()
    clean = ~(no_text|excluded)
    source_counts = {
        "all_embeddings": int(len(x)),
        "zero_or_missing_text_length": int(no_text.sum()),
        "fulltext_exclusion_flags": int(excluded.sum()),
        "overlap_invalid_and_excluded": int((no_text&excluded).sum()),
        "clean_subset": int(clean.sum()),
        "row_order_verified_for_two_parquet_tables": order_verified,
        "existing_label_columns": [c for c in metadata.columns if c.startswith("kmeans_")]
    }

    result = {"generated_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
              "parameters":{"k_values":[12,18,25], "seeds":args.seeds,
                            "subsamples":args.subsamples,
                            "fraction":args.fraction, "n_init":args.n_init,
                            "max_iter":300, "space":args.space,
                            "threads":args.threads, "silhouette_sample_size":min(1200,len(x))},
              "source":source_counts,
              "by_k":{}}
    if threadpool_limits:
        ctx = threadpool_limits(limits=args.threads)
        ctx.__enter__()
    else:
        ctx = None
    try:
        for k in (12,18,25):
            models, labels, seeds, inertias = [], [], [], []
            for i in range(args.seeds):
                seed = 42 + i*13
                m = KMeans(n_clusters=k, random_state=seed, n_init=args.n_init,
                           max_iter=300)
                lab = m.fit_predict(x)
                models.append(m)
                labels.append(lab)
                seeds.append(seed)
                inertias.append(float(m.inertia_))
            reference = labels[0]
            pairs = list(itertools.combinations(range(len(labels)),2))
            aris = [adjusted_rand_score(labels[i],labels[j]) for i,j in pairs]
            nmis = [normalized_mutual_info_score(labels[i],labels[j]) for i,j in pairs]
            rng = np.random.default_rng(7000+k)
            sub_ari_all, sub_ari_sample, sub_nmi_all = [],[],[]
            for i in range(args.subsamples):
                selected = rng.choice(len(x),size=int(len(x)*args.fraction),replace=False)
                model = KMeans(n_clusters=k, random_state=120+i*17,
                               n_init=args.n_init, max_iter=300)
                model.fit(x[selected])
                predicted = model.predict(x)
                sub_ari_all.append(adjusted_rand_score(reference,predicted))
                sub_ari_sample.append(adjusted_rand_score(reference[selected],predicted[selected]))
                sub_nmi_all.append(normalized_mutual_info_score(reference,predicted))
            clean_comparison={}
            if clean.sum() >= 5*k and not clean.all():
                fit_clean=KMeans(n_clusters=k,random_state=42,
                                 n_init=args.n_init,max_iter=300).fit(x[clean])
                labels_clean=fit_clean.predict(x)
                clean_comparison={
                    "clean_rows":int(clean.sum()),
                    "excluded_or_textless_rows":int((~clean).sum()),
                    "ari_full_vs_clean_fit_on_retained":round(float(
                        adjusted_rand_score(reference[clean],labels_clean[clean])),5),
                    "nmi_full_vs_clean_fit_on_retained":round(float(
                        normalized_mutual_info_score(reference[clean],labels_clean[clean])),5)
                }
            size=np.bincount(reference,minlength=k)
            row={
                "seeds":seeds,
                "full_corpus_seed_ari":describe(aris),
                "full_corpus_seed_nmi":describe(nmis),
                "inertia":describe(inertias),
                "resampling_ari_full_predictions":describe(sub_ari_all),
                "resampling_ari_on_selected_rows":describe(sub_ari_sample),
                "resampling_nmi_full_predictions":describe(sub_nmi_all),
                "cluster_min_size":int(size.min()),
                "cluster_median_size":float(np.median(size)),
                "cluster_max_size":int(size.max()),
                "davies_bouldin_refit":round(float(davies_bouldin_score(x,reference)),6),
                "calinski_harabasz_refit":round(float(calinski_harabasz_score(x,reference)),6),
                "silhouette_cosine_refit_sample":round(float(silhouette_score(
                    x,reference,metric="cosine",sample_size=min(1200,len(x)),
                    random_state=42)),6),
                "original_label_agreement":original_label_agreement(metadata,
                                                                   f"kmeans_{k}", reference),
                "excluded_textless_sensitivity":clean_comparison
            }
            result["by_k"][str(k)] = row
            print("k=",k,"seed ARI median=",row["full_corpus_seed_ari"].get("median"),
                  "resampling ARI median=",row["resampling_ari_full_predictions"].get("median"),
                  "clean subset rows=",int(clean.sum()), flush=True)
    finally:
        if ctx:
            ctx.__exit__(None,None,None)

    result["warnings"]=[
        "The embedding-array/document alignment is inferred from matching stage order and Parquet ID alignment, not independently cryptographically proven.",
        "Labels of alternative KMeans partitions are arbitrary; ARI/NMI are permutation invariant.",
        "Strong seed stability does not prove semantically distinct or policy-relevant clusters.",
        "Results depend on raw/L2 embedding setting; compare original code before treating refit as identical to manuscript.",
        "Excluded/textless sensitivity removes records flagged by original extraction metadata, not by newly performed human eligibility screening."
    ]
    (out/"kmeans_robustness.json").write_text(json.dumps(
        result,indent=2,ensure_ascii=False),encoding="utf-8")
    summary=["# Phase 3 — KMeans robustness",
             "","Generated: "+result["generated_utc"],
             "","Source: "+str(source_counts),
             "","## Stability and sensitivity"]
    for k, v in result["by_k"].items():
        summary+=["", "### k = "+k,
                  "- seed ARI: "+str(v["full_corpus_seed_ari"]),
                  "- seed NMI: "+str(v["full_corpus_seed_nmi"]),
                  "- resampling ARI full: "+str(v["resampling_ari_full_predictions"]),
                  "- refit cosine silhouette: "+str(v["silhouette_cosine_refit_sample"]),
                  "- refit Davies–Bouldin: "+str(v["davies_bouldin_refit"]),
                  "- refit Calinski–Harabasz: "+str(v["calinski_harabasz_refit"]),
                  "- original model label agreement: "+str(v["original_label_agreement"]),
                  "- exclusion sensitivity: "+str(v["excluded_textless_sensitivity"])]
    summary+=["","## Limits"]+["- "+warning for warning in result["warnings"]]
    (out/"summary.md").write_text("\n".join(summary)+"\n",encoding="utf-8")
    print("PHASE 3 COMPLETE:",out/"summary.md",out/"kmeans_robustness.json")


if __name__=="__main__":
    main()
