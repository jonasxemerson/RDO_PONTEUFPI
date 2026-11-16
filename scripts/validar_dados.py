#!/usr/bin/env python3
"""Valida a estrutura mínima dos apontamentos versionados no GitHub."""
import json
from pathlib import Path
from datetime import date

allowed_targets = {"GERAL", "FAB"} | {f"E{i:02}" for i in range(1, 10)}
allowed_services = {"estacas", "longarina", "equipamento", "ambiental", "canteiro", "bloco", "pilar", "travessa", "prelaje", "tabuleiro"}
manifest = json.loads(Path("data/manifest.json").read_text(encoding="utf-8"))
assert manifest.get("schema_version") == 1, "Versão do manifesto inválida"
declared_files = manifest.get("files")
assert isinstance(declared_files, list) and declared_files, "Manifesto sem arquivos"
disk_files = sorted(str(p) for p in Path("data").glob("observacoes-*.json"))
assert sorted(declared_files) == disk_files, "Manifesto divergente dos arquivos de observações"
assert len(declared_files) == len(set(declared_files)), "Manifesto com arquivo repetido"
seen = set()
count = 0
for path in sorted(Path("data").glob("observacoes-*.json")):
    doc = json.loads(path.read_text(encoding="utf-8"))
    assert doc.get("schema_version") == 1, f"{path}: schema_version inválida"
    assert isinstance(doc.get("events"), list), f"{path}: sem array events"
    for event in doc["events"]:
        eid = event.get("id")
        assert isinstance(eid, str) and eid and eid not in seen, f"{path}: ID duplicado/inválido: {eid!r}"
        seen.add(eid)
        assert isinstance(event.get("date"), str) and len(event["date"]) == 10, f"{eid}: data inválida"
        date.fromisoformat(event["date"])
        assert event.get("target") in allowed_targets, f"{eid}: frente inválida"
        assert event.get("service") in allowed_services, f"{eid}: serviço inválido"
        assert isinstance(event.get("activity"), str) and event["activity"], f"{eid}: atividade vazia"
        assert event.get("validation") in {"relato_nao_homologado", "validado_campo", "inferido"}, f"{eid}: validação inválida"
        qty = event.get("quantity")
        assert qty is None or (isinstance(qty, int) and qty >= 0), f"{eid}: quantidade inválida"
        if event.get("state") == "snapshot":
            assert event.get("quantity_kind") == "total_reportado", f"{eid}: snapshot sem total_reportado"
        if qty is not None:
            assert event.get("quantity_kind"), f"{eid}: quantidade sem tipo"
        count += 1
    for inf in doc.get("inferences", []):
        assert inf.get("based_on_event") in seen, f"Referência da inferência inválida: {inf.get('id')}"
        assert inf.get("exact_date") is None, "Inferência não pode inventar data de execução"
print(f"OK: {count} observações e IDs únicos em data/.")
