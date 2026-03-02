"""
상세페이지 전체 생성 파이프라인
입력 정보를 받아 최종 PNG/PDF까지 생성합니다.
"""

import os
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# 프로젝트 루트 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.gemini_api import generate_image, test_api_connection
from scripts.stitch_images import stitch_from_directory, create_preview


# 섹션별 기본 높이 (height_profile 기반으로 추상화)
SECTION_HEIGHTS = {
    "01_hero": 800,        # emphasis
    "02_pain": 580,        # standard
    "03_problem": 480,     # compact
    "04_story": 660,       # standard
    "05_solution": 400,    # compact
    "06_how_it_works": 580, # standard
    "07_social_proof": 780, # emphasis
    "08_authority": 460,   # standard
    "09_benefits": 660,    # standard
    "10_risk_removal": 460, # compact
    "11_comparison": 420,  # compact
    "12_target_filter": 400, # compact
    "13_final_cta": 620    # emphasis
}

# 높이 프로파일 매핑 (emphasis/standard/compact)
HEIGHT_PROFILE_MAP = {
    "emphasis": ["01_hero", "07_social_proof", "13_final_cta"],
    "standard": ["02_pain", "04_story", "06_how_it_works", "08_authority", "09_benefits"],
    "compact":  ["03_problem", "05_solution", "10_risk_removal", "11_comparison", "12_target_filter"],
}

# short 모드: 7개 핵심 전환 섹션
SHORT_MODE_SECTIONS = [
    "01_hero", "02_pain", "05_solution",
    "06_how_it_works", "07_social_proof",
    "10_risk_removal", "13_final_cta",
]


def create_sample_brief() -> Dict[str, Any]:
    """
    샘플 제품 정보 Brief를 생성합니다.
    """
    return {
        "product_name": "AI 마케팅 자동화",
        "one_liner": "광고비 50% 절감하는 AI 기반 마케팅 최적화 시스템",
        "target_audience": "월 광고비 100만원 이상 쓰는 스마트스토어 셀러",
        "main_problem": "광고 최적화에 하루 2시간 소비하면서도 ROAS는 제자리",
        "key_benefit": "AI가 24시간 자동으로 광고 최적화, 평균 광고비 50% 절감",
        "price": {
            "original": "199,000원",
            "discounted": "99,000원",
            "period": "월"
        },
        "urgency": {
            "type": "quantity",
            "value": "선착순 100명",
            "bonus": "1:1 셋업 컨설팅 무료"
        },
        "style_preset": "minimal",
        "brand_colors": {
            "primary": "#2563EB",
            "secondary": "#60A5FA",
            "accent": "#F59E0B"
        }
    }


