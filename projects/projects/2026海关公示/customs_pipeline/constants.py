"""
共享常量模块。
定义海关公示数据处理相关的常量、配置和辅助函数。
"""

import re
from typing import Final

# =============================================================================
# 985/211 高校名单
# =============================================================================

ELITE_SCHOOLS: Final[frozenset[str]] = frozenset({
    "北京大学", "清华大学", "复旦大学", "上海交通大学", "浙江大学",
    "南京大学", "中国人民大学", "中国科学技术大学", "华中科技大学",
    "武汉大学", "中山大学", "四川大学", "西安交通大学", "哈尔滨工业大学",
    "北京航空航天大学", "同济大学", "北京师范大学", "东南大学", "南开大学",
})


# =============================================================================
# 海关关区官网 URL 映射
# =============================================================================

DISTRICT_URLS: Final[dict[str, str]] = {
    "深圳海关": "http://shenzhen.customs.gov.cn",
    "广州海关": "http://guangzhou.customs.gov.cn",
    "黄埔海关": "http://huangpu.customs.gov.cn",
    "拱北海关": "http://gongbei.customs.gov.cn",
    "汕头海关": "http://shantou.customs.gov.cn",
    "江门海关": "http://jiangmen.customs.gov.cn",
    "湛江海关": "http://zhanjiang.customs.gov.cn",
    "南宁海关": "http://nanning.customs.gov.cn",
    "海口海关": "http://haikou.customs.gov.cn",
    "重庆海关": "http://chongqing.customs.gov.cn",
    "西安海关": "http://xian.customs.gov.cn",
    "乌鲁木齐海关": "http://wulumuqi.customs.gov.cn",
    "兰州海关": "http://lanzhou.customs.gov.cn",
    "银川海关": "http://yinchuan.customs.gov.cn",
    "西宁海关": "http://xining.customs.gov.cn",
    "成都海关": "http://chengdu.customs.gov.cn",
    "贵阳海关": "http://guiyang.customs.gov.cn",
    "昆明海关": "http://kunming.customs.gov.cn",
    "拉萨海关": "http://lasa.customs.gov.cn",
    "呼和浩特海关": "http://huhehaote.customs.gov.cn",
    "满洲里海关": "http://manzhouli.customs.gov.cn",
    "哈尔滨海关": "http://haerbin.customs.gov.cn",
    "长春海关": "http://changchun.customs.gov.cn",
    "沈阳海关": "http://shenyang.customs.gov.cn",
    "大连海关": "http://dalian.customs.gov.cn",
    "石家庄海关": "http://shijiazhuang.customs.gov.cn",
    "太原海关": "http://taiyuan.customs.gov.cn",
    "天津海关": "http://tianjin.customs.gov.cn",
    "青岛海关": "http://qingdao.customs.gov.cn",
    "济南海关": "http://jinan.customs.gov.cn",
    "烟台海关": "http://yantai.customs.gov.cn",
    "临沂海关": "http://linyi.customs.gov.cn",
    "上海海关": "http://shanghai.customs.gov.cn",
    "南京海关": "http://nanjing.customs.gov.cn",
    "杭州海关": "http://hangzhou.customs.gov.cn",
    "宁波海关": "http://ningbo.customs.gov.cn",
    "合肥海关": "http://hefei.customs.gov.cn",
    "福州海关": "http://fuzhou.customs.gov.cn",
    "厦门海关": "http://xiamen.customs.gov.cn",
    "南昌海关": "http://nanchang.customs.gov.cn",
    "长沙海关": "http://changsha.customs.gov.cn",
    "武汉海关": "http://wuhan.customs.gov.cn",
    "郑州海关": "http://zhengzhou.customs.gov.cn",
}


# =============================================================================
# 职位级别匹配模式
# =============================================================================

LEVEL_PATTERNS: Final[list[tuple[str, str]]] = [
    (r"一级(?:主任|主办|行政执法员)", "一级"),
    (r"二级(?:主任|主办|行政执法员)", "二级"),
    (r"三级(?:主任|主办|行政执法员)", "三级"),
    (r"四级(?:主任|主办|行政执法员)", "四级"),
    (r"一级行政执法员", "一级行政执法员"),
]


# =============================================================================
# 预编译正则表达式
# =============================================================================

