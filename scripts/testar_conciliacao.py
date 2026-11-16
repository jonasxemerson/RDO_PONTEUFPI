#!/usr/bin/env python3
"""Conciliação sem homologar relatos ou adicionar snapshots à produção."""
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
doc=json.loads((root/"data/observacoes-2026-11.json").read_text(encoding="utf-8"))
events=doc["events"]
assert len(events)==len({x["id"] for x in events}), "IDs duplicados"
expected=[24,32,32,37,37,37,37,32,24]
historical=[24,32,32,0,0,0,4,11,8]
assert sum(expected)==292, "Total de estacas divergente"
assert sum(historical)==111, "Baseline histórica divergente"
assert all(a<=b for a,b in zip(historical,expected))
assert all(e["validation"]!="validado_campo" for e in events), "Revisar aprovação antes da publicação"
assert doc["approval_state"]=="revisao_pendente"
# Snapshot = última fotografia do estoque comunicado; nunca incremento.
snapshots={}
for e in sorted(events,key=lambda x:(x["date"],x.get("time",""))):
    if e.get("quantity_kind")=="total_reportado" and e.get("service")=="estacas":
        snapshots[e["target"]]=e["quantity"]
assert snapshots.get("E09")==15, f"Último snapshot E09 inesperado: {snapshots.get('E09')}"
assert snapshots.get("E07")==13, f"Último snapshot E07 inesperado: {snapshots.get('E07')}"
# Proíbe conclusão indevida com base em relatos de etapa não especificada.
assert historical[8] != snapshots["E09"], "Snapshot E09 não deve substituir concretadas"
assert historical[6] != snapshots["E07"], "Snapshot E07 não deve substituir concretadas"
html=(root/"painel-cliente.html").read_text(encoding="utf-8")
engine=(root/"scripts/modelo-4d-publico.js").read_text(encoding="utf-8")
assert "111 / 292" in html and "2 / 9" in html and "4 / 36" in html
assert "24,32,32,0,0,0,4,11,8" in html and "24,32,32,0,0,0,4,11,8" in engine
print(f"OK: base histórica {sum(historical)}/{sum(expected)}; {len(events)} relatos pendentes; E07={snapshots['E07']}, E09={snapshots['E09']} (etapa desconhecida).")
