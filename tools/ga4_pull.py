# GA4 지표 수집 스크립트 — GitHub Actions cron 또는 로컬에서 실행
"""
최근 7일간 lp_impression / lp_cta_click / lp_reserve_submit 이벤트를
GA4 Data API로 가져와 metrics/ga4_<timestamp>_<mode>.json 에 저장한다.

필수 환경변수:
  GA4_PROPERTY_ID   숫자 형태의 GA4 속성 ID (예: 123456789)
  GA4_SA_JSON_B64   서비스계정 JSON을 base64 인코딩한 문자열

선택 환경변수:
  GA4_HOSTNAME      호스트네임 필터 (예: detail-page-8hw.pages.dev)
"""

import os
import sys
import json
import base64
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.analytics.data_v1beta.types import (
        RunReportRequest, Dimension, Metric, DateRange,
        FilterExpression, FilterExpressionList, Filter,
    )
    from google.oauth2 import service_account
except ImportError:
    print("[ERROR] 패키지 미설치. 실행: pip install google-analytics-data google-auth")
    sys.exit(1)

# ── 상수 ─────────────────────────────────────────────────────────────────────
TARGET_EVENTS = ["lp_impression", "lp_cta_click", "lp_reserve_submit"]

RICH_DIMENSIONS = [
    "date", "eventName",
    "customEvent:var",
    "customEvent:exp_id",
    "customEvent:cta_id",
    "customEvent:section_id",
]

BASIC_DIMENSIONS = ["date", "eventName"]

OUTPUT_DIR = Path(__file__).parent.parent / "metrics"


# ── 헬퍼 ─────────────────────────────────────────────────────────────────────

def load_credentials(sa_json_b64: str):
    """base64 인코딩된 서비스계정 JSON으로 credentials를 만든다."""
    try:
        sa_json = base64.b64decode(sa_json_b64).decode("utf-8")
        sa_info = json.loads(sa_json)
    except Exception as e:
        print(f"[ERROR] GA4_SA_JSON_B64 디코딩 실패: {e}")
        sys.exit(1)

    try:
        return service_account.Credentials.from_service_account_info(
            sa_info,
            scopes=["https://www.googleapis.com/auth/analytics.readonly"],
        )
    except Exception as e:
        print(f"[ERROR] Credentials 생성 실패: {e}")
        sys.exit(1)


def build_event_filter() -> FilterExpression:
    """수집 대상 3개 이벤트에 대한 OR 필터를 반환한다."""
    return FilterExpression(
        or_group=FilterExpressionList(expressions=[
            FilterExpression(filter=Filter(
                field_name="eventName",
                string_filter=Filter.StringFilter(
                    match_type=Filter.StringFilter.MatchType.EXACT,
                    value=ev,
                ),
            ))
            for ev in TARGET_EVENTS
        ])
    )


def run_report(client, property_id: str,
               dimensions: list, hostname: Optional[str]) -> dict:
    """runReport를 실행하고 rows/headers 딕셔너리를 반환한다."""
    response = client.run_report(RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name=d) for d in dimensions],
        metrics=[Metric(name="eventCount")],
        date_ranges=[DateRange(start_date="7daysAgo", end_date="today")],
        dimension_filter=build_event_filter(),
    ))

    dim_headers = [h.name for h in response.dimension_headers]
    met_headers = [h.name for h in response.metric_headers]

    rows = []
    for row in response.rows:
        dim_vals = [v.value for v in row.dimension_values]
        met_vals = [v.value for v in row.metric_values]
        # hostname 후처리 필터 (API가 직접 지원하지 않는 경우 대비)
        row_map = dict(zip(dim_headers, dim_vals))
        if hostname and row_map.get("hostname") not in (None, "", hostname):
            continue
        rows.append({"dimensions": dim_vals, "metrics": met_vals})

    return {
        "dimension_headers": dim_headers,
        "metric_headers":    met_headers,
        "rows":              rows,
        "row_count":         len(rows),
    }


def save(result: dict, mode: str) -> Path:
    """metrics/ga4_<timestamp>_<mode>.json 으로 저장하고 경로를 반환한다."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts   = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = OUTPUT_DIR / f"ga4_{ts}_{mode}.json"
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(result, fp, ensure_ascii=False, indent=2)
    return path


# ── 메인 ─────────────────────────────────────────────────────────────────────

def main() -> None:
    property_id = os.environ.get("GA4_PROPERTY_ID", "").strip()
    sa_json_b64 = os.environ.get("GA4_SA_JSON_B64", "").strip()
    hostname    = os.environ.get("GA4_HOSTNAME",    "").strip() or None

    if not property_id:
        print("[ERROR] 환경변수 GA4_PROPERTY_ID 가 없습니다.")
        sys.exit(1)
    if not sa_json_b64:
        print("[ERROR] 환경변수 GA4_SA_JSON_B64 가 없습니다.")
        sys.exit(1)

    print(f"[INFO] 속성 ID   : {property_id}")
    print(f"[INFO] 호스트 필터: {hostname or '(없음)'}")

    credentials = load_credentials(sa_json_b64)
    client      = BetaAnalyticsDataClient(credentials=credentials)

    # rich 시도 → 커스텀 디멘션 미등록이면 basic fallback
    mode   = "rich"
    result = None
    try:
        print("[INFO] rich 모드 시도 (커스텀 디멘션 포함)...")
        result = run_report(client, property_id, RICH_DIMENSIONS, hostname)
        print(f"[INFO] rich 성공 — {result['row_count']}행")
    except Exception as e:
        err = str(e).lower()
        is_dim_err = any(k in err for k in ("dimension", "not found", "invalid", "unregistered"))
        if is_dim_err:
            print(f"[WARN] 커스텀 디멘션 미등록 → basic fallback: {e}")
            mode = "basic"
            try:
                result = run_report(client, property_id, BASIC_DIMENSIONS, hostname)
                print(f"[INFO] basic 성공 — {result['row_count']}행")
            except Exception as e2:
                print(f"[ERROR] basic 모드도 실패: {e2}")
                sys.exit(1)
        else:
            print(f"[ERROR] runReport 실패: {e}")
            sys.exit(1)

    result["meta"] = {
        "mode":           mode,
        "property_id":    property_id,
        "hostname_filter": hostname,
        "pulled_at":      datetime.now(timezone.utc).isoformat(),
        "date_range":     "7daysAgo ~ today",
        "target_events":  TARGET_EVENTS,
    }

    out_path = save(result, mode)
    print(f"[INFO] 저장 완료: {out_path}")


if __name__ == "__main__":
    main()
