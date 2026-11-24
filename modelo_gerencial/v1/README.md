# Modelo técnico-gerencial v1 — Ponte da UFPI

**Objetivo:** implementar o contrato de dados técnico-gerencial, preservando a base de campo e sem modificar o painel ou os arquivos de publicação.

- [Modelo lógico e critérios de auditoria](MODELO_TECNICO_GERENCIAL_V1.md)
- [Schema JSON 2020-12](schema_snapshot.json) — 28 definições, incluindo estruturas de RNC, RFI, ensaios, hold points, medições, documentos e decisões
- [Exemplo de projeção pública 24/11/2026](exemplos/snapshot_publico_2026-11-24.json) — 45 referências publicáveis; valores agregados sem ajuste artificial
- [Gerador não destrutivo](../../scripts/gerar_modelo_gerencial.py)
- [Validador com reconciliação de fontes](../../scripts/validar_modelo_gerencial.py)
- [Gerador do próprio schema](../../scripts/gerar_schema_estrutural.py)
- [Testes de integridade](../../tests/test_modelo_gerencial.py)

## Geração e validação

```bash
python -m pip install jsonschema
python scripts/gerar_modelo_gerencial.py --root . --scope publico --output /tmp/snapshot_publico.json
python scripts/gerar_modelo_gerencial.py --root . --scope interno --output /tmp/snapshot_interno.json
python scripts/validar_modelo_gerencial.py --root . --snapshot /tmp/snapshot_publico.json
MODEL_REPO_ROOT=. python -m unittest discover -s tests -p 'test_modelo_gerencial.py' -v
```

O snapshot interno com os 20 achados da auditoria e as 14 recomendações documentais **não** está neste repositório público. É entregue à parte, em pacote local. Os exemplos de controles formais começam vazios para não inventar atos administrativos, ensaios ou aceites. Para credenciais, registros sensíveis e documentos operacionais internos, utilizar armazenamento privado autenticado.

**Status:** somente a branch de desenvolvimento contém estes arquivos; `main`, `painel-cliente.html`, `index.html` e `data/*.json` continuam intactos.
