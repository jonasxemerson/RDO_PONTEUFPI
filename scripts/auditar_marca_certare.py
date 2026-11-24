#!/usr/bin/env python3
"""Investigação temporária: coletar candidatos a marca diretamente do site oficial."""
import re
import urllib.request
import html
for page in ["https://www.grupocertare.com/","https://www.grupocertare.com/quemsomos"]:
    try:
        req=urllib.request.Request(page,headers={"User-Agent":"Mozilla/5.0"})
        source=urllib.request.urlopen(req,timeout=14).read().decode("utf-8","ignore")
        print("SOURCE",page,"SIZE",len(source))
        chunks=list(re.finditer(r'\b(?:logo|logomarca|grupo certare|certare-engenharia|certare_engenharia)\b',source,re.I))
        for m in chunks[:24]:
            frag=source[max(0,m.start()-220):m.end()+500]
            urls=re.findall(r'https?:[^"<> ]+(?:png|webp|svg|jpe?g)',frag,re.I)
            print("CANDIDATE",m.group(0),html.unescape(frag[:500]).replace("\n"," ")[:500], urls[:2])
        # Site Wix: lista de IDs multimídia e textos de imagem contextualizados
        for match in re.finditer(r'(?i)(?:logo[^"<>]{0,140}|certare[^"<>]{0,130})(?:\.png|\.svg|\.webp)',source):
            print("IMAGE_TAG",html.unescape(source[match.start():match.end()])[:200])
    except Exception as exc:
        print("FETCH_ERROR",str(exc))

# Exportação controlada da logomarca do cabeçalho oficial.
import base64
logo="https://static.wixstatic.com/media/b0723a_f5fc2b4a40314e1eb2609467d5b54c57~mv2.png/v1/fill/w_720,h_200,al_c,q_95/Logo-grupo-Certare-em-cinza.png"
try:
    rq=urllib.request.Request(logo,headers={"User-Agent":"Mozilla/5.0","Accept":"image/png"})
    res=urllib.request.urlopen(rq,timeout=18)
    data=res.read()
    print("CERTARE_LOGO_CONTENT_TYPE",res.headers.get("Content-Type"),"SIZE",len(data))
    assert data[:8]==b"\\x89PNG\\r\\n\\x1a\\n", "não é PNG"
    print("CERTARE_LOGO_B64="+base64.b64encode(data).decode("ascii"))
except Exception as exc:
    print("CERTARE_LOGO_DOWNLOAD_ERROR",repr(exc))
