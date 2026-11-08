#!/usr/bin/env python3
"""Phase26 — PRIVATE panel calibration dossier after serious Phase25 QA discordance.

Rechecks protected Phase22/23 consensus, original independent Phase24 QA,
later corrected Phase24 QA and completed Phase25 policy normalization.
Exports a 3-sheet PRIVATELY held XLSX for an independent methods panel:
- instructions, including no automated consensus;
- all 80 QA cases with source abstracts, original A/B ratings, reconciled
  human consensus, independently rated relevance/discipline, *later corrected*
  policy dimension and provenance-specific written rationales;
- rubric.

No AI screening labels, original sample IDs, OpenAlex IDs or sampling
strata appear in the XLSX. Zero individually traceable data may be pushed
to GitHub. Public output is counts and readiness, not new ratings.
"""
from __future__ import annotations
from collections import Counter
import argparse
import datetime as dt
import importlib.util
import json
import os
from pathlib import Path

FIELDS=[
    "qa_code","title","abstract","publication_year","type",
    "relevance_a","relevance_b","consensus_relevance","independent_qa_relevance",
    "discipline_a","discipline_b","consensus_discipline","independent_qa_discipline",
    "policy_a","policy_b","consensus_policy","posthoc_normalized_qa_policy",
    "consensus_reason","qa_original_reason","qa_corrected_reason",
    "relevance_disagreement","discipline_disagreement","policy_disagreement",
    "panel_final_relevance","panel_final_discipline","panel_final_policy","panel_rationale"
]
HEADERS=[
    "Código QA","Título","Resumen","Año","Tipo",
    "Relevancia A","Relevancia B","Consenso relevancia","QA independiente relevancia",
    "Disciplina A","Disciplina B","Consenso disciplina","QA independiente disciplina",
    "Política A","Política B","Consenso política","QA política normalizada POSTERIOR",
    "Justificación consenso","Justificación QA ORIGINAL",
    "Justificación QA CORREGIDA",
    "Discrepancia relevancia","Discrepancia disciplina","Discrepancia política",
    "DECISIÓN FINAL DE RELEVANCIA","DECISIÓN FINAL DISCIPLINA",
    "DECISIÓN FINAL POLÍTICA","RAZONAMIENTO CIENTÍFICO DEL PANEL"
]
RELEVANCE=("0","1","2","3","9")
DISCIPLINES=("ssh","engineering","health_sciences","general_he","uncertain")
POLICIES=("teaching_learning","assessment","ethics_integrity","governance_policy",
          "research_scholarship","ai_literacy_training","equity_access",
          "privacy_security","general_policy","not_applicable","uncertain")
