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
assert c["registros_pendentes"] == 1, "Única pendência legada ambígua deve permanecer separada"
assert c["registros_homologados"] == 59, "18 relatos de campo do dia 24 devem estar homologados"
assert state["data_referencia"] == "2026-11-24", "Data da última homologação divergente"
field = c["execucao_em_campo"]
assert field["sem_contagem_dupla"] is True
piles = field["estacas_por_eixo"]
assert piles["E07"]["executadas_em_campo"] == 19
assert piles["E08"]["executadas_em_campo"] == 13
assert piles["E09"]["executadas_em_campo"] == 25
assert piles["E09"]["previstas_projeto"] == 24
assert piles["E09"]["diferenca_executado_menos_previsto"] == 1
assert piles["E09"]["locacao_conforme_projeto"] == "nao_verificada"
assert piles["E09"]["participacao_na_resistencia"] == "nao_determinada"
assert field["longarinas"]["concretadas_em_campo"] == 3
assert field["pilares_parciais_E03"]["metades_inferiores_concretadas"] == 2
assert field["pilares_parciais_E03"]["concretagem_superior_confirmada"] is False

# O indicador de evolução usa a última execução homologada por eixo, jamais somente
# os 111 da base histórica ou a soma indiscriminada dos totais de diferentes dias.
evo=c["evolucao_fisica"]
assert len(evo["estacas_por_eixo"])==9
assert evo["total_estacas_execucao_registrada"] == 145, evo
assert evo["total_estacas_previstas_projeto"] == 292
assert evo["total_estacas_concretadas_identificadas"] == 111
assert evo["indicador_execucao_etapas_mistas"] is True
observed=[x["executadas_registradas"] for x in evo["estacas_por_eixo"]]
assert observed == [24,32,32,0,0,0,19,13,25], observed
concreted=[x["concretadas_identificadas"] for x in evo["estacas_por_eixo"]]
assert concreted == [24,32,32,0,0,0,4,11,8], concreted
assert [x["origem_execucao"] for x in evo["estacas_por_eixo"][6:]] == ["campo_homologado"]*3
assert [x["origem_execucao"] for x in evo["estacas_por_eixo"][:6]] == ["base_historica"]*6
assert evo["estacas_por_eixo"][8]["excedente_executado"] == 1
assert evo["estacas_por_eixo"][8]["participacao_resistente"] == "nao_determinada"
assert evo["total_longarinas_concretadas_em_campo"] == 3
assert evo["total_pilares_integralmente_concretados_registrados"] == 6
assert evo["total_blocos_concluidos_registrados"] == 2
assert evo["pilares_E03_concretagem_parcial"]["concretagem_superior_confirmada"] is False
assert evo["prelajes_acrescimos_reportados_novembro"] == 218
assert evo["prelajes_estoque_total"] is None
assert len({x["eixo"] for x in evo["estacas_por_eixo"]}) == 9
assert all(x["concretadas_identificadas"]<=x["executadas_registradas"]
           for x in evo["estacas_por_eixo"])

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
assert 'id="fieldProgress"' in html
assert 'id="fieldCaveat"' in html
print(f"OK: {c['registros_homologados']} homologados, {c['registros_pendentes']} pendente(s), "
      f"{c['total_estacas_concretadas_base_mais_snapshots']} estacas, "
      f"{c['total_pilares_concretados_base_mais_snapshots']} pilares, "
      "longarinas 1 observada + 1 inferida.")
