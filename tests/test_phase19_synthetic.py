#!/usr/bin/env python3
"""Synthetic, independent Phase19 import-readiness and adjudication tests."""
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

from test_phase16_synthetic import rows
from test_phase18_synthetic import set_rating

ROOT=Path(__file__).resolve().parents[1]
PHASE18=ROOT/"scripts"/"18_prepare_blinded_adjudication_excel.py"
PHASE19=ROOT/"scripts"/"19_analyze_completed_adjudication.py"
NS="http://schemas.openxmlformats.org/spreadsheetml/2006/main"


def execute(script,*args):
    p=subprocess.run([sys.executable,str(script),*map(str,args)],
        capture_output=True,text=True)
    if p.returncode:
        raise AssertionError(f"Failed synthetic {script.name}: "+p.stderr[-2000:])
    return p


def fill_workbook(original,returned,disputed):
    replacement={}
    for row in range(2,50):
        replacement.update({
            ("xl/worksheets/sheet2.xml",f"L{row}"):"AI governance topics",
            ("xl/worksheets/sheet2.xml",f"M{row}"):"4",
            ("xl/worksheets/sheet2.xml",f"N{row}"):"3",
            ("xl/worksheets/sheet2.xml",f"O{row}"):"2",
            ("xl/worksheets/sheet2.xml",f"P{row}"):"Evidence checked by adjudicator"
        })
    for row in range(2,disputed+2):
        replacement.update({
            ("xl/worksheets/sheet4.xml",f"M{row}"):"1",
            ("xl/worksheets/sheet4.xml",f"N{row}"):"3",
            ("xl/worksheets/sheet4.xml",f"O{row}"):"Independent evidence adjudicated"
        })
    with zipfile.ZipFile(original,"r") as zin:
        with zipfile.ZipFile(returned,"w",compression=zipfile.ZIP_DEFLATED) as zout:
            for info in zin.infolist():
                data=zin.read(info.filename)
                if info.filename.startswith("xl/worksheets/sheet") and info.filename.endswith(".xml"):
                    root=ET.fromstring(data)
                    for c in root.findall(f".//{{{NS}}}sheetData/{{{NS}}}row/{{{NS}}}c"):
                        value=replacement.get((info.filename,c.get("r")))
                        if value is not None:
                            t=c.find(f"{{{NS}}}is/{{{NS}}}t")
                            if t is None:
                                raise AssertionError("Synthetic cell not initialized")
                            t.text=value
                    data=ET.tostring(root,encoding="utf-8",xml_declaration=True)
                zout.writestr(info,data)


def sample_case(disputes,fill):
    with tempfile.TemporaryDirectory() as td:
        home=Path(td)
        original=home/"phase15"
        original.mkdir()
        normalized=home/"normalized"
        normalized.mkdir()
        rows(original,False)
        rows(normalized,True)
        if disputes:
            set_rating(normalized/"rater_b_documents.csv",
                "belongs_to_one_coherent_theme_0_no_1_yes_9_uncertain",0,"0")
            set_rating(normalized/"rater_b_documents.csv",
                "policy_relevance_0_to_3_or_9_uncertain",0,"3")
            set_rating(normalized/"rater_b_documents.csv",
                "policy_relevance_0_to_3_or_9_uncertain",1,"3")
        priv=home/"private"
        report18=home/"phase18"
        execute(PHASE18,"--normalized-ratings",normalized,
           "--phase15-private",original,"--private-out",priv,"--out",report18)
        original_xlsx=priv/"Adjudicacion_Ciega_Fase18.xlsx"
        returned=home/"Adjudicacion_COMPLETADA.xlsx"
        if fill:
            fill_workbook(original_xlsx,returned,2 if disputes else 0)
        else:
            import shutil
            shutil.copy2(original_xlsx,returned)
        report19=home/"phase19"
        execute(PHASE19,
            "--original-xlsx",original_xlsx,
            "--returned-xlsx",returned,
            "--phase18-report",report18/"adjudication_preparation_aggregate.json",
            "--normalized-ratings",normalized,
            "--out",report19)
        result=json.loads(
            (report19/"adjudicated_topic_comparison_aggregate.json").read_text(encoding="utf8"))
        public=json.dumps(result)
        assert "SYNTH-" not in public
        assert "Synthetic research" not in public
        assert "Evidence checked by adjudicator" not in public
        return result


class TestAdjudicationImport(unittest.TestCase):
    def test_blank_template_remains_pending(self):
        result=sample_case(disputes=True,fill=False)
        self.assertEqual(result["status"],"awaiting_human_adjudication")
        self.assertNotIn("aggregate_results",result)
        self.assertEqual(result["input_integrity"]["DESACUERDOS"]["records"],2)
        self.assertEqual(result["readiness"]["topic_groups"]["11"]["filled"],0)

    def test_complete_adjudication_unblinds_only_aggregate(self):
        result=sample_case(disputes=True,fill=True)
        self.assertEqual(result["status"],"completed_human_adjudication_unblinded_aggregate")
        self.assertEqual(result["readiness"]["disputed_documents"]["12"]["filled"],2)
        models=result["aggregate_results"]["models"]
        self.assertEqual(set(models),{"body_chunks_k12","body_chunks_k18","hybrid_equal_k18"})
        self.assertEqual(models["body_chunks_k12"]["topic_groups"],12)
        self.assertEqual(models["body_chunks_k12"]["topic_coherence"]["mean"],4)
        self.assertEqual(result["aggregate_results"]["document_consensus_source_counts"][
            "adjudicated_disputed_cases"],2)

    def test_no_disagreements_can_be_completed(self):
        result=sample_case(disputes=False,fill=True)
        self.assertEqual(result["status"],"completed_human_adjudication_unblinded_aggregate")
        self.assertEqual(result["input_integrity"]["DESACUERDOS"]["records"],0)
        self.assertEqual(result["aggregate_results"]["document_consensus_source_counts"][
            "unanimous_A_B_cases_retained_without_adjudication"],336)


if __name__=="__main__":
    unittest.main()
