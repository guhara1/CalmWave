#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
간다GO — static site generator.
- Injects shared partials (footer, regional header) into ALL html files.
- Generates data-driven interior pages (hubs, 9 areas, check/policy, about).
- Emits sitemap.xml.
Run:  python3 build/generate.py
"""
import os, re, html, datetime, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://gandago.co.kr"
TEL = "0508-202-4719"
TG = "https://t.me/ganda_go"  # ⚠️ 임시 텔레그램 핸들 — 실제 계정으로 교체

def read(p):
    with open(os.path.join(ROOT, p), encoding="utf-8") as f:
        return f.read()

def write(p, s):
    full = os.path.join(ROOT, p)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(s)

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from admin_data import CITIES, STATIONS

FOOTER = read("partials/footer.html")
RHEADER = None  # built from CITIES below, before any page is emitted

def inject(s):
    return (s.replace("<!--#FOOTER#-->", FOOTER)
             .replace("<!--#RHEADER#-->", RHEADER))

# ---------------------------------------------------------------------------
# Shared HTML helpers
# ---------------------------------------------------------------------------
def head(title, desc, url, og_img="og-region.svg", jsonld="", robots="index,follow,max-image-preview:large"):
    assert len(desc) <= 80, f"description too long ({len(desc)}): {desc}"
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(desc)}" />
  <link rel="canonical" href="{url}" />
  <meta name="robots" content="{robots}" />
  <meta property="og:type" content="article" />
  <meta property="og:site_name" content="간다GO" />
  <meta property="og:title" content="{html.escape(title)}" />
  <meta property="og:description" content="{html.escape(desc)}" />
  <meta property="og:url" content="{url}" />
  <meta property="og:image" content="{SITE}/assets/{og_img}" />
  <meta name="twitter:card" content="summary_large_image" />
  <link rel="preload" href="/assets/hero.webp" as="image" />
  <link rel="stylesheet" href="/css/tokens.css" />
  <link rel="stylesheet" href="/css/base.css" />
  <link rel="stylesheet" href="/css/components.css" />
  {jsonld}
</head>
<body>
  <a class="skip-link" href="#main">본문 바로가기</a>
  <!--#RHEADER#-->"""

HERO_IMG = "/assets/hero.webp"

def page_hero(eyebrow, h1):
    return f"""
  <section class="section page-hero" style="--hero-image:url('{HERO_IMG}');padding-block:clamp(2.2rem,5vw,3.6rem)">
    <div class="container">
      <span class="eyebrow">{html.escape(eyebrow)}</span>
      <h1>{html.escape(h1)}</h1>
    </div>
  </section>"""

# ---------------------------------------------------------------------------
# Regional header with 행정구 dropdown mega-menu (built from CITIES)
# 클릭(details) 시 행정구 버튼들이 펼쳐집니다 — JS 불필요, 모바일 호환.
# ---------------------------------------------------------------------------
def _mega(city_key):
    c = CITIES[city_key]
    btns = f'<a class="mega-all" href="{c["hub"]}">{c["name"]}권 전체 보기 →</a>'
    for d in c["districts"]:
        btns += f'<a href="/incheon-bucheon-siheung/{city_key}/{d["slug"]}/">{html.escape(d["name"])}</a>'
    return (f'<details class="nav-mega"><summary>{c["name"]}권</summary>'
            f'<div class="mega">{btns}</div></details>')

def build_rheader():
    return f"""  <header class="site-header">
    <div class="container">
      <a class="brand" href="/">간다<b>GO</b> <span>지역 안내</span></a>
      <button class="nav-toggle" aria-expanded="false" aria-controls="primary-nav" aria-label="메뉴 열기">☰</button>
      <nav class="nav" id="primary-nav" aria-label="지역 안내 메뉴">
        <a href="/incheon-bucheon-siheung/">홈</a>
        {_mega('incheon')}
        {_mega('bucheon')}
        {_mega('siheung')}
        <a href="/incheon-bucheon-siheung/#areas">생활권</a>
        <a href="/incheon-bucheon-siheung/subway/">지하철</a>
        <a href="/incheon-bucheon-siheung/check/address.html">예약 전 확인</a>
        <a class="btn btn--accent nav-cta" href="tel:0508-202-4719">전화예약 0508-202-4719</a>
      </nav>
    </div>
  </header>"""

RHEADER = build_rheader()
write("partials/rheader.html", RHEADER + "\n")

def breadcrumb_html(trail):
    lis = "".join(
        f'<li><a href="{u}">{html.escape(n)}</a></li>' if u else f"<li>{html.escape(n)}</li>"
        for n, u in trail)
    return f'<div class="container"><nav class="breadcrumb" aria-label="위치"><ol>{lis}</ol></nav></div>'

def breadcrumb_ld(trail):
    items = []
    for i, (n, u) in enumerate(trail, 1):
        url = (SITE + u) if u else (SITE + "/")
        items.append({"@type":"ListItem","position":i,"name":n,"item":url})
    return J({"@type":"BreadcrumbList","itemListElement":items})

def J(x):
    return json.dumps(x, ensure_ascii=False)

def faq_ld(faqs):
    entities = [{"@type":"Question","name":q,
                 "acceptedAnswer":{"@type":"Answer","text":re.sub("<[^>]+>","",a)}}
                for q, a in faqs]
    return J({"@type":"FAQPage","mainEntity":entities})

def webpage_ld(url, name, img="og-region.svg"):
    return J({"@type":"WebPage","url":url,"name":name,"inLanguage":"ko-KR",
              "isPartOf":{"@id":SITE+"/#website"},"about":{"@id":SITE+"/#org"},
              "primaryImageOfPage":f"{SITE}/assets/{img}"})

def jsonld(*nodes):
    return ('<script type="application/ld+json">{"@context":"https://schema.org","@graph":['
            + ",".join(nodes) + "]}</script>")

def faq_html(faqs, open_first=True):
    out = ['<div class="faq">']
    for i, (q, a) in enumerate(faqs):
        op = " open" if (open_first and i == 0) else ""
        out.append(f"<details{op}><summary>{html.escape(q)}</summary><p>{a}</p></details>")
    out.append("</div>")
    return "\n".join(out)

def whw_html(who, how, why):
    return f"""<div class="grid whw">
      <article class="card"><h3>누가</h3><p>{who}</p></article>
      <article class="card"><h3>어떻게</h3><p>{how}</p></article>
      <article class="card"><h3>왜</h3><p>{why}</p></article>
    </div>"""

CHECKLIST = """<ul class="checklist">
  <li>정확한 방문 주소와 상세 호실·동을 확인합니다.</li>
  <li>아파트·오피스텔 공동현관 출입 방식을 확인합니다.</li>
  <li>호텔·숙소의 객실 출입·방문 정책을 확인합니다.</li>
  <li>예약 가능 시간과 야간 출입 가능 여부를 확인합니다.</li>
  <li>공항·항만·산단 인접 지역은 이동 시간과 주차를 확인합니다.</li>
</ul>"""

NOTICE = """<div class="notice notice--danger">간다GO는 불법·선정적 서비스를 제공하거나 안내하지 않습니다.
  건전한 방문 케어만 안내하며, 개인정보는 예약 확인과 연락에 필요한 최소 정보만 처리합니다.
  <a href="/incheon-bucheon-siheung/check/service-policy.html">서비스 불가 안내</a> ·
  <a href="/incheon-bucheon-siheung/check/privacy.html">개인정보 처리방침</a></div>"""

FOOT = """  <!--#FOOTER#-->
  <script src="/js/main.js" defer></script>
</body>
</html>"""

# collect urls for sitemap
URLS = ["/", "/incheon-bucheon-siheung/"]

def emit(path, url, htmlstr):
    write(path, inject(htmlstr))
    URLS.append(url)

