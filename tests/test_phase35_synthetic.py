#!/usr/bin/env python3
"""Synthetic-only Phase35 frame/rubric/privacy and weighted-uncertainty tests."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile

from test_phase28_synthetic import synthetic_frame

ROOT=Path(__file__).resolve().parents[1]
SOURCE30=ROOT/"scripts"/"30_prepare_full1200_validation.py"
SCRIPT=ROOT/"scripts"/"35_screen_vs_expert_weighted.py"
CODEBOOK=ROOT/"docs"/"phase30_full_validation_codebook_v1.0.md"
NS="http://schemas.openxmlformats.org/spreadsheetml/2006/main"


def run(command):
    return subprocess.run(command,capture_output=True,text=True)


def rating_source(original,dest,who,change_source=False):
    with zipfile.ZipFile(original) as src:
        with zipfile.ZipFile(dest,"w",compression=zipfile.ZIP_DEFLATED) as dst:
            for member in src.infolist():
                raw=src.read(member.filename)
                if member.filename=="xl/worksheets/sheet1.xml":
                    tree=ET.fromstring(raw)
                    for c in tree.findall(f".//{{{NS}}}c"):
                        if c.get("r")=="B1":
                            t=c.find(f"{{{NS}}}is/{{{NS}}}t")
                            if t is not None:
                                t.text=("PASADA IA-"+("1" if who=="A" else "2")
                                        +" — etiqueta remanente Claude, NO es una evaluación humana.")
                    raw=ET.tostring(tree,encoding="utf-8",xml_declaration=True)
                if member.filename=="xl/worksheets/sheet2.xml":
                    tree=ET.fromstring(raw)
                    for row in tree.findall(f".//{{{NS}}}sheetData/{{{NS}}}row"):
                        if int(row.get("r","0"))<2:continue
                        cells={c.get("r"):c for c in row.findall(f"{{{NS}}}c")}
                        n=int(next(c for c in cells if c.startswith("A"))[1:])
                        code=cells["A"+str(n)].find(f"{{{NS}}}is/{{{NS}}}t").text
                        num=int(code[3:])
                        relevance="9" if num<=74 else ("3" if num%13==0 else "2" if num%7==0 else "1")
                        scope="9" if relevance=="9" else "1"
                        new={
                          "F":scope,"G":relevance,
                          "H":("ethics_integrity" if who=="B" and 149<=num<=324 else "teaching_learning"),
                          "I":"general_he",
                          "J":"institutional policy test" if relevance in ("2","3") else "",
                          "K":"Synthetic source evidence for title and abstract",
                          "L":"yes" if num<=148 else "no",
                          "M":"Synthetic independent rating, not a real human response"
                        }
                        for prefix,value in new.items():
                            cell=cells[prefix+str(n)]
                            t=cell.find(f"{{{NS}}}is/{{{NS}}}t")
                            if t is not None:t.text=value
                        if change_source and num==1:
                            t=cells["B"+str(n)].find(f"{{{NS}}}is/{{{NS}}}t")
                            t.text="TAMPERED TITLE"
                    raw=ET.tostring(tree,encoding="utf-8",xml_declaration=True)
                dst.writestr(member,raw)


def panel_book(path):
    import importlib.util
    base=ROOT/"scripts"
    def mod(p,name):
        spec=importlib.util.spec_from_file_location(name,base/p)
        m=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m
    p32=mod("32_audit_pi_attested_human1200.py","phase35_fixture_32")
    e=mod("17_excel_reviewer_packages.py","phase35_fixture_excel")
    p=mod("18_prepare_blinded_adjudication_excel.py","phase35_fixture_pack")
    rows=[]
    for num in range(1,325):
        code=f"VAL{num:04d}"
        R="9" if num<=74 else ("3" if num%13==0 else "2" if num%7==0 else "1")
        S="9" if R=="9" else "1"
        row=dict.fromkeys(p32.FIELDS,"")
        row.update({
           "validation_code":code,"title":f"Synthetic title {code}",
           "abstract":f"Synthetic university-policy abstract {code}",
           "publication_year":"2026","type":"article",
           "scope_a":S,"scope_b":S,
           "relevance_a":R,"relevance_b":R,
           "topic_a":"teaching_learning",
           "topic_b":"ethics_integrity" if num>=149 else "teaching_learning",
           "discipline_a":"general_he","discipline_b":"general_he",
           "fulltext_a":"yes" if num<=148 else "no",
           "fulltext_b":"yes" if num<=148 else "no",
           "panel_scope":S,"panel_relevance":R,
           "panel_topic":"teaching_learning","panel_discipline":"general_he",
           "panel_evidence_reason":"Synthetic panel resolution based on tested rubric",
           "fulltext_escalation":"yes" if num<=148 else "no"
        })
        rows.append({"group_code":code,**row})
    sheet=e.section_xml("DOCUMENTOS",p32.FIELDS,p32.HEADERS,rows,
                        [25]*len(p32.FIELDS),{22:["0","1","9"],23:["0","1","2","3","9"],
                        24:["teaching_learning"],25:["general_he"],26:None,27:["yes","no"]})
    p.xlsx_generic(path,[
        ("INSTRUCCIONES",e.basic_sheet([["PANEL","Synthetic"]],[24,42])),
        ("DISCREPANCIAS",sheet),
        ("ESCALAS",e.basic_sheet([["SCALE","Synthetic"]],[24,42]))
    ],e)


class TestPhase35(unittest.TestCase):
    def test_strata_weighting_unknown_bounds_and_lineage(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            project,frame,key,phase05,old=synthetic_frame(root)
            source=root/"blank_source"
            phase30=root/"phase30_agg"
            p=run([sys.executable,str(SOURCE30),
                   "--project",str(project),
                   "--source-frame",str(frame),"--source-format","csv",
                   "--phase05-key",str(key),"--phase05-report",str(phase05),
                   "--codebook",str(CODEBOOK),"--private-out",str(source),
                   "--out",str(phase30)])
            self.assertEqual(p.returncode,0,p.stderr[-2000:])
            incoming=root/"private_received"
            incoming.mkdir()
            for who in ("A","B"):
                rating_source(source/f"Validacion_1200_{who}.xlsx",
                              incoming/f"submitted_{who}.xlsx",who)
            panel_dir=root/"private_panel"
            panel_dir.mkdir()
            panel=panel_dir/"panel.xlsx"
            # The panel's original bibliographic text MUST match the 1200
            # frozen source, not synthetic filler: replaced below.
            import importlib.util
            def mod(p,name):
                spec=importlib.util.spec_from_file_location(name,ROOT/"scripts"/p)
                m=importlib.util.module_from_spec(spec)
                spec.loader.exec_module(m)
                return m
            p32=mod("32_audit_pi_attested_human1200.py","p35fixture_reader")
            e=mod("17_excel_reviewer_packages.py","p35fixture_writer")
            pack=mod("18_prepare_blinded_adjudication_excel.py","p35fixture_pack")
            a=p32.readbook(incoming/"submitted_A.xlsx",mod("30_prepare_full1200_validation.py","p35p30").HEADERS,"A")["records"]
            b=p32.readbook(incoming/"submitted_B.xlsx",mod("30_prepare_full1200_validation.py","p35p30x").HEADERS,"B")["records"]
            rows=[]
            for num in range(1,325):
                code=f"VAL{num:04d}"
                x,y=a[code],b[code]
                out=dict.fromkeys(p32.FIELDS,"")
                out.update({
                    "validation_code":code,"title":x[1],"abstract":x[2],
                    "publication_year":x[3],"type":x[4],
                    "scope_a":x[5],"scope_b":y[5],
                    "relevance_a":x[6],"relevance_b":y[6],
                    "topic_a":x[7],"topic_b":y[7],
                    "discipline_a":x[8],"discipline_b":y[8],
                    "fulltext_a":x[11],"fulltext_b":y[11],
                    "panel_scope":x[5],"panel_relevance":x[6],
                    "panel_topic":"teaching_learning","panel_discipline":"general_he",
                    "panel_evidence_reason":"Synthetic documented specific reasoning",
                    "fulltext_escalation":"yes" if num<=148 else "no"
                })
                rows.append({"group_code":code,**out})
            sheet=e.section_xml("DOCUMENTOS",p32.FIELDS,p32.HEADERS,rows,
                [22]*len(p32.FIELDS),{22:["0","1","9"],23:["0","1","2","3","9"],
                24:["teaching_learning"],25:["general_he"],26:None,27:["yes","no"]})
            pack.xlsx_generic(panel,[("INSTRUCCIONES",e.basic_sheet(
                [["PANEL","Synthetic only"]],[24,48])),
                ("DISCREPANCIAS",sheet),
                ("ESCALAS",e.basic_sheet([["SCALE","Synthetic"]],[24,48]))],e)
            report32=root/"report32.json";report33=root/"report33.json"
            report32.write_text(json.dumps({
                "sample_n":1200,"original_phase30_source_integrity_verified":True
            }))
            report33.write_text(json.dumps({
                "casebook_n":324,"phase32_original_expert_labels_immutable":True,
                "panel_scientific_reason_diagnostics":{"residual":{
                    "uncertain_relevance_9":74,"requested_fulltext_yes":148
                }}
            }))
            out=root/"public_report"
            args=[sys.executable,str(SCRIPT),
                "--private-key",str(source/"private_sampling_key.csv"),
                "--original-a",str(source/"Validacion_1200_A.xlsx"),
                "--original-b",str(source/"Validacion_1200_B.xlsx"),
                "--returned-a",str(incoming/"submitted_A.xlsx"),
                "--returned-b",str(incoming/"submitted_B.xlsx"),
                "--manifest",str(source/"private_locked_manifest.json"),
                "--returned-panel",str(panel),
                "--phase30-report",str(phase30/"full_validation_packet_aggregate.json"),
                "--phase32-report",str(report32),
                "--phase33-report",str(report33),
                "--codebook",str(CODEBOOK),
                "--out",str(out)]
            p=run(args)
            self.assertEqual(p.returncode,0,p.stderr[-3500:])
            data=json.loads((out/"screening_vs_expert_weighted_aggregate.json").read_text())
            self.assertEqual(data["sample_n"],1200)
            self.assertEqual(data["panel_n"],324)
            self.assertEqual(data["AB_unanimous_not_on_panel_n"],876)
            self.assertEqual(data["residual_R9_uncertain_n"],74)
            self.assertEqual(data["fulltext_requested_not_completed_n"],148)
            self.assertAlmostEqual(
                sum(data["analysis"]["weighted_aggregated_cross_tabs"]["human_relevance_weighted"].values()),10283,
                delta=0.01)
            self.assertFalse(data["fulltext_review_done"])
            self.assertFalse(data["source_provenance_of_human_authorship_verified_independently"])
            self.assertNotIn("VAL0001",json.dumps(data))
            self.assertNotIn("Fictional publication",json.dumps(data))
            self.assertNotIn("Synthetic university-policy abstract",json.dumps(data))
            again=run(args)
            self.assertNotEqual(again.returncode,0)

if __name__=="__main__":
    unittest.main()