def generate_section_prompts(brief: Dict[str, Any]) -> Dict[str, Dict]:
    """
    Brief 정보를 바탕으로 13개 섹션의 Gemini 프롬프트를 생성합니다.
    style_preset에 따라 배경색과 시각 언어를 자동 적용합니다.
    """
    style = brief.get("style_preset", "minimal")
    colors = brief.get("brand_colors", {})
    primary = colors.get("primary", "#2563EB")
    accent = colors.get("accent", "#F59E0B")

    product_name = brief.get("product_name", "제품명")
    one_liner = brief.get("one_liner", "제품 설명")
    target = brief.get("target_audience", "타겟 고객")
    problem = brief.get("main_problem", "해결하는 문제")
    benefit = brief.get("key_benefit", "핵심 혜택")
    price = brief.get("price", {})
    urgency = brief.get("urgency", {})

    # 도메인 컨텍스트 힌트 (optional — 있으면 시각 언어에 포함)
    ctx = brief.get("product_context", {})
    visual_hint = ""
    if ctx:
        cat = ctx.get("category", "")
        tech = ctx.get("target_tech", "")
        stats = ctx.get("pain_stats", "")
        proof = ctx.get("proof_stats", "")
        if cat:
            visual_hint += f"\nProduct category: {cat}"
        if tech:
            visual_hint += f"\nTech context: {tech}"
        if stats:
            visual_hint += f"\nKey stats: {stats}"
        if proof:
            visual_hint += f"\nProof data: {proof}"

    # ── 스타일별 배경색 팔레트 ──────────────────────────────────────────────
    STYLE_BG = {
        "minimal":   {"light": "#F3F4F6", "white": "#FFFFFF",  "dark": f"dark gradient {primary}", "card_border": "thin 1px, soft shadow"},
        "sales":     {"light": "#FEF3C7", "white": "#FFFBEB",  "dark": f"dark gradient {primary}", "card_border": "thin 1px, slight warm shadow"},
        "premium":   {"light": "#F9FAFB", "white": "#FFFFFF",  "dark": f"dark gradient {primary}", "card_border": "1px subtle, no shadow"},
        "community": {"light": "#FAF5FF", "white": "#FFFFFF",  "dark": f"dark gradient {primary}", "card_border": "1px soft, pastel shadow"},
        "dark_tech": {"light": "#0D1321", "white": "#0A0F1E",  "dark": f"very dark {primary} with subtle grid lines", "card_border": "1px cyan #00D4FF border, dark card bg #1A2035"},
    }
    bg = STYLE_BG.get(style, STYLE_BG["minimal"])
    bg_light = bg["light"]
    bg_white = bg["white"]
    bg_dark  = bg["dark"]
    card_style = bg["card_border"]

    # ── 스타일별 시각 언어 추가 지시 ────────────────────────────────────────
    STYLE_VISUAL = {
        "minimal":   "Clean, modern, white-space-heavy. Subtle blue/gray tones. No heavy effects.",
        "sales":     "Energetic, warm amber/red tones. High-contrast CTA. Urgency-driven.",
        "premium":   "Elegant, gold accents on dark backgrounds. Refined typography. Luxury feel.",
        "community": "Warm purple/pink palette. Friendly icons. Approachable, inclusive atmosphere.",
        "dark_tech": (
            "Dark quantitative finance / algorithmic trading terminal aesthetic. "
            "Primary backgrounds: very dark navy-black. "
            "Accent: Electric cyan (#00D4FF), Neon green (#00FF7F). "
            "Typography: Monospace code font for data/numbers, bold sans-serif for headlines. "
            "Visual elements: trading charts, candlestick patterns, API code snippets, grid lines. "
            "Reference: Bloomberg Terminal, TradingView dark mode. "
            "Korean text: Bold white or cyan headlines. "
            "NO light/white backgrounds — this is a dark-themed product."
        ),
    }
    visual_lang = STYLE_VISUAL.get(style, STYLE_VISUAL["minimal"])

    # 공통 스타일 앵커 — 웹 랜딩 문법 강제
    style_anchor = f"""
=== DIMENSION LOCK ===
- EXACT WIDTH: 1200 pixels (non-negotiable)
- FULL BLEED: Content fills ENTIRE 1200px — NO side margins, NO border frame

=== WEB LANDING RULES (MUST FOLLOW) ===
- This is a SCROLL SECTION of a web landing page, NOT a standalone slide
- Design as CONTINUOUS PAGE SEGMENT flowing naturally with adjacent sections
- SPACIOUS LAYOUT: generous whitespace, clear breathing room between elements
- TYPOGRAPHIC HIERARCHY: one dominant headline, clear visual weight difference
- MINIMAL FRAMING: use whitespace to separate elements, avoid heavy boxes
- HIGH READABILITY: key message visible within 2 seconds of viewing
- BACKGROUND CONTINUITY: background should feel like part of a longer page

=== SLIDE PREVENTION (STRICTLY FORBIDDEN) ===
- NOT a presentation slide, NOT a pitch deck, NOT PPT style
- NOT slide-frame or slide-border layout
- NO bullet-heavy text blocks filling the entire image
- NO dense paragraph text in large areas
- NO identical card grid repeated look (same box pattern everywhere)
- AVOID: too many glowing borders or neon outlines on every element

=== DESIGN STYLE ===
Style preset: {style}
Visual language: {visual_lang}
Color palette: Primary {primary}, Accent {accent}.
Typography: Bold Korean headlines (max 2 lines, 22 chars each), minimal body text.
Text in image: ONLY headlines (max 2 lines) + short bullets (max 3, 15 chars each).
Do NOT place long paragraphs or 4+ bullet points inside the image.
{visual_hint}

=== FINAL CHECKLIST ===
✓ Width is EXACTLY 1200 pixels wide
✓ Looks like a WEB LANDING PAGE section, NOT a PPT slide
✓ Headline is dominant, body text is minimal or absent
✓ Korean text is short, bold, and readable
✓ Background color matches the style preset above
"""

    prompts = {
        "01_hero": {
            "prompt": f"""Create a hero section for a Korean landing page.
Dimensions: 1200x800 pixels.
{style_anchor}

Layout:
- Top-right: Small urgency badge with text "{urgency.get('value', '한정 특가')}"
- Center: Large headline area for Korean text
- Below: Subheadline area
⚠️ CRITICAL: This image must NOT contain any button, CTA, or clickable element.
The design ends after the subheadline. The bottom area is plain dark background only.
NO button shape. NO rounded rectangle. NO placeholder. NO CTA text of any kind.
A real HTML button will be overlaid on top of this image by code.

Background: {bg_dark}
Include: Subtle geometric shapes, professional glow effects.
Mood: Trustworthy, action-oriented, premium feel.

Key message concept: "{benefit}"
""",
            "width": 1200,
            "height": SECTION_HEIGHTS["01_hero"],
            "filename": "01_hero.png"
        },

        "02_pain": {
            "prompt": f"""Create a pain points section for Korean landing page.
Dimensions: 1200x{SECTION_HEIGHTS['02_pain']} pixels.
LAYOUT TYPE: type_c — Minimal cards (exactly 3 cards, generous spacing).
{style_anchor}

Background: {bg_light}
Cards: {card_style}

Layout:
- Top: Small label "이런 고민 하고 계신가요?" (not a big headline)
- Center: EXACTLY 3 cards in horizontal row — each card: icon + SHORT title only (no paragraph text in cards)
- Bottom: 1-line hook text

Pain point concepts related to: "{problem}"

Visual: 3 cards. Icons: empathy style. SPACIOUS gaps between cards.
DO NOT fill cards with paragraph descriptions — icon + title (15 chars max) only.
""",
            "width": 1200,
            "height": SECTION_HEIGHTS["02_pain"],
            "filename": "02_pain.png"
        },

        "03_problem": {
            "prompt": f"""Create a problem definition section.
Dimensions: 1200x{SECTION_HEIGHTS['03_problem']} pixels.
LAYOUT TYPE: type_a — Full-bleed background + big typography (BREATHING SECTION — no card grid).
{style_anchor}

Background: {bg_white}

Layout (NO CARD GRID):
- Top: Large hook headline "당신 탓이 아닙니다" (dominant, centered)
- Below: Sub line (1 line, gray)
- Center: 3 numbered items as simple list — NOT as cards or boxes
- Use connecting arrows or flow diagram between items

Concept: Reframing the problem — it's the system, not you.
NO card boxes. Use numbered list with connecting flow arrows.
""",
            "width": 1200,
            "height": SECTION_HEIGHTS["03_problem"],
            "filename": "03_problem.png"
        },

        "04_story": {
            "prompt": f"""Create a before/after transformation section.
Dimensions: 1200x{SECTION_HEIGHTS['04_story']} pixels.
LAYOUT TYPE: type_b — Split layout (left BEFORE / right AFTER).
{style_anchor}

Layout (SPLIT — no card grid):
- Left half: "BEFORE" label + muted background + state keyword + small stress icon
- Right half: "AFTER" label + vibrant background + state keyword + success icon
- Center: Subtle vertical divider with arrow pointing right
- Bottom center: ONE key stat — large, bold

Before concept: Struggling with "{problem}"
After concept: Achieving "{benefit}"

BEFORE stat: "{ctx.get('before_stat', '주당 14시간 전처리')}"
AFTER stat: "{ctx.get('after_stat', 'API 호출 1번으로 끝')}"

DO NOT put paragraph text. Just labels, short keywords, and 1 stat number.
Left side muted/gray colors, right side vibrant brand colors.
""",
            "width": 1200,
            "height": SECTION_HEIGHTS["04_story"],
            "filename": "04_story.png"
        },

        "05_solution": {
            "prompt": f"""Create a solution introduction section.
Dimensions: 1200x{SECTION_HEIGHTS['05_solution']} pixels.
LAYOUT TYPE: type_a — Full-bleed background + BIG product name typography.
{style_anchor}

Background: {bg_dark}

Layout (NO CARDS — big typography focus):
- Center dominant: Product name "{product_name}" — very large, white, bold
- Below: One-liner "{one_liner}" — medium size, gray/light
- Below: 3 small feature badges (pill shape, 8 chars each) in a row

Simple, clean, impactful product reveal. Background has subtle radial glow.
Product name must be the largest element on the page.
""",
            "width": 1200,
            "height": SECTION_HEIGHTS["05_solution"],
            "filename": "05_solution.png"
        },

        "06_how_it_works": {
            "prompt": f"""Create a "how it works" process section.
Dimensions: 1200x{SECTION_HEIGHTS['06_how_it_works']} pixels.
LAYOUT TYPE: type_b — Horizontal process flow (left-to-right steps).
{style_anchor}

Background: {bg_light}

Layout (PROCESS FLOW — not a card grid):
- Top: Section headline "3단계로 끝납니다" (max 22 chars)
- Center: 3-step horizontal flow
  - Each step: numbered circle + icon + step title (10 chars max) ONLY
  - Steps connected by arrows (no card boxes around steps)
  - Clean, airy spacing between steps

DO NOT put description paragraphs under each step. Title only.
Flow arrows between steps. Clean horizontal layout.
""",
            "width": 1200,
            "height": SECTION_HEIGHTS["06_how_it_works"],
            "filename": "06_how_it_works.png"
        },

        "07_social_proof": {
            "prompt": f"""Create a social proof/testimonials section.
Dimensions: 1200x{SECTION_HEIGHTS['07_social_proof']} pixels.
LAYOUT TYPE: type_d — Proof grid (HEAVY FRAME PERMITTED for this section).
{style_anchor}

Background: {bg_white}
Cards: {card_style}

Layout:
- Top: Stats bar with 3 large bold numbers + short labels (10 chars each)
- Center: 3 testimonial cards
- Each card: quote icon + SHORT quote (max 40 chars) + avatar circle + name + result badge

Include: Star ratings, quote marks, result highlight badges.
Cards: keep quotes SHORT — no long paragraphs.
Mood: Trust-building, credible numbers, clean grid.
""",
            "width": 1200,
            "height": SECTION_HEIGHTS["07_social_proof"],
            "filename": "07_social_proof.png"
        },

        "08_authority": {
            "prompt": f"""Create an authority/about section.
Dimensions: 1200x{SECTION_HEIGHTS['08_authority']} pixels.
LAYOUT TYPE: type_b — Split (left: visual/logo, right: text credentials).
{style_anchor}

Background: {bg_light}

Layout (SPLIT — no card boxes on text side):
- Left 40%: Brand logo/mark + 3 credential badges (icon + short label, no boxes)
- Right 60%: Headline (max 22 chars) + 3 bullet credentials (max 15 chars each)
- Right: Body intro text — KEEP TO 2 LINES MAX in image

NO card boxes on text side. Clean split layout.
Include: Credential icons. Professional, credible tone.
""",
            "width": 1200,
            "height": SECTION_HEIGHTS["08_authority"],
            "filename": "08_authority.png"
        },

        "09_benefits": {
            "prompt": f"""Create a benefits section.
Dimensions: 1200x{SECTION_HEIGHTS['09_benefits']} pixels.
LAYOUT TYPE: type_d — Benefits grid (HEAVY FRAME PERMITTED for this section).
{style_anchor}

Background: Subtle {primary} tint

Layout:
- Top: Headline (max 22 chars)
- Center: Grid of 5~7 benefit items — each: icon + short title (15 chars MAX) ONLY
- Grid: 3-4 items per row, generous gaps
- Bottom: 1 value/savings callout

DO NOT put description paragraphs under each benefit — icon + title only.
Keep grid clean and airy. Include checkmark or relevant icon per item.
""",
            "width": 1200,
            "height": SECTION_HEIGHTS["09_benefits"],
            "filename": "09_benefits.png"
        },

        "10_risk_removal": {
            "prompt": f"""Create a risk removal/guarantee section.
Dimensions: 1200x{SECTION_HEIGHTS['10_risk_removal']} pixels.
LAYOUT TYPE: type_c — Minimal cards (2~3 cards max, BREATHING SECTION).
{style_anchor}

Background: {bg_white}
Cards: {card_style}

Layout (MINIMAL — no heavy frames):
- Top: Large shield/lock icon + guarantee headline (max 22 chars)
- Center: 2~3 guarantee cards — each: icon + title (15 chars) ONLY
- Bottom: 2 FAQ Q-only items (questions only, max 20 chars each — no answers in image)

Generous whitespace above and below card row.
Safe, reassuring, clean tone. NO dense text blocks.
""",
            "width": 1200,
            "height": SECTION_HEIGHTS["10_risk_removal"],
            "filename": "10_risk_removal.png"
        },

        "11_comparison": {
            "prompt": f"""Create a comparison section.
Dimensions: 1200x{SECTION_HEIGHTS['11_comparison']} pixels.
LAYOUT TYPE: type_d — Comparison table (HEAVY FRAME PERMITTED for this section).
{style_anchor}

Background: {bg_light}

Layout (COMPARISON TABLE):
- 2 or 3 columns: "없이" (dim) vs product name (highlighted) [vs competitor (dim)]
- 4~5 feature rows: short feature label (12 chars) + checkmark/X per column
- Highlighted column: brand accent color background
- Bottom row: price comparison (large discounted price in highlighted column)

Column headers: short labels (10 chars). Row labels: 12 chars max.
Clean table grid. Highlighted column has subtle glow/border.
""",
            "width": 1200,
            "height": SECTION_HEIGHTS["11_comparison"],
            "filename": "11_comparison.png"
        },

        "12_target_filter": {
            "prompt": f"""Create a target audience filter section.
Dimensions: 1200x{SECTION_HEIGHTS['12_target_filter']} pixels.
LAYOUT TYPE: type_c — 2-column minimal layout (BREATHING SECTION).
{style_anchor}

Background: {bg_white}

Layout (2-COLUMN — no card boxes, clean typography):
- Left column: "이런 분께 추천" header (green) + 4~5 items with ✅ (max 18 chars each)
- Right column: "이런 분은 비추" header (gray) + 3~4 items with ❌ (max 18 chars each)
- NO card boxes around columns — just clean 2-column text layout
- Bottom: 1-line mini CTA text (not a button)

Target concept: "{target}"
Honest, clean, professional. No borders between columns.
""",
            "width": 1200,
            "height": SECTION_HEIGHTS["12_target_filter"],
            "filename": "12_target_filter.png"
        },

        "13_final_cta": {
            "prompt": f"""Create a final call-to-action section.
Dimensions: 1200x{SECTION_HEIGHTS['13_final_cta']} pixels.
LAYOUT TYPE: type_a — Full-bleed impact (HEAVY FRAME ONLY for CTA button).
{style_anchor}

Background: {bg_dark} with subtle radial glow at center

Layout (SINGLE FOCAL POINT — no card grid):
- Small urgency badge at top (10 chars, amber/red)
- Large headline (max 22 chars, white, dominant)
- Price: original strikethrough (small) → discounted LARGE (bold, accent color)
- Trust micro-copy: 1 short line below the price (e.g., "언제든 취소 가능")
⚠️ CRITICAL: This image must NOT contain any button, CTA, or clickable element.
The design is: badge → headline → price → trust micro-copy. Nothing else.
NO button shape. NO rounded rectangle. NO placeholder. NO CTA text of any kind.
A real HTML button will be overlaid on top of this image by code.

High contrast, single focal CTA. NO card grid. All attention on the button.
Original: {price.get('original', '199,000원')} | Discounted: {price.get('discounted', '99,000원')}
Urgency: "{urgency.get('value', '한정 수량')}"
""",
            "width": 1200,
            "height": SECTION_HEIGHTS["13_final_cta"],
            "filename": "13_final_cta.png"
        }
    }

    return prompts