# ---------------------------------------------------------------------------
# HUB pages (인천 / 부천 / 시흥)
# ---------------------------------------------------------------------------
HUBS = {
"incheon": {
  "path": "incheon-bucheon-siheung/incheon/index.html",
  "url": "/incheon-bucheon-siheung/incheon/",
  "title": "인천 출장마사지｜송도·부평·구월·영종 생활권 안내 — 간다GO",
  "desc": "인천 출장마사지·홈타이. 송도·부평·구월·청라·검단·영종 생활권 이용 기준 안내.",
  "h1": "인천 출장마사지 · 송도·부평·구월·영종 생활권 안내",
  "lead": ("인천은 송도국제도시·연수·구월·부평·계양·청라·검단·영종·제물포처럼 생활권 차이가 큰 도시입니다. "
           "2026년 7월 행정체제 개편으로 제물포구·영종구·서해구·검단구가 새로 정리되었고, 기존 서구·중구·동구 검색 수요도 함께 "
           "고려해 안내합니다. 호텔·레지던스가 밀집한 송도 국제업무지구, 환승 상권인 부평역·부평시장, 인천시청 중심의 구월, "
           "공항·장기숙소 중심의 영종은 이용 기준이 서로 다르므로 방문 장소를 먼저 확인하는 것이 좋습니다."),
  "regions": [
    ("송도국제도시", "국제업무지구·호텔·레지던스·오피스텔 중심. 객실 출입과 예약 시간을 함께 확인합니다.", "/incheon-bucheon-siheung/area/songdo-yeonsu-nonhyeon.html"),
    ("연수·동춘", "주거지·역세권 중심 생활권. 아파트 공동현관 출입 방식을 확인합니다.", "/incheon-bucheon-siheung/area/songdo-yeonsu-nonhyeon.html"),
    ("구월·인천시청", "인천 내륙 핵심 상권·업무지구. 오피스텔·상권 숙소 기준을 확인합니다.", "/incheon-bucheon-siheung/area/guwol-namdong-bupyeong.html"),
    ("부평역·부평시장", "환승역·상권·숙소 밀집권. 야간 출입과 예약 가능 시간을 확인합니다.", "/incheon-bucheon-siheung/area/guwol-namdong-bupyeong.html"),
    ("청라·루원", "신도시·상권·오피스텔 중심. 서울 서북부 이동 기준을 확인합니다.", "/incheon-bucheon-siheung/area/cheongna-seohae-geomdan.html"),
    ("검단신도시", "아파트 단지·신도시 생활권. 외곽 이동 기준을 확인합니다.", "/incheon-bucheon-siheung/area/cheongna-seohae-geomdan.html"),
    ("영종·운서", "공항·호텔·장기숙소 중심. 이동 시간·주차·출입 방식을 확인합니다.", "/incheon-bucheon-siheung/area/yeongjong-airport-jemulpo.html"),
    ("제물포·동인천", "원도심·항만·관광 숙소 중심. 숙소 방문 정책을 확인합니다.", "/incheon-bucheon-siheung/area/yeongjong-airport-jemulpo.html"),
  ],
  "faqs": [
    ("인천 어느 생활권까지 안내되나요?", "송도·연수·구월·부평·계양·청라·검단·영종·제물포 등 주요 생활권을 안내하며, 강화·옹진 도서 지역은 이동 기준 확인 후 안내합니다."),
    ("인천공항 근처 숙소도 확인할 수 있나요?", "영종·운서·공항신도시·인천공항 인접 숙소는 이동 시간, 주차, 예약 가능 시간, 숙소 출입 방식을 함께 확인해야 합니다."),
    ("송도 호텔·오피스텔에서도 이용할 수 있나요?", "숙소 정책, 객실 출입 가능 여부, 공동현관, 엘리베이터, 관리 규정을 먼저 확인해야 합니다."),
  ],
  "whw": ("간다GO 예약 안내 담당이 인천 생활권 자료를 바탕으로 작성·검수합니다.",
          "행정체제 개편과 송도·부평·영종 등 생활권 차이를 반영해 지역별로 다르게 작성합니다.",
          "인천 이용자가 자기 위치와 숙소 유형을 정확히 확인하고 안심하고 예약하도록 돕기 위함입니다."),
},
"bucheon": {
  "path": "incheon-bucheon-siheung/bucheon/index.html",
  "url": "/incheon-bucheon-siheung/bucheon/",
  "title": "부천 출장마사지｜중동·상동·송내 생활권 안내 — 간다GO",
  "desc": "부천 출장마사지·홈타이. 중동·상동·송내·역곡·옥길 생활권 이용 기준 안내.",
  "h1": "부천 출장마사지 · 중동·상동·송내 생활권 안내",
  "lead": ("부천은 서울과 인천 사이의 고밀도 생활권으로, 원미구·소사구·오정구 세 개 구로 나뉩니다. "
           "중동·신중동·상동은 부천 핵심 상권과 오피스텔이 밀집해 있고, 송내·역곡·소사는 지하철 환승과 서울 구로·광명 연결이 "
           "좋은 주거형 생활권입니다. 옥길은 신도시형, 원종·고강·오정은 김포공항·강서·계양과 이어지는 북부 생활권입니다. "
           "구별로만 찾기보다 실제 이용 생활권까지 함께 확인하는 것이 예약에 편리합니다."),
  "regions": [
    ("원미구 (중동·상동·심곡)", "부천 중심 상권·부천시청·오피스텔 밀집권. 상동역·부천역 접근성이 좋습니다.", "/incheon-bucheon-siheung/area/bucheon-jungdong-sangdong-songnae.html"),
    ("소사구 (소사·송내·역곡)", "서울 구로·광명·시흥 연결 주거형 생활권. 옥길신도시·소사역·송내역 중심입니다.", "/incheon-bucheon-siheung/area/yeokgok-sosa-okgil.html"),
    ("오정구 (원종·고강·오정)", "김포공항·서울 서남권·인천 계양 연결권. 야간 출입 확인이 중요합니다.", "/incheon-bucheon-siheung/area/wonjong-gogang-ojeong.html"),
  ],
  "faqs": [
    ("부천은 구별로 찾는 것이 좋나요?", "원미구·소사구·오정구를 기준으로 보되, 실제 이용은 중동·상동·송내·역곡·옥길 같은 생활권까지 함께 확인하는 것이 좋습니다."),
    ("상동·중동 오피스텔에서도 이용할 수 있나요?", "오피스텔 관리 규정, 공동현관, 객실 출입 가능 여부를 먼저 확인해야 합니다."),
    ("역곡·소사에서 서울 방향 이동도 되나요?", "역곡·소사·옥길은 서울 구로·광명과 가까워 이동이 수월하며, 정확한 주소와 예약 시간을 확인해 안내합니다."),
  ],
  "whw": ("간다GO 예약 안내 담당이 부천 생활권 자료를 바탕으로 작성·검수합니다.",
          "원미·소사·오정 3구와 중동·상동·역곡·옥길 생활권 차이를 반영해 작성합니다.",
          "부천 이용자가 상권·주거·환승 조건에 맞춰 정확히 확인하고 예약하도록 돕기 위함입니다."),
},
"siheung": {
  "path": "incheon-bucheon-siheung/siheung/index.html",
  "url": "/incheon-bucheon-siheung/siheung/",
  "title": "시흥 출장마사지｜배곧·정왕·은계 생활권 안내 — 간다GO",
  "desc": "시흥 출장마사지·홈타이. 배곧·정왕·오이도·은계·장현 생활권 이용 기준 안내.",
  "h1": "시흥 출장마사지 · 배곧·정왕·은계 생활권 안내",
  "lead": ("시흥은 신도시·산업단지·해안 생활권·주거지가 섞인 도시입니다. 서부는 배곧신도시·정왕·오이도·월곶·거북섬으로 "
           "이어지는 핵심 생활권이고, 동부는 은계·대야·장현·목감처럼 부천·광명·안산과 연결되는 주거형 권역입니다. "
           "배곧은 신도시·오피스텔·해안 숙소 중심, 정왕은 시화산단과 주거지, 오이도·월곶은 해안 상권 숙소 중심으로 "
           "이용 기준이 다르므로 방문 장소를 먼저 확인하는 것이 좋습니다."),
  "regions": [
    ("배곧신도시", "신도시·오피스텔·해안 숙소 중심. 공동현관·객실 출입 방식을 확인합니다.", "/incheon-bucheon-siheung/area/baegot-jeongwang-oido.html"),
    ("정왕·시화산단", "시화산단·주거지 생활권. 산단 인접 숙소는 주차·야간 출입을 확인합니다.", "/incheon-bucheon-siheung/area/baegot-jeongwang-oido.html"),
    ("오이도·월곶", "해안 상권·숙소 중심. 이동 시간과 예약 가능 시간을 확인합니다.", "/incheon-bucheon-siheung/area/baegot-jeongwang-oido.html"),
    ("은계·대야·장현", "부천·광명·안산 연결 주거형 권역. 아파트 공동현관을 확인합니다.", "/incheon-bucheon-siheung/area/eungye-janghyeon-mokgam.html"),
    ("목감·능곡", "외곽 이동 기준과 건물 출입 방식을 함께 확인하는 주거 생활권.", "/incheon-bucheon-siheung/area/eungye-janghyeon-mokgam.html"),
  ],
  "faqs": [
    ("시흥 배곧과 정왕은 기준이 다른가요?", "배곧은 신도시·오피스텔·해안 숙소 중심이고, 정왕은 시화산단·주거지·오이도 인접권을 함께 확인해야 합니다."),
    ("시화산단 인근 숙소도 가능한가요?", "시화산단·시화MTV 인접 지역은 정확한 주소, 주차 가능 여부, 야간 출입 가능 여부를 먼저 확인해야 합니다."),
    ("오이도·월곶 해안 숙소도 안내되나요?", "해안 상권 숙소는 이동 시간과 예약 가능 시간을 함께 확인해 안내합니다."),
  ],
  "whw": ("간다GO 예약 안내 담당이 시흥 생활권 자료를 바탕으로 작성·검수합니다.",
          "배곧·정왕·오이도 서부권과 은계·장현·목감 동부권의 차이를 반영해 작성합니다.",
          "시흥 이용자가 신도시·산단·해안 조건에 맞춰 정확히 확인하고 예약하도록 돕기 위함입니다."),
},
}

