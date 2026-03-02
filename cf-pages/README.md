# OpenClaw 랜딩 페이지 (Cloudflare Pages) — A/B + GA4 + Formspree(모달) 운영 가이드

PNG 랜딩(배경 이미지) 위에 투명 Hotspot을 올려 **클릭/신청(폼 제출)** 을 가능하게 만든 정적 랜딩입니다.

- A/B 노출: URL 파라미터/쿠키/로컬스토리지로 변형 고정
- GA4 측정: impression / cta_click / reserve_submit
- 신청 수집: Formspree AJAX(모달 폼)로 제출 성공 시 전환 이벤트 기록
- 배포: Cloudflare Pages (정적)

---

## 디렉토리 구조
cf-pages/
├── index.html # 메인 랜딩 (A/B 라우팅 + GA4 + Formspree 모달)
├── hotspots.json # 클릭 영역(Hotspot) 정의(좌표는 %)
├── images/
│ ├── final_page_A.png # A 변형
│ └── final_page_B.png # B 변형
└── README.md


---

## 0) 먼저 이해할 것 (중요)

### ✅ PNG 자체는 클릭/링크를 가질 수 없습니다
클릭 가능한 영역은 반드시 HTML 레이어(Hotspot/버튼/모달)로 만들어야 합니다.

### ✅ GA4에는 개인정보(이메일/전화/메시지)를 절대 보내지 마세요
GA4 이벤트에는 `exp_id`, `var`, `cta_id` 같은 “행동 데이터”만 포함합니다.  
이메일/전화번호/메시지는 **Formspree로만** 전송합니다.

---

## 1) 배포 전 필수 설정(반드시 수정)

### 1-1. GA4 측정 ID 교체

`index.html`에서 `G-XXXXXXXXXX`를 실제 Measurement ID로 교체합니다.

```html
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
...
gtag('config', 'G-XXXXXXXXXX', { send_page_view: false });

→ 예시:
<script async src="https://www.googletagmanager.com/gtag/js?id=G-AB12CD34EF"></script>
...
gtag('config', 'G-AB12CD34EF', { send_page_view: false });

또한 index.html 내 CONFIG가 있으면 같이 수정합니다.
var CONFIG = {
  GA4_ID:  'G-AB12CD34EF',     // 실제 GA4 ID
  EXP_ID:  'openclaw_v3v4',    // 실험명(필터링/분석용)
  PAGE_ID: 'openclaw_lp',      // 페이지 식별자
  // ...
};

Formspree에서 폼을 만들면 엔드포인트가 생성됩니다.
index.html의 아래 값을 교체하세요.
var CONFIG = {
  // ...
  FORMSPREE_ENDPOINT: "https://formspree.io/f/REPLACE_ME"
};
Formspree 폼 설정에서 email(필수), phone(필수), message(선택) 를 받습니다.
스팸 방지용으로 _gotcha(honeypot) 필드도 함께 전송합니다.

cd cf-pages
python -m http.server 8080
# http://localhost:8080

| URL                                       | 동작                           |
| ----------------------------------------- | ---------------------------- |
| `http://localhost:8080/?var=A`            | A 강제                         |
| `http://localhost:8080/?var=B`            | B 강제                         |
| `http://localhost:8080/?debug=true`       | 핫스팟 시각화(점선) + GA4 debug_mode |
| `http://localhost:8080/?var=A&debug=true` | A + 디버그                      |


정상 동작 체크

페이지 로드 시 콘솔에 lp_impression 로그 (구현돼있다면)

CTA 영역 클릭 시 모달이 열리고 lp_cta_click 이벤트 전송 로그

폼 제출 성공 시 “접수 완료” 표시 + lp_reserve_submit 이벤트 전송 로그

3) Cloudflare Pages 배포(권장)
방법 A — GitHub 연동 자동 배포 (실전 권장)

Cloudflare Dashboard → Pages → Create a project

GitHub 레포 연결

설정

Framework preset: None

Build command: 비움

Output directory:

레포 루트가 곧 cf-pages/라면: /

레포 안에 cf-pages/ 폴더가 따로 있다면: cf-pages

main 브랜치에 머지하면 자동 배포

