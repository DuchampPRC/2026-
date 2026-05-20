"""
海关公示数据提取模块。
从 Word 文档中提取结构化数据。
"""

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from customs_pipeline.config import (
    DEFAULT_YEAR,
    ensure_dir,
    get_input_dir,
    get_output_dir,
    get_temp_docx_dir,
)
from customs_pipeline.converter import convert_doc_to_docx
from customs_pipeline.constants import (
    classify_school,
    extract_district_from_filename,
    parse_position_field,
)

# =============================================================================
# Types
# =============================================================================

@dataclass
class Record:
    """单条公示记录。"""
    关区: str
    姓名: str
    性别: str
    准考证号: str
    学历: str
    毕业院校: str
    工作单位: str
    职位代码: str = ""
    隶属关: str = ""
    职务职位: str = ""
    原始职位: str = ""
    高校分类: str = ""

    def __post_init__(self):
        """解析职位字段。"""
        if not self.职位代码:
            parsed = parse_position_field(self.原始职位)
            self.职位代码 = parsed["职位代码"]
            self.隶属关 = parsed["隶属关"]
            self.职务职位 = parsed["职务职位"]

# =============================================================================
# Constants
# =============================================================================

# CSV 列顺序
CSV_COLUMNS: list[str] = [
    '关区', '拟录用职位及代码', '姓名', '性别',
    '准考证号', '学历', '毕业院校', '工作单位'
]

# 表头关键词（用于识别表头行）
HEADER_KEYWORDS: list[str] = [
    '姓名', '职位', '代码', '准考证', '学历', '院校', '工作', '性别', '关区'
]

# 需要跳过的人员名称
SKIP_NAMES: set[str] = {'姓名', '合计', '备注', '/', '序号', '编号'}

# 列名映射（支持多种命名变体）
COLUMN_MAPPINGS: dict[str, list[str]] = {
    'position': ['职位', '代码', '岗位', '拟录用职位'],
    'name': ['姓名'],
    'gender': ['性别'],
    'exam_id': ['准考证'],
    'edu': ['学历'],
    'school': ['毕业院校', '院校'],
    'work': ['工作单位'],
    'district': ['关区', '招录机关'],
}

# 预编译正则表达式
_SKIP_NAME_PATTERNS = [re.compile(r'公示'), re.compile(r'^[0-9]+$')]


# =============================================================================
# Helper Functions
# =============================================================================

def should_skip_name(name: str) -> bool:
    """判断是否为需要跳过的姓名。"""
    name = name.strip()
    if not name or name in SKIP_NAMES:
        return True
    # 检查正则模式
    for pattern in _SKIP_NAME_PATTERNS:
        if pattern.search(name):
            return True
    return False


def normalize_header(header: str) -> str:
    """标准化表头文本。"""
    return header.replace('\n', '').replace(' ', '').replace('\r', '')


def match_column(header: str, target: str) -> bool:
    """检查表头是否匹配目标列。"""
    normalized = normalize_header(header)
    target_headers = COLUMN_MAPPINGS.get(target, [])
    return any(t in normalized for t in target_headers)


def find_header_row(table) -> tuple[int, list[str]]:
    """在表格中找到表头行。
    
    策略：
    1. 如果某行包含"姓名"列，直接使用（表头行或数据行）
    2. 否则要求至少3个关键词匹配
    """
    for i, row in enumerate(table.rows[:10]):  # 检查前10行（可能有多行表头）
        cells = [normalize_header(cell.text) for cell in row.cells]
        # 方案1：包含"姓名"列的就是有效数据行
        if any('姓名' in c for c in cells):
            return i, [cell.text.strip() for cell in row.cells]
        # 方案2：至少3个关键词匹配
        score = sum(1 for kw in HEADER_KEYWORDS if any(kw in c for c in cells))
        if score >= 3:
            return i, [cell.text.strip() for cell in row.cells]
    return -1, []


def build_column_map(headers: list[str]) -> dict[str, int]:
    """根据表头构建列索引映射。"""
    col_map = {}
    for c, header in enumerate(headers):
        for col_name, keywords in COLUMN_MAPPINGS.items():
            if any(kw in normalize_header(header) for kw in keywords):
                col_map[col_name] = c
                break
    return col_map


def get_cell_text(row, col_idx: int, default: str = '') -> str:
    """安全获取单元格文本。"""
    try:
        cells = row.cells
        if col_idx >= len(cells):
            return default
        return normalize_header(cells[col_idx].text) or default
    except Exception:
        return default


