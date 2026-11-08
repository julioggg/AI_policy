#!/usr/bin/env python3
"""Phase24 — PRIVATELY select an independent blinded QA audit of Phase23 human consensus.

Risk-enriched reproducible sample (nominal 80 cases); it is NOT a probability
validation study and must never be used for pooled sensitivity/accuracy.
The reviewer sees only original bibliographic source + blank rubric categories;
NOT A/B ratings, machine decisions, stratum, previous adjudication, sampled
risk reason or Phase05 sample codes. A protected key preserves correspondence.
This script does not fabricate any human review; no case-level data on GitHub.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import datetime as dt
import importlib.util
import json
import os
from pathlib import Path
import random

FIELDS=["qa_code","title","abstract","publication_year","type",
        "relevance_code","discipline_code","primary_policy_code","reason"]
HEADERS=["Código QA","Título","Resumen","Año","Tipo",
         "Relevancia independiente (0,1,2,3,9)",
         "Disciplina independiente",
         "Dimensión principal de política","Justificación científica"]
EDITS={
 5:["0","1","2","3","9"],
 6:["ssh","engineering","health_sciences","general_he","uncertain"],
 7:["teaching_learning","assessment","ethics_integrity","governance_policy",
    "research_scholarship","ai_literacy_training","equity_access",
    "privacy_security","general_policy","not_applicable","uncertain"],
 8:None
}
INTRO=[
  ["CONTROL DE CALIDAD INDEPENDIENTE","Auditoría ciega de concordancia del cribado humano"],
  ["PROPÓSITO","Reevaluar de manera INDEPENDIENTE una muestra enriquecida por incertidumbre y discordancia previa; no reemplaza el análisis estratificado original."],
  ["ENMASCARAMIENTO","Esta planilla NO revela: selección automática, muestras/estratos, decisiones de A/B o del adjudicador, ni razón de selección de cada publicación."],
  ["PASO 1","Lea título y resumen; decida con base en la evidencia textual disponible y en la rúbrica."],
  ["PASO 2","Complete SOLO las 4 columnas amarillas de CONTROL_QA para cada registro; cada decisión debe acompañarse de una justificación específica, no plantilla genérica."],
  ["PASO 3","Relevancia 0 fuera del campo IA/educación superior, 1 IA/educación superior sin política comprobada, 2 implicación indirecta, 3 estudio directo de gobernanza o política, 9 insuficiente información."],
  ["PASO 4","Categorice la disciplina y dimensión política principal; no infiera política por mencionar ChatGPT ni por recomendaciones educativas genéricas."],
  ["PASO 5","En duda, use 9 en relevancia, y explique si requiere texto completo o aclaración del contexto; no invente datos."],
  ["PASO 6","No consulte clasificaciones anteriores ni otro evaluador, no cambie encabezados, códigos, títulos, resúmenes ni filas."],
  ["PASO 7","Devuelva el mismo XLSX por canal privado y sin exponer artículos o respuestas a repositorios públicos."],
  ["NO INFERENCIA","La selección es un muestreo dirigido de control de calidad (80 casos), no representativo. No informe tasas globales de precisión o prevalencia."],
]
RUBRIC=[
 ["CÓDIGO","DEFINICIÓN"],
 ["0","Fuera de IA en educación superior"],
 ["1","IA en educación superior sin relación política claramente sustentada"],
 ["2","Relevancia indirecta para políticas, normas o gobernanza"],
 ["3","Investigación directamente centrada en políticas, reglas o gobernanza de IA"],
 ["9","Evidencia insuficiente para juicio de relevancia"],
 ["ssh","Ciencias sociales y humanidades"],
 ["engineering","Ingeniería y tecnología"],
 ["health_sciences","Ciencias de la salud"],
 ["general_he","Educación superior general"],
 ["uncertain","No clasificable desde título/resumen"],
 ["teaching_learning","Enseñanza y aprendizaje"],
 ["assessment","Evaluación y calificaciones"],
 ["ethics_integrity","Ética e integridad"],
 ["governance_policy","Gobernanza y políticas"],
 ["research_scholarship","Investigación académica"],
 ["ai_literacy_training","Capacitación y alfabetización en IA"],
 ["equity_access","Acceso y equidad"],
 ["privacy_security","Privacidad y seguridad"],
 ["general_policy","Política general"],
 ["not_applicable","No aplica"],
]

def module(file,tag):
    loc=Path(__file__).resolve().parent/file
    spec=importlib.util.spec_from_file_location(tag,loc)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def write_private_csv(path,rows,fields):
    with path.open("w",newline="",encoding="utf-8-sig") as f:
        writer=csv.DictWriter(f,fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    os.chmod(path,0o600)

def select(records,disputed,consensus,keys,seed,n=80):
    rng=random.Random(seed)
    allids=sorted(records)
    chooses={}
    quotas=[
        ("unresolved_relevance_9",13,lambda k:consensus[k][0]=="9"),
        ("reviewer_B_relevance_on_disagreement",12,
            lambda k:k in disputed and disputed[k][5]!=disputed[k][6]
            and disputed[k][13]==disputed[k][6]),
        ("reviewer_B_discipline_on_disagreement",15,
            lambda k:k in disputed and disputed[k][7]!=disputed[k][8]
            and disputed[k][14]==disputed[k][8]),
        ("reviewer_B_policy_on_disagreement",15,
            lambda k:k in disputed and disputed[k][9]!=disputed[k][10]
            and disputed[k][15]==disputed[k][10]),
        ("include_policy_but_consensus_relevance_1",15,
            lambda k:keys[k]["stratum"]=="screen_include_policy"
            and consensus[k][0]=="1"),
        ("direct_policy_relevance_3",5,lambda k:consensus[k][0]=="3"),
    ]
    for reason,quota,predicate in quotas:
        candidates=[k for k in allids if k not in chooses and predicate(k)]
        rng.shuffle(candidates)
        for k in candidates[:quota]:
            chooses[k]=reason
    remaining=[k for k in allids if k not in chooses]
    rng.shuffle(remaining)
    if len(chooses)>n:
        raise ValueError("Risk quota exceeds sample size")
    for k in remaining[:n-len(chooses)]:
        chooses[k]="random_safety_fill"
    if len(chooses)!=n:
        raise ValueError("Insufficient original records for QA sample")
    selected=list(chooses)
    rng.shuffle(selected)
    return [(k,chooses[k]) for k in selected]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--original-xlsx",default=str(
        Path.home()/"ai_policy_screening_adjudicacion_privado/Adjudicacion_Cribado_Fase22.xlsx"))
    ap.add_argument("--completed-xlsx",default=str(
        Path.home()/"ai_policy_screening_adjudicacion_recibida_privado/Adjudicacion_Cribado_Fase22_COMPLETADA.xlsx"))
    ap.add_argument("--private-in",default=str(
        Path.home()/"ai_policy_screening_calificaciones_normalizadas_privado"))
    ap.add_argument("--phase05-report",default="reports/phase05/sample_aggregate.json")
    ap.add_argument("--phase22-report",default="reports/phase22/screening_adjudication_packet_aggregate.json")
    ap.add_argument("--phase23-report",default="reports/phase23/adjudicated_screening_aggregate.json")
    ap.add_argument("--private-out",default=str(
        Path.home()/"ai_policy_screening_qa_independent_privado"))
    ap.add_argument("--out",default="reports/phase24")
    ap.add_argument("--seed",type=int,default=20261108)
    args=ap.parse_args()
    original=Path(args.original_xlsx).expanduser().resolve()
    completed=Path(args.completed_xlsx).expanduser().resolve()
    private=Path(args.private_in).expanduser().resolve()
    target=Path(args.private_out).expanduser().resolve()
    out=Path(args.out).expanduser().resolve()
    repo=Path.home()/"AI_policy"
    if target==out or target in out.parents or out in target.parents or \
       target==repo or repo in target.parents or \
       target==private or private in target.parents or target in private.parents:
        ap.error("QA workbook and matching key must stay OUTSIDE GitHub and source folders")
    if target.exists() and any(target.iterdir()):
        ap.error("QA private folder already has files; do not overwrite previous review")
    p23=json.loads(Path(args.phase23_report).read_text(encoding="utf8"))
    if p23.get("status")!="completed_human_screening_adjudication_aggregate_QA_pending":
        raise ValueError("Phase23 completed adjudication report missing")
    p22=json.loads(Path(args.phase22_report).read_text(encoding="utf8"))
    p05=json.loads(Path(args.phase05_report).read_text(encoding="utf8"))
    phase23=module("23_analyze_adjudicated_screening.py","phase23_private_qa")
    helper=phase23.excel_helper()
    base=phase23.sheet_data(original,helper)
    returned=phase23.sheet_data(completed,helper)
    reviewers=phase23.read_original_raters(private)
    keys=phase23.read_private_key(private,p05)
    allrows,disputes,counts=phase23.validate_workbooks(base,returned,reviewers,p22)
    readiness,complete=phase23.readiness(disputes)
    if not complete:
        raise ValueError("No QA allowed before human adjudication is complete")
    consensus,source_counts=phase23.assigned_consensus(allrows,disputes)
    if p23["integrity"]["counts"]!=counts:
        raise ValueError("Phase23 report no longer matches original blinded review counts")
    selected=select(allrows,disputes,consensus,keys,args.seed)
    records=[]
    private_index=[]
    for i,(sample_id,reason) in enumerate(selected,1):
        qa_code=f"Q{i:04d}"
        source=allrows[sample_id]
        records.append({
            "qa_code":qa_code,"title":source[1],"abstract":source[2],
            "publication_year":source[3],"type":source[4],
            "relevance_code":"","discipline_code":"","primary_policy_code":"",
            "reason":""
        })
        private_index.append({
            "qa_code":qa_code,"sample_id":sample_id,
            "selection_reason":reason,
            "stratum":keys[sample_id]["stratum"],
            "consensus_relevance":consensus[sample_id][0],
            "consensus_discipline":consensus[sample_id][1],
            "consensus_policy":consensus[sample_id][2],
        })
    excel=module("17_excel_reviewer_packages.py","excel_phase24")
    pack=module("18_prepare_blinded_adjudication_excel.py","pack_phase24")
    tagged=[{"group_code":r["qa_code"],**r} for r in records]
    tabs=[
       ("INSTRUCCIONES",excel.basic_sheet(INTRO,[38,112])),
       ("CONTROL_QA",excel.section_xml("DOCUMENTOS",FIELDS,HEADERS,tagged,
           [17,47,106,14,20,30,28,33,78],EDITS)),
       ("ESCALAS",excel.basic_sheet(RUBRIC,[33,110]))
    ]
    target.mkdir(parents=True,mode=0o700)
    os.chmod(target,0o700)
    file=target/"Control_Independiente_Cribado_Fase24.xlsx"
    pack.xlsx_generic(file,tabs,excel)
    write_private_csv(target/"correspondencia_qa_privada.csv",private_index,
        list(private_index[0]))
    report={
        "created_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
        "status":"private_blinded_quality_audit_packet_prepared_human_QA_pending",
        "input_integrity":"passed_original_Phase22_Phase23_and_private_key",
        "random_seed":args.seed,
        "review_sample_n":len(selected),
        "sample_type":"deliberately_risk_enriched_NOT_population_representative",
        "source_phase23_consensus_n":len(consensus),
        "selection_channel_counts":dict(sorted(Counter(r["selection_reason"] for r in private_index).items())),
        "privacy":"No individual records or private mapping exported to GitHub",
        "limitations":[
            "No independent QA ratings are yet available; the workbook is blank.",
            "Selection is intentionally enriched for uncertain/rater-B-dominant/policy-sensitive strata.",
            "The third independent QA coder must not see earlier A/B scores, consensus, sample strata, or model labels before rating.",
            "This is a procedural and taxonomy quality check, not a random validation sample for estimating corpus performance.",
            "The Phase23 weighted estimates remain conditional and should be reassessed if the QA review detects systematic consensus problems."
        ]
    }
    out.mkdir(parents=True,exist_ok=True)
    (out/"quality_audit_packet_aggregate.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    (out/"summary.md").write_text(
        "# Phase24 — Independent blinded QA audit of screening consensus\n\n"+
        "Status: "+report["status"]+"\n\n"+
        "Risk-enriched sample: "+str(len(selected))+" records.\n\n"+
        "Selection channel counts:\n"+
        json.dumps(report["selection_channel_counts"],indent=2)+"\n\n"+
        "The private QA Excel and mapping key remain outside GitHub; no human QA has yet occurred.\n\n"+
        "## Limitations\n"+"\n".join("- "+x for x in report["limitations"])+"\n",encoding="utf8")
    print("PHASE24",report["status"])
    print("Independent QA cases:",len(selected))
    print("PRIVATE reviewer workbook:",file)
    print("PRIVATE mapping key:",target/"correspondencia_qa_privada.csv")
    print("PUBLIC counts only:",out/"summary.md")
    print("No human QA scores invented, and no previous labels included in reviewer workbook.")


if __name__=="__main__":
    main()
