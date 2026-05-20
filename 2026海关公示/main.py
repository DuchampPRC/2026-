import argparse
import importlib.util
import os

from customs_pipeline.config import DEFAULT_YEAR, START_URLS, get_input_dir, get_input_csv, get_output_xlsx, get_temp_docx_dir
from customs_pipeline.converter import convert_doc_to_docx
from customs_pipeline.crawler import crawl, save_records
from customs_pipeline.extractor import build_csv
from customs_pipeline.exporter import csv_to_excel
from customs_pipeline.normalizer import rename_customs_files
from customs_pipeline.validator import validate_docx_completeness


REQUIRED_MODULES = {
    "openpyxl": "openpyxl",
    "docx": "python-docx",
}
OPTIONAL_MODULES = {
    "requests": "requests",
    "bs4": "beautifulsoup4",
    "win32com": "pywin32",
}


def module_exists(module_name):
    return importlib.util.find_spec(module_name) is not None


def check_dependencies(include_optional=False):
    missing_required = [
        package for module, package in REQUIRED_MODULES.items()
        if not module_exists(module)
    ]
    missing_optional = [
        package for module, package in OPTIONAL_MODULES.items()
        if not module_exists(module)
    ]

    if missing_required:
        print("缺少必要依赖，部分流程无法运行：")
        print("  " + " ".join(missing_required))
        print("请先运行: pip install -r requirements.txt")
        return False

    if include_optional and missing_optional:
        print("提示：以下可选依赖缺失，相关功能可能跳过或失败：")
        print("  " + " ".join(missing_optional))
        print("完整安装命令: pip install -r requirements.txt")

    return True


def count_files(year=DEFAULT_YEAR):
    input_dir = get_input_dir(year)
    temp_docx_dir = get_temp_docx_dir(year)
    doc_count = len([
        f for f in os.listdir(input_dir)
        if f.lower().endswith(".doc") and not f.lower().endswith(".docx")
    ]) if os.path.exists(input_dir) else 0
    docx_count = len([
        f for f in os.listdir(temp_docx_dir)
        if f.lower().endswith(".docx")
    ]) if os.path.exists(temp_docx_dir) else 0
    return doc_count, docx_count


def run_crawler(args, year=DEFAULT_YEAR):
    start_urls = args.urls or START_URLS
    if not start_urls:
        print("未配置爬虫入口 URL，跳过爬取。")
        return

    try:
        records = crawl(
            start_urls=start_urls,
            keywords=args.keywords,
            max_pages=args.max_pages,
            delay=args.delay,
            overwrite=args.overwrite,
            year=year,
        )
        save_records(records, year=year)
        print(f"爬取完成，下载附件 {len(records)} 个")
    except RuntimeError as exc:
        print(f"[爬取跳过] {exc}")


def run_pipeline(args, year=DEFAULT_YEAR):
    input_dir = get_input_dir(year)
    input_csv = get_input_csv(year)
    output_xlsx = get_output_xlsx(year)

    os.makedirs(input_dir, exist_ok=True)

    if args.crawl:
        print(f"\n[{year}年 1/5] 爬取公示附件")
        run_crawler(args, year)
    else:
        print(f"\n[{year}年 1/5] 跳过爬取。如需联网下载附件，请加参数 --crawl")

    print(f"\n[{year}年 2/5] 规范文件名")
    rename_customs_files(input_dir, year)

    print(f"\n[{year}年 3/5] 转换 .doc 为 .docx")
    try:
        convert_doc_to_docx(input_dir=input_dir, overwrite=args.overwrite, year=year)
    except RuntimeError as exc:
        print(f"[转换跳过] {exc}")

    doc_count, docx_count = count_files(year)
    print(f"当前文件统计: downloads/{year}/.doc={doc_count}, temp/{year}/docx/.docx={docx_count}")

    print(f"\n[{year}年 4/6] 检查 42 个关区 docx 是否齐全")
    docx_ready = validate_docx_completeness(input_dir, year=year)

    print(f"\n[{year}年 5/6] 生成 CSV 汇总")
    if docx_ready:
        csv_created = build_csv(auto_convert=False, year=year)
    else:
        print("docx 文件未齐全，跳过本次 CSV 重新生成。")
        csv_created = False

    print(f"\n[{year}年 6/6] 生成 Excel 汇总")
    if not csv_created and os.path.exists(input_csv):
        print("本次未重新生成 CSV，将使用已有 CSV 生成 Excel。")
    csv_to_excel(input_csv, output_xlsx, year)

    print("\n流程结束")
    print(f"CSV: {input_csv if os.path.exists(input_csv) else '未生成'}")
    print(f"Excel: {output_xlsx if os.path.exists(output_xlsx) else '未生成'}")


def parse_args():
    parser = argparse.ArgumentParser(description="海关公示数据一键处理流程（支持多年份）")
    parser.add_argument("urls", nargs="*", help="可选：爬虫入口页 URL")
    parser.add_argument("--crawl", action="store_true", help="启用爬虫下载附件")
    parser.add_argument("--keyword", action="append", dest="extra_keywords", default=[], help="追加爬虫关键词")
    parser.add_argument("--max-pages", type=int, default=100, help="爬虫最多抓取页面数")
    parser.add_argument("--delay", type=float, default=1.0, help="爬虫请求间隔秒数")
    parser.add_argument("--overwrite", action="store_true", help="覆盖已存在文件")
    parser.add_argument("--year", type=int, default=DEFAULT_YEAR, help="处理年份（默认 2026）")
    return parser.parse_args()


def main():
    args = parse_args()

    from customs_pipeline.crawler import DEFAULT_KEYWORDS
    args.keywords = DEFAULT_KEYWORDS + args.extra_keywords

    if not check_dependencies(include_optional=True):
        return

    run_pipeline(args, year=args.year)


if __name__ == "__main__":
    main()
