#!/usr/bin/env python3
"""Synthetic-only integration tests for Phase16; uses NO real manuscripts."""
from __future__ import annotations
import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "16_score_human_topic_review.py"
TOPIC = ["group_code","topic_name_proposed","topic_coherence_1_to_5",
         "distinctiveness_1_to_5","direct_policy_relevance_0_to_3_or_9",
         "confidence_1_to_5","reviewer_comments"]
DOCS = ["group_code","item_code","title","abstract",
        "body_excerpt_A","body_excerpt_B",
        "belongs_to_one_coherent_theme_0_no_1_yes_9_uncertain",
        "policy_relevance_0_to_3_or_9_uncertain","document_comments"]
KEY = ["group_code","item_code","modality","k","cluster_label",
       "candidate_cluster_population","phase14_row_index","openalex_id","sampling_role"]


def write_csv(path, fields, rows):
    with path.open("w",encoding="utf-8-sig",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def rows(private, filled):
    topics=[]
    docs=[]
    keys=[]
    for g in range(48):
        group=f"G-{g+1:03d}"
        name,k = ("body_chunks",12) if g<12 else (
            ("body_chunks",18) if g<30 else ("hybrid_equal",18))
        topics.append({
            "group_code":group,
            "topic_name_proposed":"Synthetic research theme" if filled else "",
            "topic_coherence_1_to_5":"4" if filled else "",
            "distinctiveness_1_to_5":"4" if filled else "",
            "direct_policy_relevance_0_to_3_or_9":"3" if filled else "",
            "confidence_1_to_5":"5" if filled else "",
            "reviewer_comments":""
        })
        for j in range(7):
            code=f"{group}-R{j+1:02d}"
            docs.append({
                "group_code":group,"item_code":code,
                "title":"Synthetic title only","abstract":"Synthetic abstract",
                "body_excerpt_A":"", "body_excerpt_B":"",
                "belongs_to_one_coherent_theme_0_no_1_yes_9_uncertain": (
                    "0" if (filled and j==6) else ("1" if filled else "")
                ),
                "policy_relevance_0_to_3_or_9_uncertain":"2" if filled else "",
                "document_comments":""
            })
            keys.append({
                "group_code":group,"item_code":code,"modality":name,
                "k":str(k),"cluster_label":str(g),"candidate_cluster_population":"50",
                "phase14_row_index":str(g*7+j),"openalex_id":f"SYNTH-{g}-{j}",
                "sampling_role":"random"
            })
    for r in ("a","b"):
        write_csv(private / f"rater_{r}_topics.csv",TOPIC,topics)
        write_csv(private / f"rater_{r}_documents.csv",DOCS,docs)
    write_csv(private / "private_sampling_key.csv",KEY,keys)
    (private / "private_validation_manifest.json").write_text(
        json.dumps({"n_groups":48,"n_document_assessments_per_rater":336}),
        encoding="utf-8")


def run_audit(private,out):
    result=subprocess.run(
        [sys.executable,str(SCRIPT),"--private-in",str(private),"--out",str(out)],
        capture_output=True,text=True,check=False
    )
    if result.returncode:
        raise AssertionError("Synthetic integration audit failed: "+result.stderr[-1400:])
    return json.loads((out/"human_topic_review_aggregate.json").read_text(encoding="utf8"))


class Phase16Tests(unittest.TestCase):
    def test_blank_forms_are_not_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            priv=Path(tmp)/"private"
            priv.mkdir()
            rows(priv,False)
            report=run_audit(priv,Path(tmp)/"report")
            self.assertEqual(report["status"],"awaiting_independent_human_ratings")
            self.assertNotIn("results",report)
            self.assertEqual(report["readiness"]["a"]["topics"]["topic_coherence_1_to_5"]["filled"],0)

    def test_completed_fake_forms_score_descriptively_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            priv=Path(tmp)/"private"
            priv.mkdir()
            rows(priv,True)
            report=run_audit(priv,Path(tmp)/"report")
            self.assertEqual(report["status"],
                             "complete_independent_ratings_not_yet_adjudicated")
            models=report["results"]["candidate_descriptive_comparison"]
            self.assertEqual(len(models),3)
            self.assertEqual(models["body_chunks_k12"]["groups"],12)
            self.assertEqual(models["body_chunks_k18"]["groups"],18)
            self.assertEqual(models["hybrid_equal_k18"]["groups"],18)
            # Perfect agreement can have undefined kappa when only one rating value exists.
            overall=report["results"]["overall_inter_rater_agreement"]
            self.assertEqual(
                overall["document_belongs_to_one_coherent_theme_0_no_1_yes_9_uncertain"]["exact_agreement_fraction"],
                1.0
            )
            output=json.dumps(report)
            self.assertNotIn("SYNTH-",output)
            self.assertNotIn("Synthetic research theme",output)


if __name__=="__main__":
    unittest.main()
