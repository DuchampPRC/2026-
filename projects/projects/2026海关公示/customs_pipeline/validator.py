import os
import re

from customs_pipeline.config import DEFAULT_YEAR, EXPECTED_CUSTOMS_DISTRICTS, get_input_dir, get_temp_docx_dir


def extract_district_from_filename(filename):
    """从带年份前缀的文件名中提取关区名，如 '2026上海海关.doc' -> '上海海关'"""
    m = re.search(r'([\u4e00-\u9fa5]+海关)', filename)
    return m.group(1) if m else None


def collect_customs_files(input_dir=None, docx_dir=None, year=DEFAULT_YEAR):
    if input_dir is None:
        input_dir = get_input_dir(year)
    if docx_dir is None:
        docx_dir = get_temp_docx_dir(year)

    doc_files = set()
    docx_files = set()

    if os.path.exists(input_dir):
        for filename in os.listdir(input_dir):
            ext = os.path.splitext(filename)[1].lower()
            district = extract_district_from_filename(filename)
            if district in EXPECTED_CUSTOMS_DISTRICTS and ext == '.doc':
                doc_files.add(district)

    if os.path.exists(docx_dir):
        for filename in os.listdir(docx_dir):
            ext = os.path.splitext(filename)[1].lower()
            district = extract_district_from_filename(filename)
            if district in EXPECTED_CUSTOMS_DISTRICTS and ext == '.docx':
                docx_files.add(district)

    return doc_files, docx_files


def validate_docx_completeness(input_dir=None, docx_dir=None, expected_districts=EXPECTED_CUSTOMS_DISTRICTS, year=DEFAULT_YEAR):
    if input_dir is None:
        input_dir = get_input_dir(year)
    if docx_dir is None:
        docx_dir = get_temp_docx_dir(year)

    doc_files, docx_files = collect_customs_files(input_dir, docx_dir, year)
    expected = set(expected_districts)
    missing_docx = sorted(expected - docx_files, key=expected_districts.index)
    extra_docx = sorted(docx_files - expected)

    print(f"\n=== {year}年关区 docx 完整性检查 ===")
    print(f"docx 检查目录: {docx_dir}")
    print(f"应有关区数: {len(expected_districts)}")
    print(f"已发现 .docx 关区数: {len(docx_files)}")
    print(f"仍只有 .doc 的关区数: {len((expected - docx_files) & doc_files)}")

    if extra_docx:
        print("发现未在预期清单中的 .docx 文件：")
        for district in extra_docx:
            print(f"  - {district}")

    if missing_docx:
        print("缺少以下关区的 .docx 文件：")
        for district in missing_docx:
            suffix = "（已有 .doc，待转换）" if district in doc_files else "（未发现 .doc/.docx）"
            print(f"  - {district}{suffix}")
        return False

    print(f"检查通过：{len(expected_districts)} 个关区的 .docx 文件已齐全。")
    return True


if __name__ == '__main__':
    validate_docx_completeness()