def get_cell_value(row, col_idx: int, default: str = '') -> str:
    """获取单元格原始值（保留格式）。"""
    try:
        cells = row.cells
        if col_idx >= len(cells):
            return default
        text = cells[col_idx].text.strip().replace('\n', '').replace('\r', '')
        return text if text else default
    except Exception:
        return default


# =============================================================================
# Core Parsing Functions
# =============================================================================

def parse_docx(docx_path: Path, district: str) -> list[dict]:
    """解析单个 docx 文件并提取数据。
    
    支持一个文件中有多个表格的情况。
    如果后续表格没有表头，会复用第一个表格的列映射。
    """
    from docx import Document

    doc = Document(docx_path)
    results = []
    
    # 记录第一个有效表格的列映射
    first_col_map = None

    for table in doc.tables:
        idx, headers = find_header_row(table)
        
        if idx >= 0:
            # 有表头的表格
            col_map = build_column_map(headers)
            if 'name' not in col_map:
                continue
            # 保存第一个表格的列映射
            if first_col_map is None:
                first_col_map = col_map
            start_idx = idx + 1
        elif first_col_map is not None:
            # 没有表头但有已知的列映射，复用
            col_map = first_col_map
            start_idx = 0
        else:
            # 没有表头也没有已知的列映射，跳过
            continue

        for row in table.rows[start_idx:]:
            name = get_cell_value(row, col_map.get('name', 0))
            if should_skip_name(name):
                continue

            # 检查列数是否足够
            max_col = max(col_map.values()) if col_map else 0
            if len(row.cells) <= max_col:
                continue

            results.append({
                '关区': get_cell_value(row, col_map.get('district', 0)) if 'district' in col_map else district,
                '拟录用职位及代码': get_cell_value(row, col_map.get('position', 0)),
                '姓名': name,
                '性别': get_cell_value(row, col_map.get('gender', 0)),
                '准考证号': get_cell_value(row, col_map.get('exam_id', 0)),
                '学历': get_cell_value(row, col_map.get('edu', 0)),
                '毕业院校': get_cell_value(row, col_map.get('school', 0)),
                '工作单位': get_cell_value(row, col_map.get('work', 0)),
            })

    return results


# =============================================================================
# CSV Export Functions
# =============================================================================

def write_csv(data: list[dict], output_path: Path) -> bool:
    """写入 CSV 文件。"""
    if not data:
        return False

    ensure_dir(output_path.parent)
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(data)
    return True


# =============================================================================
# Main Build Function
# =============================================================================

def build_csv(
    auto_convert: bool = True,
    docx_dir: Optional[Path] = None,
    year: int = DEFAULT_YEAR,
) -> bool:
    """
    构建 CSV 文件。

    Args:
        auto_convert: 是否自动转换 doc 为 docx
        docx_dir: docx 文件目录，None 则使用默认目录
        year: 年份

    Returns:
        是否成功
    """
    input_dir = get_input_dir(year)
    output_dir = get_output_dir(year)

    if docx_dir is None:
        docx_dir = get_temp_docx_dir(year)

    ensure_dir(output_dir)

    # 自动转换 doc 到 docx
    if auto_convert:
        try:
            convert_doc_to_docx(input_dir=input_dir, year=year)
        except RuntimeError as e:
            print(f"[转换提示] {e}")
            print("将继续处理目录中已有的 .docx 文件")

    ensure_dir(docx_dir)

    # 收集 docx 文件
    docx_files = list(docx_dir.glob('*.docx'))
    doc_files = set(input_dir.glob('*.doc')) - set(input_dir.glob('*.docx'))

    if not docx_files and doc_files:
        print(f"\n发现 {len(doc_files)} 个 .doc 文件，但没有可解析的 .docx 文件。")
        print("请先安装 pywin32，并确认本机 Word/WPS 可用。")
        print(f"也可以手动将 downloads/{year} 目录中的 .doc 文件另存为 .docx。")
        return False

    if not docx_files:
        print(f"\n未发现 .docx 文件，请先将公示文件放入 downloads/{year} 目录。")
        return False

    # 处理每个文件
    all_data = []
    for docx_file in docx_files:
        district = extract_district_from_filename(docx_file.name)
        print(f"处理: {docx_file.name}")

        try:
            data = parse_docx(docx_file, district)
            all_data.extend(data)
            print(f"  -> {len(data)} 条")
        except Exception as e:
            print(f"  [异常] {docx_file.name}: {e}")

    if all_data:
        output_path = output_dir / f'{year}海关公示汇总.csv'
        write_csv(all_data, output_path)
        print(f"\n完成，共 {len(all_data)} 条，保存至: {output_path}")
        return True

    print("\n未提取到数据")
    return False


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == '__main__':
    build_csv()
