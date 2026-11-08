#!/usr/bin/env python3
"""Synthetic Phase23 tests. No confidential CEDIA data used."""
from __future__ import annotations
import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
S22=ROOT/"scripts"/"22_prepare_screening_adjudication_excel.py"
S23=ROOT/"scripts"/"23_analyze_adjudicated_screening.py"
NS="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
STRATA=[
    ("screen_include_core",120,9264),("screen_include_policy",80,899),
    ("screen_include_context",40,102),("screen_exclude",18,18),
    ("q1_not_article_ready",80,11393),("core_not_q1",30,848)
]
HEADERS=[
    "sample_id","title","abstract","publication_year","type",
    "relevance_code","discipline_code","primary_policy_code","reason"
]
KHEAD=["sample_id","stratum","openalex_id","ai_decision",
       "original_policy_dimension","original_disciplinary_area"]


def invoke(script,*args,successful=True):
    r=subprocess.run([sys.executable,str(script),*map(str,args)],
        capture_output=True,text=True)
    if successful and r.returncode:
        raise AssertionError("Synthetic test failure "+str(r.stderr[-3000:]))
    return r


def make_originals(root):
    private=root/"rating_private";private.mkdir()
    keys=[];reviewers={"a":[],"b":[]}
    pos=0
    for stratum,n,pop in STRATA:
        for _ in range(n):
            i=pos
            pos+=1
            id=f"P{pos:04d}"
            keys.append(dict(zip(KHEAD,[
                id,stratum,"FAKE_IDENTIFIER_"+str(pos),
                "exclude" if stratum=="screen_exclude" else "include_core",
                "",""])))
            for rater in ("a","b"):
                relevance="2" if rater=="b" and i<89 else "1"
                discipline="ssh" if rater=="b" and 89<=i<307 else "general_he"
                policy="assessment" if rater=="b" and 133<=i<316 else "teaching_learning"
                reviewers[rater].append(dict(zip(HEADERS,[
                   id,"Synthetic Title identical for all",
                   "Artificial abstract used for CI tests only",
                   "2022","journal-article",relevance,
                   discipline,policy,"Synthetic human rationale"])))
    with (private/"sampling_key.csv").open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=KHEAD);w.writeheader();w.writerows(keys)
    for rater in ("a","b"):
        with (private/f"rater_{rater}.csv").open("w",newline="",encoding="utf-8-sig") as f:
            w=csv.DictWriter(f,fieldnames=HEADERS)
            w.writeheader();w.writerows(reviewers[rater])
    p21=root/"phase21.json"
    p21.write_text(json.dumps({
        "status":"complete_independent_ratings_not_yet_adjudicated",
        "results":{"flagged_for_human_adjudication":{
            "any_relevance_disagreement":89,
            "any_discipline_disagreement":218,
            "any_policy_dimension_disagreement":183,
            "unique_records_disagreeing_in_one_or_more_fields":316
        }}))
    p05=root/"phase05.json"
    p05.write_text(json.dumps({
        "sample_size":368,
        "strata":{name:{"sample_n":n,"population_n":pop}
                  for name,n,pop in STRATA}}))
    return private,p05,p21


def fill_xlsx(original,returned,complete=True,corrupt=False):
    with zipfile.ZipFile(original) as inp:
        with zipfile.ZipFile(returned,"w",compression=zipfile.ZIP_DEFLATED) as out:
            for info in inp.infolist():
                data=inp.read(info.filename)
                if info.filename=="xl/worksheets/sheet2.xml":
                    sheet=ET.fromstring(data)
                    for cell in sheet.findall(f".//{{{NS}}}sheetData/{{{NS}}}row/{{{NS}}}c"):
                        ref=cell.get("r")
                        if ref is None:continue
                        col="".join(c for c in ref if c.isalpha())
                        rn=int("".join(c for c in ref if c.isdigit()))
                        if 2<=rn<=317 and col in ("N","O","P","Q"):
                            if not complete and rn==316:
                                continue
                            value={
                                "N":"2",
                                "O":"ssh",
                                "P":"assessment",
                                "Q":"Reviewed evidence and arrived at consensus"
                            }[col]
                            t=cell.find(f"{{{NS}}}is/{{{NS}}}t")
                            assert t is not None
                            t.text=value
                        if corrupt and ref=="B2":
                            t=cell.find(f"{{{NS}}}is/{{{NS}}}t")
                            t.text="TAMPERED SOURCE ARTICLE"
                    data=ET.tostring(sheet,encoding="utf-8",xml_declaration=True)
                out.writestr(info,data)


def scenario(complete=True,corrupt=False):
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        private,p05,p21=make_originals(root)
        original_folder=root/"original"
        out22=root/"public22"
        invoke(S22,"--private-in",private,"--private-out",original_folder,
             "--out",out22,"--phase21-report",p21)
        orig=original_folder/"Adjudicacion_Cribado_Fase22.xlsx"
        ret=root/"returned.xlsx"
        fill_xlsx(orig,ret,complete,corrupt)
        result=invoke(S23,"--original-xlsx",orig,"--returned-xlsx",ret,
            "--private-in",private,"--phase05-report",p05,
            "--phase21-report",p21,
            "--phase22-report",out22/"screening_adjudication_packet_aggregate.json",
            "--out",root/"public23",successful=not corrupt)
        if corrupt:
            assert result.returncode!=0
            assert "modified" in result.stderr
            return
        r=json.loads((root/"public23/adjudicated_screening_aggregate.json").read_text())
        assert "FAKE_IDENTIFIER" not in json.dumps(r)
        assert "Synthetic Title" not in json.dumps(r)
        assert "P0001" not in json.dumps(r)
        return r


class TestPhase23(unittest.TestCase):
    def test_blank_adjudication_is_not_consensus(self):
        r=scenario(complete=False)
        self.assertEqual(r["status"],"awaiting_human_screening_adjudication")
        self.assertNotIn("results",r)
        self.assertEqual(r["adjudication_readiness"]["reason"]["filled"],315)

    def test_finished_adjudication_gets_aggregate_not_accuracy(self):
        r=scenario(complete=True)
        self.assertEqual(r["status"],"completed_human_screening_adjudication_aggregate_QA_pending")
        self.assertEqual(r["results"]["human_consensus_source"],
                         {"adjudicated":316,"unanimous_retained":52})
        self.assertEqual(r["integrity"]["counts"]["unique"],316)
        self.assertEqual(r["results"]["per_stratum_descriptive_counts"][
            "screen_include_core"]["n"],120)
        self.assertEqual(r["results"]["weighted_four_screening_strata"][
            "target_final_screened_population_N"],10283)
        self.assertEqual(r["results"]["adjudication_quality_diagnostics"][
            "conflicting_dimension_choice"]["relevance"]["conflicting_cases"],89)
        self.assertIn("NOT_COMPUTED",r["results"]["classifier_performance_status"])

    def test_detect_original_evidence_tampering(self):
        scenario(complete=True,corrupt=True)


if __name__=="__main__":
    unittest.main()
