"""
OpenClaw Quant API 상세페이지 생성 스크립트
퀀트 자동매매 데이터 파이프라인 — 월 4만 원 사전예약
다크 트레이딩 터미널 스타일 커스텀 프롬프트 사용
"""

import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.gemini_api import generate_image, test_api_connection
from scripts.stitch_images import stitch_from_directory, create_preview

# ── 공통 스타일 앵커 ─────────────────────────────────────────────────────────
STYLE_ANCHOR = """
=== CRITICAL DIMENSION REQUIREMENTS ===
1. EXACT WIDTH: Image must be EXACTLY 1200px wide
2. FULL BLEED: Content fills ENTIRE 1200px — NO side margins
3. HIGH QUALITY: Sharp, crisp, professional rendering

=== DESIGN STYLE (MANDATORY — FOLLOW STRICTLY) ===
- Aesthetic: Dark quantitative finance / algorithmic trading terminal
- Primary background: Very dark navy-black (#0A0F1E or #070B14)
- Accent colors: Electric cyan (#00D4FF), Neon green (#00FF7F), Amber (#F59E0B)
- Typography: Monospace code font for data/numbers, bold sans-serif for headlines
- Data visualization: Charts, candlestick patterns, live feed tickers, API JSON snippets
- Grid lines: Subtle dark grid overlay like a Bloomberg terminal
- Glow effects: Cyan/green neon glow on key elements
- Style reference: Bloomberg Terminal, TradingView dark mode, Binance Pro interface
- Korean text: Bold white or cyan headlines, gray body text

=== DO NOT ===
- No light/white backgrounds (this is a dark-themed product)
- No generic clipart or cartoons
- No cheerful consumer app style
- No English-only text (Korean is primary)
"""

# ── 13개 섹션 커스텀 프롬프트 ──────────────────────────────────────────────

