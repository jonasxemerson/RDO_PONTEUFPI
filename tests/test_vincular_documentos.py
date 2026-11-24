import importlib.util
import unittest
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "scripts/vincular_documentos.py"
spec = importlib.util.spec_from_file_location("vincular_documentos", PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

SNAPSHOT = {
    "id_empreendimento": "ponte-ufpi",
    "eixos": [{"id": "E03"}, {"id": "E09"}],
    "referencias_eventos": [{"id": "wa-exemplo-01"}],
    "elementos_individualizados": [{"id": "E03-P03"}],
}
DOCUMENT = {
    "id": "DOC-001", "type": "rdo", "visibility": "privado",
    "reference": "arquivo-privado/RDO-001.pdf", "sha256": None, "version": "1",
}
LINK = {
    "document_id": "DOC-001", "target_type": "elemento",
    "target_id": "E03-P03", "status": "pendente_conferencia",
}
def manifest():
    return {"schema_version": "vinculos-documentais/1.0.0",
            "project": "ponte-ufpi", "documents": [dict(DOCUMENT)],
            "links": [dict(LINK)]}

class TestVinculosDocumentais(unittest.TestCase):
    def test_valid_and_never_approves(self):
        result = module.build_links(SNAPSHOT, manifest())
        self.assertEqual(result["counts"], {"documents": 1, "links": 1})
        self.assertEqual(result["status"], "proposta_nao_homologada")
        self.assertFalse(result["controls"]["publicavel"])
        self.assertFalse(result["controls"]["medicao_autorizada"])
        self.assertFalse(result["controls"]["aceite_tecnico_inferido"])

    def test_axis_and_event_targets(self):
        m = manifest()
        m["links"] = [
            {"document_id": "DOC-001", "target_type": "eixo", "target_id": "E09", "status": "referenciado"},
            {"document_id": "DOC-001", "target_type": "evento", "target_id": "wa-exemplo-01", "status": "referenciado"},
        ]
        self.assertEqual(module.build_links(SNAPSHOT, m)["counts"]["links"], 2)

    def test_unknown_element_rejected(self):
        m = manifest(); m["links"][0]["target_id"] = "E07-E99"
        with self.assertRaises(ValueError):
            module.build_links(SNAPSHOT, m)

    def test_duplicate_document_rejected(self):
        m = manifest(); m["documents"].append(dict(DOCUMENT))
        with self.assertRaises(ValueError):
            module.build_links(SNAPSHOT, m)

    def test_duplicate_link_rejected(self):
        m = manifest(); m["links"].append(dict(LINK))
        with self.assertRaises(ValueError):
            module.build_links(SNAPSHOT, m)

    def test_extra_fields_rejected(self):
        m = manifest(); m["links"][0]["approval"] = "liberado"
        with self.assertRaises(ValueError):
            module.build_links(SNAPSHOT, m)

    def test_invalid_sha_rejected(self):
        m = manifest(); m["documents"][0]["sha256"] = "123"
        with self.assertRaises(ValueError):
            module.build_links(SNAPSHOT, m)

    def test_no_snapshot_mutation(self):
        import copy
        original = copy.deepcopy(SNAPSHOT)
        module.build_links(SNAPSHOT, manifest())
        self.assertEqual(original, SNAPSHOT)

if __name__ == "__main__":
    unittest.main()
