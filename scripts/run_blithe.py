"""
BLITHE 안티-폴루에이징 포어 클렌징 밤 상세페이지 생성 스크립트
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.generate_page import generate_landing_page

# BLITHE 제품 brief
blithe_brief = {
    "product_name": "BLITHE 안티-폴루에이징 포어 클렌징 밤",
    "one_liner": "1번의 클렌징으로 미세먼지 제거 + 모공 케어 + 안티에이징까지",
    "target_audience": "도심 환경에 매일 노출되는 30-40대 여성 중 모공·피부 트러블 고민자",
    "main_problem": "일반 클렌저로는 도심 미세먼지가 쌓인 모공을 제대로 비우기 어렵고, 노화까지 동시에 잡기 불가능",
    "key_benefit": "그린 티 씨드 오일 성분이 모공 속 노폐물·미세먼지를 한 번에 녹여내고, 피부 노화 원인인 폴루션 스트레스까지 차단",
    "price": {
        "original": "45,000원",
        "discounted": "34,900원",
        "period": ""
    },
    "urgency": {
        "type": "quantity",
        "value": "선착순 200개 특가",
        "bonus": "미니 클렌징 오일 증정"
    },
    "testimonials": [
        {"text": "모공이 눈에 띄게 줄었어요. 클렌징 후 피부가 촉촉해서 깜짝 놀랐습니다.", "name": "김**", "result": "2주 사용 후 모공 개선"},
        {"text": "회사 다니면서 미세먼지 걱정이 많았는데, 이거 하나로 깔끔하게 해결됐어요.", "name": "박**", "result": "4주 사용, 피부 톤 개선"},
        {"text": "밤 텍스처라 처음엔 걱정했는데 오일처럼 녹아서 세정이 완벽해요.", "name": "이**", "result": "한 달째 재구매"}
    ],
    "creator_bio": "BLITHE는 서울에서 시작된 K-뷰티 브랜드로, 도심 여성을 위한 안티-폴루션 스킨케어를 전문으로 합니다.",
    "guarantee": "30일 이내 피부 개선이 없으면 100% 환불 보장",
    "style_preset": "luxury",
    "brand_colors": {
        "primary": "#1B4332",
        "secondary": "#2D6A4F",
        "accent": "#B7E4C7"
    },
    "product_details": {
        "key_ingredients": ["그린 티 씨드 오일", "녹차 추출물", "식물성 클렌징 오일"],
        "texture": "클렌징 밤 → 오일 전환",
        "size": "50ml",
        "usage": "매일 저녁 메이크업 리무버 & 클렌저로 사용"
    }
}

if __name__ == "__main__":
    print("=" * 60)
    print("BLITHE 안티-폴루에이징 포어 클렌징 밤 상세페이지 생성")
    print("=" * 60)

    result = generate_landing_page(
        brief=blithe_brief,
        output_dir="output/blithe",
        skip_generation=False
    )

    if result:
        print(f"\n완료! 결과물: {result}")
    else:
        print("\n생성 실패. 로그를 확인하세요.")
