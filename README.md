# 간다GO — 출장마사지·홈타이 지역 안내 사이트

인천·부천·시흥 서부 수도권 생활권 기준의 방문 케어 안내 정적 사이트입니다.
프리미엄 다크 팔레트 + Pretendard 토큰 시스템 위에 컴포넌트 오버레이를 얹었습니다.

## 구조
```
index.html                          메인 (간다GO 브랜드 · 코스 요금 · 지역 안내 진입)
incheon-bucheon-siheung/
  index.html                        지역 메인 (3대 핵심축 · 9대 생활권)
  incheon|bucheon|siheung/          3대 핵심축 허브 (행정구/권역 버튼)
    <행정구>/index.html             행정구·권역 페이지 (행정동 목록)   ← index
    <행정구>/<행정동>.html          행정동 페이지                      ← noindex,follow
  area/*.html                       9대 생활권 페이지
  subway/                           지하철 중심 안내 (핵심 역세권 허브)
  check/*.html                      예약 전 확인 · 개인정보 · 서비스 불가 안내
  about/                            작성자·검수자 안내 (E-E-A-T)
css/  tokens.css | base.css | components.css   프리미엄 팔레트 토큰 + 컴포넌트
partials/  footer.html | rheader.html          공용 파셜 (빌드 시 주입)
build/admin_data.py                 행정구·행정동·지하철 데이터 (단일 소스)
build/generate.py                   데이터 기반 페이지 생성 + 파셜 주입 + sitemap
sitemap.xml · robots.txt
```

## 빌드
```bash
python3 build/generate.py     # 파셜 주입 + 지역/행정동/지하철/정책 페이지 생성 + sitemap.xml
```
행정동·지하철 추가/수정은 `build/admin_data.py` 만 고치고 다시 빌드하면 됩니다.

## 내비게이션
- 상단 메뉴 **인천권 / 부천권 / 시흥권** 클릭 시 행정구(권역)가 버튼으로 펼쳐집니다
  (details/summary 기반, JS 불필요·모바일 호환).
- 행정구 클릭 → 행정구 페이지(행정동 목록) → 행정동 페이지로 이동.

## SEO · 도어웨이 방지
- 모든 페이지: `<title>`, canonical, meta description(80자 이내), OG, JSON-LD 구조화 데이터.
- Schema: Organization / WebSite / WebPage / Service / FAQPage / BreadcrumbList.
- 실제 오프라인 매장이 없는 방문형 서비스이므로 **LocalBusiness · Review · AggregateRating 미사용**.
- **번호동 통합**: 부평1~6동·정왕1~4동 등은 대표 동 1개로만 생성.
- **행정동 = `noindex,follow`**: 템플릿 기반 얇은 페이지의 도어웨이 색인을 막고 탐색·링크는 유지.
  행정구·생활권·지하철·허브 페이지는 색인(집계 가치 있음).
- **지하철**: 출구별·노선별 페이지는 만들지 않고 핵심 환승·상권 허브만 색인.
- 롱테일 이용상황 앵커 기반 내부링크로 메인 → 지역 → 행정구 → 행정동 연결.

## ⚠️ 배포 전 교체 필요
- **텔레그램 핸들**: `https://t.me/ganda_go` 는 임시값입니다. 실제 계정으로 교체하세요.
  (`partials/footer.html`, `index.html` hero, `build/generate.py`의 `TG` 상수)
- **도메인**: `https://gandago.co.kr` 을 실제 도메인으로 교체하세요 (`build/generate.py`의 `SITE`, 각 canonical/OG).
- 상호: 간다GO · 전화예약: 0508-202-4719
