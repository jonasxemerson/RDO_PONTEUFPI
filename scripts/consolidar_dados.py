#!/usr/bin/env python3
"""Reconcilia a base legada com snapshots de campo, sem somar reportes cumulativos.

O estado construído aqui é um retrato técnico de acompanhamento, não uma medição.
"""
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APPROVED = {"homologado_responsavel", "validado_campo"}


def build_state(root=ROOT):
    root = Path(root)
    legacy = json.loads((root / "data/indicadores-historicos.json").read_text(encoding="utf-8"))
    manifest = json.loads((root / "data/manifest.json").read_text(encoding="utf-8"))
    events, inferences = [], []
    ids = set()
    for file in manifest["files"]:
        doc = json.loads((root / file).read_text(encoding="utf-8"))
        for event in doc.get("events", []):
            if event["id"] in ids:
                raise ValueError("Evento duplicado: " + event["id"])
            ids.add(event["id"])
            events.append(event)
        inferences.extend(doc.get("inferences", []))
    ordered = sorted(events, key=lambda x: (x["date"], x.get("time", ""), x["id"]))
    approved = [e for e in ordered if e.get("validation") in APPROVED]
    pending = [e for e in ordered if e.get("validation") not in APPROVED]
    piles = copy.deepcopy(legacy["estacas"]["historicas_por_eixo"])
    pillars = copy.deepcopy(legacy["pilares"]["historicos_por_eixo"])
    blocks = copy.deepcopy(legacy["blocos"]["historicos_por_eixo"])
    latest = {}

    for e in approved:
        if e.get("state") != "snapshot" or e.get("quantity_kind") != "total_reportado":
            continue
        metric, target = e.get("metric"), e.get("target")
        if not metric or not target or not target.startswith("E") or not target[1:].isdigit():
            continue
        i = int(target[1:]) - 1
        if not 0 <= i < legacy["eixos"]:
            continue
        latest[(target, metric)] = e
        if metric == "estacas_concretadas":
            piles[i] = max(piles[i], e["quantity"])
        elif metric == "pilares_concretados":
            pillars[i] = max(pillars[i], e["quantity"])

    planned = legacy["estacas"]["previstas_por_eixo"]
    assert sum(planned) == 292, "Quantitativo do modelo alterado sem documentação"
    if any(not 0 <= n <= maxn for n, maxn in zip(piles, planned)):
        raise ValueError("Quantitativo de estacas excede o modelo")
    if any(not 0 <= n <= legacy["pilares"]["previstos_por_eixo"] for n in pillars):
        raise ValueError("Quantitativo de pilares incompatível com o modelo")

    def snapshot(target, metric):
        row = latest.get((target, metric))
        if row is None:
            return None
        return {"quantity": row["quantity"], "date": row["date"], "event_id": row["id"]}

    # Elementos com identificação inequívoca. Outros eventos não podem criar mais longarinas.
    beam_1 = next((e for e in approved if e["id"] == "wa-20261110-1451-long1" and e["state"] == "executado"), None)
    beam_2_event = next((e for e in approved if e["id"] == "wa-20261117-0828-long2"), None)
    beam_2_inferred = next((i for i in inferences if i.get("id") == "inf-long2-concretagem"
                            and i.get("based_on_event") in ids
                            and i.get("exact_date") is None
                            and i.get("validation") == "homologada_por_inferencia"), None)
    ordinal = {}
    for target in ("E07", "E09"):
        matches = [e for e in approved if e["target"] == target
                   and e.get("quantity_kind") == "ordinal_em_execucao"
                   and e["state"] == "em_andamento"]
        if matches:
            e = matches[-1]
            ordinal[target] = {"position": e["quantity"], "date": e["date"], "event_id": e["id"],
                               "is_completed": False}

    other = {
        "estacas_feitas_etapa_indefinida": {axis: snapshot(axis, "estacas_feitas_etapa_indefinida")
                                           for axis in ("E07", "E09")},
        "camisas_sem_concretagem": {"E08": snapshot("E08", "camisas_sem_concretagem")},
        "perfuracao_ordinal_em_andamento": ordinal,
        "pilares_E03_em_armacao": 2 if any(e["id"] == "wa-20261117-0855-e03-armadura" for e in approved) else None,
        "formas_longarina_3_percentual": 50 if any(e["id"] == "wa-20261117-0828-long3-formas" for e in approved) else None,
        "prelajes_acrescimos_nao_conciliados": [
            {"date": e["date"], "quantity": e["quantity"], "event_id": e["id"]}
            for e in approved if e.get("service") == "prelaje"
            and e.get("quantity_kind") == "acrescimo_reportado"
        ],
    }

    # Executado em campo: afirmações do responsável são homologadas como registros reais.
    # Não colapsar "executadas/finalizadas" em "concretadas" sem indicação explícita
    # da etapa. Capacidade resistente, posição e aceite são campos independentes.
    def latest_approved_metric(target, metric):
        matches = [e for e in approved if e.get("target") == target and
                   e.get("metric") == metric and
                   e.get("state") == "snapshot" and
                   e.get("quantity_kind") == "total_reportado"]
        return matches[-1] if matches else None

    field_piles = {}
    # Um snapshot de execução é a última fotografia acumulada homologada, por eixo,
    # e não o somatório das mensagens de vários dias. Aplicável também a eixos
    # que receberem registros novos em meses posteriores.
    pile_status_metrics = {
        "estacas_executadas_etapa_a_verificar": "nao_especificada",
        "estacas_finalizadas_etapa_a_verificar": "finalizadas_sem_etapa_detalhada",
    }
    for axis_index in range(legacy["eixos"]):
        axis = f"E{axis_index + 1:02d}"
        matches = [e for e in approved if e.get("target") == axis and
                   e.get("metric") in pile_status_metrics and
                   e.get("state") == "snapshot" and
                   e.get("quantity_kind") == "total_reportado"]
        if not matches:
            continue
        row = matches[-1]
        planned_number = planned[axis_index]
        executed = row["quantity"]
        field_piles[axis] = {
            "executadas_em_campo": executed,
            "previstas_projeto": planned_number,
            "diferenca_executado_menos_previsto": executed - planned_number,
            "concretadas_na_base_anterior": piles[axis_index],
            "data": row["date"],
            "evento_origem": row["id"],
            "etapa_de_conclusao": pile_status_metrics[row["metric"]],
            "locacao_conforme_projeto": "nao_verificada",
            "participacao_na_resistencia": "nao_determinada",
            "status": "executado_em_campo_homologado",
        }
    longarinas_row = latest_approved_metric("FAB", "longarinas_concretadas_total")
    field_longarinas = ({
        "concretadas_em_campo": longarinas_row["quantity"],
        "data": longarinas_row["date"],
        "evento_origem": longarinas_row["id"],
        "identificacao_individual_de_todas": False,
        "status": "executado_em_campo_homologado",
    } if longarinas_row else None)
    partial_pillars = [e for e in approved if e["id"] == "wa-20261124-103159-e03-pilar03-04-inferior"]
    pillar_formwork = [e for e in approved if e["id"] == "wa-20261124-103159-e03-pilar03-04-formas"]
    field_pillar_status = ({
        "elementos": ["E03-P03", "E03-P04"],
        "metades_inferiores_concretadas": 2,
        "formas_superiores_montadas": len(pillar_formwork) > 0,
        "concretagem_superior_confirmada": False,
        "nao_adicionar_aos_pilares_integrais": True,
        "data": partial_pillars[-1]["date"],
    } if partial_pillars else None)

    # Projeção da evolução física: uma única referência por eixo.
    # Snapshot homologado mais recente da execução de campo prevalece sobre a base
    # histórica APENAS na leitura "execução"; a série "concretagem" fica separada.
    # E09: 25 peças executadas versus 24 de projeto, sem corte em 100% ou descarte.
    progress_axes = []
    for i, project_count in enumerate(planned):
        axis = f"E{i + 1:02d}"
        field = field_piles.get(axis)
        concrete_count = piles[i]
        observed_count = field["executadas_em_campo"] if field is not None else concrete_count
        if observed_count < concrete_count:
            raise ValueError(f"{axis}: execução homologada inferior à concretagem registrada")
        progress_axes.append({
            "eixo": axis,
            "previstas_projeto": project_count,
            "executadas_registradas": observed_count,
            "concretadas_identificadas": concrete_count,
            "origem_execucao": "campo_homologado" if field is not None else "base_historica",
            "data_execucao_campo": field["data"] if field is not None else None,
            "evento_origem": field["evento_origem"] if field is not None else None,
            "etapa_execucao": field["etapa_de_conclusao"] if field is not None else
                              "concretagem_base_historica",
            "excedente_executado": max(0, observed_count - project_count),
            "locacao_conforme_projeto": field["locacao_conforme_projeto"] if field is not None else
                                        "nao_auditada_individualmente",
            "participacao_resistente": field["participacao_na_resistencia"] if field is not None else
                                      "nao_auditada_individualmente",
        })
    additional_preslabs = sum(
        e["quantity"] for e in approved
        if e.get("service") == "prelaje"
        and e.get("quantity_kind") == "acrescimo_reportado"
        and e.get("state") == "incremento_reportado"
        and isinstance(e.get("quantity"), int)
    )
    evolution = {
        "data_referencia": max((e["date"] for e in approved), default=None),
        "estacas_por_eixo": progress_axes,
        "total_estacas_execucao_registrada": sum(row["executadas_registradas"] for row in progress_axes),
        "total_estacas_previstas_projeto": sum(row["previstas_projeto"] for row in progress_axes),
        "total_estacas_concretadas_identificadas": sum(row["concretadas_identificadas"] for row in progress_axes),
        "indicador_execucao_etapas_mistas": True,
        "total_blocos_concluidos_registrados": sum(blocks),
        "total_pilares_integralmente_concretados_registrados": sum(pillars),
        "pilares_E03_concretagem_parcial": field_pillar_status,
        "total_longarinas_concretadas_em_campo": field_longarinas["concretadas_em_campo"] if field_longarinas else None,
        "prelajes_acrescimos_reportados_novembro": additional_preslabs,
        "prelajes_estoque_total": None,
        "precaucoes": [
            "Estacas executadas em etapa não especificada não devem ser rotuladas como concretadas.",
            "Eixo 09 tem 25 estacas finalizadas em campo contra 24 previstas em projeto.",
            "A soma de execução por eixo agrega base histórica e apontamentos homologados; não é avanço contratual homogêneo.",
            "Pilares E03-P03/P04 possuem somente a parte inferior concretada, sem confirmação dos topos.",
            "Pré-lajes registradas como incrementos não permitem total de estoque sem conciliar a base anterior.",
            "Nenhum conjunto de estacas pode ser colorido como elementos individuais concluídos sem locação validada.",
        ],
    }

    state = copy.deepcopy(legacy)
    state["schema_version"] = 2
    state["classification"] = "consolidacao_parcial_para_acompanhamento"
    # A data do estado homologado deve refletir só o último evento aprovado.
    # Novos relatos não homologados são indicados separadamente.
    state["data_referencia"] = max((e["date"] for e in approved), default="nao_determinada")
    state["source_note"] = ("Indicadores de concretagem preservam a base histórica. Na leitura de execução física, "
                            "o último total de campo homologado prevalece por eixo. As etapas são distintas: "
                            "o total de execução não constitui medição nem aceite. Não há atribuição por estaca.")
    state["estacas"]["historicas_por_eixo"] = piles
    state["pilares"]["historicos_por_eixo"] = pillars
    state["blocos"]["historicos_por_eixo"] = blocks
    state["consolidacao"] = {
        "registros_totais": len(ordered),
        "registros_homologados": len(approved),
        "registros_pendentes": len(pending),
        "ultimo_relato_pendente": max((e["date"] for e in pending), default=None),
        "eventos_pendentes_ids": [e["id"] for e in pending],
        "metodo": "maximo_por_etapa_e_eixo_entre_base_historica_e_ultimo_snapshot_homologado",
        "total_estacas_concretadas_base_mais_snapshots": sum(piles),
        "total_blocos_base_historica": sum(blocks),
        "total_pilares_concretados_base_mais_snapshots": sum(pillars),
        "longarinas_concretadas_observadas": 1 if beam_1 else 0,
        "longarinas_concretadas_inferidas": 1 if beam_2_event and beam_2_inferred else 0,
        "inferencia_longarina_2_data_exata": None,
        "detalhes": other,
        "evolucao_fisica": evolution,
        "execucao_em_campo": {
            "estacas_por_eixo": field_piles,
            "longarinas": field_longarinas,
            "pilares_parciais_E03": field_pillar_status,
            "critica_de_conformidade": "Projeto e executado coexistem; divergência de quantidade não prova erro de locação ou exclusão da resistência.",
            "sem_contagem_dupla": True,
        },
        "criterios": [
            "Totais reportados nao se somam entre datas.",
            "Total de 25 estacas executadas no E09 pode superar as 24 projetadas sem alterar a previsão: locação e resistência permanecem indeterminadas.",
            "Ordinais de perfuracao nao sao estacas concretadas.",
            "A ausencia de registro nao constitui paralizacao.",
            "Inferencia de concretagem de longarina 2 nao constitui medicao ou aceite.",
            "Apontamentos locais do navegador nao entram no total centralizado.",
        ],
        "base_historica_ainda_nao_auditada_por_peca": True,
    }
    return state


if __name__ == "__main__":
    s = build_state()
    print(json.dumps(s["consolidacao"], ensure_ascii=False, indent=2))
