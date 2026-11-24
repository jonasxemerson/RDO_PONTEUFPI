#!/usr/bin/env python3
"""Browser smoke test sem credencial real. Faz mock de toda a API GitHub."""
import io,json,os
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"capturas"
OUT.mkdir(exist_ok=True)
def image_jpeg():
    f=io.BytesIO();Image.new("RGB",(240,180),(211,227,218)).save(f,"JPEG");return f.getvalue()
def run():
    captures=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,args=["--no-sandbox","--disable-dev-shm-usage"])
        for label,w,h in (("desktop",1350,890),("celular",390,844)):
            page=browser.new_page(viewport={"width":w,"height":h},device_scale_factor=1)
            calls=[];errors=[]
            page.on("pageerror",lambda e:errors.append(str(e)))
            page.on("dialog",lambda d:d.accept())
            def route(r):
                q=r.request
                if q.method=="OPTIONS":
                    r.fulfill(status=204,headers={"access-control-allow-origin":"*","access-control-allow-headers":"*","access-control-allow-methods":"GET,POST,PATCH,OPTIONS"});return
                key=q.url.split("https://api.github.com")[-1]
                body=q.post_data_json if q.post_data and "application/json" in q.headers.get("content-type","") else None
                calls.append((q.method,key,body))
                if key=="/user":v={"login":"jonasxemerson"}
                elif key=="/repos/jonasxemerson/RDO_CERTARE":v={"private":True,"full_name":"jonasxemerson/RDO_CERTARE","permissions":{"admin":True}}
                elif key.endswith("/git/ref/heads/main"):v={"object":{"sha":"c"*40}}
                elif "/git/commits/" in key and q.method=="GET":v={"tree":{"sha":"d"*40}}
                elif key.endswith("/git/blobs"):v={"sha":str(len(calls)).zfill(40)}
                elif key.endswith("/git/trees"):v={"sha":"a"*40}
                elif key.endswith("/git/commits"):v={"sha":"b"*40}
                elif key.endswith("/git/refs"):v={"ref":"refs/heads/rdo/sample"}
                elif key.endswith("/pulls"):v={"number":51,"html_url":"https://github.com/jonasxemerson/RDO_CERTARE/pull/51"}
                else:r.fulfill(status=404,body="{}");return
                r.fulfill(status=200 if q.method=="GET" else 201,content_type="application/json",
                          headers={"access-control-allow-origin":"*","access-control-allow-headers":"*"},body=json.dumps(v))
            page.route("https://api.github.com/**",route)
            page.goto((ROOT/"admin-rdo/index.html").as_uri(),wait_until="load")
            assert page.locator("#authGate").is_visible()
            assert not page.locator("#workspace").is_visible()
            page.screenshot(path=str(OUT/f"{label}-login.png"),full_page=True)
            page.locator("#githubToken").fill("mocked-token-never-real")
            page.locator("#connectBtn").click()
            page.locator("#workspace").wait_for(state="visible")
            assert page.locator("#githubToken").input_value()==""
            page.locator("#rdoDate").fill("2026-11-24")
            page.locator('[data-tab="frentes"]').click()
            page.locator("#frontAxis").select_option("E09")
            page.locator("#frontService").select_option("estacas")
            page.locator("#frontState").select_option("snapshot")
            page.locator("#frontQty").fill("25")
            page.locator("#frontQtyKind").select_option("total_reportado")
            page.locator("#frontActivity").fill("25 estacas relatadas como executadas")
            page.locator('#frontForm button[type="submit"]').click()
            assert page.locator("#frontList .front-card").count()==1
            page.locator('[data-tab="fotos"]').click()
            page.locator("#pickPhotos").set_input_files({"name":"teste.jpg","mimeType":"image/jpeg","buffer":image_jpeg()})
            page.locator(".photo-card").first.wait_for(state="visible")
            page.locator('[data-field="caption"]').fill("Frente E09 — imagem demonstrativa")
            page.locator('[data-field="front_ref"]').select_option(index=1)
            page.locator('[data-tab="revisao"]').click()
            page.screenshot(path=str(OUT/f"{label}-revisao.png"),full_page=True)
            page.locator("#confirmSubmit").check()
            page.locator("#submitGithub").click()
            page.locator("#submittedResult").wait_for(state="visible",timeout=20000)
            blobs=[x[2] for x in calls if x[1].endswith("/git/blobs")]
            assert len(blobs)==2
            content=json.loads(next(b["content"] for b in blobs if b["encoding"]=="utf-8"))
            assert content["records"][0]["quantity"]==25
            assert content["records"][0]["quantity_kind"]=="total_reportado"
            assert content["records"][0]["validation"]=="proposto_revisao"
            assert content["records"][0]["status_tech"]=="nao_avaliado"
            assert content["photos"][0]["record_ref"]==content["records"][0]["id"]
            assert content["photos"][0]["sha256"] is not None
            prs=[x[2] for x in calls if x[1].endswith("/pulls")]
            assert len(prs)==1 and prs[0]["draft"] is True
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 2")
            assert not errors,errors
            captures.append({"tela":label,"autenticacao":True,"RDO":True,"fotos":True,"PR":True})
            page.close()
        # Autorização negada sem admin.
        page=browser.new_page()
        def denied(r):
            if r.request.url.endswith("/user"):r.fulfill(status=200,content_type="application/json",headers={"access-control-allow-origin":"*"},body='{"login":"usuario_sem_acesso"}')
            else:r.fulfill(status=404,body="{}")
        page.route("https://api.github.com/**",denied)
        page.goto((ROOT/"admin-rdo/index.html").as_uri())
        page.locator("#githubToken").fill("sem-acesso")
        page.locator("#connectBtn").click()
        page.wait_for_function("() => document.querySelector(\"#authFeedback\").textContent.includes(\"não é o administrador\")",timeout=10000)
        assert "não é o administrador" in page.locator("#authFeedback").inner_text()
        assert not page.locator("#workspace").is_visible()
        browser.close()
    print(json.dumps(captures,ensure_ascii=False))
if __name__=="__main__":run()
