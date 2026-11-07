#!/usr/bin/env python3
"""Phase 13 — resumable full-corpus, BODY-only MiniLM chunk encoding.

Runs inside the original CEDIA .venv, offline. Original source project is
read-only. All per-record data and embeddings stay in a PRIVATE directory
outside the public GitHub checkout; only aggregate counts and diagnostics
are exported. No claims of human-reviewed eligibility or topic validity.

The body's input is the available full_text field (often capped at 30003
characters) and may not span entire PDF. First 512 tokens and final 15 %
are skipped as a transparent heuristic, not formal section extraction.
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
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ.setdefault("OMP_NUM_THREADS", "8")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "8")
os.environ.setdefault("MKL_NUM_THREADS", "8")

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from numpy.lib.format import open_memmap

MODEL = "sentence-transformers/all-MiniLM-L6-v2"
ALLOWED = {"include_meta_candidate", "include_core_fulltext",
           "include_policy_fulltext"}


def hash_inputs(selected, args):
    h = hashlib.sha256()
    h.update(MODEL.encode())
    for key in ("max_chunks", "skip_first_tokens", "chunk_tokens",
                "overlap", "body_end_fraction"):
        h.update((key + ":" + str(getattr(args, key)) + "\n").encode())
    for row in selected.itertuples(index=False):
        for val in (row.openalex_id, row.title, row.abstract, row.full_text):
            s = "" if pd.isna(val) else str(val)
            h.update(len(s.encode("utf-8")).to_bytes(8, "little"))
            h.update(s.encode("utf-8"))
    return h.hexdigest()


def init_memmap(path, n, dtype, initial):
    if path.exists():
        arr = np.load(path, mmap_mode="r+")
        if arr.shape != ((n, 384) if dtype == "float32" else (n,)):
            raise ValueError("Private cache array shape mismatch: " + path.name)
        if str(arr.dtype) != dtype:
            raise ValueError("Private cache array dtype mismatch: " + path.name)
        return arr
    arr = open_memmap(path, mode="w+", dtype=dtype,
                      shape=((n, 384) if dtype == "float32" else (n,)))
    arr[:] = initial
    arr.flush()
    os.chmod(path, 0o600)
    return arr


def chunks_from_fulltext(fulltext, tokenizer, args):
    token_ids = tokenizer.encode(str(fulltext), add_special_tokens=False,
                                 truncation=False)
    end = int(len(token_ids) * args.body_end_fraction)
    body = token_ids[args.skip_first_tokens:end]
    if len(body) < args.chunk_tokens:
        return [], len(token_ids), len(body)
    window = args.chunk_tokens
    stride = window - args.overlap
    starts = list(range(0, len(body) - window + 1, stride))
    last = len(body) - window
    if not starts or starts[-1] != last:
        starts.append(last)
    if len(starts) > args.max_chunks:
        positions = np.linspace(0, len(starts)-1, args.max_chunks)
        starts = [starts[j] for j in sorted(set(np.rint(positions).astype(int).tolist()))]
    text_chunks = []
    for st in starts:
        ids = body[st:st + window]
        phrase = tokenizer.decode(ids, skip_special_tokens=True,
                                  clean_up_tokenization_spaces=False)
        if not phrase.strip():
            continue
        if len(tokenizer.encode(phrase, add_special_tokens=True,
                                truncation=False)) > 256:
            # Re-encoding can merge/split word pieces at decoded boundaries.
            phrase = tokenizer.decode(ids[:-12], skip_special_tokens=True,
                                      clean_up_tokenization_spaces=False)
        if len(tokenizer.encode(phrase, add_special_tokens=True,
                                truncation=False)) > 256:
            raise ValueError("Chunk exceeds model's maximum input length")
        text_chunks.append(phrase)
    return text_chunks, len(token_ids), len(body)


def summarize(a):
    x = np.asarray(a, dtype=float)
    if not len(x):
        return {}
    return {"min": float(np.min(x)), "p10": float(np.quantile(x, .1)),
            "median": float(np.median(x)), "p90": float(np.quantile(x, .9)),
            "max": float(np.max(x)), "mean": float(np.mean(x))}


def public_write(out, report):
    out.mkdir(parents=True, exist_ok=True)
    (out/"full_corpus_chunk_encoding.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = ["# Phase 13 — Full-corpus BODY chunk embeddings", "",
             "Status: " + report["status"],
             "UTC: " + report["created_utc"],
             "", "## Aggregate status",
             json.dumps(report["counts"], indent=2),
             "", "## Method",
             json.dumps(report["parameters"], indent=2),
             "", "## Diagnostics",
             json.dumps(report.get("diagnostics", {}), indent=2),
             "", "## Limitations"]
    lines += ["- "+v for v in report["limitations"]]
    (out/"summary.md").write_text("\n".join(lines)+"\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default=str(Path.home()/"ai_policy_he"))
    parser.add_argument("--out", default="reports/phase13")
    parser.add_argument("--private-cache", default=str(Path.home()/"ai_policy_chunks_full_private"))
    parser.add_argument("--max-chunks", type=int, default=12)
    parser.add_argument("--skip-first-tokens", type=int, default=512)
    parser.add_argument("--chunk-tokens", type=int, default=192)
    parser.add_argument("--overlap", type=int, default=32)
    parser.add_argument("--body-end-fraction", type=float, default=.85)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--threads", type=int, default=8)
    parser.add_argument("--max-new-docs", type=int, default=0,
                        help="0 means process all remaining; positive enables checkpointed batches")
    args=parser.parse_args()

    if not 0 <= args.max_new_docs or args.max_chunks<1 or args.skip_first_tokens<256 or \
       args.chunk_tokens<32 or args.chunk_tokens>220 or args.overlap<0 or \
       args.overlap>=args.chunk_tokens or not .5<=args.body_end_fraction<=1 or \
       args.threads<1 or args.batch_size<1:
        parser.error("Invalid chunking or execution parameters")
    root=Path(args.project).expanduser().resolve()
    out=Path(args.out).expanduser().resolve()
    private=Path(args.private_cache).expanduser().resolve()
    repo=Path.home()/"AI_policy"
    if not root.is_dir() or out == root or root in out.parents or \
       private == root or root in private.parents or \
       private == repo or repo in private.parents or \
       private == out or out in private.parents or private in out.parents:
        parser.error("Original project, private cache, and public reports must not overlap")
    private.mkdir(parents=True,exist_ok=True,mode=0o700)
    os.chmod(private,0o700)
    out.mkdir(parents=True,exist_ok=True)

    import torch
    from sentence_transformers import SentenceTransformer
    torch.set_num_threads(args.threads)

    source_file=root/"data/processed/fulltext_topic_model_documents_with_kmeans.parquet"
    cols=set(pq.ParquetFile(source_file).schema_arrow.names)
    needed={"openalex_id","title","abstract","full_text",
            "text_length","ft_decision"}
    if not needed.issubset(cols):
        raise ValueError("Missing required original fulltext fields: "+
                         str(sorted(needed-cols)))
    df=pd.read_parquet(source_file,columns=sorted(needed))
    ids=df["openalex_id"].fillna("").astype(str).str.strip().str.lower().str.rstrip("/")
    if ids.eq("").any() or ids.duplicated().any():
        raise ValueError("Missing or duplicated OpenAlex IDs")
    decision=df["ft_decision"].fillna("").astype(str).str.strip().str.lower()
    length=pd.to_numeric(df["text_length"], errors="coerce").fillna(0)
    mask=decision.isin(ALLOWED)&(length>0)
    selected=df.loc[mask].copy()
    selected_index=selected.index.to_numpy(dtype=int)
    n=len(selected)
    if n<3000:
        raise ValueError("Unexpectedly small eligible corpus; verify source data first")
    result_base = {
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "parameters": {
            "model":MODEL,
            "model_max_seq_length":256,
            "chunk_content_tokens":args.chunk_tokens,
            "max_chunks_per_document":args.max_chunks,
            "chunk_overlap":args.overlap,
            "first_tokens_excluded":args.skip_first_tokens,
            "tail_fraction_excluded":round(1-args.body_end_fraction,5),
            "source_field":"full_text, which is capped in the original extraction workflow",
            "pooling":"unit-normalize chunks, arithmetic mean, unit-normalize document",
            "baseline":"fresh unit-normalized encoding of title followed by abstract",
            "hybrid":"computed later by unit-normalized sum of baseline and body vectors",
            "tokenizer_and_model":"local offline MiniLM in original project virtualenv",
            "device":"cpu"
        },
        "limitations":[
            "Explicit original AI decisions are not a substitute for independent human eligibility coding.",
            "The available full_text field is truncated by the preexisting extraction pipeline for many PDFs; this is not every page of every original publication.",
            "Skipping the first 512 tokens and last 15 percent is a reproducible heuristic, not section-aware rhetorical segmentation.",
            "No model, source text, document label or original fulltext vector is overwritten.",
            "The public report contains aggregate metadata only; per-document vectors, source hashes and progress arrays remain private.",
            "No topic validity, policy impact or scientific superiority can be claimed until full-corpus and expert analyses."
        ]
    }
    fingerprint=hash_inputs(selected,args)
    state_file=private/"input_manifest_private.json"
    if state_file.exists():
        state=json.loads(state_file.read_text(encoding="utf-8"))
        if state.get("fingerprint")!=fingerprint or state.get("rows")!=n:
            raise ValueError("Cache fingerprint differs; do not mix runs. Use a NEW private-cache directory")
    else:
        state={"fingerprint":fingerprint,"rows":n,"model":MODEL}
        state_file.write_text(json.dumps(state,indent=2),encoding="utf-8")
        os.chmod(state_file,0o600)

    baseline=init_memmap(private/"full_bibliographic_vectors.npy",n,"float32",np.nan)
    body=init_memmap(private/"full_body_vectors.npy",n,"float32",np.nan)
    nchunks=init_memmap(private/"number_of_chunks.npy",n,"int16",-1)
    token_counts=init_memmap(private/"total_token_counts.npy",n,"int32",-1)
    available_counts=init_memmap(private/"body_available_token_counts.npy",n,"int32",-1)
    model=SentenceTransformer(MODEL,device="cpu")
    if int(model.max_seq_length)!=256:
        raise ValueError("Expected MiniLM 256 token budget. Audit changed model settings")
    tokenizer=model.tokenizer

    fresh=0
    for j,record in enumerate(selected.itertuples(index=False)):
        if int(nchunks[j])>=0 and (int(nchunks[j])==0 or (
                np.isfinite(baseline[j]).all() and np.isfinite(body[j]).all())):
            continue
        chunks,total,available=chunks_from_fulltext(record.full_text,tokenizer,args)
        token_counts[j]=total
        available_counts[j]=available
        if not chunks:
            nchunks[j]=0
        else:
            if not np.isfinite(baseline[j]).all():
                biblio=(str(record.title or "")+". "+str(record.abstract or "")).strip()
                encoded=model.encode([biblio],batch_size=1,show_progress_bar=False,
                                     normalize_embeddings=True,convert_to_numpy=True)
                baseline[j]=np.asarray(encoded[0],dtype="float32")
            embedded=model.encode(chunks,batch_size=args.batch_size,
                                  show_progress_bar=False,
                                  normalize_embeddings=True,convert_to_numpy=True)
            averaged=np.mean(embedded,axis=0)
            magnitude=float(np.linalg.norm(averaged))
            if not np.isfinite(magnitude) or magnitude<1e-10:
                raise ValueError("Document's pooled vector is invalid")
            body[j]=np.asarray(averaged/magnitude,dtype="float32")
            # Set count only AFTER vectors have been written.
            nchunks[j]=len(chunks)
        fresh+=1
        if fresh % 25 == 0:
            baseline.flush();body.flush();nchunks.flush()
            token_counts.flush();available_counts.flush()
            print("Checkpoint: newly processed",fresh,"done total",int((nchunks>=0).sum()),
                  "of",n,flush=True)
        if args.max_new_docs and fresh>=args.max_new_docs:
            break
    baseline.flush();body.flush();nchunks.flush()
    token_counts.flush();available_counts.flush()

    finished=nchunks>=0
    usable=(nchunks>0)&np.isfinite(baseline).all(axis=1)&np.isfinite(body).all(axis=1)
    counts={
        "original_fulltext_rows":int(len(df)),
        "explicit_accepted_input_rows":int(n),
        "new_documents_this_call":int(fresh),
        "processed_in_private_cache":int(finished.sum()),
        "remaining_unprocessed":int((~finished).sum()),
        "eligible_with_body_vectors":int(usable.sum()),
        "no_usable_body_after_exclusion_rules":int((nchunks==0).sum()),
    }
    details={}
    if usable.any():
        from sklearn.preprocessing import normalize
        xb=normalize(np.asarray(baseline[usable],dtype=np.float32))
        xbody=normalize(np.asarray(body[usable],dtype=np.float32))
        cosine=np.einsum("ij,ij->i",xb,xbody)
        details["bibliographic_body_cosine"]=summarize(cosine)
        details["document_body_chunk_counts"]=summarize(nchunks[usable])
        details["input_fulltext_token_counts"]=summarize(token_counts[usable])
        details["usable_body_token_counts"]=summarize(available_counts[usable])
    report=dict(result_base)
    report["status"]="completed_vectors_private" if finished.all() else "partial_resumable"
    report["counts"]=counts
    report["diagnostics"]=details
    public_write(out,report)
    print("PHASE 13",report["status"],":",counts["eligible_with_body_vectors"],"usable")
    print("Remaining:",counts["remaining_unprocessed"])
    print("Reports:",out/"summary.md",out/"full_corpus_chunk_encoding.json")
    print("Per-document vectors saved PRIVATE; do not git add the private directory")


if __name__=="__main__":
    main()
