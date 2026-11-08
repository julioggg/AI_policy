#!/usr/bin/env python3
"""Synthetic-only regression tests for XLSX reviewer export/import. No manuscripts."""
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

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"17_excel_reviewer_packages.py"
D_FIELDS=[
    "group_code","item_code",
    "belongs_to_one_coherent_theme_0_no_1_yes_9_uncertain",
    "policy_relevance_0_to_3_or_9_uncertain",
    "title","abstract","body_excerpt_A","body_excerpt_B","document_comments"
]
G_FIELDS=[
    "group_code","topic_name_proposed","topic_coherence_1_to_5",
    "distinctiveness_1_to_5","direct_policy_relevance_0_to_3_or_9",
    "confidence_1_to_5","reviewer_comments"
]


def csv_write(path,headers,rows):
    with path.open("w",encoding="utf-8-sig",newline="") as fp:
        w=csv.DictWriter(fp,fieldnames=headers)
        w.writeheader()
        w.writerows(rows)


def fixture(private):
    for p in ("a","b"):
        docs=[];topics=[]
        for g in range(48):
            group=f"G-{g+1:03d}"
            topics.append({"group_code":group,"topic_name_proposed":"",
               "topic_coherence_1_to_5":"","distinctiveness_1_to_5":"",
               "direct_policy_relevance_0_to_3_or_9":"","confidence_1_to_5":"",
               "reviewer_comments":""})
            for j in range(7):
                docs.append({
                    "group_code":group,"item_code":f"{group}-R{j+1:02d}",
                    "belongs_to_one_coherent_theme_0_no_1_yes_9_uncertain":"",
                    "policy_relevance_0_to_3_or_9_uncertain":"",
                    "title":"Artículo de prueba con =NO_EJECUTAR",
                    "abstract":"Resumen sintético y sin datos reales",
                    "body_excerpt_A":"Texto sintético A","body_excerpt_B":"Texto sintético B",
                    "document_comments":""
                })
        csv_write(private/f"rater_{p}_documents.csv",D_FIELDS,docs)
        csv_write(private/f"rater_{p}_topics.csv",G_FIELDS,topics)
    (private/"private_sampling_key.csv").write_text("synthetic,never_real\n",encoding="utf8")
    (private/"private_validation_manifest.json").write_text(
        json.dumps({"n_groups":48,"n_document_assessments_per_rater":336}),encoding="utf8")


def invoke(*args):
    p=subprocess.run([sys.executable,str(SCRIPT),*map(str,args)],
         stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    if p.returncode:
        raise AssertionError("Phase17 integration failed:\n"+p.stderr[-1800:])
    return p


class ReviewerWorkbookTests(unittest.TestCase):
    def test_export_two_books_and_import_to_standard_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            source=p/"source";source.mkdir()
            fixture(source)
            out=p/"workbooks"
            invoke("--mode","export","--private-in",source,"--out-dir",out)
            xlsx_a=out/"Evaluador_A.xlsx"
            xlsx_b=out/"Evaluador_B.xlsx"
            self.assertTrue(xlsx_a.is_file() and xlsx_b.is_file())
            with zipfile.ZipFile(xlsx_a) as z:
                self.assertIsNone(z.testzip())
                self.assertEqual(len([v for v in z.namelist() if v.startswith(
                    "xl/worksheets/sheet") and v.endswith(".xml")]),4)
                tab=z.read("xl/worksheets/sheet2.xml").decode("utf8")
                self.assertIn('dataValidation type="list"',tab)
                self.assertIn('Artículo de prueba con =NO_EJECUTAR',tab)
                self.assertNotIn("<f>",tab)
            ratings=p/"imported"
            invoke("--mode","import","--private-in",source,"--out-dir",ratings,
                   "--reviewer","a","--received-xlsx",xlsx_a)
            invoke("--mode","import","--private-in",source,"--out-dir",ratings,
                   "--reviewer","b","--received-xlsx",xlsx_b)
            self.assertEqual(len(list(csv.DictReader(
                (ratings/"rater_a_documents.csv").open(encoding="utf-8-sig")))),336)
            self.assertEqual(len(list(csv.DictReader(
                (ratings/"rater_b_topics.csv").open(encoding="utf-8-sig")))),48)
            self.assertTrue((ratings/"private_sampling_key.csv").is_file())
            self.assertTrue((ratings/"private_validation_manifest.json").is_file())

    def test_reviewer_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);source=p/"source";source.mkdir()
            fixture(source)
            out=p/"workbooks"
            invoke("--mode","export","--private-in",source,"--out-dir",out)
            bad=subprocess.run(
                [sys.executable,str(SCRIPT),"--mode","import",
                "--private-in",str(source),"--out-dir",str(p/"bad"),
                "--reviewer","b","--received-xlsx",str(out/"Evaluador_A.xlsx")],
                stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            self.assertNotEqual(bad.returncode,0)
            self.assertIn("OTHER evaluator",bad.stderr)


if __name__=="__main__":
    unittest.main()
