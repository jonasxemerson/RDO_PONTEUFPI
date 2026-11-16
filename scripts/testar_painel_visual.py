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
        assert page.locator("#modelPresentation").is_visible()
        assert page.locator("#modelFocusAxis").is_visible()
        assert page.evaluate("window.Certare4D.inspect().conceptual === true")
        assert page.evaluate("window.Certare4D.inspect().piles === 292")
        assert page.evaluate("window.Certare4D.inspect().style === 'axonometric-clay'")
        assert page.evaluate("window.Certare4D.inspect().detailAxis === null")
        assert page.evaluate("window.Certare4D.inspect().visiblePiles === 0")
        assert page.locator("#modelOverview").is_visible()
        assert page.evaluate("window.Certare4D.inspect().axes === 9")
        assert page.locator("canvas#bridge4d").evaluate("(e) => e.width > 0 && e.height > 0")
        assert page.evaluate("typeof window.Certare4D?.setSelection === 'function'")
        assert page.locator("#axisTitle").inner_text() == "Eixo 07"
        assert page.locator("nav a").count() == 6
        assert page.locator("#kpiEstacas").inner_text() == "111 / 292"
        assert page.locator("#kpiBlocos").inner_text() == "2 / 9"
        assert page.locator("#kpiPilares").inner_text() == "4 / 36"
        assert page.locator("#noticePending").is_visible()
        assert page.locator(".summary-row").count() == 0
        assert page.evaluate("() => !!document.getElementById('certare-config')")
        assert page.locator("#axisProgress button").count() == 9
        assert page.locator("#axisChooser button").count() == 9
        assert page.locator("#timelineSelect").is_disabled()
        assert "Não há série temporal validada" in page.locator("#timelineContent").inner_text()
        assert "Nenhum evento" in page.locator("#timelineCount").inner_text()
        assert page.get_by_text("Importar RDO").count() == 0
        assert page.get_by_text("Agente de atividades").count() == 0
        assert page.evaluate("() => document.documentElement.scrollWidth <= innerWidth + 3"), ("Transbordamento horizontal: " + str(page.evaluate("""() => ({width:document.documentElement.scrollWidth, viewport:innerWidth, offenders:[...document.querySelectorAll('body *')].filter(e=>e.getBoundingClientRect().right>innerWidth+3).slice(0,12).map(e=>({tag:e.tagName,id:e.id,cls:e.className?.baseVal||e.className,right:Math.round(e.getBoundingClientRect().right)}))})""")))
        # Verificação real de WebGL: contexto, framebuffer e pixels renderizados.
        assert page.evaluate("window.Certare4D.inspect().renderer === 'webgl'")
        painted = page.locator("#bridge4d").evaluate("""canvas => {
          const gl=canvas.getContext('webgl'),pixel=new Uint8Array(4);
          if(!gl)return 0;
          let n=0;
          for(let i=2;i<28;i++)for(let j=2;j<15;j++){
            gl.readPixels(Math.floor(canvas.width*i/30),Math.floor(canvas.height*j/17),1,1,gl.RGBA,gl.UNSIGNED_BYTE,pixel);
            if(pixel[3]>0)n++;
          }
          return n;
        }""")
        assert painted > 10, f"WebGL sem geometria visível ({painted} amostras)"
        assert page.evaluate("window.Certare4D.inspect().lastVertices > 1000")
        assert page.locator("#modelMarkers .axis-marker").count() > 0
        page.locator("#axisChooser button[data-axis=\"9\"]").click()
        assert page.locator("#axisTitle").inner_text() == "Eixo 09"
        assert page.locator("#axisProgress button[data-axis=\"9\"]").get_attribute("aria-pressed") == "true"
        page.locator('[data-model-view="superior"]').click()
        assert page.evaluate("window.Certare4D.inspect().view === 'superior'")
        assert page.locator('[data-model-view="superior"]').get_attribute("aria-pressed") == "true"
        page.locator("#bridge4d").focus()
        page.keyboard.press("ArrowRight")
        page.keyboard.press("Home")
        page.locator("#modelZoomIn").click()
        page.locator("#modelFocusAxis").click()
        assert page.evaluate("window.Certare4D.inspect().detailAxis === 9")
        assert page.evaluate("window.Certare4D.inspect().visiblePiles === 24")
        assert page.evaluate("window.Certare4D.inspect().focusX !== 0")
        page.locator("#modelReset").click()
        assert page.evaluate("window.Certare4D.inspect().focusX === 0")
        assert page.evaluate("window.Certare4D.inspect().detailAxis === null")
        assert page.evaluate("window.Certare4D.inspect().visiblePiles === 0")
        page.locator("#modelFocusAxis").click()
        assert page.evaluate("window.Certare4D.inspect().visiblePiles > 0")
        page.locator("#modelOverview").click()
        assert page.evaluate("window.Certare4D.inspect().visiblePiles === 0")
        page.locator("#modelPresentation").click()
        assert page.locator("#modelMarkers .axis-marker").count() > 0
        assert page.locator("#modelPresentation").get_attribute("aria-pressed") == "true"
        assert page.locator(".model-presentation").count() == 1
        page.screenshot(path=str(out / f"modelo-apresentacao-{name}.png"))
        page.keyboard.press("Escape")
        assert page.locator(".model-presentation").count() == 0
        assert page.locator("#modelPresentation").get_attribute("aria-pressed") == "false"
        page.locator('[data-model-layer="fundacoes"]').click()
        assert page.locator('[data-model-layer="fundacoes"]').get_attribute("aria-pressed") == "true"
        page.evaluate("window.Certare4D.setSelection(9)")
        # O modelo é visualização; API pública de seleção não modifica KPI institucional.
        page.locator("#estrutura").scroll_into_view_if_needed()
        page.screenshot(path=str(out / f"painel-{name}.png"), full_page=True)
        assert not errors, "Erros JavaScript: " + "; ".join(errors)
        assert page.locator("#elementInspector").is_visible()
        page.close()
        print(f"OK: Chromium {name}, WebGL {painted} amostras opacas, sem erros JS")
    browser.close()
server.shutdown()
