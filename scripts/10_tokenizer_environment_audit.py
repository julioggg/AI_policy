#!/usr/bin/env python3
"""Phase 10: tokenizer truncation and offline model-environment audit.

Reads original project data and code without modification.
Outputs ONLY aggregate counts, package availability, safe AST signals.
Never publishes titles, text, document IDs, model-cache paths or secrets.
"""
from __future__ import annotations

import argparse
import ast
import collections
import datetime as dt
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import sys

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

SCRIPTS = [
    "03_embeddings_and_clusters.py",
    "12_fulltext_screening_and_extraction.py",
    "16_fulltext_topic_modeling_umap_hdbscan.py",
    "18_fulltext_topic_modeling_kmeans_robust.py"
]
FIELDS = {"title", "abstract", "text", "text_for_analysis",
          "full_text", "topic_text", "semantic_text", "combined_text"}
CODE_NAMES = {"encode", "tokenize", "tokenizer", "SentenceTransformer",
              "AutoTokenizer", "from_pretrained"}
LIMIT_NAMES = {"max_seq_length", "max_length", "truncation",
               "batch_size", "normalize_embeddings", "model_max_length"}


def safe_simple(node):
    try:
        value = ast.literal_eval(node)
    except (ValueError, TypeError, RecursionError):
        return "[expression]"
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return value if value in {"sentence-transformers/all-MiniLM-L6-v2",
                                  "cpu", "cuda", "longest", "max_length"} else "[string]"
    return "[collection]"


def script_signals(script):
    if not script.is_file():
        return {"filename": script.name, "error": "missing"}
    try:
        root = ast.parse(script.read_text(encoding="utf8", errors="replace"))
    except (OSError, UnicodeError, SyntaxError) as err:
        return {"filename": script.name, "error": type(err).__name__}
    records = []
    field_uses = collections.Counter()
    for node in ast.walk(root):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value in FIELDS:
            field_uses[node.value] += 1
        if isinstance(node, ast.Assign):
            for target in node.targets:
                name = target.attr if isinstance(target, ast.Attribute) else (
                    target.id if isinstance(target, ast.Name) else None)
                if name in LIMIT_NAMES:
                    records.append({"line": node.lineno, "kind": "assignment",
                                    "parameter": name, "value": safe_simple(node.value)})
        if isinstance(node, ast.Call):
            name = node.func.attr if isinstance(node.func, ast.Attribute) else (
                node.func.id if isinstance(node.func, ast.Name) else None)
            if name in CODE_NAMES or name in {"KMeans", "UMAP", "HDBSCAN"}:
                kws = {kw.arg: safe_simple(kw.value) for kw in node.keywords if kw.arg in LIMIT_NAMES
                       or kw.arg in {"n_clusters", "random_state", "n_init"}}
                first = safe_simple(node.args[0]) if name in {"SentenceTransformer",
                      "AutoTokenizer", "from_pretrained"} and node.args else None
                records.append({"line": node.lineno, "kind": "call",
                                "name": name, "first_arg": first, "safe_kwargs": kws})
        if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Slice):
            hi = node.slice.upper
            if isinstance(hi, ast.Constant) and isinstance(hi.value, int) and hi.value in {
                    128, 256, 384, 512, 1024, 2048, 4096, 8000, 12000, 16000, 20000, 30000,
                    30003, 32000, 50000}:
                records.append({"line": node.lineno, "kind": "slice_limit",
                                "upper_bound": int(hi.value)})
    return {"filename": script.name,
            "whitelisted_field_occurrences": dict(sorted(field_uses.items())),
            "runtime_or_truncation_signals": sorted(records, key=lambda r: r["line"]),
            "warning": "Static syntax clues are not evidence that a particular code path ran."}


