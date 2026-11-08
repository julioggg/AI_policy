#!/usr/bin/env python3
"""Phase27 — integrity and scientific QA of returned 80-case methods-panel decisions.

Inputs: original protected BLANK Phase26 XLSX and its separately returned
completed version. The original Phase26 package itself was assembled from the
independent Phase20/21/23/24/25 source-of-record files and checked against public
counts. We strictly verify EVERY immutable source field of that original
package against the returned workbook and all four manually completed fields.

Publication-facing result has ONLY aggregated counts, response completeness,
panel/earlier consensus retention, conflict with independently authored QA,
and transparent warning that a panel exposed to old ratings is *not*
an independent blind validation. The code does not overwrite any previous
human labels, key, or Phase23 design-based estimates, and publishes NO
publication texts, IDs, single-record annotations or source rationales.
"""
from __future__ import annotations
import argparse
from collections import Counter
import datetime as dt
import json
from pathlib import Path
import importlib.util
import math

N=80
EDITABLE=(23,24,25,26)
RELEVANCE=("0","1","2","3","9")
DISCIPLINES=("ssh","engineering","health_sciences","general_he","uncertain")
POLICIES=("teaching_learning","assessment","ethics_integrity","governance_policy",
          "research_scholarship","ai_literacy_training","equity_access",
          "privacy_security","general_policy","not_applicable","uncertain")
FIELD_NAMES={"relevance":(7,8,23),"discipline":(11,12,24),
             "policy_posthoc":(15,16,25)}
COLUMNS={
  "relevance":(23,RELEVANCE),
  "discipline":(24,DISCIPLINES),
  "policy":(25,POLICIES),
  "scientific_justification":(26,None)
}

def module(filename,name):
    import importlib.util
    path=Path(__file__).resolve().parent/filename
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def integrity(original,completed,phase26,report25):
    phase26module=module("26_prepare_methodological_reconciliation.py","phase27_source")
    reader=module("25_compare_independent_screening_qa.py","phase27_excel_reader")
    blank=reader.sheet_records(reader.xlsx_sheets(original,{"CASOS"})["CASOS"],
                              phase26module.HEADERS,N,"Original Phase26")
    returned=reader.sheet_records(reader.xlsx_sheets(completed,{"CASOS"})["CASOS"],
                                 phase26module.HEADERS,N,"Returned Phase26")
    if set(blank)!=set(returned):
        raise ValueError("Returned Phase26 workbook does not contain exactly the original 80 QA codes")
    flags=Counter()
    for q in blank:
        ref=blank[q]
        row=returned[q]
        if any(ref[i]!=row[i] for i in range(len(ref)) if i not in EDITABLE):
            raise ValueError("The returned panel edited scientific evidence or previously recorded ratings")
        if any(ref[i] for i in EDITABLE):
            raise ValueError("Source Phase26 panel rubric was not originally blank")
        if not ref[0].startswith("Q"):
            raise ValueError("Protected QA code was altered")
        for name,ind in (("relevance",20),("discipline",21),("policy",22)):
            if row[ind] not in ("SÍ","NO"):
                raise ValueError("Protected Phase26 mismatch indicator was altered")
            flags[name]+=int(row[ind]=="SÍ")
        flags["unique"]+=int(any(row[i]=="SÍ" for i in (20,21,22)))
    expected=phase26.get("mismatch_counts",{})
    if (expected.get("mismatch_relevance")!=flags["relevance"] or
        expected.get("mismatch_discipline")!=flags["discipline"] or
        expected.get("mismatch_policy")!=flags["policy"] or
        expected.get("unique_cases_with_mismatch")!=flags["unique"]):
        raise ValueError("Returned Phase26 casebook differs from public Phase26 source integrity report")
    old=report25.get("results",{})
    if flags["relevance"]!=old.get("relevance_mismatch_cases") or \
       flags["discipline"]!=old.get("discipline_mismatch_cases") or \
       flags["policy"]!=old.get("post_hoc_policy_mismatch_cases"):
        raise ValueError("Phase26 casebook does not match the published Phase25 independent QA diagnostic")
    # The original Phase26 QA source is not a new independent fourth rater;
    # we must not silently cast its later normalized policy as a fully blinded review.
    return returned,dict(flags)


