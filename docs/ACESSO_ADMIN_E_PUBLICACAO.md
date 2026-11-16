# CERTARE — política de administração, publicação e autenticação

## Acesso administrativo com GitHub-only

A autenticação de editores é realizada **pelo GitHub**, com conta individual (senha/passkey e 2FA recomendada) e permissões atribuídas ao repositório. O painel público não aceita credenciais e não possui token, chave de API ou endpoint de escrita.

- O link **Acesso administrativo via GitHub** encaminha o editor à interface nativa do GitHub. O GitHub exige login para salvar alterações; usuários sem permissão no repositório não podem modificar a fonte oficial.
- Alterações em `data/observacoes-AAAA-MM.json` devem ocorrer em branch com Pull Request, passando por `scripts/validar_dados.py`, conferência de quantitativos e aprovação humana.
- **Operação individual:** não se exige revisão por CODEOWNERS nem aprovação de outro usuário; a autoria, o histórico e a responsabilidade permanecem vinculados à conta GitHub do administrador. O GitHub Actions deve ser configurado como bloqueio técnico obrigatório antes do merge.
- Ruleset recomendado para `main`: exigir Pull Request, exigir sucesso dos checks `validar` e `testar_visual`, permitir zero aprovações, desativar `Require review from Code Owners`, bloquear exclusão e force push, sem bypass. As definições do ruleset são alteradas nas configurações do GitHub, não por este repositório.
- Quando um segundo colaborador habilitado passar a revisar os dados, aumentar o número de aprovações para 1 e reintroduzir CODEOWNERS, se necessário.

## O que NÃO está implementado

Não existe formulário de senha próprio para o HTML. GitHub Pages padrão não oferece autenticação de visitante/controle de acesso por sessão; uma senha escrita no JavaScript não protegeria a área administrativa. Um painel web privado próprio exigiria um componente de autenticação do lado servidor ou GitHub Enterprise Cloud Pages privado em organização elegível.

## Publicação institucional

O GitHub Actions executa `scripts/gerar_site_publico.py` e publica uma pasta `site/` gerada, não a raiz do repositório. O novo `index.html` da publicação é gerado de `painel-cliente.html`; a geometria 4D usa `scripts/modelo-4d-publico.js`. A versão operacional `index.html`, importadores e histórico local não entram no artefato publicado.

O script aplica duas condições antes de exportar qualquer evento: documento mensal com `approval_state=homologado` (homologação explícita) **e** evento `validation=validado_campo`, sem marcação `review=true`. Exporta apenas atributos permitidos. Se nada tiver sido homologado, a área de novidades permanece vazia e indicadores históricos continuam rotulados como não reconciliados.

**Atenção**: isso impede acesso casual pelo **site**, mas não protege informações que já constam no repositório público e em seu histórico Git. Nunca registrar documentos ou dados confidenciais nesse repositório; caso necessário, transferir os dados operacionais para repositório privado e distribuir apenas exportações aprovadas no site público. A migração ou remoção de conteúdo sensível existente exige auditoria específica.

## Política de avanço

- Ausência de relato ou visita não significa paralisação.
- Snapshots acumulados não são incrementos e não devem ser somados.
- Etapas necessárias podem ser concluídas por inferência apenas para a mesma peça identificada; não geram aceitação, ensaios ou medições.
- Não calcular avanço global ponderado ou atraso frente ao planejado sem cronograma-base validado e critérios de ponderação.
- O modelo 4D é uma geometria ilustrativa; peças e cores por frente representam uma leitura agregada da base histórica, não levantamento individual.

## Liberação individual

O administrador registra alterações por branch/PR e verifica a passagem dos checks automáticos antes de integrar. Para os indicadores legados, nenhuma quantidade adicional será declarada como homologada sem evidência técnica associada. A aprovação editorial para exibição do painel não equivale a atesto de medição contratual.