def render_hub(key, d):
    trail = [("간다GO", "/"), ("인천·부천·시흥", "/incheon-bucheon-siheung/"),
             (d["h1"].split(" · ")[0], d["url"])]
    ld = jsonld(webpage_ld(SITE+d["url"], d["title"].split("｜")[0]),
                breadcrumb_ld(trail), faq_ld(d["faqs"]))
    cards = "\n".join(
        f'<a class="card card--link" href="{u}"><h3>{html.escape(n)}</h3><p>{html.escape(desc)}</p></a>'
        for n, desc, u in d["regions"])
    s = head(d["title"], d["desc"], SITE+d["url"], jsonld=ld)
    s += breadcrumb_html(trail)
    city = CITIES[key]
    dist_btns = "".join(
        f'<a href="/incheon-bucheon-siheung/{key}/{dd["slug"]}/">{html.escape(dd["name"])}</a>'
        for dd in city["districts"])
    s += f"""
  <main id="main">
    {page_hero("인천·부천·시흥 지역 안내", d["h1"])}
    <section class="section">
      <div class="container">
        <div class="prose"><p class="lede">{d["lead"]}</p>
          <p>예약 전에는 <a href="/incheon-bucheon-siheung/check/address.html">방문 주소</a>,
            <a href="/incheon-bucheon-siheung/check/building-access.html">건물 출입 방식</a>,
            <a href="/incheon-bucheon-siheung/check/time.html">예약 가능 시간</a>,
            <a href="/incheon-bucheon-siheung/check/travel-fee.html">외곽 이동비 기준</a>을 함께 확인하세요.</p></div>
      </div>
    </section>
    <section class="section" style="padding-top:0;">
      <div class="container">
        <div class="section-head"><h2>{city["name"]} {city["mid_label"]} 바로가기</h2>
          <p>{city["mid_label"]}를 선택하면 행정동 안내로 이동합니다.</p></div>
        <div class="related">{dist_btns}</div>
      </div>
    </section>
    <section class="section" style="padding-top:0;">
      <div class="container">
        <div class="section-head"><h2>대표 생활권</h2></div>
        <div class="grid cards-3">{cards}</div>
      </div>
    </section>
    <section class="section" style="padding-top:0;">
      <div class="container narrow">
        <div class="card"><h2>예약 전 체크리스트</h2>{CHECKLIST}
          <p class="muted">자세한 항목은 <a href="/incheon-bucheon-siheung/check/address.html">예약 전 확인</a>에서 이어집니다.</p></div>
      </div>
    </section>
    <section class="section" style="padding-top:0;">
      <div class="container"><div class="section-head"><h2>Who · How · Why</h2></div>{whw_html(*d["whw"])}</div>
    </section>
    <section class="section" style="padding-top:0;"><div class="container narrow">{NOTICE}</div></section>
    <section class="section" style="padding-top:0;">
      <div class="container narrow"><div class="section-head"><h2>자주 묻는 질문</h2></div>{faq_html(d["faqs"])}</div>
    </section>
    <section class="section" style="padding-top:0;">
      <div class="container narrow"><div class="section-head"><h2>관련 지역 보기</h2></div>
        <div class="related">
          <a href="/incheon-bucheon-siheung/incheon/">인천권 안내</a>
          <a href="/incheon-bucheon-siheung/bucheon/">부천권 안내</a>
          <a href="/incheon-bucheon-siheung/siheung/">시흥권 안내</a>
          <a href="/incheon-bucheon-siheung/">서부 수도권 전체</a>
        </div></div>
    </section>
  </main>
{FOOT}"""
    emit(d["path"], d["url"], s)

for k, d in HUBS.items():
    render_hub(k, d)

