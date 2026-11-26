# CERTARE — Estratégia de modelo BIM fiel para a Ponte da UFPI

## 1. Diagnóstico da publicação atual

O renderizador em `scripts/modelo-4d-publico.js` é **esquemático**: espaçamento entre eixos constante (`L=76`, unidades gráficas), alturas e dimensões armazenadas em `CONST`, distribuição gráfica de estacas por índice. O arquivo declara explicitamente ausência de equivalência métrica. NÃO serve para aferir cotas, locação ou interferências.

O modelo não deve ser simplesmente retocado como se fosse geometria de projeto. Preservar a maquete como **representação conceitual** enquanto se constrói um modelo independente georreferenciado.

## 2. Plano de execução por fontes verificáveis

| Etapa | Evidência necessária | Resultado |
|---|---|---|
| 0. Inventário documental | Índice de revisões das pranchas, DXF/DWG, escalas, notas e referenciais | Matriz de origem e vigência |
| 1. Implantação e locação | Prancha 11, tabelas de coordenadas, eixos, estacas e unidades | Transformação e orientação conferidas |
| 2. Seções estruturais | Pranchas 12 a 16, cortes e detalhamentos | Blocos, pilares, travessas, longarinas e tabuleiro dimensionados |
| 3. Conciliação de geometrias | Coordenadas remanescentes, divergência E07, unidades e transformação CAD→mundo | Lista de discrepâncias com resolução fundamentada |
| 4. Modelo federado | Geometrias verificadas, nomes de componentes e GUIDs de projeto, sem inventar identificação de campo | IFC (preferencialmente IFC4.3 se houver suporte da ferramenta) e derivado GLB/XKT |
| 5. Conferência cruzada | Comprimentos, offsets, seções, quantitativos e vistas 2D/3D | Relatório de QA geométrico com prancha/revisão |
| 6. Integração 4D | Eixos/frentes e somente elementos realmente individualizados por evidência | Camadas por fonte e estado: previsto, observado, inferido, confirmado e não localizado |

Números históricos atualmente controlados: **9 eixos, 8 vãos, 292 estacas projetadas**. Esses números são validações de consistência, não geometria suficiente para posicionar todas as peças.

## 3. Pilha tecnológica considerada

- **xeokit + XKT**: opção preferencial para visualizador institucional de modelo IFC convertido e versionado; seleção e propriedades de elementos, árvore, cortes, visibilidade, modelo grande e coordenadas precisas. XKT é um derivado otimizado; o IFC permanece como fonte primária.
- **That Open (web-ifc / Fragments)**: alternativa para pipeline e ferramentas IFC diretamente integradas a Three.js, com propriedades, seleção e conversão. Exige empacotamento de bibliotecas e WASM.
- **Speckle viewer**: boa opção para visualização compartilhada e incorporação de vista publicada em iframe com controle de acesso externo. Um link de modelo externo não substitui homologação dos dados.
- **Autodesk APS**: viável para formatos proprietários e ecossistema Autodesk, mas requer configuração de aplicação, conversão de arquivos e autenticação em backend.

O primeiro piloto escolhe **GLB local em navegador** para conferência visual e espaço opcional de visualização Speckle aprovada. **GLB NÃO é substituto do IFC em informações de elementos.** A seleção do motor BIM final fica condicionada ao modelo IFC real e ao desempenho medido.

## 4. Implementação atual (branch de prévia)

- `bim/index.html`: portal separado com câmera orbital para GLB carregado **localmente**, sem fazer upload; e área de iframe Speckle apenas se um manifesto validado informar URL de origem autorizada.
- `bim/modelo-manifest.json`: bloqueado em `aguardando_geometria_validada`. Sem URL inventada, sem modelo fictício e sem credencial no frontend.
- `painel-cliente.html`: entrada no portal mantendo o renderizador antigo e demais indicadores.
- `scripts/gerar_site_publico.py`: publica apenas portal e manifesto. Nenhum IFC, GLB ou foto é automaticamente incluído.
- `scripts/testar_painel_visual.py`: smoke test da navegação ao portal em desktop e celular.

O portal carrega o componente web externo `model-viewer` para preview GLB; isso requer conectividade. O arquivo GLB local fica no dispositivo, sem envio ao GitHub, mas bibliotecas JS externas são executadas na página. Para uso com dados sigilosos, exigir revisão de segurança e hospedagem autônoma/pacote de dependências antes de liberar uploads mesmo locais.

## 5. Critérios de liberação de um modelo fiel

1. Identificar código/revisão de cada prancha e comprovar unidades reais, orientação e plano de referência.
2. Resolver a divergência E07 e a conferência das coordenadas remanescentes antes de afirmar locações geométricas.
3. Amostrar cotas de cada tipo estrutural (estaca, bloco, pilar, travessa, longarina, tabuleiro) contra planta/corte.
4. Registrar matriz `ID BIM → prancha / identificação de projeto → frente de obra`. Sem evidência, deixar vínculo individual não homologado.
5. Segregar coordenadas locais de levantamento, georreferência, esboços e modelos de demonstração.
6. Publicar só ativos públicos autorizados; não expor arquivos de execução, fotos e RDOs privados via GitHub Pages.
7. Validar desktop e celular, navegação, memória, carregamento, seleção de objetos e integridade do progresso já publicado.
8. Confirmar implantação no GitHub Pages somente após CI aprovado.

## 6. Restrições do primeiro piloto

O repositório público **não contém IFC/DWG/DXF validado nem GLB/XKT da ponte**. Por isso o portal é uma **infraestrutura funcional para receber o modelo**, e NÃO uma reconstrução fiel já concluída. A maquete anterior continua rotulada como esquemática. O avanço físico de 26/11 permanece derivado dos registros auditáveis, não da existência de malhas.
