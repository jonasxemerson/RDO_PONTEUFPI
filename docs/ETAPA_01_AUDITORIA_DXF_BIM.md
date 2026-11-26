# CERTARE — Etapa 01: inventário e auditoria CAD para modelo BIM fiel

## Objetivo
Conectar documentos de projeto à construção geométrica auditável, começando pelo inventário dos arquivos DXF e sem atribuir coordenadas ou seções ao modelo público antes da conferência de projeto.

## Entradas aceitas
- Arquivo **.dxf** isolado, diretório contendo DXFs ou **.zip** com DXFs.
- Limite por arquivo de 100 MiB e 100 arquivos por lote.
- Não realiza upload nem lê RDOs/fotos privados. Nenhum modelo IFC ou GLB é criado nesta etapa.

## Execução local
Instalar Python 3 e `ezdxf>=1.3,<2`:

```bash
python -m pip install "ezdxf>=1.3,<2"
python scripts/auditar_dxf_projeto.py "/caminho/DXF(3).zip" --output "/pasta_privada/inventario_dxf.json"
```

O relatório inclui SHA256 por DXF, versão CAD, código INSUNITS, tipos e contagens de entidades, camadas utilizadas e bounding box do modelspace. Todos os resultados geométricos são **brutos e não verificados**.

**Atenção:** EXTMIN/EXTMAX, limites de entidades CAD, unidades declaradas e quantidade de círculos não constituem automaticamente locação de estacas, dimensões executivas ou coordenadas georreferenciadas.

## Revisões necessárias antes da geração de geometria

1. **Prancha 11:** comparar índices de estacas, coordenadas e unidades com a base de acompanhamento. Há evidência anterior de contagem documental de **270** em quadros da prancha e **292** no controle do site; nenhuma contagem será apagada sem identificação de revisão e escopo.
2. **E07:** revisar divergências/duplicidades de coordenadas e identidade das peças. Não posicionar por aproximação.
3. **Transformação CAD → referência de projeto:** confirmar sistema, origem, rotação e escala por coordenadas de controle independentes, não por ajuste visual.
4. **Pranchas 12–16:** reconstruir seções de estacas/blocos/pilares/travessas/longarinas e relações com a implantação.
5. **Publicação:** emitir relatório de QA com prancha, revisão, cotas verificadas e identificador de cada objeto. Só então autorizar GLB/XKT derivado e IFC fonte.

## Status
O presente código é a **Etapa 01A — inventário**, não a própria modelagem executiva. O Portal BIM permanece com `approval_state=aguardando_geometria_validada`. O modelo esquemático continua no painel, mas não é fonte de dimensões. Nenhuma data, serviço ou quantitativo de obra é modificado por este inventário.

## Verificações do CI
Testes de DXF gerados exclusivamente para a suíte de teste verificam: entidades e camadas, unidade declarada, hashes, arquivo ZIP com pasta interna, proteção contra travessia de diretório, fontes vazias e bloqueio de homologação. Esses DXFs sintéticos **não são usados** no modelo da ponte.

## Próxima entrega geométrica
Com o conjunto de arquivos de projeto disponível na execução: matriz de correspondência entre coordenadas e quadros da prancha 11, com campos `identificador_prancha`, `revisao`, `referencia_dxf`, `coordinate_x`, `coordinate_y`, `unidade`, `evidencia`, `status_validacao`, e transformação CAD validada. Depois, GLB por eixo e IFC de origem.
