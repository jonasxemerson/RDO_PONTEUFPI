#!/usr/bin/env python3
"""Teste do HTML file:/// real e do candidato ligado aos JSONs públicos."""
from __future__ import annotations
import json
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
import threading
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
OFFLINE = HERE / "preview_offline.html"
CAND = HERE / "candidatos"
assert OFFLINE.exists() and OFFLINE.stat().st_size > 650_000
assert not any(s in OFFLINE.read_text(encoding="utf-8") for s in (
    '<script src="', '<link rel="stylesheet" href=', '<img src="assets/',
)), "Dependência externa na prévia offline"
OUT = HERE / "screenshots"
OUT.mkdir(exist_ok=True)

class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

os.chdir(CAND)
server = ThreadingHTTPServer(("127.0.0.1", 0), Quiet)
threading.Thread(target=server.serve_forever, daemon=True).start()
online_local = f"http://127.0.0.1:{server.server_port}/index.html"

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True, args=[
        "--no-sandbox", "--enable-webgl", "--use-gl=angle",
        "--use-angle=swiftshader", "--enable-unsafe-swiftshader"
    ])
    results = []
    for kind, url in [
        ("offline", OFFLINE.as_uri()),
        ("candidato_json", online_local),
    ]:
        for screen, viewport in [
            ("desktop", {"width": 1440, "height": 900}),
            ("mobile", {"width": 390, "height": 844}),
        ]:
            page = browser.new_page(viewport=viewport, device_scale_factor=1)
            errors, requests = [], []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on("request", lambda request: requests.append(request.url))
            response = page.goto(url, wait_until="load")
            page.wait_for_function(
                "() => document.querySelector('#kpi-exec').textContent.includes('145')",
                timeout=30000,
            )
            assert "145 / 292" in page.locator("#kpi-exec").inner_text()
            assert "111 / 292" in page.locator("#kpi-concrete").inner_text()
            assert page.locator("#kpi-plan").inner_text() == "292"
            assert page.locator("#kpi-blocks").inner_text() == "2 / 9"
            assert page.locator("#kpi-pillars").inner_text() == "6 / 36"
            assert page.locator("#kpi-girders").inner_text() == "3 / 64"
            assert page.locator("#chartRows .chart-row").count() == 9
            assert page.locator("#timelineList button").count() == 9
            assert page.evaluate("() => window.THREE && window.THREE.REVISION") == "150"
            assert page.locator("#viewerCanvas").is_visible()
            assert page.locator("#chartRows .chart-row[data-axis='9']").inner_text().find("25 / 24") >= 0
            assert page.locator("#chartRows .chart-row[data-axis='9']").inner_text().find("+1 excedente") >= 0
            assert not page.locator("#offlineBanner").is_visible() if kind != "offline" else page.locator("#offlineBanner").is_visible()
            overflow=page.evaluate("""() => ({
                width: innerWidth, scroll: document.documentElement.scrollWidth,
                offenders: [...document.querySelectorAll('body *')].map(el=>{
                  const r=el.getBoundingClientRect();
                  return {tag:el.tagName,id:el.id,cls:String(el.className||'').slice(0,70),
                          left:Math.round(r.left),right:Math.round(r.right),width:Math.round(r.width)}
                }).filter(x=>x.right > innerWidth + 2 || x.left < -2).slice(0,20)
            })""")
            print("LAYOUT_DIAGNOSTIC",kind,screen,overflow,flush=True)
            assert overflow["scroll"] <= overflow["width"] + 2
            if kind == "offline":
                assert not any(u.startswith(("http://", "https://")) for u in requests), requests
            page.locator("#chartRows .chart-row[data-axis='9']").click()
            assert page.locator("#axisName").inner_text() == "E09"
            assert page.locator("#axisExecuted").inner_text() == "25"
            assert page.locator("#axisConcrete").inner_text() == "8"
            assert "indeterminadas" in page.locator("#axisCaveat").inner_text()
            page.locator("[data-viewer-mode='heatmap']").click()
            assert "Heatmap agregado" in page.locator("#scenePill").inner_text()
            page.locator("[data-viewer-system='fundacoes']").click()
            assert page.locator("[data-viewer-system='fundacoes']").get_attribute("aria-pressed") == "true"
            page.locator("#timelineList button[data-date='2026-11-17']").click()
            assert "17/11/2026" in page.locator("#bulletin").inner_text()
            assert page.locator("#kpi-exec").inner_text().endswith("*"), "Cronologia não pode herdar global atual"
            assert "data/observacoes-2026-11.json" in page.locator("#bulletin").inner_text()
            page.locator("#timelineList button[data-date='atual']").click()
            assert "145" in page.locator("#kpi-exec").inner_text()
            page.locator("#openMethod").click()
            assert page.locator("#methodDrawer").is_visible()
            page.keyboard.press("Escape")
            assert not page.locator("#methodDrawer").is_visible()
            page.locator("#evidenceFilters button[data-service='estacas']").click()
            assert page.locator("#evidenceFilters button[data-service='estacas']").get_attribute("aria-pressed")=="true"
            page.locator("#copyView").click()
            assert "eixo=09" in page.url
            assert not errors, "JS errors: " + repr(errors)
            page.screenshot(path=str(OUT / f"{kind}-{screen}.png"), full_page=True, animations="disabled")
            results.append({"environment":kind,"viewport":screen,"kpis":True,"timeline":True,"xray":True,"deep_link":True,"webgl":True})
            page.close()
    browser.close()

(OUT/"test-report.json").write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(results,ensure_ascii=False,indent=2))
