#!/usr/bin/env python3
"""Conecta RDO privado ao modelo gerencial v1 SEM publicar fotos ou alterar saldos.
Uso: python scripts/conectar_rdo_gerencial.py --snapshot ... --schema ... --input-dir ... --output ...
"""
from __future__ import annotations
import argparse,datetime as dt,hashlib,json
from pathlib import Path
from jsonschema import Draft202012Validator,FormatChecker

def load(p):return json.loads(Path(p).read_text(encoding="utf-8"))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def validated(rdo,schema,path):
    errors=list(Draft202012Validator(schema,format_checker=FormatChecker()).iter_errors(rdo))
    if errors:raise ValueError(f"{path}: "+ "; ".join(e.message for e in errors[:5]))
    if not rdo["id"].startswith("rdo-"+rdo["header"]["date"]+"-"):
        raise ValueError(f"{path}: data e ID não coincidem")
    ids=set()
    for x in rdo["records"]:
        if x["id"] in ids:raise ValueError("ID de evento duplicado: "+x["id"])
        ids.add(x["id"])
        if x["original_source_ref"]!=rdo["id"] or x["date"]!=rdo["header"]["date"]:
            raise ValueError("Vínculo de origem/data inválido: "+x["id"])
        if (x["quantity"] is None)!=(x["quantity_kind"]=="nao_informado"):
            raise ValueError("Quantidade/natureza inconsistentes: "+x["id"])
        if (x["state"]=="snapshot")!=(x["quantity_kind"]=="total_reportado"):
            raise ValueError("Snapshot acumulado sem natureza adequada: "+x["id"])
        if x["quantity_kind"]=="ordinal_em_execucao" and x["state"]=="executado":
            raise ValueError("Ordinal não comprova conclusão: "+x["id"])
    for p in rdo["photos"]:
        if p["record_ref"] is not None and p["record_ref"] not in ids:
            raise ValueError("Fotografia ligada a evento inexistente: "+p["path"])

def connect(snapshot,schema,paths,scope="interno"):
    if snapshot.get("versao_schema")!="1.0.0" or snapshot.get("id_empreendimento")!="ponte-ufpi":
        raise ValueError("Snapshot gerencial incompatível")
    if scope not in ("interno","publicavel_candidato"):raise ValueError("Escopo inválido")
    axes={r["id"] for r in snapshot["eixos"]}
    elements={r["id"] for r in snapshot.get("elementos_individualizados",[])}
    original={r["id"] for r in snapshot.get("referencias_eventos",[])}
    seen=set();rdos=[];records=[];alerts=[];photos=0
    for path in paths:
        rdo=load(path);validated(rdo,schema,path)
        if rdo["id"] in seen:raise ValueError("RDO duplicado: "+rdo["id"])
        seen.add(rdo["id"])
        photos+=len(rdo["photos"])
        rdos.append({"id":rdo["id"],"data":rdo["header"]["date"],
                     "sha256":sha(path),"frentes":len(rdo["records"]),
                     "fotos_privadas":len(rdo["photos"])})
        for x in rdo["records"]:
            if x["id"] in seen or x["id"] in original:
                raise ValueError("Evento duplicado contra modelo: "+x["id"])
            seen.add(x["id"])
            row={"id":x["id"],"rdo_origem":rdo["id"],"data":x["date"],
                 "eixo":x["target"] if x["target"] in axes else None,
                 "frente":x["target"],"servico":x["service"],"etapa":x["phase"],
                 "status_relato":x["state"],"quantidade_relato":x["quantity"],
                 "natureza_quantidade":x["quantity_kind"],
                 "codigo_individual_informado":x["element"],
                 "elemento_modelo_id":x["element"] if x["element"] in elements else None,
                 "classificacao":"proposto_revisao","controle_tecnologico":"nao_avaliado",
                 "hold_point":"nao_configurado","medicao":"nao_avaliada",
                 "nao_agregar_saldos":True,
                 "qtd_fotos":sum(p["record_ref"]==x["id"] for p in rdo["photos"])}
            if scope=="interno":
                row.update({"atividade":x["activity"],"observacoes":x["notes"],
                            "equipe":x["workers"],"equipamentos":x["equipment"],
                            "anexos_privados":[p["path"] for p in rdo["photos"]
                                               if p["record_ref"]==x["id"]]})
            records.append(row)
            if x["quantity_kind"]=="total_reportado":
                alerts.append({"id":x["id"],"tipo":"snapshot_nao_somatorio"})
            if x["element"] and x["element"] not in elements:
                alerts.append({"id":x["id"],"tipo":"identificacao_a_conciliar"})
    return {"schema_version":"rdo-gerencial-overlay/1.0.0","project":"ponte-ufpi",
            "scope":scope,"status":"proposta_nao_homologada",
            "model_version":"1.0.0","model_date":snapshot["data_referencia"],
            "rdos":rdos,"registros_propostos":records,"alertas_analiticos_nao_formais":alerts,
            "fotos_privadas_quantidade":photos,
            "base_fisica_original_imutavel":snapshot["base_quantitativa"],
            "apto_para_publicacao":False,"pode_alterar_quantitativos":False,
            "regras":["sem soma de snapshots","sem aceite/medição implícitos",
                      "sem fotos privadas no painel público",
                      "homologação humana separada"]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--snapshot",required=True);p.add_argument("--schema",required=True)
    p.add_argument("--input-dir",required=True);p.add_argument("--output",required=True)
    p.add_argument("--scope",choices=["interno","publicavel_candidato"],default="interno")
    a=p.parse_args()
    root=Path(a.input_dir)
    files=sorted(root.rglob("*.json"))
    result=connect(load(a.snapshot),load(a.schema),files,a.scope)
    result["source_snapshot_sha256"]=sha(a.snapshot)
    target=Path(a.output);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Conectados {len(result['rdos'])} RDO(s) e {len(result['registros_propostos'])} proposta(s). Quantitativos inalterados.")
if __name__=="__main__":main()
