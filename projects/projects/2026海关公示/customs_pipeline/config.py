import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULT_YEAR = 2026


def get_input_dir(year=DEFAULT_YEAR):
    return os.path.join(BASE_DIR, 'downloads', str(year))


def get_output_dir(year=DEFAULT_YEAR):
    return os.path.join(BASE_DIR, 'output', str(year))


def get_temp_dir(year=DEFAULT_YEAR):
    return os.path.join(BASE_DIR, 'temp', str(year))


def get_temp_docx_dir(year=DEFAULT_YEAR):
    return os.path.join(get_temp_dir(year), 'docx')


def get_input_csv(year=DEFAULT_YEAR):
    return os.path.join(get_output_dir(year), f'{year}海关公示汇总.csv')


def get_output_xlsx(year=DEFAULT_YEAR):
    return os.path.join(get_output_dir(year), f'{year}海关公示汇总.xlsx')


def get_crawl_record_csv(year=DEFAULT_YEAR):
    return os.path.join(get_output_dir(year), f'{year}爬取公示附件记录.csv')


START_URLS_FILE = os.path.join(BASE_DIR, 'start_urls.txt')

# 海关公示入口页 URL。可以填写各海关人事信息栏目页、搜索结果页或具体公示列表页。
START_URLS = [
    'http://www.customs.gov.cn/customs/302427/302434/index.html',
]

EXPECTED_CUSTOMS_DISTRICTS = [
    '上海海关',
    '乌鲁木齐海关',
    '兰州海关',
    '北京海关',
    '南京海关',
    '南宁海关',
    '南昌海关',
    '厦门海关',
    '合肥海关',
    '呼和浩特海关',
    '哈尔滨海关',
    '大连海关',
    '天津海关',
    '太原海关',
    '宁波海关',
    '广州海关',
    '成都海关',
    '拉萨海关',
    '拱北海关',
    '昆明海关',
    '杭州海关',
    '武汉海关',
    '汕头海关',
    '江门海关',
    '沈阳海关',
    '济南海关',
    '海口海关',
    '深圳海关',
    '湛江海关',
    '满洲里海关',
    '石家庄海关',
    '福州海关',
    '西宁海关',
    '西安海关',
    '贵阳海关',
    '郑州海关',
    '重庆海关',
    '银川海关',
    '长春海关',
    '长沙海关',
    '青岛海关',
    '黄埔海关',
]

# Backward-compatible aliases used by older scripts.
INPUT_DIR = get_input_dir()
OUTPUT_DIR = get_output_dir()
TEMP_DIR = get_temp_dir()
TEMP_DOCX_DIR = get_temp_docx_dir()
INPUT_CSV = get_input_csv()
OUTPUT_XLSX = get_output_xlsx()
CRAWL_RECORD_CSV = get_crawl_record_csv()
directory = INPUT_DIR