def generate_cta_slots(output_dir: str, sections_dir: str) -> Optional[str]:
    """
    섹션 이미지를 읽어 CTA 슬롯 좌표(%)를 계산하고 cta_slots.json을 저장합니다.
    01_hero / 13_final_cta 섹션의 빈 슬롯 위치를 cf-pages HTML 버튼에 전달합니다.
    """
    from PIL import Image

    TARGET_W = 1200

    # 섹션별 슬롯 스펙: btn_w(px), btn_h(px), section_top_pct(섹션 높이 내 위치 비율)
    SLOT_SPECS = {
        "01_hero":      {"id": "hero_cta",  "label": "지금 사전예약하기", "btn_w": 260, "btn_h": 56, "top_pct": 0.68},
        "13_final_cta": {"id": "final_cta", "label": "지금 사전예약하기", "btn_w": 290, "btn_h": 58, "top_pct": 0.73},
    }

    sections_path = Path(sections_dir)
    section_files = sorted(sections_path.glob("*.png"))
    if not section_files:
        print("[cta_slots] 섹션 이미지 없음 — 스킵")
        return None

    # 각 섹션의 1200px 기준 실제 높이 계산
    sections = []
    total_h = 0
    for f in section_files:
        try:
            with Image.open(f) as img:
                w, h = img.size
                new_h = round(h * TARGET_W / w)
        except Exception:
            new_h = SECTION_HEIGHTS.get(f.stem, 600)
        sections.append({"name": f.stem, "y": total_h, "h": new_h})
        total_h += new_h

    # 슬롯 좌표를 전체 페이지 높이 기준 %로 산출
    slots = []
    for sec in sections:
        spec = SLOT_SPECS.get(sec["name"])
        if not spec:
            continue
        btn_top_y  = sec["y"] + round(sec["h"] * spec["top_pct"])
        left_pct   = round((TARGET_W / 2 - spec["btn_w"] / 2) / TARGET_W * 100, 2)
        top_pct    = round(btn_top_y / total_h * 100, 2)
        width_pct  = round(spec["btn_w"] / TARGET_W * 100, 2)
        slots.append({
            "id":         spec["id"],
            "section_id": sec["name"],
            "label":      spec["label"],
            "left_pct":   left_pct,
            "top_pct":    top_pct,
            "width_pct":  width_pct,
            "ga4": {"cta_id": spec["id"], "section_id": sec["name"]},
        })

    data = {
        "_note": "auto-generated by generate_cta_slots(). 1200px-width page 기준 % 좌표.",
        "page_size": {"width": TARGET_W, "height": total_h},
        "slots": slots,
    }

    out_path = Path(output_dir) / "cta_slots.json"
    with open(out_path, "w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)
    print(f"CTA slots saved: {out_path}")
    return str(out_path)


def save_prompts(prompts: Dict, output_path: str):
    """프롬프트를 JSON 파일로 저장"""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2)
    print(f"Prompts saved: {output_path}")


