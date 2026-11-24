#!/usr/bin/env python3
"""Vinculação auditável de evidências documentais ao modelo gerencial.

Entrada: manifesto local de documentos e vínculos, preferencialmente privado.
Saída: overlay de referências; NÃO publica arquivo, conteúdo ou URL privada,
NÃO altera saldos, nem infere conformidade, autorização ou medição.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

VALID_TYPES = {"projeto", "rdo", "fotografia", "ensaio", "parecer", "ata",
               "comunicacao", "medicao", "outro"}
VALID_VISIBILITY = {"privado", "publico"}
VALID_TARGET = {"evento", "elemento", "eixo"}
VALID_STATUS = {"referenciado", "pendente_conferencia"}
AXES = {f"E{i:02d}" for i in range(1, 10)}

def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def _identifier(value, label):
    if not isinstance(value, str) or not value.strip() or len(value) > 120:
        raise ValueError(f"{label}: identificador ausente ou inválido")
    if not all(c.isalnum() or c in "-_." for c in value):
        raise ValueError(f"{label}: caracteres inválidos")

def build_links(snapshot, manifest):
    if snapshot.get("id_empreendimento") != "ponte-ufpi":
        raise ValueError("Snapshot de empreendimento incompatível")
    if manifest.get("schema_version") != "vinculos-documentais/1.0.0":
        raise ValueError("Versão do manifesto incompatível")
    if manifest.get("project") != "ponte-ufpi":
        raise ValueError("Empreendimento do manifesto incompatível")
    if set(manifest) != {"schema_version", "project", "documents", "links"}:
        raise ValueError("Chaves não reconhecidas no manifesto")
    events = {row["id"] for row in snapshot.get("referencias_eventos", [])}
    elements = {row["id"] for row in snapshot.get("elementos_individualizados", [])}
    axes = {row["id"] for row in snapshot.get("eixos", [])}
    valid_ids = {"evento": events, "elemento": elements, "eixo": axes}
    docs, links = {}, []
    for document in manifest["documents"]:
        required = {"id", "type", "visibility", "reference", "sha256", "version"}
        if not isinstance(document, dict) or set(document) != required:
            raise ValueError("Documento com campos ausentes ou extras")
        _identifier(document["id"], "documento")
        if document["id"] in docs:
            raise ValueError("Documento duplicado: " + document["id"])
        if document["type"] not in VALID_TYPES:
            raise ValueError("Tipo documental inválido")
        if document["visibility"] not in VALID_VISIBILITY:
            raise ValueError("Visibilidade inválida")
        if not isinstance(document["reference"], str) or not document["reference"].strip():
            raise ValueError("Referência documental vazia")
        if not isinstance(document["version"], str) or not document["version"].strip():
            raise ValueError("Versão documental vazia")
        checksum = document["sha256"]
        if checksum is not None and (not isinstance(checksum, str) or
                                     len(checksum) != 64 or
                                     any(c not in "0123456789abcdef" for c in checksum)):
            raise ValueError("SHA-256 inválido")
        docs[document["id"]] = document
    seen = set()
    for link in manifest["links"]:
        required = {"document_id", "target_type", "target_id", "status"}
        if not isinstance(link, dict) or set(link) != required:
            raise ValueError("Vínculo com campos ausentes ou extras")
        d, t, target = link["document_id"], link["target_type"], link["target_id"]
        if d not in docs:
            raise ValueError("Documento inexistente em vínculo")
        if t not in VALID_TARGET or target not in valid_ids[t]:
            raise ValueError("Destino não homologado no snapshot: " + str(target))
        if link["status"] not in VALID_STATUS:
            raise ValueError("Situação do vínculo inválida")
        key = (d, t, target)
        if key in seen:
            raise ValueError("Vínculo duplicado: " + str(key))
        seen.add(key)
        links.append(dict(link))
    # Overlay interno somente: referências podem conter caminhos ou metadados privados.
    return {
        "schema_version": "evidencias-overlay/1.0.0",
        "project": "ponte-ufpi",
        "visibility": "privado",
        "status": "proposta_nao_homologada",
        "documents": list(docs.values()),
        "links": links,
        "counts": {"documents": len(docs), "links": len(links)},
        "controls": {
            "quantitativos_alterados": False,
            "aceite_tecnico_inferido": False,
            "hold_point_liberado": False,
            "medicao_autorizada": False,
            "publicavel": False,
        },
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    overlay = build_links(_load(args.snapshot), _load(args.manifest))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(overlay, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Overlay privado: {overlay['counts']['documents']} documentos e {overlay['counts']['links']} vínculos. Nenhum aceite ou quantitativo alterado.")

if __name__ == "__main__":
    main()
