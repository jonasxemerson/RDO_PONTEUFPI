# Agente de atividades — Ponte UFPI

## Objetivo
Converter relatos de conversa em **propostas de registros** no modelo da Fiscalização 4D V5. O agente não acessa automaticamente conversas privadas do ChatGPT: o usuário deve fornecer o texto à ferramenta de IA e colar o JSON gerado na aba Agente de atividades.

## Fluxo
1. No HTML, clique em **Agente de atividades → Copiar instruções para ChatGPT**.
2. Envie as instruções e o relato relevante ao ChatGPT.
3. Cole a resposta JSON na nova aba e clique em **Analisar lançamentos**.
4. Revise cada proposta e marque apenas as corretas.
5. Clique em **Registrar selecionados**. Exporte backup JSON na aba Dados.

## Campos de cada atividade
`date`, `target`, `service`, `phase`, `status`, `qty`, `element`, `rdo`, `resource`, `reason`, `note`, `sourceText`.

Exemplo fictício:
```json
{
  "atividades": [
    {
      "date": "2026-11-10",
      "target": "E07",
      "service": "estacas",
      "phase": "CON",
      "status": "produziu",
      "qty": 2,
      "element": "",
      "rdo": "",
      "resource": "",
      "reason": "",
      "note": "Exemplo fictício: duas estacas concretadas; identificações ausentes",
      "sourceText": "Foram concretadas duas estacas do eixo 7."
    }
  ],
  "pendencias": []
}
```

## Regras
- Não presumir datas, unidades, identificação de peças ou quantitativos.
- Uma atividade iniciada em `andamento` terá `qty=0`.
- Quantidades somadas aos indicadores apenas quando `status=produziu` e `phase` corresponde à etapa final definida no HTML.
- Registros já existentes no localStorage continuam separados da referência histórica.
- A identificação de duplicados é conservadora: combina campos e evidências. **Não substitui** análise de duplicidade semântica pelo fiscal.
- A integração é local: o repositório versiona o código, **não** sincroniza registros de navegadores distintos.
- Não inserir token da API de IA ou GitHub no HTML público.
- A branch é experimental; validar em navegador e conferir os indicadores antes de mesclar em `main`.

## Evolução posterior
Para leitura direta de chats, usar uma integração autorizada por usuário com serviço backend, autenticação, fila de propostas e confirmação humana. O GitHub deve armazenar código-fonte, não segredos nem necessariamente dados operacionais de obra.
