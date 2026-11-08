#!/usr/bin/env python3
"""Synthetic-only Phase22 screening adjudication workbook and privacy tests."""
from __future__ import annotations
import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile
from test_phase20_synthetic import FIELDS,make_source

ROOT=Path(__file__).resolve().parents[1]
S21=ROOT/"scripts"/"21_score_human_screening.py"
S22=ROOT/"scripts"/"22_prepare_screening_adjudication_excel.py"
STRATA=[
    ("screen_include_core",120),("screen_include_policy",80),
    ("screen_include_context",40),("screen_exclude",18),
    ("q1_not_article_ready",80),("core_not_q1",30)
]


def run(script,*args):
    p=subprocess.run([sys.executable,str(script),*map(str,args)],
                     capture_output=True,text=True)
    if p.returncode:
        raise AssertionError(f"synthetic {script.name} failed: "+p.stderr[-2200:])
    return p.stdout


class TestPhase22(unittest.TestCase):
    def test_exact_conflicts_and_private_export(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            private=root/"private";private.mkdir()
            make_source(private)
            key=[]
            i=0
            for stratum,n in STRATA:
                for _ in range(n):
                    i+=1
                    key.append({
                      "sample_id":f"P{i:04d}","stratum":stratum,
                      "openalex_id":f"FAKE_OPENALEX_{i}",
                      "ai_decision":"include_core","original_policy_dimension":"",
                      "original_disciplinary_area":""})
            with (private/"sampling_key.csv").open("w",newline="",encoding="utf-8-sig") as f:
                w=csv.DictWriter(f,fieldnames=list(key[0]));w.writeheader();w.writerows(key)
            for rater in ("a","b"):
                f=private/f"rater_{rater}.csv"
                with f.open(encoding="utf-8-sig",newline="") as fp:
                    recs=list(csv.DictReader(fp))
                for r in recs:
                    r.update({"relevance_code":"1","discipline_code":"general_he",
                              "primary_policy_code":"teaching_learning",
                              "reason":"human explanation from evidence"})
                if rater=="b":
                    recs[0]["relevance_code"]="2"
                    recs[0]["discipline_code"]="ssh"
                    recs[1]["primary_policy_code"]="assessment"
                    recs[2]["discipline_code"]="health_sciences"
                    recs[3]["relevance_code"]="9"
                with f.open("w",newline="",encoding="utf-8-sig") as fp:
                    w=csv.DictWriter(fp,fieldnames=FIELDS);w.writeheader();w.writerows(recs)
            phase05=root/"sample.json"
            phase05.write_text(json.dumps({"sample_size":368,"strata":{
                s:{"sample_n":n,"population_n":1000} for s,n in STRATA}}))
            report21=root/"reports21"
            run(S21,"--private-in",private,"--phase05-report",phase05,
                "--out",report21)
            report22=root/"reports22";out=root/"adjudication-private"
            run(S22,"--private-in",private,"--private-out",out,"--out",report22,
                "--phase21-report",report21/"human_screening_agreement_aggregate.json")
            data=json.loads((report22/"screening_adjudication_packet_aggregate.json").read_text())
            self.assertEqual(data["counts"]["relevance"],2)
            self.assertEqual(data["counts"]["discipline"],2)
            self.assertEqual(data["counts"]["policy"],1)
            self.assertEqual(data["counts"]["unique"],4)
            self.assertEqual(data["counts"]["original_no_disagreement"],364)
            workbook=out/"Adjudicacion_Cribado_Fase22.xlsx"
            self.assertTrue(workbook.is_file())
            with zipfile.ZipFile(workbook) as z:
                self.assertIsNone(z.testzip())
                pages=sorted(x for x in z.namelist() if
                             x.startswith("xl/worksheets/sheet") and x.endswith(".xml"))
                self.assertEqual(len(pages),4)
                self.assertEqual(z.read("xl/worksheets/sheet2.xml").count(b"<row "),5)
                self.assertEqual(z.read("xl/worksheets/sheet3.xml").count(b"<row "),369)
                self.assertIn(b"dataValidation",z.read("xl/worksheets/sheet2.xml"))
                self.assertNotIn(b"FAKE_OPENALEX",z.read("xl/worksheets/sheet2.xml"))
                self.assertNotIn(b"screen_include_core",z.read("xl/worksheets/sheet2.xml"))
            public=json.dumps(data)
            self.assertNotIn("FAKE_OPENALEX",public)
            self.assertNotIn("P0001",public)
            self.assertEqual(data["status"],
                "screening_adjudication_packet_prepared_consensus_pending")


if __name__=="__main__":
    unittest.main()
