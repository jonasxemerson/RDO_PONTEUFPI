#!/usr/bin/env python3
"""Testa idempotência da consolidação, sem recontar snapshots e ordinais."""
import json
from pathlib import Path
from consolidar_dados import build_state

root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / "data/manifest.json").read_text(encoding="utf-8"))
events = []
for p in manifest["files"]:
    events += json.loads((root / p).read_text(encoding="utf-8"))["events"]
assert len(events) == len({e["id"] for e in events}), "IDs duplicados"
state = build_state(root)
again = build_state(root)
assert state == again, "Consolidação instável"
c = state["consolidacao"]
assert state["classification"] == "consolidacao_parcial_para_acompanhamento"
assert sum(state["estacas"]["previstas_por_eixo"]) == 292
assert c["registros_totais"] == len(events)
assert c["registros_homologados"] + c["registros_pendentes"] == len(events)
assert c["registros_homologados"] >= 41
assert c["registros_pendentes"] >= 1
assert state["estacas"]["historicas_por_eixo"][7] == 11, "E08 contou duas vezes"
assert state["pilares"]["historicos_por_eixo"][2] >= 2, "Dois pilares E03 não consolidados"
assert c["total_estacas_concretadas_base_mais_snapshots"] >= 111
assert c["total_pilares_concretados_base_mais_snapshots"] >= 6
assert c["longarinas_concretadas_observadas"] == 1
assert c["longarinas_concretadas_inferidas"] == 1
assert c["inferencia_longarina_2_data_exata"] is None
details = c["detalhes"]
assert details["estacas_feitas_etapa_indefinida"]["E07"]["quantity"] >= 13
assert details["estacas_feitas_etapa_indefinida"]["E09"]["quantity"] >= 15
assert details["perfuracao_ordinal_em_andamento"]["E07"]["position"] >= 18
assert details["perfuracao_ordinal_em_andamento"]["E09"]["position"] >= 17
assert details["camisas_sem_concretagem"]["E08"]["quantity"] >= 6
assert not any(e["id"] == "wa-20261117-0852-e07-camisas-ambiguo"
               and e["validation"] in {"homologado_responsavel", "validado_campo"}
               for e in events), "Mensagem ambígua foi homologada indevidamente"
assert c["base_historica_ainda_nao_auditada_por_peca"] is True
assert state["estacas"]["historicas_por_eixo"][8] < details["estacas_feitas_etapa_indefinida"]["E09"]["quantity"], "Etapas indevidas"
assert c["detalhes"]["prelajes_acrescimos_nao_conciliados"], "Acréscimos de pré-lajes perdidos"
html = (root / "painel-cliente.html").read_text(encoding="utf-8")
assert "<!-- CERTARE_CONFIG -->" in html
assert "111 / 292" not in html, "KPI não deve ser fixo no HTML"
print(f"OK: {c['registros_homologados']} homologados, {c['registros_pendentes']} pendente(s), "
      f"{c['total_estacas_concretadas_base_mais_snapshots']} estacas, "
      f"{c['total_pilares_concretados_base_mais_snapshots']} pilares, "
      "longarinas 1 observada + 1 inferida.")
