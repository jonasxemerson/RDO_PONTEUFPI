# Entrega — modelo técnico-gerencial v1 da Ponte da UFPI

Esta entrega desenha e implementa o **contrato de dados** (sem criar telas), com migração não destrutiva dos relatos confiáveis.

- [`docs/MODELO_TECNICO_GERENCIAL_V1.md`](docs/MODELO_TECNICO_GERENCIAL_V1.md): arquitetura, entidades, decisões, exemplos reais, governança, integração e critérios de aceite.
- [`modelo_gerencial/v1/schema_snapshot.json`](modelo_gerencial/v1/schema_snapshot.json): schema JSON formal, com entidades operacionais futuras.
- [`scripts/gerar_modelo_gerencial.py`](scripts/gerar_modelo_gerencial.py): adaptador determinístico dos JSONs da obra (não altera a fonte).
- [`scripts/validar_modelo_gerencial.py`](scripts/validar_modelo_gerencial.py): validação de esquema, fontes/SHAs, vínculos, quantidades e regras.
- [`tests/test_modelo_gerencial.py`](tests/test_modelo_gerencial.py): testes de integridade e casos negativos.
- [`examples/snapshot_interno_2026-11-24.json`](examples/snapshot_interno_2026-11-24.json): fotografia para trabalho interno; inclui achados e controles documentais do arquivo de auditoria. **Não publicar.**
- [`examples/snapshot_publico_2026-11-24.json`](examples/snapshot_publico_2026-11-24.json): exemplo publicável com indicadores e referências dos 45 eventos permitidos na exportação atual.

**Situação:** já produzido e testado com a base de referência de 24/11/2026. **Não houve merge com `main` nem alteração de painel ou boletim.**