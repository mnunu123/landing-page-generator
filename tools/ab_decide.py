# A/B 실험 승자 판단 스크립트 — metrics_summary.json을 분석해 decision.json + .md를 생성한다
# 사용법: python tools/ab_decide.py [--input metrics/metrics_summary.json]

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone

OUTPUT_DIR = Path(__file__).parent.parent / "metrics"
DEFAULT_IN = OUTPUT_DIR / "metrics_summary.json"

THRESHOLDS = {
    "min_submits_total":    10,
    "min_impressions_each": 100,
    "max_imbalance":        0.20,
    "min_cvr_delta":        0.002,
}


def safe_div(num, den):
    return round(num / den, 6) if den else 0.0


def pick_exp_id(by_exp: dict) -> str:
    """non-unknown exp_id 중 submits 합산이 가장 큰 것을 선택한다."""
    candidates = {k: v for k, v in by_exp.items() if k != "unknown"}
    if not candidates:
        return "unknown"
    return max(candidates, key=lambda k: candidates[k].get("submits", 0))


def get_var_stats(by_var: dict, var: str) -> dict:
    d   = by_var.get(var, {})
    imp = d.get("impressions", 0)
    clk = d.get("clicks",      0)
    sub = d.get("submits",     0)
    return {
        "impressions": imp,
        "clicks":      clk,
        "submits":     sub,
        "ctr":         safe_div(clk, imp),
        "cvr":         safe_div(sub, imp),
        "submit_rate": safe_div(sub, clk),
    }


def check_samples(a: dict, b: dict, total_sub: int):
    """(ok: bool, reason: str, action: str) 반환."""
    th = THRESHOLDS
    if total_sub < th["min_submits_total"]:
        return False, f"submits_total={total_sub} < {th['min_submits_total']}", "collect_more"
    for var, s in [("A", a), ("B", b)]:
        if s["impressions"] < th["min_impressions_each"]:
            return False, f"impressions_{var}={s['impressions']} < {th['min_impressions_each']}", "collect_more"
    total_imp = a["impressions"] + b["impressions"]
    if total_imp == 0:
        return False, "impressions_total=0", "collect_more"
    imbalance = abs(a["impressions"] - b["impressions"]) / total_imp
    if imbalance > th["max_imbalance"]:
        return False, f"SRM imbalance={imbalance:.3f} > {th['max_imbalance']}", "reroute_check"
    return True, "", ""


def determine_winner(a: dict, b: dict) -> str:
    delta = a["cvr"] - b["cvr"]
    if abs(delta) >= THRESHOLDS["min_cvr_delta"]:
        return "A" if delta > 0 else "B"
    sr_delta = a["submit_rate"] - b["submit_rate"]
    if abs(sr_delta) >= 0.01:
        return "A" if sr_delta > 0 else "B"
    return "unknown"


def build_md(d: dict, summary: dict) -> str:
    s      = d["stats"]
    totals = summary.get("totals", {})
    dr     = summary.get("date_range", {})
    th     = d["thresholds"]
    ok     = d["status"] == "declare_winner"
    imp_a, imp_b = s["A"]["impressions"], s["B"]["impressions"]
    total_imp    = imp_a + imp_b
    imb          = abs(imp_a - imp_b) / total_imp if total_imp else 0

    def pct(v): return f"{v * 100:.2f}%" if v else "—"
    def chk(c): return "✅" if c else "❌"

    lines = [
        "# A/B 승자 판단",
        f"\n**exp_id**: `{d['exp_id']}`  ",
        f"**기간**: {dr.get('min', '')} ~ {dr.get('max', '')}  ",
        f"**생성**: {d['generated_at'][:19]}Z",
        "\n## 표본 조건 체크",
        "| 조건 | 결과 |", "|------|------|",
        f"| submits_total ≥ {th['min_submits_total']} | {chk(totals.get('submits',0) >= th['min_submits_total'])} {totals.get('submits',0)} |",
        f"| impressions_A ≥ {th['min_impressions_each']} | {chk(imp_a >= th['min_impressions_each'])} {imp_a} |",
        f"| impressions_B ≥ {th['min_impressions_each']} | {chk(imp_b >= th['min_impressions_each'])} {imp_b} |",
        f"| SRM imbalance ≤ {th['max_imbalance']} | {chk(imb <= th['max_imbalance'])} {imb:.3f} |",
        "\n## A/B 지표",
        "| Var | Impressions | Clicks | Submits | CTR | CVR | SubmitRate |",
        "|-----|-------------|--------|---------|-----|-----|------------|",
    ]
    for v in ["A", "B"]:
        vs = s[v]
        lines.append(
            f"| {v} | {vs['impressions']:,} | {vs['clicks']:,} | {vs['submits']:,} "
            f"| {pct(vs['ctr'])} | {pct(vs['cvr'])} | {pct(vs['submit_rate'])} |"
        )
    winner_line = f"**winner**: `{s['winner']}`  " if ok else ""
    lines += [
        "\n## 결론",
        f"**status**: `{d['status']}`  ",
        f"**action**: `{d['action']}`  ",
        winner_line,
        f"\n> {d['reason']}",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="A/B 승자 판단")
    parser.add_argument("--input", default=str(DEFAULT_IN))
    args = parser.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"[ERROR] 파일 없음: {in_path}")
        sys.exit(1)

    with open(in_path, encoding="utf-8") as f:
        summary = json.load(f)

    by_var    = summary.get("by_var",  {})
    by_exp    = summary.get("by_exp",  {})
    totals    = summary.get("totals",  {})
    exp_id    = pick_exp_id(by_exp)
    a_stats   = get_var_stats(by_var, "A")
    b_stats   = get_var_stats(by_var, "B")
    total_sub = totals.get("submits", 0)

    ok, reason, action = check_samples(a_stats, b_stats, total_sub)

    total_imp = a_stats["impressions"] + b_stats["impressions"]
    imbalance = abs(a_stats["impressions"] - b_stats["impressions"]) / total_imp \
                if total_imp else 0.0

    winner = "unknown"
    if ok:
        winner = determine_winner(a_stats, b_stats)
        if winner == "unknown":
            status = "hold"
            reason = "CVR/SubmitRate 차이가 임계값 미만 — 동률 판단"
            action = "collect_more"
        else:
            status = "declare_winner"
            reason = (
                f"CVR 기준 Var {winner} 승리 "
                f"(delta={abs(a_stats['cvr'] - b_stats['cvr']):.4f})"
            )
            action = "declare_winner"
    else:
        status = "hold"

    decision = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input_file":   in_path.name,
        "exp_id":       exp_id,
        "status":       status,
        "action":       action,
        "reason":       reason,
        "thresholds":   THRESHOLDS,
        "stats": {
            "A":         a_stats,
            "B":         b_stats,
            "imbalance": round(imbalance, 4),
            "winner":    winner,
        },
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    json_path = OUTPUT_DIR / "decision.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(decision, f, ensure_ascii=False, indent=2)
    print(f"[INFO] 저장: {json_path}  status={status}  winner={winner}")

    md_path = OUTPUT_DIR / "decision.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(build_md(decision, summary))
    print(f"[INFO] 저장: {md_path}")


if __name__ == "__main__":
    main()
