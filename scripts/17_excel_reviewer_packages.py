#!/usr/bin/env python3
"""Phase 17: give nontechnical reviewers TWO ready-to-fill XLSX workbooks.

Modes:
  export: private Phase15 CSV -> Evaluador_A.xlsx / Evaluador_B.xlsx
  import: returned XLSX -> protected standardized Phase16 CSV staging area

No third-party packages. XLSX is a standard Office Open XML zip container.
All source excerpts, article IDs and rated rows stay OUTSIDE GitHub.
The model-to-group private sampling key is NEVER included in reviewer books.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
import re
import shutil
from xml.sax.saxutils import escape
import xml.etree.ElementTree as ET
import zipfile

GROUP_FIELDS = [
    "group_code","topic_name_proposed","topic_coherence_1_to_5",
    "distinctiveness_1_to_5","direct_policy_relevance_0_to_3_or_9",
    "confidence_1_to_5","reviewer_comments"
]
DOC_FIELDS = [
    "group_code","item_code",
    "belongs_to_one_coherent_theme_0_no_1_yes_9_uncertain",
    "policy_relevance_0_to_3_or_9_uncertain",
    "title","abstract","body_excerpt_A","body_excerpt_B","document_comments"
]
GROUP_HEADERS = [
    "Código grupo","Nombre del tema propuesto","Coherencia (1–5)",
    "Diferenciación (1–5)","Pertinencia política (0–3 o 9)",
    "Confianza (1–5)","Justificación / comentarios"
]
DOC_HEADERS = [
    "Código grupo","Código documento","¿Pertenece al tema? (0,1,9)",
    "Pertinencia política (0–3,9)","Título","Resumen",
    "Extracto cuerpo A","Extracto cuerpo B","Justificación / comentarios"
]
RUBRIC = [
    ("Pertinencia 0","Ajeno a IA en educación superior"),
    ("Pertinencia 1","IA educativa, sin dimensión de política claramente identificada"),
    ("Pertinencia 2","Implicación indirecta para políticas institucionales o públicas"),
    ("Pertinencia 3","Relación directa con gobernanza, regulación, normas o política"),
    ("Pertinencia 9","No hay evidencia suficiente para decidir"),
    ("Pertenencia 0","El documento NO corresponde al tema que propone el evaluador"),
    ("Pertenencia 1","El documento SÍ corresponde al tema propuesto"),
    ("Pertenencia 9","No es posible juzgar con la información disponible"),
    ("Coherencia 1–5","1 sin tema compartido; 3 moderada; 5 clara, específica y consistente"),
    ("Diferenciación 1–5","1 solapa otros grupos; 3 moderada; 5 claramente distinta"),
    ("Confianza 1–5","1 confianza baja; 5 confianza alta"),
]
INSTRUCTIONS = [
    ("Evaluador asignado","{PERSON}"),
    ("Objeto","Evaluación ciega de temas en políticas de IA en educación superior."),
    ("ANTES DE EMPEZAR","Trabaje independientemente. No consulte otros evaluadores ni solicite la clave del modelo."),
    ("1. DOCUMENTOS","Abra DOCUMENTOS. Filtre por Código grupo y lea los 7 artículos del mismo código."),
    ("2. EVIDENCIA","Lea título, resumen y extractos orientativos del cuerpo. Pueden existir errores de extracción."),
    ("3. GRUPOS","En GRUPOS, proponga un nombre temático para el grupo y complete coherencia, diferenciación, pertinencia y confianza."),
    ("4. PERTENENCIA","Vuelva a DOCUMENTOS y valore cada publicación en relación con el nombre temático que propuso."),
    ("5. SOLO AMARILLO","Complete las celdas amarillas. No modifique códigos, títulos, resúmenes, extractos, filas ni columnas."),
    ("6. LISTAS","Use las listas desplegables. 9 significa información insuficiente, NO puntuación máxima."),
    ("7. COMENTARIOS","Justifique dudas, documentos fuera de tema, errores de extracción y nombres ambiguos."),
    ("8. DIFERENCIACIÓN","La escala de diferenciación requiere comparar los grupos entre sí antes de terminar."),
    ("9. GUARDAR","Guarde este mismo archivo en formato .xlsx; no lo convierta a PDF ni CSV."),
    ("10. DEVOLVER","Entregue el Excel al coordinador por un canal privado, no por GitHub."),
    ("CONTROL","Cada evaluador tiene 48 grupos y 336 publicaciones; 7 ejemplos por grupo."),
    ("ESCALAS","La pestaña ESCALAS define los valores permitidos en cada calificación."),
]
REV_SECTION = {"documents":("DOCUMENTOS",DOC_FIELDS,DOC_HEADERS),
               "topics":("GRUPOS",GROUP_FIELDS,GROUP_HEADERS)}
EDITABLE = {
    "DOCUMENTOS": {2:["0","1","9"], 3:["0","1","2","3","9"], 8:None},
    "GRUPOS": {1:None,2:["1","2","3","4","5"],3:["1","2","3","4","5"],
               4:["0","1","2","3","9"],5:["1","2","3","4","5"],6:None},
}
NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def xmltext(value):
    value="" if value is None else str(value)
    value=re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", value)
    return escape(value[:32767], {'"':"&quot;"})


def column(n):
    out=""
    n+=1
    while n:
        n,j=divmod(n-1,26)
        out=chr(j+65)+out
    return out


def cell(ref, value, style):
    return (f'<c r="{ref}" s="{style}" t="inlineStr"><is><t xml:space="preserve">'
            f'{xmltext(value)}</t></is></c>')


def section_xml(name, fields, headers, records, widths, editable):
    nrows=len(records)+1
    ncols=len(fields)
    cols="".join(
        f'<col min="{j+1}" max="{j+1}" width="{width}" customWidth="1"/>'
        for j,width in enumerate(widths)
    )
    body=[]
    header_cells="".join(cell(f"{column(j)}1",head,1) for j,head in enumerate(headers))
    body.append(f'<row r="1" ht="32" customHeight="1">{header_cells}</row>')
    for i,rec in enumerate(records,2):
        group_code=rec["group_code"]
        group_num=int(re.search(r"\d+",group_code).group()) if re.search(r"\d+",group_code) else 0
        base_style=4 if group_num%2==0 else 2
        cells=[]
        for j,field in enumerate(fields):
            style=3 if j in editable else (5 if field in ("group_code","item_code") else base_style)
            cells.append(cell(f"{column(j)}{i}",rec.get(field,""),style))
        height=72 if name=="DOCUMENTOS" else 40
        body.append(f'<row r="{i}" ht="{height}" customHeight="1">'+
                    "".join(cells)+"</row>")
    validations=[]
    for j,allowed in editable.items():
        if allowed is None:
            continue
        values=",".join(allowed)
        sq=f"{column(j)}2:{column(j)}{nrows}"
        validations.append(
            f'<dataValidation type="list" allowBlank="1" showDropDown="0" '
            f'showInputMessage="1" showErrorMessage="1" errorStyle="stop" '
            f'errorTitle="Escala inválida" error="Seleccione un valor de la lista" '
            f'promptTitle="Campo de evaluación" prompt="Use las opciones del desplegable" '
            f'sqref="{sq}"><formula1>&quot;{xmltext(values)}&quot;</formula1></dataValidation>'
        )
    dv=(f'<dataValidations count="{len(validations)}">'+
        "".join(validations)+'</dataValidations>') if validations else ""
    end=f"{column(ncols-1)}{nrows}"
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<worksheet xmlns="{NS}"><dimension ref="A1:{end}"/>'
        f'<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" '
        f'activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>'
        f'<sheetFormatPr defaultRowHeight="17"/>'
        f'<cols>{cols}</cols><sheetData>{"".join(body)}</sheetData>'
        f'<autoFilter ref="A1:{end}"/>{dv}</worksheet>')


def basic_sheet(rows,widths):
    nrows=len(rows);ncols=max(len(x) for x in rows)
    cols="".join(f'<col min="{i+1}" max="{i+1}" width="{w}" customWidth="1"/>'
                 for i,w in enumerate(widths))
    lines=[]
    for i,row in enumerate(rows,1):
        h=33 if i==1 else 54
        style=1 if i==1 else (6 if i in (4,5) else 0)
        lines.append(f'<row r="{i}" ht="{h}" customHeight="1">'+
                     "".join(cell(f"{column(j)}{i}",v,style) for j,v in enumerate(row))+
                     '</row>')
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<worksheet xmlns="{NS}"><sheetViews><sheetView workbookViewId="0"/>'
            f'</sheetViews><sheetFormatPr defaultRowHeight="17"/>'
            f'<cols>{cols}</cols><sheetData>{"".join(lines)}</sheetData></worksheet>')


def styles_xml():
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <styleSheet xmlns="{NS}">
    <fonts count="3">
      <font><sz val="10"/><name val="Aptos"/><color rgb="FF17212E"/></font>
      <font><b/><sz val="11"/><name val="Aptos"/><color rgb="FFFFFFFF"/></font>
      <font><b/><sz val="10"/><name val="Aptos"/><color rgb="FF0F566D"/></font>
    </fonts>
    <fills count="5">
      <fill><patternFill patternType="none"/></fill>
      <fill><patternFill patternType="gray125"/></fill>
      <fill><patternFill patternType="solid"><fgColor rgb="FF17365D"/></patternFill></fill>
      <fill><patternFill patternType="solid"><fgColor rgb="FFF8F3D8"/></patternFill></fill>
      <fill><patternFill patternType="solid"><fgColor rgb="FFF0F5F8"/></patternFill></fill>
    </fills>
    <borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
    <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
    <cellXfs count="7">
      <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" applyAlignment="1"><alignment wrapText="1" vertical="top"/></xf>
      <xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyAlignment="1"><alignment wrapText="1" vertical="center"/></xf>
      <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" applyAlignment="1"><alignment wrapText="1" vertical="top"/></xf>
      <xf numFmtId="0" fontId="0" fillId="3" borderId="0" xfId="0" applyAlignment="1"><alignment wrapText="1" vertical="top"/></xf>
      <xf numFmtId="0" fontId="0" fillId="4" borderId="0" xfId="0" applyAlignment="1"><alignment wrapText="1" vertical="top"/></xf>
      <xf numFmtId="0" fontId="2" fillId="4" borderId="0" xfId="0" applyAlignment="1"><alignment wrapText="1" vertical="top"/></xf>
      <xf numFmtId="0" fontId="2" fillId="0" borderId="0" xfId="0" applyAlignment="1"><alignment wrapText="1" vertical="top"/></xf>
    </cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
    </styleSheet>'''


def build_book(dest, reviewer, docs, topics):
    ins=[["INSTRUCCIONES DEL EVALUADOR","Qué hacer en el Excel"]]
    ins.extend([[label, value.replace("{PERSON}",reviewer)] for label,value in INSTRUCTIONS])
    tabs=[
        ("INSTRUCCIONES",basic_sheet(ins,[29,111])),
        ("DOCUMENTOS",section_xml("DOCUMENTOS",DOC_FIELDS,DOC_HEADERS,docs,
            [16,19,24,25,42,65,61,61,43],EDITABLE["DOCUMENTOS"])),
        ("GRUPOS",section_xml("GRUPOS",GROUP_FIELDS,GROUP_HEADERS,topics,
            [16,52,23,25,27,20,68],EDITABLE["GRUPOS"])),
        ("ESCALAS",basic_sheet([["ESCALA","DEFINICIÓN"]]+[list(x) for x in RUBRIC],[30,105]))
    ]
    rootrels='''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
    Target="xl/workbook.xml"/></Relationships>'''
    sheets="".join(f'<sheet name="{name}" sheetId="{i}" r:id="rId{i}"/>'
                   for i,(name,_) in enumerate(tabs,1))
    book=f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="{NS}" xmlns:r="{REL}"><sheets>{sheets}</sheets></workbook>'
    links="".join(f'<Relationship Id="rId{i}" Type="{REL}/worksheet" '
                  f'Target="worksheets/sheet{i}.xml"/>' for i in range(1,len(tabs)+1))
    linkxml=(f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships '
             f'xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{links}'
             f'<Relationship Id="rId5" Type="{REL}/styles" Target="styles.xml"/>'
             f'</Relationships>')
    overrides="".join(f'<Override PartName="/xl/worksheets/sheet{i}.xml" '
                       f'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                       for i in range(1,len(tabs)+1))
    types=(f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types '
           f'xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
           f'<Default Extension="xml" ContentType="application/xml"/>'
           f'<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
           f'<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
           f'<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
           f'{overrides}</Types>')
    with zipfile.ZipFile(dest,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=7) as z:
        for name,payload in {
            "[Content_Types].xml":types,
            "_rels/.rels":rootrels,
            "xl/workbook.xml":book,
            "xl/_rels/workbook.xml.rels":linkxml,
            "xl/styles.xml":styles_xml(),
        }.items():
            z.writestr(name,payload)
        for i,(_,xml) in enumerate(tabs,1):
            z.writestr(f"xl/worksheets/sheet{i}.xml",xml)
    os.chmod(dest,0o600)
    with zipfile.ZipFile(dest) as z:
        if z.testzip() is not None:
            raise ValueError("Generated workbook integrity check failed")


def read_csv(path):
    with path.open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, fields, rows):
    tmp=path.with_name(path.name+".writing")
    with tmp.open("w",encoding="utf-8-sig",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    os.chmod(tmp,0o600)
    os.replace(tmp,path)


def getcell(node, shared):
    t=node.get("t","")
    if t=="inlineStr":
        return "".join(v.text or "" for v in node.findall(f".//{{{NS}}}t"))
    if t=="s":
        v=node.find(f"{{{NS}}}v")
        return shared[int(v.text)] if v is not None and v.text else ""
    v=node.find(f"{{{NS}}}v")
    if v is None: return ""
    return v.text or ""


def xlsx_sheet(z,path,shared):
    root=ET.fromstring(z.read(path))
    rows=[]
    for row in root.findall(f".//{{{NS}}}sheetData/{{{NS}}}row"):
        cols={}
        for c in row.findall(f"{{{NS}}}c"):
            ref=c.get("r","")
            m=re.match(r"^([A-Z]+)\d+$",ref)
            if not m: continue
            ci=0
            for letter in m.group(1): ci=ci*26+ord(letter)-64
            cols[ci-1]=getcell(c,shared)
        rows.append(cols)
    return rows


def imported_sections(path, reviewer):
    if path.stat().st_size>40_000_000:
        raise ValueError("Unexpectedly large workbook")
    with zipfile.ZipFile(path) as z:
        if sum(v.file_size for v in z.infolist())>180_000_000:
            raise ValueError("Workbook uncompressed data too large")
        necessary={f"xl/worksheets/sheet{i}.xml" for i in range(1,5)}
        if not necessary.issubset(set(z.namelist())):
            raise ValueError("Workbook tabs missing: resend original Excel template")
        shared=[]
        if "xl/sharedStrings.xml" in z.namelist():
            node=ET.fromstring(z.read("xl/sharedStrings.xml"))
            shared=["".join(x.text or "" for x in si.findall(f".//{{{NS}}}t"))
                    for si in node.findall(f"{{{NS}}}si")]
        guide=xlsx_sheet(z,"xl/worksheets/sheet1.xml",shared)
        if len(guide)<2 or guide[1].get(1,"").strip().upper()!=reviewer.upper():
            raise ValueError("Workbook belongs to the OTHER evaluator")
        incoming={}
        for sec,order,path_part,headers in [
            ("documents",DOC_FIELDS,"xl/worksheets/sheet2.xml",DOC_HEADERS),
            ("topics",GROUP_FIELDS,"xl/worksheets/sheet3.xml",GROUP_HEADERS)
        ]:
            sheet=xlsx_sheet(z,path_part,shared)
            if not sheet or [sheet[0].get(i,"") for i in range(len(order))]!=headers:
                raise ValueError("Workbook header changed: restore the original Excel template")
            incoming[sec]=[
                {field:row.get(i,"") for i,field in enumerate(order)}
                for row in sheet[1:] if any(str(v).strip() for v in row.values())
            ]
        return incoming


def validate_return(submitted,source,fields,ratings,keys):
    lookup={}
    for row in source:
        key=tuple(row[k] for k in keys)
        if key in lookup: raise ValueError("Duplicate source key")
        lookup[key]=row
    encountered=set()
    result=[]
    for row in submitted:
        key=tuple(row[k] for k in keys)
        if key in encountered or key not in lookup:
            raise ValueError("Group/item codes changed, duplicated or missing")
        encountered.add(key)
        base=lookup[key].copy()
        for field in fields:
            value=str(row.get(field,""))
            if field in ratings:
                if ratings[field] is not None and value.strip() and value.strip() not in ratings[field]:
                    raise ValueError("Some rating cells contain invalid values; use only the dropdowns")
                base[field]=value.strip() if ratings[field] is not None else value.strip()
            elif value!=base[field]:
                raise ValueError("Evidence or group/item codes were changed; restore source text")
        result.append(base)
    if encountered!=set(lookup):
        raise ValueError("Rows were deleted or added; keep all original documents/groups")
    return result


def export_all(private,out):
    if not private.is_dir():
        raise FileNotFoundError("Phase15 private sampling folder not found")
    if out.exists() and any(out.iterdir()):
        raise ValueError("Export folder is not empty; choose an unused private folder")
    out.mkdir(parents=True,exist_ok=True,mode=0o700)
    os.chmod(out,0o700)
    for reviewer in ("a","b"):
        documents=read_csv(private/f"rater_{reviewer}_documents.csv")
        topics=read_csv(private/f"rater_{reviewer}_topics.csv")
        if len(documents)!=336 or len(topics)!=48:
            raise ValueError("Unexpected original Phase15 row counts")
        doc_groups={x["group_code"] for x in documents}
        if doc_groups!={x["group_code"] for x in topics}:
            raise ValueError("Topic/document groups do not match")
        documents.sort(key=lambda x:(x["group_code"],x["item_code"]))
        topics.sort(key=lambda x:x["group_code"])
        build_book(out/f"Evaluador_{reviewer.upper()}.xlsx",
                   reviewer.upper(),documents,topics)
    notice=(
        "ENTREGAR PRIVADAMENTE SOLO:\n"
        "Evaluador_A.xlsx al evaluador A, Evaluador_B.xlsx al evaluador B.\n\n"
        "Cada Excel contiene las hojas INSTRUCCIONES, DOCUMENTOS, GRUPOS, ESCALAS.\n"
        "La carpeta privada de Phase15 y private_sampling_key.csv NO se envian.\n"
        "El evaluador completa las celdas amarillas, guarda Excel y lo devuelve.\n"
        "NO subir ningun Excel a GitHub publico.\n"
    )
    file=out/"LEER_ANTES_DE_ENVIAR.txt"
    file.write_text(notice,encoding="utf8")
    os.chmod(file,0o600)
    print("EXPORTACIÓN COMPLETA: 2 Excel privados en",out)
    print("Evaluador_A.xlsx -> Evaluador A; Evaluador_B.xlsx -> Evaluador B")
    print("Cada uno contiene 48 grupos y 336 documentos, con instrucciones.")


def import_one(private,received,reviewer,out):
    incoming=imported_sections(received,reviewer)
    updates={}
    for section,fields,_ in [
        ("documents",DOC_FIELDS,DOC_HEADERS),
        ("topics",GROUP_FIELDS,GROUP_HEADERS)
    ]:
        source=read_csv(private/f"rater_{reviewer.lower()}_{section}.csv")
        keys=["group_code","item_code"] if section=="documents" else ["group_code"]
        keyfield="DOCUMENTOS" if section=="documents" else "GRUPOS"
        ratings={fields[i]:allowed for i,allowed in EDITABLE[keyfield].items()}
        updates[section]=validate_return(incoming[section],source,fields,ratings,keys)

    if out.exists() and not out.is_dir():
        raise ValueError("Import destination must be a directory")
    out.mkdir(parents=True,exist_ok=True,mode=0o700)
    os.chmod(out,0o700)
    for name in ("private_sampling_key.csv","private_validation_manifest.json"):
        dest=out/name
        if not dest.exists():
            shutil.copy2(private/name,dest)
            os.chmod(dest,0o600)
    for r in ("a","b"):
        for section in ("documents","topics"):
            dest=out/f"rater_{r}_{section}.csv"
            if not dest.exists():
                shutil.copy2(private/dest.name,dest)
                os.chmod(dest,0o600)
    for section,rows in updates.items():
        dest=out/f"rater_{reviewer.lower()}_{section}.csv"
        present=read_csv(dest)
        original=read_csv(private/dest.name)
        if present!=original and present!=rows:
            raise ValueError("This rater's imported ratings differ from an earlier import; use a new import folder")
    for section,rows in updates.items():
        dest=out/f"rater_{reviewer.lower()}_{section}.csv"
        write_csv(dest,DOC_FIELDS if section=="documents" else GROUP_FIELDS,rows)
    print("IMPORTACIÓN COMPLETA del evaluador",reviewer.upper())
    print("Calificaciones convertidas a CSV normalizado, solo en carpeta privada:",out)
    print("Cuando estén ambos evaluadores, ejecute Phase16 --private-in en ESTA carpeta.")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--mode",choices=["export","import"],required=True)
    p.add_argument("--private-in",default=str(Path.home()/"ai_policy_topic_validation_private"))
    p.add_argument("--out-dir",required=True)
    p.add_argument("--reviewer",choices=["a","b"])
    p.add_argument("--received-xlsx")
    args=p.parse_args()
    private=Path(args.private_in).expanduser().resolve()
    out=Path(args.out_dir).expanduser().resolve()
    repo=Path.home()/"AI_policy"
    if not private.is_dir():
        p.error("Original protected Phase15 files missing")
    if out==private or private in out.parents or out in private.parents or \
       out==repo or repo in out.parents:
        p.error("Output must be new, separate and OUTSIDE the GitHub repo")
    if args.mode=="export":
        export_all(private,out)
    else:
        if not args.reviewer or not args.received_xlsx:
            p.error("--reviewer and --received-xlsx required to import")
        received=Path(args.received_xlsx).expanduser().resolve()
        if not received.is_file():
            p.error("Returned Excel file not found")
        import_one(private,received,args.reviewer,out)


if __name__=="__main__":
    main()