def current_environment(home):
    dep_map = {
        "numpy": "numpy", "pandas": "pandas",
        "pyarrow": "pyarrow", "scikit-learn": "sklearn",
        "torch": "torch", "transformers": "transformers",
        "sentence-transformers": "sentence_transformers",
        "tokenizers": "tokenizers"
    }
    deps = {}
    for package, module in dep_map.items():
        try:
            present = importlib.util.find_spec(module) is not None
        except (ImportError, ValueError, AttributeError):
            present = False
        try:
            version = importlib.metadata.version(package) if present else None
        except importlib.metadata.PackageNotFoundError:
            version = None
        deps[package] = {"import_discoverable": present, "version": version}
    places = [
        (".venv", home/".venv/bin/python"),
        ("venv", home/"venv/bin/python"),
        ("ai_policy_he/.venv", home/"ai_policy_he/.venv/bin/python"),
        ("ai_policy_he/venv", home/"ai_policy_he/venv/bin/python"),
        ("ai_policy_he/env", home/"ai_policy_he/env/bin/python"),
        ("ai_policy_he/.conda", home/"ai_policy_he/.conda/bin/python"),
        (".local/share/virtualenvs", home/".local/share/virtualenvs"),
        ("miniconda3", home/"miniconda3/bin/python"),
        ("mambaforge", home/"mambaforge/bin/python"),
        ("anaconda3", home/"anaconda3/bin/python")
    ]
    cache_presence = {
        "hf_hub_model_default_cache": (
            home/".cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2"
        ).is_dir(),
        "torch_sentence_transformer_cache": (
            home/".cache/torch/sentence_transformers/sentence-transformers_all-MiniLM-L6-v2"
        ).is_dir(),
        "HF_HOME_is_configured": bool(os.environ.get("HF_HOME")),
        "SENTENCE_TRANSFORMERS_HOME_is_configured": bool(os.environ.get("SENTENCE_TRANSFORMERS_HOME")),
        "HF_HUB_OFFLINE_is_configured": bool(os.environ.get("HF_HUB_OFFLINE"))
    }
    return {"python_version": platform.python_version(),
            "python_executable_basename": Path(sys.executable).name,
            "running_inside_singularity": bool(
                os.environ.get("SINGULARITY_NAME") or os.environ.get("APPTAINER_NAME")),
            "dependency_availability": deps,
            "common_virtualenv_candidates": {
                label: bool(path.exists()) for label, path in places},
            "model_cache_presence": cache_presence}


def text_probe(project):
    base = project/"data/processed"
    corep = base/"openalex_ai_policy_he_core_50k_embedded.parquet"
    ftp = base/"fulltext_topic_model_documents_with_kmeans.parquet"
    cols = ["openalex_id", "text_for_analysis", "abstract"]
    core = pd.read_parquet(corep, columns=[c for c in cols if c in
                                  pq.ParquetFile(corep).schema_arrow.names])
    fc = ["openalex_id", "topic_text", "full_text", "ft_decision", "text_length"]
    full = pd.read_parquet(ftp, columns=[c for c in fc if c in
                                  pq.ParquetFile(ftp).schema_arrow.names])
    coreids = core["openalex_id"].fillna("").astype(str).str.strip().str.lower().str.rstrip("/")
    fullids = full["openalex_id"].fillna("").astype(str).str.strip().str.lower().str.rstrip("/")
    if coreids.eq("").any() or coreids.duplicated().any() or fullids.duplicated().any():
        raise ValueError("Empty/duplicate identifiers prevent matching")
    mapped = pd.Index(coreids).get_indexer(fullids)
    eligible = full["ft_decision"].fillna("").astype(str).str.lower().str.strip().isin(
        {"include_meta_candidate", "include_core_fulltext", "include_policy_fulltext"})
    length = pd.to_numeric(full["text_length"], errors="coerce").fillna(0)
    selected = np.flatnonzero((eligible&(length>0)).to_numpy() & (mapped>=0))
    orig = core.iloc[mapped[selected]]
    desc = full.iloc[selected]
    n = len(selected)
    limits = [64, 128, 256, 384, 512, 768]
    matches = collections.Counter()
    counters = collections.Counter()
    for old, new in zip(orig["text_for_analysis"].fillna(""),
                        desc["topic_text"].fillna("")):
        a = " ".join(str(old).split()).casefold()
        b = " ".join(str(new).split()).casefold()
        aw = a.split(" ")
        bw = b.split(" ")
        for length_words in limits:
            if len(aw)>=length_words and len(bw)>=length_words:
                counters[length_words] += 1
                if aw[:length_words] == bw[:length_words]:
                    matches[length_words] += 1
    return {
        "paired_explicitly_accepted": n,
        "whitespace_token_prefix_comparison": {
            str(k): {"eligible_pairs_with_at_least_n_words": counters[k],
                     "identical_first_n_words": matches[k]}
            for k in limits
        },
        "caution": "Word splits are NOT MiniLM WordPiece token counts; actual tokenizer inspection remains required."
    }


