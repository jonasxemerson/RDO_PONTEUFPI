#!/usr/bin/env python3
"""Testes do inventário CAD; desenho sintético apenas de teste, nunca de projeto."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

import ezdxf

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("auditar_dxf_projeto", ROOT / "scripts/auditar_dxf_projeto.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

class DXFAuditTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.path = self.root / "PRANCHA-TESTE.dxf"
        doc = ezdxf.new("R2010")
        doc.header["$INSUNITS"] = 6
        ms = doc.modelspace()
        ms.add_line((0, 0), (10, 0), dxfattribs={"layer": "EIXOS"})
        ms.add_circle((3, 4), 0.5, dxfattribs={"layer": "FUNDACOES"})
        doc.saveas(self.path)

    def test_single_dxf_detected_without_homologation(self):
        result = audit.build_report(self.path)
        self.assertEqual(result["total_files"], 1)
        self.assertFalse(result["geometry_approved"])
        self.assertFalse(result["publishable_bim"])
        f = result["files"][0]
        self.assertEqual(f["insunits_code"], 6)
        self.assertFalse(f["units_verified_against_drawing"])
        self.assertEqual(f["modelspace_entities"], 2)
        self.assertEqual(f["entity_types"], {"CIRCLE": 1, "LINE": 1})
        self.assertIsNotNone(f["raw_cad_extents"])

    def test_zip_and_directory_match(self):
        zpath = self.root / "entrada.zip"
        with ZipFile(zpath, "w") as z:
            z.write(self.path, arcname="pranchas/PRANCHA-TESTE.dxf")
        self.assertEqual(audit.build_report(zpath)["source_hashes_sha256"],
                         audit.build_report(self.path)["source_hashes_sha256"])

    def test_zip_traversal_rejected(self):
        zpath = self.root / "malicioso.zip"
        with ZipFile(zpath, "w") as z:
            z.writestr("../evasao.dxf", self.path.read_bytes())
        with self.assertRaisesRegex(ValueError, "inseguro"):
            audit.build_report(zpath)

    def test_missing_inputs_rejected(self):
        empty = self.root / "vazio"
        empty.mkdir()
        with self.assertRaisesRegex(ValueError, "Nenhum DXF"):
            audit.build_report(empty)

    def test_raw_cad_entity_count_not_pile_count(self):
        result = audit.build_report(self.path)
        self.assertEqual(result["files"][0]["identified_project_elements"], [])
        self.assertIn("divergencia", result["critical_checks"]["prancha_11_vs_base_292_estacas"])

if __name__ == "__main__":
    unittest.main()
