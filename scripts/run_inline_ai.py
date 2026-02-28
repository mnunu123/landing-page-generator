"""
inline AI 상세페이지 생성 스크립트
한글 문서 위에 바로 써주는 AI 비서 — https://www.inline-ai.com/
소프트웨어 SaaS 제품 전용 커스텀 프롬프트 사용
"""

import os
import sys
import time
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.gemini_api import generate_image, test_api_connection
from scripts.stitch_images import stitch_from_directory, create_preview

# ── 공통 스타일 앵커 ─────────────────────────────────────────────────────────
STYLE_ANCHOR = """
=== CRITICAL DIMENSION REQUIREMENTS ===
1. EXACT WIDTH: Image must be EXACTLY 1200px wide
2. FULL BLEED: Content fills ENTIRE 1200px width — NO side margins
3. HIGH QUALITY: Sharp, professional, crisp rendering

=== DESIGN STYLE (MANDATORY) ===
- Clean, modern SaaS/tech product landing page aesthetic
- Dark navy (#111827) and vibrant blue (#2563EB) as main colors
- White backgrounds for light sections, dark navy for accent sections
- Professional Korean typography (Pretendard-style: bold headlines, clean body)
- Flat/semi-flat illustration style mixed with realistic UI screenshot mockups
- Inspired by: Notion, Linear, Figma landing page design quality

=== DO NOT ===
- No cheesy stock photos of people pointing at screens
- No generic clipart or cartoon characters
- No overly busy or cluttered layout
- No English-only text (Korean text is primary)
"""

# ── 13개 섹션 커스텀 프롬프트 ──────────────────────────────────────────────

