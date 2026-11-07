#!/usr/bin/env python3
"""Phase 2: safe, read-only audit of corpus provenance, full-text selection and bias.
Exports only aggregate tables, no document identifiers, titles, texts or author data.
"""
import argparse
import collections
import csv
import datetime as dt
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

STAGES = {
    "raw": "data/processed/openalex_ai_policy_he_checkpoint.parquet",
    "deduplicated": "data/processed/openalex_ai_policy_he_works.parquet",
    "core": "data/processed/openalex_ai_policy_he_core.parquet",
    "q1_refined": "data/processed/openalex_ai_policy_he_q1_refined.parquet",
    "article_ready": "data/processed/openalex_ai_policy_he_article_ready_strict.parquet",
    "screening": "data/processed/ai_assisted_screening_decisions.parquet",
    "fulltext": "data/processed/fulltext_topic_model_documents.parquet",
    "fulltext_kmeans": "data/processed/fulltext_topic_model_documents_with_kmeans.parquet",
    "extracted": "data/processed/fulltext/fulltext_extracted_texts.parquet",
}
SELECT_COLS = ["openalex_id", "doi", "publication_year", "disciplinary_area",
               "policy_dimension", "type", "source_type", "is_oa", "oa_status",
               "status", "text_length", "ai_decision", "ft_decision"]
COMPARE_COLS = ["publication_year", "disciplinary_area", "policy_dimension",
                "type", "source_type", "is_oa", "oa_status"]
INCLUDE = {"include", "included", "retain", "retained", "keep", "yes"}
EXCLUDE = {"exclude", "excluded", "reject", "rejected", "no"}


def read_table(file):
    available = set(pq.ParquetFile(file).schema_arrow.names)
    return pd.read_parquet(file, columns=[x for x in SELECT_COLS if x in available])


def strings(col, doi=False):
    vals = col.fillna("").astype(str).str.strip().str.lower()
    if doi:
        vals = vals.str.replace(r"^(https?://(dx\.)?doi\.org/|doi:)", "", regex=True)
    return set(v for v in vals if v and v not in {"none", "nan", "null"})


def category(value, column):
    if pd.isna(value):
        return "[missing]"
    if column == "publication_year":
        try:
            year = int(float(value))
            return str(year) if 1980 <= year <= 2030 else "[invalid]"
        except Exception:
            return "[invalid]"
    s = str(value).strip().lower()
    if not s or s in {"none", "null", "nan"}:
        return "[missing]"
    if len(s) > 80 or not re.fullmatch(r"[a-z0-9 _;&/().+\-]+", s):
        return "[other]"
    return s


def counts(series, column, suppress=5):
    raw = collections.Counter(category(x, column) for x in series)
    agg = collections.Counter()
    for key, n in raw.items():
        agg[key if n >= suppress else "[rare combined]"] += n
    return dict(sorted(agg.items(), key=lambda pair: (-pair[1], pair[0])))


