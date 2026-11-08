#!/usr/bin/env python3
"""Synthetic end-to-end Phase25 tests (zero real publications or human data)."""
from __future__ import annotations
import csv
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile

from test_phase23_synthetic import make_originals,fill_xlsx

ROOT=Path(__file__).resolve().parents[1]
S22=ROOT/"scripts"/"22_prepare_screening_adjudication_excel.py"
S23=ROOT/"scripts"/"23_analyze_adjudicated_screening.py"
S24=ROOT/"scripts"/"24_prepare_blinded_screening_qa.py"
S25=ROOT/"scripts"/"25_compare_independent_screening_qa.py"
NS="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
MAP_HEADERS=["Código QA","Relevancia QA","Título","Resumen",
  "Categoría original","Propuesta técnica","CÓDIGO FINAL","Estado",
  "Justificación QA","Nota del validador"]
RAW=["Ninguna (Uso General)","Ética y Gobernanza","Ética y Plagio",
     "Marco Político/Regulatorio","N/A"]
PROPOSED={
 "Ninguna (Uso General)":"not_applicable",
 "Ética y Gobernanza":None,
 "Ética y Plagio":"ethics_integrity",
 "Marco Político/Regulatorio":"governance_policy",
 "N/A":"not_applicable",
}


def run(script,*args):
    r=subprocess.run([sys.executable,str(script),*map(str,args)],
        capture_output=True,text=True)
    if r.returncode:
        raise AssertionError("Failure in "+script.name+"\n"+r.stderr[-3000:])
    return r.stdout


def module(file,tag):
    spec=importlib.util.spec_from_file_location(tag,ROOT/"scripts"/file)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod


def fill_QA(original,target):
    with zipfile.ZipFile(original) as inp:
        with zipfile.ZipFile(target,"w",compression=zipfile.ZIP_DEFLATED) as out:
            for info in inp.infolist():
                data=inp.read(info.filename)
                if info.filename=="xl/worksheets/sheet2.xml":
                    sheet=ET.fromstring(data)
                    for cell in sheet.findall(f".//{{{NS}}}sheetData/{{{NS}}}row/{{{NS}}}c"):
                        ref=cell.get("r","")
                        col="".join(x for x in ref if x.isalpha())
                        row=int("".join(x for x in ref if x.isdigit()))
                        if row>=2 and col in ("F","G","H","I"):
                            idx=(row-2)%5
                            value={
                               "F":str(idx if idx<4 else 9),
                               "G":"ssh" if idx%2 else "general_he",
                               "H":RAW[idx],
                               "I":"Evidence-based independent explanation of this synthetic publication"
                            }[col]
                            t=cell.find(f"{{{NS}}}is/{{{NS}}}t")
                            assert t is not None
                            t.text=value
                    data=ET.tostring(sheet,encoding="utf-8",xml_declaration=True)
                out.writestr(info,data)


def make_map(private,blank_ambiguous):
    excel=module("17_excel_reviewer_packages.py","p25_excel")
    pack=module("18_prepare_blinded_adjudication_excel.py","p25_pack")
    qa_path=private/"QA_completado.xlsx"
    import zipfile
    with zipfile.ZipFile(qa_path) as z:
        sheets=excel.xlsx_sheet(z,"xl/worksheets/sheet2.xml",[])
    data=[]
    for entry in sheets[1:]:
        i=len(data)
        raw=RAW[i%5]
        proposed=PROPOSED[raw]
        decided=(proposed or "ethics_integrity")
        if blank_ambiguous and raw=="Ética y Gobernanza":
            decided=""
        data.append({
            "group_code":f"Q{i+1:04d}",
            "code":entry[0],
            "relevance":entry[5],
            "title":entry[1],
            "abstract":entry[2],
            "original":raw,
            "proposal":proposed or "",
            "final":decided,
            "status":"review",
            "reason":entry[8],
            "notes":""
        })
    fields=["code","relevance","title","abstract","original","proposal",
            "final","status","reason","notes"]
    output=private/"QA_map.xlsx"
    pack.xlsx_generic(output,[
        ("NORMALIZACION",excel.section_xml("DOCUMENTOS",fields,MAP_HEADERS,data,
            [14,18,44,60,30,25,25,18,55,40],{6:None}))
    ],excel)
    return output


