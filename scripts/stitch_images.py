"""
섹션별 PNG 이미지를 세로로 이어붙여 최종 상세페이지를 생성하는 모듈

⚠️ 중요: 모든 이미지는 1200px 너비로 자동 리사이즈됩니다.
   Gemini API가 정확한 픽셀 크기를 보장하지 않기 때문에
   스티칭 전 강제로 1200px로 맞춥니다.
"""

import os
from pathlib import Path
from typing import List, Optional, Tuple
from PIL import Image, ImageFilter


# 고정 너비 (절대 변경 금지)
FIXED_WIDTH = 1200


def load_images(image_paths: List[str], target_width: int = FIXED_WIDTH) -> List[Image.Image]:
    """
    이미지 파일들을 로드하고 지정된 너비로 리사이즈합니다.

    ⚠️ 중요: 모든 이미지는 target_width로 강제 리사이즈됩니다.
    이는 Gemini API가 정확한 픽셀 크기를 생성하지 않기 때문입니다.

    Args:
        image_paths: 이미지 파일 경로 리스트
        target_width: 목표 너비 (기본값: 1200px)

    Returns:
        PIL Image 객체 리스트
    """
    images = []
    for path in image_paths:
        if os.path.exists(path):
            img = Image.open(path)
            original_size = f"{img.width}x{img.height}"

            # RGBA로 변환 (투명도 지원)
            if img.mode != 'RGBA':
                img = img.convert('RGBA')

            # 너비가 target_width와 다르면 리사이즈
            if img.width != target_width:
                ratio = target_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((target_width, new_height), Image.Resampling.LANCZOS)
                print(f"Loaded & Resized: {path} ({original_size} → {img.width}x{img.height})")
            else:
                print(f"Loaded: {path} ({img.width}x{img.height})")

            images.append(img)
        else:
            print(f"Warning: File not found - {path}")
    return images


def _blend_seams(
    canvas: Image.Image,
    seam_ys: List[int],
    blend_px: int = 32
) -> Image.Image:
    """
    섹션 경계선(seam)을 부드럽게 블렌딩합니다.
    각 seam 위치에 좁은 Gaussian blur를 적용해 경계 노이즈를 줄입니다.

    Args:
        canvas: 전체 스티칭된 캔버스 이미지 (RGBA)
        seam_ys: 각 섹션 경계의 y 좌표 리스트
        blend_px: 블렌딩 범위 (픽셀, 기본 32px — seam 위아래 16px씩)

    Returns:
        블렌딩이 적용된 캔버스
    """
    half = blend_px // 2
    for seam_y in seam_ys:
        y_start = max(0, seam_y - half)
        y_end = min(canvas.height, seam_y + half)
        if y_end <= y_start:
            continue

        band = canvas.crop((0, y_start, canvas.width, y_end))
        # 부드러운 blur (radius=3 — 자연스럽고 과하지 않은 수준)
        blurred = band.filter(ImageFilter.GaussianBlur(radius=3))
        # 원본 40% + 블러 60% 혼합 (경계 완화)
        blended = Image.blend(band.convert("RGBA"), blurred.convert("RGBA"), alpha=0.55)
        canvas.paste(blended, (0, y_start))

    return canvas


