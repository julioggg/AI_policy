#!/usr/bin/env python3
"""Phase22 — PRIVATE blinded human screening adjudication workbook.

After two *real* independent Phase20/21 reviewer forms, prepares one private
XLSX for adjudicating ALL records with disagreement on relevance, discipline
or primary policy dimension. A and B labels are visible; original AI decisions,
strata, OpenAlex IDs and machine labels are NOT visible. No consensus values are
autofilled. Public reports contain counts only.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import importlib.util
import json
import os
from pathlib import Path

FIELDS = ("sample_id","title","abstract","publication_year","type",
          "relevance_code","discipline_code","primary_policy_code","reason")
SCORE_FIELDS = ("relevance_code","discipline_code","primary_policy_code")
GROUP_FIELDS = [
    "sample_id","title","abstract","publication_year","type",
    "relevance_a","relevance_b","discipline_a","discipline_b",
    "policy_a","policy_b","reason_a","reason_b",
    "final_relevance","final_discipline","final_policy","adjudication_reason"
]
HEADER = [
    "Código","Título","Resumen","Año","Tipo",
    "Relevancia A","Relevancia B","Disciplina A","Disciplina B",
    "Política A","Política B","Justificación A","Justificación B",
    "RELEVANCIA FINAL (0,1,2,3,9)","DISCIPLINA FINAL",
    "DIMENSIÓN FINAL","JUSTIFICACIÓN DEL CONSENSO"
]
EDITABLE = {
    13:["0","1","2","3","9"],
    14:["ssh","engineering","health_sciences","general_he","uncertain"],
    15:["teaching_learning","assessment","ethics_integrity",
        "governance_policy","research_scholarship","ai_literacy_training",
        "equity_access","privacy_security","general_policy",
        "not_applicable","uncertain"],
    16:None
}
ALL_FIELDS = ["sample_id","title","abstract","publication_year","type",
              "relevance_a","relevance_b","discipline_a","discipline_b",
              "policy_a","policy_b"]
ALL_HEADERS = [
    "Código","Título","Resumen","Año","Tipo",
    "Relevancia A","Relevancia B","Disciplina A","Disciplina B",
    "Política A","Política B"
]
SCALES = [
    ["CÓDIGO","SIGNIFICADO"],
    ["0","Fuera de IA en educación superior"],
    ["1","IA en educación superior sin dimensión política clara"],
    ["2","IA con implicaciones indirectas para políticas o gobernanza"],
    ["3","Estudia directamente política, regulación, normas o gobernanza de IA"],
    ["9","Título/resumen insuficiente, necesita consulta adicional"],
    ["ssh","Ciencias sociales y humanidades"],
    ["engineering","Ingeniería y tecnología"],
    ["health_sciences","Ciencias de la salud"],
    ["general_he","Educación superior general o interdisciplinar"],
    ["uncertain","No es posible determinar disciplina o dimensión"],
    ["teaching_learning","Enseñanza y aprendizaje"],
    ["assessment","Evaluación y calificaciones"],
    ["ethics_integrity","Ética e integridad académica"],
    ["governance_policy","Políticas, regulación y gobernanza"],
    ["research_scholarship","Investigación científica y tareas académicas"],
    ["ai_literacy_training","Alfabetización y formación en IA"],
    ["equity_access","Acceso y equidad"],
    ["privacy_security","Privacidad y seguridad"],
    ["general_policy","Otros aspectos generales de política"],
    ["not_applicable","No se identifica dimensión principal de política"],
]
INSTRUCTIONS = [
    ["ADJUDICACIÓN DEL CRIBADO","Protocolo de consenso basado en dos evaluaciones humanas ya completadas"],
    ["OBJETIVO","Resolver discrepancias de relevancia, disciplina o dimensión política en 316 publicaciones. No inventar consenso ni basarse solo en la mayoría."],
    ["ENMASCARAMIENTO","Se ven los dictámenes y justificaciones de A/B, pero NO las etiquetas automáticas, la identidad bibliográfica OpenAlex ni el estrato de muestreo."],
    ["PASO 1","Abra DISCREPANCIAS. Evalúe cada título y resumen; compare A/B y sus justificaciones."],
    ["PASO 2","Complete las cuatro celdas amarillas por fila: RELEVANCIA FINAL, DISCIPLINA FINAL, DIMENSIÓN FINAL y JUSTIFICACIÓN."],
    ["PASO 3","Puede confirmar el criterio de A, el de B o una tercera opción; escriba el razonamiento y, para casos 9, qué evidencia adicional sería necesaria."],
    ["PASO 4","Abra TODOS para consultar los 368 registros y comprobar consistencia conceptual de la clasificación; NO cambie esta hoja."],
    ["PASO 5","Diferencie AI in higher education, AI with indirect policy implications y DIRECT AI POLICY research. Una mera mención a ChatGPT NO implica política."],
    ["PASO 6","Disciplina y dimensión deben representar la contribución principal; documente ambigüedad interdisciplinaria cuando corresponda."],
    ["PASO 7","No edite nombres de pestañas, encabezados, códigos, títulos, resúmenes, respuestas A/B o el número de filas."],
    ["PASO 8","Guarde una COPIA COMPLETA del archivo .xlsx y devuélvala por vía privada al coordinador, sin subirla a GitHub."],
    ["NOTA METODOLÓGICA","La adjudicación NO es una tercera evaluación independiente. Se preservan los kappas originales."],
    ["NOTA MUESTRAL","La muestra está estratificada; no calcule proporciones globales de clasificación ni ajuste automáticamente las etiquetas de estratos excluidos."],
    ["NOTA ÉTICA","Los registros y calificaciones son privados para el manuscrito; no enviar a repositorios públicos."]
]


def load_module(filename,name):
    file=Path(__file__).resolve().parent/filename
    spec=importlib.util.spec_from_file_location(name,file)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def csv_read(path):
    with path.open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        if not set(FIELDS).issubset(reader.fieldnames or []):
            raise ValueError("Normalized reviewer CSV lacks expected fields")
        records=list(reader)
    if len(records)!=368:
        raise ValueError("Expected 368 independent human-coded publications")
    if len({x["sample_id"] for x in records})!=368 or \
       any(not x["sample_id"] for x in records):
        raise ValueError("Missing or duplicated sampled records")
    if any(any(not r[f].strip() for f in SCORE_FIELDS+("reason",))
           for r in records):
        raise ValueError("Both human reviewer CSVs must be fully completed")
    return {x["sample_id"]:x for x in records}


def build(normalized):
    a=csv_read(normalized/"rater_a.csv")
    b=csv_read(normalized/"rater_b.csv")
    if set(a)!=set(b):
        raise ValueError("A/B sample key sets disagree")
    samples=[]
    disputes=[]
    counts={"relevance":0,"discipline":0,"policy":0,"unique":0,
            "original_no_disagreement":0}
    for id in sorted(a):
        x=a[id]; y=b[id]
        for field in FIELDS[:5]:
            if x[field]!=y[field]:
                raise ValueError("Human rater evidence was modified")
        row={
            "sample_id":id,"title":x["title"],"abstract":x["abstract"],
            "publication_year":x["publication_year"],"type":x["type"],
            "relevance_a":x["relevance_code"],"relevance_b":y["relevance_code"],
            "discipline_a":x["discipline_code"],"discipline_b":y["discipline_code"],
            "policy_a":x["primary_policy_code"],"policy_b":y["primary_policy_code"],
            "reason_a":x["reason"],"reason_b":y["reason"],
            "final_relevance":"","final_discipline":"","final_policy":"",
            "adjudication_reason":""
        }
        samples.append(row)
        disagree=tuple(x[f]!=y[f] for f in SCORE_FIELDS)
        for label,v in zip(("relevance","discipline","policy"),disagree):
            counts[label]+=int(v)
        if any(disagree):
            disputes.append(row)
            counts["unique"]+=1
        else:
            counts["original_no_disagreement"]+=1
    return samples,disputes,counts


def public_write(out,stats):
    out.mkdir(parents=True,exist_ok=True)
    obj={
        "created_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
        "status":"screening_adjudication_packet_prepared_consensus_pending",
        "sample_n":368,
        "counts":stats,
        "adjudication_fields_required_per_disputed_record":4,
        "consensus_values_prepopulated":False,
        "privacy":"Blinded book is in CEDIA private folder only; no individual texts, scores or IDs in GitHub.",
        "limitations":[
            "Adjudication is NOT a third independent expert coding round.",
            "No machine labels or sample stratum may be shown before consensus.",
            "Only the 316 records in at least one A/B disagreement are routed to adjudication; unanimous ratings of 52 records stay as independent concordant opinions.",
            "9=uncertain may remain after adjudication; titles/abstracts do not necessarily resolve true inclusion.",
            "Screening error rates require a later design-based, per-stratum analysis with source eligibility logic; early bibliographic-filter exclusions are not classifier negatives."
        ]}
    (out/"screening_adjudication_packet_aggregate.json").write_text(
        json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    lines=["# Phase 22 — Private human screening adjudication packet","",
           "Status: "+obj["status"],"UTC: "+obj["created_utc"],"",
           "## Public counts",json.dumps(stats,indent=2),"",
           "Human consensus decisions remain pending. Private XLSX is NOT committed.",
           "","## Caveats"]+["- "+x for x in obj["limitations"]]
    (out/"summary.md").write_text("\n".join(lines)+"\n",encoding="utf8")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--private-in",default=str(
        Path.home()/"ai_policy_screening_calificaciones_normalizadas_privado"))
    p.add_argument("--private-out",default=str(
        Path.home()/"ai_policy_screening_adjudicacion_privado"))
    p.add_argument("--out",default="reports/phase22")
    p.add_argument("--phase21-report",default="reports/phase21/human_screening_agreement_aggregate.json")
    args=p.parse_args()
    source=Path(args.private_in).expanduser().resolve()
    target=Path(args.private_out).expanduser().resolve()
    public=Path(args.out).expanduser().resolve()
    repo=Path.home()/"AI_policy"
    if not source.is_dir() or not (source/"sampling_key.csv").is_file():
        p.error("Private Phase20 imported rating directory or key missing")
    if repo==target or repo in target.parents or target==source or \
       source in target.parents or target in source.parents or \
       target==public or target in public.parents or public in target.parents:
        p.error("Never write private adjudication XLSX inside GitHub or reviewer inputs")
    if target.exists() and any(target.iterdir()):
        p.error("Use an empty private adjudication destination to preserve any earlier work")
    samples,disputes,counts=build(source)
    data=json.loads(Path(args.phase21_report).read_text(encoding="utf8"))
    if data.get("status")!="complete_independent_ratings_not_yet_adjudicated":
        raise ValueError("Phase21 must have two complete real independent reviews")
    published=data.get("results",{}).get("flagged_for_human_adjudication",{})
    expected={
       "relevance":published.get("any_relevance_disagreement"),
       "discipline":published.get("any_discipline_disagreement"),
       "policy":published.get("any_policy_dimension_disagreement"),
       "unique":published.get("unique_records_disagreeing_in_one_or_more_fields")
    }
    if any(counts[k]!=v for k,v in expected.items()):
        raise ValueError("Private Phase20 rating CSVs do not match published Phase21 audit")
    excel=load_module("17_excel_reviewer_packages.py","excel_phase22")
    helper=load_module("18_prepare_blinded_adjudication_excel.py","pack_phase22")
    def sheet(records,fields,header,widths,edits):
        # Phase17's colored-column renderer expects a blinded group code;
        # the extra property is never written to the displayed 17 columns.
        rendered=[{"group_code":row["sample_id"],**row} for row in records]
        return excel.section_xml("DOCUMENTOS",fields,header,rendered,widths,edits)
    tabs=[
        ("INSTRUCCIONES",excel.basic_sheet(INSTRUCTIONS,[33,111])),
        ("DISCREPANCIAS",sheet(disputes,GROUP_FIELDS,HEADER,
         [14,43,78,13,18,15,15,21,21,22,22,59,59,27,30,35,63],
         EDITABLE)),
        ("TODOS",sheet(samples,ALL_FIELDS,ALL_HEADERS,
         [14,44,91,13,18,17,17,21,21,20,20],{})),
        ("ESCALAS",excel.basic_sheet(SCALES,[32,117]))
    ]
    target.mkdir(parents=True,mode=0o700)
    os.chmod(target,0o700)
    outfile=target/"Adjudicacion_Cribado_Fase22.xlsx"
    helper.xlsx_generic(outfile,tabs,excel)
    public_write(public,counts)
    print("PHASE22 private adjudication workbook prepared — NO consensus fabricated")
    print("Disputed records:",counts["unique"],"of 368")
    print("Relevance:",counts["relevance"],"Discipline:",counts["discipline"],
          "Policy:",counts["policy"])
    print("PRIVATE XLSX:",outfile)
    print("Aggregate public report:",public/"summary.md")
    print("Never upload the private adjudication workbook to GitHub")


if __name__=="__main__":
    main()
