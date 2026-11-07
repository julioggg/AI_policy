#!/usr/bin/env python3
"""Phase 15 — Prepare BLINDED, PRIVATE expert validation of topic partitions.

Pure preparation: no simulated annotators, invented labels or human assessments.
Compare preregistered candidate topic partitions from Phase 14:
    body_chunks K=12, body_chunks K=18, hybrid_equal K=18.
Uses exactly the same 3629 matched records, verifies Phase 13's input
fingerprint and Phase 14's saved-label manifest. Generates two independent
rater workbooks as CSV, a PRIVATE key and an aggregate public sampling report.

NEVER git add $HOME/ai_policy_topic_validation_private. Titles, abstracts,
body excerpts, OpenAlex IDs, labels and correspondence keys stay private.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from sklearn.preprocessing import normalize

MODEL = "sentence-transformers/all-MiniLM-L6-v2"
ALLOWED = {"include_meta_candidate", "include_core_fulltext",
           "include_policy_fulltext"}
CANDIDATES = [
    ("body_chunks", 12),
    ("body_chunks", 18),
    ("hybrid_equal", 18),
]


def input_fingerprint(selected, params):
    h = hashlib.sha256()
    h.update(MODEL.encode("utf8"))
    cfg = {
        "max_chunks": int(params["max_chunks_per_document"]),
        "skip_first_tokens": int(params["first_tokens_excluded"]),
        "chunk_tokens": int(params["chunk_content_tokens"]),
        "overlap": int(params["chunk_overlap"]),
        "body_end_fraction": 1-float(params["tail_fraction_excluded"]),
    }
    for key in ("max_chunks","skip_first_tokens","chunk_tokens",
                "overlap","body_end_fraction"):
        h.update((key+":"+str(cfg[key])+"\n").encode("utf8"))
    for row in selected.itertuples(index=False):
        for val in (row.openalex_id,row.title,row.abstract,row.full_text):
            s = "" if pd.isna(val) else str(val)
            b = s.encode("utf8")
            h.update(len(b).to_bytes(8,"little"))
            h.update(b)
    return h.hexdigest()


def write_csv(file, rows, cols):
    with file.open("w",newline="",encoding="utf-8-sig") as stream:
        writer=csv.DictWriter(stream,fieldnames=cols,extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    os.chmod(file,0o600)


def safe_text(value,limit):
    if pd.isna(value):
        return ""
    return " ".join(str(value).split())[:limit]


def body_excerpt(text):
    raw=str(text or "")
    size=len(raw)
    # Body-only context, avoiding most front matter and final references.
    # The phase13 inputs are character-capped, so excerpts do NOT prove
    # coverage or rhetorical-section identification.
    if size<1600:
        return raw[:900], raw[900:1500]
    start1=max(800,int(size*.38))
    start2=max(start1+800,int(size*.64))
    return (safe_text(raw[start1:start1+900],900),
            safe_text(raw[start2:start2+900],900))


def select_stratified(x, labels, seed, per_topic):
    rng=np.random.default_rng(seed)
    groups={}
    for lab in sorted(np.unique(labels)):
        rows=np.flatnonzero(labels==lab)
        center=normalize(x[rows].mean(axis=0).reshape(1,-1))[0]
        similarity=x[rows]@center
        close=rows[np.argsort(-similarity)]
        # 3 prototypes, 3 random, 1 peripheral = 7 items per topic.
        representative=close[:min(3,len(rows))].tolist()
        distant=[int(v) for v in close[::-1] if v not in representative][:1]
        selected=set(representative+distant)
        pool=np.asarray([v for v in rows if int(v) not in selected],dtype=int)
        n_random=min(max(0,per_topic-len(selected)),len(pool))
        randoms=rng.choice(pool,size=n_random,replace=False).tolist() if n_random else []
        chosen=representative+randoms+distant
        if len(chosen)<per_topic:
            raise ValueError("Topic does not contain enough documents")
        role=["prototype"]*len(representative)+["random"]*len(randoms)+["peripheral"]*len(distant)
        groups[int(lab)]=list(zip(chosen,role))
    return groups


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--project",default=str(Path.home()/"ai_policy_he"))
    ap.add_argument("--phase13-cache",default=str(Path.home()/"ai_policy_chunks_full_private"))
    ap.add_argument("--phase14-labels",default=str(Path.home()/"ai_policy_cluster_labels_private"))
    ap.add_argument("--phase13-report",default="reports/phase13/full_corpus_chunk_encoding.json")
    ap.add_argument("--out",default="reports/phase15")
    ap.add_argument("--private-out",default=str(Path.home()/"ai_policy_topic_validation_private"))
    ap.add_argument("--seed",type=int,default=20261107)
    ap.add_argument("--per-topic",type=int,default=7)
    args=ap.parse_args()
    if args.per_topic<5 or args.per_topic>10:
        ap.error("Per-topic size must be between 5 and 10")
    root=Path(args.project).expanduser().resolve()
    cache=Path(args.phase13_cache).expanduser().resolve()
    labels_dir=Path(args.phase14_labels).expanduser().resolve()
    out=Path(args.out).expanduser().resolve()
    private=Path(args.private_out).expanduser().resolve()
    repo=Path.home()/"AI_policy"
    if not root.is_dir() or not cache.is_dir() or not labels_dir.is_dir():
        ap.error("Missing original project or Phase13/14 private cache")
    for directory in (private,out):
        if directory==root or root in directory.parents:
            ap.error("Outputs may not overwrite original project")
    if private==repo or repo in private.parents or private==out or out in private.parents or private in out.parents:
        ap.error("Private spreadsheets must be outside public GitHub")
    if private.exists() and any(private.iterdir()):
        ap.error("Private output folder already contains files; choose new --private-out to avoid overwriting human evaluations")
    private.mkdir(parents=True,exist_ok=True,mode=0o700)
    os.chmod(private,0o700)
    out.mkdir(parents=True,exist_ok=True)

    public13=json.loads(Path(args.phase13_report).read_text(encoding="utf8"))
    if public13.get("status")!="completed_vectors_private":
        raise ValueError("Phase13 is not completed")
    source=root/"data/processed/fulltext_topic_model_documents_with_kmeans.parquet"
    cols={"openalex_id","title","abstract","full_text","ft_decision","text_length"}
    if not cols.issubset(set(pq.ParquetFile(source).schema_arrow.names)):
        raise ValueError("Missing required fulltext fields")
    frame=pd.read_parquet(source,columns=sorted(cols))
    decisions=frame["ft_decision"].fillna("").astype(str).str.strip().str.lower()
    sizes=pd.to_numeric(frame["text_length"],errors="coerce").fillna(0)
    selected=frame.loc[decisions.isin(ALLOWED)&(sizes>0)].copy()
    if len(selected)!=3644:
        raise ValueError("Unexpected accepted sample size; re-audit denominator")
    id_series=selected["openalex_id"].fillna("").astype(str).str.strip().str.lower().str.rstrip("/")
    if id_series.eq("").any() or id_series.duplicated().any():
        raise ValueError("Missing or duplicated identifiers")
    manifest=json.loads((cache/"input_manifest_private.json").read_text(encoding="utf8"))
    fingerprint=input_fingerprint(selected,public13["parameters"])
    state=json.loads((labels_dir/"phase14_manifest_private.json").read_text(encoding="utf8"))
    if manifest.get("fingerprint")!=fingerprint or \
       state.get("source_private_fingerprint")!=fingerprint:
        raise ValueError("Phase 13/14 source fingerprint mismatch")
    chunk=np.load(cache/"number_of_chunks.npy",mmap_mode="r",allow_pickle=False)
    biblio=np.load(cache/"full_bibliographic_vectors.npy",mmap_mode="r",allow_pickle=False)
    body=np.load(cache/"full_body_vectors.npy",mmap_mode="r",allow_pickle=False)
    valid=(chunk>0)&np.isfinite(biblio).all(axis=1)&np.isfinite(body).all(axis=1)
    if valid.sum()!=3629 or state.get("n")!=3629:
        raise ValueError("Eligible body rows differ from Phase14 count")
    chosen=selected.iloc[np.flatnonzero(valid)].reset_index(drop=True)
    xb=normalize(np.asarray(biblio[valid],dtype=np.float32))
    xbody=normalize(np.asarray(body[valid],dtype=np.float32))
    matrices={"body_chunks":xbody,"hybrid_equal":normalize(xb+xbody)}
    rng=np.random.default_rng(args.seed)
    group_list=[]
    topic_sample=[]
    private_key=[]
    for modal,k in CANDIDATES:
        f=labels_dir/f"phase14_labels_{modal}_k{k}.npy"
        lab=np.load(f,allow_pickle=False)
        if lab.shape!=(len(chosen),) or np.unique(lab).size!=k:
            raise ValueError("Phase14 topic labels missing or inconsistent")
        for topic, samples in select_stratified(
            matrices[modal],lab,args.seed+k+(0 if modal=="body_chunks" else 1000),
            args.per_topic
        ).items():
            group_list.append((modal,k,topic,samples,int((lab==topic).sum())))
    rng.shuffle(group_list)
    for serial,(modal,k,topic,items,total) in enumerate(group_list,1):
        code=f"G-{serial:03d}"
        for ridx,(j,role) in enumerate(items):
            item_code=f"{code}-R{ridx+1:02d}"
            row=chosen.iloc[int(j)]
            excerpt1,excerpt2=body_excerpt(row["full_text"])
            topic_sample.append({
                "group_code":code,"item_code":item_code,
                "title":safe_text(row["title"],250),
                "abstract":safe_text(row["abstract"],3000),
                "body_excerpt_A":excerpt1,"body_excerpt_B":excerpt2,
                "belongs_to_one_coherent_theme_0_no_1_yes_9_uncertain":"",
                "policy_relevance_0_to_3_or_9_uncertain":"",
                "document_comments":""
            })
            private_key.append({
                "group_code":code,"item_code":item_code,
                "modality":modal,"k":k,"cluster_label":topic,
                "candidate_cluster_population":total,
                "phase14_row_index":int(j),
                "openalex_id":row["openalex_id"],
                "sampling_role":role
            })
    topic_template=[]
    for serial,(_,_,_,_,total) in enumerate(group_list,1):
        topic_template.append({
            "group_code":f"G-{serial:03d}",
            "topic_name_proposed":"",
            "topic_coherence_1_to_5":"",
            "distinctiveness_1_to_5":"",
            "direct_policy_relevance_0_to_3_or_9":"",
            "confidence_1_to_5":"",
            "reviewer_comments":""
        })
    doc_cols=list(topic_sample[0])
    topic_cols=list(topic_template[0])
    for person in ("a","b"):
        # Same items and group codes, independent order of display.
        rows=topic_sample.copy()
        groups=topic_template.copy()
        order=np.random.default_rng(args.seed+(37 if person=="a" else 91))
        order.shuffle(rows)
        order.shuffle(groups)
        write_csv(private/f"rater_{person}_documents.csv",rows,doc_cols)
        write_csv(private/f"rater_{person}_topics.csv",groups,topic_cols)
    write_csv(private/"private_sampling_key.csv",private_key,list(private_key[0]))
    manifest_private={
        "created_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
        "input_fingerprint":fingerprint,
        "seed":args.seed,"per_topic":args.per_topic,
        "comparisons":[{"modality":n,"k":k} for n,k in CANDIDATES],
        "n_groups":len(group_list),"n_document_assessments_per_rater":len(topic_sample),
        "instructions":"Keep this manifest and all CSV files private. No public GitHub upload."
    }
    mf=private/"private_validation_manifest.json"
    mf.write_text(json.dumps(manifest_private,indent=2),encoding="utf8")
    os.chmod(mf,0o600)
    aggregate={
        "status":"sample_prepared_no_human_ratings",
        "created_utc":manifest_private["created_utc"],
        "source_explicit_acceptances":len(selected),
        "source_body_usable":len(chosen),
        "blinded_candidate_topic_count":len(group_list),
        "document_evaluations_per_rater":len(topic_sample),
        "rater_count_expected":2,
        "topics_per_candidate":{
            "body_chunks_k12":12,"body_chunks_k18":18,"hybrid_equal_k18":18
        },
        "sampling":{"items_per_topic":args.per_topic,
                    "per_topic_roles":{"centroid_prototypes":3,
                                       "random":args.per_topic-4,
                                       "peripheral":1},
                    "seed":args.seed,
                    "same_documents_across_raters":True,
                    "cluster_codes_blinded_to_modality_and_k":True},
        "privacy":"Raw examples, titles, abstracts, body excerpts, identifiers and cluster correspondence remain exclusively on private CEDIA.",
        "limitations":[
            "The blind hides the model/k source but not the fact that seven examples are presented as one proposed topic.",
            "More central examples are oversampled intentionally; random and peripheral cases mitigate representativeness bias.",
            "An expert agreement study must be performed before any manual validation claim.",
            "Rater topic naming and document-level topic membership should be coded independently.",
            "Document policy relevance is a separate judgment from within-topic coherence.",
            "No rater assessment has been performed by this script."
        ]
    }
    (out/"blinded_topic_sample_aggregate.json").write_text(
        json.dumps(aggregate,indent=2,ensure_ascii=False),encoding="utf8")
    lines=[
        "# Phase 15 — Blinded expert review of candidate KMeans topics",
        "","Status: sample prepared; humans have NOT performed coding.",
        "UTC: "+aggregate["created_utc"],"",
        f"Paired source: {len(chosen)} body-usable publications.",
        f"Candidates: body/k12; body/k18; hybrid/k18 ({len(group_list)} anonymized groups).",
        f"Each rater: {len(group_list)} topic forms and {len(topic_sample)} document forms.",
        f"Per group: 3 centroid prototypes + {args.per_topic-4} random + 1 peripheral.",
        "",
        "## Privacy and interpretation",
        "All documents, titles, abstracts, body excerpts, labels and group mapping reside",
        "outside GitHub in private CEDIA CSV files.",
        "The public file contains sample counts only.",
        "No independent human topic validation exists until two raters complete the sheets.",
        "Use docs/topic_validation_codebook.md for definitions and adjudication guidance."
    ]
    (out/"summary.md").write_text("\n".join(lines)+"\n",encoding="utf8")
    print("PHASE 15 SAMPLE PREPARED — NOT VALIDATED")
    print("Topic groups:",len(group_list),"document assessments per rater:",len(topic_sample))
    print("Private file directory:",private)
    print("DO NOT upload private CSV files to public GitHub")
    print("Public aggregate reports:",out)


if __name__=="__main__":
    main()
