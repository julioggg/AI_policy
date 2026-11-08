#!/usr/bin/env python3
"""Synthetic-only tests for Phase18 private adjudication Excel preparation."""
from __future__ import annotations
import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

from test_phase16_synthetic import rows

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"18_prepare_blinded_adjudication_excel.py"


def set_rating(path,field,index,value):
    with path.open(encoding="utf-8-sig",newline="") as file:
        reader=csv.DictReader(file)
        names=reader.fieldnames
        data=list(reader)
    data[index][field]=value
    with path.open("w",encoding="utf-8-sig",newline="") as file:
        writer=csv.DictWriter(file,fieldnames=names)
        writer.writeheader()
        writer.writerows(data)


def run_case(with_disagreements):
    with tempfile.TemporaryDirectory() as t:
        root=Path(t)
        original=root/"phase15";original.mkdir()
        normalized=root/"normalized";normalized.mkdir()
        rows(original,False)
        rows(normalized,True)
        if with_disagreements:
            set_rating(normalized/"rater_b_documents.csv",
                "belongs_to_one_coherent_theme_0_no_1_yes_9_uncertain",0,"0")
            set_rating(normalized/"rater_b_documents.csv",
                "policy_relevance_0_to_3_or_9_uncertain",0,"3")
            set_rating(normalized/"rater_b_documents.csv",
                "policy_relevance_0_to_3_or_9_uncertain",1,"3")
            set_rating(normalized/"rater_b_topics.csv",
                "topic_coherence_1_to_5",0,"3")
            set_rating(normalized/"rater_b_topics.csv",
                "direct_policy_relevance_0_to_3_or_9",0,"2")
        private=root/"private-output"
        public=root/"reports"
        result=subprocess.run([sys.executable,str(SCRIPT),
            "--normalized-ratings",str(normalized),
            "--phase15-private",str(original),
            "--private-out",str(private),
            "--out",str(public)],
            capture_output=True,text=True)
        if result.returncode:
            raise AssertionError("Synthetic Phase18 failed: "+result.stderr[-1900:])
        summary=json.loads((public/"adjudication_preparation_aggregate.json").read_text(
            encoding="utf8"))
        book=private/"Adjudicacion_Ciega_Fase18.xlsx"
        assert book.is_file()
        with zipfile.ZipFile(book) as z:
            assert z.testzip() is None
            assert sum(n.startswith("xl/worksheets/sheet") and n.endswith(".xml")
                       for n in z.namelist())==5
            assert b"dataValidation" in z.read("xl/worksheets/sheet2.xml")
            assert b"dataValidation" in z.read("xl/worksheets/sheet4.xml")
            assert b"SYNTH-" not in z.read("xl/worksheets/sheet3.xml")
            assert b"body_chunks" not in z.read("xl/worksheets/sheet2.xml")
        output=json.dumps(summary)
        assert "SYNTH-" not in output
        assert "Synthetic research" not in output
        return summary


class TestPhase18(unittest.TestCase):
    def test_preparation_with_realistic_synthetic_disagreements(self):
        report=run_case(True)
        self.assertEqual(report["status"],
                         "adjudication_packet_prepared_human_consensus_pending")
        c=report["counts"]
        self.assertEqual(c["blind_topic_groups_total"],48)
        self.assertEqual(c["document_examples_for_context"],336)
        self.assertEqual(c["disputed_unique_document_cases"],2)
        self.assertEqual(c["document_membership_disagreements"],1)
        self.assertEqual(c["document_policy_relevance_disagreements"],2)
        self.assertEqual(c["document_cases_with_both_disagreements"],1)
        self.assertEqual(c["topic_coherence_disagreements"],1)
        self.assertEqual(c["topic_policy_relevance_disagreements"],1)

    def test_preparation_works_with_no_disagreements(self):
        report=run_case(False)
        c=report["counts"]
        self.assertEqual(c["disputed_unique_document_cases"],0)
        self.assertEqual(c["topic_coherence_disagreements"],0)


if __name__=="__main__":
    unittest.main()