EDIT={23:list(RELEVANCE),24:list(DISCIPLINES),25:list(POLICIES),26:None}
INTRO=[
 ["FASE 26 — REVISIÓN METODOLÓGICA","Conciliación cuidadosa de un control independiente de calidad con desacuerdos sustantivos"],
 ["PROPÓSITO","Resolver discrepancias de validez de constructo, no elegir por defecto a un evaluador ni confirmar por mayoría simple."],
 ["ORIGEN","La muestra contiene 80 casos de QA deliberadamente enriquecidos por riesgo; no es una muestra representativa."],
 ["EVIDENCIA","Las columnas A/B y el CONSENSO corresponden a Phase21/23. QA independiente se refiere a la primera versión de Phase24."],
 ["PROCEDENCIA","La clasificación de política QA se NORMALIZÓ POSTERIORMENTE, y sus justificaciones se CORRIGIERON en un segundo archivo: no es una evaluación independiente adicional."],
 ["REGISTROS","Se incluyen los 80 casos para calibración. Las columnas de discrepancia identifican diferencias con el consenso anterior."],
 ["INSTRUCCIÓN 1","El panel debería definir por escrito una misma regla operacional para relevancia 0/1/2/3/9 antes de modificar resultados."],
 ["INSTRUCCIÓN 2","Lea el título/resumen y compare justificaciones. Cuando la evidencia sea insuficiente, conserve relevancia 9 e indique la evidencia o texto completo necesario."],
 ["INSTRUCCIÓN 3","Disciplina representa el área principal de contribución; la dimensión de política representa el objeto principal, no cualquier tema mencionado."],
 ["INSTRUCCIÓN 4","Complete las cuatro columnas amarillas (relevancia final, disciplina final, política final y argumentación), sin alterar fuentes, códigos o dictámenes anteriores."],
 ["INSTRUCCIÓN 5","La respuesta debe justificar específicamente por qué el criterio es 1 frente a 2, o 2 frente a 3; citar evidencia textual breve disponible."],
 ["INSTRUCCIÓN 6","No adopte automáticamente al evaluador B, al adjudicador ni al auditor QA; las tres fuentes tienen incertidumbre."],
 ["INSTRUCCIÓN 7","No invente un tercer evaluador independiente: esta etapa es conciliación metodológica posterior a conocer decisiones anteriores."],
 ["INSTRUCCIÓN 8","No acceda a la clave de muestreo ni etiquetas automáticas durante la conciliación. Conserve la independencia de criterios científicos."],
 ["PRIVACIDAD","Este libro incluye títulos, resúmenes y juicios individuales: NO subir a GitHub, compartir públicamente ni poner dentro de $HOME/AI_policy."],
 ["REPORTE","La reevaluación debe indicar las reglas del codebook, incertidumbre residual, desviaciones al procedimiento y la limitación de muestreo dirigido."],
]
RUBRIC=[
 ["CÓDIGO","DEFINICIÓN OPERACIONAL"],
 ["0","Fuera de estudios de IA en educación superior"],
 ["1","Estudio de IA en educación superior SIN implicación política sustentada por contenido"],
 ["2","Estudio de IA con implicación INDIRECTA y defendible en políticas, normas o gobernanza"],
 ["3","Estudio que investiga DIRECTAMENTE normas, políticas, regulaciones, gobernanza o efectos de estas"],
 ["9","Evidencia bibliográfica insuficiente; título/resumen no permiten concluir"],
 ["ssh","Ciencias sociales/humanidades"],
 ["engineering","Ingeniería/tecnología"],
 ["health_sciences","Ciencias de la salud"],
 ["general_he","Educación superior general o interdisciplinar"],
 ["uncertain","Disciplina o política insuficientemente determinada"],
 ["teaching_learning","Enseñanza y aprendizaje"],
 ["assessment","Evaluación educativa"],
 ["ethics_integrity","Ética, integridad y plagio académico"],
 ["governance_policy","Gobernanza y políticas institucionales o públicas"],
 ["research_scholarship","Investigación y trabajo académico"],
 ["ai_literacy_training","Alfabetización y capacitación en IA"],
 ["equity_access","Equidad/acceso"],
 ["privacy_security","Privacidad y seguridad"],
 ["general_policy","Dimensiones generales de políticas"],
 ["not_applicable","No aplica"],
]

