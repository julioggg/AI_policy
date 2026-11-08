#!/usr/bin/env python3
"""Synthetic-only Phase27 integrity, no-fabrication and methodological stop-rule tests."""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile
import xml.etree.ElementTree as ET
import importlib.util

ROOT=Path(__file__).resolve().parents[1]
S27=ROOT/"scripts"/"27_audit_panel_reconciliation.py"
NS="http://schemas.openxmlformats.org/spreadsheetml/2006/main"

def mod(name,ref):
    location=ROOT/"scripts"/name
    spec=importlib.util.spec_from_file_location(ref,location)
    target=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(target)
    return target

def create_original(path):
    excel=mod("17_excel_reviewer_packages.py","phase27_test_excel")
    pack=mod("18_prepare_blinded_adjudication_excel.py","phase27_test_pack")
    fields=mod("26_prepare_methodological_reconciliation.py","phase27_test_fields")
    records=[]
    for i in range(80):
        q=f"Q{i+1:04d}"
        relevant_old="2" if i<2 else "1"
        policy_old="equity_access" if i==2 else "teaching_learning"
        rel_qa="3" if i<47 else relevant_old
        disc_qa="ssh" if i>=22 else "general_he"
        pol_qa="ethics_integrity" if i<71 else policy_old
        flags=(rel_qa!=relevant_old,
               disc_qa!="general_he",
               pol_qa!=policy_old)
        row={
            "qa_code":q,"title":"Synthetic disclosure-protected title",
            "abstract":"Fictitious higher education AI research abstract.",
            "publication_year":"2024","type":"article",
            "relevance_a":relevant_old,"relevance_b":relevant_old,
            "consensus_relevance":relevant_old,
            "independent_qa_relevance":rel_qa,
            "discipline_a":"general_he","discipline_b":"general_he",
            "consensus_discipline":"general_he",
            "independent_qa_discipline":disc_qa,
            "policy_a":policy_old,"policy_b":policy_old,
            "consensus_policy":policy_old,
            "posthoc_normalized_qa_policy":pol_qa,
            "consensus_reason":"synthetic previously adjudicated reason",
            "qa_original_reason":"synthetic independent reviewer rationale",
            "qa_corrected_reason":"synthetic later edit rationale",
            "relevance_disagreement":"SÍ" if flags[0] else "NO",
            "discipline_disagreement":"SÍ" if flags[1] else "NO",
            "policy_disagreement":"SÍ" if flags[2] else "NO",
            "panel_final_relevance":"",
            "panel_final_discipline":"",
            "panel_final_policy":"",
            "panel_rationale":"",
        }
        records.append({"group_code":q,**row})
    return pack.xlsx_generic(path,[
        ("INSTRUCCIONES",excel.basic_sheet([["Instruction","Synthetic only"]],[40,90])),
        ("CASOS",excel.section_xml("DOCUMENTOS",fields.FIELDS,fields.HEADERS,
            records,[22]*len(fields.FIELDS),fields.EDIT)),
        ("ESCALAS",excel.basic_sheet([["Code","Definition"],["0","Synthetic"]],[20,80])),
    ],excel)


def complete_book(original,returned,partial=False,tamper=False):
    with zipfile.ZipFile(original) as z:
        with zipfile.ZipFile(returned,"w",compression=zipfile.ZIP_DEFLATED) as dst:
            for entry in z.infolist():
                data=z.read(entry.filename)
                if entry.filename=="xl/worksheets/sheet2.xml":
                    root=ET.fromstring(data)
                    for node in root.findall(f".//{{{NS}}}sheetData/{{{NS}}}row/{{{NS}}}c"):
                        ref=node.get("r","")
                        col="".join(x for x in ref if x.isalpha())
                        rn=int("".join(x for x in ref if x.isdigit()))
                        idx=rn-2
                        if rn<2 or rn>81: continue
                        t=node.find(f"{{{NS}}}is/{{{NS}}}t")
                        if t is None: continue
                        if tamper and rn==2 and col=="B":
                            t.text="INJECTED TAMPERED SOURCE"
                        if partial and rn==3 and col=="AA":
                            continue
                        if col=="X":t.text="1"
                        if col=="Y":t.text="general_he"
                        if col=="Z":t.text="teaching_learning"
                        if col=="AA":t.text="[R1] Synthetic documented evidence supports original"
                    data=ET.tostring(root,encoding="utf-8",xml_declaration=True)
                dst.writestr(entry,data)


def scenario(partial=False,tamper=False):
    with tempfile.TemporaryDirectory() as td:
        base=Path(td)
        private=base/"private";private.mkdir()
        original=private/"Original.xlsx"
        create_original(original)
        returned_dir=base/"returned";returned_dir.mkdir()
        returned=returned_dir/"Finished.xlsx"
        complete_book(original,returned,partial=partial,tamper=tamper)
        p25=base/"phase25.json"
        p25.write_text(json.dumps({
            "status":"independent_qa_scored_with_posthoc_policy_normalization",
            "results":{
                "relevance_mismatch_cases":47,
                "discipline_mismatch_cases":58,
                "post_hoc_policy_mismatch_cases":71
            }
        }))
        p26=base/"phase26.json"
        p26.write_text(json.dumps({
            "status":"private_methodological_reconciliation_packet_prepared_NO_new_human_decisions",
            "cases":80,"panel_decisions_filled":0,
            "mismatch_counts":{
                "mismatch_relevance":47,
                "mismatch_discipline":58,
                "mismatch_policy":71,
                "unique_cases_with_mismatch":80
            }
        }))
        out=base/"aggregates"
        cmd=[sys.executable,str(S27),"--original-xlsx",str(original),
             "--returned-xlsx",str(returned),
             "--phase25-report",str(p25),
             "--phase26-report",str(p26),"--out",str(out)]
        p=subprocess.run(cmd,capture_output=True,text=True)
        if tamper:
            if p.returncode==0:
                raise AssertionError("Modified immutable source passed audit!")
            assert "edited" in p.stderr.lower()
            return None
        if p.returncode:
            raise AssertionError("Synthetic Phase27 failed:\n"+p.stderr[-3000:])
        report=json.loads((out/"panel_reconciliation_audit_aggregate.json").read_text())
        blob=json.dumps(report)
        assert "Q0001" not in blob
        assert "Synthetic disclosure-protected title" not in blob
        assert "INJECTED" not in blob
        return report


class TestPhase27(unittest.TestCase):
    def test_completed_human_panel_is_not_blind_validation(self):
        r=scenario()
        self.assertEqual(r["status"],
            "completed_panel_reconciliation_reviewed_not_independently_validated")
        self.assertEqual(r["readiness"]["relevance"]["filled"],80)
        self.assertEqual(r["readiness"]["scientific_justification"]["filled"],80)
        self.assertEqual(r["results"]["relevance"]["retained_prior_consensus"],78)
        self.assertEqual(r["results"]["discipline"]["retained_prior_consensus"],80)
        self.assertEqual(r["results"]["policy_posthoc"]["retained_prior_consensus"],79)
        self.assertFalse(r["results"]["scientific_stop_rule"][
            "phase23_population_estimates_automatically_updated"])

    def test_incomplete_panel_cannot_be_called_complete(self):
        r=scenario(partial=True)
        self.assertEqual(r["status"],"awaiting_panel_reconciliation_human_decisions")
        self.assertNotIn("results",r)
        self.assertEqual(r["readiness"]["scientific_justification"]["filled"],79)

    def test_immutable_evidence_tamper_rejected(self):
        scenario(tamper=True)


if __name__=="__main__":
    unittest.main()
