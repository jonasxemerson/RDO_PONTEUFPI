"""Auxiliar local para emitir schema JSON; os schemas gerados são entregáveis versionados."""
import json
from pathlib import Path
OUT=Path(__file__).resolve().parents[1]/'modelo_gerencial/v1'
OUT.mkdir(exist_ok=True,parents=True)
S=lambda **kw:kw
REF=lambda name:{'$ref':f'#/$defs/{name}'}

def obj(props,req=None,extra=False):
 return {'type':'object','properties':props,'required':req or list(props),'additionalProperties':extra}

def arr(items,minItems=None,maxItems=None):
 x={'type':'array','items':items}
 if minItems is not None:x['minItems']=minItems
 if maxItems is not None:x['maxItems']=maxItems
 return x

def text(minLength=1, pattern=None):
 d={'type':'string','minLength':minLength}
 if pattern: d['pattern']=pattern
 return d

def nullable(t):
 return {'anyOf':[t,{'type':'null'}]}

D={
 'sha256':text(pattern='^[a-f0-9]{64}$'),
 'date':{'type':'string','format':'date'},
 'id':text(pattern='^[A-Za-z0-9_.:-]+$'),
 'filesha':obj({'arquivo':text(),'sha256':REF('sha256')}),
 'origem':obj({'integracao':{'const':'projecao_nao_destrutiva'},'regra_relato':{'const':'homologado_responsavel_e_confiavel_como_registro_de_campo'},'arquivos_sha256':arr(REF('filesha'),minItems=3)}),
 'q_stat':obj({'situacao':{'enum':['nao_avaliado','em_analise','conforme','nao_conforme','nao_aplicavel']},'quantidade_aceita':nullable({'type':'integer','minimum':0}), 'documento_liberacao_id':nullable(REF('id'))}),
 'hp_stat':obj({'situacao':{'enum':['nao_configurado','aguardando_analise','liberado_por_ato','bloqueado_por_ato']},'ato_liberacao_id':nullable(REF('id'))}),
 'med_stat':obj({'situacao':{'enum':['nao_avaliada','em_conferencia','apta_por_criterio_contratual','retida_por_ato','medida']},'quantidade_apta':nullable({'type':'number','minimum':0}),'referencia_bm_id':nullable(REF('id'))}),
 'axis':obj({
  'id':text(pattern='^E0[1-9]$'),
  'estacas_previstas':{'type':'integer','minimum':1},
  'estacas_execucao_registrada':{'type':'integer','minimum':0},
  'estacas_concretagem_identificada':{'type':'integer','minimum':0},
  'execucao_etapa':text(), 'origem_execucao':{'enum':['base_historica','campo_homologado']},
  'data_ultimo_snapshot':nullable(REF('date')),
  'evento_snapshot_id':nullable(REF('id')),
  'evidencia_do_eixo_ids':arr(REF('id')),
  'excedente_execucao_sobre_projeto':{'type':'integer','minimum':0},
  'status_geom':{'const':'nao_verificado_individualmente'},
  'controle_tecnologico':REF('q_stat'), 'hold_point':REF('hp_stat'), 'medicao':REF('med_stat')
 }),
 'element':obj({
  'id':REF('id'), 'eixo_id':text(pattern='^E0[1-9]$'), 'tipo':text(),
  'identificacao':{'const':'identificado_em_relato_sem_validacao_geometrica'},
  'etapa_relato':text(), 'execucao_integral_comprovada':{'type':'boolean'},
  'evento_origem_ids':arr(REF('id'),minItems=1), 'liberacao_tecnica':{'enum':['nao_avaliada','em_analise','liberada_por_ato','bloqueada_por_ato']}
 }),
 'event_ref':obj({
  'id':REF('id'),'arquivo_origem':text(pattern='^data/observacoes-\\d{4}-\\d{2}\\.json$'),
  'data':REF('date'),'eixo_ou_frente':text(pattern='^(E0[1-9]|GERAL|FAB)$'),
  'servico':text(), 'estado_relato':text(),
  'validacao_relato':{'enum':['homologado_responsavel','validado_campo','pendente_esclarecimento','inferido','relato_nao_homologado']},
  'revisao_classificacao_pendente':{'type':'boolean'},'elementos_identificados_ids':arr(REF('id'))
 }),
 'numeric':{'type':'integer','minimum':0},
 'quant':obj({
  'estacas_previstas':REF('numeric'),'estacas_execucao_registrada':REF('numeric'),
  'estacas_concretagem_identificada':REF('numeric'),'execucao_etapas_mistas':{'type':'boolean'},
  'blocos_concluidos_registrados':REF('numeric'),'pilares_integralmente_concretados_registrados':REF('numeric'),
  'longarinas_concretadas_registradas':nullable(REF('numeric')),
  'prelajes_incrementais_novembro':REF('numeric'),'prelajes_estoque_total':nullable(REF('numeric'))
 }),
 'contract':obj({
  'linha_base_cronograma_aprovada_id':nullable(REF('id')),
  'idp_spi':nullable({'type':'number','minimum':0}),
  'valor_agregado_ev':nullable({'type':'number','minimum':0}),
  'valor_planejado_pv':nullable({'type':'number','exclusiveMinimum':0}),
  'idp_situacao':{'enum':['nao_calculavel_sem_linha_base_e_pesos','calculado_sobre_linha_base_aprovada']},
  'caminho_critico_documentado':nullable(arr(REF('id'))),
  'ritmo_semanal_meta':nullable({'type':'number','minimum':0}),
  'medicao_financeira_vigente':nullable({'type':'number','minimum':0}),
  'alerta_90pct_quantidade_contratual':{'enum':['nao_calculavel_sem_itens_contratuais_comparaveis','avaliado_por_item_contratual']}
 }),
 'alert':obj({
  'id':REF('id'),'tipo':{'const':'diferenca_quantitativa_executado_previsto'},
  'eixo_id':text(pattern='^E0[1-9]$'), 'gravidade':{'const':'requer_compatibilizacao'},
  'automatico':{'type':'boolean'},'rnc_formal':{'type':'boolean'},'referencia_evento_id':REF('id')
 }),
}