# ---------------------------------------------------------------------------
# 9 AREA pages
# ---------------------------------------------------------------------------
AREAS = [
 {"slug":"songdo-yeonsu-nonhyeon","name":"송도·연수·논현권",
  "title":"송도·연수·논현 출장마사지｜국제업무지구·호텔 이용 안내 — 간다GO",
  "desc":"송도·연수·논현 출장마사지·홈타이. 국제업무지구 호텔·오피스텔 이용 기준 안내.",
  "h1":"송도·연수·논현권 · 국제업무지구·해안 생활권 안내",
  "incs":"송도, 연수, 동춘, 청학, 인천논현, 소래포구, 남동산단 인접권",
  "body":["송도는 국제업무지구를 중심으로 호텔·레지던스·오피스텔이 밀집한 생활권입니다. 객실 출입 정책, 공동현관, 엘리베이터 카드키, 예약 가능 시간을 먼저 확인하면 방문이 매끄럽습니다.",
          "연수·동춘은 주거지와 역세권이 섞인 생활권으로 아파트 공동현관 출입 방식 확인이 중요합니다. 논현·소래포구는 해안 상권과 남동산단 인접 숙소가 많아 이동 시간과 주차 여부를 함께 확인합니다."],
  "hub":("인천","/incheon-bucheon-siheung/incheon/")},
 {"slug":"guwol-namdong-bupyeong","name":"구월·남동·부평권",
  "title":"구월·남동·부평 출장마사지｜인천시청·부평역 생활권 안내 — 간다GO",
  "desc":"구월·남동·부평 출장마사지·홈타이. 인천시청·부평역 상권 숙소 이용 기준 안내.",
  "h1":"구월·남동·부평권 · 인천 내륙 핵심 상권 안내",
  "incs":"구월동, 간석동, 만수동, 부평역, 부평시장, 삼산, 부개, 청천",
  "body":["구월은 인천시청과 상권이 밀집한 인천 내륙 핵심 생활권입니다. 오피스텔·상권 숙소가 많아 정확한 호실과 공동현관 출입 방식을 확인합니다.",
          "부평역·부평시장은 환승역 상권으로 숙소가 밀집해 있고 야간 이용 문의가 많은 편입니다. 예약 가능 시간과 야간 출입 가능 여부를 먼저 확인합니다. 남동은 주거지와 남동산단 이동이 함께 있어 이동 기준을 확인합니다."],
  "hub":("인천","/incheon-bucheon-siheung/incheon/")},
 {"slug":"cheongna-seohae-geomdan","name":"청라·서해·검단권",
  "title":"청라·검단 출장마사지｜신도시·오피스텔 이용 안내 — 간다GO",
  "desc":"청라·서해·검단 출장마사지·홈타이. 신도시·오피스텔·아파트 이용 기준 안내.",
  "h1":"청라·서해·검단권 · 신도시 생활권 안내",
  "incs":"청라, 가정, 루원, 석남, 가좌, 검단, 원당, 당하, 마전",
  "body":["청라·루원은 신도시 상권과 오피스텔이 발달한 생활권입니다. 오피스텔 관리 규정과 공동현관 출입 방식을 확인하면 방문이 편리합니다.",
          "검단신도시는 아파트 단지가 넓고 서울 서북부 이동이 잦은 지역으로, 정확한 동·호수와 외곽 이동 기준을 확인합니다. 서해구 생활권은 기존 서구 검색 수요를 함께 고려해 안내합니다."],
  "hub":("인천","/incheon-bucheon-siheung/incheon/")},
 {"slug":"yeongjong-airport-jemulpo","name":"영종·공항·제물포권",
  "title":"영종·인천공항 출장마사지｜공항 숙소·원도심 이용 안내 — 간다GO",
  "desc":"영종·공항·제물포 출장마사지·홈타이. 공항 인접 숙소·원도심 이용 기준 안내.",
  "h1":"영종·공항·제물포권 · 공항·항만 생활권 안내",
  "incs":"영종, 운서, 공항신도시, 인천공항, 제물포, 동인천, 인천역, 월미도, 인천항",
  "body":["영종은 인천공항과 공항신도시를 중심으로 호텔·장기숙소가 많은 생활권입니다. 이동 시간, 주차, 예약 가능 시간, 숙소 출입 방식을 함께 확인해야 방문 예약이 정확합니다.",
          "제물포·동인천은 원도심과 항만·관광 숙소가 섞여 있습니다. 숙소 방문 정책과 건물 출입 방식을 확인하고, 공항·섬 권역은 예약 시간과 이동 기준을 명확히 안내합니다."],
  "hub":("인천","/incheon-bucheon-siheung/incheon/")},
 {"slug":"bucheon-jungdong-sangdong-songnae","name":"부천 중동·상동·송내권",
  "title":"부천 중동·상동 출장마사지｜핵심 상권·오피스텔 안내 — 간다GO",
  "desc":"부천 중동·상동·송내 출장마사지·홈타이. 핵심 상권 오피스텔 이용 기준 안내.",
  "h1":"부천 중동·상동·송내권 · 핵심 상권 생활권 안내",
  "incs":"중동, 신중동, 상동, 송내, 부천시청, 부천종합터미널",
  "body":["중동·신중동·상동은 부천 핵심 상권과 오피스텔·주거가 밀집한 생활권입니다. 지하철 7호선과 상동·중동 상권, 부천시청 접근성이 좋아 예약이 수월합니다. 오피스텔은 관리 규정과 공동현관 출입 방식을 확인합니다.",
          "송내는 1호선·경인선 환승성이 좋아 서울과 인천 사이 이동이 편리합니다. 정확한 방문 주소와 예약 가능 시간을 확인해 안내합니다."],
  "hub":("부천","/incheon-bucheon-siheung/bucheon/")},
 {"slug":"yeokgok-sosa-okgil","name":"부천 역곡·소사·옥길권",
  "title":"부천 역곡·소사·옥길 출장마사지｜주거 생활권 안내 — 간다GO",
  "desc":"부천 역곡·소사·옥길 출장마사지·홈타이. 역세권·신도시 주거 이용 기준 안내.",
  "h1":"부천 역곡·소사·옥길권 · 서울 연결 주거 생활권 안내",
  "incs":"역곡, 소사, 괴안, 범박, 옥길, 송내 남부 생활권",
  "body":["역곡·소사는 서울 구로·광명과 가까운 역세권 주거 생활권입니다. 아파트·빌라가 많아 공동현관 출입 방식과 정확한 동·호수를 확인합니다.",
          "옥길은 신도시형 아파트 단지가 넓은 지역으로 외곽 이동 기준을 확인하면 좋습니다. 범박·괴안은 주거지형 생활권으로 야간 예약 시 출입 방식을 함께 확인합니다."],
  "hub":("부천","/incheon-bucheon-siheung/bucheon/")},
 {"slug":"wonjong-gogang-ojeong","name":"부천 원종·고강·오정권",
  "title":"부천 원종·고강·오정 출장마사지｜북부 생활권 안내 — 간다GO",
  "desc":"부천 원종·고강·오정 출장마사지·홈타이. 김포공항·강서 연결 생활권 안내.",
  "h1":"부천 원종·고강·오정권 · 북부 연결 생활권 안내",
  "incs":"원종, 고강, 오정, 성곡, 신흥",
  "body":["원종·고강·오정은 김포공항·서울 강서·인천 계양과 이어지는 부천 북부 생활권입니다. 주거지와 소규모 산업권이 섞여 있어 정확한 주소와 외곽 이동 기준을 확인합니다.",
          "야간 예약이 있을 경우 건물 출입 방식과 공동현관 확인이 중요합니다. 성곡·신흥 산업권 인접 숙소는 주차와 야간 출입 가능 여부를 먼저 확인합니다."],
  "hub":("부천","/incheon-bucheon-siheung/bucheon/")},
 {"slug":"baegot-jeongwang-oido","name":"시흥 배곧·정왕·오이도권",
  "title":"시흥 배곧·정왕 출장마사지｜신도시·시화산단 안내 — 간다GO",
  "desc":"시흥 배곧·정왕·오이도 출장마사지·홈타이. 신도시·산단·해안 이용 기준 안내.",
  "h1":"시흥 배곧·정왕·오이도권 · 서부 핵심 생활권 안내",
  "incs":"배곧, 정왕, 오이도, 월곶, 거북섬, 시화산단",
  "body":["배곧신도시는 오피스텔·해안 숙소가 많은 시흥 서부 핵심 생활권입니다. 공동현관·객실 출입 방식과 예약 가능 시간을 확인하면 방문이 편리합니다.",
          "정왕은 시화산단과 주거지가 함께 있어 산단 인접 숙소의 주차·야간 출입을 확인합니다. 오이도·월곶·거북섬은 해안 상권 숙소 중심으로 이동 시간을 함께 확인해 안내합니다."],
  "hub":("시흥","/incheon-bucheon-siheung/siheung/")},
 {"slug":"eungye-janghyeon-mokgam","name":"시흥 은계·장현·목감권",
  "title":"시흥 은계·장현·목감 출장마사지｜동부 주거 생활권 안내 — 간다GO",
  "desc":"시흥 은계·장현·목감 출장마사지·홈타이. 부천·광명·안산 연결 이용 기준 안내.",
  "h1":"시흥 은계·장현·목감권 · 동부 주거 생활권 안내",
  "incs":"은계, 대야, 신천, 장현, 장곡, 능곡, 목감, 시흥시청",
  "body":["은계·대야·장현은 아파트 단지와 신도시가 발달한 시흥 동부 주거 생활권으로, 부천·광명·안산과 연결됩니다. 아파트 공동현관 출입 방식과 정확한 동·호수를 확인합니다.",
          "목감·능곡은 외곽 이동 기준과 건물 출입 방식을 함께 확인하는 것이 좋습니다. 시흥시청 인접 생활권은 예약 가능 시간을 확인해 안내합니다."],
  "hub":("시흥","/incheon-bucheon-siheung/siheung/")},
]