def _compile_patterns() -> dict[str, re.Pattern]:
    """编译并缓存正则表达式。"""
    return {
        "level": re.compile(r"(?:一级|二级|三级|四级)(?:主任|主办|行政执法员)"),
        "level_rank": re.compile(r"(?:一级|二级|三级|四级)"),
        "district": re.compile(r'([\u4e00-\u9fa5]+海关)'),
    }


COMPILED_PATTERNS: Final[dict[str, re.Pattern]] = _compile_patterns()


# =============================================================================
# 辅助函数
# =============================================================================

def classify_school(school: str | None) -> str:
    """
    根据学校名称判断是否为 985/211 院校。

    Args:
        school: 学校名称

    Returns:
        "985/211" 或 "其他"
    """
    return "985/211" if school and school in ELITE_SCHOOLS else "其他"


def extract_level(position: str | None) -> str:
    """
    从职位名称中提取级别。

    Args:
        position: 职位名称

    Returns:
        级别名称或 "其他"
    """
    if not position:
        return "其他"
    for pattern, label in LEVEL_PATTERNS:
        if COMPILED_PATTERNS["level"].search(position):
            return label
    return "其他"


def get_district_url(district: str) -> str | None:
    """
    获取关区官网 URL。

    Args:
        district: 关区名称

    Returns:
        官网 URL 或 None
    """
    return DISTRICT_URLS.get(district)


def extract_district_from_filename(filename: str) -> str:
    """
    从文件名中提取关区名称。

    Args:
        filename: 文件名

    Returns:
        关区名称
    """
    match = COMPILED_PATTERNS["district"].search(filename)
    return match.group(1) if match else ""


# =============================================================================
# 职位解析
# =============================================================================

# 职位代码正则（12位数字）
POSITION_CODE_PATTERN: Final[re.Pattern] = re.compile(r"（(\d{12})）|\((\d{12})\)")


def parse_position_field(position_field: str | None) -> dict[str, str]:
    """
    解析"拟录用职位及代码"字段。

    字段格式：隶属海关名称 + 职位名称 + （职位代码）
    例如： 上海浦东国际机场海关海关业务二级主办及以下职位（300110101001）

    Args:
        position_field: 原始职位字段

    Returns:
        包含以下键的字典：
        - 隶属关: 隶属海关名称（如"上海浦东国际机场海关"）
        - 职务职位: 职位名称（如"海关业务二级主办及以下职位"）
        - 职位代码: 职位代码（如"300110101001"）
        - 原始值: 原始字段（保留）

    Example:
        >>> parse_position_field("上海浦东国际机场海关海关业务二级主办及以下职位（300110101001）")
        {
            "隶属关": "上海浦东国际机场海关",
            "职务职位": "海关业务二级主办及以下职位",
            "职位代码": "300110101001",
            "原始值": "上海浦东国际机场海关海关业务二级主办及以下职位（300110101001）"
        }
    """
    if not position_field:
        return {
            "隶属关": "",
            "职务职位": "",
            "职位代码": "",
            "原始值": ""
        }

    # 提取职位代码
    code_match = POSITION_CODE_PATTERN.search(position_field)
    position_code = code_match.group(1) or code_match.group(2) if code_match else ""

    # 移除代码部分，获取职位主体
    if code_match:
        position_main = position_field[:code_match.start()].strip()
    else:
        position_main = position_field

    # 职位主体 = 隶属关 + 职务职位
    # 原始数据中可能有重复的"海关"后缀，需要特殊处理
    # 例如："XX海关海关业务二级主办..." 应解析为：隶属关="XX海关"，职务职位="海关业务二级主办..."

    # 查找以"海关"结尾的隶属关名称
    customs_pattern = re.compile(r"([\u4e00-\u9fa5]+)海关")
    matches = list(customs_pattern.finditer(position_main))

    if matches:
        # 取最后一个"XX海关"作为隶属关
        last_match = matches[-1]
        sub_district = last_match.group()  # 如 "上海浦东国际机场海关"
        
        # 职务职位从隶属关之后开始
        position_name = position_main[last_match.end():].strip()
        
        # 如果职务职位仍然以"海关"开头（这是职位分类名称），保留完整名称
        # 否则不需要额外处理
    else:
        sub_district = ""
        position_name = position_main

    # 清理可能残留的重复"海关"
    # 如果隶属关以"海关海关"结尾，修正为"海关"
    if sub_district.endswith("海关海关"):
        sub_district = sub_district[:-2]  # 去掉一个"海关"

    return {
        "隶属关": sub_district,
        "职务职位": position_name,
        "职位代码": position_code,
        "原始值": position_field
    }