SECTION_PROMPTS = {

    "01_hero": {
        "prompt": f"""Create a hero section for a Korean quantitative trading API product landing page.
Dimensions: 1200x850 pixels.
{STYLE_ANCHOR}

Background: Very dark navy (#0A0F1E) with subtle animated-looking grid lines.
Background elements: Faint candlestick chart and line graphs in the background (very subtle, like ghost data).

Layout:
- Top-left: "OpenClaw" logo — stylized text with a claw/talon icon in cyan
- Top-right: "사전예약하기" button — bright cyan (#00D4FF), pill shape, glowing border

- Center-left text block:
  Small label above: "QUANT DATA API — EARLY BIRD" in cyan monospace, small caps
  Main headline (white, very large, bold):
    "월 100만 원 전문가용"
    "퀀트 데이터, 이제"
    "월 4만 원에 정복하세요"
    Highlight "월 4만 원" in bright cyan glow

  Subtext (light gray):
    "수치 데이터부터 실시간 비트코인 뉴스까지,"
    "자동매매 파이프라인을 위한 가장 날카로운 도구."

  Two CTA buttons:
    Primary: "지금 사전예약하기" — cyan background, dark text, glowing
    Secondary: "API 문서 보기 →" — transparent, cyan outline

- Center-right: A sleek dark terminal/dashboard mockup showing:
  A dark monitor screen with:
    - Real-time Bitcoin price ticker at top
    - Candlestick chart with cyan line overlay
    - A JSON data feed panel showing structured OHLCV + news data
    - Small "LIVE" red indicator blinking
    - Code snippet: {{ "price": 68420, "news_sentiment": 0.87, "signal": "BUY" }}

- Bottom: Subtle data stream scrolling text in very faint green (matrix-like but subtle)

Mood: Powerful, technical, premium, exclusive. Like owning a Bloomberg terminal for 40,000 won.
""",
        "width": 1200,
        "height": 850,
        "filename": "01_hero.png"
    },

    "02_pain": {
        "prompt": f"""Create a pain points section for a Korean quant trading API landing page.
Dimensions: 1200x640 pixels.
{STYLE_ANCHOR}

Background: Dark navy (#0D1321) — slightly lighter than hero

Layout:
- Top center: Section label "개인 투자자의 현실" in cyan small caps
- Headline: "왜 개인 투자자는 항상 뒤처질 수밖에 없을까요?" — white, bold, large

- Center: 3 dark cards in horizontal row (dark gray #1A2035 background, subtle cyan border):

  Card 1 — "비용의 벽":
    Icon: Wall/barrier icon with dollar signs, red/orange tint
    Title: "연 1,200만 원의 데이터 비용" (amber color)
    Number callout: "₩1,200만" — large, red, monospace font
    Text: "전문가급 퀀트 데이터를 구독하려면 월 100만 원이 넘는 비용이 필요합니다. 개인 투자자에게는 현실적으로 불가능한 진입장벽입니다."

  Card 2 — "데이터의 파편화":
    Icon: Broken chart / fragmented data icon, orange tint
    Title: "차트만 봐서는 놓치는 것들" (amber color)
    Text: "비트코인 가격이 급락하는 순간, 그 원인은 뉴스였습니다. 수치 데이터만 보는 퀀트 엔진은 이 맥락을 영원히 알 수 없습니다."

  Card 3 — "복잡한 가공":
    Icon: Gear/code processing icon, orange tint
    Title: "데이터 전처리에 낭비되는 시간" (amber color)
    Text: "원천 데이터를 매매 엔진에 먹이려면 수십 시간의 전처리 작업이 필요합니다. 매매는 언제 하실 건가요?"

- Bottom: A subtle horizontal data ticker strip (price feeds scrolling) as separator

Background has very faint grid lines for terminal aesthetic.
""",
        "width": 1200,
        "height": 640,
        "filename": "02_pain.png"
    },

    "03_problem": {
        "prompt": f"""Create a problem analysis section for a Korean quant trading landing page.
Dimensions: 1200x520 pixels.
{STYLE_ANCHOR}

Background: Very dark (#070B14)

Layout:
- Top: Headline "개인 투자자와 기관 사이의 '정보 격차'" — white, bold
- Below: Subtext "문제는 실력이 아닙니다. 도구의 차이입니다." — cyan, slightly smaller

- Center: A visual comparison diagram — dark infographic style:

  LEFT SIDE — "기관/전문 투자자" (blue glow):
    Stack of icons/cards showing:
    ✅ 실시간 뉴스 데이터 피드
    ✅ OHLCV 정밀 수치 데이터
    ✅ 전처리 완료된 학습 데이터셋
    ✅ 자동매매 엔진 직결
    Label: "월 100만 원~" in small amber text

  CENTER: VS divider with lightning bolt icon, glowing

  RIGHT SIDE — "개인 투자자" (dim, gray):
    Stack showing:
    ❌ 뉴스는 직접 크롤링
    ❌ 데이터는 파편화
    ❌ 전처리에 수십 시간
    ❌ 수동 매매로 대응
    Label: "기회 손실" in red text

  BELOW diagram: Arrow pointing down to a glowing box:
    "OpenClaw가 이 격차를 월 4만 원으로 메웁니다"
    In bright cyan with subtle glow effect

Dark terminal style, clean infographic
""",
        "width": 1200,
        "height": 520,
        "filename": "03_problem.png"
    },

    "04_story": {
        "prompt": f"""Create a before/after transformation story section for a quant trading landing page.
Dimensions: 1200x700 pixels.
{STYLE_ANCHOR}

Background: Dark navy split layout

Layout: Two panels side by side with vertical divider

LEFT PANEL — "OpenClaw 없이" (slightly dimmer, red/gray tint):
  Top label: "BEFORE" in small monospace, dim red
  Icon: Frustrated developer at multiple screens

  Timeline showing painful workflow:
    ① "거래소 API → 가격 데이터 수집" (clock: 2h)
    ② "뉴스 크롤러 직접 개발/운영" (clock: 5h)
    ③ "두 데이터 형식 맞춰 병합" (clock: 3h)
    ④ "전처리 → 정규화 → 결측 처리" (clock: 4h)
    ⑤ "드디어 매매 로직 개발 시작..." (clock: 지쳐있음)

  Bottom: Total time indicator "주당 14시간 낭비" in red

RIGHT PANEL — "OpenClaw 사용 후" (bright, cyan/green glow):
  Top label: "AFTER" in small monospace, bright cyan
  Icon: Clean dashboard, single API call

  Clean workflow:
    ① "OpenClaw API 엔드포인트 호출" (1 line of code)
    ② "OHLCV + 뉴스 감성 통합 데이터 수신" (즉시)
    ③ "자동매매 엔진에 바로 주입" (즉시)
    ④ "매매 실행" ✅

  Code snippet mockup:
    response = openclaw.get_hybrid_data("BTC")
    engine.feed(response.dataset)  # 완료

  Bottom: "주당 14시간 → 10분" in bright green, large

Center divider: Arrow pointing right with "OpenClaw" label
""",
        "width": 1200,
        "height": 700,
        "filename": "04_story.png"
    },

    "05_solution": {
        "prompt": f"""Create a solution introduction section for a quant trading landing page.
Dimensions: 1200x440 pixels.
{STYLE_ANCHOR}

Background: Very dark (#070B14) with radial cyan glow in center (subtle)

Layout (centered, bold, impactful):
- Small label above: "THE SOLUTION" in cyan monospace small caps
- Large product name: "OpenClaw" — very large, white, bold
  With a stylized claw/talon icon integrated into the lettering, in cyan
- Below: Tagline in light gray:
  "퀀트 엔진이 바로 학습할 수 있는 '기계적 데이터'를 제공합니다"
- Below: Three feature badges in a dark row:
  [🦾 Hybrid Dataset]  [⚡ Auto-Trade Ready]  [💸 월 4만 원]
  Each badge: dark card with cyan border, white text

- Bottom right: Small JSON code block in dark terminal style:
  {{
    "symbol": "BTC/USDT",
    "ohlcv": {{ "o":68000, "h":69200, "l":67800, "c":68420, "v":1204.5 }},
    "news_sentiment": 0.87,
    "signal": "BULLISH",
    "timestamp": "2026-02-28T09:00:00Z"
  }}
  With syntax highlighting (cyan keys, green values)

Powerful, clean, technical product reveal moment
""",
        "width": 1200,
        "height": 440,
        "filename": "05_solution.png"
    },

    "06_how_it_works": {
        "prompt": f"""Create a "how it works" technical process section for a quant trading landing page.
Dimensions: 1200x620 pixels.
{STYLE_ANCHOR}

Background: Dark navy (#0D1321)

Layout:
- Top center: Section label "HOW IT WORKS" in cyan monospace
- Headline: "OpenClaw의 3가지 핵심 엔진" — white, bold
- Subtext: "수집부터 자동매매 주입까지, 단 하나의 API 호출로" — gray

- Center: 3-step horizontal process with connecting glowing lines:

  Step 1 — "🦾 CLAW (수집)":
    Icon: Spider/claw web icon in cyan
    Title: "실시간 데이터 클로우링"
    Description:
      "비트코인 관련 뉴스, SNS 이슈, 시장 급변 이벤트를
       실시간으로 자동 수집합니다.
       OHLCV 가격 데이터와 동시에 처리됩니다."
    Visual: Small feed animation showing news headlines + price ticks

  → Glowing arrow →

  Step 2 — "⚡ CONVERT (변환)":
    Icon: Transform/processor icon in amber
    Title: "기계 학습용 데이터로 즉시 변환"
    Description:
      "수집된 텍스트 데이터를 감성 점수(Sentiment Score)와
       벡터값으로 변환합니다.
       수치 데이터와 완벽하게 병합·정규화됩니다."
    Visual: Data transformation diagram (text → numbers)

  → Glowing arrow →

  Step 3 — "🚀 DELIVER (전달)":
    Icon: API/rocket icon in green
    Title: "자동매매 파이프라인에 즉시 주입"
    Description:
      "REST API 한 번의 호출로 Hybrid Dataset을 수신합니다.
       별도 전처리 없이 바로 퀀트 엔진에 넣을 수 있습니다."
    Code: response = openclaw.get('BTC')  # 끝

- Bottom: Glowing separator line with data ticker

Dark terminal aesthetic, technical but clear
""",
        "width": 1200,
        "height": 620,
        "filename": "06_how_it_works.png"
    },

    "07_social_proof": {
        "prompt": f"""Create a social proof section for a quant trading API landing page.
Dimensions: 1200x760 pixels.
{STYLE_ANCHOR}

Background: Dark (#0A0F1E)

Layout:
- Top: 3 stats in a glowing dark stat bar:
  "96% 비용 절감"  |  "2종 데이터 완벽 융합"  |  "사전예약 진행 중"
  Each stat: Large bold number/text in cyan, description in gray

- Section headline: "이미 예약한 개발자들의 이야기" — white bold

- 3 testimonial cards (dark card #1A2035, cyan-glow left border):

  Card 1:
    Quote symbol in cyan
    Text: "개인이 뉴스 크롤러 직접 개발하고 유지보수하는 비용이 얼마인지 아세요? 이거 하나면 그 모든 게 필요 없어요."
    Name: "김 ** 님"
    Role: "개인 퀀트 트레이더"
    Badge: "개발 비용 90% 절감" in green

  Card 2:
    Quote symbol in cyan
    Text: "OHLCV에 뉴스 감성 점수가 통합된 데이터셋이 이 가격에 나온다는 게 믿기지 않았습니다. 직접 만들면 수백 시간인데."
    Name: "박 ** 님"
    Role: "핀테크 스타트업 개발자"
    Badge: "개발 기간 3개월 단축" in green

  Card 3:
    Quote symbol in cyan
    Text: "뉴스 이벤트 감지가 자동매매 정확도에 미치는 영향이 이렇게 클 줄 몰랐습니다. 데이터가 전략을 바꿨습니다."
    Name: "이 ** 님"
    Role: "알고리즘 트레이딩 연구자"
    Badge: "전략 정확도 향상" in green

- Bottom: "지금도 예약이 접수되고 있습니다" with pulsing dot indicator

Dark, premium, credible technical community feel
""",
        "width": 1200,
        "height": 760,
        "filename": "07_social_proof.png"
    },

    "08_authority": {
        "prompt": f"""Create an authority/about section for a quant trading API landing page.
Dimensions: 1200x480 pixels.
{STYLE_ANCHOR}

Background: Dark navy (#0D1321)

Layout: Two columns

Left column (45%):
  - "OpenClaw" logo mark, large
  - Tagline: "Claw the Alpha" — in cyan italic
  - 3 credential badges (dark cards, cyan icon):
    📡 "실시간 데이터 수집 특화"
    🤖 "ML 즉시 적용 가능한 구조"
    🔐 "API 기반 안정적 데이터 전달"

Right column (55%):
  - Section label: "OpenClaw 소개" in cyan small monospace
  - Headline: "퀀트 투자자를 위해\n처음부터 설계된 데이터 파이프라인" — white bold
  - Body text (gray):
    "OpenClaw는 개인 투자자와 기관 사이의 '데이터 격차'를 해소하기 위해 만들어졌습니다.
     수치 데이터와 텍스트 데이터를 하나의 파이프라인으로 통합하여,
     복잡한 전처리 없이 자동매매 엔진에 바로 연결할 수 있습니다."
  - Bottom: A mini architecture diagram showing:
    [News Sources] + [Exchange API] → [OpenClaw Engine] → [Your Bot]
    Connected with glowing arrows in cyan

Technical, credible, developer-facing authority
""",
        "width": 1200,
        "height": 480,
        "filename": "08_authority.png"
    },

    "09_benefits": {
        "prompt": f"""Create a features and unique selling points section for a quant trading landing page.
Dimensions: 1200x720 pixels.
{STYLE_ANCHOR}

Background: Very dark (#070B14)

Layout:
- Top: Headline "OpenClaw만의 3가지 차별점" — white bold
- Subtext: "다른 데이터 서비스와 근본적으로 다릅니다" — gray

- Center: 3 large feature cards vertically or in 3-column layout:

  Feature Card 1 — "Hybrid Dataset" (most prominent):
    Top: "01" in large cyan monospace
    Title: "Hybrid Dataset — 완벽한 융합" — white bold
    Icon/Visual: Venn diagram of "수치 데이터 (OHLCV)" ∩ "텍스트 데이터 (News/Social)"
    Description: "가격 데이터(시가·고가·저가·종가·거래량)와 비트코인 관련 뉴스·소셜 데이터를 하나의 정규화된 데이터셋으로 제공합니다. 두 데이터를 직접 병합하는 수십 시간의 작업이 사라집니다."
    Tags: [OHLCV] [Sentiment] [Normalized]

  Feature Card 2 — "Auto-Trade Ready":
    Top: "02" in cyan monospace
    Title: "Auto-Trade Ready — 즉시 주입 가능"
    Visual: Arrow from API → to robot/engine icon
    Description: "수집된 데이터는 별도 전처리 없이 자동매매 파이프라인에 바로 주입할 수 있는 '기계적 데이터' 형태입니다. 퀀트 엔진이 즉시 학습하고 실행할 수 있습니다."
    Code snippet: engine.train(openclaw.get_dataset())
    Tags: [REST API] [ML-Ready] [Real-time]

  Feature Card 3 — "Pre-order Benefit":
    Top: "03" in amber monospace
    Title: "Pre-order Benefit — 96% 절감"
    Visual: Price comparison — ₩1,000,000 (strikethrough red) → ₩40,000 (large green)
    Description: "사전예약 기간 한정으로 전문가급 솔루션 대비 96% 저렴한 월 4만 원에 이용 가능합니다. 이 혜택은 사전예약 인원 달성 시 예고 없이 종료됩니다."
    Tags: [Early Bird] [한정 혜택] [⚠️ 곧 종료]

Dark, technical, premium feature showcase
""",
        "width": 1200,
        "height": 720,
        "filename": "09_benefits.png"
    },

    "10_risk_removal": {
        "prompt": f"""Create a risk removal / FAQ section for a quant trading API landing page.
Dimensions: 1200x500 pixels.
{STYLE_ANCHOR}

Background: Dark navy (#0D1321)

Layout:
- Top center: Shield icon in cyan with glow
- Headline: "자주 묻는 질문들" — white bold

- 2-column FAQ grid (4 items):

  Q1: "어떤 데이터를 제공하나요?"
  A1: "비트코인(BTC/USDT) OHLCV 가격 데이터와 실시간 뉴스·소셜 감성 데이터를 통합한 Hybrid Dataset을 제공합니다."

  Q2: "자동매매 시스템에 바로 연결 가능한가요?"
  A2: "네. REST API 한 번의 호출로 전처리 완료된 데이터를 수신하며, 별도 가공 없이 퀀트 엔진에 주입 가능합니다."

  Q3: "사전예약 혜택은 언제 끝나나요?"
  A3: "사전예약 목표 인원 달성 시 예고 없이 종료됩니다. 정식 출시 후 가격은 변경될 수 있습니다."

  Q4: "개발 경험이 없어도 사용할 수 있나요?"
  A4: "Python 기본 지식으로 API 호출이 가능합니다. 상세한 문서와 예제 코드를 제공합니다."

- Bottom: 3 guarantee badges in dark cards:
  🔒 "안정적인 API SLA 보장"
  📄 "상세 API 문서 제공"
  💬 "개발자 전용 지원 채널"

Each FAQ card: dark background #1A2035, cyan left border, clean layout
""",
        "width": 1200,
        "height": 500,
        "filename": "10_risk_removal.png"
    },

    "11_comparison": {
        "prompt": f"""Create a price and value comparison section for a quant trading landing page.
Dimensions: 1200x440 pixels.
{STYLE_ANCHOR}

Background: Very dark (#070B14)

Layout:
- Top: Headline "비용 비교" — white bold
- Subtext: "같은 퀄리티, 96% 저렴하게" — cyan

- Center: Large comparison table — terminal style with grid lines:

  Columns:
    Col 1 (dim gray): "타사 전문가용 서비스"
    Col 2 (HIGHLIGHTED — cyan glow border): "OpenClaw Early Bird" + "⭐ 추천" badge
    Col 3 (dim gray): "직접 구축"

  Rows (feature items):
    "하이브리드 데이터셋" → ✅ / ✅ / ⚠️ 수개월 작업
    "자동매매 즉시 연결" → ✅ / ✅ / ❌ 별도 개발 필요
    "실시간 뉴스 감성" → ✅ / ✅ / ❌
    "전처리 완료" → ✅ / ✅ / ❌
    "월 비용" → ₩1,000,000 (red) / ₩40,000 (large green, bold) / ₩수백만 (dev cost)

  OpenClaw column:
    - Cyan glow highlight on entire column
    - "Early Bird" amber badge at top
    - Price: "₩40,000" in very large green monospace font

- Below table: "같은 전문가급 데이터, 96% 저렴하게 — 지금만 가능합니다" — cyan centered

Dark terminal table style, numbers in monospace
""",
        "width": 1200,
        "height": 440,
        "filename": "11_comparison.png"
    },

    "12_target_filter": {
        "prompt": f"""Create a target audience filter section for a quant trading API landing page.
Dimensions: 1200x420 pixels.
{STYLE_ANCHOR}

Background: Dark navy (#0D1321)

Layout: Two columns

Left column — "이런 분께 최적입니다" — cyan/green theme:
  Green-glowing header with checkmark icon
  List with ✅ icons (monospace terminal style):
    ✅ 자동매매 파이프라인을 구축 중인 개발자
    ✅ 뉴스/감성 데이터를 전략에 활용하고 싶은 퀀트 투자자
    ✅ 데이터 수집·전처리 비용을 줄이고 싶은 분
    ✅ 월 100만 원이 부담스러운 개인 투자자
    ✅ Python으로 API 호출이 가능한 분

Right column — "이런 분은 맞지 않을 수 있습니다" — dim gray theme:
  Gray header with X icon
  List with ❌ icons:
    ❌ 차트 분석만으로 충분하신 분
    ❌ 자동화 없이 수동 매매만 하시는 분
    ❌ 비트코인 외 다른 자산만 거래하시는 분 (현재 BTC 특화)
    ❌ API 사용 경험이 전혀 없으신 분

- Bottom center glowing line:
  "해당되신다면 — 사전예약 마감 전에 지금 신청하세요 →" in cyan

Terminal-style bullet points, dark atmosphere
""",
        "width": 1200,
        "height": 420,
        "filename": "12_target_filter.png"
    },

    "13_final_cta": {
        "prompt": f"""Create a final call-to-action section for a quant trading API landing page.
Dimensions: 1200x620 pixels.
{STYLE_ANCHOR}

Background: Very dark (#070B14) with powerful radial cyan glow emanating from center.
Background: Faint candlestick chart ghost pattern in background.

Layout (fully centered, maximum impact):
- Small label: "⚠️ 사전예약 한정 혜택" in amber pill badge with pulsing border
- Large headline (white, very bold, largest text on page):
  "지금 바로 OpenClaw 사전예약하고"
  "퀀트 투자의 격차를 줄이세요"
  The word "격차" in cyan with glow

- Price display:
  타사 정가: "₩1,000,000 / 월" — red strikethrough, small
  OpenClaw Early Bird: "₩40,000 / 월" — huge, neon green, monospace, glowing
  Savings badge: "96% 절감" in amber

- Primary CTA button (very large, neon cyan, glowing effect):
  "사전예약 신청하기"
  Subtext below button: "사전예약 인원 달성 시 예고 없이 종료됩니다"

- Below button: 3 trust items (small, subtle):
  "⚡ 즉시 API 문서 제공"  |  "🔒 안정적 SLA"  |  "🤝 개발자 지원 채널"

- Very bottom: "openclaw.io" in very faint gray monospace

Mood: Urgent, powerful, exclusive. The most impactful moment of the page.
The cyan glow should make the CTA feel electric and unmissable.
""",
        "width": 1200,
        "height": 620,
        "filename": "13_final_cta.png"
    }
}

