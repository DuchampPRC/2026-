import argparse
import csv
import os
import re
import time
from html import unescape
from urllib.parse import unquote, urljoin, urlparse

from customs_pipeline.config import (
    CRAWL_RECORD_CSV,
    DEFAULT_YEAR,
    INPUT_DIR,
    START_URLS,
    START_URLS_FILE,
    get_crawl_record_csv,
    get_input_dir,
)


BeautifulSoup = None
requests = None


DEFAULT_KEYWORDS = [
    "拟录用",
    "拟聘用",
    "公示",
    "考试录用公务员",
    "事业单位",
]
ATTACHMENT_EXTENSIONS = (".doc", ".docx", ".pdf")
ALLOWED_DOMAINS = ("customs.gov.cn",)
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )
}


def ensure_dirs(year=DEFAULT_YEAR):
    os.makedirs(get_input_dir(year), exist_ok=True)
    os.makedirs(os.path.dirname(get_crawl_record_csv(year)), exist_ok=True)


def normalize_text(text):
    return re.sub(r"\s+", " ", unescape(text or "")).strip()


def is_allowed_url(url):
    host = urlparse(url).netloc.lower()
    return any(host == domain or host.endswith("." + domain) for domain in ALLOWED_DOMAINS)


def has_keyword(text, keywords):
    return any(keyword in text for keyword in keywords)


def looks_like_attachment(url):
    path = unquote(urlparse(url).path).lower()
    return path.endswith(ATTACHMENT_EXTENSIONS)


def sanitize_filename(filename):
    filename = unquote(filename).strip().strip('"')
    filename = re.sub(r'[\\/:*?"<>|]+', "_", filename)
    filename = re.sub(r"\s+", " ", filename)
    return filename or "attachment"


def filename_from_response(response, fallback_url):
    disposition = response.headers.get("Content-Disposition", "")
    match = re.search(r"filename\*=UTF-8''([^;]+)", disposition, re.I)
    if match:
        return sanitize_filename(match.group(1))

    match = re.search(r'filename="?([^";]+)"?', disposition, re.I)
    if match:
        return sanitize_filename(match.group(1))

    return sanitize_filename(os.path.basename(unquote(urlparse(fallback_url).path)))


def unique_path(directory, filename):
    name, ext = os.path.splitext(filename)
    path = os.path.join(directory, filename)
    index = 1

    while os.path.exists(path):
        path = os.path.join(directory, f"{name}_{index}{ext}")
        index += 1

    return path


def fetch(session, url, timeout=20):
    response = session.get(url, timeout=timeout)
    response.raise_for_status()
    if not response.encoding or response.encoding.lower() == "iso-8859-1":
        response.encoding = response.apparent_encoding
    return response


def extract_links(page_url, html):
    soup = BeautifulSoup(html, "html.parser")
    title = normalize_text(soup.title.get_text()) if soup.title else ""
    page_text = normalize_text(soup.get_text(" "))
    links = []

    for tag in soup.find_all("a", href=True):
        href = tag.get("href")
        link_url = urljoin(page_url, href).split("#", 1)[0]
        link_text = normalize_text(tag.get_text(" "))

        if link_url.startswith(("http://", "https://")) and is_allowed_url(link_url):
            links.append({
                "url": link_url,
                "text": link_text,
                "is_attachment": looks_like_attachment(link_url),
            })

    return title, page_text, links


def download_attachment(session, url, page_title, page_url, overwrite=False, year=DEFAULT_YEAR):
    response = fetch(session, url)
    filename = filename_from_response(response, url)

    if not filename.lower().endswith(ATTACHMENT_EXTENSIONS):
        ext = os.path.splitext(unquote(urlparse(url).path))[1]
        if ext.lower() in ATTACHMENT_EXTENSIONS:
            filename += ext

    # 添加年份前缀
    if not filename.startswith(f"{year}"):
        filename = f"{year}{filename}"

    input_dir = get_input_dir(year)
    target_path = os.path.join(input_dir, filename)
    if os.path.exists(target_path) and not overwrite:
        print(f"跳过已存在附件: {filename}")
    else:
        target_path = target_path if overwrite else unique_path(input_dir, filename)
        with open(target_path, "wb") as f:
            f.write(response.content)
        print(f"已下载: {os.path.basename(target_path)}")

    return {
        "页面标题": page_title,
        "页面地址": page_url,
        "附件地址": url,
        "本地文件": target_path,
    }


