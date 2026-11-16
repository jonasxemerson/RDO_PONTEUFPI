#!/usr/bin/env python3
"""Constrói exclusivamente o artefato institucional publicável.
Não é mecanismo de sigilo do repositório: dados privados NÃO podem ser commitados em repo público.
"""
from pathlib import Path
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "site"
if DEST.exists():
    shutil.rmtree(DEST)
(DEST / "scripts").mkdir(parents=True)
(DEST / "data").mkdir(parents=True)
# Fonte única e auditável para indicadores de referência, incorporada no HTML.
cfg = json.loads((ROOT / "data/indicadores-historicos.json").read_text(encoding="utf-8"))
ax = cfg["estacas"]["previstas_por_eixo"]
hist = cfg["estacas"]["historicas_por_eixo"]
assert len(ax) == len(hist) == cfg["eixos"] == 9
assert all(isinstance(x, int) and x > 0 for x in ax)
assert all(isinstance(x, int) and 0 <= x <= a for x, a in zip(hist, ax))
assert len(cfg["blocos"]["historicos_por_eixo"]) == cfg["eixos"]
assert len(cfg["pilares"]["historicos_por_eixo"]) == cfg["eixos"]
assert cfg["classification"] == "referencia_historica_nao_homologada"
html = (ROOT / "painel-cliente.html").read_text(encoding="utf-8")
assert "<!-- CERTARE_CONFIG -->" in html
payload = json.dumps(cfg, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
html = html.replace("<!-- CERTARE_CONFIG -->", '<script id="certare-config" type="application/json">' + payload + "</script>")
(DEST / "index.html").write_text(html, encoding="utf-8")
shutil.copy2(ROOT / "scripts/modelo-4d-publico.js", DEST / "scripts/modelo-4d-publico.js")
shutil.copy2(ROOT / "scripts/painel-v2.js", DEST / "scripts/painel-v2.js")
(DEST / ".nojekyll").write_text("", encoding="utf-8")

manifest = json.loads((ROOT / "data/manifest.json").read_text(encoding="utf-8"))
exported = []
seen = set()
for path in manifest.get("files", []):
    if not isinstance(path, str) or not path.startswith("data/observacoes-") or not path.endswith(".json") or "/" in path[5:]:
        raise ValueError(f"Arquivo de dados inesperado: {path!r}")
    doc = json.loads((ROOT / path).read_text(encoding="utf-8"))
    # Nenhum dado pendente de homologação deve ser publicado no painel institucional.
    approved = doc.get("approval_state") == "homologado"
    # Status desconhecido nunca equivale a autorização de publicação.
    items = []
    for row in doc.get("events", []):
        if not approved or row.get("validation") != "validado_campo" or row.get("review", False):
            continue
        if row.get("service") in ("seguranca", "qualidade", "equipamento"):
            continue
        uid = row.get("id")
        if not uid or uid in seen:
            continue
        seen.add(uid)
        # Allowlist de campos: nenhum campo textual de evidência, mensagens ou identidade é exportado.
        items.append({key: row.get(key) for key in ("id", "date", "time", "target", "element", "service", "activity", "state", "quantity", "quantity_kind")})
    output = {"schema_version": 1, "approval_state": "publicado", "events": items, "inferences": []}
    (DEST / path).write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    exported.append(path)
(DEST / "data/manifest.json").write_text(json.dumps({"schema_version": 1, "files": exported}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Publicação institucional: {len(exported)} arquivos; {len(seen)} eventos homologados.")
