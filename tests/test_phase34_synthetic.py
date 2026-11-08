#!/usr/bin/env python3
"""Synthetic privacy tests for Phase34 148 full-text evidence workbooks."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"scripts"/"34_prepare_fulltext148_review.py"
CODEBOOK=ROOT/"docs"/"phase30_full_validation_codebook_v1.0.md"

def mod(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    obj=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj

def fixture(root):
    private_in=root/"phase33_private"
    private_in.mkdir()
    output=root/"phase34_private"
    public=root/"phase34_public"
    report=root/"phase33_report.json"
    manifestdir=root/"source_manifest_private"
    manifestdir.mkdir()
    manifest=manifestdir/"phase30_manifest.json"
    manifest.write_text(json.dumps({
        "codebook_sha256":hashlib.sha256(CODEBOOK.read_bytes()).hexdigest()
    }))
    report.write_text(json.dumps({
        "casebook_n":324,
        "panel_scientific_reason_diagnostics":{"residual":{
            "requested_fulltext_yes":148,
            "uncertain_relevance_9":74
        }}
    }))
    p32=mod(ROOT/"scripts"/"32_audit_pi_attested_human1200.py","phase34_fixture32")
    excel=mod(ROOT/"scripts"/"17_excel_reviewer_packages.py","phase34_fixture_excel")
    pack=mod(ROOT/"scripts"/"18_prepare_blinded_adjudication_excel.py","phase34_fixture_pack")
    rows=[]
    for n in range(324):
        code=f"VAL{n+1:04d}"
        r=dict.fromkeys(p32.FIELDS,"")
        r.update({
            "validation_code":code,
            "title":f"Fictional publication about university policy {n+1}",
            "abstract":"Synthetic bibliography summary for test only.",
            "publication_year":"2025","type":"article",
            "scope_a":"1","scope_b":"1",
            "relevance_a":"1","relevance_b":"1",
            "topic_a":"teaching_learning","topic_b":"teaching_learning",
            "discipline_a":"general_he","discipline_b":"general_he",
            "panel_scope":"9" if n<74 else "1",
            "panel_relevance":"9" if n<74 else "1",
            "panel_topic":"uncertain" if n<74 else "teaching_learning",
            "panel_discipline":"uncertain" if n<74 else "general_he",
            "panel_evidence_reason":"Synthetic panel decision, not a real paper.",
            "fulltext_escalation":"yes" if n<148 else "no",
        })
        rows.append({"group_code":code,**r})
    sheet=excel.section_xml(
        "DOCUMENTOS",p32.FIELDS,p32.HEADERS,rows,[20]*len(p32.FIELDS),
        {22:["0","1","9"],23:["0","1","2","3","9"],
         24:["teaching_learning","uncertain"],
         25:["general_he","uncertain"],
         26:None,27:["yes","no"]})
    book=private_in/"panel_completed.xlsx"
    pack.xlsx_generic(book,[
       ("INSTRUCCIONES",excel.basic_sheet([["Title","Synthetic only"]],[28,48])),
       ("DISCREPANCIAS",sheet),
       ("ESCALAS",excel.basic_sheet([["Type","Test"]],[22,22]))
    ],excel)
    return book,manifest,report,output,public

class TestFulltext148(unittest.TestCase):
    def test_private_blinded_fulltext_books_and_all_uncertain_included(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            panel,manifest,report,private,public=fixture(root)
            args=[
                sys.executable,str(SOURCE),
                "--returned-panel",str(panel),"--phase33-report",str(report),
                "--phase30-manifest",str(manifest),"--codebook",str(CODEBOOK),
                "--private-out",str(private),"--out",str(public)
            ]
            p=subprocess.run(args,text=True,capture_output=True)
            if p.returncode:
                raise AssertionError(p.stderr[-3000:])
            obj=json.loads((public/"fulltext_preparation_aggregate.json").read_text())
            self.assertEqual(obj["n_requested_for_fulltext"],148)
            self.assertEqual(obj["n_undecidable_R9_in_original_panel"],74)
            self.assertEqual(obj["n_sources_read_in_this_step"],0)
            self.assertEqual(obj["n_new_human_decisions"],0)
            with (private/"private_fulltext_key.csv").open(encoding="utf-8-sig") as f:
                import csv
                keys=list(csv.DictReader(f))
            self.assertEqual(len(keys),148)
            self.assertEqual(sum(x["panel_relevance_before_fulltext"]=="9" for x in keys),74)
            self.assertEqual(len(set(x["validation_code"] for x in keys)),148)
            self.assertEqual((private/"Rubrica_Validacion_V1.md").read_bytes(),
                             CODEBOOK.read_bytes())
            manifest_obj=json.loads((private/"private_fulltext_manifest.json").read_text())
            self.assertFalse(manifest_obj["actual_fulltext_files_retrieved"])
            for who in ("A","B"):
                workbook=private/f"TextoCompleto_148_{who}.xlsx"
                self.assertTrue(workbook.is_file())
                self.assertEqual(manifest_obj["workbook_sha256"][who],
                                 hashlib.sha256(workbook.read_bytes()).hexdigest())
                with zipfile.ZipFile(workbook) as z:
                    self.assertIsNone(z.testzip())
                    s=z.read("xl/worksheets/sheet2.xml").decode()
                    self.assertEqual(s.count("<row "),149)
                    self.assertIn("FT0001",s)
                    self.assertNotIn("VAL0001",s)
                    self.assertNotIn("panel_relevance_before_fulltext",s)
                    self.assertNotIn("screen_include_core",s)
                    self.assertIn("dataValidation",s)
            self.assertNotIn("Fictional publication",json.dumps(obj))
            self.assertNotIn("FT0001",json.dumps(obj))
            p=subprocess.run(args,text=True,capture_output=True)
            self.assertNotEqual(p.returncode,0)

if __name__=="__main__":
    unittest.main()
