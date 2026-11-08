#!/usr/bin/env python3
"""Phase32 — audit two PI-attributed HUMAN expert evaluations of full Phase30 sample.

Special provenance issue: returned workbooks are named IA-1/IA-2 and contain
two unchanged historic CLAUDE/AI provenance notices. The PI states these are
actual independent human expert evaluations using a recycled template.
Those claims are recorded as a PI attribution, not silently asserted as
verified fact. Require an explicit acknowledgment flag; preserve BOTH
unaltered originals, raw metadata, hashes, and identify the unresolved
independent-reviewer provenance issue for manuscript reporting.

Strictly check against frozen Phase30 blank books, codebook and manifest.
Emit aggregate inter-rater statistics and a PRIVATE discrepancy/adjudication
packet; NEVER reveal article sources, human ratings or linking keys in GitHub.
Never manufacture adjudications, classifier accuracy, precision or recall.
"""
from __future__ import annotations

import argparse
from collections import Counter
import datetime as dt
import hashlib
import importlib.util
import json
import math
from pathlib import Path

from sklearn.metrics import cohen_kappa_score, confusion_matrix

N=1200
DIMENSIONS={"scope":5,"relevance":6,"topic":7,"discipline":8,"fulltext_required":11}
ALLOW={
 5:{"0","1","9"},
 6:{"0","1","2","3","9"},
 7:{"teaching_learning","assessment","ethics_integrity",
    "governance_policy","research_scholarship","ai_literacy_training",
    "equity_access","privacy_security","general_policy",
    "not_applicable","uncertain"},
 8:{"ssh","engineering","health_sciences","general_he","uncertain"},
 11:{"yes","no"}
}
RELEVANCE=["0","1","2","3","9"]
EDITABLE=range(5,13)
FIELDS=[
 "validation_code","title","abstract","publication_year","type",
 "scope_a","scope_b","relevance_a","relevance_b",
 "topic_a","topic_b","discipline_a","discipline_b",
 "policy_mechanism_a","policy_mechanism_b",
 "evidence_a","evidence_b","fulltext_a","fulltext_b",
 "reason_a","reason_b","disagreement_fields",
 "panel_scope","panel_relevance","panel_topic",
 "panel_discipline","panel_evidence_reason","fulltext_escalation"
]
HEADERS=[
 "Código ciego","Título","Resumen","Año","Tipo",
 "Alcance A","Alcance B","Relevancia A","Relevancia B",
 "Tema A","Tema B","Disciplina A","Disciplina B",
 "Mecanismo A","Mecanismo B",
 "Evidencia A","Evidencia B",
 "Texto completo A","Texto completo B",
 "Justificación A","Justificación B","Dimensiones discrepantes",
 "DECISIÓN PANEL ALCANCE","DECISIÓN PANEL RELEVANCIA",
 "DECISIÓN PANEL TEMA","DECISIÓN PANEL DISCIPLINA",
 "JUSTIFICACIÓN DEL PANEL","SOLICITAR TEXTO COMPLETO (yes/no)"
]
PANEL_EDIT={22:["0","1","9"],23:["0","1","2","3","9"],
            24:sorted(ALLOW[7]),25:sorted(ALLOW[8]),26:None,27:["yes","no"]}
INTRO=[
 ["FASE 32","CONFLICTOS DE DOS EVALUACIONES ATRIBUIDAS A EXPERTOS HUMANOS; validación de 1200 registros"],
 ["PROCEDENCIA","Los archivos recibidos contienen etiquetas antiguas que afirman IA/Claude; el investigador principal confirma que son revisiones humanas. Conservar originales y declaraciones de autoría."],
 ["NO VALIDACIÓN TERCERA","Esta hoja de discrepancias NO constituye una tercera calificación ciega; es adjudicación posterior al conocimiento de A/B."],
 ["MÉTODO","Leer fuente, discrepancia, justificaciones separadas A/B. No decidir solo por mayoría ni preferir por defecto una persona."],
 ["DATOS PRIVADOS","No compartir con evaluadores originales durante su valoración. No subir XLSX, títulos, respuestas o códigos a GitHub."],
 ["RELEVANCIA","0 fuera de alcance, 1 IA universitaria sin política, 2 vínculo político indirecto sustentado, 3 política objeto central, 9 falta de evidencia."],
 ["INSTRUCCIÓN","Completar SOLO 6 columnas amarillas de panel cuando exista acuerdo científico documentado; conservar A/B originales."],
 ["TEXTOS COMPLETOS","Para 9 y decisiones relevantes ambiguas, solicitar artículo y documentar quién lo leyó, cuándo y qué evidencia lo resolvió."],
 ["SIN PILOTO","La validación fue evaluada directamente con 1200 registros sin piloto previo, por decisión del investigador principal."],
]
SCALES=[
 ["ESCALA","INTERPRETACIÓN"],
 ["0","Fuera de IA en educación superior"],["1","IA universitaria sin vínculo político"],
 ["2","Vínculo institucional indirecto con evidencia concreta"],
 ["3","Normativa o gobernanza objeto central"],
 ["9","Evidencia insuficiente y posible texto completo"]
]


