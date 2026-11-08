#!/usr/bin/env python3
"""Phase 18 — blinded, PRIVATE Excel adjudication packet after two real raters.

Reads Phase16 normalized ratings and Phase15 master samples. Produces a single
editable Excel with ALL 48 topic groups, ALL 336 evidence cases and ONLY
document cases with rater disagreements. Model/k group correspondence stays
in the private CEDIA key; this Excel does not disclose it.

Never export article texts, document IDs, private group codes or model keys
to public GitHub. Public reports contain counts only. No adjudications are
inferred, auto-filled or fabricated.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import importlib.util
import json
import os
from pathlib import Path
from xml.sax.saxutils import escape
import zipfile

import numpy as np
import pandas as pd


def load_mod(filename, tag):
    p=Path(__file__).resolve().parent/filename
    s=importlib.util.spec_from_file_location(tag,p)
    m=importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def public_report(out,info):
    out.mkdir(parents=True,exist_ok=True)
    (out/"adjudication_preparation_aggregate.json").write_text(
        json.dumps(info,indent=2,ensure_ascii=False),encoding="utf8")
    lines=[
        "# Phase 18 — Blinded human adjudication packet",
        "",
        "Status: "+info["status"],
        "UTC: "+info["generated_utc"],
        "",
        "## Counts only",
        json.dumps(info["counts"],indent=2),
        "",
        "The private Excel is prepared on CEDIA, outside GitHub.",
        "Two independent ratings already exist. No third-party adjudication has occurred.",
        "The adjudicator does not see which cluster was produced by which model or k.",
        "",
        "## Scientific limitations",
    ]+["- "+note for note in info["limitations"]]
    (out/"summary.md").write_text("\n".join(lines)+"\n",encoding="utf8")


def xlsx_generic(outfile,tabs,excel_helper):
    """Create Office XLSX with five sheets, relying on Phase17's tested XML."""
    NS=excel_helper.NS
    REL=excel_helper.REL
    n=len(tabs)
    tabnames="".join(
        f'<sheet name="{escape(name)}" sheetId="{i}" r:id="rId{i}"/>'
        for i,(name,_) in enumerate(tabs,1))
    book=(f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          f'<workbook xmlns="{NS}" xmlns:r="{REL}">'
          f'<sheets>{tabnames}</sheets></workbook>')
    relations="".join(
        f'<Relationship Id="rId{i}" Type="{REL}/worksheet" '
        f'Target="worksheets/sheet{i}.xml"/>'
        for i in range(1,n+1))
    relxml=(f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            f'{relations}<Relationship Id="rId{n+1}" Type="{REL}/styles" '
            f'Target="styles.xml"/></Relationships>')
    overrides="".join(
        f'<Override PartName="/xl/worksheets/sheet{i}.xml" '
        f'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        for i in range(1,n+1))
    contenttypes=(f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        f'<Default Extension="xml" ContentType="application/xml"/>'
        f'<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        f'<Override PartName="/xl/workbook.xml" '
        f'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        f'<Override PartName="/xl/styles.xml" '
        f'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        f'{overrides}</Types>')
    relroot=('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
             '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
             '<Relationship Id="rId1" '
             'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
             'Target="xl/workbook.xml"/></Relationships>')
    with zipfile.ZipFile(outfile,mode="w",
                         compression=zipfile.ZIP_DEFLATED,compresslevel=7) as z:
        for name,xml in {
            "[Content_Types].xml":contenttypes,
            "_rels/.rels":relroot,
            "xl/workbook.xml":book,
            "xl/_rels/workbook.xml.rels":relxml,
            "xl/styles.xml":excel_helper.styles_xml()
        }.items():
            z.writestr(name,xml)
        for index,(_,xml) in enumerate(tabs,1):
            z.writestr(f"xl/worksheets/sheet{index}.xml",xml)
    os.chmod(outfile,0o600)
    with zipfile.ZipFile(outfile) as z:
        if z.testzip() is not None:
            raise ValueError("Corrupted workbook detected after export")


def load_and_verify(normalized,original):
    phase16=load_mod("16_score_human_topic_review.py","phase16_private")
    if not normalized.is_dir() or not original.is_dir():
        raise FileNotFoundError("Protected Phase15 or normalized Phase16 folder unavailable")
    forms=phase16.read_ratings(normalized)
    manifest=json.loads((normalized/"private_validation_manifest.json").read_text(encoding="utf8"))
    key=phase16.private_key_verify(normalized,forms,manifest)
    if int(manifest["n_groups"])!=48 or \
       int(manifest["n_document_assessments_per_rater"])!=336:
        raise ValueError("Unexpected sample size or source manifest")
    for r in ("a","b"):
        for section in ("documents","topics"):
            master=original/f"rater_{r}_{section}.csv"
            original_frame=pd.read_csv(master,dtype=str,encoding="utf-8-sig").fillna("")
            normalized_frame=pd.read_csv(normalized/master.name,dtype=str,encoding="utf-8-sig").fillna("")
            # Verify source evidence in normalized files is unchanged.
            readonly=[
                "group_code","item_code","title","abstract","body_excerpt_A","body_excerpt_B"
            ] if section=="documents" else ["group_code"]
            if not original_frame[readonly].sort_values(readonly[:2],kind="stable").reset_index(drop=True).equals(
                   normalized_frame[readonly].sort_values(readonly[:2],kind="stable").reset_index(drop=True)):
                raise ValueError("Protected rating inputs have altered original evidence")
    for p in forms:
        frame=forms[p]
        fields=(phase16.TOPIC_FIELDS if p[1]=="topics" else phase16.DOC_FIELDS)
        for f in fields:
            vals=frame[f]
            if frame[f].notna().sum()!=len(frame) if fields[f]!="text" else frame[f].astype(str).str.strip().ne("").sum()!=len(frame):
                raise ValueError("Both independent rating forms must be complete")
    return forms,key


def build_data(forms,original):
    def merge_section(which,fields,codes):
        aa=forms[("a",which)][list(codes)+fields].copy()
        bb=forms[("b",which)][list(codes)+fields].copy()
        joined=aa.merge(bb,on=list(codes),suffixes=("_a","_b"),
                        validate="one_to_one").sort_values(list(codes),kind="stable")
        return joined
    tg=merge_section("topics",[
        "topic_name_proposed","topic_coherence_1_to_5",
        "distinctiveness_1_to_5","direct_policy_relevance_0_to_3_or_9",
        "confidence_1_to_5","reviewer_comments"
    ],["group_code"])
    dd=merge_section("documents",[
        "belongs_to_one_coherent_theme_0_no_1_yes_9_uncertain",
        "policy_relevance_0_to_3_or_9_uncertain","document_comments"
    ],["group_code","item_code"])
    # Extract evidence strictly from the original, unchanged, protected master forms.
    doc_source=pd.read_csv(original/"rater_a_documents.csv",
                           dtype=str,encoding="utf-8-sig").fillna("")
    dd=dd.merge(doc_source[[
        "group_code","item_code","title","abstract","body_excerpt_A","body_excerpt_B"
    ]],on=["group_code","item_code"],validate="one_to_one")
    belong="belongs_to_one_coherent_theme_0_no_1_yes_9_uncertain"
    policy="policy_relevance_0_to_3_or_9_uncertain"
    disagree_belong=dd[belong+"_a"]!=dd[belong+"_b"]
    disagree_policy=dd[policy+"_a"]!=dd[policy+"_b"]
    disagreements=dd.loc[disagree_belong|disagree_policy].copy()

    def s(value):
        if pd.isna(value):return ""
        if isinstance(value,(np.integer,np.floating)):
            return str(int(value)) if float(value).is_integer() else str(value)
        return str(value)
    groups=[]
    for row in tg.to_dict("records"):
        groups.append({
            "group_code":s(row["group_code"]),
            "topic_name_a":s(row["topic_name_proposed_a"]),
            "topic_name_b":s(row["topic_name_proposed_b"]),
            "coherence_a":s(row["topic_coherence_1_to_5_a"]),
            "coherence_b":s(row["topic_coherence_1_to_5_b"]),
            "distinctiveness_a":s(row["distinctiveness_1_to_5_a"]),
            "distinctiveness_b":s(row["distinctiveness_1_to_5_b"]),
            "policy_a":s(row["direct_policy_relevance_0_to_3_or_9_a"]),
            "policy_b":s(row["direct_policy_relevance_0_to_3_or_9_b"]),
            "comment_a":s(row.get("reviewer_comments_a","")),
            "comment_b":s(row.get("reviewer_comments_b","")),
            "consensus_topic_name":"",
            "consensus_coherence":"",
            "consensus_distinctiveness":"",
            "consensus_policy_relevance":"",
            "adjudication_reason":""
        })
    docs=[]
    for row in dd.to_dict("records"):
        docs.append({
            "group_code":s(row["group_code"]),
            "item_code":s(row["item_code"]),
            "title":s(row["title"]),
            "abstract":s(row["abstract"]),
            "body_excerpt_A":s(row["body_excerpt_A"]),
            "body_excerpt_B":s(row["body_excerpt_B"]),
            "membership_a":s(row[belong+"_a"]),
            "membership_b":s(row[belong+"_b"]),
            "policy_a":s(row[policy+"_a"]),
            "policy_b":s(row[policy+"_b"]),
        })
    differences=[]
    for row in disagreements.to_dict("records"):
        differences.append({
            "group_code":s(row["group_code"]),
            "item_code":s(row["item_code"]),
            "membership_a":s(row[belong+"_a"]),
            "membership_b":s(row[belong+"_b"]),
            "policy_a":s(row[policy+"_a"]),
            "policy_b":s(row[policy+"_b"]),
            "title":s(row["title"]),
            "abstract":s(row["abstract"]),
            "body_excerpt_A":s(row["body_excerpt_A"]),
            "body_excerpt_B":s(row["body_excerpt_B"]),
            "comment_a":s(row.get("document_comments_a","")),
            "comment_b":s(row.get("document_comments_b","")),
            "consensus_membership":"",
            "consensus_policy_relevance":"",
            "adjudication_reason":""
        })
    counts={
        "blind_topic_groups_total":len(groups),
        "document_examples_for_context":len(docs),
        "disputed_unique_document_cases":len(differences),
        "document_membership_disagreements":int(disagree_belong.sum()),
        "document_policy_relevance_disagreements":int(disagree_policy.sum()),
        "document_cases_with_both_disagreements":int((disagree_belong&disagree_policy).sum()),
        "topic_coherence_disagreements":int((tg["topic_coherence_1_to_5_a"]!=tg["topic_coherence_1_to_5_b"]).sum()),
        "topic_distinctiveness_disagreements":int((tg["distinctiveness_1_to_5_a"]!=tg["distinctiveness_1_to_5_b"]).sum()),
        "topic_policy_relevance_disagreements":int((tg["direct_policy_relevance_0_to_3_or_9_a"]!=tg["direct_policy_relevance_0_to_3_or_9_b"]).sum())
    }
    return groups,docs,differences,counts


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--normalized-ratings",
        default=str(Path.home()/"ai_policy_calificaciones_normalizadas_privado"))
    ap.add_argument("--phase15-private",
        default=str(Path.home()/"ai_policy_topic_validation_private"))
    ap.add_argument("--private-out",
        default=str(Path.home()/"ai_policy_adjudicacion_privado"))
    ap.add_argument("--out",default="reports/phase18")
    args=ap.parse_args()
    normalized=Path(args.normalized_ratings).expanduser().resolve()
    original=Path(args.phase15_private).expanduser().resolve()
    private=Path(args.private_out).expanduser().resolve()
    public=Path(args.out).expanduser().resolve()
    repo=Path.home()/"AI_policy"
    if not normalized.is_dir() or not original.is_dir():
        ap.error("Protected original or normalized ratings are missing")
    if private==repo or repo in private.parents or private==public or public in private.parents or \
       private in public.parents or public in private.parents or \
       private==normalized or normalized in private.parents or private in normalized.parents or \
       private==original or original in private.parents or private in original.parents:
        ap.error("Adjudication files must be in a new PRIVATE folder outside source and GitHub")
    if private.exists() and any(private.iterdir()):
        ap.error("Adjudication destination already contains files, refusing to overwrite")
    forms,_=load_and_verify(normalized,original)
    groups,docs,disputes,counts=build_data(forms,original)
    excel=load_mod("17_excel_reviewer_packages.py","excel_phase17")
    private.mkdir(parents=True,exist_ok=True,mode=0o700)
    os.chmod(private,0o700)

    def sect(name,records,headers,widths,editable):
        fields=list(records[0])
        if len(fields)!=len(headers):
            raise ValueError("Header mismatch")
        return excel.section_xml(name,fields,headers,records,widths,editable)
    intro=[
        ["ADJUDICACIÓN CIEGA","Instrucciones para la persona responsable"],
        ["Objetivo","Resolver nombres, coherencia, diferenciación y pertinencia política de los 48 grupos y los casos documentales en desacuerdo."],
        ["Independencia","Las calificaciones A y B ya fueron hechas independientemente; esta tercera fase es un CONSENSO o adjudicación y NO debe presentarse como tercera evaluación independiente ciega de las respuestas."],
        ["Ocultamiento","La hoja no revela qué algoritmo ni qué valor de k produjo cada grupo."],
        ["PASO 1","Abra GRUPOS y examine las etiquetas y calificaciones de A y B."],
        ["PASO 2","Abra EJEMPLOS para leer los siete casos de cada grupo; puede filtrar por código de grupo."],
        ["PASO 3","En GRUPOS complete SOLO las celdas amarillas con nombre, coherencia, diferenciación, pertinencia y justificación de consenso para los 48 grupos."],
        ["PASO 4","En DESACUERDOS documentales complete SOLO las celdas amarillas para resolver pertenencia y pertinencia en cada caso, con una breve justificación."],
        ["Criterio fundamental","Pertinencia 0: no IA educativa; 1: IA educativa sin política clara; 2: implicación indirecta para política; 3: gobernanza, regulación o política directamente estudiada; 9: evidencia insuficiente."],
        ["Escala tema","Coherencia: 1 sin tema, 3 moderada, 5 específica/consistente. Diferenciación: 1 solapa otras, 5 claramente distinto."],
        ["Escala documento","Pertenencia: 0=no, 1=sí, 9=incierto."],
        ["NO hacer","No editar los identificadores, títulos, resúmenes, extractos ni puntuaciones A y B. No reordenar/cortar filas ni renombrar pestañas."],
        ["Entrega","Guarde el mismo .xlsx, con las celdas amarillas completas. Devuélvalo privadamente al coordinador; NO lo suba a GitHub."],
        ["Seguridad","Este libro contiene material académico y calificaciones individuales de los evaluadores. Solo debe almacenarse/transferirse por canales privados."]
    ]
    scales=[
        ["Campo","Significado"],
        ["Tema coherencia 1-5","1 sin tema compartido, 3 moderada, 5 tema bien delimitado"],
        ["Tema diferenciación 1-5","1 solapamiento amplio, 3 diferencia moderada, 5 tema claramente distinto"],
        ["Pertinencia 0","No aborda IA en educación superior"],
        ["Pertinencia 1","IA educativa sin dimensión política clara"],
        ["Pertinencia 2","Consecuencias o recomendaciones indirectas de política"],
        ["Pertinencia 3","Normas, regulación, políticas, gobernanza directamente estudiadas"],
        ["Pertinencia 9","Información insuficiente para decidir"],
        ["Pertenencia 0","Documento no pertenece al tema identificado"],
        ["Pertenencia 1","Documento sí pertenece al tema identificado"],
        ["Pertenencia 9","No se puede determinar"],
        ["Justificación","Exponer evidencia textual concreta; no se exige coincidir con A ni B"]
    ]
    groups_headers=[
        "Grupo","Nombre propuesto A","Nombre propuesto B",
        "Coherencia A","Coherencia B","Diferenciación A","Diferenciación B",
        "Pertinencia A","Pertinencia B","Comentario A","Comentario B",
        "NOMBRE FINAL (editar)","COHERENCIA FINAL (1-5)",
        "DIFERENCIACIÓN FINAL (1-5)","PERTINENCIA FINAL (0-3,9)",
        "JUSTIFICACIÓN FINAL (editar)"
    ]
    docs_headers=[
        "Grupo","Documento","Título","Resumen","Extracto cuerpo A","Extracto cuerpo B",
        "Pertenencia A","Pertenencia B","Pertinencia A","Pertinencia B"
    ]
    disagreements_headers=[
        "Grupo","Documento","Pertenencia A","Pertenencia B","Pertinencia A","Pertinencia B",
        "Título","Resumen","Extracto cuerpo A","Extracto cuerpo B",
        "Comentario A","Comentario B",
        "PERTENENCIA FINAL (0,1,9)","PERTINENCIA FINAL (0-3,9)",
        "JUSTIFICACIÓN FINAL (editar)"
    ]
    tabs=[
        ("INSTRUCCIONES",excel.basic_sheet(intro,[34,104])),
        ("GRUPOS",sect("GRUPOS",groups,groups_headers,
            [15,39,39,14,14,17,17,15,15,40,40,48,24,26,26,60],
            {11:None,12:["1","2","3","4","5"],13:["1","2","3","4","5"],
             14:["0","1","2","3","9"],15:None})),
        ("EJEMPLOS",sect("DOCUMENTOS",docs,docs_headers,
            [15,19,42,75,67,67,18,18,18,18],{})),
        ("DESACUERDOS",sect("DOCUMENTOS",disputes,disagreements_headers,
            [15,19,18,18,18,18,42,70,65,65,40,40,28,28,58],
            {12:["0","1","9"],13:["0","1","2","3","9"],14:None})),
        ("ESCALAS",excel.basic_sheet(scales,[34,95]))
    ]
    output=private/"Adjudicacion_Ciega_Fase18.xlsx"
    xlsx_generic(output,tabs,excel)
    info={
        "generated_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
        "status":"adjudication_packet_prepared_human_consensus_pending",
        "counts":counts,
        "reviewer_input_status":"Both independent reviewers fully completed Phase16.",
        "private_output_format":"XLSX, private CEDIA only",
        "limitations":[
            "No third-party adjudication has occurred yet and no consensus is auto-filled.",
            "The full source text was character-capped in the original extraction and supplied excerpts may contain formatting noise.",
            "The adjudicator can observe A and B ratings but not model identity; this is reconciliation, not independent blind rating.",
            "The 7 examples per topic overrepresent centroid-proximate cases and cannot estimate topic population-wide precision without adjustment.",
            "Any agreement in both independent ratings is not necessarily scientifically correct.",
            "The final topic names and decisions require documented expert judgment.",
            "Phase5 relevance/eligibility screening audit remains separate and unfinished."
        ]
    }
    public_report(public,info)
    print("PHASE 18 ADJUDICATION EXCEL READY — NO HUMAN CONSENSUS YET")
    print("Groups:",counts["blind_topic_groups_total"])
    print("Document examples:",counts["document_examples_for_context"])
    print("Unique disputed document cases:",counts["disputed_unique_document_cases"])
    print("PRIVATE workbook:",output)
    print("Public AGGREGATE report:",public/"summary.md")
    print("Never push the private XLSX or individual reviewer comments to GitHub")


if __name__=="__main__":
    main()
