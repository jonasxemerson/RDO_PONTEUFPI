#!/usr/bin/env python3
"""Constrói exclusivamente o artefato institucional publicável.
Não é mecanismo de sigilo do repositório: dados privados NÃO podem ser commitados em repo público.
"""
from pathlib import Path
import json
import shutil
from consolidar_dados import build_state, APPROVED

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "site"
if DEST.exists():
    shutil.rmtree(DEST)
(DEST / "scripts").mkdir(parents=True)
(DEST / "data").mkdir(parents=True)
(DEST / "assets").mkdir(parents=True)
(DEST / "bim").mkdir(parents=True)
# Fonte única e auditável para indicadores de referência, incorporada no HTML.
cfg = build_state(ROOT)
ax = cfg["estacas"]["previstas_por_eixo"]
hist = cfg["estacas"]["historicas_por_eixo"]
assert len(ax) == len(hist) == cfg["eixos"] == 9
assert all(isinstance(x, int) and x > 0 for x in ax)
assert all(isinstance(x, int) and 0 <= x <= a for x, a in zip(hist, ax))
assert len(cfg["blocos"]["historicos_por_eixo"]) == cfg["eixos"]
assert len(cfg["pilares"]["historicos_por_eixo"]) == cfg["eixos"]
assert cfg["classification"] == "consolidacao_parcial_para_acompanhamento"
html = (ROOT / "painel-cliente.html").read_text(encoding="utf-8")
assert "<!-- CERTARE_CONFIG -->" in html
payload = json.dumps(cfg, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
html = html.replace("<!-- CERTARE_CONFIG -->", '<script id="certare-config" type="application/json">' + payload + "</script>")
(DEST / "index.html").write_text(html, encoding="utf-8")
shutil.copy2(ROOT / "assets/sdu-norte-identificacao.svg", DEST / "assets/sdu-norte-identificacao.svg")
shutil.copy2(ROOT / "assets/logo-grupo-certare-oficial.svg", DEST / "assets/logo-grupo-certare-oficial.svg")
shutil.copy2(ROOT / "scripts/modelo-4d-publico.js", DEST / "scripts/modelo-4d-publico.js")
shutil.copy2(ROOT / "scripts/painel-v2.js", DEST / "scripts/painel-v2.js")
# Porta BIM: publicar apenas o visualizador vazio e manifesto de controle.
# Nenhum arquivo de modelo/IFC/GLB privado é enviado por este gerador.
bim_manifest = json.loads((ROOT / "bim/modelo-manifest.json").read_text(encoding="utf-8"))
assert bim_manifest["schema_version"] == 1
assert bim_manifest["project"] == "ponte-ufpi"
if bim_manifest["approval_state"] != "geometria_validada":
    assert bim_manifest["public_url"] is None and bim_manifest["viewer"] is None, "Modelo não homologado não pode apontar para publicação"
shutil.copy2(ROOT / "bim/index.html", DEST / "bim/index.html")
shutil.copy2(ROOT / "bim/modelo-manifest.json", DEST / "bim/modelo-manifest.json")
(DEST / ".nojekyll").write_text("", encoding="utf-8")

manifest = json.loads((ROOT / "data/manifest.json").read_text(encoding="utf-8"))
exported = []
seen = set()
for path in manifest.get("files", []):
    if not isinstance(path, str) or not path.startswith("data/observacoes-") or not path.endswith(".json") or "/" in path[5:]:
        raise ValueError(f"Arquivo de dados inesperado: {path!r}")
    doc = json.loads((ROOT / path).read_text(encoding="utf-8"))
    # Homologação individual por autorização do responsável: não equivale a laudo ou atesto de serviço.
    # Evitar exibir mensagens de qualidade, acidentes, alegações ambientais ou nomes pessoais.
    items = []
    for row in doc.get("events", []):
        if row.get("validation") not in APPROVED:
            continue
        if row.get("service") in ("seguranca", "qualidade", "equipamento", "ambiental"):
            continue
        uid = row.get("id")
        if not uid or uid in seen:
            continue
        seen.add(uid)
        keys = ("id", "date", "time", "target", "element", "service",
                "activity", "state", "quantity", "quantity_kind", "metric")
        items.append({key: row.get(key) for key in keys})
    # Pré-requisitos em dados distintos e rotulados: não podem virar serviço medido.
    safe_inferences = []
    for inf in doc.get("inferences", []):
        if inf.get("validation") != "homologada_por_inferencia":
            continue
        if inf.get("based_on_event") not in {x.get("id") for x in doc.get("events", [])
                                             if x.get("validation") in APPROVED}:
            continue
        safe_inferences.append({key: inf.get(key) for key in
            ("id", "target", "element", "service", "activity", "state",
             "exact_date", "completed_no_later_than")})
    output = {"schema_version": 1, "approval_state": "homologado_com_ressalvas",
              "events": items, "inferences": safe_inferences}
    (DEST / path).write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    exported.append(path)
(DEST / "data/manifest.json").write_text(json.dumps({"schema_version": 1, "files": exported}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(DEST / "data/estado_consolidado.json").write_text(
    json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Publicação institucional: {len(exported)} arquivos; {len(seen)} eventos homologados; "
      f"{cfg['consolidacao']['total_estacas_concretadas_base_mais_snapshots']} estacas e "
      f"{cfg['consolidacao']['total_pilares_concretados_base_mais_snapshots']} pilares na consolidação.")