AREA_FAQ = [
 ("이 생활권 전 지역 방문이 가능한가요?", "정확한 방문 주소, 가까운 역·생활권, 예약 가능 시간, 이동 기준을 확인한 뒤 안내합니다."),
 ("호텔이나 오피스텔에서도 이용할 수 있나요?", "숙소 정책, 객실 출입 가능 여부, 공동현관, 엘리베이터, 관리 규정을 먼저 확인해야 합니다."),
 ("불법·선정적 서비스도 가능한가요?", "불법·선정적 서비스는 제공하거나 안내하지 않습니다."),
]

def render_area(a):
    url = f"/incheon-bucheon-siheung/area/{a['slug']}.html"
    trail = [("간다GO","/"),("인천·부천·시흥","/incheon-bucheon-siheung/"),
             (a["hub"][0], a["hub"][1]),(a["name"], url)]
    ld = jsonld(webpage_ld(SITE+url, a["title"].split("｜")[0]),
                breadcrumb_ld(trail), faq_ld(AREA_FAQ))
    body = "\n".join(f"<p>{p}</p>" for p in a["body"])
    s = head(a["title"], a["desc"], SITE+url, jsonld=ld)
    s += breadcrumb_html(trail)
    s += f"""
  <main id="main">
    {page_hero(a['hub'][0]+" 생활권", a['h1'])}
    <section class="section">
      <div class="container prose">
        <p class="muted">포함 지역 · {html.escape(a['incs'])}</p>
        {body}
        <h2>이용 장소 기준</h2>
        <ul>
          <li><a href="/incheon-bucheon-siheung/check/apartment-access.html">아파트 공동현관</a> — 출입 방식과 동·호수 확인</li>
          <li><a href="/incheon-bucheon-siheung/check/hotel-policy.html">호텔·숙소 정책</a> — 객실 방문 가능 여부 확인</li>
          <li><a href="/incheon-bucheon-siheung/check/officetel-rule.html">오피스텔 관리 규정</a> — 공동현관·엘리베이터 확인</li>
          <li><a href="/incheon-bucheon-siheung/check/time.html">예약 가능 시간</a> — 야간 출입 가능 여부 확인</li>
        </ul>
      </div>
    </section>
    <section class="section" style="padding-top:0;">
      <div class="container narrow"><div class="card"><h2>예약 전 체크리스트</h2>{CHECKLIST}</div></div>
    </section>
    <section class="section" style="padding-top:0;">
      <div class="container"><div class="section-head"><h2>Who · How · Why</h2></div>
        {whw_html("간다GO 예약 안내 담당이 해당 생활권 자료로 작성·검수합니다.",
                  "생활권별 숙소 유형과 이동 조건을 반영해 다르게 작성합니다.",
                  "이용자가 위치와 이용 장소를 정확히 확인하고 안심하고 예약하도록 돕기 위함입니다.")}</div>
    </section>
    <section class="section" style="padding-top:0;"><div class="container narrow">{NOTICE}</div></section>
    <section class="section" style="padding-top:0;">
      <div class="container narrow"><div class="section-head"><h2>자주 묻는 질문</h2></div>{faq_html(AREA_FAQ)}</div>
    </section>
    <section class="section" style="padding-top:0;">
      <div class="container narrow"><div class="section-head"><h2>관련 지역 보기</h2></div>
        <div class="related">
          <a href="{a['hub'][1]}">{a['hub'][0]}권 전체</a>
          <a href="/incheon-bucheon-siheung/">서부 수도권 전체</a>
          <a href="/incheon-bucheon-siheung/check/address.html">예약 전 확인</a>
        </div></div>
    </section>
  </main>
{FOOT}"""
    emit(f"incheon-bucheon-siheung/area/{a['slug']}.html", url, s)

for a in AREAS:
    render_area(a)

# ---------------------------------------------------------------------------
# CHECK / POLICY pages
# ---------------------------------------------------------------------------
def render_doc(slug, title, desc, h1, sections, faqs=None, danger=False):
    url = f"/incheon-bucheon-siheung/check/{slug}.html"
    trail = [("간다GO","/"),("인천·부천·시흥","/incheon-bucheon-siheung/"),
             ("예약 전 확인","/incheon-bucheon-siheung/check/address.html"),(h1, url)]
    nodes = [webpage_ld(SITE+url, title.split("｜")[0]), breadcrumb_ld(trail)]
    if faqs: nodes.append(faq_ld(faqs))
    s = head(title, desc, SITE+url, jsonld=jsonld(*nodes))
    s += breadcrumb_html(trail)
    body = ""
    for h, ps in sections:
        body += f"<h2>{html.escape(h)}</h2>" + "".join(f"<p>{p}</p>" for p in ps)
    n = NOTICE if not danger else NOTICE.replace('notice notice--danger','notice notice--danger')
    s += f"""
  <main id="main">
    {page_hero("예약 전 확인 · 운영 기준", h1)}
    <section class="section">
      <div class="container prose">
        {body}
      </div>
    </section>
    <section class="section" style="padding-top:0;"><div class="container narrow">{n}</div></section>
    {('<section class="section" style="padding-top:0;"><div class="container narrow"><div class="section-head"><h2>자주 묻는 질문</h2></div>'+faq_html(faqs)+'</div></section>') if faqs else ''}
    <section class="section" style="padding-top:0;">
      <div class="container narrow"><div class="section-head"><h2>다른 확인 사항</h2></div>
        <div class="related">
          <a href="/incheon-bucheon-siheung/check/address.html">방문 주소 확인</a>
          <a href="/incheon-bucheon-siheung/check/building-access.html">건물 출입 방식</a>
          <a href="/incheon-bucheon-siheung/check/apartment-access.html">아파트 공동현관</a>
          <a href="/incheon-bucheon-siheung/check/hotel-policy.html">호텔·숙소 정책</a>
          <a href="/incheon-bucheon-siheung/check/officetel-rule.html">오피스텔 관리 규정</a>
          <a href="/incheon-bucheon-siheung/check/time.html">예약 가능 시간</a>
          <a href="/incheon-bucheon-siheung/check/travel-fee.html">외곽 이동비 기준</a>
          <a href="/incheon-bucheon-siheung/check/privacy.html">개인정보 처리방침</a>
          <a href="/incheon-bucheon-siheung/check/service-policy.html">서비스 불가 안내</a>
        </div></div>
    </section>
  </main>
{FOOT}"""
    emit(f"incheon-bucheon-siheung/check/{slug}.html", url, s)

render_doc("address","방문 주소 확인｜예약 전 확인 — 간다GO",
  "출장마사지 예약 전 방문 주소·상세 호실 확인 방법과 준비 사항을 안내합니다.",
  "방문 주소 확인",
  [("정확한 주소가 예약의 시작입니다",["방문 케어는 정확한 주소에서 출발합니다. 도로명 주소와 함께 동·호수, 건물명, 상세 위치를 확인하면 도착 시간이 정확해집니다."]),
   ("생활권별 확인 포인트",["아파트는 단지명과 동·호수, 공동현관 방식을 확인합니다. 오피스텔은 건물명과 층·호실, 관리 규정을 확인합니다. 호텔은 호텔명과 객실 방문 가능 여부를 확인합니다."]),
   ("공항·항만·외곽 지역",["영종·인천공항·오이도·월곶·강화 방향 외곽은 이동 시간이 길 수 있어 예약 시간을 여유 있게 확인합니다."])],
  faqs=[("주소를 미리 알려야 하나요?","예약 확인과 정확한 방문을 위해 방문 주소와 상세 호실을 확인합니다. 개인정보는 최소한만 처리합니다.")])

