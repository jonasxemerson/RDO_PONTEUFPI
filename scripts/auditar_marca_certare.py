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
