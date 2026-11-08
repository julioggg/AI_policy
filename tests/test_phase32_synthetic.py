#!/usr/bin/env python3
"""Synthetic-only Phase32 provenance-conflict / original-evidence protection tests."""
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
S30=ROOT/"scripts"/"30_prepare_full1200_validation.py"
S32=ROOT/"scripts"/"32_audit_pi_attested_human1200.py"
CODEBOOK=ROOT/"docs"/"phase30_full_validation_codebook_v1.0.md"
NS="http://schemas.openxmlformats.org/spreadsheetml/2006/main"

def run(script,*args):
    return subprocess.run([sys.executable,str(script),*map(str,args)],
                          text=True,capture_output=True)

def fill(original,destination,role,tamper=False):
    with zipfile.ZipFile(original) as src:
        with zipfile.ZipFile(destination,"w",compression=zipfile.ZIP_DEFLATED) as dst:
            for entry in src.infolist():
                raw=src.read(entry.filename)
                if entry.filename=="xl/worksheets/sheet1.xml":
                    root=ET.fromstring(raw)
                    for c in root.findall(f".//{{{NS}}}c"):
                        ref=c.get("r")
                        if ref=="B1":
                            t=c.find(f"{{{NS}}}is/{{{NS}}}t")
                            if t is not None:
                                t.text=f"PASADA IA-{1 if role=='A' else 2} — clasificación generada por IA (Claude), NO es una evaluación humana."
                        if ref=="B2":
                            t=c.find(f"{{{NS}}}is/{{{NS}}}t")
                            if t is not None:
                                t.text="Pasada IA independiente para un experimento interno. No usar como evaluación de experto humano."
                    raw=ET.tostring(root,encoding="utf-8",xml_declaration=True)
                if entry.filename=="xl/worksheets/sheet2.xml":
                    root=ET.fromstring(raw)
                    for row in root.findall(f".//{{{NS}}}sheetData/{{{NS}}}row"):
                        i=int(row.get("r","0"))
                        if i<2:continue
                        val=(i-2)%13
                        scope="0" if val==0 else ("9" if val==12 else "1")
                        relevance=("0" if scope=="0" else "9" if scope=="9"
                                   else "3" if val==10 and role=="A"
                                   else "2" if val==7 else "1")
                        values={
                            "F":scope,"G":relevance,
                            "H":"not_applicable" if scope=="0" else "teaching_learning",
                            "I":"general_he" if role=="A" else (
                                "ssh" if val==4 else "general_he"),
                            "J":"institutional AI regulation" if relevance in ("2","3") else "",
                            "K":"Explicit evidence from synthetic university abstract.",
                            "L":"yes" if relevance=="9" else "no",
                            "M":"Independent synthetic rationale for testing; no actual humans involved"
                        }
                        for c in row.findall(f"{{{NS}}}c"):
                            ref=c.get("r","")
                            letter="".join(ch for ch in ref if ch.isalpha())
                            t=c.find(f"{{{NS}}}is/{{{NS}}}t")
                            if letter in values and t is not None:
                                t.text=values[letter]
                            if tamper and ref=="B2" and t is not None:
                                t.text="TAMPERED ORIGINAL ARTICLE"
                    raw=ET.tostring(root,encoding="utf-8",xml_declaration=True)
                dst.writestr(entry,raw)

class TestPhase32(unittest.TestCase):
    def test_conflicting_provenance_is_explicit_and_no_human_claim_automatically_verified(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            project,frame,key,phase05,old=synthetic_frame(root)
            private=root/"original"; public=root/"report30"
            p=run(S30,"--project",project,"--source-frame",frame,
                   "--source-format","csv","--phase05-key",key,
                   "--phase05-report",phase05,"--codebook",CODEBOOK,
                   "--private-out",private,"--out",public)
            self.assertEqual(p.returncode,0,p.stderr[-2500:])
            incoming=root/"returned";incoming.mkdir()
            for role in ("A","B"):
                fill(private/f"Validacion_1200_{role}.xlsx",
                     incoming/f"IA-{1 if role=='A' else 2}.xlsx",role)
            out=root/"phase32_public"
            packet=root/"phase32_private"
            base=[
                "--original-a",private/"Validacion_1200_A.xlsx",
                "--original-b",private/"Validacion_1200_B.xlsx",
                "--returned-a",incoming/"IA-1.xlsx",
                "--returned-b",incoming/"IA-2.xlsx",
                "--manifest",private/"private_locked_manifest.json",
                "--codebook",CODEBOOK,
                "--phase30-report",public/"full_validation_packet_aggregate.json",
                "--private-out",packet,"--out",out
            ]
            absent=run(S32,*base)
            self.assertNotEqual(absent.returncode,0)
            self.assertIn("Legacy AI/Claude metadata conflict",absent.stderr)
            scored=run(S32,*base,"--acknowledge-legacy-ai-metadata")
            self.assertEqual(scored.returncode,0,scored.stderr[-4000:])
            report=json.loads((out/"human_expert_agreement_aggregate.json").read_text())
            self.assertEqual(report["sample_n"],1200)
            self.assertEqual(report["reviewer_attribution"][
                "file_provenance_resolution"],"not_verified_by_automated_script")
            self.assertTrue(report["reviewer_attribution"][
                "both_returned_files_preserve_legacy_AI_Claude_notice"])
            self.assertFalse(report["classifier_accuracy_calculated"])
            self.assertEqual(report["human_disagreements_adjudicated"],0)
            self.assertTrue((packet/"Adjudicacion_Validacion_1200_Humana.xlsx").is_file())
            self.assertNotIn("FAKE:screen_include_core",json.dumps(report))
            self.assertNotIn("VAL0001",json.dumps(report))
            self.assertNotIn("TAMPERED",json.dumps(report))
            second=run(S32,*base,"--acknowledge-legacy-ai-metadata")
            self.assertNotEqual(second.returncode,0)

    def test_source_immutability_guard(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            project,frame,key,phase05,old=synthetic_frame(root)
            private=root/"original";public=root/"report30"
            p=run(S30,"--project",project,"--source-frame",frame,
                  "--source-format","csv","--phase05-key",key,
                  "--phase05-report",phase05,"--codebook",CODEBOOK,
                  "--private-out",private,"--out",public)
            self.assertEqual(p.returncode,0,p.stderr[-2500:])
            incoming=root/"returned";incoming.mkdir()
            fill(private/"Validacion_1200_A.xlsx",incoming/"IA1.xlsx","A",tamper=True)
            fill(private/"Validacion_1200_B.xlsx",incoming/"IA2.xlsx","B")
            p=run(S32,"--original-a",private/"Validacion_1200_A.xlsx",
                  "--original-b",private/"Validacion_1200_B.xlsx",
                  "--returned-a",incoming/"IA1.xlsx","--returned-b",incoming/"IA2.xlsx",
                  "--manifest",private/"private_locked_manifest.json",
                  "--codebook",CODEBOOK,
                  "--phase30-report",public/"full_validation_packet_aggregate.json",
                  "--private-out",root/"human_private","--out",root/"counts",
                  "--acknowledge-legacy-ai-metadata")
            self.assertNotEqual(p.returncode,0)
            self.assertIn("source",p.stderr.lower())


if __name__=="__main__":
    unittest.main()
