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
        # Assinaturas corretas da CERTARE e SDU Norte no canto superior esquerdo.
        assert page.locator(".brand-logos").is_visible()
        assert page.locator(".institutional-band").count() == 0
        assert page.locator(".brand-logos .brand-certare").count() == 1
        assert page.locator(".brand-logos .brand-sdu").count() == 1
        for selector in (".brand-certare", ".brand-sdu"):
            assert page.locator(selector).evaluate("(img) => img.complete && img.naturalWidth > 0")
            assert page.locator(selector).get_attribute("src").startswith("assets/")
        assert page.locator(".brand-certare").get_attribute("src") == "assets/logo-grupo-certare-oficial.svg"
        sdu_svg=(ROOT/"assets/sdu-norte-identificacao.svg").read_text(encoding="utf-8")
        assert 'viewBox="0 0 420 92"' in sdu_svg
        assert 'fill="#2057A6"' in sdu_svg
        assert '<rect' not in sdu_svg and '<path' not in sdu_svg, "Placa ou fundo retangular reapareceu"
        assert 'Superintendência de Desenvolvimento' in sdu_svg
        assert 'Urbano • Norte — Teresina/PI' in sdu_svg

        assert page.locator(".brand-logos").evaluate(
            "(el) => el.closest('header') !== null && el.getBoundingClientRect().left < 60"
        )
        assert page.locator(".brand-sdu").evaluate(
            "(el) => el.getBoundingClientRect().left > document.querySelector('.brand-certare').getBoundingClientRect().right"
        )
        assert page.locator(".brand-logos").evaluate(
            "(el) => el.getBoundingClientRect().right < innerWidth - 5"
        )

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
        assert page.locator("#kpiEstacas").inner_text() == "145 / 292"
        assert page.locator("#kpiConcretadas").inner_text() == "111 / 292"
        assert page.locator("#kpiLongarinas").inner_text() == "3 / 64"
        assert page.locator("#kpiBlocos").inner_text() == "2 / 9"
        assert page.locator("#kpiPilares").inner_text() == "6 / 36"
        assert page.locator("#noticePending").is_hidden()
        assert page.locator(".summary-row").count() == 0
        assert page.evaluate("() => !!document.getElementById('certare-config')")
        assert page.locator("#fieldProgress .progress-card").count() == 6
        assert "+218" in page.locator("#fieldProgress").inner_text()
        assert "2 parciais" in page.locator("#fieldProgress").inner_text()
        assert "25 / 24" in page.locator("#fieldProgress").inner_text()
        assert "19 / 37" in page.locator("#fieldProgress").inner_text()
        assert "13 / 32" in page.locator("#fieldProgress").inner_text()
        assert "3" in page.locator("#fieldProgress").inner_text()
        assert "não prova erro de locação" in page.locator("#fieldCaveat").inner_text()
        assert page.evaluate("JSON.parse(document.getElementById('certare-config').textContent).consolidacao.registros_homologados === 59")
        assert page.locator("#axisProgress button").count() == 9
        assert page.locator('[data-progress-mode="execucao"]').get_attribute("aria-pressed") == "true"
        assert page.locator("#axisProgress button[data-axis='7'] .axis-progress-count").inner_text() == "19 / 37"
        assert page.locator("#axisProgress button[data-axis='8'] .axis-progress-count").inner_text() == "13 / 32"
        assert "25 / 24" in page.locator("#axisProgress button[data-axis='9'] .axis-progress-count").inner_text()
        assert "+1 além do previsto" in page.locator("#axisProgress button[data-axis='9'] .axis-progress-count").inner_text()
        assert page.locator("#axisProgress button[data-axis='9']").get_attribute("data-source") == "campo_homologado"
        assert page.locator("#axisProgress button[data-axis='9']").get_attribute("data-excess") == "true"
        assert page.locator("#axisProgress button[data-axis='9'] .axis-progress-concrete").count() == 1
        assert "145 estacas" in page.locator("#progressContext").inner_text()
        page.locator('[data-progress-mode="concretagem"]').click()
        assert page.locator('[data-progress-mode="concretagem"]').get_attribute("aria-pressed") == "true"
        assert page.locator("#axisProgress button[data-axis='7'] .axis-progress-count").inner_text() == "4 / 37"
        assert page.locator("#axisProgress button[data-axis='8'] .axis-progress-count").inner_text() == "11 / 32"
        assert page.locator("#axisProgress button[data-axis='9'] .axis-progress-count").inner_text() == "8 / 24"
        assert "111 estacas" in page.locator("#progressContext").inner_text()
        page.locator('[data-progress-mode="execucao"]').click()
        assert page.locator('#axisProgress button[data-axis="9"] .axis-progress-count').inner_text().startswith("25 / 24")
        assert page.evaluate("JSON.parse(document.querySelector('#certare-config').textContent).estacas.historicas_por_eixo[7] === 11")
        assert page.locator("#axisChooser button").count() == 9
        assert page.locator("#timelineSelect").is_enabled()
        assert page.locator("#timelineContent .timeline-event").count() > 0
        assert page.locator("#timelineSelect").input_value() == "2026-11-24"
        assert page.evaluate("window.CertarePublicEvents.length > 20")
        assert page.evaluate("JSON.parse(document.querySelector('#certare-config').textContent).consolidacao.registros_homologados >= 41")
        assert page.evaluate("JSON.parse(document.querySelector('#certare-config').textContent).consolidacao.longarinas_concretadas_inferidas === 1")
        assert "Camisas" not in page.locator("#kpiEstacas").inner_text()
        assert "registros nesta data" in page.locator("#timelineCount").inner_text()
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
        assert page.locator("#modelMarkers .axis-marker[data-progress]").count() >= 1
        page.locator("#axisChooser button[data-axis=\"9\"]").click()
        assert page.locator("#axisTitle").inner_text() == "Eixo 09"
        assert "Concretagem identificada" in page.locator("#axisRows").inner_text()
        assert "25" in page.locator("#axisRows").inner_text()
        assert "Excedente de execução sobre projeto" in page.locator("#axisRows").inner_text()
        assert "registro anterior, não é estágio atual" in page.locator("#axisRows").inner_text()
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
