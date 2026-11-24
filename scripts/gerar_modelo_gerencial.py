#!/usr/bin/env python3
"""Projeção não destrutiva da base física da Ponte da UFPI para gestão contratual.

Confiança no relato homologado não implica inspeção aprovada ou medição elegível.
Não sobrescreve dados originais nem arquivos da publicação institucional.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

APPROVED = {"homologado_responsavel", "validado_campo"}
EXCLUDE_PUBLIC_SERVICES = {"seguranca", "qualidade", "equipamento", "ambiental"}
SCHEMA_VERSION = "1.0.0"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source(root: Path):
    sys.path.insert(0, str(root / "scripts"))
    from consolidar_dados import build_state
    cfg = build_state(root)
    manifest = load_json(root / "data/manifest.json")
    histories = load_json(root / "data/indicadores-historicos.json")
    files = ["data/manifest.json", "data/indicadores-historicos.json"] + manifest["files"]
    events = []
    for relative in manifest["files"]:
        doc = load_json(root / relative)
        events.extend((relative, e) for e in doc["events"])
    return cfg, manifest, histories, files, events


def get_snapshot(root: Path, scope: str, audit_path: Path | None = None) -> dict:
    root = Path(root).resolve()
    cfg, manifest, history, files, source_events = source(root)
    evo = cfg["consolidacao"]["evolucao_fisica"]
    source_index = {e["id"]: e for _, e in source_events}
    if len(source_index) != len(source_events):
        raise ValueError("IDs de eventos duplicados nas fontes")
    public = scope == "publico"
    chosen = [(f, e) for f, e in source_events if not public or
              (e.get("validation") in APPROVED and e.get("service") not in EXCLUDE_PUBLIC_SERVICES)]

    axes = []
    for p in evo["estacas_por_eixo"]:
        ref = p["evento_origem"]
        known = [e["id"] for f, e in chosen if e.get("target") == p["eixo"]]
        axes.append({
            "id": p["eixo"],
            "estacas_previstas": p["previstas_projeto"],
            "estacas_execucao_registrada": p["executadas_registradas"],
            "estacas_concretagem_identificada": p["concretadas_identificadas"],
            "execucao_etapa": p["etapa_execucao"],
            "origem_execucao": p["origem_execucao"],
            "data_ultimo_snapshot": p["data_execucao_campo"],
            "evento_snapshot_id": ref if ref in {e["id"] for _,e in chosen} else None,
            "evidencia_do_eixo_ids": known,
            "excedente_execucao_sobre_projeto": p["excedente_executado"],
            "status_geom": "nao_verificado_individualmente",
            "controle_tecnologico": {"situacao": "nao_avaliado", "quantidade_aceita": None, "documento_liberacao_id": None},
            "hold_point": {"situacao": "nao_configurado", "ato_liberacao_id": None},
            "medicao": {"situacao": "nao_avaliada", "quantidade_apta": None, "referencia_bm_id": None}
        })

    event_refs=[]
    for source_path,e in chosen:
        element_id = e.get("element")
        linked = []
        if e.get("target") == "E03" and element_id == "Pilares 03 e 04":
            linked = ["E03-P03", "E03-P04"]
        event_refs.append({
            "id": e["id"],
            "arquivo_origem": source_path,
            "data": e["date"],
            "eixo_ou_frente": e["target"],
            "servico": e["service"],
            "estado_relato": e["state"],
            "validacao_relato": e["validation"],
            "revisao_classificacao_pendente": bool(e["review"]),
            "elementos_identificados_ids": linked,
        })

    # Só peças inequivocamente identificadas na base são individualizadas.
    e03lower = "wa-20261124-103159-e03-pilar03-04-inferior"
    e03forms = "wa-20261124-103159-e03-pilar03-04-formas"
    known_elements = []
    for n in (3, 4):
        eid = f"E03-P{n:02d}"
        if e03lower in source_index and e03forms in source_index:
            known_elements.append({
                "id": eid,
                "eixo_id": "E03",
                "tipo": "pilar",
                "identificacao": "identificado_em_relato_sem_validacao_geometrica",
                "etapa_relato": "metade_inferior_concretada_forma_superior_montada",
                "execucao_integral_comprovada": False,
                "evento_origem_ids": [e03lower, e03forms],
                "liberacao_tecnica": "nao_avaliada"
            })

    base={
        "versao_schema": SCHEMA_VERSION,
        "id_empreendimento": "ponte-ufpi",
        "escopo": scope,
        "data_referencia": cfg["data_referencia"],
        "origem": {
            "integracao": "projecao_nao_destrutiva",
            "regra_relato": "homologado_responsavel_e_confiavel_como_registro_de_campo",
            "arquivos_sha256": [{"arquivo": rel, "sha256": digest(root/rel)} for rel in files],
        },
        "base_quantitativa": {
            "estacas_previstas": evo["total_estacas_previstas_projeto"],
            "estacas_execucao_registrada": evo["total_estacas_execucao_registrada"],
            "estacas_concretagem_identificada": evo["total_estacas_concretadas_identificadas"],
            "execucao_etapas_mistas": bool(evo["indicador_execucao_etapas_mistas"]),
            "blocos_concluidos_registrados": evo["total_blocos_concluidos_registrados"],
            "pilares_integralmente_concretados_registrados": evo["total_pilares_integralmente_concretados_registrados"],
            "longarinas_concretadas_registradas": evo["total_longarinas_concretadas_em_campo"],
            "prelajes_incrementais_novembro": evo["prelajes_acrescimos_reportados_novembro"],
            "prelajes_estoque_total": evo["prelajes_estoque_total"],
        },
        "eixos": axes,
        "elementos_individualizados": known_elements,
        "referencias_eventos": event_refs,
        "gestao_contratual": {
            "linha_base_cronograma_aprovada_id": None,
            "idp_spi": None,
            "valor_agregado_ev": None,
            "valor_planejado_pv": None,
            "idp_situacao": "nao_calculavel_sem_linha_base_e_pesos",
            "caminho_critico_documentado": None,
            "ritmo_semanal_meta": None,
            "medicao_financeira_vigente": None,
            "alerta_90pct_quantidade_contratual": "nao_calculavel_sem_itens_contratuais_comparaveis"
        },
        "controles_formais": {
            "documentos": [],
            "planos_inspecao": [],
            "ensaios": [],
            "hold_points": [],
            "rnc": [],
            "rfi": [],
            "medicoes": [],
            "decisoes": [],
            "producao_diaria": [],
            "recursos_diarios": [],
        },
        "alertas_derivados": [
            {"id": "ALERTA-QUANT-E09", "tipo": "diferenca_quantitativa_executado_previsto",
             "eixo_id": "E09", "gravidade": "requer_compatibilizacao",
             "automatico": True, "rnc_formal": False,
             "referencia_evento_id": "wa-20261124-101003-e09-finalizadas-25"}
        ] if any(a["id"]=="E09" and a["excedente_execucao_sobre_projeto"]>0 for a in axes) else [],
        "regras": {
            "idp_nao_calculado_sem_cronograma": True,
            "camisas_e_ordinais_nao_sao_concretagens": True,
            "snapshots_nao_sao_incrementos": True,
            "ausencia_de_registro_nao_e_paralisacao": True,
            "relato_homologado_nao_e_aceite": True,
            "hold_point_nao_bloqueado_sem_ato": True,
            "nao_criar_rnc_rfi_medicoes_automaticamente": True,
        }
    }
    if not public:
        base["diagnostico"]={
            "registros_totais": len(source_events),
            "registros_homologados_campo": sum(e.get("validation") in APPROVED for _,e in source_events),
            "registros_pendentes_esclarecimento": sum(e.get("validation") not in APPROVED for _,e in source_events),
            "registros_homologados_a_reclassificar": sum(e.get("validation") in APPROVED and bool(e.get("review")) for _,e in source_events)
        }
        if audit_path is not None:
            audit = load_json(audit_path)
            if audit.get("totais", {}).get("execucao_registrada") != evo["total_estacas_execucao_registrada"]:
                raise ValueError("Auditoria com total de execução divergente da base")
            base["diagnostico"]["achados_auditoria_nao_sao_rnc"]=[
                {"id": x[0], "prioridade": x[1], "assunto": x[2], "frente": x[3],
                 "encaminhamento": x[5], "referencia_original": x[7],
                 "situacao": "recomendacao_a_tratar"}
                for x in audit["achados"]
            ]
            base["diagnostico"]["documentos_requeridos_a_confirmar"]=[
                {"id": d[0], "descricao": d[1], "situacao_na_auditoria": d[2],
                 "responsavel_proposto": d[4], "prioridade": d[5]}
                for d in audit["documentos"]
            ]
            base["diagnostico"]["financeiro_referencia_historica"]={
                "situacao": "base_de_relatorio_outubro_nao_conciliada_nem_atualizada",
                "valor_contrato_relatado": audit["financeiro"]["contrato"],
                "base_bm_relatada": audit["financeiro"]["base_bm"],
                "diferenca_bm_contrato": round(audit["financeiro"]["diferenca_bm_contrato"],2),
                "primeira_medicao_relatada": audit["financeiro"]["primeira_medicao"],
                "nota": "Não representa pagamento confirmado ou última medição."
            }
    return base


def write_snapshot(root:Path, output:Path, scope:str, audit:Path|None=None):
    data=get_snapshot(root,scope,audit)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return data


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",type=Path,required=True,help="Raiz da cópia do repositório RDO_PONTEUFPI")
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--scope",choices=["interno","publico"],required=True)
    parser.add_argument("--audit",type=Path,help="Auditoria privada anterior (somente --scope interno)")
    args=parser.parse_args()
    if args.scope=="publico" and args.audit:
        parser.error("É proibido embutir auditoria de acesso interno na projeção pública")
    data=write_snapshot(args.root,args.output,args.scope,args.audit)
    print(json.dumps({"saida":str(args.output),"escopo":args.scope,
                      "referencias_eventos":len(data["referencias_eventos"]),
                      "eixos":len(data["eixos"]),"spi":data["gestao_contratual"]["idp_spi"]},ensure_ascii=False))

if __name__=="__main__":main()