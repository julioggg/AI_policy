#!/usr/bin/env python3
"""Phase30 — FULL prospective 1,200-record dual independent screening sample.

NO 30-record pilot. Frozen, new codebook V1.0 for two new qualified experts.
Samples WITHOUT replacement inside all four original final-screening strata:
core 800/9264, policy 290/899, context 92/102, exclude census 18/18.
Does NOT exclude historical Phase05 records, preserving probability coverage.
Neither A/B workbook reveals prior labels, sampling strata, model decisions,
IDs, classifications nor corresponding machine outputs.
Private labels and articles NEVER enter GitHub.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import shutil

SAMPLE={"screen_include_core":("include_core",800,9264),
        "screen_include_policy":("include_policy",290,899),
        "screen_include_context":("include_context",92,102),
        "screen_exclude":("exclude",18,18)}
TOTAL=1200
FRAME=10283

FIELDS=[
    "validation_code","title","abstract","publication_year","type",
    "scope_code","relevance_code","primary_topic","primary_discipline",
    "policy_mechanism","evidence_excerpt","fulltext_required","reason"
]
HEADERS=[
    "Código de validación","Título","Resumen","Año","Tipo",
    "ALCANCE S (0,1,9)","POLÍTICA R (0,1,2,3,9)",
    "TEMA PRINCIPAL","DISCIPLINA PRINCIPAL",
    "MECANISMO NORMATIVO PARA R2/3",
    "EVIDENCIA DEL TÍTULO/RESUMEN",
    "REQUIERE TEXTO COMPLETO (yes/no)","JUSTIFICACIÓN CIENTÍFICA"
]
TOPIC=[
    "teaching_learning","assessment","ethics_integrity",
    "governance_policy","research_scholarship","ai_literacy_training",
    "equity_access","privacy_security","general_policy",
    "not_applicable","uncertain"
]
DISCIPLINE=["ssh","engineering","health_sciences","general_he","uncertain"]
EDIT={5:["0","1","9"],6:["0","1","2","3","9"],
      7:TOPIC,8:DISCIPLINE,9:None,10:None,11:["yes","no"],12:None}
INSTRUCTIONS=[
 ["EVALUADOR ASIGNADO","Evaluador {RATER} — validación completa V1.0, 1.200 registros"],
 ["ESTUDIO","Nueva validación humana prospectiva e independiente. Sin piloto, por decisión del investigador principal."],
 ["RÚBRICA","Leer primero Rubrica_Validacion_V1.md; la misma versión se aplica a TODOS los registros."],
 ["INDEPENDENCIA","No consulte al otro experto, anteriores evaluaciones, IA, estrato, archivos de correspondencia ni etiquetas automáticas."],
 ["PASO 1","Abra VALIDACION, lea título y resumen. Complete ALCANCE S=0/1/9."],
 ["PASO 2","Marque RELEVANCIA R=0/1/2/3/9 según la rúbrica: R2 vínculo específico indirecto, R3 normas/políticas como objeto central."],
 ["PASO 3","Asigne tema y disciplina principal sin inferir relevancia política a partir del tema."],
 ["PASO 4","Para R2/R3 describa en MECANISMO la norma o decisión institucional concreta y registre evidencia."],
 ["PASO 5","Para todas las filas complete EVIDENCIA concreta del título/resumen y JUSTIFICACIÓN específica."],
 ["PASO 6","R9 exige REQUIERE TEXTO COMPLETO=yes. No invente contenido no presente en resumen."],
 ["PASO 7","S0 exige R0. S9 exige R9. S1 admite R1/R2/R3/R9, pero nunca R0."],
 ["PASO 8","Edite solamente ocho columnas amarillas F–M, no títulos, códigos, encabezados, orden ni hojas."],
 ["PASO 9","Cada revisor completará el libro de manera independiente, sin que ChatGPT u otra IA emita etiquetas humanas."],
 ["ENTREGA","Devuelva el mismo Excel privadamente; no compartan evaluaciones antes del cierre de ambos libros."],
 ["PRIVACIDAD","NO subir Excel a GitHub ni a repositorios públicos. No mostrar ni solicitar clave del modelo."],
 ["NOTA","La selección es estratificada; NO calcular precisión como proporción no ponderada de 1.200 casos."],
]
SCALES=[
 ["ESCALA","DEFINICIÓN"],
 ["S0","Fuera de IA en educación superior"],["S1","Dentro de IA en educación superior"],
 ["S9","Información insuficiente para alcance"],
 ["R0","No investiga IA en educación superior"],["R1","IA universitaria sin relevancia política sustentada"],
 ["R2","Implicación institucional/normativa indirecta y ESPECÍFICA, sustentada"],
 ["R3","Norma, gobernanza, regulación o política es objeto CENTRAL del estudio"],
 ["R9","Evidencia insuficiente; requiere texto completo, NO es una clase negativa"],
 ["POLICY MECHANISM","Obligatorio para R2/3: norma, protocolo, regla o decisión institucional concreta"],
 ["EVIDENCE","Justificar con evidencia de título/resumen, no con conjeturas"],
 ["TEMA","ethics_integrity, assessment o teaching_learning por sí solos NO implican R2/R3"],
]
SCALES.extend([[s,s.replace("_"," ")] for s in TOPIC+DISCIPLINE])


def mod(name,alias):
    p=Path(__file__).resolve().parent/name
    spec=importlib.util.spec_from_file_location(alias,p)
    obj=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as fp:
        for block in iter(lambda:fp.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()


def csvread(path):
    with path.open("r",newline="",encoding="utf-8-sig") as fp:
        return list(csv.DictReader(fp))


def csvwrite(path,headers,rows):
    with path.open("w",newline="",encoding="utf-8-sig") as fp:
        writer=csv.DictWriter(fp,fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    path.chmod(0o600)


def safe(value):
    if value is None:return ""
    v=str(value).replace("\x00","").strip()
    if v.lower() in ("nan","none","nat"):return ""
    return "'"+v if v.startswith(("=","+","-","@")) else v


def source_data(path,fmt):
    if fmt=="csv":
        data=csvread(path)
    else:
        import pandas as pd
        import pyarrow.parquet as pq
        available=set(pq.ParquetFile(path).schema_arrow.names)
        mandatory={"openalex_id","title","abstract","ai_decision"}
        if not mandatory.issubset(available):
            raise ValueError("Source parquet lacks scientific screening evidence")
        requested=[c for c in ("openalex_id","title","abstract","publication_year","type","ai_decision")
                   if c in available]
        df=pd.read_parquet(path,columns=requested)
        data=df.where(pd.notnull(df),"").to_dict("records")
    required={"openalex_id","title","abstract","ai_decision"}
    if any(not required.issubset(r) for r in data):
        raise ValueError("Source must contain OpenAlex ID, title, abstract and frozen AI decision")
    frame={}
    for row in data:
        key=str(row["openalex_id"]).strip()
        if not key or key.lower()=="nan":
            continue
        if key in frame:
            raise ValueError("Duplicate source ID in final-screening frame: frame must be auditable")
        frame[key]=row
    return frame


def check_frame(frame,phase05,old_key):
    if len(frame)!=FRAME:
        raise ValueError("Final AI-screening population no longer has 10,283 distinct records")
    by_decision=Counter(str(r["ai_decision"]).strip().lower() for r in frame.values())
    for stratum,(decision,n,N) in SAMPLE.items():
        if by_decision[decision]!=N or int(phase05["strata"][stratum]["population_n"])!=N:
            raise ValueError("Frozen CEDIA stratum size differs from validated Phase05")
    if set(by_decision)!=set(v[0] for v in SAMPLE.values()):
        raise ValueError("Unknown or missing machine screening label in frozen input")
    if int(phase05.get("sample_size",-1))!=368:
        raise ValueError("Historical Phase05 368-case sample report missing")
    historical=csvread(old_key)
    if len(historical)!=368 or len(set(x["openalex_id"] for x in historical))!=368:
        raise ValueError("Historical private key is not the original 368 unique records")
    fingerprint=hashlib.sha256(
        "\n".join(sorted(x["openalex_id"] for x in historical)).encode("utf8")
    ).hexdigest()
    if fingerprint!=phase05.get("id_set_sha256"):
        raise ValueError("Historical Phase05 sample key checksum changed")
    return set(x["openalex_id"] for x in historical)


def select(frame,seed):
    rng=random.Random(seed)
    selected=[]
    for stratum,(decision,n,N) in SAMPLE.items():
        keys=sorted(k for k,row in frame.items()
                    if str(row["ai_decision"]).strip().lower()==decision)
        if len(keys)!=N:
            raise ValueError("Incorrect stratum size for "+stratum)
        chosen=keys if n==N else rng.sample(keys,n)
        selected.extend((stratum,key) for key in chosen)
    if len(selected)!=TOTAL or len({id for _,id in selected})!=TOTAL:
        raise ValueError("Sample is incomplete or contains duplicate publication IDs")
    rng.shuffle(selected)
    return selected


def workbook(dest,reviewer,records):
    excel=mod("17_excel_reviewer_packages.py","full30_excel")
    pack=mod("18_prepare_blinded_adjudication_excel.py","full30_xlsx")
    ins=[[k,v.replace("{RATER}",reviewer)] for k,v in INSTRUCTIONS]
    tabs=[
        ("INSTRUCCIONES",excel.basic_sheet(ins,[37,122])),
        ("VALIDACION",excel.section_xml("DOCUMENTOS",FIELDS,HEADERS,
             [{"group_code":r["validation_code"],**r} for r in records],
             [18,56,103,14,21,22,24,32,28,74,89,25,80],EDIT)),
        ("ESCALAS",excel.basic_sheet(SCALES,[32,115]))
    ]
    pack.xlsx_generic(dest,tabs,excel)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--project",default=str(Path.home()/"ai_policy_he"))
    p.add_argument("--source-frame")
    p.add_argument("--source-format",choices=("parquet","csv"),default="parquet")
    p.add_argument("--phase05-key",default=str(
        Path.home()/"ai_policy_validation_private/sampling_key.csv"))
    p.add_argument("--phase05-report",default="reports/phase05/sample_aggregate.json")
    p.add_argument("--codebook",default="docs/phase30_full_validation_codebook_v1.0.md")
    p.add_argument("--private-out",default=str(Path.home()/"ai_policy_validation1200_private"))
    p.add_argument("--out",default="reports/phase30")
    p.add_argument("--seed",type=int,default=20261108)
    args=p.parse_args()
    root=Path(args.project).expanduser().resolve()
    source=(Path(args.source_frame).expanduser().resolve() if args.source_frame else
            root/"data/processed/ai_assisted_screening_decisions.parquet")
    original=Path(args.phase05_key).expanduser().resolve()
    codebook=Path(args.codebook).expanduser().resolve()
    dest=Path(args.private_out).expanduser().resolve()
    public=Path(args.out).expanduser().resolve()
    repo=Path.home()/"AI_policy"
    if not all(p.is_file() for p in (source,original,codebook)):
        p.error("Missing original CEDIA screening file, Phase05 private key or codebook")
    if any(dest==d or d in dest.parents or dest in d.parents
           for d in (repo,root,original.parent,source.parent,public)):
        p.error("Protected XLSX must be in a new private folder outside GitHub and source")
    if dest.exists() and any(dest.iterdir()):
        p.error("Private destination already has material; never overwrite issued forms")
    phase05=json.loads(Path(args.phase05_report).read_text(encoding="utf8"))
    frame=source_data(source,args.source_format)
    old=check_frame(frame,phase05,original)
    chosen=select(frame,args.seed)
    records=[]
    matching=[]
    for i,(stratum,key) in enumerate(chosen,1):
        ref=frame[key]
        code=f"VAL{i:04d}"
        records.append({
            "validation_code":code,"title":safe(ref.get("title")),
            "abstract":safe(ref.get("abstract")),
            "publication_year":safe(ref.get("publication_year")),
            "type":safe(ref.get("type")),
            **{name:"" for name in FIELDS[5:]}
        })
        matching.append({"validation_code":code,"openalex_id":key,
                         "stratum":stratum,
                         "machine_ai_decision":str(ref["ai_decision"]).strip().lower()})
    dest.mkdir(parents=True,mode=0o700)
    dest.chmod(0o700)
    for reviewer in ("A","B"):
        shuffled=list(records)
        random.Random(f"{args.seed}:full1200:{reviewer}").shuffle(shuffled)
        workbook(dest/f"Validacion_1200_{reviewer}.xlsx",reviewer,shuffled)
    csvwrite(dest/"private_sampling_key.csv",
             ["validation_code","openalex_id","stratum","machine_ai_decision"],matching)
    readme=dest/"Rubrica_Validacion_V1.md"
    shutil.copy2(codebook,readme)
    readme.chmod(0o600)
    detail={
        "status":"prepared_full1200_two_blind_expert_workbooks_NO_human_ratings",
        "generated_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
        "seed":args.seed,"n":TOTAL,"population":FRAME,
        "sampling_strategy":"SRS_without_replacement_in_3_strata_plus_census_in_exclude",
        "strata":{
            k:{"population_n":N,"sample_n":n,"weight":N/n}
            for k,(_,n,N) in SAMPLE.items()
        },
        "previously_sampled_from_phase05_n":sum(key in old for _,key in chosen),
        "original_corpus_sha256":digest(source),
        "codebook_sha256":digest(codebook),
        "pristine_workbook_sha256":{
            reviewer:digest(dest/f"Validacion_1200_{reviewer}.xlsx")
            for reviewer in ("A","B")
        },
        "reviewer_forms_have_no_human_ratings":True,
        "codebook_piloting":"omitted_by_PI_request_pre_specified_before_sampling",
        "private_files":["Validacion_1200_A.xlsx","Validacion_1200_B.xlsx",
                         "Rubrica_Validacion_V1.md","private_sampling_key.csv"]
    }
    manifest=dest/"private_locked_manifest.json"
    manifest.write_text(json.dumps(detail,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    manifest.chmod(0o600)
    counts=dict(Counter(s for s,_ in chosen))
    aggregate={
       "status":detail["status"],
       "generated_utc":detail["generated_utc"],
       "population_n":FRAME,
       "sample_n":TOTAL,
       "selected_per_stratum":{k:{"population_n":N,"sample_n":n}
                               for k,(_,n,N) in SAMPLE.items()},
       "actual_draw_counts":counts,
       "reviewer_count":2,
       "human_assessments_completed":0,
       "pilot":False,
       "codebook_version":"V1.0-FULL",
       "sampling":"probability_stratified_with_full_census_of_18_screen_exclude",
       "privacy":"All article records, original ids, machine outputs, complete reviewer books and private keys are kept OUTSIDE GitHub",
       "caution":"Inter-rater agreement must be evaluated; no calibration pilot was conducted. Sample size does not guarantee precise rare-class recall."
    }
    public.mkdir(parents=True,exist_ok=True)
    (public/"full_validation_packet_aggregate.json").write_text(
        json.dumps(aggregate,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    (public/"summary.md").write_text(
        "# Phase30 — Two new experts, 1,200 selected bibliography records\n\n"
        "Status: "+detail["status"]+"\n\n"+
        "Original frame: N=10,283; planned sample: 800 core, 290 policy, 92 context, 18 exclude.\n"
        "Original Phase05 records were not excluded from the draw.\n"
        "NO 30-case pilot performed. No independent human scores yet available.\n"
        "All xlsx and private matching files remain on protected CEDIA storage.\n",
        encoding="utf8")
    print("PHASE30",detail["status"])
    print("1,200 sampled: core800 policy290 context92 exclude18")
    print("NEW experts review A/B; ZERO human scores generated")
    print("A:",dest/"Validacion_1200_A.xlsx")
    print("B:",dest/"Validacion_1200_B.xlsx")
    print("Rubric:",readme)
    print("PRIVATE key and manifest: DO NOT SHARE OR PUBLISH")
    print("PUBLIC counts only:",public/"full_validation_packet_aggregate.json")


if __name__=="__main__":
    main()
