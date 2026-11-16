# Armazenamento GitHub-only — Ponte da UFPI

## Decisão arquitetural
O **GitHub é a única fonte central**: HTML do painel em `index.html`, observações em `data/observacoes-AAAA-MM.json`, revisão via Pull Request, validação via GitHub Actions e hospedagem via GitHub Pages (habilitar em *Settings > Pages > GitHub Actions*). Não é preciso usar Supabase, Vercel ou servidor próprio.

**Atenção:** o repositório atual é **público**. Os registros publicados são extratos técnicos sem nomes/telefones; NÃO subir o ZIP ou o TXT integral da conversa, fotografias internas ou dados pessoais sem revisão de confidencialidade.

## Fonte oficial e tipos de registro
Cada `event` possui `id` estável, `date`, `time`, `target`, `element`, `service`, `activity`, `state`, `quantity`, `quantity_kind`, `detail`, `source`, `validation` e `review`.

- `snapshot` + `total_reportado`: o total comunicado em uma data **substitui o snapshot anterior**, não se soma como produção.
- `executado`: evento relatado de serviço; não implica liberação para medição.
- `em_andamento`, `parado`, `operando`: estados pontuais, válidos na data do relato; uma máquina parada em uma manhã não torna o dia ou o período todo parado.
- `inferences`: pré-requisitos necessários tecnicamente, sempre com `exact_date: null` quando a data não foi relatada. Apenas para o mesmo elemento identificado.
- Ausência de mensagens: **SEM INFORMAÇÃO**, jamais 'PARADO'.

O `approval_state: revisao_pendente` indica que o lote ainda não foi homologado. O painel exibe, mas **não altera indicadores de estacas concretadas ou medição** automaticamente.

## Processo de atualização

1. Extrair mensagens relacionadas à ponte; nunca usar valores cumulativos como incremento.
2. Produzir extrato técnico com ID de evento, data, frente, tipo e referência resumida; separar pendências e inferências.
3. Abrir uma branch e alterar somente os arquivos de mês afetados.
4. O GitHub Actions executa `scripts/validar_dados.py`; solicitar revisão humana no Pull Request.
5. Após merge em `main`, o Actions republica o GitHub Pages. O site lê o JSON com `fetch`, atualiza por comando e periodicamente, sem acesso privado de escrita no navegador.

O agente do ChatGPT com GitHub conectado pode executar os passos 1–4 diretamente no repositório, criando commits/PRs. Nenhum token de escrita do GitHub deve ser incluído no JavaScript do site.

## Compatibilidade com o protótipo existente
O app V5 ainda possui `localStorage('certare_ufpi_v4_records')` para apontamentos legados **deste navegador**. O histórico GitHub aparece em uma aba separada e não é somado ao histórico local automaticamente, para prevenir contagem dupla. Para migrar os registros existentes, exportar backup em **Dados** e revisar reconciliação por chave de evento antes de incorporar ao repositório.

## Limitações
- GitHub Pages não é banco transacional; atualizações ficam visíveis depois de commit + publicação, não em tempo real por WebSocket.
- Caso o repo permaneça público, qualquer pessoa pode consultar as observações publicadas. Reavaliar restrições de acesso se os RDOs/evidências forem confidenciais.
- As etapas de pré-requisito inferidas não podem gerar aceite contratual, resultados de ensaios ou medições automaticamente.