def mod(file,alias):
    loc=Path(__file__).resolve().parent/file
    spec=importlib.util.spec_from_file_location(alias,loc)
    obj=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


def sha(path):
    d=hashlib.sha256()
    with path.open("rb") as fp:
        for part in iter(lambda:fp.read(1048576),b""):
            d.update(part)
    return d.hexdigest()


def readbook(path,headers,role):
    reader=mod("25_compare_independent_screening_qa.py","phase32_reader")
    tabs=reader.xlsx_sheets(path,{"INSTRUCCIONES","VALIDACION"})
    ins=tabs["INSTRUCCIONES"]
    if len(ins)<2:
        raise ValueError("Incomplete workbook instructions for "+role)
    first=str(ins[0].get(1,"")).strip()
    second=str(ins[1].get(1,"")).strip()
    raw=tabs["VALIDACION"]
    if not raw or [str(raw[0].get(j,"")).strip() for j in range(len(headers))]!=headers:
        raise ValueError("Changed Phase30 header structure for "+role)
    records={}
    order=[]
    for cells in raw[1:]:
        if not any(str(v).strip() for v in cells.values()):
            continue
        if any(j>=len(headers) and str(v).strip() for j,v in cells.items()):
            raise ValueError("Unexpected extra data columns in "+role)
        values=[str(cells.get(j,"")).strip() for j in range(len(headers))]
        key=values[0]
        if len(key)!=7 or not key.startswith("VAL") or not key[3:].isdigit():
            raise ValueError("Invalid source item ID in "+role)
        if key in records:
            raise ValueError("Duplicate source item ID in "+role)
        records[key]=values
        order.append(key)
    if len(records)!=N:
        raise ValueError(role+" must contain exactly 1200 source records")
    return {"records":records,"order":order,"first":first,"second":second}


def assert_rubric(record,role):
    for j,legal in ALLOW.items():
        if record[j] not in legal:
            raise ValueError(role+" has a missing or invalid rubric code in column "+str(j))
    for j in (10,12):
        if not record[j]:
            raise ValueError(role+" missing required source evidence or written rationale")
    s,r=record[5],record[6]
    if (s=="0" and r!="0" or s=="9" and r!="9" or
        s=="1" and r=="0" or r=="0" and s!="0"):
        raise ValueError("Scope and relevance inconsistent for "+role)
    if r in {"2","3"} and not record[9]:
        raise ValueError("Relevance 2/3 requires named institutional policy mechanism in "+role)
    if r=="9" and record[11]!="yes":
        raise ValueError("Uncertain relevance 9 requires full-text review flag in "+role)


def integrity(pristine,returned,role,allow_legacy):
    if set(pristine["records"])!=set(returned["records"]):
        raise ValueError("Returned labels do not map to 1200 frozen source records")
    if pristine["order"]!=returned["order"]:
        raise ValueError("Returned item order does not match reviewer-specific blank original")
    if not pristine["first"].startswith("Evaluador "+role):
        raise ValueError("Original blank book does not match expected expert reviewer")
    meta=returned["first"]+" "+returned["second"]
    legacy=("PASADA IA-"+("1" if role=="A" else "2") in meta and
            "Claude" in meta and "NO es una evaluación humana" in meta)
    if legacy and not allow_legacy:
        raise ValueError("Legacy AI/Claude metadata conflict detected. PI must explicitly acknowledge provenance issue")
    if not legacy and returned["first"]!=pristine["first"]:
        raise ValueError("Nonstandard returned-book identity and no recognized legacy metadata")
    for key,ref in pristine["records"].items():
        row=returned["records"][key]
        if row[:5]!=ref[:5]:
            raise ValueError("Original source code/title/abstract/year/type changed")
        if any(ref[j] for j in EDITABLE):
            raise ValueError("Original source book contained a nonempty purported human rating")
        assert_rubric(row,role)
    return {"legacy_AI_Claude_metadata_present":legacy,
            "original_sources_and_blank_rating_cells_verified":True,
            "all_1200_valid_ratings":True}


