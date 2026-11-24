#!/usr/bin/env python3
"""Validação de schema, reconciliação com fonte e invariantes gerenciais.

Requer jsonschema: python -m pip install jsonschema
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    raise SystemExit('Dependência faltante: instale jsonschema para validação formal')

from gerar_modelo_gerencial import APPROVED, EXCLUDE_PUBLIC_SERVICES, source, digest

HERE = Path(__file__).resolve().parents[1]
SCHEMA = HERE/'modelo_gerencial/v1/schema_snapshot.json'
FORMAL_KEYS = ["documentos", "planos_inspecao", "ensaios", "hold_points", "rnc", "rfi", "medicoes", "decisoes", "producao_diaria", "recursos_diarios"]


def require(condition, message):
    if not condition: raise ValueError(message)


def validate(data:dict,root:Path,schema_path:Path=SCHEMA)->dict:
    root=Path(root).resolve()
    schema=json.loads(schema_path.read_text(encoding='utf-8'))
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema,format_checker=jsonschema.FormatChecker()).validate(data)
    cfg, manifest, historical, files, source_events = source(root)
    full_source={e['id']:e for f,e in source_events}
    require(len(full_source)==len(source_events),'ID duplicado na fonte')
    require(data['data_referencia']==cfg['data_referencia'],'Data referência divergente')
    provenance=data['origem']['arquivos_sha256']
    require(set(e['arquivo'] for e in provenance)==set(files),'Manifesto de proveniência incompleto')
    for ref in provenance:
        require(digest(root/ref['arquivo'])==ref['sha256'],'SHA-256 de origem alterado: '+ref['arquivo'])
    scope=data['escopo']
    expected=[e for f,e in source_events if scope=='interno' or (e['validation'] in APPROVED and e['service'] not in EXCLUDE_PUBLIC_SERVICES)]
    ref_index={r['id']:r for r in data['referencias_eventos']}
    require(len(ref_index)==len(data['referencias_eventos']),'Referências duplicadas')
    require(set(ref_index)=={e['id'] for e in expected},'Referências de eventos não correspondem ao escopo')
    for evt in expected:
        ref=ref_index[evt['id']]
        require(ref['validacao_relato']==evt['validation'],'Mudança indevida de homologação '+evt['id'])
        require(ref['estado_relato']==evt['state'],'Mudança indevida do estado '+evt['id'])
        require(ref['revisao_classificacao_pendente']==evt['review'],'Mudança indevida review '+evt['id'])
        require(ref['data']==evt['date'] and ref['servico']==evt['service'],'Metadados divergentes '+evt['id'])
    require(scope!='publico' or 'diagnostico' not in data,'Diagnóstico privado na projeção pública')
    q=data['base_quantitativa']; e=cfg['consolidacao']['evolucao_fisica']
    for a,b in {
       'estacas_previstas':'total_estacas_previstas_projeto',
       'estacas_execucao_registrada':'total_estacas_execucao_registrada',
       'estacas_concretagem_identificada':'total_estacas_concretadas_identificadas',
       'blocos_concluidos_registrados':'total_blocos_concluidos_registrados',
       'pilares_integralmente_concretados_registrados':'total_pilares_integralmente_concretados_registrados',
       'longarinas_concretadas_registradas':'total_longarinas_concretadas_em_campo',
       'prelajes_incrementais_novembro':'prelajes_acrescimos_reportados_novembro',
    }.items():
        require(q[a]==e[b],'Indicador não reconciliado: '+a)
    require(q['prelajes_estoque_total'] is None,'Estoque de pré-lajes não comprovado')
    axes=data['eixos'];axes_ids=[a['id'] for a in axes]
    require(axes_ids==[f'E{i:02d}' for i in range(1,10)],'Sequência de eixos incorreta')
    require(sum(a['estacas_previstas'] for a in axes)==q['estacas_previstas'],'Estacas previstas: soma incorreta')
    require(sum(a['estacas_execucao_registrada'] for a in axes)==q['estacas_execucao_registrada'],'Execução: soma incorreta')
    require(sum(a['estacas_concretagem_identificada'] for a in axes)==q['estacas_concretagem_identificada'],'Concretagem: soma incorreta')
    rawaxes={row['eixo']:row for row in e['estacas_por_eixo']}
    for a in axes:
        raw=rawaxes[a['id']]
        for x,y in [('estacas_previstas','previstas_projeto'),('estacas_execucao_registrada','executadas_registradas'),('estacas_concretagem_identificada','concretadas_identificadas')]:
            require(a[x]==raw[y],a['id']+': quantitativo não corresponde à fonte ('+x+')')
        require(a['estacas_concretagem_identificada']<=a['estacas_execucao_registrada'],a['id']+': concretagem > execução')
        require(a['excedente_execucao_sobre_projeto']==max(0,a['estacas_execucao_registrada']-a['estacas_previstas']),a['id']+': excedente incorreto')
        require(a['evento_snapshot_id'] is None or a['evento_snapshot_id'] in ref_index,a['id']+': snapshot sem referência')
        require(all(x in ref_index for x in a['evidencia_do_eixo_ids']),a['id']+': ID de evento não encontrado')
        # As dimensões técnica/financeira só podem ser atribuídas por atos/documentos próprios.
        qc=a['controle_tecnologico'];hp=a['hold_point'];med=a['medicao']
        if qc['situacao'] in ('conforme','nao_conforme'):
            require(qc['documento_liberacao_id'] is not None,a['id']+': conclusão técnica sem ato documentado')
        if qc['quantidade_aceita'] is not None:
            require(qc['situacao']=='conforme' and qc['documento_liberacao_id'],a['id']+': quantidade aceita sem parecer')
        if hp['situacao'] in ('liberado_por_ato','bloqueado_por_ato'):
            require(hp['ato_liberacao_id'] is not None,a['id']+': hold point sem ato')
        if med['situacao'] in ('apta_por_criterio_contratual','medida','retida_por_ato'):
            require(med['referencia_bm_id'] is not None,a['id']+': medição/retensão sem referência contratual')
        if med['quantidade_apta'] is not None:
            require(med['situacao']=='apta_por_criterio_contratual',a['id']+': aptidão não comprovada')
    require(sum(a['excedente_execucao_sobre_projeto'] for a in axes)==1,'Excedentes: não corresponde a único caso E09')
    e09=axes[8]
    require((e09['estacas_previstas'],e09['estacas_execucao_registrada'],e09['estacas_concretagem_identificada'])==(24,25,8),'E09 não preservado')
    check_elements={el['id']:el for el in data['elementos_individualizados']}
    require(set(check_elements)=={'E03-P03','E03-P04'},'Individualização de peça sem fonte explícita')
    for el in check_elements.values():
        require(el['execucao_integral_comprovada'] is False,'Pilar parcial contado como integral')
        require(all(ref in ref_index for ref in el['evento_origem_ids']),'Elemento sem IDs de origem')
    contract=data['gestao_contratual']
    docs={d['id']:d for d in data['controles_formais']['documentos']}
    plans={p['id']:p for p in data['controles_formais']['planos_inspecao']}
    measurements={m['id']:m for m in data['controles_formais']['medicoes']}
    all_records=[r for kind in FORMAL_KEYS for r in data['controles_formais'][kind]]
    require(len({r['id'] for r in all_records})==len(all_records),'IDs de atos/documentos repetidos')
    for a in axes:
        for key in (a['controle_tecnologico']['documento_liberacao_id'], a['hold_point']['ato_liberacao_id']):
            if key is not None: require(key in docs,a['id']+': documento de validação não cadastrado')
        bm=a['medicao']['referencia_bm_id']
        if bm is not None:require(bm in measurements,a['id']+': BM não cadastrada')
    for e in data['controles_formais']['ensaios']:
        require(e['plano_inspecao_id'] in plans,'Ensaio sem plano aprovado: '+e['id'])
        require(all(x in docs for x in e['evidencias_documentais_ids']),'Ensaio sem documento cadastrado')
    for h in data['controles_formais']['hold_points']:
        require(h['plano_inspecao_id'] in plans,'Hold point sem plano de inspeção: '+h['id'])
        if h['situacao'] in ('liberado_por_ato','bloqueado_por_ato'):
            require(h['ato_formal_id'] in docs,'Hold point sem ato de liberação/bloqueio: '+h['id'])
    for r in data['controles_formais']['rnc']:
        if r['situacao']=='encerrada':require(r['ato_encerramento_id'] in docs,'RNC encerrada sem ato: '+r['id'])
    for r in data['controles_formais']['rfi']:
        if r['situacao'] in ('respondida','concluida'):
            require(r['documento_resposta_id'] in docs and r['data_resposta'] is not None,'RFI respondida sem resposta documental: '+r['id'])
    if contract['idp_spi'] is not None:
        require(contract['linha_base_cronograma_aprovada_id'] in docs,'SPI sem linha de base aprovada')
        require(contract['valor_agregado_ev'] is not None and contract['valor_planejado_pv'] is not None,'SPI sem EV e PV')
        require(abs(contract['idp_spi']-contract['valor_agregado_ev']/contract['valor_planejado_pv'])<0.0001,'SPI divergente de EV/PV')
        require(contract['idp_situacao']=='calculado_sobre_linha_base_aprovada','SPI sem marcador de base aprovada')
    else:
        require(contract['idp_situacao']=='nao_calculavel_sem_linha_base_e_pesos','SPI ausente com estado inconsistente')
        require(contract['valor_agregado_ev'] is None and contract['valor_planejado_pv'] is None,'EV/PV preenchidos sem SPI')
    alerts=data['alertas_derivados']
    require(len(alerts)==1 and alerts[0]['eixo_id']=='E09' and alerts[0]['rnc_formal'] is False,'Alerta E09 não deve virar RNC automática')
    require(alerts[0]['referencia_evento_id'] in ref_index,'Alerta sem evento de origem')
    if scope=='interno':
       diag=data['diagnostico']
       require(diag['registros_totais']==len(source_events),'Diagnóstico de eventos divergente')
       require(diag['registros_homologados_campo']==sum(e.get('validation') in APPROVED for _,e in source_events),'Aprovações divergentes')
       require(diag['registros_pendentes_esclarecimento']==sum(e.get('validation') not in APPROVED for _,e in source_events),'Pendências divergentes')
       require(diag['registros_homologados_a_reclassificar']==sum(e.get('validation') in APPROVED and e.get('review') for _,e in source_events),'Flag review alterada')
    return {'valido':True,'escopo':scope,'eixos':len(axes),'eventos':len(ref_index),'estacas_previstas':q['estacas_previstas'],'estacas_execucao_registrada':q['estacas_execucao_registrada'],'concretagens_identificadas':q['estacas_concretagem_identificada'],'hold_points_formais':len(data['controles_formais']['hold_points']),'rnc_formais':len(data['controles_formais']['rnc']),'idp_spi':contract['idp_spi']}


def main():
    cli=argparse.ArgumentParser()
    cli.add_argument('--root',type=Path,required=True)
    cli.add_argument('--snapshot',type=Path,required=True)
    args=cli.parse_args()
    print(json.dumps(validate(json.loads(args.snapshot.read_text(encoding='utf-8')),args.root),ensure_ascii=False,indent=2))

if __name__=='__main__':main()