#!/usr/bin/env python3
"""Phase20 — Phase05 independent screening coding as PRIVATE Excel workbooks.

Export two researcher-friendly XLSX files, or import returned XLSX safely
back into protected Phase05 CSV files. No automatic judgment is generated.
No private titles, abstracts, IDs, labels or comments enter public GitHub.
Uses the tested XML Excel helper (Phase17) and private packaging (Phase18).
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import os
from pathlib import Path
import shutil
import zipfile

FIELDS = ["sample_id","title","abstract","publication_year","type",
          "relevance_code","discipline_code","primary_policy_code","reason"]
HEADERS = ["Código de muestra","Título","Resumen","Año","Tipo",
           "Relevancia de IA/política (0,1,2,3,9)",
           "Disciplina","Dimensión principal de política","Justificación / evidencia"]
FIELD_EDIT = {
    5:["0","1","2","3","9"],
    6:["ssh","engineering","health_sciences","general_he","uncertain"],
    7:["teaching_learning","assessment","ethics_integrity",
       "governance_policy","research_scholarship","ai_literacy_training",
       "equity_access","privacy_security","general_policy",
       "not_applicable","uncertain"],
    8:None
}
INTRO = [
    ("Evaluador asignado","{REVIEWER}"),
    ("Objetivo","Verificar de manera INDEPENDIENTE el cribado y la clasificación de publicaciones sobre IA y políticas en educación superior."),
    ("Estudio ciego","Los libros NO muestran las predicciones computacionales ni estratos. No consulte el libro del otro evaluador."),
    ("PASO 1","Abra CRIBADO; revise título, resumen, año y tipo de cada uno de los 368 registros."),
    ("PASO 2","Asigne la relevancia: 0 fuera de IA en educación superior; 1 IA en educación superior sin política clara; 2 pertinencia indirecta; 3 política/gobernanza directamente estudiada; 9 insuficiente evidencia."),
    ("PASO 3","Asigne una disciplina principal y una dimensión principal de política mediante los menús desplegables. Si es insuficiente, elija uncertain."),
    ("PASO 4","En JUSTIFICACIÓN añada evidencia breve; especifique casos ambiguos, insuficiencia de resumen y razones para decisiones de relevancia 0 o 9."),
    ("PASO 5","No infiera políticas únicamente porque un artículo mencione ChatGPT; distinga uso de IA, implicaciones institucionales y estudio de política."),
    ("PASO 6","Edite ÚNICAMENTE las cuatro columnas amarillas. No modifique títulos, resúmenes, tipos, años, códigos, encabezados ni filas."),
    ("PASO 7","Use la pestaña ESCALAS para definiciones exactas. Los valores literales en inglés de los desplegables son necesarios para el análisis HPC."),
    ("PASO 8","Si considera que necesita texto completo para decidir, asigne 9 y descríbalo en la justificación; no invente evidencia del cuerpo."),
    ("ENTREGA","Guarde el MISMO libro .xlsx y devuélvalo de forma privada. No hace falta escribir código, calcular estadísticas ni presentar otro informe."),
    ("PRIVACIDAD","Este libro contiene títulos y resúmenes de la muestra: NO subir a GitHub ni a repositorios públicos."),
    ("CONTROL","Deben conservarse los 368 registros, con los mismos identificadores y el mismo orden."),
]
RUBRIC = [
    ("0","Fuera de investigaciones de IA en educación superior"),
    ("1","IA en educación superior sin relevancia política justificable"),
    ("2","IA con implicación indirecta para políticas de educación superior"),
    ("3","Investigación que estudia directamente políticas, reglas, gobernanza, regulación o salvaguardas"),
    ("9","Información insuficiente para concluir"),
    ("ssh","Ciencias sociales y humanidades"),
    ("engineering","Ingeniería / tecnología"),
    ("health_sciences","Ciencias de la salud"),
    ("general_he","Educación superior general/interdisciplinar"),
    ("uncertain","Disciplina o dimensión insuficientemente determinada"),
    ("teaching_learning","Enseñanza y aprendizaje"),
    ("assessment","Evaluación educativa"),
    ("ethics_integrity","Ética e integridad académica"),
    ("governance_policy","Gobernanza y políticas institucionales/públicas"),
    ("research_scholarship","Investigación y trabajo académico"),
    ("ai_literacy_training","Alfabetización y capacitación en IA"),
    ("equity_access","Equidad y acceso"),
    ("privacy_security","Privacidad y seguridad"),
    ("general_policy","Implicaciones generales de política"),
    ("not_applicable","No se identifica dimensión de política aplicable"),
]


def load_helper(filename,module_name):
    p=Path(__file__).resolve().parent/filename
    spec=importlib.util.spec_from_file_location(module_name,p)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def csv_load(path):
    with path.open(encoding="utf-8-sig",newline="") as f:
        records=list(csv.DictReader(f))
    if len(records)!=368:
        raise ValueError("Unexpected Phase05 row count: expected 368")
    ids=[r["sample_id"] for r in records]
    if len(set(ids))!=368 or any(not x for x in ids):
        raise ValueError("Missing/duplicate blinded sample identifiers")
    if any(set(rec)!=set(FIELDS) for rec in records):
        raise ValueError("Unexpected Phase05 source columns")
    return records


def save_csv(path,records):
    temp=path.with_name(path.name+".writing")
    with temp.open("w",encoding="utf-8-sig",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(records)
    os.chmod(temp,0o600)
    os.replace(temp,path)


def workbook_file(out,name,rater,records):
    excel=load_helper("17_excel_reviewer_packages.py","excel_phase20")
    phases=load_helper("18_prepare_blinded_adjudication_excel.py","package_phase20")
    ins=[["INSTRUCCIONES DE CRIBADO","Qué hacer"]]
    ins += [[key,value.replace("{REVIEWER}",rater.upper())] for key,value in INTRO]
    scale=[["CÓDIGO","SIGNIFICADO"]]+[list(x) for x in RUBRIC]
    tabs=[
        ("INSTRUCCIONES",excel.basic_sheet(ins,[35,113])),
        ("CRIBADO",excel.section_xml("DOCUMENTOS",FIELDS,HEADERS,records,
            [16,57,107,16,24,25,24,33,72],FIELD_EDIT)),
        ("ESCALAS",excel.basic_sheet(scale,[31,115]))
    ]
    phases.xlsx_generic(out,tabs,excel)


def read_returned(path,expected_rater):
    if not path.is_file() or path.stat().st_size>40_000_000:
        raise ValueError("Returned workbook not found or too large")
    excel=load_helper("17_excel_reviewer_packages.py","excel_phase20_import")
    with zipfile.ZipFile(path) as z:
        if sum(i.file_size for i in z.infolist())>180_000_000:
            raise ValueError("Excessive uncompressed workbook size")
        required={f"xl/worksheets/sheet{i}.xml" for i in (1,2,3)}
        if not required.issubset(z.namelist()):
            raise ValueError("Expected original three-tab XLSX workbook")
        shared=[]
        if "xl/sharedStrings.xml" in z.namelist():
            import xml.etree.ElementTree as ET
            root=ET.fromstring(z.read("xl/sharedStrings.xml"))
            shared=["".join(t.text or "" for t in si.findall(f".//{{{excel.NS}}}t"))
                    for si in root.findall(f"{{{excel.NS}}}si")]
        instructions=excel.xlsx_sheet(z,"xl/worksheets/sheet1.xml",shared)
        if len(instructions)<2 or instructions[1].get(1,"").strip().upper()!=expected_rater.upper():
            raise ValueError("Returned workbook belongs to other evaluator")
        data=excel.xlsx_sheet(z,"xl/worksheets/sheet2.xml",shared)
        if not data or [data[0].get(i,"") for i in range(len(FIELDS))]!=HEADERS:
            raise ValueError("Unexpected/changed screening worksheet headers")
        result=[]
        for row in data[1:]:
            if any(str(v).strip() for v in row.values()):
                if any(k>=len(FIELDS) and str(v).strip() for k,v in row.items()):
                    raise ValueError("Unexpected additional screening columns")
                result.append(dict(zip(FIELDS,[str(row.get(i,"")) for i in range(len(FIELDS))])))
        return result


def compare(original,returned):
    indexed={r["sample_id"]:r for r in original}
    if len(returned)!=len(original):
        raise ValueError("Screening workbook row count changed")
    observed=set()
    validated=[]
    for row in returned:
        sample_id=row["sample_id"]
        if sample_id in observed or sample_id not in indexed:
            raise ValueError("Missing, duplicated or modified sample identifiers")
        observed.add(sample_id)
        reference=indexed[sample_id]
        for field in FIELDS[:5]:
            if row[field]!=reference[field]:
                raise ValueError("Title, abstract, publication year, type or code changed")
        result=reference.copy()
        for i in (5,6,7,8):
            field=FIELDS[i]
            value=row[field].strip()
            valid=FIELD_EDIT[i]
            if value and valid is not None and value not in valid:
                raise ValueError("Invalid human screening code in "+field)
            result[field]=value
        validated.append(result)
    if observed!=set(indexed):
        raise ValueError("Some Phase05 sampled records missing")
    return validated


def export(private,out):
    if out.exists() and any(out.iterdir()):
        raise ValueError("Excel export target must be an unused private folder")
    for rater in ("a","b"):
        if not (private/f"rater_{rater}.csv").is_file():
            raise FileNotFoundError("Missing Phase05 prepared reviewer CSV")
    if not (private/"sampling_key.csv").is_file():
        raise FileNotFoundError("Missing protected Phase05 machine/stratum key")
    out.mkdir(parents=True,mode=0o700)
    os.chmod(out,0o700)
    for rater in ("a","b"):
        workbook_file(out,f"Cribado_{rater.upper()}.xlsx",rater,
                      csv_load(private/f"rater_{rater}.csv"))
    (out/"LEER_ANTES_DE_ENVIAR.txt").write_text(
        "Enviar SOLO Cribado_A.xlsx al evaluador A y Cribado_B.xlsx al B. "
        "No compartir sampling_key.csv ni etiquetas automáticas. "
        "Cada libro tiene instrucciones, 368 publicaciones y escalas. "
        "No subir XLSX a GitHub.\n",encoding="utf8")
    print("PHASE20 prepared two private screening Excel books")
    print("Evaluator A:",out/"Cribado_A.xlsx")
    print("Evaluator B:",out/"Cribado_B.xlsx")
    print("368 items per reviewer. No human responses created.")


def import_rater(private,out,received,rater):
    master=csv_load(private/f"rater_{rater}.csv")
    incoming=read_returned(received,rater)
    converted=compare(master,incoming)
    if out.exists() and not out.is_dir():
        raise ValueError("Output path is not a directory")
    out.mkdir(parents=True,exist_ok=True,mode=0o700)
    os.chmod(out,0o700)
    for name in ("sampling_key.csv","rater_a.csv","rater_b.csv"):
        dst=out/name
        if not dst.exists():
            shutil.copy2(private/name,dst)
            os.chmod(dst,0o600)
    path=out/f"rater_{rater}.csv"
    current=csv_load(path)
    if current!=master and current!=converted:
        raise ValueError("This rater has previous different imported responses. Use a new destination.")
    save_csv(path,converted)
    completed=sum(all(row[f].strip() for f in FIELDS[5:]) for row in converted)
    print("PHASE20 imported reviewer",rater.upper(),"; complete rows:",completed,"/368")
    print("Protected normalized CSV stored:",path)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--mode",choices=["export","import"],required=True)
    p.add_argument("--private-in",default=str(Path.home()/"ai_policy_validation_private"))
    p.add_argument("--out-dir",required=True)
    p.add_argument("--rater",choices=["a","b"])
    p.add_argument("--received-xlsx")
    args=p.parse_args()
    private=Path(args.private_in).expanduser().resolve()
    out=Path(args.out_dir).expanduser().resolve()
    repo=Path.home()/"AI_policy"
    if not private.is_dir():
        p.error("Phase05 private validation input folder not found")
    if out==private or private in out.parents or out in private.parents or \
       out==repo or repo in out.parents:
        p.error("Output must be a separate PRIVATE folder outside GitHub")
    if args.mode=="export":
        export(private,out)
    else:
        if not args.rater or not args.received_xlsx:
            p.error("Import requires --rater and --received-xlsx")
        received=Path(args.received_xlsx).expanduser().resolve()
        if not received.is_file():
            p.error("Returned screening Excel does not exist")
        import_rater(private,out,received,args.rater)


if __name__=="__main__":
    main()
