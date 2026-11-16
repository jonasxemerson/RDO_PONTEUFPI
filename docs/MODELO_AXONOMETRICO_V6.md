# CERTARE — V6: maquete técnica axonométrica

## Objetivo

Substituir a estética de motor 3D genérico por uma linguagem visual de maquete técnica institucional. **O objetivo é apresentação gráfica, não revisão do projeto executivo.**

## Regras de desenho

- Câmera ortográfica/axonométrica, fundo branco ou cinza muito claro, iluminação difusa.
- Volumes estruturais neutros em off-white/cinza, contornos técnicos finos, verde restrito ao objeto selecionado.
- Na **vista geral**, a superestrutura, os apoios e os blocos constituem a silhueta. As 292 estacas são suprimidas visualmente (*nível de detalhe*, não exclusão do modelo).
- No **detalhe de eixo**, apenas as posições conceituais das estacas do eixo selecionado aparecem; nenhuma posição representa locação verificada em planta.
- **Vista geral** e **Recentrar** voltam ao nível de detalhe geral; **Detalhar eixo** expõe o nível do eixo selecionado.
- Preservar controles de perspectiva/lateral/superior/frontal, rotação, zoom, teclado, filtros, modo apresentação e navegação por eixos.

## Fonte dos dados

Quantitativos permanecem provenientes de `data/indicadores-historicos.json`. Não alterar os históricos em resposta ao modelo 3D, não somar snapshots e não supor que uma peça apresentada foi concretada. A geometria e as proporções são **composição esquemática**, sem escala, coordenadas, localizações ou dimensões de projeto verificadas.

## Arquivos alterados

- `scripts/modelo-4d-publico.js`: materiais, desenho de arestas, proporções conceituais, simplificação por nível de detalhe e inspeção de estado.
- `painel-cliente.html`: linguagem visual e controles Vista geral / Detalhar eixo.
- `scripts/testar_painel_visual.py`: testes de LOD em desktop/mobile.

## Critérios de aceite

1. Navegação pública intacta, WebGL funcionando e sem erros JavaScript em desktop e celular.
2. `visiblePiles = 0` no nível geral e `visiblePiles = 24` ao detalhar E09, conforme fonte única.
3. Reset e botão Vista geral retornam a `detailAxis = null` sem alterar indicadores de avanço.
4. Todos os dados históricos preservados e sem inferência documental automática.
5. Publicação apenas com `validar` e `testar_visual` concluídos.
