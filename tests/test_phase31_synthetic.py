#!/usr/bin/env python3
"""Synthetic Phase31 test: two *AI-labeled* passes are NOT two human reviewers."""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile
import xml.etree.ElementTree as ET

from test_phase28_synthetic import synthetic_frame

ROOT=Path(__file__).resolve().parents[1]
PHASE30=ROOT/"scripts"/"30_prepare_full1200_validation.py"
PHASE31=ROOT/"scripts"/"31_audit_two_claude_passes.py"
CODEBOOK=ROOT/"docs"/"phase30_full_validation_codebook_v1.0.md"
NS="http://schemas.openxmlformats.org/spreadsheetml/2006/main"


def run(script,*args,success=True):
    p=subprocess.run([sys.executable,str(script),*map(str,args)],
        capture_output=True,text=True)
    if success and p.returncode:
        raise AssertionError(script.name+"\n"+p.stderr[-3200:])
    return p


def fill_source(original,target,who,tamper=False):
    with zipfile.ZipFile(original) as src:
        with zipfile.ZipFile(target,"w",compression=zipfile.ZIP_DEFLATED) as dst:
            for info in src.infolist():
                data=src.read(info.filename)
                if info.filename=="xl/worksheets/sheet1.xml":
                    root=ET.fromstring(data)
                    for cell in root.findall(f".//{{{NS}}}c"):
                        if cell.get("r")=="B1":
                            node=cell.find(f"{{{NS}}}is/{{{NS}}}t")
                            node.text=f"PASADA IA-{who} — clasificación generada por IA (Claude), NO es una evaluación humana."
                    data=ET.tostring(root,encoding="utf-8",xml_declaration=True)
                elif info.filename=="xl/worksheets/sheet2.xml":
                    root=ET.fromstring(data)
                    for row in root.findall(f".//{{{NS}}}sheetData/{{{NS}}}row"):
                        number=int(row.get("r","0"))
                        if number<2:continue
                        values={}
                        for cell in row.findall(f"{{{NS}}}c"):
                            ref=cell.get("r","")
                            if ref=="A"+str(number):
                                code=cell.find(f"{{{NS}}}is/{{{NS}}}t").text
                                n=int(code[3:])
                                scope="0" if n%7==0 else ("9" if n%37==0 else "1")
                                R=("0" if scope=="0" else "9" if scope=="9"
                                   else "3" if n%19==0 and not (who=="2" and n%5==0)
                                   else "2" if n%13==0 and not (who=="2" and n%5==0)
                                   else "1")
                                values={
                                  "F":scope,"G":R,
                                  "H":"not_applicable" if scope=="0" else "teaching_learning",
                                  "I":"general_he",
                                  "J":"Institutional policy under study" if R in ("2","3") else "",
                                  "K":"Synthetic evidence from title/abstract.",
                                  "L":"yes" if R=="9" else "no",
                                  "M":"A separate synthetic AI-pass judgment with a rationale"
                                }
                        for cell in row.findall(f"{{{NS}}}c"):
                            ref=cell.get("r","")
                            column="".join(ch for ch in ref if ch.isalpha())
                            node=cell.find(f"{{{NS}}}is/{{{NS}}}t")
                            if column in values and node is not None:
                                node.text=values[column]
                            if tamper and ref=="B2" and node is not None:
                                node.text="CORRUPTED BIBLIOGRAPHIC TITLE"
                    data=ET.tostring(root,encoding="utf-8",xml_declaration=True)
                dst.writestr(info,data)


class TestPhase31(unittest.TestCase):
    def test_two_claude_passes_remain_distinct_from_human_gold_standard(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            project,frame,key,phase05,old=synthetic_frame(root)
            private=root/"human_blank_private";public30=root/"phase30_aggregate"
            run(PHASE30,
                "--project",project,"--source-frame",frame,"--source-format","csv",
                "--phase05-key",key,"--phase05-report",phase05,
                "--codebook",CODEBOOK,"--private-out",private,"--out",public30)
            received=root/"ai_only_private";received.mkdir()
            for who,original in (("1","A"),("2","B")):
                fill_source(private/f"Validacion_1200_{original}.xlsx",
                            received/f"Claude_{who}.xlsx",who)
            out=root/"phase31_aggregate"
            args=[
                "--original-a",private/"Validacion_1200_A.xlsx",
                "--original-b",private/"Validacion_1200_B.xlsx",
                "--ai1",received/"Claude_1.xlsx",
                "--ai2",received/"Claude_2.xlsx",
                "--manifest",private/"private_locked_manifest.json",
                "--codebook",CODEBOOK,
                "--phase30-report",public30/"full_validation_packet_aggregate.json",
                "--out",out,
            ]
            run(PHASE31,*args)
            result=json.loads((out/"two_ai_runs_agreement_aggregate.json").read_text())
            self.assertEqual(result["n_records"],1200)
            self.assertEqual(result["status"],
                "two_Claude_AI_passes_audited_NOT_independent_human_validation")
            self.assertEqual(result["runs"]["AI1"]["rubric_validity"]["evidence_filled"],1200)
            self.assertTrue(result["source_original_phase30_template_verified"])
            self.assertLess(result["ai_to_ai_agreement"]["relevance_code"]["exact_agreement_n"],1200)
            self.assertNotIn("FAKE:screen_include_core",json.dumps(result))
            self.assertNotIn("VAL0001",json.dumps(result))
            self.assertNotIn("Synthetic evidence from title",json.dumps(result))
            # Rerun cannot overwrite existing AI audit.
            rerun=run(PHASE31,*args,success=False)
            self.assertNotEqual(rerun.returncode,0)

    def test_modified_original_evidence_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            project,frame,key,phase05,old=synthetic_frame(root)
            private=root/"blank";public30=root/"counts30"
            run(PHASE30,"--project",project,"--source-frame",frame,
                "--source-format","csv","--phase05-key",key,
                "--phase05-report",phase05,"--codebook",CODEBOOK,
                "--private-out",private,"--out",public30)
            received=root/"AI";received.mkdir()
            fill_source(private/"Validacion_1200_A.xlsx",received/"a.xlsx","1",tamper=True)
            fill_source(private/"Validacion_1200_B.xlsx",received/"b.xlsx","2")
            x=run(PHASE31,"--original-a",private/"Validacion_1200_A.xlsx",
                  "--original-b",private/"Validacion_1200_B.xlsx",
                  "--ai1",received/"a.xlsx","--ai2",received/"b.xlsx",
                  "--manifest",private/"private_locked_manifest.json",
                  "--codebook",CODEBOOK,
                  "--phase30-report",public30/"full_validation_packet_aggregate.json",
                  "--out",root/"counts31",success=False)
            self.assertNotEqual(x.returncode,0)
            self.assertIn("modified",x.stderr.lower())


if __name__=="__main__":
    unittest.main()