def optional_local_tokenizer(project):
    result = {"status": "not_attempted"}
    try:
        import transformers
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(
            "sentence-transformers/all-MiniLM-L6-v2",
            local_files_only=True
        )
        sample = pd.read_parquet(
            project/"data/processed/fulltext_topic_model_documents.parquet",
            columns=["topic_text", "ft_decision", "text_length"]
        )
        flags = sample["ft_decision"].fillna("").astype(str).str.strip().str.lower()
        acceptable = flags.isin({"include_meta_candidate","include_core_fulltext",
                                 "include_policy_fulltext"})
        texts = sample.loc[acceptable, "topic_text"].fillna("").astype(str)
        if len(texts)>200:
            texts = texts.sample(n=200, random_state=42)
        counts = [len(tokenizer.encode(v, add_special_tokens=True,
                 truncation=False)) for v in texts.tolist()]
        result = {"status": "available",
                  "sample_documents": len(counts),
                  "tokenizer_reported_max_length": (
                      int(tokenizer.model_max_length)
                      if tokenizer.model_max_length < 1000000 else None),
                  "untruncated_wordpiece_p10": int(np.quantile(counts, .1)),
                  "untruncated_wordpiece_median": int(np.median(counts)),
                  "untruncated_wordpiece_p90": int(np.quantile(counts, .9)),
                  "fraction_over_256": round(float(np.mean(np.asarray(counts)>256)),5),
                  "fraction_over_512": round(float(np.mean(np.asarray(counts)>512)),5)}
    except Exception as exc:
        result = {"status": "offline_tokenizer_not_available",
                  "exception_type": type(exc).__name__}
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default=str(Path.home()/"ai_policy_he"))
    parser.add_argument("--out", default="reports/phase10")
    args = parser.parse_args()
    root=Path(args.project).expanduser().resolve()
    out=Path(args.out).expanduser().resolve()
    if not root.is_dir() or out==root or root in out.parents:
        parser.error("Project required; output outside original project")
    out.mkdir(parents=True, exist_ok=True)
    evidence={
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "environment": current_environment(Path.home()),
        "original_scripts": [script_signals(root/"scripts"/name) for name in SCRIPTS],
        "text_prefix_audit": text_probe(root),
        "local_tokenizer_probe": optional_local_tokenizer(root),
        "limitations": [
            "Identical vectors are confirmed by phase09, but identifying truncation requires original tokenizer/model settings.",
            "The online/offline model availability of the current Python does not rule out other Singularity or virtualenv installations.",
            "Source-code syntax signals do not establish that a parameter was used in the saved embedding matrices.",
            "No model downloads, new embeddings, raw texts or source-project modifications were performed."
        ]
    }
    (out/"tokenizer_environment_audit.json").write_text(
        json.dumps(evidence,indent=2,ensure_ascii=False),encoding="utf8")
    lines=["# Phase 10 — MiniLM truncation and environment audit","",
           "UTC: "+evidence["created_utc"],"",
           "## Python environment",str(evidence["environment"]),"",
           "## Offline tokenizer",str(evidence["local_tokenizer_probe"]),"",
           "## Whitespace token prefix audit",str(evidence["text_prefix_audit"]),"",
           "## Original program source clues"]
    for s in evidence["original_scripts"]:
        lines.append("- "+s["filename"]+": "+str(s.get("runtime_or_truncation_signals",s.get("error"))))
    lines+=["","## Limitations"]+["- "+x for x in evidence["limitations"]]
    (out/"summary.md").write_text("\n".join(lines)+"\n",encoding="utf8")
    print("PHASE 10 COMPLETE")
    print("Current Python sentence-transformers:",evidence["environment"]["dependency_availability"]["sentence-transformers"])
    print("HF model cached:",evidence["environment"]["model_cache_presence"]["hf_hub_model_default_cache"])
    print("Offline tokenizer:",evidence["local_tokenizer_probe"]["status"])
    print("Reports:",out/"summary.md",out/"tokenizer_environment_audit.json")


if __name__=="__main__":
    main()