배포가 끝나면 https://xxxx.pages.dev 주소로 접속 확인

이후 GA4 웹 스트림 설정의 “웹사이트 URL”에는 이 배포 주소를 넣습니다.

4) A/B 라우팅 규칙

?var=A 또는 ?var=B가 있으면 강제

없으면 최초 방문 시 랜덤(A/B 50:50)

할당된 var는 localStorage + cookie로 30일 고정

실험을 바꿀 때는 EXP_ID를 변경하고(예: openclaw_v5v6),
필요하면 쿠키 키/스토리지 키도 바꾸면 깔끔합니다.

5) GA4 이벤트 스펙
| 이벤트명                | 발생 시점                  | 주요 파라미터                                            |
| ------------------- | ---------------------- | -------------------------------------------------- |
| `lp_impression`     | 페이지 로드 완료              | `exp_id`, `var`, `page_id`                         |
| `lp_cta_click`      | CTA hotspot 클릭         | `exp_id`, `var`, `page_id`, `cta_id`, `section_id` |
| `lp_reserve_submit` | Formspree AJAX 성공 응답 후 | `exp_id`, `var`, `page_id` *(PII 금지)*              |

GA4 DebugView 보기(권장)

URL에 ?debug=true로 접속하면 debug_mode가 켜지도록 구현하는 것을 권장합니다.

GA4 → [관리] → [DebugView]에서 실시간 이벤트 확인

주의: debug=true는 “핫스팟 시각화” + “debug_mode 활성화” 용입니다.
실사용 트래픽에서는 붙이지 않습니다.

6) GA4 맞춤 정의(필수: A/B 분석용)

GA4에서 A/B 비교를 편하게 하려면, 이벤트 파라미터를 맞춤 측정기준으로 등록하세요.

GA4 → 관리 → 맞춤 정의 → 맞춤 측정기준 만들기

이름: ab_variant

범위: 이벤트

이벤트 매개변수: var

(선택) 실험명도 보고 싶으면:

이름: experiment_id

범위: 이벤트

이벤트 매개변수: exp_id

7) A/B 결과 보는 법(탐색)

GA4 → 탐색 → 자유형식

측정기준: ab_variant(=var)

측정항목:

이벤트 수(lp_cta_click)

이벤트 수(lp_reserve_submit)

계산:

전환율 = reserve_submit / impression (또는 reserve_submit / cta_click)

트래픽이 적으면 하루 단위로 흔들립니다. 최소 5~7일 단위로 보세요.

8) 핫스팟 좌표 조정(버튼 위치 안 맞을 때)

?debug=true로 초록 점선이 보이게 한 뒤, hotspots.json의 값을 조정합니다.

권장 포맷: 숫자(%) 로 통일
[
  {
    "id": "hero_cta",
    "cta_id": "hero_cta",
    "section_id": "01_hero",
    "left": 34,
    "top": 18.2,
    "width": 32,
    "height": 6
  }
]
left/top/width/height는 %

모바일에서 오탭이 있으면 영역을 시각 버튼보다 조금 넓게 잡으세요.

9) 보안/운영 팁

GA4에는 PII(이메일/전화/메시지) 절대 전송 금지

Formspree에는 스팸 방지:

_gotcha honeypot 필드 사용(권장)

제출량이 늘면 Formspree 플랜/레이트리밋 검토


10) 문제 해결
(1) 클릭은 되는데 GA4 이벤트가 안 찍힘

Measurement ID 교체 누락 확인

브라우저 콘솔 에러 확인

GA4 DebugView에서 이벤트가 들어오는지 확인(디버그 모드)

(2) submit은 했는데 reserve_submit이 안 찍힘

Formspree endpoint 오타 확인

AJAX 성공 응답(200/OK) 뒤에만 이벤트를 보내는지 확인

(3) 모바일에서 클릭 영역이 어긋남

핫스팟 좌표 기준이 이미지 컨테이너(상대 좌표)인지 확인

hotspots.json의 top/height 재조정

참고

A/B는 “한 URL + var 파라미터” 방식으로 운영합니다.

Cloudflare Pages 배포 URL(예: pages.dev)이 GA4 웹 스트림의 website URL이 됩니다.