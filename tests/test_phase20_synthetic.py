#!/usr/bin/env python3
"""Synthetic-only Phase20 two-rater eligibility screening Excel roundtrip."""
from __future__ import annotations
import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"20_screening_reviewer_excel.py"
FIELDS=["sample_id","title","abstract","publication_year","type",
        "relevance_code","discipline_code","primary_policy_code","reason"]


def make_source(folder):
    for r in ("a","b"):
        rows=[{
            "sample_id":f"P{i:04d}","title":"Study title =KEEP_LITERAL",
            "abstract":"Summary of synthetic university research with AI, no actual real paper",
            "publication_year":"2024","type":"journal-article",
            "relevance_code":"","discipline_code":"",
            "primary_policy_code":"","reason":""
        } for i in range(1,369)]
        with (folder/f"rater_{r}.csv").open("w",encoding="utf-8-sig",newline="") as f:
            w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
    (folder/"sampling_key.csv").write_text(
        "sample_id,stratum,openalex_id,ai_decision,original_policy_dimension,original_disciplinary_area\n",
        encoding="utf8")


def invoke(*args):
    p=subprocess.run([sys.executable,str(SCRIPT),*map(str,args)],
        capture_output=True,text=True)
    if p.returncode:
        raise AssertionError("Phase20 synthetic failure: "+p.stderr[-1800:])
    return p.stdout


class Phase20(unittest.TestCase):
    def test_two_private_workbooks_and_safe_blank_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            src=root/"phase05";src.mkdir()
            make_source(src)
            out=root/"xls"
            invoke("--mode","export","--private-in",src,"--out-dir",out)
            for name,r in [("Cribado_A.xlsx","a"),("Cribado_B.xlsx","b")]:
                file=out/name
                self.assertTrue(file.is_file())
                with zipfile.ZipFile(file) as z:
                    self.assertIsNone(z.testzip())
                    self.assertEqual(len([n for n in z.namelist()
                        if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")]),3)
                    xml=z.read("xl/worksheets/sheet2.xml").decode("utf8")
                    self.assertIn("dataValidation",xml)
                    self.assertIn("=KEEP_LITERAL",xml)
                    self.assertNotIn("<f>",xml)
                imported=root/"imported"
                invoke("--mode","import","--private-in",src,
                       "--received-xlsx",file,"--rater",r,"--out-dir",imported)
                with (imported/f"rater_{r}.csv").open(encoding="utf-8-sig") as f:
                    rows=list(csv.DictReader(f))
                self.assertEqual(len(rows),368)
                self.assertEqual(rows[0]["abstract"],
                    "Summary of synthetic university research with AI, no actual real paper")
            self.assertTrue((root/"imported/sampling_key.csv").is_file())

    def test_wrong_reviewer_workbook_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);private=root/"phase05";private.mkdir()
            make_source(private)
            out=root/"export"
            invoke("--mode","export","--private-in",private,"--out-dir",out)
            p=subprocess.run([sys.executable,str(SCRIPT),"--mode","import",
               "--private-in",str(private),"--received-xlsx",str(out/"Cribado_A.xlsx"),
               "--rater","b","--out-dir",str(root/"imported")],
               capture_output=True,text=True)
            self.assertNotEqual(p.returncode,0)
            self.assertIn("other evaluator",p.stderr)


if __name__=="__main__":
    unittest.main()
