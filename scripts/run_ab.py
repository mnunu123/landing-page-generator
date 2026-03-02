"""
OpenClaw A/B 테스트 통합 실행 스크립트
실행할 때마다 output/runs/YYYYMMDD_HHMMSS/ 에 별도 저장됩니다.

사용법:
  python scripts/run_ab.py                          → A, B 둘 다 새로 생성
  python scripts/run_ab.py --variant A              → A만 생성
  python scripts/run_ab.py --variant B              → B만 생성
  python scripts/run_ab.py --list                   → 저장된 결과 목록 확인
  python scripts/run_ab.py --use-run 20260228_1430  → 과거 결과를 cf-pages에 복사
"""

import sys
import shutil
import argparse
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
RUNS_DIR     = PROJECT_ROOT / "output" / "runs"
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.generate_page import generate_landing_page

# ── A 변형 브리프 (Cyan #00D4FF / 가격 강조) ────────────────────────────────
BRIEF_A = {
    "product_name": "OpenClaw",
    "one_liner": "퀀트 엔진에 즉시 주입 가능한 Hybrid Dataset API",
    "target_audience": "자동매매 파이프라인을 구축 중인 개인 퀀트 개발자",
    "main_problem": "전문가급 퀀트 데이터는 월 100만 원 — 개인 투자자에게 현실적으로 불가능한 진입장벽",
    "key_benefit": "OHLCV + 뉴스 감성 통합 Hybrid Dataset을 월 4만 원에, 전처리 없이 자동매매 엔진에 바로 주입",
    "price": {
        "original": "₩1,000,000 / 월",
        "discounted": "₩40,000 / 월",
        "period": "월",
        "savings_pct": "96%"
    },
    "urgency": {
        "type": "quantity",
        "value": "사전예약 한정",
        "bonus": "사전예약 목표 인원 달성 시 예고 없이 종료"
    },
    "style_preset": "dark_tech",
    "brand_colors": {
        "primary": "#0A0F1E",
        "secondary": "#1A2035",
        "accent": "#00D4FF"          # A 변형: cyan
    },
    "page_variant": "long",
    "product_context": {
        "category": "퀀트 금융 데이터 API — 자동매매 파이프라인용 Hybrid Dataset",
        "target_tech": "Python REST API, 알고리즘 자동매매 봇, 퀀트 투자 엔진",
        "data_types": "OHLCV 가격 데이터 + 뉴스/SNS 감성 점수 통합 데이터셋 (BTC/USDT 특화)",
        "pain_stats": "월 100만 원 타사 대비 96% 절감, 주당 14시간 전처리 작업 완전 제거",
        "proof_stats": "사전예약 진행 중 / 개발 비용 96% 절감 / 개발 기간 3개월 단축",
        "visual_references": "Bloomberg Terminal, TradingView dark mode, candlestick charts, JSON API responses, live ticker feeds",
        "hero_headline": "월 100만 원 전문가 퀀트 데이터를 월 4만 원에",
        "how_it_works_headline": "CLAW -> CONVERT -> DELIVER",
        "before_stat": "주당 14시간 전처리",
        "after_stat": "API 호출 1번으로 끝",
    }
}

# ── B 변형 브리프 (Neon Green #00FF7F / 전처리 제로 강조) ──────────────────
BRIEF_B = {
    "product_name": "OpenClaw",
    "one_liner": "전처리 없이 퀀트 엔진에 바로 꽂히는 Hybrid Dataset API",
    "target_audience": "자동매매 파이프라인을 구축 중인 개인 퀀트 개발자",
    "main_problem": "전처리에 매주 14시간 — 정작 전략 개발할 시간이 없다",
    "key_benefit": "OHLCV + 뉴스 감성 통합 Hybrid Dataset, 전처리 없이 API 1번 호출로 즉시 주입",
    "price": {
        "original": "₩1,000,000 / 월",
        "discounted": "₩40,000 / 월",
        "period": "월",
        "savings_pct": "96%"
    },
    "urgency": {
        "type": "quantity",
        "value": "사전예약 한정",
        "bonus": "사전예약 목표 인원 달성 시 예고 없이 종료"
    },
    "style_preset": "dark_tech",
    "brand_colors": {
        "primary": "#0A0F1E",
        "secondary": "#0D2010",
        "accent": "#00FF7F"          # B 변형: neon green
    },
    "page_variant": "long",
    "product_context": {
        "category": "퀀트 금융 데이터 API — 자동매매 파이프라인용 Hybrid Dataset",
        "target_tech": "Python REST API, 알고리즘 자동매매 봇, 퀀트 투자 엔진",
        "data_types": "OHLCV 가격 데이터 + 뉴스/SNS 감성 점수 통합 데이터셋 (BTC/USDT 특화)",
        "pain_stats": "주당 14시간 전처리 → 0, API 1번 호출로 즉시 주입 가능",
        "proof_stats": "사전예약 진행 중 / 개발 비용 96% 절감 / 개발 기간 3개월 단축",
        "visual_references": "Terminal green output, matrix-style data streams, live profit charts, green candles",
        "hero_headline": "주당 14시간 전처리, 이제 API 1번으로 끝",
        "how_it_works_headline": "CLAW -> CONVERT -> DELIVER",
        "before_stat": "주당 14시간 전처리",
        "after_stat": "API 호출 1번으로 끝",
    }
}

