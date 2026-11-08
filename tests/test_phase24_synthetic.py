#!/usr/bin/env python3
"""Synthetic-only Phase24 blinded QA export, privacy and no-guess assertions."""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

from test_phase23_synthetic import make_originals, fill_xlsx

ROOT=Path(__file__).resolve().parents[1]
S22=ROOT/"scripts"/"22_prepare_screening_adjudication_excel.py"
S23=ROOT/"scripts"/"23_analyze_adjudicated_screening.py"
S24=ROOT/"scripts"/"24_prepare_blinded_screening_qa.py"


def run(script,*args):
    p=subprocess.run([sys.executable,str(script),*map(str,args)],
                     capture_output=True,text=True)
    if p.returncode:
        raise AssertionError("Synthetic "+script.name+" failed:\n"+p.stderr[-3000:])
    return p.stdout


class TestIndependentScreeningQA(unittest.TestCase):
    def test_qa_reviewer_is_blinded_and_key_private(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            private,p05,p21=make_originals(root)
            original_folder=root/"private_phase22";public22=root/"report22"
            run(S22,"--private-in",private,"--private-out",original_folder,
                "--phase21-report",p21,"--out",public22)
            original=original_folder/"Adjudicacion_Cribado_Fase22.xlsx"
            returned=root/"completed.xlsx"
            fill_xlsx(original,returned,complete=True)
            public23=root/"report23"
            run(S23,"--original-xlsx",original,"--returned-xlsx",returned,
                "--private-in",private,"--phase05-report",p05,
                "--phase21-report",p21,
                "--phase22-report",public22/"screening_adjudication_packet_aggregate.json",
                "--out",public23)
            out=root/"qa_private";public24=root/"report24"
            run(S24,"--original-xlsx",original,"--completed-xlsx",returned,
                "--private-in",private,"--phase05-report",p05,
                "--phase22-report",public22/"screening_adjudication_packet_aggregate.json",
                "--phase23-report",public23/"adjudicated_screening_aggregate.json",
                "--private-out",out,"--out",public24)
            book=out/"Control_Independiente_Cribado_Fase24.xlsx"
            self.assertTrue(book.is_file())
            self.assertTrue((out/"correspondencia_qa_privada.csv").is_file())
            with zipfile.ZipFile(book) as z:
                self.assertIsNone(z.testzip())
                sheet=z.read("xl/worksheets/sheet2.xml").decode("utf-8")
                self.assertEqual(sheet.count("<row "),81)
                self.assertNotIn("FAKE_IDENTIFIER",sheet)
                self.assertNotIn("P0001",sheet)
                self.assertNotIn("include_core",sheet)
                self.assertNotIn("Synthetic human rationale",sheet)
                self.assertNotIn("Reviewed evidence and arrived at consensus",sheet)
                self.assertIn("dataValidation",sheet)
            report=json.loads((public24/"quality_audit_packet_aggregate.json").read_text())
            self.assertEqual(report["review_sample_n"],80)
            self.assertEqual(report["source_phase23_consensus_n"],368)
            self.assertEqual(sum(report["selection_channel_counts"].values()),80)
            self.assertEqual(report["status"],
                "private_blinded_quality_audit_packet_prepared_human_QA_pending")
            self.assertNotIn("FAKE_IDENTIFIER",json.dumps(report))
            self.assertNotIn("P0001",json.dumps(report))


if __name__=="__main__":
    unittest.main()