# Entidades operacionais: esquema de futuras entradas FORMAIS, nenhuma lançada na conversão inicial.
formal_base={
 'id':REF('id'),
 'data_abertura':REF('date'),
 'frente_id':text(pattern='^(E0[1-9]|GERAL|FAB|CONTRATO)$'),
 'elemento_id':nullable(REF('id')),
 'responsavel_papel':text(),
 'evidencias_documentais_ids':arr(REF('id')),
 'fonte_evento_id':nullable(REF('id')),
}

formal_defs={
 'documentos':obj({'id':REF('id'),'classe':{'enum':['projeto','especificacao','rdo','ensaio','liberacao','medicao','notificacao','outro']},'data_documento':REF('date'),'versao':text(),'acesso':{'enum':['publico','interno','restrito']},'url_ou_referencia':text(),'sha256':nullable(REF('sha256'))}),
 'planos_inspecao':obj({'id':REF('id'),'servico':text(),'etapa':text(),'referencia_projeto_id':REF('id'),'criterio_aprovacao':text(),'ensaios_exigidos':arr(text()),'autoridade_liberadora':text(),'data_aprovacao':nullable(REF('date'))}),
 'ensaios':obj(dict(formal_base,**{'tipo_ensaio':text(),'plano_inspecao_id':REF('id'),'laboratorio':text(),'data_ensaio':REF('date'),'resultado':nullable({'type':'number'}),'unidade':nullable(text()),'criterio_aprovacao_documento_id':nullable(REF('id')),'situacao':{'enum':['informado','em_validacao','aprovado_por_responsavel','reprovado_por_responsavel','inconclusivo']}})),
 'hold_points':obj(dict(formal_base,**{'etapa':text(),'plano_inspecao_id':REF('id'),'situacao':{'enum':['aguardando_analise','liberado_por_ato','bloqueado_por_ato']},'ato_formal_id':nullable(REF('id')),'data_decisao':nullable(REF('date'))})),
 'rnc':obj(dict(formal_base,**{'descricao':text(),'situacao':{'enum':['aberta','em_tratamento','em_verificacao','encerrada']},'data_limite':nullable(REF('date')),'data_encerramento':nullable(REF('date')),'ato_encerramento_id':nullable(REF('id'))})),
 'rfi':obj(dict(formal_base,**{'assunto':text(),'destinatario_papel':text(),'situacao':{'enum':['aberta','respondida','concluida']},'data_envio':REF('date'),'data_resposta':nullable(REF('date')),'documento_resposta_id':nullable(REF('id'))})),
 'medicoes':obj({'id':REF('id'),'numero_bm':text(),'data_corte':REF('date'),'item_contratual_id':REF('id'),'marco_contratual_id':nullable(REF('id')),'referencia_documental_id':REF('id'),'quantidade_medida':nullable({'type':'number','minimum':0}),'unidade':nullable(text()),'valor_medido':{'type':'number','minimum':0},'situacao':{'enum':['em_conferencia','atestada','liquidada','paga','glosada']}}),
 'decisoes':obj(dict(formal_base,**{'tipo':{'enum':['encaminhamento','recomendacao','notificacao','liberacao','indeferimento','outro']},'descricao':text(),'ato_decisorio_id':nullable(REF('id')),'data_limite':nullable(REF('date')),'situacao':{'enum':['aberta','em_acompanhamento','encerrada']}})),
 'producao_diaria':obj({'id':REF('id'),'data':REF('date'),'frente_id':text(pattern='^(E0[1-9]|FAB|GERAL)$'),'servico':text(),'etapa':text(),'quantidade':{'type':'number','minimum':0},'unidade':text(),'tipo_quantidade':{'enum':['incremento_validado','snapshot_acumulado','ordinal_em_execucao']},'evento_origem_id':REF('id')}),
 'recursos_diarios':obj({'id':REF('id'),'data':REF('date'),'frente_id':text(pattern='^(E0[1-9]|FAB|GERAL)$'),'recurso_tipo':text(),'quantidade_observada':{'type':'integer','minimum':0},'turno':nullable(text()),'evento_origem_id':REF('id')}),
}
D.update(formal_defs)
control_fields={k:arr(REF(k)) for k in formal_defs}
D['formal_controls']=obj(control_fields)
D['regras']=obj({
 'idp_nao_calculado_sem_cronograma':{'const':True},
 'camisas_e_ordinais_nao_sao_concretagens':{'const':True},
 'snapshots_nao_sao_incrementos':{'const':True},
 'ausencia_de_registro_nao_e_paralisacao':{'const':True},
 'relato_homologado_nao_e_aceite':{'const':True},
 'hold_point_nao_bloqueado_sem_ato':{'const':True},
 'nao_criar_rnc_rfi_medicoes_automaticamente':{'const':True},
})
D['diagnostic']={'type':'object','properties':{
 'registros_totais':REF('numeric'),
 'registros_homologados_campo':REF('numeric'),
 'registros_pendentes_esclarecimento':REF('numeric'),
 'registros_homologados_a_reclassificar':REF('numeric'),
 'achados_auditoria_nao_sao_rnc':arr({'type':'object'}),
 'documentos_requeridos_a_confirmar':arr({'type':'object'}),
 'financeiro_referencia_historica':{'type':'object'},
 },'required':['registros_totais','registros_homologados_campo','registros_pendentes_esclarecimento','registros_homologados_a_reclassificar'], 'additionalProperties':False}
S=obj({
 'versao_schema':{'const':'1.0.0'},
 'id_empreendimento':{'const':'ponte-ufpi'},
 'escopo':{'enum':['interno','publico']},
 'data_referencia':REF('date'),
 'origem':REF('origem'),
 'base_quantitativa':REF('quant'),
 'eixos':arr(REF('axis'),minItems=9,maxItems=9),
 'elementos_individualizados':arr(REF('element')),
 'referencias_eventos':arr(REF('event_ref')),
 'gestao_contratual':REF('contract'),
 'controles_formais':REF('formal_controls'),
 'alertas_derivados':arr(REF('alert')),
 'regras':REF('regras'),
 'diagnostico':REF('diagnostic')
},req=['versao_schema','id_empreendimento','escopo','data_referencia','origem','base_quantitativa','eixos','elementos_individualizados','referencias_eventos','gestao_contratual','controles_formais','alertas_derivados','regras'])
S.update({'$schema':'https://json-schema.org/draft/2020-12/schema', '$id':'https://github.com/jonasxemerson/RDO_PONTEUFPI/modelo_gerencial/v1/schema_snapshot.json','$defs':D})
p=OUT/'schema_snapshot.json'
p.write_text(json.dumps(S,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('generated',p,p.stat().st_size)