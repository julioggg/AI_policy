#!/usr/bin/env python3
"""Synthetic-only Phase21 screening agreement and privacy tests."""
from __future__ import annotations
import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from test_phase20_synthetic import FIELDS,make_source

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"21_score_human_screening.py"
STRATA=[
    ("screen_include_core",120),("screen_include_policy",80),
    ("screen_include_context",40),("screen_exclude",18),
    ("q1_not_article_ready",80),("core_not_q1",30)
]


def run_case(filled):
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        private=root/"input";private.mkdir()
        report=root/"reports"
        make_source(private)
        keys=[]
        index=0
        for stratum,n in STRATA:
            for i in range(n):
                index+=1
                keys.append({
                   "sample_id":f"P{index:04d}",
                   "stratum":stratum,
                   "openalex_id":f"FAKE_OPENALEX_{index}",
                   "ai_decision":"include_core" if stratum=="screen_include_core" else "exclude",
                   "original_policy_dimension":"",
                   "original_disciplinary_area":""})
        with (private/"sampling_key.csv").open("w",encoding="utf-8-sig",newline="") as f:
            w=csv.DictWriter(f,fieldnames=list(keys[0]));w.writeheader();w.writerows(keys)
        if filled:
            for who in ("a","b"):
                path=private/f"rater_{who}.csv"
                with path.open(encoding="utf-8-sig",newline="") as f:
                    rows=list(csv.DictReader(f))
                for i,r in enumerate(rows):
                    r["relevance_code"]="1" if who=="a" or i%7 else "2"
                    r["discipline_code"]="general_he" if who=="a" or i%9 else "ssh"
                    r["primary_policy_code"]="teaching_learning" if who=="a" or i%11 else "assessment"
                    r["reason"]="An actual human justification would go here"
                with path.open("w",encoding="utf-8-sig",newline="") as f:
                    w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
        aggregate={
            "sample_size":368,
            "strata":{name:{"sample_n":n,"population_n":5000} for name,n in STRATA}}
        p5=root/"phase05.json"
        p5.write_text(json.dumps(aggregate),encoding="utf8")
        p=subprocess.run([sys.executable,str(SCRIPT),
             "--private-in",str(private),
             "--phase05-report",str(p5),
             "--out",str(report)],capture_output=True,text=True)
        if p.returncode:
            raise AssertionError(p.stderr[-2500:])
        output=json.loads(
            (report/"human_screening_agreement_aggregate.json").read_text(encoding="utf8"))
        serialized=json.dumps(output)
        assert "FAKE_OPENALEX" not in serialized
        assert "Synthetic university" not in serialized
        assert "P0001" not in serialized
        return output


class Phase21(unittest.TestCase):
    def test_blank_unrated_sample_has_no_accuracy_claims(self):
        result=run_case(False)
        self.assertEqual(result["status"],"awaiting_two_human_screening_ratings")
        self.assertNotIn("results",result)

    def test_filled_sample_agreements_only(self):
        result=run_case(True)
        self.assertEqual(result["status"],"complete_independent_ratings_not_yet_adjudicated")
        self.assertEqual(result["sample"]["n"],368)
        self.assertEqual(result["readiness"]["a"]["relevance_code"]["filled"],368)
        self.assertEqual(result["results"]["overall_inter_rater"]["relevance"][
            "ordinal_0_to_3_unweighted"]["paired_evaluable"],368)
        self.assertGreater(result["results"]["flagged_for_human_adjudication"][
            "unique_records_disagreeing_in_one_or_more_fields"],0)
        self.assertEqual(result["results"]["stratified_review_summary"]["screen_exclude"]["sample_n"],18)
        self.assertIn("NOT_AI_classifier_negative",
            result["results"]["stratified_review_summary"]["q1_not_article_ready"]["scope"])
        self.assertIn("NO_GOLD_STANDARD_YET",result["results"]["classifier_accuracy_status"])


if __name__=="__main__":
    unittest.main()