def scenario(with_mapping=False,blank_ambiguous=False):
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        private,p05,p21=make_originals(root)
        p22dir=root/"orig22";report22=root/"public22"
        run(S22,"--private-in",private,"--private-out",p22dir,
            "--phase21-report",p21,"--out",report22)
        original22=p22dir/"Adjudicacion_Cribado_Fase22.xlsx"
        completed22=root/"completed22.xlsx"
        fill_xlsx(original22,completed22,True)
        report23=root/"public23"
        run(S23,"--original-xlsx",original22,"--returned-xlsx",completed22,
           "--private-in",private,"--phase05-report",p05,
           "--phase21-report",p21,
           "--phase22-report",report22/"screening_adjudication_packet_aggregate.json",
           "--out",report23)
        p24dir=root/"private24";report24=root/"public24"
        run(S24,"--original-xlsx",original22,"--completed-xlsx",completed22,
            "--private-in",private,"--phase05-report",p05,
            "--phase22-report",report22/"screening_adjudication_packet_aggregate.json",
            "--phase23-report",report23/"adjudicated_screening_aggregate.json",
            "--private-out",p24dir,"--out",report24)
        origQA=p24dir/"Control_Independiente_Cribado_Fase24.xlsx"
        received=p24dir/"QA_completado.xlsx"
        fill_QA(origQA,received)
        arguments=[
            "--qa-original-xlsx",origQA,
            "--qa-returned-xlsx",received,
            "--qa-private-key",p24dir/"correspondencia_qa_privada.csv",
            "--phase24-report",report24/"quality_audit_packet_aggregate.json",
            "--out",root/"report25"
        ]
        if with_mapping:
            mapfile=make_map(p24dir,blank_ambiguous)
            arguments+=["--normalization-xlsx",mapfile]
        run(S25,*arguments)
        public=json.loads((root/"report25/independent_screening_qa_aggregate.json").read_text())
        out=json.dumps(public)
        assert "Synthetic Title" not in out
        assert "FAKE_IDENTIFIER" not in out
        assert "Q0001" not in out
        assert "P0001" not in out
        return public


class TestPhase25(unittest.TestCase):
    def test_independent_relevance_discipline_with_nonstandard_policy(self):
        r=scenario(False)
        self.assertEqual(r["sample_n"],80)
        self.assertIn("policy_normalization_pending",r["status"])
        self.assertEqual(r["results"]["policy_original_QA_labels_outside_rubric_n"],80)
        self.assertNotIn("post_hoc_normalized_policy_vs_prior_consensus",r["results"])

    def test_partial_normalization_does_not_masquerade_as_complete(self):
        r=scenario(True,True)
        self.assertEqual(r["policy_normalization"]["validated_final_codes"],64)
        self.assertEqual(r["policy_normalization"]["pending_ambiguous_or_revised_codes"],16)
        self.assertNotIn("post_hoc_normalized_policy_vs_prior_consensus",r["results"])

    def test_complete_normalization_keeps_provenance(self):
        r=scenario(True,False)
        self.assertEqual(r["status"],
            "independent_qa_scored_with_posthoc_policy_normalization")
        self.assertEqual(r["policy_normalization"]["validated_final_codes"],80)
        self.assertEqual(r["results"]["qa_policy_codebook_status"],
            "post_hoc_normalized_mixed_analyst_and_expert")
        self.assertEqual(r["results"]["independent_QA_relevance_vs_prior_human_consensus"][
            "paired_all_including_9"],80)


if __name__=="__main__":
    unittest.main()
