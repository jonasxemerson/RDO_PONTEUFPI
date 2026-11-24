# Vínculos de documentos e evidências — módulo técnico-gerencial

**Estado:** desenvolvimento, uso interno. Não integrado ao site público, não homologado.

O arquivo `scripts/vincular_documentos.py` liga metadados documentais a IDs já existentes no snapshot gerencial: `evento`, `elemento` ou `eixo`. O processamento **não cria elementos inexistentes** e não modifica quantitativos, etapas, qualidade, liberação, medição ou os dados originais. Para elementos não individualizados, utilize vínculo por eixo e mantenha a identificação a conciliar.

## Arquivo de entrada (privado)

```json
{
  "schema_version": "vinculos-documentais/1.0.0",
  "project": "ponte-ufpi",
  "documents": [
    {
      "id": "DOC-EXEMPLO-001",
      "type": "rdo",
      "visibility": "privado",
      "reference": "referencia-interna-sem-dados-pessoais",
      "sha256": null,
      "version": "1"
    }
  ],
  "links": [
    {
      "document_id": "DOC-EXEMPLO-001",
      "target_type": "eixo",
      "target_id": "E09",
      "status": "pendente_conferencia"
    }
  ]
}
```

**O exemplo acima é inteiramente fictício e não representa emissão real de RDO ou aprovação.**

## Processamento

```bash
python scripts/vincular_documentos.py \
  --snapshot /pasta-privada/snapshot_interno.json \
  --manifest /pasta-privada/manifesto_documental.json \
  --output /pasta-privada/overlay_vinculos.json

python -m unittest discover -s tests -p 'test_vincular_documentos.py' -v
```

O módulo verifica documentos e IDs duplicados, existência de todos os destinos, compatibilidade do empreendimento, enumerações e integridade sintática opcional de SHA-256. É uma **conciliação referencial**, não uma prova de autenticidade ou existência física do documento.

### Segurança e governança

- Não comitar manifestos, overlays, tokens, fotos, laudos ou caminhos internos em repositório público.
- O caminho `reference` é somente um identificador/ponteiro fornecido pelo operador, não significa que o módulo acessou ou verificou o conteúdo.
- A saída é classificada `privado` e `proposta_nao_homologada` mesmo quando a referência documental está corretamente vinculada.
- Um documento pode ligar-se a vários eixos, eventos ou elementos; duplicações exatas de vínculo são rejeitadas.
- `main`, o painel institucional e o 3D permanecem inalterados. A integração com a interface autenticada e a revisão formal ainda exigem desenvolvimento e aprovação.