def completeness(data):
    outcome={}
    all_filled=True
    for name,(column,valid) in COLUMNS.items():
        values=[row[column] for row in data.values()]
        filled=sum(bool(x) for x in values)
        outcome[name]={"filled":filled,"total":N}
        if any(x and valid is not None and x not in valid for x in values):
            raise ValueError("Returned human panel decision outside the agreed rubric in "+name)
        all_filled=all_filled and filled==N
    return outcome,all_filled


def summarize(data):
    result={}
    for name,(previous,qa,final) in FIELD_NAMES.items():
        old=[row[previous] for row in data.values()]
        independent=[row[qa] for row in data.values()]
        post=[row[final] for row in data.values()]
        prior_exact=sum(x==y for x,y in zip(old,post))
        QA_exact=sum(x==y for x,y in zip(independent,post))
        transition=Counter((a,b) for a,b in zip(old,post) if a!=b)
        count=Counter(post)
        result[name]={
            "records":N,
            "retained_prior_consensus":prior_exact,
            "changed_prior_consensus":N-prior_exact,
            "agreement_with_prior_fraction":round(prior_exact/N,5),
            "agreement_with_prior_qa_fraction":round(QA_exact/N,5),
            "agree_with_prior_QA_cases":QA_exact,
            "final_category_counts":dict(sorted(count.items())),
            "changes_from_prior":{str(a)+"_to_"+str(b):v for (a,b),v in
                                  sorted(transition.items())},
            "comparison_type":(
                "posthoc-normalized policy QA, NOT original blind codebook QA"
                if name=="policy_posthoc" else
                "original independent Phase24 QA ratings compared with nonblinded panel"
            )
        }
    reasons=[row[26] for row in data.values()]
    templated=sum(reason.startswith("[R") for reason in reasons)
    unresolved=Counter(r[23] for r in data.values())["9"]
    count_noreview=sum(
        row[23]==row[7] and row[24]==row[11] and row[25]==row[15]
        for row in data.values())
    result["panel_justification_diagnostics"]={
        "filled":len(reasons),
        "distinct_rationale_strings":len(set(reasons)),
        "using_category_prefix_template":templated,
        "residual_uncertain_9_relevance":unresolved,
        "all_three_dimensions_identical_to_prior_consensus_n":count_noreview,
        "interpretation":"Text-pattern and prior-consensus retention flags are methodological cautions, not proof of correctness, independence, invalidity or fabrication."
    }
    result["scientific_stop_rule"]={
        "methodological_compatibility_vs_blind_QA":"UNRESOLVED",
        "independent_agreement_not_recalculated_by_nonblinded_panel":True,
        "original_Phase25_80case_QA_remains_independent":True,
        "phase23_population_estimates_automatically_updated":False,
        "policy_codebook_validity_and_rater_training_require_external_documentation":True,
        "next_needed":"Document a panel protocol/coder independence and full-text resolution or independent blinded rescreen on a new probability sample before making validation claims."
    }
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--original-xlsx",default=str(
        Path.home()/"ai_policy_panel_conciliacion_fase26_privado/Conciliacion_Metodologica_Fase26.xlsx"))
    p.add_argument("--returned-xlsx",required=True)
    p.add_argument("--phase26-report",default="reports/phase26/panel_reconciliation_preparation_aggregate.json")
    p.add_argument("--phase25-report",default="reports/phase25/independent_screening_qa_aggregate.json")
    p.add_argument("--out",default="reports/phase27")
    args=p.parse_args()
    original=Path(args.original_xlsx).expanduser().resolve()
    returned=Path(args.returned_xlsx).expanduser().resolve()
    out=Path(args.out).expanduser().resolve()
    if original==returned or not original.is_file() or not returned.is_file():
        p.error("Both original blank Phase26 and separately completed Phase26 XLSX files are required")
    for folder in (original.parent,returned.parent):
        if out==folder or folder in out.parents or out in folder.parents:
            p.error("Never write public aggregate reports in or above private human-review sources")
    p26=json.loads(Path(args.phase26_report).read_text(encoding="utf8"))
    p25=json.loads(Path(args.phase25_report).read_text(encoding="utf8"))
    if p26.get("status")!="private_methodological_reconciliation_packet_prepared_NO_new_human_decisions" or \
       p26.get("cases")!=N or p26.get("panel_decisions_filled")!=0:
        raise ValueError("Phase26 source package not authoritative/expected")
    if p25.get("status")!="independent_qa_scored_with_posthoc_policy_normalization":
        raise ValueError("Phase25 original independent QA report is missing")
    raw,flags=integrity(original,returned,p26,p25)
    readiness,filled=completeness(raw)
    report={
        "created_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
        "status":("completed_panel_reconciliation_reviewed_not_independently_validated"
                  if filled else "awaiting_panel_reconciliation_human_decisions"),
        "source_integrity":{
            "returned_workbook_matches_original_sample":True,
            "all_historical_source_text_and_evaluations_unchanged":True,
            "all_original_panel_decision_cells_blank":True,
            "phase25_and_phase26_aggregate_conflicts_reverified":True,
            "phase26_original_mismatch_counts":flags
        },
        "readiness":readiness,
        "study_design":"80-case purposely risk-enriched human panel reconciliation, nonblinded to earlier A/B and consensus ratings",
        "limitations":[
            "A panel that saw the prior A/B and consensus decisions cannot be treated as an independent blinded validation round.",
            "Very high retention of the previous consensus, if seen, requires protocol and case-specific rationales rather than automatic endorsement.",
            "Original independent Phase24 relevance and discipline ratings retain their status. Later codebook-normalized Phase24 policy was post hoc and must be labelled as such.",
            "The 80-case panel sample was deliberately risk-enriched and cannot be extrapolated to all 368 or 10,283 corpus records.",
            "The original Phase23 stratum-weighted estimates are unchanged; this script does not recalculate classifier accuracy, precision or recall.",
            "The presence of text in rationales is not itself a demonstration that a methods panel met procedural independence or study-quality criteria.",
            "No raw records, blinded QA IDs, human case justifications, article titles/abstracts or matching keys are released."
        ]
    }
    if filled:
        report["results"]=summarize(raw)
    out.mkdir(parents=True,exist_ok=True)
    (out/"panel_reconciliation_audit_aggregate.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    text=[
        "# Phase27 — Returned methods-panel screening reconciliation audit",
        "", "Status: "+report["status"],"",
        "## Source integrity and all four consensus fields",
        json.dumps({"source_integrity":report["source_integrity"],
                    "readiness":report["readiness"]},indent=2),
    ]
    if filled:
        text+=["","## Descriptive panel disposition — DOES NOT independently validate previous consensus",
               json.dumps(report["results"],indent=2)]
    text+=["","## Limits"]+["- "+v for v in report["limitations"]]
    (out/"summary.md").write_text("\n".join(text)+"\n",encoding="utf8")
    print("PHASE27",report["status"])
    for name,v in readiness.items():
        print(name,v["filled"],"/",v["total"])
    if filled:
        for name in FIELD_NAMES:
            part=report["results"][name]
            print(name,"retained original",part["retained_prior_consensus"],
                 "changed",part["changed_prior_consensus"],
                 "matches original QA",part["agree_with_prior_QA_cases"])
        print("WARNING: Panel review is NOT independently blinded confirmation.")
    print("PUBLIC aggregate:",out/"panel_reconciliation_audit_aggregate.json")
    print("NO private records, original source sheets or panel rationales exported.")


if __name__=="__main__":
    main()
