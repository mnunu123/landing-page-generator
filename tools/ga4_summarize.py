# GA4 metrics 요약 생성기 — ga4_pull.py 출력을 받아 KPI 집계 파일을 만든다
# 사용법: python tools/ga4_summarize.py [--input metrics/ga4_xxx_rich.json]
# 출력: metrics/metrics_summary.json + metrics/metrics_summary.md

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone

OUTPUT_DIR = Path(__file__).parent.parent / "metrics"
IMPRESSION = "lp_impression"
CLICK      = "lp_cta_click"
SUBMIT     = "lp_reserve_submit"


def safe_div(num, den):
    return round(num / den, 4) if den else None


def find_latest_input() -> Path:
    files = sorted(OUTPUT_DIR.glob("ga4_*.json"),
                   key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        print("[ERROR] metrics/ga4_*.json 파일 없음. ga4_pull.py를 먼저 실행하세요.")
        sys.exit(1)
    return files[0]


class Counter:
    def __init__(self):
        self.imp = self.clk = self.sub = 0

    def add(self, event: str, count: int):
        if   event == IMPRESSION: self.imp += count
        elif event == CLICK:      self.clk += count
        elif event == SUBMIT:     self.sub += count

    def to_dict(self) -> dict:
        return {
            "impressions": self.imp,
            "clicks":      self.clk,
            "submits":     self.sub,
            "ctr":         safe_div(self.clk, self.imp),
            "cvr":         safe_div(self.sub, self.imp),
            "submit_rate": safe_div(self.sub, self.clk),
        }


def parse_row(row: dict, dim_headers: list) -> dict:
    dims = dict(zip(dim_headers, row["dimensions"]))
    return {
        "date":       dims.get("date", ""),
        "event":      dims.get("eventName", ""),
        "var":        dims.get("customEvent:var",        "") or "unknown",
        "exp_id":     dims.get("customEvent:exp_id",     "") or "unknown",
        "cta_id":     dims.get("customEvent:cta_id",     "") or "unknown",
        "section_id": dims.get("customEvent:section_id", "") or "unknown",
        "count":      int(row["metrics"][0]),
    }


def aggregate(rows: list, dim_headers: list) -> tuple:
    total      = Counter()
    by_var     = {}
    by_cta     = {}
    by_section = {}
    by_exp     = {}
    dates      = set()

    for row in rows:
        r = parse_row(row, dim_headers)
        e, c = r["event"], r["count"]
        if r["date"]:
            dates.add(r["date"])
        total.add(e, c)
        for key, store in [
            (r["var"],        by_var),
            (r["cta_id"],     by_cta),
            (r["section_id"], by_section),
            (r["exp_id"],     by_exp),
        ]:
            store.setdefault(key, Counter()).add(e, c)

    return total, by_var, by_cta, by_section, by_exp, sorted(dates)


def pct(v) -> str:
    return f"{v * 100:.1f}%" if v is not None else "—"


def build_md(s: dict) -> str:
    t, dr = s["totals"], s["date_range"]
    lines = [
        "# GA4 지표 요약",
        f"\n**기간**: {dr['min']} ~ {dr['max']}  ",
        f"**생성**: {s['generated_at'][:19]}Z  ",
        f"**입력**: `{s['input_file']}` (mode: {s['mode']})",
        "\n## 전체 KPI",
        "| 항목 | 값 |", "|------|-----|",
        f"| Impressions | {t['impressions']:,} |",
        f"| CTA Clicks  | {t['clicks']:,} |",
        f"| Submits     | {t['submits']:,} |",
        f"| CTR         | {pct(t['ctr'])} |",
        f"| CVR         | {pct(t['cvr'])} |",
        f"| Submit Rate | {pct(t['submit_rate'])} |",
    ]
    if t["submits"] < 10:
        lines.append(
            "\n> ⚠️ **표본 부족**: 제출 수가 10건 미만입니다. 통계적 유의성이 낮습니다."
        )

    # A/B var 별
    lines += [
        "\n## A/B Variant별",
        "| Var | Impressions | Clicks | Submits | CTR | CVR | Submit Rate |",
        "|-----|-------------|--------|---------|-----|-----|-------------|",
    ]
    for k, v in sorted(s["by_var"].items()):
        lines.append(
            f"| {k} | {v['impressions']:,} | {v['clicks']:,} | {v['submits']:,} "
            f"| {pct(v['ctr'])} | {pct(v['cvr'])} | {pct(v['submit_rate'])} |"
        )

    # CTA 상위 5
    lines += [
        "\n## CTA별 Submit Rate (상위 5)",
        "| CTA ID | Clicks | Submits | Submit Rate |",
        "|--------|--------|---------|-------------|",
    ]
    for k, v in sorted(s["by_cta"].items(),
                        key=lambda x: x[1]["submit_rate"] or 0, reverse=True)[:5]:
        lines.append(f"| {k} | {v['clicks']:,} | {v['submits']:,} | {pct(v['submit_rate'])} |")

    # 섹션 상위 5
    lines += [
        "\n## 섹션별 Submit Rate (상위 5)",
        "| Section ID | Clicks | Submits | Submit Rate |",
        "|------------|--------|---------|-------------|",
    ]
    for k, v in sorted(s["by_section"].items(),
                        key=lambda x: x[1]["submit_rate"] or 0, reverse=True)[:5]:
        lines.append(f"| {k} | {v['clicks']:,} | {v['submits']:,} | {pct(v['submit_rate'])} |")

    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="GA4 metrics 요약 생성")
    parser.add_argument("--input", help="입력 JSON 경로 (기본: 가장 최신 ga4_*.json)")
    args = parser.parse_args()

    in_path = Path(args.input) if args.input else find_latest_input()
    if not in_path.exists():
        print(f"[ERROR] 파일 없음: {in_path}")
        sys.exit(1)

    with open(in_path, encoding="utf-8") as f:
        data = json.load(f)

    mode        = data.get("meta", {}).get("mode", "basic")
    dim_headers = data["dimension_headers"]
    rows        = data["rows"]
    print(f"[INFO] 입력: {in_path.name}  (mode={mode}, rows={len(rows)})")

    total, by_var, by_cta, by_section, by_exp, dates = aggregate(rows, dim_headers)
    date_range = {"min": dates[0] if dates else "", "max": dates[-1] if dates else ""}

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input_file":   in_path.name,
        "mode":         mode,
        "date_range":   date_range,
        "totals":       total.to_dict(),
        "by_var":       {k: v.to_dict() for k, v in sorted(by_var.items())},
        "by_cta":       {k: v.to_dict() for k, v in sorted(by_cta.items())},
        "by_section":   {k: v.to_dict() for k, v in sorted(by_section.items())},
        "by_exp":       {k: v.to_dict() for k, v in sorted(by_exp.items())},
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    json_path = OUTPUT_DIR / "metrics_summary.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"[INFO] 저장: {json_path}")

    md_path = OUTPUT_DIR / "metrics_summary.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(build_md(summary))
    print(f"[INFO] 저장: {md_path}")


if __name__ == "__main__":
    main()
