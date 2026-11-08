#!/usr/bin/env python3
"""Synthetic Phase26 tests. No private documents or human records used."""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

from test_phase23_synthetic import make_originals,fill_xlsx
from test_phase25_synthetic import fill_QA,make_map,corrected_QA_from_mapping

ROOT=Path(__file__).resolve().parents[1]
S22=ROOT/"scripts"/"22_prepare_screening_adjudication_excel.py"
S23=ROOT/"scripts"/"23_analyze_adjudicated_screening.py"
S24=ROOT/"scripts"/"24_prepare_blinded_screening_qa.py"
S25=ROOT/"scripts"/"25_compare_independent_screening_qa.py"
S26=ROOT/"scripts"/"26_prepare_methodological_reconciliation.py"


def invoke(script,*args):
    r=subprocess.run([sys.executable,str(script),*map(str,args)],
                     capture_output=True,text=True)
    if r.returncode:
        raise AssertionError(script.name+": "+r.stderr[-3500:])
    return r.stdout


class TestPhase26(unittest.TestCase):
    def test_private_panel_book_matches_public_qa_disagreements(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            private,p05,p21=make_originals(root)
            original_folder=root/"phase22_original"
            out22=root/"phase22_aggregates"
            invoke(S22,"--private-in",private,
                   "--private-out",original_folder,
                   "--phase21-report",p21,"--out",out22)
            original22=original_folder/"Adjudicacion_Cribado_Fase22.xlsx"
            returned22=root/"phase22_returned.xlsx"
            fill_xlsx(original22,returned22,True)
            out23=root/"phase23_aggregates"
            invoke(S23,"--original-xlsx",original22,"--returned-xlsx",returned22,
                   "--private-in",private,"--phase05-report",p05,
                   "--phase21-report",p21,
                   "--phase22-report",out22/"screening_adjudication_packet_aggregate.json",
                   "--out",out23)
            qa_folder=root/"phase24_private"
            out24=root/"phase24_aggregates"
            invoke(S24,"--original-xlsx",original22,
                   "--completed-xlsx",returned22,
                   "--private-in",private,
                   "--phase05-report",p05,
                   "--phase22-report",out22/"screening_adjudication_packet_aggregate.json",
                   "--phase23-report",out23/"adjudicated_screening_aggregate.json",
                   "--private-out",qa_folder,"--out",out24)
            qa_original=qa_folder/"Control_Independiente_Cribado_Fase24.xlsx"
            qa_received=qa_folder/"QA_completado.xlsx"
            fill_QA(qa_original,qa_received)
            mapfile=make_map(qa_folder,False)
            qa_corrected=qa_folder/"QA_corregido.xlsx"
            corrected_QA_from_mapping(qa_received,mapfile,qa_corrected)
            out25=root/"phase25_aggregates"
            invoke(S25,"--qa-original-xlsx",qa_original,
                   "--qa-returned-xlsx",qa_received,
                   "--qa-corrected-xlsx",qa_corrected,
                   "--qa-private-key",qa_folder/"correspondencia_qa_privada.csv",
                   "--normalization-xlsx",mapfile,
                   "--phase24-report",out24/"quality_audit_packet_aggregate.json",
                   "--out",out25)
            out26=root/"phase26_aggregates"
            private26=root/"phase26_casebook_private"
            invoke(S26,"--original-phase22",original22,
                   "--returned-phase22",returned22,
                   "--human-private",private,
                   "--qa-original",qa_original,
                   "--qa-received",qa_received,
                   "--qa-corrected",qa_corrected,
                   "--normalization",mapfile,
                   "--qa-key",qa_folder/"correspondencia_qa_privada.csv",
                   "--phase05-report",p05,
                   "--phase22-report",out22/"screening_adjudication_packet_aggregate.json",
                   "--phase25-report",out25/"independent_screening_qa_aggregate.json",
                   "--private-out",private26,"--out",out26)
            public=json.loads(
                (out26/"panel_reconciliation_preparation_aggregate.json").read_text())
            previous=json.loads(
                (out25/"independent_screening_qa_aggregate.json").read_text())
            self.assertEqual(public["cases"],80)
            self.assertEqual(public["panel_decisions_filled"],0)
            for k,prior in [
                ("mismatch_relevance","relevance_mismatch_cases"),
                ("mismatch_discipline","discipline_mismatch_cases"),
                ("mismatch_policy","post_hoc_policy_mismatch_cases")]:
                self.assertEqual(public["mismatch_counts"][k],
                                 previous["results"][prior])
            self.assertNotIn("FAKE_IDENTIFIER",json.dumps(public))
            self.assertNotIn("P0001",json.dumps(public))
            self.assertNotIn("Q0001",json.dumps(public))
            book=private26/"Conciliacion_Metodologica_Fase26.xlsx"
            self.assertTrue(book.is_file())
            with zipfile.ZipFile(book) as z:
                self.assertIsNone(z.testzip())
                page=z.read("xl/worksheets/sheet2.xml").decode("utf8")
                self.assertEqual(page.count("<row "),81)
                self.assertIn("dataValidation",page)
                self.assertNotIn("FAKE_IDENTIFIER",page)
                self.assertNotIn("screen_include_core",page)
                self.assertNotIn("P0001",page)
                self.assertIn("Synthetic Title",page)


if __name__=="__main__":
    unittest.main()