# ── 변형 메타데이터 ───────────────────────────────────────────────────────────
VARIANT_META = {
    "A": {
        "brief": BRIEF_A,
        "dest":  "cf-pages/images/final_page_A.png",
        "label": "Cyan / 가격 강조",
    },
    "B": {
        "brief": BRIEF_B,
        "dest":  "cf-pages/images/final_page_B.png",
        "label": "Neon Green / 전처리 제로 강조",
    },
}


def run_output_dir(run_id: str, key: str) -> Path:
    """실행별 출력 디렉토리 경로를 반환한다."""
    return RUNS_DIR / run_id / key


def copy_to_cfpages(run_id: str, key: str) -> bool:
    """지정 실행 결과의 final_page.png 를 cf-pages/images/ 에 복사한다."""
    src = run_output_dir(run_id, key) / "final_page.png"
    if not src.exists():
        print(f"  [ERROR] 파일 없음: {src.relative_to(PROJECT_ROOT)}")
        return False

    dest = PROJECT_ROOT / VARIANT_META[key]["dest"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    print(f"  [COPIED] {dest.relative_to(PROJECT_ROOT)}")
    return True


def generate_variant(run_id: str, key: str) -> bool:
    """Gemini API 로 변형을 생성하고 runs/{run_id}/{key}/ 에 저장한다."""
    meta    = VARIANT_META[key]
    out_dir = str(run_output_dir(run_id, key))

    print(f"\n{'='*60}")
    print(f"  변형 {key} — {meta['label']}")
    print(f"  저장 위치: output/runs/{run_id}/{key}/")
    print(f"{'='*60}")

    result = generate_landing_page(
        brief=meta["brief"],
        output_dir=out_dir,
        skip_generation=False,
        page_variant="long",
    )
    return bool(result)


def list_runs():
    """저장된 실행 결과를 최신순으로 출력한다."""
    if not RUNS_DIR.exists() or not any(RUNS_DIR.iterdir()):
        print("  저장된 실행 결과가 없습니다.")
        return

    runs = sorted(
        [d.name for d in RUNS_DIR.iterdir() if d.is_dir()],
        reverse=True
    )

    print(f"\n{'='*60}")
    print("  저장된 실행 결과 (최신순)")
    print(f"{'='*60}")
    for run_id in runs:
        present = [
            k for k in ["A", "B"]
            if (RUNS_DIR / run_id / k / "final_page.png").exists()
        ]
        print(f"  {run_id}  [{', '.join(present)}]")
    print(f"\n  재사용 예시:")
    print(f"    python scripts/run_ab.py --use-run {runs[0]}")


def main():
    parser = argparse.ArgumentParser(
        description="OpenClaw A/B 랜딩 페이지 생성 + cf-pages 자동 배포"
    )
    parser.add_argument(
        "--variant", choices=["A", "B", "both"], default="both",
        help="생성할 변형 (기본값: both)"
    )
    parser.add_argument(
        "--use-run", metavar="RUN_ID",
        help="기존 실행 결과를 cf-pages에 복사 (예: --use-run 20260228_143052)"
    )
    parser.add_argument(
        "--list", action="store_true",
        help="저장된 실행 결과 목록 출력"
    )
    args = parser.parse_args()

    # ── 목록 출력 ────────────────────────────────────────────────────────────
    if args.list:
        list_runs()
        return

    targets = ["A", "B"] if args.variant == "both" else [args.variant]

    # ── 기존 결과 재사용 ─────────────────────────────────────────────────────
    if args.use_run:
        run_id = args.use_run
        if not (RUNS_DIR / run_id).exists():
            print(f"  [ERROR] 실행 결과 없음: {run_id}")
            print(f"  목록 확인: python scripts/run_ab.py --list")
            sys.exit(1)

        print(f"\n{'='*60}")
        print(f"  실행 결과 재사용: {run_id}")
        print(f"{'='*60}")
        results = {k: copy_to_cfpages(run_id, k) for k in targets}

    # ── 신규 생성 ────────────────────────────────────────────────────────────
    else:
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        print(f"\n{'='*60}")
        print(f"  OpenClaw A/B 테스트 페이지 생성")
        print(f"  실행 ID: {run_id}")
        print(f"{'='*60}")

        results = {}
        for key in targets:
            ok = generate_variant(run_id, key)
            if ok:
                ok = copy_to_cfpages(run_id, key)
            results[key] = ok

    # ── 결과 요약 ────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  결과 요약  (실행 ID: {run_id})")
    print(f"{'='*60}")
    for key, ok in results.items():
        icon = "✓" if ok else "✗"
        print(f"  [{icon}] {key}: {VARIANT_META[key]['label']}")

    if any(results.values()):
        print(f"\n  나중에 이 결과를 다시 쓰려면:")
        print(f"    python scripts/run_ab.py --use-run {run_id}")
        print(f"\n  로컬 서버 시작:")
        print(f"    cd cf-pages && python -m http.server 8080")
        print(f"\n  브라우저 확인:")
        for key in targets:
            print(f"    http://localhost:8080/?var={key}")

    if not all(results.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
