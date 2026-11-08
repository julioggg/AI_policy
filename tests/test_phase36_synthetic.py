#!/usr/bin/env python3
"""Phase36 synthetic-only test: country-incidence audit and 5000 DOI proxy."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"36_geographic_fulltext_bias.py"


class TestPhase36(unittest.TestCase):
    def test_geographic_incidence_bias_with_separate_attempt_and_availability_stages(self):
        import pandas as pd
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            project=root/"original_project"
            data=project/"data"/"processed"
            outputs=project/"outputs"/"tables"
            scripts=project/"scripts"
            for x in (data,outputs,scripts):x.mkdir(parents=True,exist_ok=True)
            records=[]
            for i in range(10283):
                records.append({
                    "openalex_id":f"W{i+1:07d}",
                    "doi":f"10.3999/research.{i+1}",
                    "ai_decision":"exclude" if i>=10265 else ("include_core" if i<9264 else "include_policy"),
                    "countries":json.dumps(["EC","US"] if i%7==0 else ["US"] if i%3 else ["DE"]),
                    "publication_year":2026,
                    "disciplinary_area":"ssh",
                    "policy_dimension":"teaching_learning",
                    "source_type":"journal",
                    "type":"article",
                    "is_oa":True
                })
            frame=pd.DataFrame.from_records(records)
            frame.to_parquet(data/"ai_assisted_screening_decisions.parquet",index=False)
            frame.iloc[:3656].to_parquet(data/"fulltext_topic_model_documents.parquet",index=False)
            with (outputs/"fulltext_pdf_download_manifest.csv").open("w",newline="") as f:
                w=csv.DictWriter(f,fieldnames=["doi","status","pdf_path","title","download_url","bytes"])
                w.writeheader()
                for i in range(5000):
                    w.writerow({"doi":records[i]["doi"],
                                "status":"downloaded" if i<3655 else "http_403",
                                "pdf_path":f"x{i}.pdf","title":f"PRIVATE ARTICLE {i}",
                                "download_url":"https://example.invalid","bytes":16000})
            (scripts/"10_download_open_access_pdfs.py").write_text(
                "def sample(df):\n    return df.sort_values(by='audit_priority').head(5000)\n"
            )
            out=root/"public_aggregate"
            args=[sys.executable,str(SCRIPT),"--project",str(project),"--out",str(out)]
            p=subprocess.run(args,capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stderr[-3500:])
            result=json.loads((out/"five_thousand_geographic_bias_aggregate.json").read_text())
            self.assertEqual(result["original_counts"]["screening_included_n"],10265)
            self.assertEqual(result["original_counts"]["attempts_n"],5000)
            self.assertEqual(result["original_counts"]["fulltext_downloaded_or_preexisting_n"],3656)
            self.assertEqual(result["attempt_DOI_linkage_diagnostics"][
                "unambiguously_linked_unique_included_records"],5000)
            self.assertTrue(result["attempt_DOI_linkage_diagnostics"][
                "linked_DOI_records_are_NOT_exact_original_5000_membership"])
            self.assertEqual(result["country_parent_vs_fulltext"]["subset_records_n"],3656)
            self.assertEqual(result["country_parent_vs_DOI_linked_attempt_proxy"]["subset_records_n"],5000)
            self.assertTrue(result["selection_script_AST"]["available"])
            self.assertNotIn("W0000001",json.dumps(result))
            self.assertNotIn("PRIVATE ARTICLE",json.dumps(result))
            self.assertNotIn("10.3999/research",json.dumps(result))
            second=subprocess.run(args,capture_output=True,text=True)
            self.assertNotEqual(second.returncode,0)

if __name__=="__main__":
    unittest.main()
