#!/usr/bin/env python3
"""Phase37: conservative correction of semicolon-separated ISO2 country strings.

Uses frozen original sources. Does NOT replace or rewrite Phase36 or the
original metadata. Reports corrected geographic INCIDENCE (multiple countries
per study permitted) for 10265 included, 3656 accessible documents and the
unambiguously matched DOI proxy of 5000 attempted records.

The 'priority_score / citations / top MAX_PDFS' pipeline is assessed by
STATIC AST only: no inference that a particular script revision was run, no
individual 5000-record membership audit because OpenAlex IDs are missing
from the manifest. No source text, DOI, title or record IDs in public reports.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
import csv
import datetime as dt
import importlib.util
import json
from pathlib import Path
import re

ISO2_SEMICOLON = re.compile(r"^\s*[A-Za-z]{2}\s*(?:;\s*[A-Za-z]{2}\s*)+$")


def load_phase36():
    source=Path(__file__).resolve().parent/"36_geographic_fulltext_bias.py"
    spec=importlib.util.spec_from_file_location("phase37_reused_36",source)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_countries(value, base):
    """Return (array | None, classification). Do not guess semicolon meaning."""
    old=base.countries(value)
    if old is not None:
        return old, ("empty" if not old else "previously_recognized")
    txt=str(value).strip()
    if ";" in txt:
        if ISO2_SEMICOLON.fullmatch(txt):
            codes=sorted(set(x.strip().upper() for x in txt.split(";")))
            return codes,"semicolon_iso2_recovered"
        return None,"semicolon_unrecognized"
    return None,"other_unrecognized"


def indexed(df, base):
    ids={}
    counters=Counter()
    for row in df.to_dict("records"):
        key=base.norm(row["openalex_id"])
        if not key or key in ids:
            raise ValueError("OpenAlex IDs empty or duplicated in frozen source")
        countries,status=parse_countries(row.get("countries"),base)
        ids[key]=countries
        counters[status]+=1
    return ids,counters


def _literal(node):
    try:
        return ast.literal_eval(node)
    except (ValueError,TypeError,MemoryError,RecursionError):
        return None


def selection_trace(path):
    if not path.is_file():
        return {"script_available":False,"status":"original source selection script missing"}
    tree=ast.parse(path.read_text(encoding="utf-8",errors="replace"))
    maxpdf=[]
    sorting=[]
    limit=[]
    priority_assignment_count=0
    for node in ast.walk(tree):
        if isinstance(node,(ast.Assign,ast.AnnAssign)):
            names=[]
            targets=node.targets if isinstance(node,ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target,ast.Name):
                    names.append(target.id)
                if isinstance(target,ast.Subscript):
                    key=_literal(target.slice)
                    if key=="priority_score":
                        priority_assignment_count+=1
            if "MAX_PDFS" in names:
                value=_literal(node.value)
                if type(value) is int:
                    maxpdf.append(value)
        if not isinstance(node,ast.Call) or not isinstance(node.func,ast.Attribute):
            continue
        method=node.func.attr
        receiver=node.func.value
        if not isinstance(receiver,ast.Name) or receiver.id!="included":
            continue
        if method=="sort_values":
            by=_literal(node.args[0]) if node.args else None
            ascending=None
            for kw in node.keywords:
                if kw.arg=="by":by=_literal(kw.value)
                if kw.arg=="ascending":ascending=_literal(kw.value)
            sorting.append({
                "line":node.lineno,
                "keys_match_priority_then_citations":by==["priority_score","cited_by_count"],
                "both_descending":ascending==[False,False],
            })
        elif method=="head":
            arg=node.args[0] if node.args else None
            limit.append({
                "line":node.lineno,
                "uses_MAX_PDFS":isinstance(arg,ast.Name) and arg.id=="MAX_PDFS",
                "literal_limit":_literal(arg)
            })
    return {
       "script_available":True,
       "MAX_PDFS_literal_assignments":maxpdf,
       "sort_operations":sorting,
       "head_operations":limit,
       "priority_score_assignment_nodes":priority_assignment_count,
       "selection_pipeline_explicit_priority_score_cited_by_count_descending":any(
           x["keys_match_priority_then_citations"] and x["both_descending"]
           for x in sorting),
       "selection_pipeline_has_head_MAX_PDFS":any(x["uses_MAX_PDFS"] for x in limit),
       "caution":"STATIC source inspection only. Definition of priority_score, original data ordering, and executed-version identity require separate verification."
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--project",default=str(Path.home()/"ai_policy_he"))
    p.add_argument("--phase36-report",default="reports/phase36/five_thousand_geographic_bias_aggregate.json")
    p.add_argument("--out",default="reports/phase37")
    args=p.parse_args()
    root=Path(args.project).expanduser().resolve()
    original=Path(args.phase36_report).expanduser().resolve()
    dest=Path(args.out).expanduser().resolve()
    if dest==root or dest in root.parents or root in dest.parents:
        p.error("Do not overwrite or publish within the original confidential project")
    if dest.exists() and any(dest.iterdir()):
        p.error("Phase37 exists; preserve previous independent audit")
    if not original.is_file():
        p.error("Phase36 original aggregate missing")
    p36=json.loads(original.read_text(encoding="utf-8"))
    if p36.get("original_counts",{}).get("screening_included_n")!=10265 or p36.get("original_counts",{}).get("fulltext_downloaded_or_preexisting_n")!=3656:
        raise ValueError("Phase36 lineage does not match original frame")
    base=load_phase36()
    data=root/"data/processed"
    original_manifest=root/"outputs/tables/fulltext_pdf_download_manifest.csv"
    src_script=root/"scripts/10_download_open_access_pdfs.py"
    if not all(x.is_file() for x in (
        data/"ai_assisted_screening_decisions.parquet",
        data/"fulltext_topic_model_documents.parquet",
        original_manifest
    )):
        p.error("Original private sources are missing")
    raw=base.load_parquet(data/"ai_assisted_screening_decisions.parquet",base.SOURCE_COLUMNS)
    full=base.load_parquet(data/"fulltext_topic_model_documents.parquet",base.SOURCE_COLUMNS)
    if len(raw)!=10283 or len(full)!=3656:
        raise ValueError("Frozen source sizes differ from original audit")
    flags=raw.ai_decision.astype(str).str.lower().isin(
        {"include_core","include_policy","include_context"})
    screened=raw.loc[flags].copy()
    if len(screened)!=10265:
        raise ValueError("Incorrect initial included frame")
    parent,parent_stats=indexed(screened,base)
    child,child_stats=indexed(full,base)
    if not set(child).issubset(parent):
        raise ValueError("Fulltext IDs do not belong to original included frame")
    doi_to_ids=defaultdict(set)
    for row in screened.to_dict("records"):
        d=base.doi(row.get("doi"))
        if d:doi_to_ids[d].add(base.norm(row["openalex_id"]))
    matched_ids=set()
    missing=0;ambiguous=0;unmatched=0
    with original_manifest.open(encoding="utf-8-sig",newline="") as f:
        manifestrows=list(csv.DictReader(f))
    if len(manifestrows)!=5000:
        raise ValueError("Attempt manifest does not contain exactly 5000 rows")
    for row in manifestrows:
        d=base.doi(row.get("doi"))
        if not d:
            missing+=1;continue
        ids=doi_to_ids.get(d,set())
        if len(ids)==1:
            matched_ids.update(ids)
        elif not ids:unmatched+=1
        else:ambiguous+=1
    proxy=p36["attempt_DOI_linkage_diagnostics"]
    if (len(matched_ids)!=proxy["unambiguously_linked_unique_included_records"] or
        missing!=proxy["missing_doi"] or ambiguous!=proxy["ambiguous_multiple_included_OpenAlex_ids"] or
        unmatched!=proxy["unmatched_doi"]):
        raise ValueError("DOI proxy reconstruction mismatch; audit sources independently")
    parent_vals=list(parent.values())
    full_vals=list(child.values())
    proxy_vals=[parent[k] for k in sorted(matched_ids)]
    corrected={
       "created_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
       "status":"phase37_corrected_semicolon_ISO2_country_incidence_with_remaining_source_cautions",
       "supersedes_phase36_country_results_only":True,
       "phase36_original_report_preserved_unchanged":True,
       "frame_n":10283,"included_n":10265,"attempt_n":5000,"available_fulltext_n":3656,
       "country_parser":"Previously recognized structured countries + strict ISO-2 semicolon-delimited country lists; no name/ISO conflation or inferred unknown codes",
       "included_country_parser_diagnostics":dict(parent_stats),
       "fulltext_country_parser_diagnostics":dict(child_stats),
       "comparison_included_vs_fulltext":base.share_metrics(parent_vals,full_vals,
            "included_10265_vs_fulltext_3656_semicolon_corrected"),
       "comparison_included_vs_DOI_proxy_attempts":base.share_metrics(parent_vals,proxy_vals,
            "included_10265_vs_DOI_linked_attempts_4834_semicolon_corrected"),
       "selection_tracing":selection_trace(src_script),
       "original_five_thousand_DOI_proxy_summary":{
         "attempts_n":5000,"unambiguous_matched_unique_publications":len(matched_ids),
         "attempts_without_doi":missing,"ambiguous_DOI_attempts":ambiguous,
         "unmatched_DOI_attempts":unmatched,
         "manifest_no_openalex_id":True,
         "precise_5000_original_member_selection_reproduced":False
       },
       "limitations":[
          "Country entries represent one or more institutional-country affiliations for each work, not a fractionalised country-attribution model.",
          "Only strict two-letter semicolon tokens were recovered; if semicolon_unrecognized remains nonzero, report the unparsed source counts before using geographic conclusions.",
          "No attempt was made to impute empty countries, which are distinct from unparsed country strings.",
          "The fulltext subset was nonrandomly prioritised and subject to retrieval failures; descriptive shifts are not automatically statistically significant.",
          "The 5000 attempted records have no OpenAlex IDs in manifest; matches by unambiguous DOI remain proxy evidence.",
          "Static AST confirms source statements but not the exact historical version executed or source of priority_score.",
          "The aggregate does not validate scientific paper eligibility, classifier relevance or inferences about country-specific research quality."
       ]
    }
    dest.mkdir(parents=True,exist_ok=True)
    out=dest/"country_semicolon_corrected_aggregate.json"
    out.write_text(json.dumps(corrected,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    short={
        "status":corrected["status"],
        "included_country_parser_diagnostics":corrected["included_country_parser_diagnostics"],
        "fulltext_country_parser_diagnostics":corrected["fulltext_country_parser_diagnostics"],
        "original_five_thousand_DOI_proxy_summary":corrected["original_five_thousand_DOI_proxy_summary"],
        "selection_tracing":corrected["selection_tracing"],
        "largest_corrected_shifts":corrected["comparison_included_vs_fulltext"]["largest_absolute_differences"],
        "limitations":corrected["limitations"]
    }
    (dest/"summary.md").write_text(
        "# Phase37 — corrected country string parser, preservation of Phase36\n\n"+
        json.dumps(short,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("PHASE37",corrected["status"])
    print("Included country formats:",dict(parent_stats))
    print("Fulltext country formats:",dict(child_stats))
    print("5000-attempt DOI-proxy matching:",len(matched_ids),"/5000, exact membership not demonstrated")
    print("Source static selection:",corrected["selection_tracing"])
    print("Public aggregate ONLY:",out)
    print("NO private article titles, DOI, countries string examples or OpenAlex IDs exported")

if __name__=="__main__":
    main()