render_doc("building-access","건물 출입 방식｜예약 전 확인 — 간다GO",
  "출장마사지 방문 시 건물 출입·공동현관·엘리베이터 확인 사항을 안내합니다.",
  "건물 출입 방식",
  [("공동현관과 출입",["건물에 따라 공동현관 비밀번호, 호출, 카드키 방식이 다릅니다. 미리 출입 방식을 확인하면 방문이 매끄럽습니다."]),
   ("엘리베이터·층 이동",["카드 태그가 필요한 엘리베이터는 층 이동 방식을 확인합니다. 야간에는 출입이 제한될 수 있어 가능 여부를 함께 확인합니다."])])

render_doc("apartment-access","아파트 공동현관 확인｜예약 전 확인 — 간다GO",
  "아파트 공동현관 출입 방식과 동·호수 확인 등 방문 준비 사항을 안내합니다.",
  "아파트 공동현관 확인",
  [("공동현관 출입",["아파트는 공동현관 비밀번호 또는 세대 호출로 출입합니다. 동·호수와 함께 출입 방식을 확인하면 도착이 빠릅니다."]),
   ("단지 내 이동",["대단지는 동 간 거리가 있어 정확한 동 번호와 출입구를 확인합니다. 지상·지하 주차 여부도 함께 확인합니다."])])

render_doc("hotel-policy","호텔·숙소 정책｜예약 전 확인 — 간다GO",
  "호텔·숙소 방문 시 객실 출입·방문 가능 여부 등 정책 확인 사항을 안내합니다.",
  "호텔·숙소 정책",
  [("객실 방문 가능 여부",["호텔·숙소마다 외부인 객실 방문 정책이 다릅니다. 예약 전 객실 방문 가능 여부와 프런트 정책을 확인합니다."]),
   ("공항·관광 숙소",["공항 인접 호텔과 관광지 숙소는 출입 절차가 까다로울 수 있어 방문 정책을 미리 확인합니다."])])

render_doc("officetel-rule","오피스텔 관리 규정｜예약 전 확인 — 간다GO",
  "오피스텔 방문 시 공동현관·엘리베이터·관리 규정 확인 사항을 안내합니다.",
  "오피스텔 관리 규정",
  [("관리 규정 확인",["오피스텔은 공동현관, 엘리베이터 카드키, 방문객 등록 등 관리 규정이 있습니다. 예약 전 확인하면 방문이 원활합니다."]),
   ("야간 이용",["야간에는 공동현관·엘리베이터 이용이 제한될 수 있어 예약 가능 시간과 함께 확인합니다."])])

render_doc("time","예약 가능 시간｜예약 전 확인 — 간다GO",
  "출장마사지 예약 가능 시간과 야간 출입 가능 여부 확인 방법을 안내합니다.",
  "예약 가능 시간",
  [("예약 가능 시간 확인",["예약 가능 시간은 지역·이동 거리·시간대에 따라 달라집니다. 원하는 시간을 미리 알려주시면 가능 여부를 확인해 안내합니다."]),
   ("야간·심야 이용",["야간·심야는 건물 출입이 제한될 수 있어 출입 방식과 예약 가능 여부를 함께 확인합니다."])])

render_doc("travel-fee","외곽 이동비 기준｜상세 요금 안내 — 간다GO",
  "출장마사지 코스 요금과 외곽 지역 이동 기준을 투명하게 안내합니다.",
  "외곽 이동비 기준",
  [("코스 요금은 정찰제입니다",["60분 90,000원, 90분 150,000원, 120분 180,000원의 코스별 기준 요금이며 추가 비용 없이 안내합니다."]),
   ("지역·이동 거리 기준",["지역, 예약 시간대, 이동 거리에 따라 상담 시 최종 확인됩니다. 영종·강화·오이도 방향 외곽은 이동 시간을 함께 확인합니다."])],
  faqs=[("코스 요금 외에 추가 비용이 있나요?","코스별 기준 요금 그대로 안내하며, 지역·시간대·이동 거리에 따라 상담 시 최종 확인됩니다.")])

render_doc("privacy","개인정보 처리방침 — 간다GO",
  "간다GO 개인정보 처리방침. 예약 확인·연락에 필요한 최소 정보만 처리합니다.",
  "개인정보 처리방침",
  [("수집 항목과 목적",["간다GO는 예약 확인과 연락에 필요한 최소한의 정보(연락처, 방문 주소·시간)만 확인합니다. 마케팅 목적의 별도 수집은 하지 않습니다."]),
   ("보관과 파기",["예약 안내 목적이 끝나면 관련 정보를 지체 없이 파기합니다. 법령상 보관 의무가 없는 정보는 보관하지 않습니다."]),
   ("제3자 제공",["이용자의 동의 없이 개인정보를 제3자에게 제공하지 않습니다. 예약 문의 연락 외 목적으로 사용하지 않습니다."])])

render_doc("service-policy","불법·선정적 서비스 불가 안내 — 간다GO",
  "간다GO는 불법·선정적 서비스를 제공하거나 안내하지 않습니다. 건전한 방문 케어만 안내합니다.",
  "불법·선정적 서비스 불가 안내",
  [("건전한 방문 케어만 안내합니다",["간다GO는 컨디션·릴랙스·아로마 중심의 건전한 방문 케어만 안내합니다. 불법·선정적 서비스는 제공하거나 안내하지 않습니다."]),
   ("이용자 유의사항",["법령을 위반하거나 선정적 목적의 문의에는 응대하지 않습니다. 모든 안내는 건전한 이용을 전제로 합니다."])],
  danger=True)

# ---------------------------------------------------------------------------
# ABOUT (작성자·검수자 안내)
# ---------------------------------------------------------------------------
def render_about():
    url = "/incheon-bucheon-siheung/about/"
    trail = [("간다GO","/"),("인천·부천·시흥","/incheon-bucheon-siheung/"),("작성자·검수자 안내",url)]
    ld = jsonld(webpage_ld(SITE+url,"작성자·검수자 안내"), breadcrumb_ld(trail))
    s = head("작성자·검수자 안내 — 간다GO",
             "간다GO 지역 안내 콘텐츠의 작성·검수 기준과 책임 주체를 안내합니다.",
             SITE+url, jsonld=ld)
    s += breadcrumb_html(trail)
    s += f"""
  <main id="main">
    {page_hero("E-E-A-T · Who/How/Why", "작성자·검수자 안내")}
    <section class="section">
      <div class="container prose">
        <p class="lede">이 사이트의 지역 안내 콘텐츠는 간다GO 예약 안내 담당이 서부 수도권(인천·부천·시흥) 생활권 자료를
          바탕으로 작성하고 검수합니다.</p>
        <h2>작성 기준</h2>
        <ul>
          <li>지역명만 바꾼 복제 콘텐츠를 만들지 않고, 실제 생활권 차이가 있는 페이지만 안내합니다.</li>
          <li>행정체제 개편(2026년 7월)과 실제 이동·숙소 조건을 반영합니다.</li>
          <li>가짜 후기·허위 평점·상위노출 보장 표현을 사용하지 않습니다.</li>
        </ul>
        <h2>책임 주체</h2>
        <dl class="footer-biz" style="color:var(--text-base)">
          <dt>상호</dt><dd>간다GO</dd>
          <dt>전화예약</dt><dd><a href="tel:{TEL}">{TEL}</a></dd>
          <dt>문의</dt><dd><a href="{TG}" rel="nofollow noopener" target="_blank">텔레그램 문의</a></dd>
        </dl>
        <p class="muted">실제 오프라인 매장 주소가 없는 방문형 서비스이므로 LocalBusiness·Review·평점 구조화 데이터는 사용하지 않습니다.</p>
      </div>
    </section>
  </main>
{FOOT}"""
    emit("incheon-bucheon-siheung/about/index.html", url, s)

