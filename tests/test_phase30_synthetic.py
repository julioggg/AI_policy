#!/usr/bin/env python3
"""Synthetic-only Phase30 full 1200-case new expert, no-pilot sampling test."""
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

from test_phase28_synthetic import synthetic_frame

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"30_prepare_full1200_validation.py"
BOOK=ROOT/"docs"/"phase30_full_validation_codebook_v1.0.md"

class TestFull1200(unittest.TestCase):
    def test_full_frame_probability_draw_and_two_strictly_blinded_books(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            project,frame,historical_key,phase05,old=synthetic_frame(root)
            private=root/"new1200_priv";public=root/"counts"
            command=[sys.executable,str(SCRIPT),
                "--project",str(project),"--source-frame",str(frame),
                "--source-format","csv","--phase05-key",str(historical_key),
                "--phase05-report",str(phase05),"--codebook",str(BOOK),
                "--private-out",str(private),"--out",str(public)]
            result=subprocess.run(command,capture_output=True,text=True)
            if result.returncode:
                raise AssertionError(result.stderr[-3000:])
            public_json=json.loads((public/"full_validation_packet_aggregate.json").read_text())
            self.assertEqual(public_json["population_n"],10283)
            self.assertEqual(public_json["sample_n"],1200)
            self.assertFalse(public_json["pilot"])
            self.assertEqual(public_json["human_assessments_completed"],0)
            self.assertEqual(public_json["actual_draw_counts"],{
                "screen_include_core":800,"screen_include_policy":290,
                "screen_include_context":92,"screen_exclude":18
            })
            with (private/"private_sampling_key.csv").open(encoding="utf-8-sig") as fh:
                rows=list(csv.DictReader(fh))
            self.assertEqual(len(rows),1200)
            self.assertEqual(len(set(r["openalex_id"] for r in rows)),1200)
            self.assertEqual(len(set(r["validation_code"] for r in rows)),1200)
            self.assertEqual(Counter(r["stratum"] for r in rows),
                {"screen_include_core":800,"screen_include_policy":290,
                 "screen_include_context":92,"screen_exclude":18})
            self.assertTrue(set(r["openalex_id"] for r in rows)&
                            set(r["openalex_id"] for r in old),
                            "Old 368 records are intentionally not excluded from population")
            self.assertEqual((private/"Rubrica_Validacion_V1.md").read_bytes(),BOOK.read_bytes())
            manifest=json.loads((private/"private_locked_manifest.json").read_text())
            self.assertGreaterEqual(manifest["previously_sampled_from_phase05_n"],1)
            self.assertEqual(manifest["codebook_sha256"],
                hashlib.sha256(BOOK.read_bytes()).hexdigest())
            for name in ("A","B"):
                path=private/f"Validacion_1200_{name}.xlsx"
                self.assertTrue(path.is_file())
                self.assertEqual(manifest["pristine_workbook_sha256"][name],
                    hashlib.sha256(path.read_bytes()).hexdigest())
                with zipfile.ZipFile(path) as z:
                    self.assertIsNone(z.testzip())
                    page=z.read("xl/worksheets/sheet2.xml").decode("utf-8")
                    self.assertEqual(page.count("<row "),1201)
                    self.assertIn("dataValidation",page)
                    self.assertNotIn("FAKE:screen_include_core",page)
                    self.assertNotIn("openalex_id",page)
                    self.assertNotIn("include_core",page)
                    self.assertIn("VAL0001",page)
            self.assertNotIn("FAKE:",json.dumps(public_json))
            self.assertNotIn("VAL0001",json.dumps(public_json))
            rerun=subprocess.run(command,capture_output=True,text=True)
            self.assertNotEqual(rerun.returncode,0,
                 "Previously prepared independent expert books must not be overwritten")


if __name__=="__main__":
    unittest.main()
