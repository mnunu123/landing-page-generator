# OpenClaw 랜딩 페이지 — Cloudflare Pages 배포 가이드

## 디렉토리 구조

```
cf-pages/
├── index.html          # 메인 랜딩 페이지 (A/B 라우팅 + GA4)
├── hotspots.json       # 클릭 영역(Hotspot) 정의
├── images/
│   ├── final_page_A.png  # A 변형 (openclaw_v3)
│   └── final_page_B.png  # B 변형 (openclaw_v4)
└── README.md
```

---

## 1. 배포 전 필수 설정

### 1-1. GA4 측정 ID 교체

`index.html` 에서 `G-XXXXXXXXXX` 를 실제 GA4 측정 ID로 2곳 모두 교체합니다.

```html
<!-- 변경 전 -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
...
gtag('config', 'G-XXXXXXXXXX', { send_page_view: false });

<!-- 변경 후 (예시) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-AB12CD34EF"></script>
...
gtag('config', 'G-AB12CD34EF', { send_page_view: false });
```

또한 `index.html` 내 `CONFIG` 객체도 맞게 수정합니다.

```js
var CONFIG = {
  GA4_ID:  'G-AB12CD34EF',  // 실제 ID
  EXP_ID:  'openclaw_v3v4', // 실험 이름 (GA4 필터링용)
  PAGE_ID: 'openclaw',
  ...
};
```

### 1-2. CTA URL 교체

`hotspots.json` 에서 `https://forms.gle/REPLACE_ME` 를 실제 신청 URL로 교체합니다.

```json
"href": "https://forms.gle/실제구글폼ID"
```

---

## 2. Cloudflare Pages 배포

### 방법 A — Wrangler CLI (권장)

```bash
# 설치 (최초 1회)
npm install -g wrangler

# 로그인
wrangler login

# cf-pages 폴더를 바로 배포
wrangler pages deploy ./cf-pages --project-name openclaw-lp
```

### 방법 B — Cloudflare 대시보드 업로드

1. https://dash.cloudflare.com → Pages → "프로젝트 만들기"
2. "직접 업로드" 선택
3. `cf-pages/` 폴더 전체를 드래그 앤 드롭

---

## 3. 로컬 테스트

### Python 간이 서버

```bash
cd cf-pages
python -m http.server 8080
```

브라우저에서 `http://localhost:8080` 접속.

### A/B 강제 테스트

| URL | 동작 |
|-----|------|
| `http://localhost:8080/?var=A` | A 변형 강제 |
| `http://localhost:8080/?var=B` | B 변형 강제 |
| `http://localhost:8080/?debug=true` | 핫스팟 위치 시각화 (초록 점선) |
| `http://localhost:8080/?var=A&debug=true` | A + 핫스팟 시각화 동시 |

### 클릭 이벤트 확인 (콘솔)

1. 브라우저 개발자도구 → Console 탭 열기
2. CTA 버튼 영역 클릭
3. 아래와 같이 출력되면 정상:

```
[GA4] sent lp_cta_click {exp_id: 'openclaw_v3v4', var: 'A', page_id: 'openclaw', cta_id: 'hero_cta', section_id: '01_hero'}
```

---

## 4. GA4 DebugView 확인

1. `index.html` URL에 `&gtm_debug=x` 추가 혹은 Chrome 확장 **GA Debugger** 설치
2. GA4 → [관리] → [DebugView] 접속
3. 랜딩 페이지에서 클릭하면 실시간으로 이벤트 확인 가능

DebugView 직접 활성화 방법:

```
https://yoursite.pages.dev/?debug=true
```

GA4 DebugView URL:
```
https://analytics.google.com/analytics/web/#/p{측정ID}/reports/debugview
```

---

## 5. GA4 이벤트 스펙

| 이벤트명 | 시점 | 필수 파라미터 |
|---------|------|------------|
| `lp_impression` | 페이지 로드 완료 | exp_id, var, page_id |
| `lp_cta_click` | 핫스팟 클릭 | exp_id, var, page_id, cta_id, section_id |
| `lp_reserve_submit` | 신청 완료 페이지 | exp_id, var, page_id, plan, price |

### lp_reserve_submit 구현 (감사 페이지에서)

신청 완료 후 리다이렉트되는 "감사합니다" 페이지에 아래 코드를 추가합니다.

```html
<script>
  // URL 파라미터에서 A/B 정보 복원
  var storedVar = localStorage.getItem('oc_ab_var') || 'unknown';

  gtag('event', 'lp_reserve_submit', {
    exp_id:  'openclaw_v3v4',
    var:     storedVar,
    page_id: 'openclaw',
    plan:    'monthly',
    price:   40000,
  });
</script>
```

---

## 6. 핫스팟 좌표 조정

배포 후 실제 PNG에서 버튼 위치가 맞지 않으면 `?debug=true`로 초록 점선을 보면서 `hotspots.json` 의 `left / top / width / height` 값을 조정합니다.

```json
{
  "id": "hero_cta",
  "left":   "34%",   ← 왼쪽 여백 (PNG 너비 기준 %)
  "top":    "7.2%",  ← 상단 여백 (PNG 높이 기준 %)
  "width":  "32%",   ← 클릭 영역 너비
  "height": "1.1%",  ← 클릭 영역 높이
  ...
}
```

---

## 7. A/B 결과 분석 (GA4 탐색 보고서)

1. GA4 → [탐색] → 자유형식
2. 측정기준에 `var` (맞춤 측정기준으로 등록 필요) 추가
3. 측정항목: `lp_cta_click` 이벤트 수, `lp_reserve_submit` 이벤트 수
4. A vs B 전환율 비교

> **맞춤 측정기준 등록**: GA4 → 관리 → 맞춤 정의 → 맞춤 측정기준 → 만들기
> 이름: `ab_variant`, 범위: 이벤트, 이벤트 매개변수: `var`