render_about()

# ---------------------------------------------------------------------------
# DISTRICT (행정구/권역) + DONG (행정동) pages
#  - district: index,follow (실제 집계 가치)
#  - dong: noindex,follow (템플릿 기반 얇은 페이지 — 도어웨이 색인 방지, 탐색은 가능)
# ---------------------------------------------------------------------------
def dong_faq(name):
    return [
      (f"{name} 어디까지 방문 가능한가요?", "정확한 방문 주소, 가까운 역·생활권, 예약 가능 시간, 이동 기준을 확인한 뒤 안내합니다."),
      ("호텔이나 오피스텔에서도 이용할 수 있나요?", "숙소 정책, 객실 출입 가능 여부, 공동현관, 엘리베이터, 관리 규정을 먼저 확인해야 합니다."),
      ("불법·선정적 서비스도 가능한가요?", "불법·선정적 서비스는 제공하거나 안내하지 않습니다."),
    ]

def render_dong(city_key, dist, dong):
    slug, name, desc, stations = dong
    base = f"/incheon-bucheon-siheung/{city_key}/{dist['slug']}/"
    url = base + slug + ".html"
    city = CITIES[city_key]
    trail = [("간다GO","/"),("인천·부천·시흥","/incheon-bucheon-siheung/"),
             (city["name"], city["hub"]),(dist["name"], base),(name, url)]
    title = f"{name} 출장마사지｜{dist['name']} 행정동 안내 — 간다GO"
    mdesc = f"{name} 출장마사지·홈타이 방문 이용 기준과 인접 역·생활권을 안내합니다."
    ld = jsonld(webpage_ld(SITE+url, f"{name} 출장마사지 안내"), breadcrumb_ld(trail), faq_ld(dong_faq(name)))
    # 형제 동 (같은 구) 관련 링크 — 최대 6개
    sibs = [d for d in dist["dongs"] if d[0] != slug][:6]
    sib_links = "".join(f'<a href="{base}{d[0]}.html">{html.escape(d[1])}</a>' for d in sibs)
    s = head(title, mdesc, SITE+url, jsonld=ld, robots="noindex,follow,max-image-preview:large")
    s += breadcrumb_html(trail)
    s += f"""
  <main id="main">
    {page_hero(f"{city['name']} · {dist['name']}", f"{name} 출장마사지 · 생활권 이용 안내")}
    <section class="section">
      <div class="container prose">
        <p class="lede">{html.escape(desc)}</p>
        <p class="muted">인접 역·교통 · {html.escape(stations)}</p>
        <p>{name}에서 방문 케어를 이용할 때는 정확한 방문 주소와 상세 호실, 건물 출입 방식을 먼저 확인하는 것이 좋습니다.
          아파트는 <a href="/incheon-bucheon-siheung/check/apartment-access.html">공동현관 출입 방식</a>,
          오피스텔은 <a href="/incheon-bucheon-siheung/check/officetel-rule.html">관리 규정</a>,
          호텔·숙소는 <a href="/incheon-bucheon-siheung/check/hotel-policy.html">객실 방문 정책</a>을 함께 확인합니다.
          예약 가능 시간과 야간 출입 가능 여부는 <a href="/incheon-bucheon-siheung/check/time.html">예약 가능 시간</a>에서 확인하세요.</p>
      </div>
    </section>
    <section class="section" style="padding-top:0;">
      <div class="container narrow"><div class="card"><h2>예약 전 체크리스트</h2>{CHECKLIST}</div></div>
    </section>
    <section class="section" style="padding-top:0;">
      <div class="container"><div class="section-head"><h2>Who · How · Why</h2></div>
        {whw_html("간다GO 예약 안내 담당이 "+name+" 생활권 자료로 작성·검수합니다.",
                  "행정동별 숙소 유형과 인접 역·이동 조건을 반영해 안내합니다.",
                  "이용자가 위치와 이용 장소를 정확히 확인하고 안심하고 예약하도록 돕기 위함입니다.")}</div>
    </section>
    <section class="section" style="padding-top:0;"><div class="container narrow">{NOTICE}</div></section>
    <section class="section" style="padding-top:0;">
      <div class="container narrow"><div class="section-head"><h2>자주 묻는 질문</h2></div>{faq_html(dong_faq(name))}</div>
    </section>
    <section class="section" style="padding-top:0;">
      <div class="container narrow"><div class="section-head"><h2>같은 {dist['name']} 다른 지역</h2></div>
        <div class="related">{sib_links}
          <a href="{base}">{html.escape(dist['name'])} 전체</a>
          <a href="{city['hub']}">{city['name']}권 전체</a>
        </div></div>
    </section>
  </main>
{FOOT}"""
    # dong 은 sitemap 에 넣지 않음 (noindex)
    write(url.lstrip("/"), inject(s))

def render_district(city_key, dist):
    city = CITIES[city_key]
    url = f"/incheon-bucheon-siheung/{city_key}/{dist['slug']}/"
    trail = [("간다GO","/"),("인천·부천·시흥","/incheon-bucheon-siheung/"),
             (city["name"], city["hub"]),(dist["name"], url)]
    title = f"{dist['name']} 출장마사지｜행정동 이용 안내 — 간다GO"
    mdesc = f"{dist['name']} 행정동별 출장마사지·홈타이 이용 기준과 생활권을 안내합니다."
    faqs = [
      (f"{dist['name']}은 어느 행정동까지 안내되나요?",
       f"{dist['name']} 주요 행정동을 생활권 기준으로 안내하며, 번호가 나뉜 동(1·2·3동)은 대표 동으로 묶어 안내합니다."),
      ("행정동을 먼저 확인해야 하나요?",
       "네. 같은 구 안에서도 상권·주거·역세권 조건이 달라 방문 주소와 인접 역을 먼저 확인하는 것이 좋습니다."),
      ("불법·선정적 서비스도 가능한가요?", "불법·선정적 서비스는 제공하거나 안내하지 않습니다."),
    ]
    ld = jsonld(webpage_ld(SITE+url, f"{dist['name']} 출장마사지 안내"), breadcrumb_ld(trail), faq_ld(faqs))
    s = head(title, mdesc, SITE+url, jsonld=ld)
    s += breadcrumb_html(trail)
    if dist.get("overview_only"):
        body = f"""
    <section class="section">
      <div class="container prose">
        <p class="lede">{html.escape(dist['desc'])}</p>
        <p>{dist['name']}은 이동 거리·방문 가능 기준을 먼저 확인한 뒤 안내하는 지역입니다.
          정확한 방문 주소와 <a href="/incheon-bucheon-siheung/check/travel-fee.html">외곽 이동비 기준</a>,
          <a href="/incheon-bucheon-siheung/check/time.html">예약 가능 시간</a>을 함께 확인해 주세요.</p>
      </div>
    </section>"""
    else:
        cards = "".join(
          f'<a class="card card--link" href="{url}{d[0]}.html"><h3>{html.escape(d[1])}</h3>'
          f'<p>{html.escape(d[3])}</p></a>' for d in dist["dongs"])
        body = f"""
    <section class="section">
      <div class="container prose"><p class="lede">{html.escape(dist['desc'])}</p>
        <p>아래 행정동을 선택하면 생활권·인접 역·이용 장소 기준을 확인할 수 있습니다.
          번호로 나뉜 동은 대표 동으로 묶어 안내합니다.</p></div>
    </section>
    <section class="section" style="padding-top:0;">
      <div class="container"><div class="section-head"><h2>{dist['name']} 행정동</h2></div>
        <div class="grid cards-3">{cards}</div></div>
    </section>"""
    s += f"""
  <main id="main">
    {page_hero(f"{city['name']} {city['mid_label']}", f"{dist['name']} 출장마사지 · 행정동 안내")}{body}
    <section class="section" style="padding-top:0;">
      <div class="container narrow"><div class="card"><h2>예약 전 체크리스트</h2>{CHECKLIST}</div></div>
    </section>
    <section class="section" style="padding-top:0;"><div class="container narrow">{NOTICE}</div></section>
    <section class="section" style="padding-top:0;">
      <div class="container narrow"><div class="section-head"><h2>자주 묻는 질문</h2></div>{faq_html(faqs)}</div>
    </section>
    <section class="section" style="padding-top:0;">
      <div class="container narrow"><div class="section-head"><h2>다른 {city['mid_label']} 보기</h2></div>
        <div class="related">{"".join(f'<a href="/incheon-bucheon-siheung/{city_key}/{o["slug"]}/">{html.escape(o["name"])}</a>' for o in city["districts"] if o["slug"]!=dist["slug"])}
          <a href="{city['hub']}">{city['name']}권 전체</a></div></div>
    </section>
  </main>
{FOOT}"""
    write(url.lstrip("/") + "index.html", inject(s))
    URLS.append(url)

