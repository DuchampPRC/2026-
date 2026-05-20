"""
海关公示数据处理配置模块。
统一管理路径配置、关区列表等常量。
"""

from pathlib import Path
from typing import Final

# =============================================================================
# Base Path
# =============================================================================

# 项目根目录（customs_pipeline 上一级）
BASE_DIR: Final[Path] = Path(__file__).parent.parent

# =============================================================================
# Year Configuration
# =============================================================================

DEFAULT_YEAR: Final[int] = 2026


def get_year() -> int:
    """获取当前处理年份。"""
    return DEFAULT_YEAR


# =============================================================================
# Directory Paths
# =============================================================================

def get_input_dir(year: int = DEFAULT_YEAR) -> Path:
    """获取原始文件输入目录。"""
    return BASE_DIR / "downloads" / str(year)


def get_output_dir(year: int = DEFAULT_YEAR) -> Path:
    """获取输出目录。"""
    return BASE_DIR / "output" / str(year)


def get_temp_dir(year: int = DEFAULT_YEAR) -> Path:
    """获取临时文件目录。"""
    return BASE_DIR / "temp" / str(year)


def get_temp_docx_dir(year: int = DEFAULT_YEAR) -> Path:
    """获取 docx 转换临时目录。"""
    return get_temp_dir(year) / "docx"


# =============================================================================
# File Paths
# =============================================================================

def get_input_csv(year: int = DEFAULT_YEAR) -> Path:
    """获取输入 CSV 路径。"""
    return get_output_dir(year) / f"{year}海关公示汇总.csv"


def get_output_xlsx(year: int = DEFAULT_YEAR) -> Path:
    """获取输出 Excel 路径。"""
    return get_output_dir(year) / f"{year}海关公示汇总.xlsx"


def get_crawl_record_csv(year: int = DEFAULT_YEAR) -> Path:
    """获取爬取记录 CSV 路径。"""
    return get_output_dir(year) / f"{year}爬取公示附件记录.csv"


# =============================================================================
# Crawler Configuration
# =============================================================================

START_URLS_FILE: Final[Path] = BASE_DIR / "start_urls.txt"

# 海关公示入口页 URL
START_URLS: Final[list[str]] = [
    'http://www.customs.gov.cn/customs/302427/302434/index.html',
]

# 预期关区列表
EXPECTED_CUSTOMS_DISTRICTS: Final[list[str]] = [
    '上海海关', '乌鲁木齐海关', '兰州海关', '北京海关', '南京海关',
    '南宁海关', '南昌海关', '厦门海关', '合肥海关', '呼和浩特海关',
    '哈尔滨海关', '大连海关', '天津海关', '太原海关', '宁波海关',
    '广州海关', '成都海关', '拉萨海关', '拱北海关', '昆明海关',
    '杭州海关', '武汉海关', '汕头海关', '江门海关', '沈阳海关',
    '济南海关', '海口海关', '深圳海关', '湛江海关', '满洲里海关',
    '石家庄海关', '福州海关', '西宁海关', '西安海关', '贵阳海关',
    '郑州海关', '重庆海关', '银川海关', '长春海关', '长沙海关',
    '青岛海关', '黄埔海关',
]

# =============================================================================
# Backward-Compatible Aliases
# =============================================================================

# 为了向后兼容，保留旧的变量名
INPUT_DIR: Final[Path] = get_input_dir()
OUTPUT_DIR: Final[Path] = get_output_dir()
TEMP_DIR: Final[Path] = get_temp_dir()
TEMP_DOCX_DIR: Final[Path] = get_temp_docx_dir()
INPUT_CSV: Final[Path] = get_input_csv()
OUTPUT_XLSX: Final[Path] = get_output_xlsx()
CRAWL_RECORD_CSV: Final[Path] = get_crawl_record_csv()
directory: Final[Path] = INPUT_DIR


# =============================================================================
# Utility Functions
# =============================================================================

def ensure_dir(path: Path) -> Path:
    """确保目录存在，返回路径。"""
    path.mkdir(parents=True, exist_ok=True)
    return path


def validate_year(year: int) -> bool:
    """验证年份是否有效。"""
    return 2000 <= year <= 2100
