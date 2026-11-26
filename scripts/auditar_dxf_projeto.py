#!/usr/bin/env python3
"""Inventário seguro e não interpretativo de arquivos DXF de projeto.

O relatório é apenas evidência de geometria CAD bruta, não um IFC/BIM e
não atesta locação, orientação, cotas ou o quantitativo de estacas.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile, BadZipFile

MAX_FILE_BYTES = 100 * 1024 * 1024
MAX_DXF_FILES = 100
UNIT_LABELS = {
    0: "nao_definida", 1: "polegadas", 2: "pes", 3: "milhas",
    4: "milimetros", 5: "centimetros", 6: "metros", 7: "quilometros",
    8: "micropolegadas", 9: "mils", 10: "jardas", 14: "decimetros",
}

def audit_bytes(raw: bytes, *, name: str) -> dict:
    try:
        import ezdxf
        from ezdxf import bbox
    except ImportError as exc:
        raise RuntimeError("Dependência ausente: pip install ezdxf") from exc

    if not raw or len(raw) > MAX_FILE_BYTES:
        raise ValueError(f"DXF vazio ou grande demais: {name}")
    with TemporaryDirectory(prefix="certare-cad-") as td:
        tmp = Path(td) / "entrada.dxf"
        tmp.write_bytes(raw)
        try:
            doc = ezdxf.readfile(tmp)
            model = doc.modelspace()
            types = Counter(ent.dxftype() for ent in model)
            layers = Counter(ent.dxf.layer for ent in model)
            # extents CAD informativos; desenho pode conter carimbos/modelagem 2D
            ext = bbox.extents(model, fast=True)
            bounds = None
            if ext.has_data:
                bounds = {
                    "min": [round(float(x), 6) for x in ext.extmin],
                    "max": [round(float(x), 6) for x in ext.extmax],
                }
            raw_unit = int(doc.header.get("$INSUNITS", 0))
            return {
                "filename": name,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "size_bytes": len(raw),
                "dxf_version": doc.dxfversion,
                "insunits_code": raw_unit,
                "insunits_label": UNIT_LABELS.get(raw_unit, "outra_ou_nao_mapeada"),
                "units_verified_against_drawing": False,
                "modelspace_entities": sum(types.values()),
                "entity_types": dict(sorted(types.items())),
                "layers": dict(sorted(layers.items())),
                "raw_cad_extents": bounds,
                "extents_are_engineering_coordinates": False,
                "identified_project_elements": [],
                "status": "inventario_cad_sem_validacao_geometrica",
            }
        except (ValueError, OSError) as exc:
            raise ValueError(f"Falha de leitura de {name}: {exc}") from exc

def collect(input_path: Path) -> list[tuple[str, bytes]]:
    if input_path.is_file() and input_path.suffix.lower() == ".dxf":
        return [(input_path.name, input_path.read_bytes())]
    if input_path.is_dir():
        paths = sorted(input_path.rglob("*"))
        files = [p for p in paths if p.is_file() and p.suffix.lower() == ".dxf"]
        if len(files) > MAX_DXF_FILES:
            raise ValueError("Mais de 100 DXF; divida por lote de projeto.")
        out = []
        for p in files:
            if p.is_symlink():
                raise ValueError("Links simbólicos não são admitidos")
            out.append((str(p.relative_to(input_path)), p.read_bytes()))
        return out
    if input_path.is_file() and input_path.suffix.lower() == ".zip":
        try:
            with ZipFile(input_path) as zf:
                selected = [entry for entry in zf.infolist()
                            if not entry.is_dir() and entry.filename.lower().endswith(".dxf")]
                if len(selected) > MAX_DXF_FILES:
                    raise ValueError("Mais de 100 DXF; divida por lote.")
                out = []
                for entry in selected:
                    name = entry.filename.replace("\\", "/")
                    if name.startswith("/") or ".." in name.split("/"):
                        raise ValueError("Caminho inseguro dentro do ZIP")
                    if entry.file_size > MAX_FILE_BYTES:
                        raise ValueError(f"Arquivo acima de 100 MB: {name}")
                    with zf.open(entry) as stream:
                        raw = stream.read(MAX_FILE_BYTES + 1)
                    if len(raw) > MAX_FILE_BYTES:
                        raise ValueError(f"Arquivo expandido excessivo: {name}")
                    out.append((name, raw))
                return out
        except BadZipFile as exc:
            raise ValueError("ZIP inválido") from exc
    raise ValueError("Informe diretório, DXF individual ou ZIP contendo DXFs")

def build_report(source: Path) -> dict:
    files = collect(source)
    if not files:
        raise ValueError("Nenhum DXF encontrado. Não produzir relatório vazio.")
    entries = [audit_bytes(raw, name=name) for name, raw in files]
    ids = [x["sha256"] for x in entries]
    return {
        "schema_version": "certare-cad-inventario/1.0.0",
        "project_id": "ponte-ufpi",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_basename": source.name,
        "classification": "levantamento_documental_nao_homologado",
        "geometry_approved": False,
        "publishable_bim": False,
        "files": entries,
        "total_files": len(entries),
        "source_hashes_sha256": ids,
        "critical_checks": {
            "prancha_11_vs_base_292_estacas": "divergencia_270_versus_292_a_conciliar",
            "e07_identificacao_repetida": "pendente_conferencia",
            "origem_e_rotacao": "pendente_conferencia",
            "pranchas_12_a_16": "secoes_nao_certificadas",
            "coordenadas_e_unidades": "nao_verificadas",
        },
        "warnings": [
            "Unidade INSUNITS apenas declarada no DXF; confirmar em planta/cotas.",
            "Extensoes do modelspace podem incluir desenhos 2D, detalhes e carimbos.",
            "Contagem de entidades CAD nao representa quantidade de estacas.",
            "Nao gerar IFC/GLB executivo ou liberar geometria sem matriz de coordenadas e revisoes.",
        ],
    }

def main() -> None:
    ap = argparse.ArgumentParser(description="Inventário e pré-auditoria de DXFs da Ponte da UFPI")
    ap.add_argument("source", type=Path, help="DXF, diretório ou ZIP de DXFs")
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    report = build_report(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Inventário gerado: {report['total_files']} DXF(s); geometria NÃO homologada.")

if __name__ == "__main__":
    main()