def generate_landing_page(
    brief: Optional[Dict[str, Any]] = None,
    output_dir: str = "output",
    skip_generation: bool = False,
    page_variant: str = "long"
) -> Optional[str]:
    """
    전체 상세페이지 생성 파이프라인을 실행합니다.

    Args:
        brief: 제품 정보 (없으면 샘플 사용)
        output_dir: 출력 디렉토리
        skip_generation: True면 이미지 생성 스킵 (스티칭만)
        page_variant: "long" (13섹션, 기본값) 또는 "short" (7섹션 핵심 전환용)

    Returns:
        최종 페이지 경로
    """
    output_dir = str(PROJECT_ROOT / output_dir)
    sections_dir = os.path.join(output_dir, "sections")

    # brief에 page_variant 필드가 있으면 우선 적용
    if brief and brief.get("page_variant"):
        page_variant = brief["page_variant"]

    print(f"Page variant: {page_variant} ({'13섹션' if page_variant == 'long' else '7섹션 short 모드'})")

    # 디렉토리 생성
    Path(sections_dir).mkdir(parents=True, exist_ok=True)

    if brief is None:
        print("Using sample brief...")
        brief = create_sample_brief()

    # Brief 저장
    brief_path = os.path.join(output_dir, "structured_brief.json")
    with open(brief_path, "w", encoding="utf-8") as f:
        json.dump(brief, f, ensure_ascii=False, indent=2)
    print(f"Brief saved: {brief_path}")

    # 프롬프트 생성
    print("\nGenerating prompts...")
    prompts = generate_section_prompts(brief)
    prompts_path = os.path.join(output_dir, "gemini_prompts.json")
    save_prompts(prompts, prompts_path)

    # page_variant에 따라 생성 대상 섹션 필터링
    if page_variant == "short":
        prompts = {k: v for k, v in prompts.items() if k in SHORT_MODE_SECTIONS}
        print(f"Short mode: generating {len(prompts)} sections: {list(prompts.keys())}")

    if not skip_generation:
        # API 연결 테스트
        print("\nTesting API connection...")
        if not test_api_connection():
            print("API connection failed. Check your GEMINI_API_KEY.")
            return None

        # 섹션별 이미지 생성
        print("\nGenerating section images...")
        for section_key, section_data in prompts.items():
            print(f"\n{'='*50}")
            print(f"Generating: {section_key}")
            print(f"{'='*50}")

            output_path = os.path.join(sections_dir, section_data["filename"])

            result = generate_image(
                prompt=section_data["prompt"],
                output_path=output_path,
                width=section_data["width"],
                height=section_data["height"]
            )

            if not result:
                print(f"Warning: Failed to generate {section_key}")

            # API 레이트 리밋 방지
            import time
            time.sleep(3)

    # 이미지 스티칭
    print("\n" + "="*50)
    print("Stitching final page...")
    print("="*50)

    final_png = os.path.join(output_dir, "final_page.png")
    final_pdf = os.path.join(output_dir, "final_page.pdf")

    # PNG 생성
    result = stitch_from_directory(sections_dir, final_png)

    if result:
        # PDF도 생성
        stitch_from_directory(sections_dir, final_pdf)

        # CTA 슬롯 좌표 산출 → cta_slots.json
        generate_cta_slots(output_dir, sections_dir)

        # 미리보기 생성
        preview_path = os.path.join(output_dir, "preview.png")
        create_preview(final_png, preview_path, max_height=2000)

        print("\n" + "="*50)
        print("COMPLETE!")
        print("="*50)
        print(f"Final PNG: {final_png}")
        print(f"Final PDF: {final_pdf}")
        print(f"Preview: {preview_path}")

        return final_png

    return None


if __name__ == "__main__":
    # 샘플 상세페이지 생성
    result = generate_landing_page(
        brief=None,  # 샘플 사용
        output_dir="output",
        skip_generation=False  # 실제 생성
    )

    if result:
        print(f"\nSuccess! Check: {result}")
    else:
        print("\nFailed to generate landing page")
