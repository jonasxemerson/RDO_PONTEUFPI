#!/usr/bin/env python3
"""Smoke tests reais em Chromium, desktop e mobile, do pacote GitHub Pages."""
from pathlib import Path
from playwright.sync_api import sync_playwright
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import threading, os, re

ROOT = Path(__file__).resolve().parents[1] / "site"
assert (ROOT / "index.html").is_file(), "Gere site/ antes do teste"
os.chdir(ROOT)
class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass
server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
url = f"http://127.0.0.1:{server.server_port}/"
out = Path(__file__).resolve().parents[1] / "screenshots-ci"
out.mkdir(exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
    for name, dimensions in [("desktop", {"width": 1440, "height": 900}), ("mobile", {"width": 390, "height": 844})]:
        page = browser.new_page(viewport=dimensions, device_scale_factor=1)
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        response = page.goto(url, wait_until="networkidle")
        assert response.status == 200, f"HTTP {response.status}"
        assert page.title().startswith("Ponte da UFPI")
        assert page.locator("#bridge4d").is_visible()
        assert page.locator("canvas#bridge4d").evaluate("(e) => e.width > 0 && e.height > 0")
        assert page.evaluate("typeof window.Certare4D?.setSelection === 'function'")
        assert page.locator("#axisTitle").inner_text() == "Eixo 07"
        assert page.locator("nav a").count() == 4
        assert page.get_by_text("Importar RDO").count() == 0
        assert page.get_by_text("Agente de atividades").count() == 0
        assert page.evaluate("() => document.documentElement.scrollWidth <= innerWidth + 3"), "Transbordamento horizontal"
        # Integridade visual: pixels opacos pintados no canvas.
        painted = page.locator("#bridge4d").evaluate("""canvas => {
          const ctx=canvas.getContext('2d'),d=ctx.getImageData(0,0,canvas.width,canvas.height).data;
          let n=0;for(let i=3;i<d.length;i+=257*4){if(d[i]>0)n++}return n
        }""")
        assert painted > 5, f"Canvas vazio ({painted})"
        page.locator("#modelZoomIn").click()
        page.locator('[data-model-layer="fundacoes"]').click()
        assert page.locator('[data-model-layer="fundacoes"]').get_attribute("aria-pressed") == "true"
        page.evaluate("window.Certare4D.setSelection(9)")
        # O modelo é visualização; API pública de seleção não modifica KPI institucional.
        page.locator("#estrutura").scroll_into_view_if_needed()
        page.screenshot(path=str(out / f"painel-{name}.png"), full_page=True)
        assert not errors, "Erros JavaScript: " + "; ".join(errors)
        page.close()
        print(f"OK: Chromium {name}, canvas {painted} amostras pintadas, sem erros JS")
    browser.close()
server.shutdown()
