#!/usr/bin/env python3
"""Valida a estrutura mínima dos apontamentos versionados no GitHub."""
import json
from pathlib import Path
from datetime import date

allowed_targets = {"GERAL", "FAB"} | {f"E{i:02}" for i in range(1, 10)}
allowed_services = {"estacas", "longarina", "equipamento", "ambiental", "canteiro", "bloco", "pilar", "travessa", "prelaje", "tabuleiro", "qualidade", "seguranca"}
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
    if doc.get("approval_state") == "homologado_com_ressalvas":
        auth = doc.get("homologacao", {})
        assert auth.get("data") and auth.get("escopo"), f"{path}: homologação sem rastreio"
        date.fromisoformat(auth["data"])
    for event in doc["events"]:
        eid = event.get("id")
        assert isinstance(eid, str) and eid and eid not in seen, f"{path}: ID duplicado/inválido: {eid!r}"
        seen.add(eid)
        assert isinstance(event.get("date"), str) and len(event["date"]) == 10, f"{eid}: data inválida"
        date.fromisoformat(event["date"])
        assert event.get("target") in allowed_targets, f"{eid}: frente inválida"
        assert event.get("service") in allowed_services, f"{eid}: serviço inválido"
        assert isinstance(event.get("activity"), str) and event["activity"], f"{eid}: atividade vazia"
        assert event.get("validation") in {"relato_nao_homologado", "validado_campo", "inferido", "homologado_responsavel", "pendente_esclarecimento"}, f"{eid}: validação inválida"
        qty = event.get("quantity")
        assert qty is None or (isinstance(qty, int) and qty >= 0), f"{eid}: quantidade inválida"
        if event.get("state") == "snapshot":
            assert event.get("quantity_kind") == "total_reportado", f"{eid}: snapshot sem total_reportado"
        if qty is not None:
            assert event.get("quantity_kind"), f"{eid}: quantidade sem tipo"
        if event.get("metric") is not None:
            assert event.get("state") == "snapshot", f"{eid}: métrica acumulada fora de snapshot"
            assert event.get("quantity_kind") == "total_reportado", f"{eid}: métrica sem total_reportado"
        if event.get("quantity_kind") == "ordinal_em_execucao":
            assert event.get("state") == "em_andamento", f"{eid}: ordinal não pode virar total concluído"
            assert event.get("service") == "estacas", f"{eid}: ordinal incompatível"
        count += 1
    for inf in doc.get("inferences", []):
        assert inf.get("based_on_event") in seen, f"Referência da inferência inválida: {inf.get('id')}"
        assert inf.get("exact_date") is None, "Inferência não pode inventar data de execução"
        assert inf.get("validation") in {"inferencia_tecnica_pendente_validacao",
                                         "homologada_por_inferencia"}, "Classificação de inferência inválida"
    for req in doc.get("planning_requests", []):
        rid = req.get("id")
        assert isinstance(rid, str) and rid and rid not in seen, f"{path}: pendência duplicada: {rid!r}"
        seen.add(rid)
        date.fromisoformat(req["date"])
        assert req.get("title"), f"{rid}: título ausente"
from consolidar_dados import build_state
state = build_state()
assert state["consolidacao"]["registros_totais"] == count
assert state["consolidacao"]["registros_homologados"] + state["consolidacao"]["registros_pendentes"] == count
print(f"OK: {count} observações, homologação tipada e reconciliação reconstituível.")
