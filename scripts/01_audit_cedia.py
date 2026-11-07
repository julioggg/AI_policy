#!/usr/bin/env python3
"""Read-only audit of the CEDIA AI-policy project for peer-review revision.

Outputs contain aggregates, relative filenames, column NAMES, numeric metrics,
and method signatures. They NEVER export PDF/full-text content, article titles,
authors, DOIs, document identifiers, original source code or secrets.
Python >= 3.9. No external dependencies needed.
"""
from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

EXPECTED = [199366, 102822, 97267, 22524, 21676, 10283, 10265, 5000, 3656, 3655]
IGNORE_DIRS = {".git", ".venv", "venv", "__pycache__", ".ipynb_checkpoints",
               "site-packages", "node_modules", ".cache"}
DATA_EXTS = {".csv", ".parquet", ".json", ".jsonl", ".xlsx", ".npy", ".npz",
             ".pkl", ".joblib", ".feather"}
REPORT_EXTS = {".md", ".txt"}
GOOD_NAMES = (
    "article_ready", "included", "screen", "q1", "refined", "dedup", "fulltext",
    "full_text", "openalex", "corpus", "embedding", "manifest", "metadata",
    "policy", "discipline", "topic", "kmeans", "quality", "robust", "network",
    "provenance", "evidence", "method", "prisma", "search", "retriev", "sampling"
)
METRIC_WORDS = ("silhouette", "davies", "calinski", "cluster", "topic",
                "coherence", "stability", "n_records", "n_documents", "count",
                "kmeans", "n_clusters", "score", "seed", "n_init", "n_samples")
CODE_FLAGS = {
    "openalex_search": r"(?i)openalex|from_publication_date|to_publication_date|search=.*(ai|policy)",
    "filter_and_dedup": r"(?i)drop_duplicates|deduplic|article.ready|q1.refined|quality.refin|relevance",
    "screening": r"(?i)screening|screen_|human.review|manual.review|inclusion|exclusion",
    "fulltext_selection": r"(?i)5000|high.priority|fulltext|full_text|pdf.*extract",
    "classification": r"(?i)policy.dimension|disciplin|evidence.maturity|meta.tier|policy.use",
    "embedding": r"(?i)sentence.?transform|embedding|model_name|model_id",
    "umap": r"(?i)umap|n_neighbors|min_dist",
    "hdbscan": r"(?i)hdbscan|min_cluster_size|min_samples",
    "kmeans": r"(?i)kmeans|n_clusters|n_init|random_state",
    "quality": r"(?i)silhouette|davies.bouldin|calinski.harabasz|coherence|stability",
    "reproducibility": r"(?i)random.seed|manual.seed|hashlib|sha256|manifest",
}
PATTERNS = {k: re.compile(v) for k, v in CODE_FLAGS.items()}
SECRET = re.compile(r"(?i)password|passwd|secret|api.key|access.token|refresh.token|"
                    r"bearer|authorization|private.key|client.secret|^.*\.env")
NUMERIC = re.compile(r"^[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?$")
SAFE_MODEL = re.compile(r"(?i)(?:sentence-transformers|intfloat|BAAI|allenai|"
                        r"paraphrase-|all-MiniLM|multilingual-e5)[a-zA-Z0-9/_\-.]*")
SOURCE_PRIORITY = ("scripts/", "manuscript/", "outputs/", "ARTICLE_ZIPS_CLEAN/")


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def inspect_csv(path: Path, count_small: bool) -> dict:
    out = {}
    try:
        with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fp:
            reader = csv.reader(fp)
            header = next(reader, [])
            out["columns"] = [str(h)[:90] for h in header[:100]]
            out["column_count"] = len(header)
            if count_small:
                out["rows"] = sum(1 for _ in reader)
    except Exception as exc:
        out["error_type"] = type(exc).__name__
    return out


def parquet_schema(path: Path) -> dict:
    try:
        import pyarrow.parquet as pq
        meta = pq.ParquetFile(path).metadata
        return {"rows": meta.num_rows, "columns": list(meta.schema.names)[:100],
                "row_groups": meta.num_row_groups}
    except ImportError:
        return {"info": "pyarrow unavailable; no parquet data read"}
    except Exception as exc:
        return {"error_type": type(exc).__name__}


def numeric_metrics(path: Path) -> list:
    """Only export numeric scalar cells (never identifiers or text fields)."""
    preview = []
    try:
        with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fp:
            reader = csv.DictReader(fp)
            for idx, row in enumerate(reader):
                if idx >= 25:
                    break
                safe = {}
                for key, value in row.items():
                    if not key or not value or len(key) > 60:
                        continue
                    k = key.lower()
                    if not any(w in k for w in METRIC_WORDS) and k not in {"k", "n"}:
                        continue
                    if NUMERIC.fullmatch(str(value).strip()):
                        safe[key] = float(value)
                if safe:
                    preview.append(safe)
    except Exception:
        pass
    return preview[:25]


