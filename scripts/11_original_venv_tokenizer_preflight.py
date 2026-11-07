#!/usr/bin/env python3
"""Phase 11: test original CEDIA virtualenv and MiniLM truncation, no downloads.

Use this script from the normal Singularity Python. It invokes the ORIGINAL
project .venv Python as a subprocess with HF offline settings and sends only
aggregate statistics to reports/phase11. Neither sources nor embeddings change.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys

PROBE = r'''
import json, sys
record = {"python_version": sys.version.split()[0]}
try:
    import torch
    import sentence_transformers
    import transformers
    record["torch"] = torch.__version__
    record["sentence_transformers"] = sentence_transformers.__version__
    record["transformers"] = transformers.__version__
except Exception as err:
    record["status"] = "dependency_missing"
    record["failure_type"] = type(err).__name__
    print("BEGIN_AUDIT_JSON" + json.dumps(record) + "END_AUDIT_JSON")
    sys.exit(0)
try:
    import numpy as np
    import pandas as pd
    import pyarrow.parquet as pq
    from sentence_transformers import SentenceTransformer
    from transformers import AutoTokenizer
    from pathlib import Path
    root = Path(sys.argv[1])
    model_id = "sentence-transformers/all-MiniLM-L6-v2"
    tokenizer = AutoTokenizer.from_pretrained(model_id, local_files_only=True)
    model = SentenceTransformer(model_id, device="cpu")
    model_limit = int(model.max_seq_length)
    record["model_limit_tokens"] = model_limit
    record["tokenizer_reported_limit"] = int(tokenizer.model_max_length) if tokenizer.model_max_length < 1000000 else None
    src = root / "data/processed/fulltext_topic_model_documents.parquet"
    cols = ["openalex_id", "topic_text", "full_text", "abstract", "ft_decision", "text_length"]
    df = pd.read_parquet(src, columns=[c for c in cols if c in pq.ParquetFile(src).schema_arrow.names])
    decision = df["ft_decision"].fillna("").astype(str).str.strip().str.lower()
    valid = decision.isin(["include_meta_candidate", "include_core_fulltext", "include_policy_fulltext"])
    valid &= pd.to_numeric(df["text_length"], errors="coerce").fillna(0) > 0
    ids = df.index[valid]
    sample = df.loc[ids].sample(n=min(120, len(ids)), random_state=20261107)
    lengths_topic = []
    lengths_full = []
    lengths_abs = []
    topic_head_matches_abs = 0
    for row in sample.itertuples(index=False):
        title_abs = str(row.abstract or "")
        topic = str(row.topic_text or "")
        full = str(row.full_text or "")
        full_tokens = tokenizer.encode(full, add_special_tokens=True, truncation=False)
        topic_tokens = tokenizer.encode(topic, add_special_tokens=True, truncation=False)
        abs_tokens = tokenizer.encode(title_abs, add_special_tokens=True, truncation=False)
        lengths_full.append(len(full_tokens))
        lengths_topic.append(len(topic_tokens))
        lengths_abs.append(len(abs_tokens))
        if len(topic_tokens) >= model_limit and len(abs_tokens)>3:
            topic_head_matches_abs += int(topic_tokens[1:20] == abs_tokens[1:20])
    record["status"] = "completed"
    record["sample_size"] = len(sample)
    record["topic_tokens_median"] = int(np.median(lengths_topic))
    record["topic_tokens_p10"] = int(np.quantile(lengths_topic, 0.10))
    record["topic_tokens_p90"] = int(np.quantile(lengths_topic, 0.90))
    record["full_text_tokens_median"] = int(np.median(lengths_full))
    record["abstract_tokens_median"] = int(np.median(lengths_abs))
    record["topic_over_model_limit"] = sum(x > model_limit for x in lengths_topic)
    record["full_text_over_model_limit"] = sum(x > model_limit for x in lengths_full)
    record["abstract_over_model_limit"] = sum(x > model_limit for x in lengths_abs)
    record["weak_topic_abstract_prefix_matches"] = topic_head_matches_abs
    # Do not encode original text in this probe or export any per-document values.
except Exception as err:
    record["status"] = "offline_load_or_data_error"
    record["failure_type"] = type(err).__name__
print("BEGIN_AUDIT_JSON" + json.dumps(record) + "END_AUDIT_JSON")
'''


def check_candidate(path, project):
    env = dict(os.environ)
    env.update({
        "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1",
        "HF_DATASETS_OFFLINE": "1", "HF_HUB_DISABLE_TELEMETRY": "1",
        "TOKENIZERS_PARALLELISM": "false", "OMP_NUM_THREADS": "4",
        "OPENBLAS_NUM_THREADS": "4", "MKL_NUM_THREADS": "4"
    })
    if not path.is_file():
        return {"candidate": "project_dot_venv_python", "status": "not_found"}
    try:
        proc = subprocess.run(
            [str(path), "-c", PROBE, str(project)], env=env,
            capture_output=True, text=True, timeout=240, check=False
        )
    except (OSError, subprocess.TimeoutExpired) as err:
        return {"candidate": "project_dot_venv_python", "status": "cannot_execute",
                "error_type": type(err).__name__}
    begin, end = "BEGIN_AUDIT_JSON", "END_AUDIT_JSON"
    output = proc.stdout
    a = output.rfind(begin)
    b = output.rfind(end)
    if a < 0 or b < 0 or b < a:
        return {"candidate": "project_dot_venv_python",
                "status": "no_probe_report", "exit_code": proc.returncode,
                "stderr_present": bool(proc.stderr)}
    try:
        data = json.loads(output[a+len(begin):b])
    except json.JSONDecodeError:
        return {"candidate": "project_dot_venv_python", "status": "invalid_probe_report"}
    data["candidate"] = "project_dot_venv_python"
    data["exit_code"] = proc.returncode
    return data


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--project", default=str(Path.home()/"ai_policy_he"))
    p.add_argument("--out", default="reports/phase11")
    args = p.parse_args()
    project = Path(args.project).expanduser().resolve()
    out = Path(args.out).expanduser().resolve()
    if not project.is_dir() or out == project or project in out.parents:
        p.error("Project must exist; output must be outside original project")
    out.mkdir(parents=True, exist_ok=True)
    probe = check_candidate(project/".venv/bin/python", project)
    result = {
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "probe": probe,
        "constraints": [
            "Tokenizer/model loaded with HF offline and no downloads.",
            "Token-length summaries are sampled, not population-wide.",
            "No source texts, identifiers, weights, vectors or environment paths are exported.",
            "A sentence-transformer limit is evidence of sequence truncation, but original vector provenance still requires separate verification.",
            "If this preflight succeeds, a chunk-based alternative must be compared on the same explicitly eligible records."
        ]
    }
    (out/"venv_tokenizer_preflight.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf8")
    md = ["# Phase 11 — Offline MiniLM original-environment preflight",
          "", "Date (UTC): " + result["generated_utc"], "",
          "## Result", json.dumps(probe, indent=2, ensure_ascii=False),
          "", "## Scientific limits"]
    md += ["- " + v for v in result["constraints"]]
    (out/"summary.md").write_text("\n".join(md)+"\n", encoding="utf8")
    print("PHASE 11 COMPLETE:", probe.get("status"))
    print("Original venv torch:", probe.get("torch", "not available"))
    print("Model token limit:", probe.get("model_limit_tokens", "not established"))
    print("Reports:", out/"summary.md", out/"venv_tokenizer_preflight.json")


if __name__ == "__main__":
    main()