def stitch_sections(
    image_paths: List[str],
    output_path: str,
    background_color: Tuple[int, int, int, int] = (255, 255, 255, 255),
    alignment: str = "center",
    target_width: int = FIXED_WIDTH,
    seam_blend: bool = True,
    blend_px: int = 32
) -> Optional[str]:
    """
    섹션별 PNG를 세로로 이어붙여 최종 상세페이지를 생성합니다.

    ⚠️ 중요: 모든 이미지는 target_width(기본 1200px)로 강제 리사이즈됩니다.

    Args:
        image_paths: 섹션 이미지 경로 리스트 (순서대로)
        output_path: 출력 파일 경로 (.png 또는 .pdf)
        background_color: 배경 색상 (RGBA)
        alignment: 정렬 방식 ("left", "center", "right")
        target_width: 목표 너비 (기본값: 1200px)

    Returns:
        저장된 파일 경로 또는 None (실패시)
    """
    images = load_images(image_paths, target_width)

    if not images:
        print("Error: No images to stitch")
        return None

    # 전체 크기 계산 (모든 이미지가 target_width로 리사이즈됨)
    total_height = sum(img.height for img in images)
    final_width = target_width  # 고정 너비 사용

    print(f"\nStitching {len(images)} images...")
    print(f"Final size: {final_width}x{total_height} (width fixed to {target_width}px)")

    # 새 캔버스 생성
    result = Image.new('RGBA', (final_width, total_height), background_color)

    # 이미지 이어붙이기 + seam 좌표 수집
    y_offset = 0
    seam_ys = []
    for i, img in enumerate(images):
        x_offset = 0
        result.paste(img, (x_offset, y_offset), img if img.mode == 'RGBA' else None)
        print(f"  Section {i+1}: y={y_offset}, height={img.height}")
        y_offset += img.height
        # 마지막 섹션 이후엔 seam 없음
        if i < len(images) - 1:
            seam_ys.append(y_offset)

    # seam 블렌딩 적용 (ON by default)
    if seam_blend and seam_ys:
        print(f"  Applying seam blend at {len(seam_ys)} boundaries (blend_px={blend_px})...")
        result = _blend_seams(result, seam_ys, blend_px=blend_px)

    # 출력 디렉토리 생성
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # 저장
    if output_path.lower().endswith('.pdf'):
        # PDF 저장 (RGB로 변환 필요)
        rgb_result = result.convert('RGB')
        rgb_result.save(output_path, 'PDF', resolution=150)
        print(f"\nPDF saved: {output_path}")
    else:
        # PNG 저장
        result.save(output_path, 'PNG', optimize=True)
        print(f"\nPNG saved: {output_path}")

    return output_path


def stitch_from_directory(
    input_dir: str,
    output_path: str,
    section_order: Optional[List[str]] = None
) -> Optional[str]:
    """
    디렉토리 내의 섹션 이미지들을 순서대로 이어붙입니다.

    Args:
        input_dir: 섹션 이미지들이 있는 디렉토리
        output_path: 출력 파일 경로
        section_order: 섹션 파일명 순서 (없으면 자동 정렬)

    Returns:
        저장된 파일 경로
    """
    if section_order is None:
        # 기본 섹션 순서
        section_order = [
            "01_hero.png",
            "02_pain.png",
            "03_problem.png",
            "04_story.png",
            "05_solution.png",
            "06_how_it_works.png",
            "07_social_proof.png",
            "08_authority.png",
            "09_benefits.png",
            "10_risk_removal.png",
            "11_comparison.png",
            "12_target_filter.png",
            "13_final_cta.png"
        ]

    image_paths = [os.path.join(input_dir, filename) for filename in section_order]

    # 존재하는 파일만 필터링
    existing_paths = [p for p in image_paths if os.path.exists(p)]

    if not existing_paths:
        # 디렉토리 내 PNG 파일 자동 탐색
        print(f"Searching for PNG files in {input_dir}...")
        png_files = sorted([f for f in os.listdir(input_dir) if f.endswith('.png')])
        existing_paths = [os.path.join(input_dir, f) for f in png_files]

    if not existing_paths:
        print(f"Error: No PNG files found in {input_dir}")
        return None

    print(f"Found {len(existing_paths)} section images")
    return stitch_sections(existing_paths, output_path, seam_blend=True, blend_px=32)


def create_preview(
    image_path: str,
    preview_path: str,
    max_height: int = 2000
) -> Optional[str]:
    """
    미리보기용 축소 이미지를 생성합니다.

    Args:
        image_path: 원본 이미지 경로
        preview_path: 미리보기 저장 경로
        max_height: 최대 높이

    Returns:
        저장된 파일 경로
    """
    if not os.path.exists(image_path):
        print(f"Error: File not found - {image_path}")
        return None

    img = Image.open(image_path)

    if img.height > max_height:
        ratio = max_height / img.height
        new_width = int(img.width * ratio)
        img = img.resize((new_width, max_height), Image.Resampling.LANCZOS)

    Path(preview_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(preview_path, 'PNG', optimize=True)

    print(f"Preview saved: {preview_path} ({img.width}x{img.height})")
    return preview_path


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python stitch_images.py <input_dir> <output_path>")
        print("Example: python stitch_images.py output/sections output/final_page.png")
        sys.exit(1)

    input_dir = sys.argv[1]
    output_path = sys.argv[2]

    result = stitch_from_directory(input_dir, output_path)

    if result:
        print(f"\nSuccess! Final page: {result}")
    else:
        print("\nFailed to create final page")
        sys.exit(1)
