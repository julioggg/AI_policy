#!/usr/bin/env python3
"""Synthetic-only tests of Phase28 prospective pilot sampling and reviewer privacy."""
from __future__ import annotations
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"28_prepare_independent_pilot.py"
CODEBOOK=ROOT/"docs"/"phase28_pilot_codebook_v0.2.md"
COUNTS=[
    ("screen_include_core","include_core",9264,120),
    ("screen_include_policy","include_policy",899,80),
    ("screen_include_context","include_context",102,40),
    ("screen_exclude","exclude",18,18),
]
EARLY=[
    ("q1_not_article_ready",11393,80),
    ("core_not_q1",848,30),
]


def synthetic_frame(root):
    project=root/"source"
    data=project/"data"/"processed";data.mkdir(parents=True)
    frame=data/"frame.csv"
    keyfolder=root/"previous_private";keyfolder.mkdir()
    key=keyfolder/"sampling_key.csv"
    old=[]
    with frame.open("w",newline="",encoding="utf-8-sig") as f:
        headers=["openalex_id","title","abstract","publication_year","type","ai_decision"]
        w=csv.DictWriter(f,fieldnames=headers);w.writeheader()
        for stratum,decision,pop,prior in COUNTS:
            for j in range(pop):
                ident=f"FAKE:{stratum}:{j:05d}"
                w.writerow({"openalex_id":ident,
                    "title":"Synthetic academic title",
                    "abstract":"Imaginary research abstract about university AI usage.",
                    "publication_year":"2025","type":"article",
                    "ai_decision":decision})
                if j<prior:
                    old.append({"sample_id":f"P{len(old)+1:04d}",
                        "stratum":stratum,"openalex_id":ident,
                        "ai_decision":decision,"original_policy_dimension":"",
                        "original_disciplinary_area":""})
    for stratum,pop,prior in EARLY:
        for j in range(prior):
            old.append({"sample_id":f"P{len(old)+1:04d}",
                "stratum":stratum,
                "openalex_id":f"FAKE:EARLY:{stratum}:{j:05d}",
                "ai_decision":"","original_policy_dimension":"",
                "original_disciplinary_area":""})
    with key.open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=list(old[0]));w.writeheader();w.writerows(old)
    assert len(old)==368
    report=root/"old_summary.json"
    from_counts={}
    for stratum,_,pop,prior in COUNTS:
        from_counts[stratum]={"sample_n":prior,"population_n":pop}
    for stratum,pop,prior in EARLY:
        from_counts[stratum]={"sample_n":prior,"population_n":pop}
    report.write_text(json.dumps({
        "sample_size":368,"strata":from_counts,
        "id_set_sha256":hashlib.sha256(
            "\n".join(sorted(r["openalex_id"] for r in old)).encode("utf8")
        ).hexdigest()
    }))
    return project,frame,key,report,old


class TestPhase28(unittest.TestCase):
    def test_new_blinded_books_preserve_randomization_and_prior_exclusion(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            project,frame,old_key,report,prior=synthetic_frame(root)
            target=root/"private_calibration";public=root/"public_counts"
            p=subprocess.run([sys.executable,str(SCRIPT),
                "--project",str(project),"--source-frame",str(frame),
                "--source-format","csv","--phase05-key",str(old_key),
                "--phase05-report",str(report),"--codebook",str(CODEBOOK),
                "--private-out",str(target),"--out",str(public)],
                capture_output=True,text=True)
            if p.returncode:
                raise AssertionError(p.stderr[-2500:])
            output=json.loads((public/"pilot_preparation_aggregate.json").read_text())
            self.assertEqual(output["pilot_size"],30)
            self.assertEqual(output["rated_cases"],0)
            self.assertTrue(output["distinct_from_prior_phase05_368"])
            self.assertFalse(output["pilot_is_probability_validation_sample"])
            self.assertEqual(output["sample_plan"]["screen_exclude"],0)
            with (target/"pilot_private_key.csv").open(encoding="utf-8-sig") as f:
                keys=list(csv.DictReader(f))
            self.assertEqual(len(keys),30)
            self.assertEqual(Counter(x["stratum"] for x in keys),{
                "screen_include_core":10,
                "screen_include_policy":10,
                "screen_include_context":10
            })
            self.assertFalse(set(x["openalex_id"] for x in keys)&
                             set(r["openalex_id"] for r in prior))
            for rater in ("A","B"):
                f=target/f"Piloto_V02_{rater}.xlsx"
                self.assertTrue(f.is_file())
                with zipfile.ZipFile(f) as z:
                    self.assertIsNone(z.testzip())
                    page=z.read("xl/worksheets/sheet2.xml").decode()
                    self.assertEqual(page.count("<row "),31)
                    self.assertIn("dataValidation",page)
                    self.assertNotIn("FAKE:",page)
                    self.assertNotIn("include_core",page)
                    self.assertNotIn("include_policy",page)
                    self.assertNotIn("openalex_id",page)
                    self.assertIn("CAL001",page)
            manifest=json.loads((target/"pilot_locked_manifest.json").read_text())
            self.assertEqual(manifest["codebook_sha256"],
                hashlib.sha256(CODEBOOK.read_bytes()).hexdigest())
            self.assertTrue(manifest["all_30_cases_unseen_in_phase05"])
            self.assertNotIn("FAKE:",json.dumps(output))
            self.assertNotIn("CAL001",json.dumps(output))
            # Re-running must fail rather than overwriting distributed review files.
            second=subprocess.run([sys.executable,str(SCRIPT),
                "--project",str(project),"--source-frame",str(frame),
                "--source-format","csv","--phase05-key",str(old_key),
                "--phase05-report",str(report),"--codebook",str(CODEBOOK),
                "--private-out",str(target),"--out",str(public)],
                capture_output=True,text=True)
            self.assertNotEqual(second.returncode,0)


if __name__=="__main__":
    unittest.main()