def agreement(a,b,name,j):
    pairs=[(a[x][j],b[x][j]) for x in sorted(a)]
    aa=[x for x,_ in pairs]; bb=[x for _,x in pairs]
    nmatch=sum(x==y for x,y in pairs)
    labels=sorted(set(aa)|set(bb))
    kappa=float(cohen_kappa_score(aa,bb,labels=labels))
    result={
       "n":N,
       "exact_agreement_n":nmatch,
       "disagreement_n":N-nmatch,
       "agreement_fraction":round(nmatch/N,6),
       "kappa_nominal_including_uncertain":round(kappa,6) if math.isfinite(kappa) else None,
       "distribution_A":dict(sorted(Counter(aa).items())),
       "distribution_B":dict(sorted(Counter(bb).items()))
    }
    if name=="relevance":
        kept=[(x,y) for x,y in pairs if x!="9" and y!="9"]
        xa=[x for x,_ in kept]; xb=[y for _,y in kept]
        result["jointly_ordinal_0_3_n"]=len(kept)
        result["excluded_if_any_uncertain_9_n"]=N-len(kept)
        for mode in (None,"quadratic"):
            k=(float(cohen_kappa_score(xa,xb,labels=["0","1","2","3"],
                                      weights=mode)) if kept else float("nan"))
            result["kappa_ordinal_"+("quadratic" if mode else "unweighted")]=(
                round(k,6) if math.isfinite(k) else None)
        result["relevance_crosstab_A_rows_B_cols_0_1_2_3_9"]=confusion_matrix(
            aa,bb,labels=["0","1","2","3","9"]).tolist()
    return result


def write_casebook(private,rows):
    excel=mod("17_excel_reviewer_packages.py","phase32_excel")
    pack=mod("18_prepare_blinded_adjudication_excel.py","phase32_pack")
    original=[{"group_code":r["validation_code"],**r} for r in rows]
    data=[
      ("INSTRUCCIONES",excel.basic_sheet(INTRO,[41,120])),
      ("DISCREPANCIAS",excel.section_xml("DOCUMENTOS",FIELDS,HEADERS,original,
        [15,52,99,13,18,17,17,19,19,21,21,20,20,72,72,80,80,22,22,80,80,25,25,28,24,24,88,30],
        PANEL_EDIT)),
      ("ESCALAS",excel.basic_sheet(SCALES,[34,110]))
    ]
    private.mkdir(parents=True,mode=0o700)
    private.chmod(0o700)
    target=private/"Adjudicacion_Validacion_1200_Humana.xlsx"
    pack.xlsx_generic(target,data,excel)
    return target


