#!/usr/bin/env python3
"""Phase35 — design-weighted SCREENING validation after phases 30/32/33.

Technical metrics available WITHOUT claiming that the 74 R9 unresolved
records had full-text evidence. Do not conflate the human R policy scale
with an original classifier predicted "include_policy"; its three positive
labels are machine pipeline decisions, NOT ordinal predictions R1/R2/R3.

Inputs: original 10,283 row frozen CEDIA screening source, 1,200 private
random sampling key, two complete private raters, original blank files,
324 private completed panel decisions, signed manifest + phase32/33 reports.
Checks source integrity, human source evidence, codes, actual sample counts.

Outputs: ONLY aggregated 4x5 confusion/crosstab with design weights,
weighted uncertainty bounds for scope, policy relevance 2+ and 3, and
conditional-scope machine decision metrics by treating unknown S9 two
different ways. All results refer only to the ORIGINAL 10,283 final
screening records, not previous 11,393 and 848 bibliographic-filter
exclusions or the full 199,366 search-hit universe.

No unsampled source labels, article names, abstracts, source keys or other
privacy sensitive case records are exported. NO full-text validation claim.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import datetime as dt
import hashlib
import importlib.util
import json
import math
from pathlib import Path

SAMPLE={
    "screen_include_core": ("include_core",9264,800),
    "screen_include_policy": ("include_policy",899,290),
    "screen_include_context": ("include_context",102,92),
    "screen_exclude": ("exclude",18,18),
}
N=10283
NSAMPLE=1200
RELEVANCE=("0","1","2","3","9")
SCOPE=("0","1","9")

def mod(filename,alias):
    p=Path(__file__).resolve().parent/filename
    s=importlib.util.spec_from_file_location(alias,p)
    m=importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m

def digest(file):
    h=hashlib.sha256()
    with file.open("rb") as f:
        for block in iter(lambda:f.read(1048576),b""):
            h.update(block)
    return h.hexdigest()

def safe_ratio(a,b):
    return round(a/b,6) if b else None

def count_full(groups,name,numer,denom,strata=None):
    """Finite-population variance for a stratified rate with KNOWN denom."""
    total=0.
    variance=0.
    for stratum,(decision,Nh,nh) in SAMPLE.items():
        if strata is not None and stratum not in strata:
            continue
        obs=groups[stratum]
        assert len(obs)==nh
        y=[float(numer(v)) for v in obs]
        mean=sum(y)/nh
        total+=Nh*mean
        if nh<Nh and nh>1:
            var=sum((v-mean)**2 for v in y)/(nh-1)
            variance+=(Nh**2)*(1-nh/Nh)*var/nh
    rate=total/denom
    se=math.sqrt(variance)/denom
    return {
        "weighted_numerator":round(total,3),
        "known_population_denominator":denom,
        "estimate":round(rate,6),
        "approximate_normal_95pct_ci":[round(max(0,rate-1.96*se),6),
                                      round(min(1,rate+1.96*se),6)],
        "standard_error":round(se,6),
        "limitation":"Design-based SRS-WOR estimate, small-sample normal CI, conditional on reviewer reference and stated treatment of uncertain9."
    }

def safe_metric(tp,fp,fn,tn):
    def r(n,d):
        return round(n/d,6) if d else None
    precision=r(tp,tp+fp)
    recall=r(tp,tp+fn)
    specificity=r(tn,tn+fp)
    npv=r(tn,tn+fn)
    f1=r(2*tp,2*tp+fp+fn)
    return {
      "weighted_TP":round(tp,3),"weighted_FP":round(fp,3),
      "weighted_FN":round(fn,3),"weighted_TN":round(tn,3),
      "positive_predictive_value":precision,
      "sensitivity_in_FINAL_10283_frame":recall,
      "specificity_in_FINAL_10283_frame":specificity,
      "negative_predictive_value":npv,
      "f1_in_FINAL_10283_frame":f1
    }

def analyze(groups):
    totals={
      "n_by_stratum":{},
      "human_scope_weighted":{j:0. for j in SCOPE},
      "human_relevance_weighted":{j:0. for j in RELEVANCE},
      "human_topic_weighted":defaultdict(float),
      "human_discipline_weighted":defaultdict(float),
      "policy_R_by_machine_stratum_weighted":{},
      "scope_S_by_machine_stratum_weighted":{},
      "human_source_distribution":{},
    }
    for stratum,(decision,Nh,nh) in SAMPLE.items():
        rows=groups[stratum]
        w=Nh/nh
        totals["n_by_stratum"][stratum]={"population":Nh,"sample":nh,"design_weight":round(w,7)}
        dR={k:0. for k in RELEVANCE}
        dS={k:0. for k in SCOPE}
        how=Counter(row["source"] for row in rows)
        totals["human_source_distribution"][stratum]=dict(sorted(how.items()))
        for row in rows:
            r=row["R"];s=row["S"]
            dR[r]+=w;dS[s]+=w
            totals["human_relevance_weighted"][r]+=w
            totals["human_scope_weighted"][s]+=w
            totals["human_topic_weighted"][row["T"]]+=w
            totals["human_discipline_weighted"][row["D"]]+=w
        totals["policy_R_by_machine_stratum_weighted"][stratum]={k:round(v,3) for k,v in dR.items()}
        totals["scope_S_by_machine_stratum_weighted"][stratum]={k:round(v,3) for k,v in dS.items()}
    for name in ("human_relevance_weighted","human_scope_weighted",
                 "human_topic_weighted","human_discipline_weighted"):
        totals[name]={k:round(v,3) for k,v in sorted(totals[name].items())}
    if abs(sum(totals["human_scope_weighted"].values())-N)>0.01:
        raise ValueError("Weighted scope sample failed design conservation")
    if abs(sum(totals["human_relevance_weighted"].values())-N)>0.01:
        raise ValueError("Weighted relevance sample failed design conservation")
    policy_any_lo=count_full(groups,"R>=2 lower",
        lambda x:x["R"] in ("2","3"),N)
    policy_any_hi=count_full(groups,"R>=2 upper",
        lambda x:x["R"] in ("2","3","9"),N)
    direct_lo=count_full(groups,"R3 lower",
        lambda x:x["R"]=="3",N)
    direct_hi=count_full(groups,"R3 upper",
        lambda x:x["R"] in ("3","9"),N)
    higher_ed_lo=count_full(groups,"scope S1 lower",
        lambda x:x["S"]=="1",N)
    higher_ed_hi=count_full(groups,"scope S1 upper",
        lambda x:x["S"] in ("1","9"),N)

    # Original algorithm claimed inclusion: core + policy + context.
    # This is NOT model probability, and does NOT assess upstream exclusion.
    posN=sum(x[1] for k,x in SAMPLE.items() if k!="screen_exclude")
    predictive_bounds={}
    for status,unknown_as in (("S9_assumed_negative",False),("S9_assumed_positive",True)):
        sums=dict(tp=0.,fp=0.,fn=0.,tn=0.)
        for stratum,(_,Nh,nh) in SAMPLE.items():
            is_pos=stratum!="screen_exclude"
            weight=Nh/nh
            for row in groups[stratum]:
                positive=(row["S"]=="1" or (unknown_as and row["S"]=="9"))
                target=("tp" if positive else "fp") if is_pos else ("fn" if positive else "tn")
                sums[target]+=weight
        predictive_bounds[status]=safe_metric(sums["tp"],sums["fp"],sums["fn"],sums["tn"])
    return {
      "weighted_aggregated_cross_tabs":totals,
      "design_weighted_title_abstract_reference_prevalence":{
          "S1_higher_education_lower_bound":higher_ed_lo,
          "S1_or_S9_upper_bound":higher_ed_hi,
          "R2plus_strict_accepted_lower_bound":policy_any_lo,
          "R2plus_or_R9_upper_bound":policy_any_hi,
          "R3_direct_policy_lower_bound":direct_lo,
          "R3_or_R9_upper_bound":direct_hi
      },
      "AI_include_vs_human_higher_ed_scope_sensitivity":{
          "definition":"Machine positive = include_core/include_policy/include_context; machine negative = screen_exclude ONLY. Human positive = S1. S9 are separately treated as possible nonpositive/positive.",
          "population_scope":"Original final-screening N=10,283, after substantial upstream filtering; NOT original OpenAlex retrieval",
          "uncertainty_scenarios":predictive_bounds,
          "PPV_scope_lower_bound_including_uncertain9_as_negative":count_full(
              groups,"PPV scope lower",lambda x:x["S"]=="1",posN,
              strata={"screen_include_core","screen_include_policy","screen_include_context"}
          ),
          "PPV_scope_upper_bound_including_uncertain9_as_positive":count_full(
              groups,"PPV scope upper",lambda x:x["S"] in ("1","9"),posN,
              strata={"screen_include_core","screen_include_policy","screen_include_context"}
          ),
          "limitations":[
           "The original classifier has only 18 final-screen exclusions, and the original OpenAlex upstream filters are OUTSIDE the current frame. Near-perfect recall within this frame would be structurally misleading as a claim about initial search sensitivity.",
           "Scope S9 and relevance R9 represent UNRESOLVED text/abstract eligibility; these are extreme-scenario sensitivity bounds, NOT a verified fulltext truth standard.",
           "No model decision class is equated with strict direct-policy R3 or R2plus; include_policy is a pipeline stratum label, not a calibrated human relevance classification.",
           "No empirical claim of model precision can be made for policy-relatedness until a defensible mapping and study target are predeclared. No new human judgments were created.",
          ]
      }
    }

def main():
    ap=argparse.ArgumentParser()
    home=Path.home()
    ap.add_argument("--private-key",default=str(home/"ai_policy_validation1200_private/private_sampling_key.csv"))
    ap.add_argument("--original-a",default=str(home/"ai_policy_validation1200_private/Validacion_1200_A.xlsx"))
    ap.add_argument("--original-b",default=str(home/"ai_policy_validation1200_private/Validacion_1200_B.xlsx"))
    ap.add_argument("--returned-a",default=str(home/"ai_policy_validacion1200_expertos_recibidos_privado/Validacion_1200_IA-1.xlsx"))
    ap.add_argument("--returned-b",default=str(home/"ai_policy_validacion1200_expertos_recibidos_privado/Validacion_1200_IA-2.xlsx"))
    ap.add_argument("--manifest",default=str(home/"ai_policy_validation1200_private/private_locked_manifest.json"))
    ap.add_argument("--returned-panel",default=str(home/"ai_policy_validacion1200_panel_recibido_privado/Adjudicacion_Validacion_1200_Humana_COMPLETADA.xlsx"))
    ap.add_argument("--phase30-report",default="reports/phase30/full_validation_packet_aggregate.json")
    ap.add_argument("--phase32-report",default="reports/phase32/human_expert_agreement_aggregate.json")
    ap.add_argument("--phase33-report",default="reports/phase33/panel_adjudication_aggregate.json")
    ap.add_argument("--codebook",default="docs/phase30_full_validation_codebook_v1.0.md")
    ap.add_argument("--out",default="reports/phase35")
    args=ap.parse_args()
    dest=Path(args.out).expanduser().resolve()
    inputs={k:Path(v).expanduser().resolve() for k,v in vars(args).items()
            if k not in ("out",)}
    if any(not p.is_file() for p in inputs.values()):
        ap.error("Frozen private Phase30–33 source, key or manifest is missing")
    if any(dest==p.parent or dest in p.parents or p.parent in dest.parents
           for k,p in inputs.items() if k not in ("phase30_report","phase32_report","phase33_report","codebook")):
        ap.error("Cannot place public aggregate in a private source folder")
    if dest.exists() and any(dest.iterdir()):
        ap.error("Phase35 output exists, historical reports must not be overwritten")

    phase30=json.loads(inputs["phase30_report"].read_text())
    phase32=json.loads(inputs["phase32_report"].read_text())
    phase33=json.loads(inputs["phase33_report"].read_text())
    manifest=json.loads(inputs["manifest"].read_text())
    if phase30.get("sample_n")!=NSAMPLE or phase32.get("sample_n")!=NSAMPLE or phase33.get("casebook_n")!=324:
        raise ValueError("Incompatible parent phase sample counts")
    if not phase32.get("original_phase30_source_integrity_verified") or not phase33.get("phase32_original_expert_labels_immutable"):
        raise ValueError("Missing validated full sample lineage")
    if digest(inputs["codebook"])!=manifest.get("codebook_sha256"):
        raise ValueError("Frozen codebook checksum changed")
    for k in ("A","B"):
        if digest(inputs["original_"+k.lower()])!=manifest["pristine_workbook_sha256"][k]:
            raise ValueError("Pristine original Phase30 workbook checksum mismatch")
    phase30_helper=mod("30_prepare_full1200_validation.py","phase35_phase30")
    phase32_helper=mod("32_audit_pi_attested_human1200.py","phase35_phase32")
    phase33_helper=mod("33_audit_returned_panel1200.py","phase35_phase33")
    rawkey=phase30_helper.csvread(inputs["private_key"])
    if len(rawkey)!=NSAMPLE or len({r["validation_code"] for r in rawkey})!=NSAMPLE or len({r["openalex_id"] for r in rawkey})!=NSAMPLE:
        raise ValueError("Private random selection key lost unique 1200-case frame")
    check=Counter(r["stratum"] for r in rawkey)
    for k,(_,Npop,n) in SAMPLE.items():
        if check[k]!=n:
            raise ValueError("Stratified sample counts not identical to Phase30 plan")
    if set(check)!=set(SAMPLE):
        raise ValueError("Unexpected stratum in original private sample")

    blank={}
    returned={}
    for who in ("A","B"):
        b=phase32_helper.readbook(inputs["original_"+who.lower()],phase30_helper.HEADERS,"original_"+who)
        r=phase32_helper.readbook(inputs["returned_"+who.lower()],phase30_helper.HEADERS,"returned_"+who)
        phase32_helper.integrity(b,r,who,True)
        blank[who]=b["records"]
        returned[who]=r["records"]
    a=returned["A"];b=returned["B"]
    panels,_=phase33_helper.load_table(inputs["returned_panel"],phase32_helper.HEADERS)
    if len(panels)!=324 or set(a)!=set(b) or set(a)!=set(x["validation_code"] for x in rawkey):
        raise ValueError("Invalid reviewer A/B and reconciliation membership")
    if any(a[key][:5]!=b[key][:5] for key in a):
        raise ValueError("Mismatch in bibliographic evidence between independent human forms")
    if phase33["panel_scientific_reason_diagnostics"]["residual"]["uncertain_relevance_9"]!=74:
        raise ValueError("Unexpected Phase33 unresolved relevance 9 count")

    groups={k:[] for k in SAMPLE}
    stats=Counter()
    for item in rawkey:
        key=item["validation_code"]
        stratum=item["stratum"]
        if item["machine_ai_decision"]!=SAMPLE[stratum][0]:
            raise ValueError("Machine decision not consistent with original random sampling stratum")
        if key in panels:
            row=panels[key]
            if row[:5]!=a[key][:5]:
                raise ValueError("Panel silently modified source evidence")
            s,r,t,d=row[22:26]
            source="panel_324_reconciled"
            stats["panel"]+=1
            if row[27]=="yes": stats["fulltext_requested"]+=1
        else:
            x,y=a[key],b[key]
            if any(x[j]!=y[j] for j in (5,6,7,8,11)):
                raise ValueError("Unreconciled A/B disagreement outside Phase33 324-case panel")
            if x[6]=="9" or y[6]=="9" or x[11]=="yes":
                raise ValueError("Unknown or fulltext case absent from Phase33 reconciliation")
            s,r,t,d=x[5:9]
            source="A_B_unanimous_outside_panel"
            stats["unanimous"]+=1
        if s not in SCOPE or r not in RELEVANCE or t not in phase30_helper.TOPIC or d not in phase30_helper.DISCIPLINE:
            raise ValueError("Invalid final human S/R/T/D rating")
        if (s=="0" and r!="0") or (s=="9" and r!="9") or (s=="1" and r=="0"):
            raise ValueError("Inconsistent post-reconciliation human scope/relevance")
        groups[stratum].append({"S":s,"R":r,"T":t,"D":d,"source":source})
    if stats["panel"]!=324 or stats["unanimous"]!=876 or stats["fulltext_requested"]!=148:
        raise ValueError("Final human frame incomplete or more evidence missing than reported")
    if sum(v["R"]=="9" for chunk in groups.values() for v in chunk)!=74:
        raise ValueError("Human R9 unknown count differs from frozen panel report")
    report={
      "utc":dt.datetime.now(dt.timezone.utc).isoformat(),
      "status":"design_weighted_title_abstract_AI_screen_vs_PI_attributed_human_reference_NO_fulltext_truth",
      "source":"Phase30 1200-case stratified sample + independent expert attribution Phase32 + informed 324-case panel Phase33",
      "frame_population_n":N,
      "sample_n":NSAMPLE,
      "panel_n":stats["panel"],
      "AB_unanimous_not_on_panel_n":stats["unanimous"],
      "residual_R9_uncertain_n":74,
      "fulltext_requested_not_completed_n":148,
      "source_provenance_of_human_authorship_verified_independently":False,
      "fulltext_review_done":False,
      "analysis":analyze(groups),
      "required_qualifications":[
        "This analysis is conditional on the PI's assertion that both rating forms are actual independent expert work; workbook metadata says Claude AI, and Phase33 panel rationale is tagged [Adjudicación IA]. Signed/dated expert and panel provenance statements remain essential.",
        "The reference is based on title and abstract; 74 R9 remain unresolved. Rates include explicitly separate worst-case R9 scenarios, not forced judgments.",
        "Initial OpenAlex/earlier bibliographic-filter exclusions are outside the 10,283 frame. No inference about the original 199,366 retrieval pipeline's recall/specificity.",
        "Discipline/topic agreement between original rule labels and expert T/D is not computed here because differently operationalized constructs would require a declared mapping.",
        "No direct-policy classifier performance is asserted because the machine's include_policy stratum is NOT equivalent to expert R3; see weighted stratified contingency table.",
        "Design-weighted estimates reflect machine-stratified disproportionate sample; descriptive human agreement was unweighted and must be reported separately.",
        "The PHASE25 independent 80-case risk-enriched QA showed substantial discrepancies with older consensus and remains an important limitation to describe transparently."
      ]
    }
    dest.mkdir(parents=True,exist_ok=True)
    (dest/"screening_vs_expert_weighted_aggregate.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    (dest/"summary.md").write_text(
        "# Phase35 — Design-weighted title/abstract scope validation\n\n"
        "**Status:** "+report["status"]+"\n\n"
        "Target: N=10,283 final screen only; n=1200, 4 disproportionate machine screening strata; reference still has 74 unresolved R9.\n\n"
        "## Weighted human relevance by machine screening stratum\n\n"+
        json.dumps(report["analysis"]["weighted_aggregated_cross_tabs"]["policy_R_by_machine_stratum_weighted"],ensure_ascii=False,indent=2)+"\n\n"
        "## Design-weighted scope, R2+ and R3 prevalence bounds\n\n"+
        json.dumps(report["analysis"]["design_weighted_title_abstract_reference_prevalence"],ensure_ascii=False,indent=2)+"\n\n"
        "## Conditional binary screening scope sensitivity\n\n"+
        json.dumps(report["analysis"]["AI_include_vs_human_higher_ed_scope_sensitivity"],ensure_ascii=False,indent=2)+"\n\n"
        "## Scientific limits\n\n"+
        "\n".join("- "+x for x in report["required_qualifications"])+"\n",
        encoding="utf8")
    print("PHASE35",report["status"])
    print("N=10283 n=1200; panel=324; original agreement-only=876; R9=74; requested fulltext=148")
    print("Weighted summary:",dest/"screening_vs_expert_weighted_aggregate.json")
    print("NO article-level data or human/source identifiers exported.")

if __name__=="__main__":
    main()
