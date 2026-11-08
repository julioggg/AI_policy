#!/usr/bin/env python3
"""Phase29: score the genuinely independent Phase28 PILOT after both human reviews.

Checks original Phase28 workbook hashes, original evidence, blank initial
ratings, original label sets, rater-specific forms and strict rubric
consistency. Never sees machine screening decisions, strata or OpenAlex IDs;
does not assign human labels or resolve disagreements. Public report:
aggregate n/category distributions, agreement and kappa (not classifier
accuracy). Pilot is a NONREPRESENTATIVE calibration activity only.

Private original A/B responses are never overwritten or published.
"""
from __future__ import annotations

import argparse
from collections import Counter
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import importlib.util

SCOPE={"0","1","9"}
RELEVANCE={"0","1","2","3","9"}
TOPICS={"teaching_learning","assessment","ethics_integrity",
    "governance_policy","research_scholarship","ai_literacy_training",
    "equity_access","privacy_security","general_policy",
    "not_applicable","uncertain"}
DISCIPLINES={"ssh","engineering","health_sciences","general_he","uncertain"}
YESNO={"yes","no"}
EDITABLE=(5,6,7,8,9,10,11,12)


def mod(filename,name):
    here=Path(__file__).resolve().parent/filename
    spec=importlib.util.spec_from_file_location(name,here)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def hashfile(path):
    s=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            s.update(chunk)
    return s.hexdigest()


def readbook(path,rater):
    reader=mod("25_compare_independent_screening_qa.py","pilot29_reader")
    p28=mod("28_prepare_independent_pilot.py","pilot29_preparer")
    tabs=reader.xlsx_sheets(path,{"INSTRUCCIONES","PILOTO"})
    ins=tabs["INSTRUCCIONES"]
    if not ins or f"Evaluador {rater}" not in ins[0].get(1,""):
        raise ValueError("Pilot form was exchanged with the other reviewer or instructions changed")
    sheet=tabs["PILOTO"]
    if not sheet or [sheet[0].get(i,"") for i in range(len(p28.REVIEW_HEADERS))]!=p28.REVIEW_HEADERS:
        raise ValueError("Pilot workbook headers differ from the original frozen V0.2")
    data={}
    order=[]
    for item in sheet[1:]:
        if not any(str(v).strip() for v in item.values()):
            continue
        if any(k>=len(p28.REVIEW_FIELDS) and str(v).strip() for k,v in item.items()):
            raise ValueError("Unexpected extra pilot workbook data")
        values=[str(item.get(i,"")).strip() for i in range(len(p28.REVIEW_FIELDS))]
        code=values[0]
        if not code.startswith("CAL") or not code[3:].isdigit() or code in data:
            raise ValueError("Pilot codes missing, duplicated or malformed")
        data[code]=values
        order.append(code)
    if len(data)!=30:
        raise ValueError("A complete Phase28 pilot has exactly 30 source records")
    return data,order


def source_integrity(original,submitted):
    if set(original)!=set(submitted):
        raise ValueError("Pilot reviewer changed or deleted original codes")
    for code in original:
        old=original[code]
        new=submitted[code]
        if old[:5]!=new[:5]:
            raise ValueError("Source title/abstract/year/type/code modified")
        if any(old[i] for i in EDITABLE):
            raise ValueError("Expected initially blank pilot codebook fields")
    return True


def readiness(frame):
    missing=Counter()
    for row in frame.values():
        for col,label in ((5,"scope"),(6,"relevance"),(7,"topic"),
                          (8,"discipline"),(10,"evidence"),
                          (11,"fulltext"),(12,"reason")):
            if not row[col]:
                missing[label]+=1
        if row[5] and row[5] not in SCOPE:
            raise ValueError("Invalid scope score")
        if row[6] and row[6] not in RELEVANCE:
            raise ValueError("Invalid relevance score")
        if row[7] and row[7] not in TOPICS:
            raise ValueError("Invalid primary topic")
        if row[8] and row[8] not in DISCIPLINES:
            raise ValueError("Invalid primary discipline")
        if row[11] and row[11] not in YESNO:
            raise ValueError("Invalid fulltext escalation score")
        if row[6] in {"2","3"} and not row[9]:
            missing["policy_mechanism_for_relevance2_3"]+=1
        if row[5]=="0" and row[6] and row[6]!="0":
            raise ValueError("Out-of-scope S0 requires R0")
        if row[5]=="9" and row[6] and row[6]!="9":
            raise ValueError("Uncertain scope S9 requires uncertain relevance R9")
        if row[5]=="1" and row[6]=="0":
            raise ValueError("In-scope S1 cannot have outside-scope relevance R0")
        if row[6]=="0" and row[5] and row[5]!="0":
            raise ValueError("R0 requires S0")
        if row[6]=="9" and row[11] and row[11]!="yes":
            raise ValueError("R9 must be referred for full text")
        if row[6]=="9" and row[5]=="0":
            raise ValueError("Uncertain R9 cannot have definitively out-of-scope S0")
    return dict(missing)