def main():
    p=argparse.ArgumentParser()
    root=Path.home()
    p.add_argument("--original-a",default=str(root/"ai_policy_validation1200_private/Validacion_1200_A.xlsx"))
    p.add_argument("--original-b",default=str(root/"ai_policy_validation1200_private/Validacion_1200_B.xlsx"))
    p.add_argument("--returned-a",required=True)
    p.add_argument("--returned-b",required=True)
    p.add_argument("--manifest",default=str(root/"ai_policy_validation1200_private/private_locked_manifest.json"))
    p.add_argument("--codebook",default="docs/phase30_full_validation_codebook_v1.0.md")
    p.add_argument("--phase30-report",default="reports/phase30/full_validation_packet_aggregate.json")
    p.add_argument("--private-out",default=str(root/"ai_policy_validation1200_human_discrepancies_private"))
    p.add_argument("--out",default="reports/phase32")
    p.add_argument("--acknowledge-legacy-ai-metadata",action="store_true",
                   help="PI confirms IA/Claude text is stale template metadata, says independent human experts performed ratings. This attribution is NOT automatically verified.")
    args=p.parse_args()
    paths={key:Path(value).expanduser().resolve() for key,value in {
       "original_a":args.original_a,"original_b":args.original_b,
       "returned_a":args.returned_a,"returned_b":args.returned_b,
       "manifest":args.manifest,"codebook":args.codebook}.items()}
    out=Path(args.out).expanduser().resolve()
    private=Path(args.private_out).expanduser().resolve()
    repo=root/"AI_policy"
    if len(set(map(str,paths.values())))!=len(paths):
        p.error("Do not overwrite source files or confuse reviewer A/B")
    if any(not path.is_file() for path in paths.values()):
        p.error("Missing source or returned book, frozen manifest or codebook")
    prohibited=[repo,paths["original_a"].parent,paths["returned_a"].parent,
                paths["returned_b"].parent]
    if any(private==d or d in private.parents or private in d.parents for d in prohibited):
        p.error("Private adjudication packet must be in a fresh protected folder OUTSIDE GitHub and both reviewer input folders")
    if any(out==d or d in out.parents or out in d.parents for d in (
       paths["original_a"].parent,paths["returned_a"].parent,
       paths["returned_b"].parent,private)):
        p.error("Aggregate output cannot be placed in or above source directories")
    if out.exists() and any(out.iterdir()):
        p.error("Public audit already exists. Do not overwrite")
    if private.exists() and any(private.iterdir()):
        p.error("Private adjudication packet already exists. Do not overwrite")
    manifest=json.loads(paths["manifest"].read_text(encoding="utf8"))
    report=json.loads(Path(args.phase30_report).read_text(encoding="utf8"))
    if (manifest.get("status")!="prepared_full1200_two_blind_expert_workbooks_NO_human_ratings" or
        report.get("sample_n")!=N or report.get("human_assessments_completed")!=0):
        raise ValueError("Frozen Phase30 source is not the original authorized 1200-sample package")
    if sha(paths["codebook"])!=manifest["codebook_sha256"]:
        raise ValueError("V1.0 codebook SHA256 changed")
    for r in ("A","B"):
        if sha(paths["original_"+r.lower()])!=manifest["pristine_workbook_sha256"][r]:
            raise ValueError("Original reviewer "+r+" template SHA256 changed")
    phase30=mod("30_prepare_full1200_validation.py","phase32_source")
    blank_a=readbook(paths["original_a"],phase30.HEADERS,"source A")
    blank_b=readbook(paths["original_b"],phase30.HEADERS,"source B")
    returned_a=readbook(paths["returned_a"],phase30.HEADERS,"returned A")
    returned_b=readbook(paths["returned_b"],phase30.HEADERS,"returned B")
    integrity_a=integrity(blank_a,returned_a,"A",args.acknowledge_legacy_ai_metadata)
    integrity_b=integrity(blank_b,returned_b,"B",args.acknowledge_legacy_ai_metadata)
    orig_a=blank_a["records"];orig_b=blank_b["records"]
    a=returned_a["records"];b=returned_b["records"]
    if set(orig_a)!=set(orig_b) or any(orig_a[k][:5]!=orig_b[k][:5] for k in orig_a):
        raise ValueError("Original reviewer A/B books are from different frozen samples")
    if set(a)!=set(b) or any(a[k][:5]!=b[k][:5] for k in a):
        raise ValueError("Returned reviewer A/B source evidence differs")

    result={name:agreement(a,b,name,idx) for name,idx in DIMENSIONS.items()}
    diffs=[]
    total={"records_with_any_disagreement":0,"relevance_uncertain_in_any_rating":0,
           "needs_full_text_in_any_rating":0}
    for key in sorted(a):
        v1,v2=a[key],b[key]
        disagree=[name for name,j in DIMENSIONS.items() if v1[j]!=v2[j]]
        if disagree:total["records_with_any_disagreement"]+=1
        uncertain=(v1[6]=="9" or v2[6]=="9")
        if uncertain:total["relevance_uncertain_in_any_rating"]+=1
        fulltext=(v1[11]=="yes" or v2[11]=="yes")
        if fulltext:total["needs_full_text_in_any_rating"]+=1
        if not (disagree or uncertain or fulltext):
            continue
        row={
          "validation_code":key,"title":v1[1],"abstract":v1[2],
          "publication_year":v1[3],"type":v1[4],
          "scope_a":v1[5],"scope_b":v2[5],
          "relevance_a":v1[6],"relevance_b":v2[6],
          "topic_a":v1[7],"topic_b":v2[7],
          "discipline_a":v1[8],"discipline_b":v2[8],
          "policy_mechanism_a":v1[9],"policy_mechanism_b":v2[9],
          "evidence_a":v1[10],"evidence_b":v2[10],
          "fulltext_a":v1[11],"fulltext_b":v2[11],
          "reason_a":v1[12],"reason_b":v2[12],
          "disagreement_fields":",".join(disagree) or ("uncertain" if uncertain else "fulltext"),
          "panel_scope":"","panel_relevance":"","panel_topic":"",
          "panel_discipline":"","panel_evidence_reason":"","fulltext_escalation":""
        }
        diffs.append(row)

    packet=write_casebook(private,diffs)
    response={
       "created_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
       "status":"PI_attributed_expert_ratings_scored_with_unresolved_legacy_AI_metadata_provenance",
       "sample_n":N,
       "original_phase30_source_integrity_verified":True,
       "label_rubric_v1_0_integrity_verified":True,
       "reviewer_attribution":{
          "PI_asserts_two_distinct_human_experts":True,
          "both_returned_files_preserve_legacy_AI_Claude_notice":all([
              integrity_a["legacy_AI_Claude_metadata_present"],
              integrity_b["legacy_AI_Claude_metadata_present"]]),
          "no_conclusion_of_human_authorship_from_file_metadata":True,
          "independent_human_authorship_documentation":"recommended_before_submitting_article",
          "file_provenance_resolution":"not_verified_by_automated_script"
       },
       "interrater_agreement_descriptive_as_PI_attributed":result,
       "review_priority_counts":total,
       "records_needing_adjudication_or_fulltext":len(diffs),
       "human_disagreements_adjudicated":0,
       "classifier_accuracy_calculated":False,
       "private_rater_forms_disclosed":False,
       "limitations":[
           "The returned Excel instructions expressly describe Claude AI classification. PI reports that this wording was leftover from a test and real human experts completed the assessments. The actual human provenance and independence are not verified by software.",
           "Obtain dated statements from both experts documenting authorship, procedure, absence or type of AI assistance, independent rating, conflict-of-interest disclosures and confirmation they used the frozen V1.0 rubric.",
           "The two original forms and the two returned forms are retained verbatim; do NOT erase or rewrite the conflicting instruction metadata.",
           "The same humans may have systematic misunderstandings; high inter-rater kappa is reproducibility, not necessarily correctness.",
           "No pre-rating pilot was conducted by explicit PI decision.",
           "This is descriptive raw agreement in a disproportionate probability-stratified sample; classifier performance needs machine-label correspondence, adjudicated human outcomes and design weights.",
           "The private disagreement file includes full article titles/abstracts and individual rater scores and MUST NOT be published."
       ]
    }
    out.mkdir(parents=True,exist_ok=True)
    (out/"human_expert_agreement_aggregate.json").write_text(
        json.dumps(response,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    lines=[
      "# Phase32 — PI-attributed new expert screening evaluation",
      "",
      "**Status:** "+response["status"],
      "",
      "**Source note:** Returned workbooks still describe Claude AI. The PI attests the labels are from two humans, but this cannot be verified computationally. Documentary resolution remains outstanding.",
      "",
      "## Descriptive paired results",
      json.dumps(result,ensure_ascii=False,indent=2),
      "",
      "## Discrepancy / full text counts",
      json.dumps({"priority":total,"records":len(diffs)},indent=2),
      "",
      "The full casebook and all human ratings remain PRIVATE on CEDIA, never in GitHub.",
      "",
      "## Methodological limits",
      *["- "+x for x in response["limitations"]],
    ]
    (out/"summary.md").write_text("\n".join(lines)+"\n",encoding="utf8")
    print("PHASE32",response["status"])
    print("1200 rows received from each PI-attributed expert. Old labels preserved.")
    for name in DIMENSIONS:
        info=result[name]
        print(name,info["exact_agreement_n"],"/",N,
              "kappa",info["kappa_nominal_including_uncertain"])
    print("Distinct cases needing arbitration or full text:",len(diffs))
    print("PRIVATE adjudication file:",packet)
    print("PUBLIC aggregate ONLY:",out/"human_expert_agreement_aggregate.json")
    print("WARNING: prior Claude/AI metadata remains; document real human provenance before journal submission.")
    print("No classifier accuracy or actual new human adjudications were invented.")


if __name__=="__main__":
    main()