for ck, cv in CITIES.items():
    for dist in cv["districts"]:
        render_district(ck, dist)
        for dong in dist["dongs"]:
            render_dong(ck, dist, dong)

# ---------------------------------------------------------------------------
# SUBWAY (지하철 중심) — 핵심 환승·상권 허브만. 출구별·노선별 페이지는 만들지 않음.
# ---------------------------------------------------------------------------
def render_subway():
    idx_url = "/incheon-bucheon-siheung/subway/"
    trail0 = [("간다GO","/"),("인천·부천·시흥","/incheon-bucheon-siheung/"),("지하철 중심 안내", idx_url)]
    cards = "".join(
      f'<a class="card card--link" href="/incheon-bucheon-siheung/subway/{s[0]}.html">'
      f'<h3>{html.escape(s[1])}</h3><p>{html.escape(s[2])} · {html.escape(s[3][:38])}…</p></a>'
      for s in STATIONS)
    faqs = [
      ("지하철역 근처에서도 이용할 수 있나요?", "역세권 숙소·오피스텔은 정확한 출구 방향이 아닌 실제 방문 주소와 건물 출입 방식을 확인해 안내합니다."),
      ("출구별·노선별 페이지는 없나요?", "검색 조작을 위한 출구별·노선별 페이지는 만들지 않습니다. 핵심 환승·상권 허브만 안내합니다."),
    ]
    ld = jsonld(webpage_ld(SITE+idx_url, "지하철 중심 출장마사지 안내"), breadcrumb_ld(trail0), faq_ld(faqs))
    s = head("지하철 중심 출장마사지｜인천·부천·시흥 역세권 안내 — 간다GO",
             "인천·부천·시흥 지하철 역세권 출장마사지·홈타이 이용 기준을 역별로 안내합니다.",
             SITE+idx_url, jsonld=ld)
    s += breadcrumb_html(trail0)
    s += f"""
  <main id="main">
    {page_hero("지하철 중심 안내", "지하철 역세권 출장마사지 · 이용 안내")}
    <section class="section">
      <div class="container prose"><p class="lede">인천·부천·시흥의 핵심 환승·상권 역을 중심으로 역세권 이용 기준을 안내합니다.
        출구별·노선별 페이지는 검색 조작 방지를 위해 만들지 않으며, 실제 생활권 가치가 있는 허브 역만 정리했습니다.</p></div>
    </section>
    <section class="section" style="padding-top:0;">
      <div class="container"><div class="section-head"><h2>핵심 역세권</h2></div>
        <div class="grid cards-3">{cards}</div></div>
    </section>
    <section class="section" style="padding-top:0;"><div class="container narrow">{NOTICE}</div></section>
    <section class="section" style="padding-top:0;">
      <div class="container narrow"><div class="section-head"><h2>자주 묻는 질문</h2></div>{faq_html(faqs)}</div>
    </section>
  </main>
{FOOT}"""
    emit("incheon-bucheon-siheung/subway/index.html", idx_url, s)

    for slug, name, lines, desc, rel in STATIONS:
        url = f"/incheon-bucheon-siheung/subway/{slug}.html"
        trail = trail0[:-1] + [("지하철 중심 안내", idx_url), (name, url)]
        title = f"{name} 출장마사지｜{lines} 역세권 이용 안내 — 간다GO"
        mdesc = f"{name} 역세권 출장마사지·홈타이 이용 기준과 인접 생활권을 안내합니다."
        sfaq = [
          (f"{name} 근처 숙소도 안내되나요?", "역세권 숙소·오피스텔은 실제 방문 주소와 건물 출입 방식, 예약 가능 시간을 확인해 안내합니다."),
          ("불법·선정적 서비스도 가능한가요?", "불법·선정적 서비스는 제공하거나 안내하지 않습니다."),
        ]
        ld = jsonld(webpage_ld(SITE+url, f"{name} 역세권 출장마사지 안내"), breadcrumb_ld(trail), faq_ld(sfaq))
        st = head(title, mdesc, SITE+url, jsonld=ld)
        st += breadcrumb_html(trail)
        st += f"""
  <main id="main">
    {page_hero(f"지하철 · {lines}", f"{name} 출장마사지 · 역세권 이용 안내")}
    <section class="section">
      <div class="container prose">
        <p class="lede">{html.escape(desc)}</p>
        <p>{name} 인근에서 방문 케어를 이용할 때는 정확한 방문 주소와 상세 호실, 건물 출입 방식을 먼저 확인하는 것이 좋습니다.
          자세한 이용 장소 기준은 <a href="{rel}">인접 생활권 안내</a>와
          <a href="/incheon-bucheon-siheung/check/address.html">예약 전 확인</a>에서 이어집니다.</p>
      </div>
    </section>
    <section class="section" style="padding-top:0;">
      <div class="container narrow"><div class="card"><h2>예약 전 체크리스트</h2>{CHECKLIST}</div></div>
    </section>
    <section class="section" style="padding-top:0;"><div class="container narrow">{NOTICE}</div></section>
    <section class="section" style="padding-top:0;">
      <div class="container narrow"><div class="section-head"><h2>자주 묻는 질문</h2></div>{faq_html(sfaq)}</div>
    </section>
    <section class="section" style="padding-top:0;">
      <div class="container narrow"><div class="section-head"><h2>다른 역세권 보기</h2></div>
        <div class="related">
          <a href="{idx_url}">지하철 전체</a>
          <a href="{rel}">인접 생활권</a>
          <a href="/incheon-bucheon-siheung/">서부 수도권 전체</a>
        </div></div>
    </section>
  </main>
{FOOT}"""
        emit(f"incheon-bucheon-siheung/subway/{slug}.html", url, st)

render_subway()

# ---------------------------------------------------------------------------
# Inject partials into hand-written pages (index.html + regional main)
# ---------------------------------------------------------------------------
for p in ["index.html", "incheon-bucheon-siheung/index.html"]:
    write(p, inject(read(p)))

# ---------------------------------------------------------------------------
# sitemap.xml + robots.txt
# ---------------------------------------------------------------------------
today = "2026-07-03"
urls_xml = "".join(
    f"<url><loc>{SITE}{u}</loc><lastmod>{today}</lastmod>"
    f"<priority>{'1.0' if u=='/' else '0.8' if u.count('/')<=2 else '0.6'}</priority></url>"
    for u in dict.fromkeys(URLS))
write("sitemap.xml",
      '<?xml version="1.0" encoding="UTF-8"?>\n'
      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + urls_xml + "</urlset>\n")

write("robots.txt",
      "User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % SITE)

print(f"Generated {len(dict.fromkeys(URLS))} pages.")
print("Pages:")
for u in dict.fromkeys(URLS):
    print("  ", u)
