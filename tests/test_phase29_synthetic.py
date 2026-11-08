#!/usr/bin/env python3
"""Synthetic-only Phase29 independent pilot scoring integrity tests."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile

from test_phase28_synthetic import synthetic_frame, SCRIPT as PREP, CODEBOOK

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"29_score_independent_pilot.py"
NS="http://schemas.openxmlformats.org/spreadsheetml/2006/main"

def fill(original,returned,rater,partial=False,tamper=False):
    with zipfile.ZipFile(original) as src:
        with zipfile.ZipFile(returned,"w",compression=zipfile.ZIP_DEFLATED) as target:
            for member in src.infolist():
                blob=src.read(member.filename)
                if member.filename=="xl/worksheets/sheet2.xml":
                    root=ET.fromstring(blob)
                    for row in root.findall(f".//{{{NS}}}sheetData/{{{NS}}}row"):
                        rn=int(row.get("r","0"))
                        if rn<2:continue
                        code_node=next((c for c in row.findall(f"{{{NS}}}c")
                                        if c.get("r")==f"A{rn}"),None)
                        assert code_node is not None
                        code=code_node.find(f"{{{NS}}}is/{{{NS}}}t").text
                        number=int(code[3:])
                        scope="0" if number%5==0 else "1"
                        relevance="0" if scope=="0" else (
                            "3" if number%11==0 else
                            "2" if number%4==0 and rater=="A" else "1")
                        mechanism="Campus governance mechanism relevant to university policy" if relevance in ("2","3") else ""
                        cell_values={
                            "F":scope,"G":relevance,
                            "H":"not_applicable" if scope=="0" else "teaching_learning",
                            "I":"ssh" if number%8==0 and rater=="B" else "general_he",
                            "J":mechanism,
                            "K":"Source title and abstract support synthetic decision.",
                            "L":"no",
                            "M":"Document-specific independent justification, synthetic test."
                        }
                        if partial and rn==3 and rater=="B":
                            cell_values["M"]=""
                        for c in row.findall(f"{{{NS}}}c"):
                            ref=c.get("r","")
                            column="".join(v for v in ref if v.isalpha())
                            t=c.find(f"{{{NS}}}is/{{{NS}}}t")
                            if column in cell_values and t is not None:
                                t.text=cell_values[column]
                            if tamper and rn==2 and column=="B":
                                t.text="TAMPERED BIBLIOGRAPHY"
                    blob=ET.tostring(root,encoding="utf-8",xml_declaration=True)
                target.writestr(member,blob)

def scenario(partial=False,tamper=False):
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        project,frame,key,old_report,old=synthetic_frame(root)
        initial=root/"blinded";out28=root/"report28"
        run=subprocess.run([
            sys.executable,str(PREP),
            "--project",str(project),"--source-frame",str(frame),
            "--source-format","csv","--phase05-key",str(key),
            "--phase05-report",str(old_report),"--codebook",str(CODEBOOK),
            "--private-out",str(initial),"--out",str(out28)
        ],capture_output=True,text=True)
        if run.returncode:
            raise AssertionError(run.stderr[-2500:])
        returned=root/"returned_pilot";returned.mkdir()
        for who in ("A","B"):
            fill(initial/f"Piloto_V02_{who}.xlsx",
                 returned/f"Piloto_V02_{who}_COMPLETO.xlsx",who,
                 partial=partial,tamper=tamper)
        out29=root/"report29"
        command=[
            sys.executable,str(SCRIPT),
            "--original-a",str(initial/"Piloto_V02_A.xlsx"),
            "--original-b",str(initial/"Piloto_V02_B.xlsx"),
            "--returned-a",str(returned/"Piloto_V02_A_COMPLETO.xlsx"),
            "--returned-b",str(returned/"Piloto_V02_B_COMPLETO.xlsx"),
            "--manifest",str(initial/"pilot_locked_manifest.json"),
            "--codebook",str(CODEBOOK),
            "--phase28-report",str(out28/"pilot_preparation_aggregate.json"),
            "--out",str(out29),
        ]
        p=subprocess.run(command,capture_output=True,text=True)
        if tamper:
            selferror=p.returncode!=0 and "modified" in p.stderr.lower()
            assert selferror,p.stderr[-1000:]
            return None
        if p.returncode:
            raise AssertionError(p.stderr[-3000:])
        return json.loads((out29/"pilot_independent_agreement_aggregate.json").read_text())


class TestPilotScoring(unittest.TestCase):
    def test_full_two_rater_scoring_without_classifier_metrics(self):
        r=scenario()
        self.assertEqual(r["pilot_n"],30)
        self.assertEqual(r["status"],"two_independent_pilot_rounds_scored_calibration_required")
        self.assertEqual(r["result"]["relevance"]["n"],30)
        self.assertTrue(r["separate_rater_books_integrity_passed"])
        self.assertTrue(r["original_codebook_sha256_verified"])
        self.assertNotIn("precision",json.dumps(r))
        self.assertNotIn("FAKE:",json.dumps(r))
        self.assertNotIn("CAL001",json.dumps(r))

    def test_incomplete_form_is_not_mistaken_for_a_scored_pilot(self):
        r=scenario(partial=True)
        self.assertEqual(r["status"],"awaiting_completed_independent_pilot_review")
        self.assertIsNone(r["result"])
        self.assertEqual(r["missing_or_invalid_required_fields"]["b"]["reason"],1)

    def test_modified_source_evidence_is_rejected(self):
        scenario(tamper=True)


if __name__=="__main__":
    unittest.main()