def method_signatures(path: Path) -> dict:
    counts = collections.Counter()
    locations = collections.defaultdict(list)
    model_names = set()
    numeric_parameters = collections.defaultdict(set)
    par = re.compile(r"\b(random_state|n_init|n_neighbors|min_dist|min_cluster_size|min_samples|"
                     r"n_components|n_clusters|batch_size|random_seed)\s*=\s*"
                     r"([+-]?(?:\d+(?:\.\d+)?|\.\d+))\b")
    try:
        with path.open("r", encoding="utf-8", errors="replace") as fp:
            for line_no, line in enumerate(fp, 1):
                if SECRET.search(line):
                    continue
                for flag, pattern in PATTERNS.items():
                    if pattern.search(line):
                        counts[flag] += 1
                        if len(locations[flag]) < 15:
                            locations[flag].append(line_no)
                for key, val in par.findall(line):
                    numeric_parameters[key].add(val)
                for m in SAFE_MODEL.findall(line):
                    if len(m) <= 110:
                        model_names.add(m)
    except Exception as exc:
        return {"error_type": type(exc).__name__}
    return {"signals": dict(counts),
            "line_numbers": dict(locations),
            "numeric_parameters": {k: sorted(v) for k, v in numeric_parameters.items()},
            "candidate_model_identifiers": sorted(model_names)[:20]}


def references_stage_counts(path: Path) -> list:
    """Indicate mentions of expected counts only; do not export prose."""
    try:
        if path.stat().st_size > 200_000:
            return []
        txt = path.read_text(encoding="utf-8", errors="replace")
        normalized = re.sub(r"(?<=\d)[,._ ](?=\d{3}(?:\D|$))", "", txt)
        return [n for n in EXPECTED if re.search(r"(?<!\d)" + str(n) + r"(?!\d)", normalized)]
    except Exception:
        return []