OUTPUT_DIR = PROJECT_ROOT / "output" / "openclaw"
SECTIONS_DIR = OUTPUT_DIR / "sections"


def run():
    print("=" * 60)
    print("OpenClaw Quant API 상세페이지 생성")
    print("퀀트 자동매매 데이터 파이프라인 - 월 4만 원 사전예약")
    print("=" * 60)

    SECTIONS_DIR.mkdir(parents=True, exist_ok=True)

    # API 연결 테스트
    print("\nAPI 연결 테스트 중...")
    if not test_api_connection():
        print("API 연결 실패. GEMINI_API_KEY를 확인하세요.")
        return None

    # 13개 섹션 이미지 생성
    print(f"\n총 {len(SECTION_PROMPTS)}개 섹션 이미지 생성 시작...")
    failed = []

    for i, (key, data) in enumerate(SECTION_PROMPTS.items(), 1):
        print(f"\n{'='*50}")
        print(f"[{i}/{len(SECTION_PROMPTS)}] {key} 생성 중...")
        print(f"{'='*50}")

        output_path = str(SECTIONS_DIR / data["filename"])
        result = generate_image(
            prompt=data["prompt"],
            output_path=output_path,
            width=data["width"],
            height=data["height"]
        )

        if not result:
            print(f"  ⚠️ 실패: {key}")
            failed.append(key)

        if i < len(SECTION_PROMPTS):
            print("  3초 대기 중...")
            time.sleep(3)

    # 스티칭
    print("\n" + "=" * 50)
    print("최종 페이지 스티칭...")
    print("=" * 50)

    final_png = str(OUTPUT_DIR / "final_page.png")
    final_pdf = str(OUTPUT_DIR / "final_page.pdf")
    preview   = str(OUTPUT_DIR / "preview.png")

    result = stitch_from_directory(str(SECTIONS_DIR), final_png)
    if result:
        stitch_from_directory(str(SECTIONS_DIR), final_pdf)
        create_preview(final_png, preview, max_height=2000)

        print("\n" + "=" * 50)
        print("완료!")
        print("=" * 50)
        print(f"PNG:     {final_png}")
        print(f"PDF:     {final_pdf}")
        print(f"미리보기: {preview}")

        if failed:
            print(f"\n⚠️ 실패한 섹션: {', '.join(failed)}")

        return final_png

    return None


if __name__ == "__main__":
    run()
