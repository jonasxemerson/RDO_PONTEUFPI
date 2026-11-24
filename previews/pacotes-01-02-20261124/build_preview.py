#!/usr/bin/env python3
"""Gera prévia autocontida, sem tocar no site principal.

Usa exclusivamente o MESMO pipeline de consolidação/publicação da Ponte UFPI.
A prévia contém um retrato dos registros publicáveis, não dados privados dos RDOs.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CAND = HERE / "candidatos"
BACKUP = HERE / "backup"
OUT = HERE / "preview_offline.html"

subprocess.run(
    [sys.executable, str(ROOT / "scripts" / "gerar_site_publico.py")],
    cwd=ROOT,
    check=True,
)

def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")

def replace_once(content: str, old: str, new: str) -> str:
    assert content.count(old) == 1, f"Âncora ausente/duplicada: {old[:64]}"
    return content.replace(old, new, 1)

config = json.loads(read(ROOT / "site/data/estado_consolidado.json"))
manifest = json.loads(read(ROOT / "site/data/manifest.json"))
docs = [
    {
        "file": file,
        "data": json.loads(read(ROOT / "site" / file)),
    }
    for file in manifest["files"]
]
counts = config["consolidacao"]["evolucao_fisica"]
assert config["eixos"] == 9 and config["vaos"] == 8
assert counts["total_estacas_execucao_registrada"] == 145
assert counts["total_estacas_concretadas_identificadas"] == 111
assert counts["total_estacas_previstas_projeto"] == 292
assert counts["total_pilares_integralmente_concretados_registrados"] == 6
assert counts["total_longarinas_concretadas_em_campo"] == 3
assert counts["prelajes_acrescimos_reportados_novembro"] == 218
assert config["consolidacao"]["registros_homologados"] == 59
assert config["consolidacao"]["registros_pendentes"] == 1
assert sum(len(d["data"]["events"]) for d in docs) == 45

html = read(CAND / "index.html")
css = read(CAND / "styles.css")
app = read(CAND / "app.js")
three = read(CAND / "vendor/three.min.js")
certare = read(ROOT / "assets/logo-grupo-certare-oficial.svg")
sdu = read(ROOT / "assets/sdu-norte-identificacao.svg")

assert "<script" not in css.lower()
assert "</script" not in app.lower()
assert "</script" not in three.lower()

html = replace_once(
    html,
    '<link rel="stylesheet" href="styles.css">',
    "<style>\n" + css + "\n</style>",
)

html = replace_once(
    html,
    '<img class="logo-certare" src="assets/logo-grupo-certare-oficial.svg" alt="Grupo CERTARE">',
    certare.replace("<svg ", '<svg class="logo-certare" ', 1),
)
html = replace_once(
    html,
    '<img class="logo-sdu" src="assets/sdu-norte-identificacao.svg" alt="SDU Norte — Superintendência de Desenvolvimento Urbano Norte de Teresina">',
    sdu.replace("<svg ", '<svg class="logo-sdu" ', 1),
)

html = replace_once(
    html,
    '<script src="vendor/three.min.js"></script>',
    '<script>\n' + three + '\n</script>',
)

payload = json.dumps(
    {"cfg": config, "manifest": manifest, "docs": docs},
    ensure_ascii=False,
    separators=(",", ":"),
).replace("<", "\\u003c")

html = replace_once(
    html,
    '<script src="app.js"></script>',
    '<script id="offline-data" type="application/json">'
    + payload
    + '</script>\n<script>\n'
    + app
    + '\n</script>',
)

assert 'src="vendor/three.min.js"' not in html
assert 'src="app.js"' not in html
assert 'href="styles.css"' not in html
assert 'http://fonts.googleapis.com' not in html
assert 'https://fonts.googleapis.com' not in html
assert "data/estado_consolidado.json" in html  # Código de produção preservado, bypass offline via snapshot.

OUT.write_text(html, encoding="utf-8")

# Candidato de produção executável em servidor estático, usando a mesma saída
# pública da publicação atual; sem inserir dados privados e sem alterar main.
shutil.copytree(ROOT / "site/data", CAND / "data", dirs_exist_ok=True)
(CAND / "assets").mkdir(exist_ok=True)
for asset_name in ("logo-grupo-certare-oficial.svg", "sdu-norte-identificacao.svg"):
    shutil.copy2(ROOT / "assets" / asset_name, CAND / "assets" / asset_name)

with zipfile.ZipFile(HERE / "PACOTES_01_02_backup_preview.zip", "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
    zf.write(OUT, "preview_offline.html")
    for file in BACKUP.rglob("*"):
        if file.is_file():
            zf.write(file, "backup/" + file.relative_to(BACKUP).as_posix())
    for file in CAND.rglob("*"):
        if file.is_file():
            zf.write(file, "candidatos/" + file.relative_to(CAND).as_posix())
    zf.writestr(
        "LEIA_PRIMEIRO.txt",
        "1. Extraia o ZIP.\n"
        "2. Abra preview_offline.html por duplo clique, sem servidor ou Internet.\n"
        "3. Não publique os arquivos de candidatos antes da aprovação visual.\n"
        "4. Backup inclui index administrativo e painel-cliente público intactos.\n"
        "5. A data de referência, os quantitativos e as classificações vêm do pipeline central.\n"
        "6. Candidatos de produção fazem fetch dos JSONs reais, sem usar o snapshot offline.\n",
    )

print(json.dumps({
    "offline_html_bytes": OUT.stat().st_size,
    "zip_bytes": (HERE / "PACOTES_01_02_backup_preview.zip").stat().st_size,
    "backup_files": len([x for x in BACKUP.rglob("*") if x.is_file()]),
    "public_events_embedded": sum(len(d["data"]["events"]) for d in docs),
    "three_embedded": len(three),
    "reference_date": config["data_referencia"],
    "main_untouched": True,
}, ensure_ascii=False))
