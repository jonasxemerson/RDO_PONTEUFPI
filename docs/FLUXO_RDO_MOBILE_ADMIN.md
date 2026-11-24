# CERTARE — RDO móvel autenticado e integração gerencial v1

## Objetivo e situação

Interface móvel para registrar RDO, fotografar frentes, vincular serviços por eixo e encaminhar o conjunto para revisão em repositório **privado**. Esta entrega é uma **prévia de desenvolvimento**, isolada da publicação da ponte.

**Repositórios:** `jonasxemerson/RDO_PONTEUFPI` (público: painel/versões aprovadas) e `jonasxemerson/RDO_CERTARE` (privado: RDO e fotos brutas). Nenhuma imagem ou documento original é copiado ao repositório público.

## Autenticação e limites reais

O HTML estático não consegue autenticar visitantes sozinho. Para funcionar sem servidor próprio, o MVP exige **token GitHub fine-grained**, limitado ao repositório privado `RDO_CERTARE` e com permissões `Contents: Read and write` e `Pull requests: Read and write`. O navegador consulta `/user` e `/repos/jonasxemerson/RDO_CERTARE` e só desbloqueia o formulário quando o GitHub confirma `login=jonasxemerson` e `permissions.admin=true`. Todas as escritas são autorizadas novamente no servidor GitHub, jamais pelo simples estado visual da aba.

O token é mantido apenas em uma variável JS na memória, não é salvo em HTML, localStorage, IndexedDB, arquivo, URL ou commit. Ao recarregar, precisa informar o token novamente. O aplicativo não usa bibliotecas/CDN externas. **O código da interface não é secreto**: se futuramente hospedado publicamente, qualquer visitante poderá baixar o código, mas não poderá acessar/escrever dados privados sem a autorização real do GitHub. Para autenticação com botão de login GitHub (sem PAT manual), será necessária integração OAuth com sessão de servidor ou um GitHub App autorizado.

**Não usar token clássico de alcance global.** Usar dispositivo pessoal com bloqueio de tela. Ao finalizar, clicar em Sair e apagar rascunhos armazenados localmente quando necessário. Fotos podem conter dados pessoais; o repositório privado é obrigatório.

## Cadastro pelo celular

1. Abrir `admin-rdo/index.html` em HTTPS (em hospedagem futura) ou prévia offline pelo navegador do celular.
2. Informar token restrito e conectar; a API confirma identidade/permissão.
3. Na aba **RDO**, informar data, turno, clima observado, efetivo, equipamentos e condições gerais.
4. Em **Frentes**, adicionar quantos serviços forem necessários nos eixos E01–E09, FAB ou GERAL. Estado, etapa, quantidade e natureza da quantidade são distintos. `snapshot/total_reportado` não é incremento diário.
5. Em **Fotos**, usar câmera ou galeria, inserir legenda e vincular a foto à frente. Imagens viram JPEG até 1600 px e 2 MB, sem metadados EXIF/GPS herdados da imagem original.
6. Em **Revisar**, salvar rascunho local (IndexedDB), exportar JSON de conferência (sem fotos) ou enviar após marcar a declaração de revisão.
7. O envio faz commit atômico de RDO JSON e imagens em nova branch privada `rdo/<data>/<uuid>` e abre uma **Pull Request em modo draft** contra `main` do repositório privado.
8. O GitHub Actions privado valida integridade das fotos, quantidade, vínculo e classificação. O administrador analisa e decide pela incorporação ao histórico privado.

A falta de um relato em algum dia não caracteriza paralisação. Não são gerados ensaios, aceite técnico, liberação de etapa, medição ou RNC de modo automático.

## Conexão com o modelo técnico-gerencial

O `rdo-mobile/1.0.0` utiliza identificadores de RDO e registros imutáveis e campos `target` E01–E09, FAB, GERAL. A saída do `scripts/conectar_rdo_gerencial.py` contém `registros_propostos` ligados ao eixo e, apenas quando existir no modelo, à peça individualizada. IDs de peças informadas fora do cadastro são sinalizados para conciliação, não descartados.

A conexão **não substitui** `data/observacoes-2026-11.json`, não altera `modelo_gerencial/v1` nem publica nada. Também não insere automaticamente saldos diários. Para conciliar um lote revisado, exportar os JSONs privados e executar o importador sobre snapshot do modelo:

```bash
python scripts/conectar_rdo_gerencial.py \
  --snapshot modelo_gerencial/v1/exemplos/snapshot_publico_2026-11-24.json \
  --schema admin-rdo/schema_rdo_mobile.json \
  --input-dir /copia_autorizada/RDO_CERTARE/rdos \
  --scope interno \
  --output /pasta_privada/overlay_gerencial.json
```

O resultado **privado** contém atividades, observações e referências privadas de fotos. A opção `--scope publicavel_candidato` omite textos e caminhos privados, mas também exige revisão editorial antes de uso institucional.

## Campos de classificação e critérios de aceitação

- Serviço executado não significa conformidade ou aptidão de medição.
- `quantity_kind=total_reportado` exige `state=snapshot` e nunca é somado como incremento.
- `quantity_kind=ordinal_em_execucao` não pode ser marcado como serviço finalizado.
- Campo de elemento individual só é vinculado automaticamente se existir no snapshot do modelo (inicialmente E03-P03 e E03-P04).
- Fotos são evidência visual e não produzem aceite técnico automático.
- Todos os registros novos começam como `validation=proposto_revisao`, `review=true`.
- A falta de documento não produz bloqueio formal. Os campos `status_tech`, `hold_point`, `medicao` começam em `nao_avaliado`, `nao_configurado` e `nao_avaliada`.

## Restrições para implantação

O **site público continua inalterado** e a interface é entregue apenas em branch de prévia. O acesso por celular via link HTTPS depende de publicação futura da página estática e de que a requisição ao GitHub API funcione no navegador. Para substituir o token por login de verdade, será preciso configurar OAuth (servidor ou provedor). Não colocar tokens em GitHub Pages. Não tentar criar senha fixa em JavaScript, que seria uma proteção falsa.

## Evolução: histórico privado por frente (prévia)

A quinta aba **Histórico** permite selecionar E01–E09, FAB, GERAL ou todas as frentes e consultar registros existentes nas propostas de RDO do repositório privado. O filtro de situação considera o estado da Pull Request. A API retorna até **20 PRs mais recentes** por consulta, sendo exibidas somente as branches no padrão `rdo/` com arquivos RDO no formato esperado. O resultado **não equivale a um inventário histórico exaustivo**. Consultas são read-only e exigem a autenticação GitHub existente.

A tela apresenta data, eixo, serviço, fase, atividade, natureza da quantidade, contagem de fotos associadas e link para a PR privada. Não baixa fotografias para o painel e não registra imagens em cache persistente. A classificação da PR (draft/aberta/fechada/mesclada) **não é homologação de campo**, aceite técnico nem liberação contratual. Propostas encerradas sem mesclagem também permanecem distinguíveis. Ausência de registro não indica paralisação.

O teste de navegação usa API simulada para verificar filtro E09, leitura de JSON da branch privada, indicação de revisão e link privado em desktop e celular. **Integração real com PAT não executada**. Ficam pendentes: paginação para histórico completo, consulta independente de fotos e vínculos documentais, gestão da homologação com assinatura e perfis institucionais e ensaios de segurança em hospedagem aprovada. Nenhuma alteração em `main` ou no painel público.
