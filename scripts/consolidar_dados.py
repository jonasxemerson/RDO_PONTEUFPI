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

    state = copy.deepcopy(legacy)
    state["schema_version"] = 2
    state["classification"] = "consolidacao_parcial_para_acompanhamento"
    state["data_referencia"] = max((e["date"] for e in ordered), default="nao_determinada")
    state["source_note"] = ("Base histórica preservada; homologação dos apontamentos pelo responsável "
                            "não equivale a aceite ou medição. E08 foi revalidado sem nova soma; E03 atualizado por snapshot.")
    state["estacas"]["historicas_por_eixo"] = piles
    state["pilares"]["historicos_por_eixo"] = pillars
    state["blocos"]["historicos_por_eixo"] = blocks
    state["consolidacao"] = {
        "registros_totais": len(ordered),
        "registros_homologados": len(approved),
        "registros_pendentes": len(pending),
        "eventos_pendentes_ids": [e["id"] for e in pending],
        "metodo": "maximo_por_etapa_e_eixo_entre_base_historica_e_ultimo_snapshot_homologado",
        "total_estacas_concretadas_base_mais_snapshots": sum(piles),
        "total_blocos_base_historica": sum(blocks),
        "total_pilares_concretados_base_mais_snapshots": sum(pillars),
        "longarinas_concretadas_observadas": 1 if beam_1 else 0,
        "longarinas_concretadas_inferidas": 1 if beam_2_event and beam_2_inferred else 0,
        "inferencia_longarina_2_data_exata": None,
        "detalhes": other,
        "criterios": [
            "Totais reportados nao se somam entre datas.",
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