def deep_fulltext_counts(path: Path) -> dict:
    """Count records and missing text locally; never output textual values."""
    stats = {"path": path.name}
    try:
        csv.field_size_limit(min(sys.maxsize, 2**31 - 1))
        with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fp:
            reader = csv.DictReader(fp)
            fields = reader.fieldnames or []
            candidates = [h for h in fields if re.search(r"(?i)(clean.?text|full.?text|extracted.?text|^text$)", h)]
            stats["text_column_detected"] = candidates[:8]
            stats["row_count"] = 0
            stats["empty_text_count"] = 0
            for row in reader:
                stats["row_count"] += 1
                if candidates and not any(str(row.get(col, "")).strip() for col in candidates):
                    stats["empty_text_count"] += 1
    except Exception as exc:
        stats["error_type"] = type(exc).__name__
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Policy HE: safe CEDIA revision inventory")
    parser.add_argument("--project", default=str(Path.home() / "ai_policy_he"))
    parser.add_argument("--out", default="reports/phase01")
    parser.add_argument("--deep-count", action="store_true",
                        help="Parse one full-text CSV locally to reconcile exact document counts")
    args = parser.parse_args()
    root = Path(args.project).expanduser().resolve()
    out = Path(args.out).expanduser().resolve()
    if not root.is_dir():
        parser.error("Project not found: " + str(root))
    if out == root or root in out.parents:
        parser.error("Output must be OUTSIDE the original project")
    out.mkdir(parents=True, exist_ok=True)

    exts = collections.Counter()
    totals = collections.Counter()
    candidates = []
    scripts = []
    reports = []
    total_size = 0
    total_files = 0

    for base, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]
        for name in names:
            path = Path(base) / name
            try:
                size = path.stat().st_size
            except OSError:
                continue
            total_files += 1
            total_size += size
            suffix = path.suffix.lower()
            exts[suffix or "[none]"] += 1
            totals[suffix or "[none]"] += size
            relative = rel(path, root)
            if suffix == ".py" and "/scripts/" in "/" + relative:
                scripts.append(path)
            if suffix in REPORT_EXTS and any(token in name.lower() for token in GOOD_NAMES):
                reports.append(path)
            if suffix in DATA_EXTS and any(token in name.lower() for token in GOOD_NAMES):
                candidates.append((path, size))

    # Prefer canonical paths over repeated ZIP/package exports.
    def sort_priority(item):
        p = item[0] if isinstance(item, tuple) else item
        rp = rel(p, root)
        return (0 if rp.startswith("scripts/") else
                1 if rp.startswith("manuscript/") else
                2 if rp.startswith("data/") else
                3 if rp.startswith("outputs/") else
                4 if rp.startswith("ARTICLE_ZIPS_CLEAN/") else 5,
                len(rp), rp)

    data_items = []
    unique = set()
    for path, size in sorted(candidates, key=sort_priority):
        key = (path.name.casefold(), size)
        if key in unique:
            continue
        unique.add(key)
        record = {"path": rel(path, root), "size_bytes": size,
                  "extension": path.suffix.lower()}
        if path.suffix.lower() == ".csv":
            record.update(inspect_csv(path, count_small=size <= 4_000_000))
            if size < 150_000 and any(t in path.name.lower() for t in
                                      ("quality", "metric", "silhouette", "coherence",
                                       "stability", "kmeans")):
                record["numeric_metric_preview"] = numeric_metrics(path)
        elif path.suffix.lower() == ".parquet":
            record.update(parquet_schema(path))
        data_items.append(record)
        if len(data_items) >= 130:
            break

    method_items = []
    for path in sorted(scripts, key=sort_priority):
        method_items.append({"path": rel(path, root), **method_signatures(path)})

    report_items = []
    seen = set()
    for path in sorted(reports, key=sort_priority):
        if path.name.lower() in seen:
            continue
        seen.add(path.name.lower())
        counts = references_stage_counts(path)
        report_items.append({"path": rel(path, root), "stage_count_mentions": counts})
        if len(report_items) >= 80:
            break

    deep = None
    if args.deep_count:
        matching = [(p, size) for p, size in candidates
                    if p.name.lower() == "fulltext_topic_model_documents.csv"]
        if matching:
            matching.sort(key=sort_priority)
            deep = deep_fulltext_counts(matching[0][0])
        else:
            deep = {"info": "No file named fulltext_topic_model_documents.csv found"}

    inventory = {
        "audit_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "project_label": root.name,
        "files_total": total_files, "bytes_total": total_size,
        "file_extensions": dict(exts), "bytes_by_extension": dict(totals),
        "candidate_data_files": data_items,
        "report_stage_mentions": report_items,
        "deep_fulltext_count": deep,
        "privacy": "No row-level scholarly data, document text, titles, authors, identifiers or source code exported."
    }
    (out / "inventory.json").write_text(
        json.dumps(inventory, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out / "method_signals.json").write_text(
        json.dumps(method_items, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    lines = [
        "# Fase 1 — Auditoría de la investigación original",
        "",
        "Proyecto: " + root.name,
        "Fecha UTC: " + inventory["audit_utc"],
        "Modo: lectura únicamente del proyecto original; métricas agregadas.",
        "",
        "## Inventario",
        "- Archivos: " + str(total_files),
        "- Tamaño: " + format(total_size / (1024**3), ".2f") + " GiB",
        "- Scripts de la carpeta scripts/: " + str(len(scripts)),
        "- Conjuntos de datos candidatos (únicos inspeccionados): " + str(len(data_items)),
        "",
        "## Rastreos de conteos de etapas",
        "La aparición de una cifra en un reporte NO verifica que el filtro fuera reproducible.",
        ""
    ]
    for n in EXPECTED:
        matching_reports = [x["path"] for x in report_items if n in x["stage_count_mentions"]]
        lines.append("- " + str(n) + ": " +
                     (", ".join(matching_reports[:3]) if matching_reports else "no localizado en los reportes resumidos"))
    lines += ["", "## Archivos numéricos y métricas candidatos"]
    for item in data_items[:65]:
        lines.append("- " + item["path"] + " (" +
                     str(item["size_bytes"]) + " B" +
                     (", registros: " + str(item["rows"]) if "rows" in item else "") + ")")
    lines += ["", "## Scripts principales y presencia de señales metodológicas"]
    for item in method_items:
        lines.append("- " + item["path"] + ": " +
                     ", ".join(item.get("signals", {}).keys()))
    if deep:
        lines += ["", "## Recuento profundo del CSV de documentos", 
                  "Registros: " + str(deep.get("row_count", "no determinado")),
                  "Filas sin texto: " + str(deep.get("empty_text_count", "no determinado")),
                  "Columnas de texto detectadas: " + ", ".join(deep.get("text_column_detected", []))]
    lines += [
        "", "## Límites de esta auditoría",
        "- No determina si los algoritmos se ejecutaron, ni valida clasificación o contenido científico.",
        "- Las cifras presentes en un reporte no sustituyen trazas o reglas de decisión.",
        "- Los recuentos de CSV mayores a 4 MB se omiten, salvo --deep-count para un CSV de texto completo.",
        "- Los encabezados son nombres de columnas; no se exportan valores de registros.",
        "- No se han descargado archivos, ejecutado scripts originales ni recalculado embeddings.",
        ""
    ]
    (out / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    print("FASE 1 OK")
    print("Proyecto leído:", root)
    print("Archivos:", total_files, "Datos candidatos:", len(data_items), "Scripts:", len(scripts))
    for name in ("summary.md", "inventory.json", "method_signals.json"):
        print("Reporte:", out / name)
    if deep:
        print("Conteo profundo:", deep)


if __name__ == "__main__":
    main()