def crawl(start_urls, keywords, max_pages=100, delay=1.0, overwrite=False, year=DEFAULT_YEAR):
    global BeautifulSoup, requests

    try:
        import requests as requests_module
        from bs4 import BeautifulSoup as beautiful_soup_class
    except ImportError as exc:
        raise RuntimeError(
            "缺少爬虫依赖，请先运行: pip install requests beautifulsoup4"
        ) from exc

    requests = requests_module
    BeautifulSoup = beautiful_soup_class

    ensure_dirs(year)
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)

    queue = list(dict.fromkeys(start_urls))
    visited_pages = set()
    visited_attachments = set()
    records = []

    while queue and len(visited_pages) < max_pages:
        page_url = queue.pop(0)

        if page_url in visited_pages or not is_allowed_url(page_url):
            continue

        visited_pages.add(page_url)
        print(f"抓取页面: {page_url}")

        try:
            response = fetch(session, page_url)
        except Exception as exc:
            print(f"  [失败] 页面请求失败: {exc}")
            continue

        content_type = response.headers.get("Content-Type", "").lower()
        if looks_like_attachment(page_url) or "application/" in content_type:
            if page_url not in visited_attachments:
                visited_attachments.add(page_url)
                try:
                    records.append(download_attachment(session, page_url, "", page_url, overwrite, year))
                except Exception as exc:
                    print(f"  [失败] 附件下载失败: {exc}")
            continue

        title, page_text, links = extract_links(page_url, response.text)
        page_matches = has_keyword(title + " " + page_text, keywords)

        for link in links:
            link_text = link["text"]
            link_url = link["url"]
            link_matches = has_keyword(link_text + " " + link_url, keywords)

            if link["is_attachment"] and (page_matches or link_matches):
                if link_url in visited_attachments:
                    continue

                visited_attachments.add(link_url)
                try:
                    records.append(download_attachment(session, link_url, title, page_url, overwrite, year))
                except Exception as exc:
                    print(f"  [失败] 附件下载失败: {exc}")
                time.sleep(delay)
                continue

            if not link["is_attachment"] and link_url not in visited_pages:
                if page_matches or link_matches:
                    queue.append(link_url)

        time.sleep(delay)

    return records


def save_records(records, output_path=None, year=DEFAULT_YEAR):
    if output_path is None:
        output_path = get_crawl_record_csv(year)
    columns = ["页面标题", "页面地址", "附件地址", "本地文件"]

    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(records)

    print(f"下载记录已保存: {output_path}")


def load_start_urls(path=START_URLS_FILE):
    if not os.path.exists(path):
        return []

    urls = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            urls.append(line)

    return urls


def parse_args():
    parser = argparse.ArgumentParser(description="爬取海关公示页面并下载 Word/PDF 附件")
    parser.add_argument("urls", nargs="*", help="入口页 URL，可传入各海关人事信息页或搜索结果页")
    parser.add_argument("--url-file", default=START_URLS_FILE, help="入口页配置文件，默认读取项目根目录 start_urls.txt")
    parser.add_argument("--keyword", action="append", dest="keywords", help="追加筛选关键词，可多次传入")
    parser.add_argument("--max-pages", type=int, default=100, help="最多抓取页面数，默认 100")
    parser.add_argument("--delay", type=float, default=1.0, help="请求间隔秒数，默认 1.0")
    parser.add_argument("--overwrite", action="store_true", help="覆盖已存在的同名附件")
    return parser.parse_args()


def main():
    args = parse_args()
    start_urls = args.urls or START_URLS or load_start_urls(args.url_file)

    if not start_urls:
        print("未提供入口页 URL。")
        print("用法 1: python -m customs_pipeline.crawler \"海关公示栏目页URL\"")
        print("用法 2: 在 config.py 的 START_URLS 中配置 URL，然后直接运行 python -m customs_pipeline.crawler")
        print("用法 3: 在 start_urls.txt 中一行填写一个入口页 URL，然后直接运行 python -m customs_pipeline.crawler")
        return

    keywords = DEFAULT_KEYWORDS + (args.keywords or [])
    try:
        records = crawl(
            start_urls=start_urls,
            keywords=keywords,
            max_pages=args.max_pages,
            delay=args.delay,
            overwrite=args.overwrite,
        )
        save_records(records)
        print(f"完成，下载附件 {len(records)} 个")
    except RuntimeError as exc:
        print(f"[爬取失败] {exc}")


if __name__ == "__main__":
    main()