def compare(parent, child, column):
    a = collections.Counter(category(x, column) for x in parent[column])
    b = collections.Counter(category(x, column) for x in child[column])
    n, m = sum(a.values()), sum(b.values())
    if not n or not m:
        return {"error": "empty group"}
    keep = {k for k in set(a)|set(b) if a[k] >= 5 and b[k] >= 5}
    a_other, b_other = n - sum(a[k] for k in keep), m - sum(b[k] for k in keep)
    groups = sorted(keep) + (["[other/rare]"] if a_other or b_other else [])
    rows = []
    for k in groups:
        x, y = (a_other,b_other) if k == "[other/rare]" else (a[k],b[k])
        rows.append({"group": k, "parent_n": x, "fulltext_n": y,
                     "parent_pct": round(100*x/n,2), "fulltext_pct": round(100*y/m,2),
                     "difference_pp": round(100*(y/m-x/n),2)})
    return {"total_variation_distance": round(sum(abs(r["difference_pp"]) for r in rows)/200,4),
            "rows": rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default=str(Path.home()/"ai_policy_he"))
    parser.add_argument("--out", default="reports/phase02")
    args = parser.parse_args()
    root, out = Path(args.project).expanduser().resolve(), Path(args.out).expanduser().resolve()
    if not root.is_dir() or out == root or root in out.parents:
        parser.error("Project must exist; output must be outside source project")
    out.mkdir(parents=True, exist_ok=True)
    details, ids, dois, frames = {}, {}, {}, {}
    for stage, relative in STAGES.items():
        file = root/relative
        if not file.is_file():
            details[stage] = {"error": "missing"}
            continue
        frame = read_table(file)
        frames[stage] = frame
        observed = {"rows": int(len(frame))}
        if "openalex_id" in frame:
            ids[stage] = strings(frame["openalex_id"])
            observed["unique_ids"] = len(ids[stage])
            observed["missing_id_rows"] = int(frame["openalex_id"].isna().sum())
            observed["duplicate_id_rows"] = int(len(frame)-len(ids[stage])-observed["missing_id_rows"])
        if "doi" in frame:
            dois[stage] = strings(frame["doi"], doi=True)
            observed["unique_dois"] = len(dois[stage])
            observed["nonnull_doi_rows"] = int(frame["doi"].notna().sum())
        if "ai_decision" in frame:
            raw = frame["ai_decision"].fillna("[missing]").astype(str).str.strip().str.lower()
            observed["raw_decisions"] = counts(raw, "decision")
            observed["recognized_include_rows"] = int(raw.isin(INCLUDE).sum())
            observed["recognized_exclude_rows"] = int(raw.isin(EXCLUDE).sum())
            observed["other_decision_rows"] = int((~raw.isin(INCLUDE|EXCLUDE)).sum())
        if "ft_decision" in frame:
            observed["ft_decision"] = counts(frame["ft_decision"], "ft_decision")
        if "status" in frame:
            observed["status"] = counts(frame["status"], "status")
        if "text_length" in frame:
            lengths = pd.to_numeric(frame["text_length"], errors="coerce")
            observed["nonpositive_text_length"] = int((lengths.fillna(0)<=0).sum())
            observed["text_length_quantiles"] = {
                str(q): int(lengths.quantile(q)) for q in [0,.01,.05,.5,.95,1]
            } if lengths.notna().any() else {}
        details[stage] = observed

    paths = [("raw","deduplicated"),("deduplicated","core"),("core","q1_refined"),
             ("q1_refined","article_ready"),("article_ready","screening"),
             ("screening","fulltext"),("article_ready","fulltext"),
             ("fulltext","fulltext_kmeans")]
    transitions = {}
    for a,b in paths:
        if a in ids and b in ids:
            transitions[a+" -> "+b] = {
                "shared": len(ids[a]&ids[b]),
                "child_not_in_parent": len(ids[b]-ids[a]),
                "parent_not_in_child": len(ids[a]-ids[b])}
    parent = frames.get("screening")
    fulltext = frames.get("fulltext")
    representative = {}
    if parent is not None and fulltext is not None and "ai_decision" in parent:
        choices = parent["ai_decision"].fillna("").astype(str).str.strip().str.lower()
        included = parent.loc[choices.isin(INCLUDE)]
        if len(included):
            representative = {c: compare(included,fulltext,c) for c in COMPARE_COLS
                              if c in included and c in fulltext}

    manifest = root/"outputs/tables/fulltext_pdf_download_manifest.csv"
    manifest_result = {}
    if manifest.is_file():
        with manifest.open(encoding="utf-8-sig",errors="replace",newline="") as handle:
            reader = csv.DictReader(handle)
            s = collections.Counter()
            found_dois = set()
            n = 0
            for row in reader:
                n += 1
                s[category(row.get("status"),"status")] += 1
                doi = str(row.get("doi") or "").strip().lower()
                doi = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:)","",doi)
                if doi and doi not in {"nan","none"}:
                    found_dois.add(doi)
            manifest_result = {"attempts": n,
                               "statuses": {k:v for k,v in s.items() if v>=5},
                               "other_status_total": sum(v for v in s.values() if v<5),
                               "unique_dois": len(found_dois),
                               "matched_fulltext_dois": len(found_dois&dois.get("fulltext",set()))}

    embeddings_file = root/"data/processed/fulltext_topic_embeddings_minilm.npy"
    embeddings = {}
    if embeddings_file.is_file():
        matrix = np.load(embeddings_file, mmap_mode="r", allow_pickle=False)
        embeddings = {"shape": list(matrix.shape), "dtype": str(matrix.dtype),
                      "first_128_vectors_finite": bool(np.isfinite(matrix[:128]).all())}
    quality = []
    metric_file = root/"outputs/tables/kmeans_topic_model_quality_metrics.csv"
    if metric_file.is_file():
        with metric_file.open(encoding="utf-8-sig",newline="") as handle:
            for row in csv.DictReader(handle):
                quality.append({k: float(v) for k,v in row.items()
                                if k in {"k","silhouette_cosine_sample","davies_bouldin",
                                         "calinski_harabasz"} and v})
    result = {"created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
              "stage_summaries":details,"transitions":transitions,
              "fulltext_manifest":manifest_result,
              "representativeness_screened_included_vs_fulltext":representative,
              "embeddings":embeddings,"kmeans_existing_quality":quality,
              "cautions":["Descriptive comparison is not causal inference.",
                          "Counts of records do not establish that their texts were extracted correctly.",
                          "Included corpus membership must be confirmed from decision labels.",
                          "DOI duplication may be different record versions.",
                          "No source data or embeddings were modified."],
              "privacy":"aggregate only, no document identifiers, titles, authors, DOI or texts"}
    target = out/"provenance_bias.json"
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    lines = ["# Phase 2 — Provenance and representativeness","",
             "Date UTC: "+result["created_utc"],"","## Corpus counts"]
    for k,v in details.items():
        lines.append("- "+k+": "+str(v.get("rows","missing"))+" rows")
        if "raw_decisions" in v:
            lines.append("  - screening: "+str(v["raw_decisions"]))
        if "nonpositive_text_length" in v:
            lines.append("  - nonpositive text length: "+str(v["nonpositive_text_length"]))
    lines += ["","## Stage containment (OpenAlex IDs)"]
    for k,v in transitions.items():
        lines.append("- "+k+": shared "+str(v["shared"])+
                     "; child outside parent "+str(v["child_not_in_parent"]))
    lines += ["","## Full text retrieval","- "+str(manifest_result),
              "","## Embeddings","- "+str(embeddings),
              "","## Previously saved KMeans metrics"]
    for metric in quality:
        lines.append("- "+str(metric))
    lines += ["","## Observable sample differences"]
    for col, v in representative.items():
        lines.append("- "+col+": TV distance = "+str(v.get("total_variation_distance")))
    if not representative:
        lines.append("- Not calculated; recognized include label was not present.")
    lines += ["","This is an aggregate audit, not independent validation of screening or topics.",""]
    (out/"summary.md").write_text("\n".join(lines),encoding="utf-8")
    print("PHASE 2 COMPLETE")
    print("Screening categories:",details.get("screening",{}).get("raw_decisions"))
    print("Full-text count:",details.get("fulltext",{}).get("rows"))
    print("Embedding shape:",embeddings.get("shape"))
    print("Reports:",target,out/"summary.md")


if __name__ == "__main__":
    main()