def kappa(a,b,labels,weights=None):
    from sklearn.metrics import cohen_kappa_score
    if not a:return None
    value=float(cohen_kappa_score(a,b,labels=labels,weights=weights))
    return round(value,5) if math.isfinite(value) else None


def agreement(a,b,categories,ordinal=False):
    n=len(a)
    out={
        "n":n,
        "exact_agreement_n":sum(x==y for x,y in zip(a,b)),
        "exact_agreement_fraction":round(sum(x==y for x,y in zip(a,b))/n,5),
        "distribution_A":dict(sorted(Counter(a).items())),
        "distribution_B":dict(sorted(Counter(b).items())),
    }
    if ordinal:
        paired=[(x,y) for x,y in zip(a,b) if x!="9" and y!="9"]
        out["evaluable_excluding_9"]=len(paired)
        out["excluded_as_uncertain9"]=n-len(paired)
        if paired:
            x,y=zip(*paired)
            out["kappa_unweighted_excluding_9"]=kappa(x,y,["0","1","2","3"])
            out["kappa_quadratic_excluding_9"]=kappa(
                x,y,["0","1","2","3"],"quadratic")
        else:
            out["kappa_unweighted_excluding_9"]=None
            out["kappa_quadratic_excluding_9"]=None
    else:
        out["kappa_nominal"]=kappa(a,b,sorted(categories))
    return out


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--original-a",default=str(
        Path.home()/"ai_policy_pilot28_blind_private/Piloto_V02_A.xlsx"))
    ap.add_argument("--original-b",default=str(
        Path.home()/"ai_policy_pilot28_blind_private/Piloto_V02_B.xlsx"))
    ap.add_argument("--returned-a",required=True)
    ap.add_argument("--returned-b",required=True)
    ap.add_argument("--manifest",default=str(
        Path.home()/"ai_policy_pilot28_blind_private/pilot_locked_manifest.json"))
    ap.add_argument("--codebook",default="docs/phase28_pilot_codebook_v0.2.md")
    ap.add_argument("--phase28-report",default="reports/phase28/pilot_preparation_aggregate.json")
    ap.add_argument("--out",default="reports/phase29")
    args=ap.parse_args()
    originals={k:Path(getattr(args,"original_"+k)).expanduser().resolve()
               for k in ("a","b")}
    returned={k:Path(getattr(args,"returned_"+k)).expanduser().resolve()
              for k in ("a","b")}
    manifest=json.loads(Path(args.manifest).read_text(encoding="utf8"))
    phase28=json.loads(Path(args.phase28_report).read_text(encoding="utf8"))
    if manifest.get("status")!="pilot_30_prepared_NO_human_ratings" or \
       phase28.get("pilot_size")!=30 or not phase28.get("distinct_from_prior_phase05_368"):
        raise ValueError("Authoritative Phase28 pilot source not found")
    if hashfile(Path(args.codebook))!=manifest["codebook_sha256"]:
        raise ValueError("Pilot rubric changed after book generation: cancel and investigate")
    out=Path(args.out).expanduser().resolve()
    for p in list(originals.values())+list(returned.values())+[Path(args.manifest).resolve()]:
        if not p.is_file() or out==p.parent or p.parent in out.parents:
            ap.error("Original and received private files must exist OUTSIDE the aggregate report folder")
    if out.exists() and any(out.iterdir()):
        ap.error("Output already contains a pilot report; do not overwrite without versioning")
    frames={}
    for rater in ("a","b"):
        if returned[rater]==originals[rater]:
            raise ValueError("Never edit the original blank form in place")
        if hashfile(originals[rater])!=manifest["reviewer_workbook_sha256"][rater.upper()]:
            raise ValueError("Original blank reviewer form checksum mismatch")
        pristine,old_order=readbook(originals[rater],rater.upper())
        candidate,new_order=readbook(returned[rater],rater.upper())
        if old_order!=new_order:
            raise ValueError("Reviewer changed pilot item row order")
        source_integrity(pristine,candidate)
        frames[rater]=candidate
    if set(frames["a"])!=set(frames["b"]):
        raise ValueError("Both independent pilot reviewers must rate identical cases")
    for case in frames["a"]:
        if frames["a"][case][:5]!=frames["b"][case][:5]:
            raise ValueError("A/B independent pilot original evidence mismatches")
    missing={who:readiness(records) for who,records in frames.items()}
    complete=not any(missing.values())
    results=None
    if complete:
        ids=sorted(frames["a"])
        results={}
        for name,col,categories,ordinal in (
            ("scope",5,SCOPE,False),("relevance",6,RELEVANCE,True),
            ("topic",7,TOPICS,False),("discipline",8,DISCIPLINES,False),
            ("fulltext_required",11,YESNO,False)):
            a=[frames["a"][key][col] for key in ids]
            b=[frames["b"][key][col] for key in ids]
            results[name]=agreement(a,b,categories,ordinal)
        results["rubric_calibration_threshold_75pct"]={
            "scope_at_least_75pct":results["scope"]["exact_agreement_fraction"]>=0.75,
            "relevance_at_least_75pct":results["relevance"]["exact_agreement_fraction"]>=0.75,
            "interpretation":"Initial pilot-calibration threshold only; never independently establishes truth or classifier validity."
        }
        results["relevance_cross_tab"]={
            a:{b:sum(frames["a"][i][6]==a and frames["b"][i][6]==b
                     for i in ids) for b in ["0","1","2","3","9"]}
            for a in ["0","1","2","3","9"]
        }
    obj={
        "created_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
        "status":("two_independent_pilot_rounds_scored_calibration_required"
                  if complete else "awaiting_completed_independent_pilot_review"),
        "pilot_n":30,
        "separate_rater_books_integrity_passed":True,
        "original_codebook_sha256_verified":True,
        "original_bibliographic_evidence_unchanged":True,
        "missing_or_invalid_required_fields":missing,
        "result":results,
        "limitations":[
            "The 30 records were deliberately stratified for calibration, not a probability sample for inference.",
            "This assesses inter-rater reproducibility, not how well the AI classifier predicts a human truth standard.",
            "No individual rating, publication title, abstract, full-text flag or private correspondence key is made public.",
            "An agreement threshold cannot replace codebook-vs-evidence review, correct handling of uncertain9 or independently validated full-text decisions.",
            "Codebook changes are not made automatically; document reasons and freeze version V1.0 before held-out sampling."
        ]
    }
    out.mkdir(parents=True)
    (out/"pilot_independent_agreement_aggregate.json").write_text(
        json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    (out/"summary.md").write_text(
        "# Phase29 — Independent calibration pilot scoring\n\n"
        "Status: "+obj["status"]+"\n\n"
        "### Aggregate inter-rater agreement (if both reviewers complete)\n\n"+
        json.dumps(results,indent=2,ensure_ascii=False)+"\n\n"
        "### Missing source ratings\n\n"+
        json.dumps(missing,indent=2)+"\n\n"+
        "\n".join("- "+x for x in obj["limitations"])+"\n",encoding="utf8")
    print("PHASE29",obj["status"])
    if results:
        for label in ("scope","relevance","topic","discipline"):
            print(label,"agreement:",results[label]["exact_agreement_n"],"/30")
        print("Threshold review:",results["rubric_calibration_threshold_75pct"])
    else:
        print("Incomplete reviewer fields. No agreement analysis or human data fabricated.")
    print("PUBLIC AGGREGATES:",out/"pilot_independent_agreement_aggregate.json")


if __name__=="__main__":
    main()