def module(file,tag):
    p=Path(__file__).resolve().parent/file
    spec=importlib.util.spec_from_file_location(tag,p)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--original-phase22",default=str(
        Path.home()/"ai_policy_screening_adjudicacion_privado/Adjudicacion_Cribado_Fase22.xlsx"))
    ap.add_argument("--returned-phase22",default=str(
        Path.home()/"ai_policy_screening_adjudicacion_recibida_privado/Adjudicacion_Cribado_Fase22_COMPLETADA.xlsx"))
    ap.add_argument("--human-private",default=str(
        Path.home()/"ai_policy_screening_calificaciones_normalizadas_privado"))
    ap.add_argument("--qa-original",default=str(
        Path.home()/"ai_policy_screening_qa_independent_privado/Control_Independiente_Cribado_Fase24.xlsx"))
    ap.add_argument("--qa-received",default=str(
        Path.home()/"ai_policy_screening_qa_recibida_privado/Control_Independiente_Cribado_Fase24_Lleno.xlsx"))
    ap.add_argument("--qa-corrected",default=str(
        Path.home()/"ai_policy_screening_qa_recibida_privado/Control_Independiente_Cribado_Fase24_Corregido.xlsx"))
    ap.add_argument("--normalization",default=str(
        Path.home()/"ai_policy_screening_qa_recibida_privado/Normalizacion_codigos_QA_Fase24_COMPLETA.xlsx"))
    ap.add_argument("--qa-key",default=str(
        Path.home()/"ai_policy_screening_qa_independent_privado/correspondencia_qa_privada.csv"))
    ap.add_argument("--phase05-report",default="reports/phase05/sample_aggregate.json")
    ap.add_argument("--phase22-report",default="reports/phase22/screening_adjudication_packet_aggregate.json")
    ap.add_argument("--phase25-report",default="reports/phase25/independent_screening_qa_aggregate.json")
    ap.add_argument("--private-out",default=str(
        Path.home()/"ai_policy_panel_conciliacion_fase26_privado"))
    ap.add_argument("--out",default="reports/phase26")
    args=ap.parse_args()

    phase23=module("23_analyze_adjudicated_screening.py","phase23_26")
    phase25=module("25_compare_independent_screening_qa.py","phase25_26")
    excel=module("17_excel_reviewer_packages.py","excel_26")
    pack=module("18_prepare_blinded_adjudication_excel.py","pack_26")

    out_private=Path(args.private_out).expanduser().resolve()
    out_public=Path(args.out).expanduser().resolve()
    repo=Path.home()/"AI_policy"
    private_inputs=[Path(v).expanduser().resolve() for v in (
        args.original_phase22,args.returned_phase22,args.qa_original,
        args.qa_received,args.qa_corrected,args.normalization,args.qa_key)]
    private_dirs=[p.parent for p in private_inputs]
    private_dirs.append(Path(args.human_private).expanduser().resolve())
    if out_private==repo or repo in out_private.parents or \
       out_public==out_private or out_public in out_private.parents or \
       out_private in out_public.parents or any(
            out_private==d or d in out_private.parents or out_private in d.parents
            for d in private_dirs):
        ap.error("Create Phase26 casebook only in a FRESH protected folder outside source directories and GitHub")
    if out_private.exists() and any(out_private.iterdir()):
        ap.error("Phase26 protected folder already has content — not overwriting previous human review")
    for d in private_dirs:
        if out_public==d or d in out_public.parents:
            ap.error("Public counts cannot be written into private source folder")

    p05=json.loads(Path(args.phase05_report).read_text(encoding="utf8"))
    p22=json.loads(Path(args.phase22_report).read_text(encoding="utf8"))
    p25=json.loads(Path(args.phase25_report).read_text(encoding="utf8"))
    if p25.get("status")!="independent_qa_scored_with_posthoc_policy_normalization" \
       or p25.get("sample_n")!=80:
        raise ValueError("An approved completed Phase25 aggregate QA report is required")

    source=phase23.sheet_data(Path(args.original_phase22),excel)
    ret=phase23.sheet_data(Path(args.returned_phase22),excel)
    raters=phase23.read_original_raters(Path(args.human_private))
    everything,disputes,counts=phase23.validate_workbooks(source,ret,raters,p22)
    qa_relevance_ready,complete=phase23.readiness(disputes)
    if not complete:
        raise ValueError("Original Phase22 human adjudication was not complete")
    consensus,_=phase23.assigned_consensus(everything,disputes)

    qa_blank=phase25.sheet_records(
        phase25.xlsx_sheets(Path(args.qa_original),{"CONTROL_QA"})["CONTROL_QA"],
        phase25.QA_HEADERS,80,"Blank original QA")
    qa=phase25.sheet_records(
        phase25.xlsx_sheets(Path(args.qa_received),{"CONTROL_QA"})["CONTROL_QA"],
        phase25.QA_HEADERS,80,"Independent actual QA")
    if set(qa)!=set(qa_blank):
        raise ValueError("Independent QA sample codes have changed")
    for q in qa:
        if qa_blank[q][:5]!=qa[q][:5] or any(qa_blank[q][j] for j in (5,6,7,8)):
            raise ValueError("QA independent original template, evidence or code changed")
    normalized,normalization_status=phase25.read_normalization(Path(args.normalization),qa)
    if normalized is None or normalization_status["validated_final_codes"]!=80:
        raise ValueError("Posthoc policy normalization must be complete and checked")
    corrected=phase25.sheet_records(
        phase25.xlsx_sheets(Path(args.qa_corrected),{"CONTROL_QA"})["CONTROL_QA"],
        phase25.QA_HEADERS,80,"Later corrected QA")
    phase25.audit_corrected_qa(Path(args.qa_corrected),qa,normalized)
    key=phase25.load_key(Path(args.qa_key))
    if set(key)!=set(qa) or len(set(k["sample_id"] for k in key.values()))!=80:
        raise ValueError("Protected private QA key mismatch")
    if any(key[q]["sample_id"] not in consensus for q in key):
        raise ValueError("QA private key points outside original 368 consensus records")
    for q in qa:
        prior=consensus[key[q]["sample_id"]]
        actual=(key[q]["consensus_relevance"],key[q]["consensus_discipline"],
                key[q]["consensus_policy"])
        if prior!=actual:
            raise ValueError("Original Phase23 consensus differs from protected QA key")
    check=phase25.compare(qa,key,normalized)
    historical=p25["results"]
    for key_name in ("relevance_mismatch_cases","discipline_mismatch_cases",
                     "post_hoc_policy_mismatch_cases"):
        if check[key_name]!=historical[key_name]:
            raise ValueError("Actual protected QA mismatch counts differ from Phase25 public report")

    rows=[]
    stats=Counter()
    for q in sorted(qa):
        sample_id=key[q]["sample_id"]
        doc=everything[sample_id]
        cons=consensus[sample_id]
        received=qa[q]
        revised=corrected[q]
        rationale=(disputes[sample_id][16] if sample_id in disputes
                   else "A y B coincidieron; no se requirió adjudicación anterior.")
        flags=(received[5]!=cons[0],received[6]!=cons[1],
               normalized[q]!=cons[2])
        for label,flag in zip(("relevance","discipline","policy"),flags):
            stats["mismatch_"+label]+=int(flag)
        stats["unique_cases_with_mismatch"]+=int(any(flags))
        row={
            "qa_code":q,
            "title":received[1],"abstract":received[2],
            "publication_year":received[3],"type":received[4],
            "relevance_a":raters["a"][sample_id]["relevance_code"],
            "relevance_b":raters["b"][sample_id]["relevance_code"],
            "consensus_relevance":cons[0],"independent_qa_relevance":received[5],
            "discipline_a":raters["a"][sample_id]["discipline_code"],
            "discipline_b":raters["b"][sample_id]["discipline_code"],
            "consensus_discipline":cons[1],"independent_qa_discipline":received[6],
            "policy_a":raters["a"][sample_id]["primary_policy_code"],
            "policy_b":raters["b"][sample_id]["primary_policy_code"],
            "consensus_policy":cons[2],"posthoc_normalized_qa_policy":normalized[q],
            "consensus_reason":rationale,
            "qa_original_reason":received[8],
            "qa_corrected_reason":revised[8],
            "relevance_disagreement":"SÍ" if flags[0] else "NO",
            "discipline_disagreement":"SÍ" if flags[1] else "NO",
            "policy_disagreement":"SÍ" if flags[2] else "NO",
            "panel_final_relevance":"","panel_final_discipline":"",
            "panel_final_policy":"","panel_rationale":""
        }
        rows.append({"group_code":q,**row})

    tabs=[
        ("INSTRUCCIONES",excel.basic_sheet(INTRO,[42,120])),
        ("CASOS",excel.section_xml("DOCUMENTOS",FIELDS,HEADERS,rows,
         [14,52,103,13,20,15,15,18,22,18,18,18,22,18,18,20,25,
          75,80,80,18,18,18,25,29,29,90],EDIT)),
        ("ESCALAS",excel.basic_sheet(RUBRIC,[29,118]))
    ]
    out_private.mkdir(parents=True,mode=0o700)
    os.chmod(out_private,0o700)
    path=out_private/"Conciliacion_Metodologica_Fase26.xlsx"
    pack.xlsx_generic(path,tabs,excel)
    safe={
        "generated_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
        "status":"private_methodological_reconciliation_packet_prepared_NO_new_human_decisions",
        "cases":len(rows),
        "source":"original Phase21 A/B, original Phase23 consensus, original independent Phase24 QA, later posthoc-corrected QA",
        "mismatch_counts":dict(stats),
        "original_Phase25_source_integrity_reverified":True,
        "panel_decisions_filled":0,
        "required_panel_decision_fields_per_record":4,
        "limitations":[
            "A methods panel must apply a consistent written codebook, verify evidence, and explain differences; no automatic consensus is generated.",
            "The original QA policy categories were corrected after independent rating; their posthoc normalized version is NOT a second independent rating.",
            "The selected QA sample of 80 was deliberately risk-enriched, not population representative.",
            "Final Phase23 design-based estimates should not be presented unqualified without resolution of systematic codebook differences.",
            "No original sample IDs, OpenAlex IDs, machine predictions, stratum identities, document-level ratings, titles, abstracts or notes are published."
        ]
    }
    out_public.mkdir(parents=True,exist_ok=True)
    (out_public/"panel_reconciliation_preparation_aggregate.json").write_text(
        json.dumps(safe,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    (out_public/"summary.md").write_text(
        "# Phase26 — Methods panel reconciliation packet\n\n"
        "Status: "+safe["status"]+"\n\nCases: 80\n\n"+
        "Misclassification indicators are differences with human consensus, NOT objective errors.\n\n"+
        json.dumps(safe["mismatch_counts"],indent=2)+"\n\n"+
        "All records and the panel's workbook are PRIVATE, outside GitHub.\n\n"+
        "\n".join("- "+x for x in safe["limitations"])+"\n",encoding="utf8")
    print("PHASE26",safe["status"])
    print("Cases:",len(rows),
          "relevance mismatches:",stats["mismatch_relevance"],
          "discipline mismatches:",stats["mismatch_discipline"],
          "posthoc-policy mismatches:",stats["mismatch_policy"])
    print("PRIVATE CASEBOOK:",path)
    print("PUBLIC COUNT ONLY:",out_public/"summary.md")
    print("No new consensus was generated; no private ratings, model keys or texts exported")


if __name__=="__main__":
    main()
