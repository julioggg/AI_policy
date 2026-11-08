#!/usr/bin/env python3
"""Phase37 synthetic test for semicolon ISO2 country correction and provenance."""
from __future__ import annotations
import csv
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"37_country_semicolon_correction.py"

def load(name,filename):
    spec=importlib.util.spec_from_file_location(name,ROOT/"scripts"/filename)
    obj=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj

class TestPhase37(unittest.TestCase):
    def test_country_parser(self):
        f=load("phase37_test","37_country_semicolon_correction.py")
        b=f.load_phase36()
        for value,expected in [
            ("US;GB",["GB","US"]),(" US ; EC ; US ",["EC","US"]),
            ("US; CA",["CA","US"]),
        ]:
            actual,typ=f.parse_countries(value,b)
            self.assertEqual(actual,expected)
            self.assertEqual(typ,"semicolon_iso2_recovered")
        self.assertEqual(f.parse_countries('["US","EC"]',b),(["EC","US"],"previously_recognized"))
        self.assertEqual(f.parse_countries("",b),([],"empty"))
        self.assertEqual(f.parse_countries("Canada; United States",b),(None,"semicolon_unrecognized"))
        self.assertEqual(f.parse_countries("US;PRIVATE RECORD",b),(None,"semicolon_unrecognized"))

    def test_synthetic_10283_5000_3656_and_report_privacy(self):
        import pandas as pd
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            project=root/"secret_original"
            data=project/"data"/"processed"
            output=project/"outputs"/"tables"
            scripts=project/"scripts"
            for folder in (data,output,scripts):folder.mkdir(parents=True)
            rows=[]
            for i in range(10283):
                countries=("US; EC" if i<500 else
                    "CN;DE;CN" if i<1500 else
                    "US;PRIVATE" if i==1500 else
                    "" if i<2000 else
                    '["US"]' if i%3 else '["DE"]')
                rows.append({
                    "openalex_id":f"W{i+1:07d}","doi":f"10.4/test.{i+1}",
                    "ai_decision":"include_core" if i<9264 else
                                  "include_policy" if i<10163 else
                                  "include_context" if i<10265 else "exclude",
                    "countries":countries
                })
            frame=pd.DataFrame(rows)
            frame.to_parquet(data/"ai_assisted_screening_decisions.parquet",index=False)
            frame.iloc[:3656].to_parquet(data/"fulltext_topic_model_documents.parquet",index=False)
            with (output/"fulltext_pdf_download_manifest.csv").open("w",newline="") as f:
                w=csv.DictWriter(f,fieldnames=["doi","status"])
                w.writeheader()
                for i in range(5000):w.writerow({"doi":rows[i]["doi"],"status":"downloaded"})
            (scripts/"10_download_open_access_pdfs.py").write_text(
                'MAX_PDFS=5000\n'
                'def select(included):\n'
                '    included = included.sort_values(["priority_score","cited_by_count"],ascending=[False,False])\n'
                '    selected = included.head(MAX_PDFS)\n'
                '    return selected\n'
            )
            phase36=root/"aggregates36.json"
            phase36.write_text(json.dumps({
                "original_counts":{"screening_included_n":10265,
                                  "fulltext_downloaded_or_preexisting_n":3656},
                "attempt_DOI_linkage_diagnostics":{
                    "unambiguously_linked_unique_included_records":5000,
                    "missing_doi":0,
                    "ambiguous_multiple_included_OpenAlex_ids":0,
                    "unmatched_doi":0
                }
            }))
            out=root/"phase37_public"
            argv=[sys.executable,str(SCRIPT),"--project",str(project),
                  "--phase36-report",str(phase36),"--out",str(out)]
            run=subprocess.run(argv,capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr[-3500:])
            res=json.loads((out/"country_semicolon_corrected_aggregate.json").read_text())
            self.assertEqual(res["included_n"],10265)
            self.assertEqual(res["available_fulltext_n"],3656)
            self.assertEqual(res["included_country_parser_diagnostics"]["semicolon_iso2_recovered"],1500)
            self.assertEqual(res["included_country_parser_diagnostics"]["semicolon_unrecognized"],1)
            self.assertEqual(res["original_five_thousand_DOI_proxy_summary"][
                             "unambiguous_matched_unique_publications"],5000)
            self.assertEqual(res["selection_tracing"]["MAX_PDFS_literal_assignments"],[5000])
            self.assertTrue(res["selection_tracing"][
                            "selection_pipeline_explicit_priority_score_cited_by_count_descending"])
            self.assertTrue(res["selection_tracing"]["selection_pipeline_has_head_MAX_PDFS"])
            self.assertIn("EC",[x["country"] for x in res[
                "comparison_included_vs_fulltext"]["frequent_country_incidence"]])
            self.assertNotIn("PRIVATE RECORD",json.dumps(res))
            self.assertNotIn("10.4/test",json.dumps(res))
            self.assertNotIn("W0000001",json.dumps(res))
            second=subprocess.run(argv,capture_output=True,text=True)
            self.assertNotEqual(second.returncode,0)

if __name__=="__main__": unittest.main()
