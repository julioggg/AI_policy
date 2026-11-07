#!/usr/bin/env python3
"""Phase 12: pilot of BODY-only chunk embeddings versus bibliographic baseline.

Scientific safeguards:
- Paired, fixed-seed stratified sample from explicitly accepted documents only.
- MiniLM is loaded OFFLINE from original CEDIA project virtual environment.
- Body starts AFTER first 512 tokenizer tokens to avoid abstract-first reuse.
- Use at most 12 spaced chunks per document; token-window content 192,
  overlap 32. Decode and re-tokenize chunks; verify none exceed model limit.
- Compare separately: new title+abstract baseline, original cached fulltext,
  body-only mean-pooling, and a simple 50/50 hybrid.
- No title, abstract, full text, IDs, PDF or embedding leaves private CEDIA.
- Public output is aggregate, exploratory. No claims of clinical, policy,
  human-screening validity, and no fabricated performance improvement.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import hashlib
import json
import os
from pathlib import Path

os.environ["HF_HUB_OFFLINE"]="1"
os.environ["TRANSFORMERS_OFFLINE"]="1"
os.environ["HF_DATASETS_OFFLINE"]="1"
os.environ["HF_HUB_DISABLE_TELEMETRY"]="1"
os.environ["TOKENIZERS_PARALLELISM"]="false"
os.environ.setdefault("OMP_NUM_THREADS","8")
os.environ.setdefault("OPENBLAS_NUM_THREADS","8")
os.environ.setdefault("MKL_NUM_THREADS","8")

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from numpy.lib.format import open_memmap
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score, silhouette_score
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import normalize

ALLOWED = {"include_meta_candidate","include_core_fulltext","include_policy_fulltext"}
MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def hist_summary(numbers):
    arr=np.asarray(numbers,dtype=float)
    return {
        "min":round(float(np.min(arr)),5),
        "p10":round(float(np.quantile(arr,.1)),5),
        "median":round(float(np.median(arr)),5),
        "p90":round(float(np.quantile(arr,.9)),5),
        "max":round(float(np.max(arr)),5),
        "mean":round(float(np.mean(arr)),5)
    }


def stratum_sample(eligible, target, seed, min_per=18):
    if target>=len(eligible):
        return eligible.copy().sort_index()
    rng=np.random.default_rng(seed)
    selected=set()
    labels=eligible["policy_dimension"].fillna("[missing]").astype(str)
    for _, values in eligible.groupby(labels,sort=True):
        k=min(len(values),min_per)
        selected.update(rng.choice(values.index.to_numpy(),size=k,replace=False).tolist())
    if len(selected)>target:
        selected=set(rng.choice(np.array(sorted(selected)),size=target,replace=False).tolist())
    remaining=eligible.loc[~eligible.index.isin(selected)]
    extra=target-len(selected)
    if extra>0:
        selected.update(rng.choice(remaining.index.to_numpy(),size=extra,replace=False).tolist())
    return eligible.loc[sorted(selected)]


def text_chops(text,tokenizer,max_chunks,skip,content_tokens,overlap,body_fraction):
    ids=tokenizer.encode(str(text),add_special_tokens=False,truncation=False)
    cutoff=int(len(ids)*body_fraction)
    body=ids[skip:cutoff]
    if len(body)<content_tokens:
        return [],len(ids),len(body),0
    step=content_tokens-overlap
    starts=list(range(0,len(body)-content_tokens+1,step))
    if starts and starts[-1] !=len(body)-content_tokens:
        starts.append(len(body)-content_tokens)
    if len(starts)>max_chunks:
        picks=np.rint(np.linspace(0,len(starts)-1,max_chunks)).astype(int)
        starts=[starts[k] for k in sorted(set(picks))]
    chunks=[]
    for start in starts:
        phrase=tokenizer.decode(body[start:start+content_tokens],skip_special_tokens=True,
                                 clean_up_tokenization_spaces=False)
        if phrase.strip():
            count=len(tokenizer.encode(phrase,add_special_tokens=True,truncation=False))
            if count>256:
                # Token recombination can occasionally add a few tokens.
                phrase=tokenizer.decode(body[start:start+content_tokens-12],
                                        skip_special_tokens=True,
                                        clean_up_tokenization_spaces=False)
                count=len(tokenizer.encode(phrase,add_special_tokens=True,truncation=False))
            if count>256:
                raise ValueError("Chunk exceeds MiniLM token budget")
            chunks.append(phrase)
    return chunks,len(ids),len(body),len(starts)


def cosines(a,b):
    return np.einsum("ij,ij->i",a,b)


def kmeans_compare(matrices,seed):
    output={}
    for k in (12,18,25):
        labels={}
        values={}
        for key,X in matrices.items():
            lab=KMeans(n_clusters=k,random_state=seed,n_init=10,max_iter=300).fit_predict(X)
            labels[key]=lab
            values[key]={
                "cosine_silhouette_sample":round(float(silhouette_score(
                    X,lab,metric="cosine",sample_size=min(len(X),220),
                    random_state=seed)),5),
                "min_cluster_size":int(np.bincount(lab,minlength=k).min())
            }
        paired={}
        names=list(matrices)
        for i in range(len(names)):
            for j in range(i+1,len(names)):
                u,v=names[i],names[j]
                paired[u+"__"+v]={
                    "ari":round(float(adjusted_rand_score(labels[u],labels[v])),5),
                    "nmi":round(float(normalized_mutual_info_score(labels[u],labels[v])),5)
                }
        output[str(k)]={"models":values,"cross_modality":paired}
    return output


def neighbors_agreement(a,b,k=10):
    n=len(a)
    if n<k+1:
        return {}
    ix_a=NearestNeighbors(n_neighbors=k+1,metric="cosine").fit(a).kneighbors(
        a,return_distance=False)[:,1:]
    ix_b=NearestNeighbors(n_neighbors=k+1,metric="cosine").fit(b).kneighbors(
        b,return_distance=False)[:,1:]
    overlap=[len(set(x)&set(y))/k for x,y in zip(ix_a,ix_b)]
    return {"top_k":k,"overlap_fraction":hist_summary(overlap)}


def public_report(out,result):
    out.mkdir(parents=True,exist_ok=True)
    (out/"body_chunk_pilot.json").write_text(json.dumps(
        result,ensure_ascii=False,indent=2),encoding="utf8")
    lines=["# Phase 12 — Pilot: title/abstract vs BODY-only chunk embeddings",
           "","Status: "+result["status"],
           "UTC: "+result["created_utc"],"",
           "## Source and sampling",
           json.dumps(result.get("sample",{}),indent=2,ensure_ascii=False),
           "","## Configuration",json.dumps(result.get("parameters",{}),indent=2),
           "","## Summary"]
    for key,val in result.get("results",{}).items():
        lines.extend(["### "+key,str(val)])
    lines+=["","## Limitations"]+["- "+x for x in result["limitations"]]
    (out/"summary.md").write_text("\n".join(lines)+"\n",encoding="utf8")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--project",default=str(Path.home()/"ai_policy_he"))
    p.add_argument("--out",default="reports/phase12")
    p.add_argument("--private-cache",default=str(Path.home()/"ai_policy_chunk_private"))
    p.add_argument("--sample-size",type=int,default=240)
    p.add_argument("--max-chunks",type=int,default=12)
    p.add_argument("--skip-first-tokens",type=int,default=512)
    p.add_argument("--chunk-tokens",type=int,default=192)
    p.add_argument("--overlap",type=int,default=32)
    p.add_argument("--body-end-fraction",type=float,default=.85)
    p.add_argument("--batch-size",type=int,default=32)
    p.add_argument("--threads",type=int,default=8)
    p.add_argument("--seed",type=int,default=20261107)
    args=p.parse_args()
    if args.sample_size<100 or args.max_chunks<2 or args.threads<1 or args.batch_size<1:
        p.error("Invalid sampling/batch/thread settings")
    if not 1<=args.skip_first_tokens or not 20<=args.chunk_tokens<=240 or \
       not 0<=args.overlap<args.chunk_tokens or not .5<=args.body_end_fraction<=1:
        p.error("Invalid token-window and body-boundary options")
    root=Path(args.project).expanduser().resolve()
    out=Path(args.out).expanduser().resolve()
    private=Path(args.private_cache).expanduser().resolve()
    repo=Path.home()/"AI_policy"
    if not root.is_dir():
        p.error("Original source project missing")
    if out==root or root in out.parents or private==root or root in private.parents:
        p.error("Outputs cannot go inside original project")
    if private==repo or repo in private.parents or private==out or out in private.parents or private in out.parents:
        p.error("Private cache must be outside GitHub and public output")
    private.mkdir(parents=True,exist_ok=True,mode=0o700)
    os.chmod(private,0o700)
    out.mkdir(parents=True,exist_ok=True)
    import torch
    from sentence_transformers import SentenceTransformer
    torch.set_num_threads(args.threads)

    file=root/"data/processed/fulltext_topic_model_documents_with_kmeans.parquet"
    allowed=set(pq.ParquetFile(file).schema_arrow.names)
    required={"openalex_id","title","abstract","full_text","ft_decision",
              "text_length","policy_dimension"}
    if not required.issubset(allowed):
        raise ValueError("Required fulltext metadata unavailable: "+str(sorted(required-allowed)))
    df=pd.read_parquet(file,columns=sorted(required))
    if df["openalex_id"].fillna("").astype(str).duplicated().any():
        raise ValueError("Duplicate OpenAlex IDs in fulltext")
    status=df["ft_decision"].fillna("").astype(str).str.strip().str.lower()
    leng=pd.to_numeric(df["text_length"],errors="coerce").fillna(0)
    eligible=df.loc[status.isin(ALLOWED) & (leng>0)].copy()
    chosen=stratum_sample(eligible,min(args.sample_size,len(eligible)),args.seed)
    chosen=chosen.loc[chosen["abstract"].fillna("").astype(str).str.len()>=20]
    if len(chosen)<100:
        raise ValueError("Too few selected paired documents")
    model=SentenceTransformer(MODEL,device="cpu")
    tokenizer=model.tokenizer
    if int(model.max_seq_length)!=256:
        raise ValueError("Model token budget changed; expected 256. Audit before proceeding")
    base_file=root/"data/processed/fulltext_topic_embeddings_minilm.npy"
    x_original=np.load(base_file,mmap_mode="r",allow_pickle=False)
    if x_original.shape!=(len(df),384):
        raise ValueError("Cached original fulltext matrix shape differs")
    indices=chosen.index.to_numpy()
    source_hash=hashlib.sha256(
        ("\n".join(chosen["openalex_id"].astype(str))+"\n"+
         "\n".join(chosen["full_text"].fillna("").astype(str))+"\n"+
         "\n".join(chosen["abstract"].fillna("").astype(str))+
         json.dumps(vars(args),sort_keys=True)).encode("utf8")
    ).hexdigest()
    state_file=private/"pilot_state.json"
    if state_file.is_file():
        state=json.loads(state_file.read_text(encoding="utf8"))
        if state["input_fingerprint"]!=source_hash:
            raise ValueError("Private cache is from a different pilot configuration; choose a new private-cache folder")
    else:
        state={"input_fingerprint":source_hash,"n":len(chosen),"model":MODEL}
        state_file.write_text(json.dumps(state,indent=2),encoding="utf8")
        os.chmod(state_file,0o600)
    baseline_file=private/"pilot_bibliographic_vectors.npy"
    body_file=private/"pilot_body_chunk_vectors.npy"
    def open_array(path):
        if not path.exists():
            a=open_memmap(path,mode="w+",dtype="float32",shape=(len(chosen),384))
            a[:]=np.nan
            a.flush()
            os.chmod(path,0o600)
            return a
        a=np.load(path,mmap_mode="r+")
        if a.shape!=(len(chosen),384):
            raise ValueError("Incompatible cached array "+path.name)
        return a
    baseline=open_array(baseline_file)
    body=open_array(body_file)
    nchunks=[]
    lengths=[]
    usable=[]
    body_tokens=[]
    for j,(_,row) in enumerate(chosen.iterrows()):
        chunks,total,body_available,positions=text_chops(
            row["full_text"],tokenizer,args.max_chunks,args.skip_first_tokens,
            args.chunk_tokens,args.overlap,args.body_end_fraction)
        nchunks.append(len(chunks))
        lengths.append(total)
        body_tokens.append(body_available)
        if len(chunks)==0:
            usable.append(False)
            continue
        usable.append(True)
        if np.isfinite(baseline[j]).all() and np.isfinite(body[j]).all():
            continue
        biblio=str(row["title"] or "")+". "+str(row["abstract"] or "")
        enc_biblio=model.encode([biblio],batch_size=1,
            show_progress_bar=False,normalize_embeddings=True,convert_to_numpy=True)[0]
        emb_chunks=model.encode(chunks,batch_size=args.batch_size,
            show_progress_bar=False,normalize_embeddings=True,convert_to_numpy=True)
        average=np.mean(emb_chunks,axis=0)
        normal=np.linalg.norm(average)
        if not np.isfinite(normal) or normal<1e-8:
            raise ValueError("Invalid body embedding")
        baseline[j]=np.asarray(enc_biblio,dtype="float32")
        body[j]=np.asarray(average/normal,dtype="float32")
        if (j+1)%12==0:
            baseline.flush();body.flush()
            print("Embedded",j+1,"of",len(chosen),flush=True)
    baseline.flush();body.flush()
    mask=np.asarray(usable,dtype=bool)
    if mask.sum()<100:
        raise ValueError("Pilot has fewer than 100 usable body embeddings")
    xb=normalize(np.asarray(baseline[mask],dtype="float32"))
    xbody=normalize(np.asarray(body[mask],dtype="float32"))
    xold=normalize(np.asarray(x_original[indices[mask]],dtype="float32"))
    xhyb=normalize(xb+xbody)
    if not all(np.isfinite(q).all() for q in (xb,xbody,xold,xhyb)):
        raise ValueError("Nonfinite vectors in paired matrices")
    matrices={"bibliographic":xb,"original_fulltext":xold,
              "body_chunks":xbody,"hybrid_50_50":xhyb}
    results={
        "truncation_avoidance":{
            "mean_pooled_chunks_per_document":hist_summary(np.asarray(nchunks)[mask]),
            "fulltext_wordpiece_tokens":hist_summary(np.asarray(lengths)[mask]),
            "body_available_wordpiece_tokens":hist_summary(np.asarray(body_tokens)[mask]),
            "documents_no_body_after_skip_and_tail":int((~mask).sum()),
            "chunking_skips_first_tokens":args.skip_first_tokens,
            "model_limit_tokens":int(model.max_seq_length)
        },
        "paired_cosine":{
            "bibliographic_vs_body_chunks":hist_summary(cosines(xb,xbody)),
            "bibliographic_vs_original_fulltext":hist_summary(cosines(xb,xold)),
            "body_chunks_vs_original_fulltext":hist_summary(cosines(xbody,xold))
        },
        "nearest_neighbor_overlap":{
            "bibliographic_vs_body_chunks":neighbors_agreement(xb,xbody),
            "bibliographic_vs_hybrid":neighbors_agreement(xb,xhyb)
        },
        "kmeans_exploratory":kmeans_compare(matrices,args.seed)
    }
    result={
        "status":"completed_pilot_no_human_validation",
        "created_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
        "sample":{
            "explicitly_eligible_pool":int(len(eligible)),
            "selected":int(len(chosen)),
            "analyzable_paired":int(mask.sum()),
            "strata_counts":dict(sorted(
                (str(k),int(v)) for k,v in chosen.loc[mask,"policy_dimension"].value_counts().items()
                if v>=5)),
            "seed":args.seed
        },
        "parameters":{
            "model":MODEL,"model_max_seq_length":256,
            "max_body_chunks":args.max_chunks,
            "first_tokens_excluded":args.skip_first_tokens,
            "body_end_fraction":args.body_end_fraction,
            "chunk_content_tokens":args.chunk_tokens,
            "chunk_overlap_tokens":args.overlap,
            "chunk_selection":"uniformly spaced over full_text after the first 512 tokens and before the last 15%",
            "pooling":"unweighted mean of normalized chunk vectors then L2 normalization",
            "hybrid":"L2-normalized sum of bibliographic and body vectors",
            "device":"cpu"
        },
        "results":results,
        "limitations":[
            "This is an exploratory stratified pilot, not a preregistered confirmatory test.",
            "Higher silhouette does not imply semantic truth, utility or improved policy classification.",
            "The first 512 tokens and final 15 percent are excluded as a transparent heuristic, not validated section segmentation.",
            "Original fulltext vectors were computed by the legacy pipeline and may have truncated to bibliographic prefixes.",
            "KMeans partitions in a small pilot are unstable; do not replace manuscript topic taxonomy using pilot alone.",
            "No independent human annotations exist yet; evaluate them before claiming substantive policy relevance.",
            "New privately cached vectors are NOT added to GitHub; only aggregate metrics are reported."
        ]
    }
    public_report(out,result)
    print("PHASE 12 PILOT COMPLETE:",int(mask.sum()),"paired documents")
    print("Mean cosine bibliography/body:",results["paired_cosine"]["bibliographic_vs_body_chunks"]["mean"])
    print("Reports:",out/"summary.md",out/"body_chunk_pilot.json")
    print("PRIVATE embeddings remain outside GitHub")


if __name__=="__main__":
    main()
