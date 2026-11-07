#!/usr/bin/env python3
"""Phase 5: reproducible expert-validation sample, private rater worksheets.

Private sheets contain titles/abstracts and IDs. They are NEVER written to
the public repo and must not be git-added. Only sampling counts are public.
Requires pandas, pyarrow. Does not modify original CEDIA source files.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import random
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

FIELDS = ["openalex_id", "title", "abstract", "publication_year",
          "type", "ai_decision", "policy_dimension", "disciplinary_area"]
STRATA = [
    ("screen_include_core", 120),
    ("screen_include_policy", 80),
    ("screen_include_context", 40),
    ("screen_exclude", 18),
    ("q1_not_article_ready", 80),
    ("core_not_q1", 30)
]
RATER_FIELDS = [
    "sample_id", "title", "abstract", "publication_year", "type",
    "relevance_code", "discipline_code", "primary_policy_code", "reason"
]


def csv_safe(x):
    if x is None or pd.isna(x):
        return ""
    text = str(x).replace("\x00", "").strip()
    # Avoid interpreting publication text as a formula in spreadsheet software.
    if text[:1] in ("=", "+", "-", "@"):
        text = "'" + text
    return text


def read(path):
    cols = set(pq.ParquetFile(path).schema_arrow.names)
    must = {"openalex_id", "title", "abstract"}
    if not must.issubset(cols):
        raise ValueError("Missing metadata fields in "+str(path))
    requested = [col for col in FIELDS if col in cols]
    df = pd.read_parquet(path, columns=requested)
    df["openalex_id"] = df["openalex_id"].astype(str).str.strip()
    df = df.loc[(df["openalex_id"]!="") &
                (df["openalex_id"].str.lower()!="nan")]
    return df.drop_duplicates("openalex_id", keep="first")


def sample_frame(df, n, rng):
    take = min(n, len(df))
    if not take:
        return df.iloc[:0].copy()
    indexes = rng.sample(range(len(df)), take)
    return df.iloc[indexes].copy()


def write_csv(path, rows, fields):
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for item in rows:
            writer.writerow({key:item.get(key, "") for key in fields})
    os.chmod(path,0o600)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--project", default=str(Path.home()/"ai_policy_he"))
    parser.add_argument("--private-out",default=str(Path.home()/"ai_policy_validation_private"))
    parser.add_argument("--public-out",default="reports/phase05")
    parser.add_argument("--seed",type=int,default=20261107)
    args=parser.parse_args()
    root=Path(args.project).expanduser().resolve()
    private=Path(args.private_out).expanduser().resolve()
    public=Path(args.public_out).expanduser().resolve()
    repo=Path.home()/"AI_policy"
    if not root.is_dir():
        parser.error("Project root missing")
    if root == private or root in private.parents:
        parser.error("Private outputs must be outside original project")
    if repo == private or repo in private.parents:
        parser.error("Private outputs must be outside PUBLIC GitHub workspace")
    if private==public or private in public.parents or public in private.parents:
        parser.error("Private and public output locations must be separate")
    private.mkdir(parents=True,exist_ok=True,mode=0o700)
    os.chmod(private,0o700)
    public.mkdir(parents=True,exist_ok=True)

    screening=read(root/"data/processed/ai_assisted_screening_decisions.parquet")
    article=read(root/"data/processed/openalex_ai_policy_he_article_ready_strict.parquet")
    q1=read(root/"data/processed/openalex_ai_policy_he_q1_refined.parquet")
    core=read(root/"data/processed/openalex_ai_policy_he_core.parquet")
    decisions=screening["ai_decision"].fillna("").astype(str).str.strip().str.lower()
    pools={
        "screen_include_core":screening.loc[decisions=="include_core"],
        "screen_include_policy":screening.loc[decisions=="include_policy"],
        "screen_include_context":screening.loc[decisions=="include_context"],
        "screen_exclude":screening.loc[decisions=="exclude"],
        "q1_not_article_ready":q1.loc[~q1["openalex_id"].isin(set(article["openalex_id"]))],
        "core_not_q1":core.loc[~core["openalex_id"].isin(set(q1["openalex_id"]))]
    }
    rng=random.Random(args.seed)
    sampled=[]
    counts={}
    for group,target in STRATA:
        pool=pools[group]
        chosen=sample_frame(pool,target,rng)
        counts[group]={"population_n":int(len(pool)), "sample_n":int(len(chosen))}
        for record in chosen.to_dict("records"):
            sampled.append({"stratum":group, **record})
    rng.shuffle(sampled)
    keys=[]
    for i,row in enumerate(sampled,1):
        row["sample_id"]="P%04d"%i
        original=row.get("openalex_id")
        keys.append({
            "sample_id":row["sample_id"],
            "stratum":row["stratum"],
            "openalex_id":original,
            "ai_decision":str(row.get("ai_decision") or ""),
            "original_policy_dimension":str(row.get("policy_dimension") or ""),
            "original_disciplinary_area":str(row.get("disciplinary_area") or "")
        })
    sheets=[]
    for rater in ["a","b"]:
        shuffled=list(sampled)
        rng.shuffle(shuffled)
        records=[]
        for row in shuffled:
            records.append({
                "sample_id":row["sample_id"],
                "title":csv_safe(row.get("title")),
                "abstract":csv_safe(row.get("abstract")),
                "publication_year":csv_safe(row.get("publication_year")),
                "type":csv_safe(row.get("type")),
                "relevance_code":"",
                "discipline_code":"",
                "primary_policy_code":"",
                "reason":""
            })
        filename=private/("rater_"+rater+".csv")
        write_csv(filename,records,RATER_FIELDS)
        sheets.append(filename)
    keyfile=private/"sampling_key.csv"
    write_csv(keyfile,keys,[
        "sample_id","stratum","openalex_id","ai_decision",
        "original_policy_dimension","original_disciplinary_area"
    ])
    # The hash is a reproducibility checksum, not a publication identifier.
    fingerprint=hashlib.sha256(
        ("\n".join(sorted(k["openalex_id"] for k in keys))).encode("utf8")
    ).hexdigest()
    safe={
        "generated_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
        "random_seed":args.seed,
        "sample_size":len(sampled),
        "strata":counts,
        "id_set_sha256":fingerprint,
        "privacy":"Raw sample/abstracts/IDs remain in private CEDIA directory; not in public GitHub."
    }
    (public/"sample_aggregate.json").write_text(json.dumps(
        safe,indent=2,ensure_ascii=False),encoding="utf-8")
    md=["# Phase 5 — Blinded manual validation sampling",
        "","Status: SAMPLE CREATED; HUMAN CLASSIFICATION NOT PERFORMED.",
        "","Sample size: "+str(len(sampled)),
        "Seed: "+str(args.seed),
        "Fingerprint SHA256: "+fingerprint,
        "","## Strata"]
    for name,info in counts.items():
        md.append("- "+name+": "+str(info["sample_n"])+" / "+str(info["population_n"]))
    md+=["","## Scientific boundary",
          "The early-filter exclusion strata are not AI-screening negatives.",
          "Unweighted pooled accuracy is biased by stratification; use design weights.",
          "Independent two-rater coding and adjudication are outstanding.",
          "Refer to docs/human_validation_protocol.md.",
          ""]
    (public/"summary.md").write_text("\n".join(md),encoding="utf-8")
    print("PHASE 5 SAMPLE PREPARED; human coding NOT completed")
    print("Private directory:",private)
    print("Private sheets:",*(str(f.name) for f in sheets),keyfile.name)
    print("Aggregate public reports:",public/"summary.md",public/"sample_aggregate.json")
    print("NEVER upload private directory to public GitHub")


if __name__=="__main__":
    main()
