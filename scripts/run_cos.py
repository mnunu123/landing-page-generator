# COS 구름백 상세페이지 생성 스크립트
# 실행: python scripts/run_cos.py
# 결과: cf-pages/cos/images/final_page.png 자동 복사

import sys
import shutil
import argparse
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.generate_page import generate_landing_page

BRIEF_COS = {
    "product_name": "COS 구름백",
    "one_liner":    "손에 쥐면 사르르 — 구름처럼 가벼운 COS 버블 퀼팅 미니백",
    "target_audience": "감각적인 데일리 패션을 즐기는 20-30대 여성",
    "main_problem":    "예쁜 백은 늘 무겁고 불편하다",
    "key_benefit":     "COS 버블 퀼팅 소재, 깃털처럼 가벼우면서도 어디서나 시선을 사로잡는 미니백",
    "price": {
        "original":   "₩220,000",
        "discounted": "₩180,000",
        "period":     "",
        "savings_pct": "18%",
    },
    "urgency": {
        "type":  "quantity",
        "value": "한정 수량",
        "bonus": "인기 컬러 소진 중 — 재입고 미정",
    },
    "style_preset": "clean_minimal",
    "brand_colors": {
        "primary":   "#FAFAF8",
        "secondary": "#F0EDE8",
        "accent":    "#C8A882",
    },
    "page_variant": "long",
    "product_context": {
        "category":   "패션 미니백 — COS 버블 퀼팅 토트백",
        "target_tech": "데일리 캐주얼, 오피스룩, 미니멀 패션 스타일링",
        "data_types":  "버블 퀼팅 텍스처, 핸드백/숄더백 겸용, 크림·그레이·틸 3가지 컬러",
        "pain_stats":  "기존 백 대비 가벼움, 동일한 수납력",
        "proof_stats": "COS 시즌 베스트셀러 / 3가지 컬러 / 한정 수량",
        "visual_references": (
            "minimalist fashion photography, soft diffused natural light, "
            "clean cream-white background, quilted bubble-texture handbag displayed on "
            "a smooth neutral surface, Scandinavian editorial aesthetic, soft beige tones"
        ),
        "hero_headline":         "구름처럼 가볍고, 어디서나 시선을 사로잡는",
        "how_it_works_headline": "FEEL · CARRY · STYLE",
        "before_stat": "무겁고 불편한 기존 백",
        "after_stat":  "깃털처럼 가벼운 구름백",
    },
}


def main():
    parser = argparse.ArgumentParser(description="COS 구름백 상세페이지 생성")
    parser.add_argument("--skip-gen", action="store_true", help="이미지 재생성 스킵")
    args = parser.parse_args()

    run_id  = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = str(PROJECT_ROOT / "output" / "runs" / run_id / "COS")

    print(f"\n{'='*60}")
    print(f"  COS 구름백 상세페이지 생성  (run_id: {run_id})")
    print(f"{'='*60}")

    result = generate_landing_page(
        brief=BRIEF_COS,
        output_dir=out_dir,
        skip_generation=args.skip_gen,
        page_variant="long",
    )

    if not result:
        print("[ERROR] 페이지 생성 실패")
        sys.exit(1)

    dest = PROJECT_ROOT / "cf-pages" / "cos" / "images" / "final_page.png"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(result, dest)
    print(f"\n[DONE] {dest.relative_to(PROJECT_ROOT)} 복사 완료")
    print(f"\n  로컬 서버: cd cf-pages && python -m http.server 8080")
    print(f"  브라우저:  http://localhost:8080/cos/")


if __name__ == "__main__":
    main()
