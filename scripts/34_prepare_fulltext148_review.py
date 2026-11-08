#!/usr/bin/env python3
"""Phase34: privately prepare 148 independent FULL-TEXT evidence forms from Phase33.

NO machine/human scores generated. This stage exists because 148/324 cases
were explicitly flagged for full-text review, including all 74 R9 unresolved.
Returns two reviewer-facing XLSX files with the SAME 148 citations, randomized
independently, leaving ALL rating fields BLANK. Blind to original AI screening
strata, original A/B ratings and Phase33 informed panel labels. Maintain
full-text bibliographic source link/section and actual evidence. The private
key links FT-codes back to VAL-codes, never public.

Requires the Phase33 aggregate and returned 324 case XLSX as frozen sources.
No claim of actual full-text access or validation accuracy is generated.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import shutil

FRAME=148
FIELDS=[
    "ft_code","title","abstract","publication_year","type",
    "access_status","fulltext_url_doi_or_identifier","fulltext_pages_sections",
    "scope_code","relevance_code","primary_topic","primary_discipline",
    "policy_mechanism","fulltext_evidence","reviewer_reason"
]
HEADERS=[
    "Código de texto completo","Título","Resumen","Año","Tipo",
    "ACCESO A TEXTO COMPLETO","FUENTE DOI/URL/IDENTIFICADOR CONSULTADA",
    "PÁGINAS/SECCIONES VERIFICADAS","ALCANCE S (0,1,9)",
    "RELEVANCIA R (0,1,2,3,9)","TEMA PRINCIPAL",
    "DISCIPLINA PRINCIPAL","MECANISMO DE POLÍTICA (SI R2/3)",
    "EVIDENCIA OBTENIDA DEL TEXTO COMPLETO","JUSTIFICACIÓN DE DECISIÓN"
]
TOPIC=[
    "teaching_learning","assessment","ethics_integrity","governance_policy",
    "research_scholarship","ai_literacy_training","equity_access",
    "privacy_security","general_policy","not_applicable","uncertain"
]
DISCIPLINE=["ssh","engineering","health_sciences","general_he","uncertain"]
EDIT={
    5:["obtained","not_found","no_access"],
    6:None,7:None,8:["0","1","9"],9:["0","1","2","3","9"],
    10:TOPIC,11:DISCIPLINE,12:None,13:None,14:None
}
INSTRUCTIONS=[
 ["RESPONSABLE","Evaluador {REVIEWER} — Fase34: 148 documentos, revisión real de TEXTO COMPLETO"],
 ["OBJETO","Resolver los estudios marcados para consulta de texto completo; NO es un nuevo piloto ni una repetición de 1200 títulos/resúmenes."],
 ["ENMASCARAMIENTO","No se entregan decisiones antiguas de expertos, panel, IA ni estratos. Trabaje independiente del otro evaluador."],
 ["EVIDENCIA","Buscar el artículo íntegro, registrar URL/DOI exacto, secciones o páginas y evidencia concreta realmente consultada."],
 ["ACCESO","obtained si consultó texto completo; not_found si no localizó el artículo; no_access si el texto está identificado pero inaccesible."],
 ["DECISIÓN","Solo si obtuvo el texto completo, asignar S, R, tema y disciplina de nuevo siguiendo la rúbrica V1.0, de manera independiente."],
 ["INSUFICIENTE","Si acceso no está disponible, registre la búsqueda y razón; deje códigos finales vacíos, no fabrique evidencia."],
 ["RELEVANCIA","R0 fuera, R1 IA sin política demostrada, R2 vínculo institucional indirecto concreto, R3 política objeto central, R9 evidencia insuficiente."],
 ["POLÍTICA","Para R2/R3 anotar mecanismo institucional y demostrarlo en evidencia de sección/página."],
 ["REVISIÓN","No usar IA/LLM para elaborar etiquetas humanas. Las herramientas de búsqueda documental pueden usarse si se declaran."],
 ["GUARDAR","Editar SOLO columnas amarillas F–O; no modificar título, resumen, código, año, tipo, filas ni encabezados."],
 ["ENTREGA","Devolver XLSX por canal privado. No subir a GitHub ni intercambiar datos con el otro evaluador antes del cierre."],
 ["NO INFERENCIA","Los 148 artículos son selección dirigida por incertidumbre/solicitud; no estiman rendimiento muestral del clasificador."]
]
SCALES=[
 ["ESTADO","SIGNIFICADO"],
 ["obtained","Realmente obtenido y LEÍDO el texto completo; exige páginas/secciones y evidencia"],
 ["not_found","No localizado tras búsqueda documentada, sin inventar etiqueta"],
 ["no_access","Localizado, pero no accesible; sin inventar etiqueta"],
 ["R0","Fuera de IA en educación superior"],["R1","IA en educación superior sin política sustentada"],
 ["R2","Implicación de norma institucional indirecta y concreta"],
 ["R3","Regulación/gobernanza/política como OBJETO principal"],
 ["R9","Aún insuficiente con el texto completo; requiere razón muy específica"]
]
SCALES.extend([[v,v.replace("_"," ")] for v in TOPIC+DISCIPLINE])


def mod(name,tag):
    p=Path(__file__).resolve().parent/name
    spec=importlib.util.spec_from_file_location(tag,p)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def digest(path):
    d=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1048576),b""):
            d.update(block)
    return d.hexdigest()


def save_private_csv(path,fields,rows):
    with path.open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    path.chmod(0o600)


def workbook(path,who,records):
    excel=mod("17_excel_reviewer_packages.py","phase34_excel")
    pack=mod("18_prepare_blinded_adjudication_excel.py","phase34_pack")
    notes=[[a,b.replace("{REVIEWER}",who)] for a,b in INSTRUCTIONS]
    tabs=[
        ("INSTRUCCIONES",excel.basic_sheet(notes,[42,119])),
        ("TEXTO_COMPLETO",excel.section_xml("DOCUMENTOS",FIELDS,HEADERS,
            [{"group_code":r["ft_code"],**r} for r in records],
            [18,59,100,14,18,22,73,48,18,23,24,24,69,92,86],EDIT)),
        ("ESCALAS",excel.basic_sheet(SCALES,[33,119]))
    ]
    pack.xlsx_generic(path,tabs,excel)


def main():
    p=argparse.ArgumentParser()
    home=Path.home()
    p.add_argument("--returned-panel",default=str(home/"ai_policy_validacion1200_panel_recibido_privado/Adjudicacion_Validacion_1200_Humana_COMPLETADA.xlsx"))
    p.add_argument("--phase33-report",default="reports/phase33/panel_adjudication_aggregate.json")
    p.add_argument("--phase30-manifest",default=str(home/"ai_policy_validation1200_private/private_locked_manifest.json"))
    p.add_argument("--codebook",default="docs/phase30_full_validation_codebook_v1.0.md")
    p.add_argument("--private-out",default=str(home/"ai_policy_fulltext148_private"))
    p.add_argument("--out",default="reports/phase34")
    p.add_argument("--seed",type=int,default=20261108)
    args=p.parse_args()
    panel=Path(args.returned_panel).expanduser().resolve()
    manifest=Path(args.phase30_manifest).expanduser().resolve()
    codebook=Path(args.codebook).expanduser().resolve()
    private=Path(args.private_out).expanduser().resolve()
    out=Path(args.out).expanduser().resolve()
    repo=home/"AI_policy"
    if not all(path.is_file() for path in (panel,manifest,codebook)):
        p.error("Missing PRIVATE Phase33 original adjudication, Phase30 manifest or V1.0 rubric")
    if (private.exists() and any(private.iterdir())):
        p.error("Private target already nonempty; do not overwrite originally issued forms")
    if any(private==x or x in private.parents or private in x.parents
           for x in (repo,panel.parent,manifest.parent,out)):
        p.error("Full-text reviewer packet must be in a fresh PRIVATE folder outside GitHub")
    if any(out==x or x in out.parents or x in out.parents
           for x in (panel.parent,manifest.parent,private)):
        p.error("Aggregate reports may not overlap private source data")
    ph33=json.loads(Path(args.phase33_report).read_text(encoding="utf8"))
    expected=ph33["panel_scientific_reason_diagnostics"]["residual"]["requested_fulltext_yes"]
    unresolved=ph33["panel_scientific_reason_diagnostics"]["residual"]["uncertain_relevance_9"]
    if expected!=FRAME or unresolved!=74 or ph33.get("casebook_n")!=324:
        raise ValueError("Phase33 is not the verified 324-case, 148-fulltext source")
    manifest_data=json.loads(manifest.read_text(encoding="utf8"))
    if digest(codebook)!=manifest_data["codebook_sha256"]:
        raise ValueError("Source scientific rubric changed since original Phase30 ratings")
    reader=mod("33_audit_returned_panel1200.py","phase34_panel")
    p32=mod("32_audit_pi_attested_human1200.py","phase34_p32")
    panels,sequence=reader.load_table(panel,p32.HEADERS)
    if len(panels)!=324:
        raise ValueError("Source panel did not contain all original 324 records")
    selected=[row for row in panels.values() if row[27]=="yes"]
    if len(selected)!=FRAME or any(r[23]=="9" and r[27]!="yes" for r in panels.values()):
        raise ValueError("Full-text request selection does not match Phase33 audited aggregate")
    rng=random.Random(args.seed)
    rng.shuffle(selected)
    independent=[]
    key=[]
    for ix,row in enumerate(selected,1):
        code=f"FT{ix:04d}"
        independent.append({
          "ft_code":code,
          "title":row[1],"abstract":row[2],
          "publication_year":row[3],"type":row[4],
          **{f:"" for f in FIELDS[5:]}
        })
        key.append({
          "ft_code":code,"validation_code":row[0],
          "panel_relevance_before_fulltext":row[23],
          "panel_scope_before_fulltext":row[22],
          "panel_fulltext_requested":row[27],
          "panel_original_scientific_reason":row[26]
        })
    private.mkdir(parents=True,mode=0o700)
    private.chmod(0o700)
    for who in ("A","B"):
        randomized=list(independent)
        random.Random(str(args.seed)+":FT:"+who).shuffle(randomized)
        workbook(private/f"TextoCompleto_148_{who}.xlsx",who,randomized)
    save_private_csv(private/"private_fulltext_key.csv",
        list(key[0]),key)
    rubric=private/"Rubrica_Validacion_V1.md"
    shutil.copy2(codebook,rubric)
    rubric.chmod(0o600)
    locked={
       "status":"148_requested_fulltext_blinded_double_review_books_CREATED_NO_reviews",
       "utc":dt.datetime.now(dt.timezone.utc).isoformat(),
       "n":FRAME,
       "source_panel_sha256":digest(panel),
       "codebook_sha256":digest(codebook),
       "seed":args.seed,
       "workbook_sha256":{
           x:digest(private/f"TextoCompleto_148_{x}.xlsx")
           for x in ("A","B")
       },
       "private_key_sha256":digest(private/"private_fulltext_key.csv"),
       "reviewer_labels_created":0,
       "panel_74_uncertain9_included":True,
       "actual_fulltext_files_retrieved":False
    }
    m=private/"private_fulltext_manifest.json"
    m.write_text(json.dumps(locked,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    m.chmod(0o600)
    report={
       "created_utc":locked["utc"],
       "status":"prepared_148_two_blind_fulltext_evidence_books_NOT_PERFORMED",
       "n_requested_for_fulltext":FRAME,
       "n_human_review_forms":2,
       "n_undecidable_R9_in_original_panel":unresolved,
       "n_sources_read_in_this_step":0,
       "n_new_human_decisions":0,
       "source_decisions_from_324_case_phase33_panel":True,
       "original_phase33_report_unchanged":True,
       "scope":"targeted_fulltext_resolution_not_new_probability_screening_sample",
       "privacy":"Fulltext source bibliography, prior panel decisions, individual FT case IDs and responses remain private outside GitHub.",
       "warning":"An indicated need for full text is NOT proof full text was actually accessed; phase33 provenance conflict remains documentable."
    }
    out.mkdir(parents=True,exist_ok=True)
    (out/"fulltext_preparation_aggregate.json").write_text(
         json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    (out/"summary.md").write_text(
        "# Phase34 — 148 records flagged for full-text review\n\n"
        "Status: "+report["status"]+"\n\n"
        "Two private 148-row spreadsheets were generated, including all 74 residual R9s. NO human labels and NO full-text evidence were generated.\n"
        "Preserve the private source key and pristine reviewer workbooks. Retain Phase33 panel decisions unchanged.\n",
        encoding="utf8")
    print("PHASE34",report["status"])
    print("148 new fulltext review tasks, including all",unresolved,"remaining uncertain R9.")
    for who in ("A","B"):
        print("EXPERT",who,private/f"TextoCompleto_148_{who}.xlsx")
    print("Rubric:",rubric)
    print("PRIVATE linkage and manifest: NEVER upload to public GitHub")
    print("PUBLIC aggregate only:",out/"fulltext_preparation_aggregate.json")

if __name__=="__main__":
    main()