SECTION_PROMPTS = {

    "01_hero": {
        "prompt": f"""Create a hero section for a Korean SaaS product landing page.
Dimensions: 1200x820 pixels.
{STYLE_ANCHOR}

Background: Deep dark navy (#111827) gradient to slightly lighter navy.
Optional subtle grid or dot pattern overlay (very subtle, near invisible).

Layout:
- Top-left: "inline AI" logo text in white, small and clean
- Top-right: "무료로 시작하기" button in blue (#2563EB), pill shape
- Center: Large bold Korean headline (white text):
  Main: "한글 문서 위에 바로 써주는"
  Sub: "AI 비서"  ← this part in blue (#3B82F6)
- Below headline: Subtext in light gray:
  "복붙 없이, 창 전환 없이 — 한글 안에서 AI와 바로 대화하세요"
- Below subtext: Two CTA buttons side by side:
  Primary: "지금 무료로 설치하기" (bright blue, rounded)
  Secondary: "데모 보기 →" (transparent outline, white text)
- Right side or bottom center: A clean mockup showing:
  A laptop screen with a Korean HWP document open
  On the right side of the document: A sleek AI chat panel (dark sidebar)
  In the chat: Korean text conversation with AI writing suggestions
  Document showing Korean text being edited in real-time

Badge top-right of mockup: "한글 연동 지원" in blue pill badge

Mood: Premium, trustworthy, cutting-edge tech. Like a top-tier SaaS product.
""",
        "width": 1200,
        "height": 820,
        "filename": "01_hero.png"
    },

    "02_pain": {
        "prompt": f"""Create a pain points section for a Korean SaaS landing page.
Dimensions: 1200x620 pixels.
{STYLE_ANCHOR}

Background: Very light gray (#F9FAFB)

Layout:
- Top center: Small label badge "혹시 이런 경험 있으신가요?" in blue text
- Below: Section headline: "AI 쓰는데도 왜 문서 작업이 여전히 힘들까요?" (dark, bold)
- Center: 3 pain point cards in horizontal row, each card:
  - White background, subtle shadow
  - Rounded corners
  - Icon at top (frustrated emoji style but clean/flat)
  - Bold Korean title
  - Short description text in gray

Card 1:
  Icon: Copy-paste icon (two overlapping documents)
  Title: "매번 복붙이 너무 번거로워요"
  Text: "ChatGPT 결과를 한글로 붙여넣고, 수정하고, 또 복붙하고... 끝이 없습니다"

Card 2:
  Icon: Split-screen / switching tabs icon
  Title: "창 왔다갔다 하다가 집중력이 깨져요"
  Text: "AI 창, 한글 창, 자료 창... 3개 창을 번갈아 보다 보면 정작 글은 못 씁니다"

Card 3:
  Icon: Clock / hourglass icon
  Title: "양식 채우는 데 시간을 다 써요"
  Text: "공문 양식, 보고서 서식... 형식 맞추는 데만 1시간이 넘게 걸립니다"

Bottom: Small text "→ 이 문제, inline AI가 한 번에 해결합니다" in blue
""",
        "width": 1200,
        "height": 620,
        "filename": "02_pain.png"
    },

    "03_problem": {
        "prompt": f"""Create a problem analysis section for a Korean SaaS landing page.
Dimensions: 1200x500 pixels.
{STYLE_ANCHOR}

Background: White

Layout:
- Top center: Bold headline in dark navy:
  "문제는 도구가 아니라, '연결'이 없다는 것입니다"
- Below: Subtext in gray:
  "ChatGPT는 뛰어난 AI입니다. 한글도 훌륭한 문서 프로그램입니다.
   그런데 둘 사이에 다리가 없습니다."

- Center: A visual diagram showing:
  Left box (gray/muted): "ChatGPT / AI 도구" with AI icon
  Center: A broken/disconnected line or gap with "X" symbol, labeled "복붙 장벽"
  Right box (gray/muted): "한글(HWP) 문서" with document icon

  Below the gap: Arrow pointing down to a new row:
  A connected diagram showing:
  Left box (blue): "AI 채팅" → connected bridge → Right box (blue): "한글 문서"
  Label on bridge: "inline AI" in blue
  Label below: "직접 연결"

- Bottom text: "더 이상 두 창 사이를 오갈 필요가 없습니다" — clean, centered, confident tone

Clean infographic style, not photographic.
""",
        "width": 1200,
        "height": 500,
        "filename": "03_problem.png"
    },

    "04_story": {
        "prompt": f"""Create a before/after transformation section for a Korean SaaS landing page.
Dimensions: 1200x680 pixels.
{STYLE_ANCHOR}

Background: White with subtle divider

Layout: Two halves side by side

LEFT HALF — "Before" (muted, slightly gray toned):
  Top: Large label "inline AI 없이" with ❌ icon, text in gray
  Below: Timeline/steps showing painful workflow:
    Step 1: "한글에서 자료 파악" → copy text
    Step 2: "ChatGPT 창으로 이동" → paste, type request
    Step 3: "AI 결과 복사" → switch back to HWP
    Step 4: "한글에 붙여넣기" → adjust formatting
    Step 5: "마음에 안 들어서 반복..."
  Bottom stat: "평균 소요 시간: 2~3시간" in red/orange

Visual: Each step has small icon, connected by downward arrows, dull gray palette

RIGHT HALF — "After" (vibrant, clean, blue accented):
  Top: Large label "inline AI 사용 후" with ✅ icon, text in blue
  Below: Clean simplified workflow:
    Step 1: "한글 열기 → inline AI 자동 실행"
    Step 2: "AI에게 요청: '이 문서 요약해줘'"
    Step 3: "AI가 한글에 바로 작성 → 수락 클릭"
    Step 4: "완료 ✓"
  Bottom stat: "평균 소요 시간: 20분" in blue/green

CENTER: Vertical divider with arrow pointing right, labeled "변화"

Mood: Clear contrast — chaos vs. simplicity. The right side feels like relief.
""",
        "width": 1200,
        "height": 680,
        "filename": "04_story.png"
    },

    "05_solution": {
        "prompt": f"""Create a product introduction section for a Korean SaaS landing page.
Dimensions: 1200x420 pixels.
{STYLE_ANCHOR}

Background: Dark navy (#111827)

Layout (centered):
- Small label above: "솔루션 소개" in blue (#3B82F6) small caps
- Large product name: "inline AI" in white, very large, bold
- Below: Tagline in light gray: "한글 문서 위에 바로 써주는 AI 비서"
- Below tagline: Three feature badges in a row (pill shape, blue outline on dark bg):
  "한글 직접 연동"  |  "복붙 없이 즉시 반영"  |  "데이터 보안 최우선"
- Bottom: Clean mockup thumbnail — small preview of the inline AI panel inside HWP
  showing the AI chat sidebar, very clean and minimal

Optional: Subtle glow/radial gradient behind the product name

Clean, confident, minimal — like a premium SaaS product launch page
""",
        "width": 1200,
        "height": 420,
        "filename": "05_solution.png"
    },

    "06_how_it_works": {
        "prompt": f"""Create a "how it works" process section for a Korean SaaS landing page.
Dimensions: 1200x600 pixels.
{STYLE_ANCHOR}

Background: Light gray (#F3F4F6)

Layout:
- Top center: Section headline "3단계로 끝납니다" (bold, dark navy)
- Below: Subtext "설치부터 문서 완성까지, 복잡한 설정은 없습니다" (gray)
- Center: 3-step horizontal process with connecting arrows:

  Step 1 — Number circle "1" in blue:
    Icon: Plugin/connection icon
    Title: "한글 문서 연동"
    Description: "inline AI를 설치하면\n한글 문서를 열 때 자동으로 AI 패널이 활성화됩니다"

  → Arrow →

  Step 2 — Number circle "2" in blue:
    Icon: Chat bubble icon
    Title: "AI에게 요청"
    Description: "작성하거나 수정하고 싶은 내용을\n채팅창에 자유롭게 요청하세요.\n자료 파일이나 웹링크도 첨부 가능합니다"

  → Arrow →

  Step 3 — Number circle "3" in blue:
    Icon: Checkmark / accept icon
    Title: "수락 한 번으로 완료"
    Description: "AI가 제안한 내용을\n수락 버튼 하나로 한글에 바로 적용됩니다"

- Bottom: Small note "원하는 부분만 선택해서 수정도 가능합니다" in gray italic

Clean, clear, minimal SaaS how-it-works style
""",
        "width": 1200,
        "height": 600,
        "filename": "06_how_it_works.png"
    },

    "07_social_proof": {
        "prompt": f"""Create a social proof and testimonials section for a Korean SaaS landing page.
Dimensions: 1200x780 pixels.
{STYLE_ANCHOR}

Background: White

Layout:
- Top: Stats bar with 3 large metrics (dark bg strip or just white):
  "10배 빠른 작업속도"  |  "★ 4.9/5 만족도"  |  "문서 작업 시간 70% 단축"
  Each metric: Large bold number/text + small description below

- Section headline center: "실제 사용자들의 이야기" (dark navy, bold)
- Below: 3 testimonial cards in a row, each:
  White background, light border, rounded corners, subtle shadow
  Quote mark (") icon in blue at top
  Testimonial text in Korean (medium gray)
  Divider line
  Bottom: Avatar circle (colorful initials style) + Name + Job title + Result tag

  Card 1:
    Quote: "ChatGPT 쓸 때는 매번 복붙이 너무 귀찮았는데, inline AI는 한글 안에서 바로 돼서 진짜 편해요."
    Name: "김 ** 님"
    Job: "대기업 기획팀 과장"
    Result tag: "보고서 작성 70% 단축" (green badge)

  Card 2:
    Quote: "공문 양식 채우는 게 제일 오래 걸렸는데 이젠 10분이면 끝납니다. 팀 전체가 쓰고 있어요."
    Name: "박 ** 님"
    Job: "지방자치단체 행정직"
    Result tag: "주간 업무 시간 절반으로" (green badge)

  Card 3:
    Quote: "논문 초안 잡을 때 정말 유용해요. 문단 선택해서 수정 요청하면 바로 바꿔줍니다."
    Name: "이 ** 님"
    Job: "대학원생 (석사 과정)"
    Result tag: "리포트 4시간 → 40분" (green badge)

- Bottom: Star ratings row + "verified users" text in small gray
""",
        "width": 1200,
        "height": 780,
        "filename": "07_social_proof.png"
    },

    "08_authority": {
        "prompt": f"""Create an authority/about section for a Korean SaaS landing page.
Dimensions: 1200x480 pixels.
{STYLE_ANCHOR}

Background: Very light gray (#F9FAFB)

Layout: Two columns

Left column (40% width):
  - "inline AI" logo mark (simple text logo, clean)
  - Short tagline below
  - 3 trust badges/icons:
    🔒 "데이터 보안 최우선"
    🇰🇷 "한국 팀이 만든 한국어 특화 AI"
    ⚡ "즉시 사용 가능, 복잡한 설정 없음"

Right column (60% width):
  - Section label: "inline AI 소개" in small blue text
  - Headline: "한글 문서 사용자를 위해\n처음부터 다시 설계했습니다" (bold dark)
  - Body text (gray, 2-3 sentences):
    "수백만 명의 한국인이 매일 한글(HWP)로 문서를 작성합니다.
    그런데 기존 AI 도구들은 한글과 제대로 연동되지 않았습니다.
    inline AI는 이 문제를 해결하기 위해 태어났습니다."
  - Bottom: Small media/press logo placeholders or partner badges
    (simple gray boxes with "언론 보도", "파트너사" labels)

Clean, credible, startup-style but professional
""",
        "width": 1200,
        "height": 480,
        "filename": "08_authority.png"
    },

    "09_benefits": {
        "prompt": f"""Create a features and benefits section for a Korean SaaS landing page.
Dimensions: 1200x700 pixels.
{STYLE_ANCHOR}

Background: White

Layout:
- Top: Section headline "inline AI로 할 수 있는 것들" (bold, dark navy)
- Below headline: Subtext "8가지 핵심 기능으로 문서 작업을 완전히 바꿉니다" (gray)
- Center: 2x4 grid of feature cards (8 cards total), each:
  - Rounded card, light background (#F8FAFC), subtle border
  - Blue icon (flat, minimal) at top-left
  - Bold feature name
  - Short description in gray

  Feature cards:
  1. 🔗 한글 직접 연동 / "별도 복붙 없이 AI가 문서에 바로 씁니다"
  2. 💬 AI 채팅 인터페이스 / "자연어로 자유롭게 작성/수정 요청"
  3. 📎 파일·사진·링크 첨부 / "자료를 AI에게 직접 전달해 정확도 향상"
  4. ✅ 수락·거절 기능 / "AI 제안을 검토 후 한 번에 적용"
  5. ✏️ 부분 선택 수정 / "원하는 단락만 골라서 수정 가능"
  6. 📝 빈 양식 자동 채우기 / "보고서·공문 양식을 AI가 채워줍니다"
  7. 🔄 채팅·편집 모드 전환 / "상황에 맞게 두 가지 모드 활용"
  8. 🔒 데이터 보안 최우선 / "내 문서 내용은 외부로 유출되지 않습니다"

Cards arranged in 4 columns × 2 rows, uniform sizing, clean grid
""",
        "width": 1200,
        "height": 700,
        "filename": "09_benefits.png"
    },

    "10_risk_removal": {
        "prompt": f"""Create a risk removal / guarantee section for a Korean SaaS landing page.
Dimensions: 1200x480 pixels.
{STYLE_ANCHOR}

Background: White

Layout:
- Top center: Shield/lock icon in blue, large
- Headline: "걱정되는 것들, 모두 해결했습니다" (bold, dark navy)
- Center: 3 guarantee cards in a row:

  Card 1 — Security:
    Icon: Lock shield
    Title: "데이터 보안 최우선"
    Text: "내 문서 내용은 저장하거나 학습에 사용하지 않습니다"

  Card 2 — Free to start:
    Icon: Gift / no credit card
    Title: "신용카드 없이 무료 시작"
    Text: "설치 후 바로 사용 가능합니다. 숨겨진 비용이 없습니다"

  Card 3 — Support:
    Icon: Chat/headset
    Title: "한국어 전담 지원"
    Text: "문제가 생기면 한국어로 빠르게 도움드립니다"

- Below cards: FAQ section (accordion style visual):
  Q: "한글 프로그램이 꼭 설치되어 있어야 하나요?" → A: "네, 한글(HWP)과 연동됩니다"
  Q: "Mac에서도 사용할 수 있나요?" → A: "현재 Windows 우선 지원, Mac도 준비 중입니다"
  Q: "내 문서 내용이 AI 학습에 쓰이나요?" → A: "아니요, 사용자 데이터는 학습에 사용되지 않습니다"

Clean, reassuring, no-nonsense style
""",
        "width": 1200,
        "height": 480,
        "filename": "10_risk_removal.png"
    },

    "11_comparison": {
        "prompt": f"""Create a comparison section for a Korean SaaS landing page.
Dimensions: 1200x420 pixels.
{STYLE_ANCHOR}

Background: Very light gray (#F3F4F6)

Layout: Table comparison (3 options)

- Top: Headline "왜 inline AI인가요?" (bold, dark)
- Center: Comparison table with 3 columns:

  Column 1 — "기존 방식 (복붙)" — gray/muted theme:
  Column 2 — "inline AI" — blue/highlighted theme, slightly larger, with "추천" badge:
  Column 3 — "다른 AI 도구" — gray/muted theme:

  Row items:
  "한글(HWP) 직접 연동" → ❌ / ✅ / ❌
  "문서에 바로 반영" → ❌ / ✅ / ❌
  "복붙 필요 없음" → ❌ / ✅ ❌
  "한국어 특화" → ⚠️ 일부 / ✅ 완전 / ⚠️ 일부
  "무료로 시작" → ✅ / ✅ / ⚠️ 일부

- inline AI column has blue background highlight, bold text
- Bottom: "한글 사용자라면 선택지는 하나입니다" — bold, centered, blue

Clean SaaS comparison table style
""",
        "width": 1200,
        "height": 420,
        "filename": "11_comparison.png"
    },

    "12_target_filter": {
        "prompt": f"""Create a target audience filter section for a Korean SaaS landing page.
Dimensions: 1200x400 pixels.
{STYLE_ANCHOR}

Background: White

Layout: Two columns side by side

Left column — "이런 분께 딱 맞습니다" — green theme:
  - Green header bar with checkmark icon
  - List items with ✅ icons:
    ✅ 보고서·기획서를 자주 작성하는 직장인
    ✅ 공문·행정문서 작업이 많은 공무원
    ✅ 리포트·논문 초안을 써야 하는 학생
    ✅ 한글(HWP)을 주력으로 쓰는 분
    ✅ 문서 작성 시간을 줄이고 싶은 모든 분

Right column — "이런 분은 맞지 않을 수 있어요" — gray theme:
  - Gray header bar with X icon
  - List items with ❌ icons:
    ❌ 한글(HWP) 프로그램을 사용하지 않는 분
    ❌ Mac 전용 사용자 (현재 Windows 위주 지원)
    ❌ Word, Google Docs를 주로 쓰시는 분

- Bottom center: "해당되신다면, 지금 무료로 시작해보세요 →" in blue, clickable-looking

Honest, clear, professional filter style
""",
        "width": 1200,
        "height": 400,
        "filename": "12_target_filter.png"
    },

    "13_final_cta": {
        "prompt": f"""Create a final call-to-action section for a Korean SaaS landing page.
Dimensions: 1200x580 pixels.
{STYLE_ANCHOR}

Background: Deep dark navy (#111827) with subtle blue radial glow in center

Layout (fully centered):
- Small label: "지금 바로 시작하세요" in blue pill badge
- Large headline (white, very bold):
  "문서 작업, 더 이상 혼자 하지 마세요"
- Below: Subtext in light gray:
  "한글 문서 위에 AI 비서를 올려두세요.
   설치부터 첫 문서 완성까지, 20분이면 충분합니다."

- Primary CTA button (large, blue #2563EB, rounded, glowing):
  "지금 무료로 설치하기"
  Below button (tiny): "신용카드 불필요 · 즉시 사용 가능"

- Below button: 3 trust badges in a row (small, gray/subtle):
  "🔒 데이터 보안"  |  "⚡ 즉시 사용"  |  "🇰🇷 한국어 특화"

- Bottom: Small URL text "inline-ai.com" in very faint gray

Mood: Premium, confident, final push. Dark and impactful like the best SaaS landing pages.
Glow effect on CTA button. Stars or particle dots optional for premium feel.
""",
        "width": 1200,
        "height": 580,
        "filename": "13_final_cta.png"
    }
}

OUTPUT_DIR = PROJECT_ROOT / "output" / "inline_ai"
SECTIONS_DIR = OUTPUT_DIR / "sections"


def run():
    print("=" * 60)
    print("inline AI 상세페이지 생성")
    print("한글 문서 위에 바로 써주는 AI 비서")
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
