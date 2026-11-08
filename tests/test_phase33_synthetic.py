#!/usr/bin/env python3
"""Synthetic Phase33 test: private panel adjudication and source integrity."""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile
import xml.etree.ElementTree as ET

from test_phase28_synthetic import synthetic_frame
from test_phase32_synthetic import fill as fill_rater

ROOT=Path(__file__).resolve().parents[1]
SCRIPT30=ROOT/"scripts"/"30_prepare_full1200_validation.py"
SCRIPT32=ROOT/"scripts"/"32_audit_pi_attested_human1200.py"
SCRIPT33=ROOT/"scripts"/"33_audit_returned_panel1200.py"
CODEBOOK=ROOT/"docs"/"phase30_full_validation_codebook_v1.0.md"
NS="http://schemas.openxmlformats.org/spreadsheetml/2006/main"


def run(script,*args):
    return subprocess.run([sys.executable,str(script),*map(str,args)],
                          capture_output=True,text=True)


def returned_panel(pristine,returned,tamper=False,incomplete=False):
    with zipfile.ZipFile(pristine) as src:
        with zipfile.ZipFile(returned,"w",compression=zipfile.ZIP_DEFLATED) as target:
            for item in src.infolist():
                blob=src.read(item.filename)
                if item.filename=="xl/worksheets/sheet2.xml":
                    root=ET.fromstring(blob)
                    for row in root.findall(f".//{{{NS}}}sheetData/{{{NS}}}row"):
                        number=int(row.get("r","0"))
                        if number<2:continue
                        bycell={c.get("r"):c for c in row.findall(f"{{{NS}}}c")}
                        def value(letter):
                            x=bycell[letter+str(number)].find(f"{{{NS}}}is/{{{NS}}}t")
                            return (x.text or "") if x is not None else ""
                        relevance=value("H")
                        newvalues={
                          "W":value("F"),"X":relevance,"Y":value("J"),
                          "Z":value("L"),
                          "AA":"Case-specific consideration of source text and two original reviewers.",
                          "AB":"yes" if relevance=="9" or value("R")=="yes" else "no"
                        }
                        if incomplete and number==2:
                            newvalues["AA"]=""
                        for letter,val in newvalues.items():
                            x=bycell[letter+str(number)].find(f"{{{NS}}}is/{{{NS}}}t")
                            if x is not None:x.text=val
                        if tamper and number==2:
                            bycell["B2"].find(f"{{{NS}}}is/{{{NS}}}t").text="MODIFIED ARTICLE"
                    blob=ET.tostring(root,encoding="utf-8",xml_declaration=True)
                target.writestr(item,blob)


def scenario(tamper=False,incomplete=False):
    with tempfile.TemporaryDirectory() as d:
        temp=Path(d)
        project,frame,key,phase05,old=synthetic_frame(temp)
        blank=temp/"original";out30=temp/"phase30"
        p=run(SCRIPT30,"--project",project,"--source-frame",frame,
              "--source-format","csv","--phase05-key",key,
              "--phase05-report",phase05,"--codebook",CODEBOOK,
              "--private-out",blank,"--out",out30)
        assert p.returncode==0,p.stderr[-2500:]
        received=temp/"rated";received.mkdir()
        fill_rater(blank/"Validacion_1200_A.xlsx",received/"A.xlsx","A")
        fill_rater(blank/"Validacion_1200_B.xlsx",received/"B.xlsx","B")
        panel=temp/"panel";out32=temp/"out32"
        p=run(SCRIPT32,"--original-a",blank/"Validacion_1200_A.xlsx",
          "--original-b",blank/"Validacion_1200_B.xlsx",
          "--returned-a",received/"A.xlsx","--returned-b",received/"B.xlsx",
          "--manifest",blank/"private_locked_manifest.json",
          "--codebook",CODEBOOK,"--phase30-report",out30/"full_validation_packet_aggregate.json",
          "--private-out",panel,"--out",out32,"--acknowledge-legacy-ai-metadata")
        assert p.returncode==0,p.stderr[-2500:]
        src=panel/"Adjudicacion_Validacion_1200_Humana.xlsx"
        returned_folder=temp/"returned_panel_private"
        returned_folder.mkdir()
        finished=returned_folder/"returned_panel.xlsx"
        returned_panel(src,finished,tamper=tamper,incomplete=incomplete)
        out33=temp/"out33"
        p=run(SCRIPT33,
              "--original-panel-xlsx",src,
              "--returned-panel-xlsx",finished,
              "--phase32-report",out32/"human_expert_agreement_aggregate.json",
              "--codebook",CODEBOOK,
              "--phase30-manifest",blank/"private_locked_manifest.json",
              "--out",out33)
        if tamper:
            assert p.returncode!=0,p.stdout+"\n"+p.stderr[-2500:]
            assert "historical" in p.stderr.lower() or "changed" in p.stderr.lower()
            return None
        if incomplete:
            assert p.returncode!=0,p.stdout+"\n"+p.stderr[-2500:]
            assert "incomplete" in p.stderr.lower() or "inadequate" in p.stderr.lower()
            return None
        assert p.returncode==0,p.stdout+"\n"+p.stderr[-2500:]
        return json.loads((out33/"panel_adjudication_aggregate.json").read_text())

class TestPhase33(unittest.TestCase):
    def test_completed_panel_audit_aggregate_only(self):
        result=scenario()
        self.assertTrue(result["panel_all_mandatory_fields_complete"])
        self.assertFalse(result["classifier_accuracy_calculated"])
        self.assertFalse(result["fulltext_actual_access_documented"])
        self.assertIn("panel_provenance_diagnostics",result)
        self.assertFalse(result["panel_provenance_diagnostics"]["human_authorship_verified_from_workbook"])
        self.assertTrue(result["panel_provenance_diagnostics"]["actual_panel_was_informed_by_visible_AB_ratings"])
        self.assertTrue(result["panel_provenance_diagnostics"]["hashes_not_published_to_public_report"])
        self.assertEqual(result["casebook_n"],result["panel_scientific_reason_diagnostics"]["total"])
        self.assertNotIn("MODIFIED ARTICLE",json.dumps(result))
        self.assertNotIn("VAL0001",json.dumps(result))

    def test_tampered_source_rejected(self):
        scenario(tamper=True)

    def test_incomplete_adjudication_rejected(self):
        scenario(incomplete=True)

if __name__=="__main__":
    unittest.main()
