#!/usr/bin/env python3
"""Smoke test da prévia P04: Three.js real + dados homologados + UI progressiva."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright

BASE=Path(__file__).resolve().parent
HTML=BASE/"preview_pacote04_offline.html"
assert HTML.exists() and HTML.stat().st_size>700_000
source=HTML.read_text(encoding="utf-8")
assert '<script id="offline-data" type="application/json">' in source
assert 'THREE.Raycaster' in source and 'THREE.EdgesGeometry' in source
assert 'THREE.FogExp2' in source and 'THREE.WebGLRenderer' in source and '<canvas id="viewerCanvas"' in source  # fonte Three.js inclui utilitários SVG internos
assert '<script src=' not in source and '<link rel="stylesheet"' not in source
OUT=BASE/"capturas"
OUT.mkdir(exist_ok=True)
with sync_playwright() as pw:
 browser=pw.chromium.launch(headless=True,args=[
  "--no-sandbox","--enable-webgl","--use-gl=angle",
  "--use-angle=swiftshader","--enable-unsafe-swiftshader"
 ])
 report=[]
 for screen,viewport in (
  ("desktop",{"width":1440,"height":900}),
  ("mobile",{"width":390,"height":844}),
 ):
  page=browser.new_page(viewport=viewport,device_scale_factor=1)
  errors=[]
  requests=[]
  page.on("pageerror",lambda err: errors.append(str(err)))
  page.on("request",lambda r:requests.append(r.url))
  page.goto(HTML.as_uri(),wait_until="load")
  page.wait_for_function("() => document.querySelector('#kpi-exec').textContent.includes('145')",timeout=30000)
  assert "145 / 292" in page.locator("#kpi-exec").inner_text()
  assert "111 / 292" in page.locator("#kpi-concrete").inner_text()
  assert page.locator("#kpi-plan").inner_text()=="292"
  assert page.locator("#kpi-blocks").inner_text()=="2 / 9"
  assert page.locator("#kpi-pillars").inner_text()=="6 / 36"
  assert page.locator("#kpi-girders").inner_text()=="3 / 64"
  assert page.locator(".kpis .kpi:visible").count()==3
  assert page.locator("#viewerCanvas").is_visible()
  assert page.evaluate("() => typeof THREE !== 'undefined' && THREE.REVISION==='150' && !!document.querySelector('#viewerCanvas').getContext('webgl2')")
  assert page.locator("#chartRows .chart-row").count()==9
  assert "25 / 24" in page.locator("#chartRows .chart-row[data-axis='9']").inner_text()
  assert page.locator("#detailTabs").get_attribute("data-active")=="progress"
  assert not page.locator("#timeline").is_visible()
  assert not page.locator("#evidence").is_visible()
  assert page.locator("#axisDrawer").get_attribute("aria-hidden")=="true"
  assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 2"), "layout overflow at "+screen
  assert not any(r.startswith(("http://","https://")) for r in requests), requests
  # KPIs extras preserved, hidden by default.
  page.locator("#toggleKpis").click()
  assert page.locator(".kpis .kpi:visible").count()==6
  page.locator("#toggleKpis").click()
  assert page.locator(".kpis .kpi:visible").count()==3
  # Chart ↔ viewer and contextual panel.
  page.locator("#chartRows .chart-row[data-axis='9']").click()
  assert page.locator("#axisName").inner_text()=="E09"
  assert page.locator("#axisExecuted").inner_text()=="25"
  assert page.locator("#axisConcrete").inner_text()=="8"
  assert page.locator("#axisPlanned").inner_text()=="24"
  assert "indeterminadas" in page.locator("#axisCaveat").inner_text()
  assert page.locator("#axisDrawer").get_attribute("aria-hidden")=="false"
  page.locator("#closeAxisDrawer").click()
  assert page.locator("#axisDrawer").get_attribute("aria-hidden")=="true"
  page.locator("[data-viewer-mode='heatmap']").click()
  assert "Heatmap agregado" in page.locator("#scenePill").inner_text()
  page.locator("[data-viewer-system='fundacoes']").click()
  assert page.locator("[data-viewer-system='fundacoes']").get_attribute("aria-pressed")=="true"
  page.locator("#resetView").click()
  # Timeline old source-based, not interpolated.
  page.locator("[data-detail-tab='timeline']").click()
  assert page.locator("#timeline").is_visible()
  assert not page.locator("#progress").is_visible()
  assert page.locator("#timelineList button").count()==9
  page.locator("#timelineList button[data-date='2026-11-17']").click()
  assert page.locator("#kpi-exec").inner_text().endswith("*")
  assert "data/observacoes-2026-11.json" in page.locator("#bulletin").inner_text()
  page.locator("#timelineList button[data-date='atual']").click()
  assert "145" in page.locator("#kpi-exec").inner_text()
  # Evidence and filters preserved.
  page.locator("[data-detail-tab='evidence']").click()
  assert page.locator("#evidence").is_visible()
  page.locator("#evidenceFilters button[data-service='estacas']").click()
  assert page.locator("#evidenceFilters button[data-service='estacas']").get_attribute("aria-pressed")=="true"
  page.locator("#openMethod").click()
  assert page.locator("#methodDrawer").is_visible()
  page.keyboard.press("Escape")
  assert not page.locator("#methodDrawer").is_visible()
  assert not errors,errors
  page.screenshot(path=str(OUT/f"pacote04-{screen}.png"),full_page=True,animations="disabled")
  report.append({"screen":screen,"webgl":True,"data":True,"eixo09":True,"timeline":True,"evidence":True,"ui_compacta":True,"offline":True})
  page.close()
 browser.close()
(OUT/"resultado-testes.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(report,ensure_ascii=False,indent=2))
