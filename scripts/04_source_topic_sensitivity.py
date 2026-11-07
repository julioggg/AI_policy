#!/usr/bin/env python3
"""Phase 4: source-type and eligibility sensitivity of policy and topic distributions.

Uses existing Parquet data and original KMeans assignments.
No PDF/embedding recomputation. No document-level data leave CEDIA.
Only aggregate JSON/Markdown, with rare category suppression, are written.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

COLS = [
    "openalex_id", "ai_decision", "ft_decision", "text_length",
    "publication_year", "disciplinary_area", "policy_dimension",
    "type", "source_type", "is_oa", "oa_status",
    "kmeans_12", "kmeans_18", "kmeans_25"
]
TOPIC_COLS = ["kmeans_12", "kmeans_18", "kmeans_25"]


def frame_from(path):
    if not path.is_file():
        raise FileNotFoundError(str(path))
    cols = set(pq.ParquetFile(path).schema_arrow.names)
    return pd.read_parquet(path, columns=[col for col in COLS if col in cols])


def safe_category(value):
    try:
        if pd.isna(value):
            return "[missing]"
    except (TypeError, ValueError):
        return "[other]"
    label = str(value).strip().lower()
    if not label or label in {"none", "nan", "null"}:
        return "[missing]"
    if len(label) > 90 or any(c in label for c in "{}[]<>"):
        return "[other]"
    return label


def label_counts(frame, column):
    if column not in frame:
        return {}
    values = frame[column]
    if column in TOPIC_COLS:
        nums = pd.to_numeric(values, errors="coerce")
        return dict(collections.Counter(
            "topic_" + str(int(v)) if pd.notna(v) else "[missing]"
            for v in nums
        ))
    return dict(collections.Counter(safe_category(v) for v in values))


def merged_distribution(base, selected, column, threshold=5):
    a = label_counts(base, column)
    b = label_counts(selected, column)
    na, nb = sum(a.values()), sum(b.values())
    if na == 0 or nb == 0:
        return {"error": "empty population"}
    keep = {key for key in set(a)|set(b) if a.get(key,0)>=threshold and b.get(key,0)>=threshold}
    aa = {key:a.get(key,0) for key in keep}
    bb = {key:b.get(key,0) for key in keep}
    rare = "[other/rare]"
    if na-sum(aa.values()) or nb-sum(bb.values()):
        aa[rare] = na-sum(aa.values())
        bb[rare] = nb-sum(bb.values())
    labels = sorted(set(aa)|set(bb))
    pa = np.asarray([aa.get(k,0)/na for k in labels])
    pb = np.asarray([bb.get(k,0)/nb for k in labels])
    tv = 0.5*float(np.abs(pa-pb).sum())
    mid = (pa+pb)/2
    def kl(x,y):
        mask=x>0
        return float(np.sum(x[mask]*np.log2(x[mask]/y[mask])))
    js = (kl(pa,mid)+kl(pb,mid))/2
    rows = [{"label":key, "parent_n":aa.get(key,0), "subset_n":bb.get(key,0),
             "parent_pct":round(100*pa[idx],2),
             "subset_pct":round(100*pb[idx],2),
             "difference_pp":round(100*(pb[idx]-pa[idx]),2)}
            for idx,key in enumerate(labels)]
    rows.sort(key=lambda row:(-abs(row["difference_pp"]),row["label"]))
    return {"parent_n":na,"subset_n":nb, "total_variation":round(tv,5),
            "jensen_shannon_divergence_bits":round(js,5),
            "largest_absolute_difference_pp":round(
                max(abs(row["difference_pp"]) for row in rows),2),
            "distribution":rows}


def summary_population(frame):
    r={"n":int(len(frame))}
    for col in ["ai_decision","ft_decision","source_type","type","policy_dimension",
                "disciplinary_area","kmeans_18"]:
        if col in frame:
            counts=label_counts(frame,col)
            # Avoid exporting tiny categories to the public repository.
            r[col]={
                key:n for key,n in counts.items() if n>=5
            }
            small=sum(n for n in counts.values() if n<5)
            if small:
                r[col]["[rare groups combined]"]=small
    return r


def main():
    ap=argparse.ArgumentParser(description="Aggregate source and topic sensitivity")
    ap.add_argument("--project",default=str(Path.home()/"ai_policy_he"))
    ap.add_argument("--out",default="reports/phase04")
    args=ap.parse_args()
    root=Path(args.project).expanduser().resolve()
    out=Path(args.out).expanduser().resolve()
    if not root.is_dir() or out==root or root in out.parents:
        ap.error("Existing project required and output must be outside it")
    out.mkdir(parents=True,exist_ok=True)

    screen=frame_from(root/"data/processed/ai_assisted_screening_decisions.parquet")
    ft=frame_from(root/"data/processed/fulltext_topic_model_documents_with_kmeans.parquet")

    if "ai_decision" not in screen:
        raise ValueError("Screening decisions unavailable")
    includes=screen["ai_decision"].fillna("").astype(str).str.strip().str.lower()
    base=screen.loc[includes.isin({"include_core","include_policy","include_context"})]
    if len(base)!=10265:
        print("WARNING: included corpus size differs from manuscript:",len(base))
    if not {"source_type","type"}.issubset(base.columns):
        raise ValueError("source_type/type missing")
    if not {"source_type","type","text_length","ft_decision"}.issubset(ft.columns):
        raise ValueError("Fulltext metadata incomplete")

    def journal_proxy(df):
        journal=df["source_type"].fillna("").astype(str).str.strip().str.lower().eq("journal")
        article=df["type"].fillna("").astype(str).str.strip().str.lower().isin(
            {"article","review"})
        return df.loc[journal & article]

    base_journal=journal_proxy(base)
    ft_journal=journal_proxy(ft)
    excluded=ft["ft_decision"].fillna("").astype(str).str.strip().str.lower().str.startswith("exclude")
    lengths=pd.to_numeric(ft["text_length"],errors="coerce")
    textless=lengths.isna() | (lengths<=0)
    valid=~(excluded | textless)
    ft_clean=ft.loc[valid]
    ft_clean_journal=journal_proxy(ft_clean)

    populations={
        "included_all":base, "included_journal_article_review":base_journal,
        "fulltext_all":ft, "fulltext_journal_article_review":ft_journal,
        "fulltext_eligible":ft_clean,
        "fulltext_eligible_journal_article_review":ft_clean_journal
    }
    summary={key:summary_population(value) for key,value in populations.items()}

    comparisons={}
    contrasts=[
        ("included_all","included_journal_article_review"),
        ("fulltext_all","fulltext_journal_article_review"),
        ("fulltext_all","fulltext_eligible"),
        ("fulltext_eligible","fulltext_eligible_journal_article_review"),
        ("included_all","fulltext_all")
    ]
    for parent, child in contrasts:
        a,b=populations[parent],populations[child]
        cols=["disciplinary_area","policy_dimension","publication_year",
              "source_type","type"]
        if parent.startswith("fulltext") and child.startswith("fulltext"):
            cols+=TOPIC_COLS
        comparisons[parent+" -> "+child]={
            col:merged_distribution(a,b,col) for col in cols if col in a and col in b
        }

    # Only original model labels and source metadata are used.
    extra={}
    if "kmeans_18" in ft:
        label=pd.to_numeric(ft["kmeans_18"],errors="coerce")
        extra["kmeans_18_missing_labels"]=int(label.isna().sum())
        extra["kmeans_18_unique_labels"]=int(label.nunique())
        extra["kmeans_18_suspect_rows_by_label"]={
            "topic_"+str(int(k)):int(v)
            for k,v in label.loc[~valid].value_counts().items()
        }
    # Classification is exclusive if one category is stored in one cell;
    # policy_use_category may be a separate multi-label variable.
    extra["screening_categories"]={k:int(v) for k,v in
        base["ai_decision"].value_counts().items()}
    extra["excluded_fulltext_count"]=int(excluded.sum())
    extra["nonpositive_text_length"]=int(textless.sum())
    extra["excluded_and_textless_overlap"]=int((excluded & textless).sum())
    extra["valid_fulltext_count"]=int(valid.sum())

    report={
        "generated_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
        "scope":"observational sensitivity, not evidence quality assessment",
        "populations":summary,"comparisons":comparisons,"quality_checks":extra,
        "important_limitations":[
            "OpenAlex source_type=journal and type=article/review is a journal-indexed proxy, NOT verified peer-review.",
            "A genuine peer-reviewed-only analysis needs journal and publication version verification.",
            "Changes in topic proportions across subsets do not demonstrate superiority of any KMeans solution.",
            "Removing fulltext exclusions and textless records does not constitute human screening.",
            "No document-level or copyrighted textual data have been exported."
        ]
    }
    (out/"source_topic_sensitivity.json").write_text(json.dumps(
        report,indent=2,ensure_ascii=False),encoding="utf-8")
    md=["# Phase 4 — Source and topic sensitivity",
        "","Generated: "+report["generated_utc"],"",
        "## Populations (journal selection is a proxy, NOT peer-review verification)"]
    for label,value in summary.items():
        md.append("- "+label+": "+str(value["n"]))
    md+=["","## Topic and policy distribution shifts"]
    for key,values in comparisons.items():
        md.append("### "+key)
        for col,data in values.items():
            md.append("- "+col+": TV="+str(data.get("total_variation"))+
                      ", JS(bits)="+str(data.get("jensen_shannon_divergence_bits"))+
                      ", max change(pp)="+str(data.get("largest_absolute_difference_pp")))
    md+=["","## Quality checks","- "+str(extra),"",
         "## Interpretation constraints"]
    md += ["- "+x for x in report["important_limitations"]]
    (out/"summary.md").write_text("\n".join(md)+"\n",encoding="utf-8")
    print("PHASE 4 COMPLETE")
    print("Selected journal-indexed parent:",len(base_journal),
          "journal-indexed fulltext:",len(ft_journal))
    print("Eligible fulltext:",len(ft_clean))
    print("Reports:",out/"summary.md",out/"source_topic_sensitivity.json")


if __name__=="__main__":
    main()
