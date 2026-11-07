#!/usr/bin/env python3
"""Phase 14: same-document stability of four semantic KMeans representations.

Compares legacy full-text, fresh title+abstract, BODY-only chunks and
their normalized 50/50 hybrid over the SAME 3,629 usable records.
Models, labels, hashes and document IDs never leave private CEDIA folders.
The GitHub report contains only aggregate numerical comparisons.
This is a robustness audit, NOT a validation of policy-topic meaning.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import hashlib
import itertools
import json
import os
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "8")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "8")
os.environ.setdefault("MKL_NUM_THREADS", "8")

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from sklearn.cluster import KMeans
from sklearn.metrics import (
    adjusted_mutual_info_score,
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    normalized_mutual_info_score,
    silhouette_score,
)
from sklearn.preprocessing import normalize
try:
    from threadpoolctl import threadpool_limits
except ImportError:
    threadpool_limits = None


ALLOWED={"include_meta_candidate","include_core_fulltext","include_policy_fulltext"}
MODEL="sentence-transformers/all-MiniLM-L6-v2"
KS=(12,18,25)
NAMES=("bibliographic","legacy_fulltext","body_chunks","hybrid_equal")


def summary(values):
    x=np.asarray(values,dtype=float)
    if not len(x):
        return {}
    return {
        "mean":round(float(x.mean()),5),
        "median":round(float(np.median(x)),5),
        "min":round(float(x.min()),5),
        "max":round(float(x.max()),5),
        "std":round(float(x.std()),5)
    }


def ordered_fingerprint(selected, config):
    """Match original Phase13 hash_input logic to detect changed/parquet order."""
    h=hashlib.sha256()
    h.update(MODEL.encode())
    for key in ("max_chunks","skip_first_tokens","chunk_tokens",
                "overlap","body_end_fraction"):
        h.update((key+":"+str(config[key])+"\n").encode())
    for row in selected.itertuples(index=False):
        for val in (row.openalex_id,row.title,row.abstract,row.full_text):
            raw="" if pd.isna(val) else str(val)
            encoded=raw.encode("utf-8")
            h.update(len(encoded).to_bytes(8,"little"))
            h.update(encoded)
    return h.hexdigest()


def load(root, private, report13):
    source=root/"data/processed/fulltext_topic_model_documents_with_kmeans.parquet"
    original=root/"data/processed/fulltext_topic_model_documents.parquet"
    allowed_columns=set(pq.ParquetFile(source).schema_arrow.names)
    needed={"openalex_id","title","abstract","full_text","ft_decision","text_length",
            "policy_dimension","disciplinary_area"}
    if not needed.issubset(allowed_columns):
        raise ValueError("Missing columns in original full-text table: "+
                         str(sorted(needed-allowed_columns)))
    original_columns=["openalex_id"]
    orig=pd.read_parquet(original,columns=original_columns)
    cols=sorted(needed|{f"kmeans_{k}" for k in KS if f"kmeans_{k}" in allowed_columns})
    allrows=pd.read_parquet(source,columns=cols)
    if len(allrows)!=len(orig) or not allrows["openalex_id"].fillna("").astype(str).equals(
            orig["openalex_id"].fillna("").astype(str)):
        raise ValueError("Original and clustered fulltext parquet row order mismatch")
    ids=allrows["openalex_id"].fillna("").astype(str).str.strip().str.lower().str.rstrip("/")
    if ids.eq("").any() or ids.duplicated().any():
        raise ValueError("Missing or duplicate OpenAlex IDs")
    decision=allrows["ft_decision"].fillna("").astype(str).str.strip().str.lower()
    size=pd.to_numeric(allrows["text_length"],errors="coerce").fillna(0)
    accept=decision.isin(ALLOWED)&(size>0)
    selected=allrows.loc[accept].copy()
    full_indices=np.flatnonzero(accept.to_numpy())
    counts=report13["counts"]
    if len(selected)!=int(counts["explicit_accepted_input_rows"]):
        raise ValueError("Private embeddings and public Phase13 accepted populations disagree")
    expected=len(selected)
    fingerprint_file=private/"input_manifest_private.json"
    if not fingerprint_file.is_file():
        raise ValueError("Phase13 private fingerprint missing")
    fingerprint_manifest=json.loads(fingerprint_file.read_text(encoding="utf-8"))
    args=report13["parameters"]
    configuration={
        "max_chunks":int(args["max_chunks_per_document"]),
        "skip_first_tokens":int(args["first_tokens_excluded"]),
        "chunk_tokens":int(args["chunk_content_tokens"]),
        "overlap":int(args["chunk_overlap"]),
        "body_end_fraction":1-float(args["tail_fraction_excluded"])
    }
    actual=ordered_fingerprint(selected,configuration)
    if fingerprint_manifest.get("fingerprint")!=actual or \
       fingerprint_manifest.get("rows")!=expected:
        raise ValueError("Failed strict Phase13 fingerprint verification: inputs or row order changed")
    arrays={}
    for name,filename in [
        ("bibliographic","full_bibliographic_vectors.npy"),
        ("body_chunks","full_body_vectors.npy"),
        ("number_of_chunks","number_of_chunks.npy")
    ]:
        file=private/filename
        if not file.is_file():
            raise FileNotFoundError("Missing private Phase13 array: "+filename)
        arrays[name]=np.load(file,mmap_mode="r",allow_pickle=False)
    biblio,body,nchunks=(arrays["bibliographic"],arrays["body_chunks"],
                        arrays["number_of_chunks"])
    if biblio.shape!=(expected,384) or body.shape!=(expected,384) or \
       nchunks.shape!=(expected,):
        raise ValueError("Phase13 private arrays have incompatible dimensions")
    usable=(nchunks>0)&np.isfinite(biblio).all(axis=1)&np.isfinite(body).all(axis=1)
    if usable.sum()!=int(counts["eligible_with_body_vectors"]):
        raise ValueError("Phase13 count not consistent with private arrays")
    if (nchunks<0).any():
        raise ValueError("Partial Phase13 cache detected; complete it first")

    legacy=np.load(root/"data/processed/fulltext_topic_embeddings_minilm.npy",
                   mmap_mode="r",allow_pickle=False)
    if legacy.shape!=(len(allrows),384):
        raise ValueError("Legacy fulltext embeddings not aligned to source")
    chosen_rows=full_indices[usable]
    x_b=normalize(np.asarray(biblio[usable],dtype=np.float32))
    x_c=normalize(np.asarray(body[usable],dtype=np.float32))
    x_o=normalize(np.asarray(legacy[chosen_rows],dtype=np.float32))
    x_h=normalize(x_b+x_c)
    if any(not np.isfinite(v).all() for v in (x_b,x_c,x_o,x_h)):
        raise ValueError("Nonfinite vectors in compared representations")
    mat={
        "bibliographic":x_b,
        "legacy_fulltext":x_o,
        "body_chunks":x_c,
        "hybrid_equal":x_h,
    }
    labels={}
    for k in KS:
        name=f"kmeans_{k}"
        if name in selected:
            y=pd.to_numeric(selected.loc[usable,name],errors="coerce")
            if y.notna().all():
                labels[k]=y.to_numpy(dtype=int)
    meta=selected.loc[usable,["policy_dimension","disciplinary_area"]].copy()
    details={
        "fulltext_rows":len(allrows),
        "explicit_acceptances":len(selected),
        "body_usable":int(usable.sum()),
        "body_unusable":int((~usable).sum()),
        "private_input_fingerprint_verified":True,
        "legacy_fulltext_parquet_alignment_verified":True,
        "model":MODEL,
        "dimension":384,
        "comparison_uses_same_document_population":True
    }
    return mat,meta,labels,details,actual


def fit(x,k,seed,n_init):
    model=KMeans(n_clusters=k,random_state=seed,n_init=n_init,max_iter=300)
    y=model.fit_predict(x)
    return model,y


def cluster_metrics(x,labels,k,silhouette_indices):
    sizes=np.bincount(labels,minlength=k)
    subs=labels[silhouette_indices]
    subset_labels=len(set(subs))
    sil=(float(silhouette_score(x[silhouette_indices],
                                subs,metric="cosine"))
         if 2<=subset_labels<len(subs) else float("nan"))
    return {
        "silhouette_cosine_fixed_common_sample":round(sil,6),
        "davies_bouldin":round(float(davies_bouldin_score(x,labels)),6),
        "calinski_harabasz":round(float(calinski_harabasz_score(x,labels)),5),
        "cluster_min_size":int(sizes.min()),
        "cluster_median_size":round(float(np.median(sizes)),2),
        "cluster_max_size":int(sizes.max()),
        "clusters_with_5_or_fewer_documents":int((sizes<=5).sum()),
        "clusters_with_20_or_fewer_documents":int((sizes<=20).sum()),
        "cluster_size_cv":round(float(sizes.std()/sizes.mean()),5)
    }


def experiment(matrices,meta,original_labels,output_private,
               k_values,seeds,n_init,subsamples,frac,sample_n,threads):
    n=len(next(iter(matrices.values())))
    fixed=np.random.default_rng(731).choice(n,size=min(n,sample_n),
                                             replace=False)
    results={}
    context=threadpool_limits(limits=threads) if threadpool_limits else None
    if context:
        context.__enter__()
    try:
        for k in k_values:
            print("Phase14 k=",k,flush=True)
            mods={}
            primary={}
            for name,x in matrices.items():
                seed_labels=[]
                intertia=[]
                for seed in seeds:
                    model,y=fit(x,k,seed,n_init)
                    seed_labels.append(y)
                    intertia.append(float(model.inertia_))
                reference=seed_labels[0]
                private_file=output_private/f"phase14_labels_{name}_k{k}.npy"
                np.save(private_file,np.asarray(reference,dtype=np.int16))
                os.chmod(private_file,0o600)
                primary[name]=reference
                all_pairs=list(itertools.combinations(range(len(seeds)),2))
                stability_ari=[adjusted_rand_score(seed_labels[i],seed_labels[j])
                               for i,j in all_pairs]
                stability_nmi=[normalized_mutual_info_score(seed_labels[i],seed_labels[j])
                               for i,j in all_pairs]
                rng=np.random.default_rng(9000+k)
                resample_aris=[]
                for iteration in range(subsamples):
                    subset=rng.choice(n,size=int(n*frac),replace=False)
                    sub_model=KMeans(n_clusters=k,
                        random_state=1000+iteration*29,n_init=n_init,max_iter=300)
                    sub_model.fit(x[subset])
                    new_labels=sub_model.predict(x)
                    resample_aris.append(adjusted_rand_score(reference,new_labels))
                count=collections.Counter()
                for col in ("policy_dimension","disciplinary_area"):
                    category=meta[col].fillna("[missing]").astype(str)
                    if category.nunique()>1:
                        count[col+"_ami_weak_labels"]=round(float(
                            adjusted_mutual_info_score(category,reference)),5)
                old_agreement={}
                if k in original_labels:
                    old_agreement={
                        "ari":round(float(adjusted_rand_score(original_labels[k],reference)),5),
                        "nmi":round(float(normalized_mutual_info_score(original_labels[k],reference)),5)
                    }
                mods[name]={
                    **cluster_metrics(x,reference,k,fixed),
                    "multi_seed_ari":summary(stability_ari),
                    "multi_seed_nmi":summary(stability_nmi),
                    "resample_fraction":frac,
                    "subsample_fit_vs_reference_ari":summary(resample_aris),
                    "inertia":summary(intertia),
                    "weak_label_concordance_exploratory":dict(count),
                    "agreement_with_legacy_saved_labels":old_agreement
                }
                print(" ",name,"median seed ARI",mods[name]["multi_seed_ari"].get("median"),
                      "silhouette",mods[name]["silhouette_cosine_fixed_common_sample"],
                      flush=True)
            cross={}
            for left,right in itertools.combinations(NAMES,2):
                cross[left+"__"+right]={
                    "ari":round(float(adjusted_rand_score(primary[left],primary[right])),5),
                    "nmi":round(float(normalized_mutual_info_score(primary[left],primary[right])),5)
                }
            results[str(k)]={"models":mods,"between_representations":cross}
    finally:
        if context:
            context.__exit__(None,None,None)
    return results


def write(public,report):
    public.mkdir(parents=True,exist_ok=True)
    (public/"full_corpus_kmeans_comparison.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    text=[
        "# Phase 14 — Comparative full-corpus KMeans stability",
        "","UTC: "+report["generated_utc"],
        "","## Matched population",
        json.dumps(report["population"],indent=2,ensure_ascii=False),
        "","## Model settings",
        json.dumps(report["parameters"],indent=2,ensure_ascii=False)
    ]
    for k,comparisons in report["by_k"].items():
        text+=["","## k = "+k]
        for name,values in comparisons["models"].items():
            text+=["","### "+name,
                   "- cosine silhouette: "+str(values["silhouette_cosine_fixed_common_sample"]),
                   "- stability across random seeds ARI: "+str(values["multi_seed_ari"]),
                   "- 80% subset ARI vs reference: "+str(values["subsample_fit_vs_reference_ari"]),
                   "- cluster sizes: min="+str(values["cluster_min_size"])+
                   ", median="+str(values["cluster_median_size"])+
                   ", <=20="+str(values["clusters_with_20_or_fewer_documents"]),
                   "- weak-label AMI: "+str(values["weak_label_concordance_exploratory"])]
        text+=["","### Between representations",
               str(comparisons["between_representations"])]
    text+=["","## Interpretation limits"]+["- "+z for z in report["limitations"]]
    (public/"summary.md").write_text("\n".join(text)+"\n",encoding="utf-8")


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--project",default=str(Path.home()/"ai_policy_he"))
    parser.add_argument("--private-cache",default=str(Path.home()/"ai_policy_chunks_full_private"))
    parser.add_argument("--private-labels",default=str(Path.home()/"ai_policy_cluster_labels_private"))
    parser.add_argument("--phase13-report",default="reports/phase13/full_corpus_chunk_encoding.json")
    parser.add_argument("--out",default="reports/phase14")
    parser.add_argument("--n-init",type=int,default=10)
    parser.add_argument("--threads",type=int,default=8)
    parser.add_argument("--seeds",type=int,default=3)
    parser.add_argument("--subsamples",type=int,default=3)
    parser.add_argument("--fraction",type=float,default=.8)
    parser.add_argument("--silhouette-sample",type=int,default=1200)
    args=parser.parse_args()
    if args.seeds<3 or args.subsamples<2 or args.n_init<2 or args.threads<1 or \
       not .5<=args.fraction<1 or args.silhouette_sample<300:
        parser.error("Insufficient seed/bootstrap parameters")
    root=Path(args.project).expanduser().resolve()
    cache=Path(args.private_cache).expanduser().resolve()
    labels_dir=Path(args.private_labels).expanduser().resolve()
    public=Path(args.out).expanduser().resolve()
    phase13_report=Path(args.phase13_report).expanduser().resolve()
    repo=Path.home()/"AI_policy"
    if not root.is_dir() or not cache.is_dir() or not phase13_report.is_file():
        parser.error("Project, original cache, or Phase13 report missing")
    for p in (public,labels_dir):
        if p==root or root in p.parents:
            parser.error("Original project must remain read-only")
    if labels_dir==repo or repo in labels_dir.parents or \
       labels_dir==public or public in labels_dir.parents or labels_dir in public.parents:
        parser.error("Per-record labels must be outside GitHub and public reports")
    labels_dir.mkdir(parents=True,exist_ok=True,mode=0o700)
    os.chmod(labels_dir,0o700)
    report13=json.loads(phase13_report.read_text(encoding="utf-8"))
    if report13.get("status")!="completed_vectors_private":
        raise ValueError("Phase13 was not completed; check its public report")
    mat,meta,original_labels,population,private_hash=load(root,cache,report13)
    seeds=[42+i*13 for i in range(args.seeds)]
    label_state=labels_dir/"phase14_manifest_private.json"
    state={"source_private_fingerprint":private_hash,"n":len(meta),
           "model_names":list(mat),"seeds":seeds,"n_init":args.n_init,
           "k_values":list(KS)}
    if label_state.is_file():
        before=json.loads(label_state.read_text(encoding="utf-8"))
        if before!=state:
            raise ValueError("Old Phase14 private-label cache is incompatible; use a new directory")
    else:
        label_state.write_text(json.dumps(state,indent=2),encoding="utf-8")
        os.chmod(label_state,0o600)
    by_k=experiment(mat,meta,original_labels,labels_dir,KS,
                    seeds,args.n_init,args.subsamples,args.fraction,
                    args.silhouette_sample,args.threads)
    report={
        "generated_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
        "status":"completed_exploratory_not_human_validated",
        "population":population,
        "parameters":{
            "modalities":list(NAMES),
            "k_values":list(KS),
            "seeds":seeds,
            "n_init":args.n_init,
            "max_iter":300,
            "subsamples":args.subsamples,
            "subsample_fraction":args.fraction,
            "cosine_silhouette_common_fixed_sample":min(len(meta),args.silhouette_sample),
            "all_inputs_l2_normalized":True,
            "same_publications_for_all_modalities":True
        },
        "by_k":by_k,
        "limitations":[
            "Silhouette is geometric separation, NOT topic coherence, construct validity, or policy usefulness.",
            "The policy_dimension and disciplinary_area labels are algorithmic metadata, not independent human ground truth.",
            "Subsample fits are compared to a seed-42 full-data reference; the ARI is a stability diagnostic, not an accuracy measure.",
            "k=12/18/25 are pre-existing candidate values; higher silhouette alone does not establish optimal k.",
            "The 15 records without eligible body chunks are omitted from ALL compared modalities to preserve the paired population.",
            "Original legacy vectors were obtained through a pipeline subject to severe input token truncation.",
            "The extracted PDF text is character-capped and body segmentation is approximate; full-document coverage is not demonstrated.",
            "The document-level assignments and internal cache fingerprint remain private and are not suitable for public GitHub.",
            "Human adjudication and semantic topic naming remain outstanding, and original manuscript labels are not automatically superseded."
        ]
    }
    write(public,report)
    print("PHASE 14 COMPLETE, paired documents",len(meta))
    print("Report:",public/"summary.md",public/"full_corpus_kmeans_comparison.json")
    print("Private seeded labels remain outside public GitHub")


if __name__=="__main__":
    main()
