#!/usr/bin/env python3
"""Phase 8: paired abstract-vs-fulltext semantic embedding comparison.

Source project is never modified; no title, abstract, document identifier,
PDF, full text or embedding is published. Newly encoded ABSTRACT vectors are
cached outside the public GitHub repository in a private CEDIA directory.

We verify alignment of the existing full-text matrix against locally
re-encoded topic_text BEFORE computing comparisons. This does not prove
the full text itself was validly extracted.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"
os.environ.setdefault("OMP_NUM_THREADS", "8")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "8")

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from sklearn.cluster import KMeans
from sklearn.metrics import (
    adjusted_rand_score, normalized_mutual_info_score,
    silhouette_score, f1_score, balanced_accuracy_score
)
from sklearn.model_selection import GroupKFold
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import normalize
try:
    from sklearn.model_selection import StratifiedGroupKFold
except ImportError:
    StratifiedGroupKFold = None


def report_write(public, result):
    public.mkdir(parents=True,exist_ok=True)
    (public/"abstract_fulltext_comparison.json").write_text(
        json.dumps(result,indent=2,ensure_ascii=False,default=str),encoding="utf-8")
    summary=["# Phase 8 — Paired abstract/fulltext experiment","",
             "Status: "+result.get("status","unknown"),
             "UTC: "+result.get("created_utc",""),"",
             "## Alignment preflight"]
    for key,val in result.get("preflight",{}).items():
        summary.append("- "+key+": "+str(val))
    for key,val in result.get("analyses",{}).items():
        summary+=["","## "+key,"- "+str(val)]
    summary+=["","## Interpretation constraints"]
    summary+=["- "+line for line in result.get("limitations",[])]
    (public/"summary.md").write_text("\n".join(summary)+"\n",encoding="utf-8")


def model_load(model_name, threads):
    try:
        import torch
        torch.set_num_threads(threads)
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError(
            "Please use the existing CEDIA NLP environment with torch and sentence-transformers."
        ) from exc
    # Force offline mode. The original model must already exist in CEDIA cache.
    return SentenceTransformer(model_name, device="cpu")


def cosine_rows(a,b):
    a=normalize(np.asarray(a,dtype=np.float32))
    b=normalize(np.asarray(b,dtype=np.float32))
    return np.einsum("ij,ij->i",a,b)


def document_hash(ids):
    encoded="\n".join(ids.fillna("").astype(str).tolist()).encode("utf8")
    return hashlib.sha256(encoded).hexdigest()


def predict_target(x,y,groups,threads,seed):
    if len(set(y))<2:
        return {"error":"Insufficient categories"}
    if StratifiedGroupKFold is not None:
        splitter=StratifiedGroupKFold(n_splits=5,shuffle=True,random_state=seed)
        scheme="StratifiedGroupKFold"
    else:
        splitter=GroupKFold(n_splits=5)
        scheme="GroupKFold"
    folds=[]
    try:
        splits=list(splitter.split(x,y,groups))
    except ValueError as e:
        return {"error_type":type(e).__name__,"scheme":scheme}
    for train,test in splits:
        clf=LogisticRegression(max_iter=1200,class_weight="balanced")
        clf.fit(x[train],y[train])
        predicted=clf.predict(x[test])
        labels=np.unique(y)
        folds.append({
            "macro_f1":float(f1_score(y[test],predicted,average="macro",
                                       labels=labels,zero_division=0)),
            "balanced_accuracy":float(balanced_accuracy_score(y[test],predicted)),
            "test_rows":int(len(test))
        })
    return {"scheme":scheme,"folds":folds,
            "mean_macro_f1":round(float(np.mean([v["macro_f1"] for v in folds])),5),
            "mean_balanced_accuracy":round(float(np.mean([v["balanced_accuracy"] for v in folds])),5)}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--project",default=str(Path.home()/"ai_policy_he"))
    ap.add_argument("--out",default="reports/phase08")
    ap.add_argument("--private-cache",default=str(Path.home()/"ai_policy_comparison_private"))
    ap.add_argument("--threads",type=int,default=8)
    ap.add_argument("--batch-size",type=int,default=64)
    ap.add_argument("--seed",type=int,default=42)
    ap.add_argument("--model",default="sentence-transformers/all-MiniLM-L6-v2")
    args=ap.parse_args()
    root=Path(args.project).expanduser().resolve()
    public=Path(args.out).expanduser().resolve()
    private=Path(args.private_cache).expanduser().resolve()
    repo=Path.home()/"AI_policy"
    if not root.is_dir() or args.threads<1 or args.batch_size<1:
        ap.error("Valid existing project and positive threading/batch-size required")
    if root==public or root in public.parents or root==private or root in private.parents:
        ap.error("Outputs cannot be written inside original CEDIA project")
    if private==repo or repo in private.parents:
        ap.error("Private embeddings must be OUTSIDE the public GitHub repository")
    if public==private or private in public.parents or public in private.parents:
        ap.error("Public and private output folders must not overlap")
    private.mkdir(parents=True,exist_ok=True,mode=0o700)
    os.chmod(private,0o700)
    public.mkdir(parents=True,exist_ok=True)

    file=root/"data/processed/fulltext_topic_model_documents_with_kmeans.parquet"
    columns=set(pq.ParquetFile(file).schema_arrow.names)
    required={"openalex_id","title","abstract","topic_text",
              "ft_decision","text_length","policy_dimension","disciplinary_area"}
    if not required.issubset(columns):
        raise ValueError("Missing required full-text columns: "+", ".join(sorted(required-columns)))
    df=pd.read_parquet(file,columns=sorted(required))
    original_file=root/"data/processed/fulltext_topic_model_documents.parquet"
    raw_ids=pd.read_parquet(original_file,columns=["openalex_id"])["openalex_id"]
    if not df["openalex_id"].fillna("").astype(str).equals(raw_ids.fillna("").astype(str)):
        raise ValueError("Parquet row order mismatch between fulltext and clustered tables")

    stored=np.load(root/"data/processed/fulltext_topic_embeddings_minilm.npy",allow_pickle=False)
    if stored.shape!=(len(df),384):
        raise ValueError("Stored embeddings and fulltext metadata incompatible")
    if not np.isfinite(stored).all():
        raise ValueError("Stored embeddings contain NaN or infinite values")
    status=df["ft_decision"].fillna("").astype(str).str.lower().str.strip()
    text_length=pd.to_numeric(df["text_length"],errors="coerce")
    explicit=status.isin({"include_meta_candidate","include_core_fulltext",
                          "include_policy_fulltext"})
    keep=explicit&(text_length>0)
    if int(keep.sum())<1000:
        raise ValueError("Too few explicit accepts for paired comparison")
    rowhash=document_hash(df["openalex_id"])

    report={
        "created_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
        "status":"preflight",
        "preflight":{
            "model":args.model, "source_rows":len(df),
            "explicit_accepted_with_nonzero_text":int(keep.sum()),
            "excluded_or_unclear_rows":int((~keep).sum()),
            "missing_abstract_in_accepted":int((
                df.loc[keep,"abstract"].fillna("").astype(str).str.len()<20).sum()),
            "stored_embedding_shape":list(stored.shape),
            "row_order_sha256":rowhash,
            "embedding_source_field":"topic_text",
            "encoding_offline":True
        },
        "limitations":[
            "The existing fulltext embeddings must match the topic_text field; alignment is checked on a random sample.",
            "Automated policy_dimension labels are weak proxy outcomes, NOT human-validated ground truth.",
            "Predictive comparisons cannot establish regulatory or educational policy value without expert validation.",
            "Random unsupervised topic IDs have no intrinsic semantic meaning; use ARI/NMI only for label agreement.",
            "Both modalities are evaluated on the same subset to avoid corpus-size confounding.",
            "No private embeddings or copyrighted texts are exported."
        ]
    }
    rng=np.random.default_rng(args.seed)
    indices=rng.choice(np.flatnonzero(keep.to_numpy()),size=min(64,int(keep.sum())),replace=False)
    try:
        model=model_load(args.model,args.threads)
    except Exception as exc:
        report["status"]="blocked_missing_offline_model"
        report["preflight"]["error_type"]=type(exc).__name__
        report_write(public,report)
        print("PHASE 8 BLOCKED: original MiniLM model not available offline.")
        print("See reports/phase08/summary.md; no new embeddings computed.")
        return

    checktext=df.iloc[indices]["topic_text"].fillna("").astype(str).tolist()
    check=model.encode(checktext,batch_size=args.batch_size,
                       show_progress_bar=False,convert_to_numpy=True)
    alignment=cosine_rows(check,stored[indices])
    baseline=cosine_rows(check,stored[indices[::-1]])
    report["preflight"].update({
        "alignment_sample_rows":int(len(indices)),
        "matching_cosine_median":round(float(np.median(alignment)),5),
        "matching_cosine_p10":round(float(np.quantile(alignment,.1)),5),
        "permuted_cosine_median":round(float(np.median(baseline)),5)
    })
    if np.median(alignment)<.82 or np.median(alignment)-np.median(baseline)<.12:
        report["status"]="blocked_alignment_not_verified"
        report_write(public,report)
        print("PHASE 8 BLOCKED: stored embeddings were not reliably reproduced.")
        print("Check original fulltext embedding preprocessing in CEDIA before comparison.")
        return

    accepted_indices=np.flatnonzero(keep.to_numpy())
    x_full=normalize(np.asarray(stored[accepted_indices],dtype=np.float32))
    title=df.iloc[accepted_indices]["title"].fillna("").astype(str).str.strip()
    abstract=df.iloc[accepted_indices]["abstract"].fillna("").astype(str).str.strip()
    inputs=(title+" [SEP] "+abstract).str.strip().tolist()
    cache_file=private/"miniLM_title_abstract_embeddings.npy"
    manifest=private/"miniLM_title_abstract_cache.json"
    fp=hashlib.sha256(
        ("\n".join(inputs)+"\n"+args.model+"\n"+rowhash).encode("utf8")
    ).hexdigest()
    from_cache=False
    if cache_file.is_file() and manifest.is_file():
        meta=json.loads(manifest.read_text(encoding="utf8"))
        if meta.get("fingerprint")==fp:
            x_abs=np.load(cache_file,allow_pickle=False)
            from_cache=True
    if not from_cache:
        x_abs=model.encode(inputs,batch_size=args.batch_size,
                           show_progress_bar=True,convert_to_numpy=True)
        np.save(cache_file,np.asarray(x_abs,dtype=np.float32))
        manifest.write_text(json.dumps({
            "fingerprint":fp,"rows":len(inputs),"model":args.model
        },indent=2),encoding="utf8")
        os.chmod(cache_file,0o600)
        os.chmod(manifest,0o600)
    x_abs=normalize(np.asarray(x_abs,dtype=np.float32))
    if x_abs.shape!=x_full.shape or not np.isfinite(x_abs).all():
        raise ValueError("Cached abstract embeddings do not align with expected rows")
    c=cosine_rows(x_abs,x_full)
    analyses={
        "embeddings":{
            "evaluated_rows":len(x_abs),
            "reused_private_abstract_cache":from_cache,
            "paired_cosine_median":round(float(np.median(c)),5),
            "paired_cosine_p10":round(float(np.quantile(c,.1)),5),
            "paired_cosine_p90":round(float(np.quantile(c,.9)),5)
        }
    }
    for k in [12,18,25]:
        mf=KMeans(n_clusters=k,random_state=args.seed,n_init=10,max_iter=300)
        ma=KMeans(n_clusters=k,random_state=args.seed,n_init=10,max_iter=300)
        lf=mf.fit_predict(x_full)
        la=ma.fit_predict(x_abs)
        analyses["kmeans_"+str(k)]={
            "ari_between_modality_partitions":round(float(adjusted_rand_score(lf,la)),5),
            "nmi_between_modality_partitions":round(float(normalized_mutual_info_score(lf,la)),5),
            "cosine_silhouette_fulltext":round(float(silhouette_score(
                x_full,lf,metric="cosine",sample_size=min(1000,len(lf)),random_state=args.seed)),5),
            "cosine_silhouette_title_abstract":round(float(silhouette_score(
                x_abs,la,metric="cosine",sample_size=min(1000,len(la)),random_state=args.seed)),5)
        }
    key=df.iloc[accepted_indices]["openalex_id"].fillna("").astype(str)
    # DOIs are more appropriate for grouping versions, but this phase's
    # selected table is not read with DOI; OpenAlex IDs guard only exact record repeats.
    groups=key.to_numpy()
    targets={}
    for field in ["policy_dimension","disciplinary_area"]:
        values=df.iloc[accepted_indices][field].fillna("[missing]").astype(str)
        frequent=values.value_counts()
        target_mask=values.isin(set(frequent[frequent>=40].index)).to_numpy()
        if int(target_mask.sum())<500:
            continue
        label=values[target_mask].to_numpy()
        target_groups=groups[target_mask]
        # Same stratified/group folds and target definition for both modalities.
        targets[field]={
            "rows":int(target_mask.sum()),
            "categories":int(len(set(label))),
            "fulltext":predict_target(x_full[target_mask],label,target_groups,args.threads,args.seed),
            "title_abstract":predict_target(x_abs[target_mask],label,target_groups,args.threads,args.seed)
        }
    analyses["weak_label_prediction"]=targets
    report["analyses"]=analyses
    report["status"]="completed"
    report_write(public,report)
    print("PHASE 8 COMPLETE: paired modalities",len(x_abs))
    print("Alignment cosine median",report["preflight"]["matching_cosine_median"])
    for k in (12,18,25):
        print("k",k,"ARI modalities",analyses["kmeans_"+str(k)]["ari_between_modality_partitions"])
    print("Reports:",public/"summary.md",public/"abstract_fulltext_comparison.json")
    print("Private abstract cache (DO NOT PUSH):",private)


if __name__=="__main__":
    main()
