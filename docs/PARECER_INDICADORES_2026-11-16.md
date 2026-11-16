# Parecer de conferência — indicadores Ponte UFPI
**Data de referência:** 16/11/2026
**Situação:** NÃO HOMOLOGADO para apresentação como execução oficial
**Escopo:** conferência automatizada de consistência, sem vistoria, laudo, boletim de medição ou RDO assinado.

| Indicador | Quantidade | Enquadramento | Pendência para homologação |
| --- | --- | --- | --- |
| Estacas previstas | 292 | Referência geométrica do V5 | Conferir quantitativos com as pranchas aprovadas |
| Estacas concretadas | 111/292 | Base histórica legada; soma interna verificada | Conciliar por eixo/estaca com registros de concretagem e documentos de fiscalização |
| Blocos | 2/9 | Base histórica legada | Identificar blocos, datas e evidências |
| Pilares concretados | 4/36 | Base histórica legada | Verificar por pilar e data |
| E07 — estacas relatadas | 13 | Snapshot reportado, etapa não especificada | Determinar se foram perfuradas, armadas ou concretadas |
| E09 — estacas relatadas | 15 | Snapshot reportado, etapa não especificada | Determinar etapa; substitui snapshot anterior de 14, sem incremento automático |
| Longarinas | relatos de concretagem, desforma e montagem | Observações não homologadas; não constituem totais de longarinas concretadas | Identificação das peças, evidências e avaliação técnica |
| Avanço global da obra | — | NÃO CALCULADO | Cronograma-base aprovado, pesos físico-financeiros e aferição dos itens |

## Critérios de homologação

1. Confirmar fonte primária identificável (RDO, ficha de concretagem, levantamento, medição, ensaio ou vistoria validada), peça/eixo e data da constatação.
2. Verificar cumulativos: snapshots **substituem** os anteriores; não são somados entre si; eventos repetidos são conciliados por elemento e etapa.
3. Tratar falta de observação como **sem informação**, não como paralisação.
4. Pré-requisito inferido a partir de etapa posterior pode ser registrado como `concluido_por_inferencia`, sem data inventada; não é aceite de serviço.
5. Classificar cada evento validado como `validado_campo` apenas após revisão técnica; marcar `review=false` somente quando pendências forem resolvidas.
6. Publicar lote apenas quando `approval_state=homologado`, com responsável, data da homologação e referência da evidência em registro interno apropriado.
7. Registrar decisão em Pull Request, com revisão de outra conta com permissão, quando habilitada.

**Atenção:** este documento não é termo de aceite, não homologa os quantitativos legados e não substitui medição contratual.
