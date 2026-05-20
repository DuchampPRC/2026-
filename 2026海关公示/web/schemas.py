"""
Pydantic v2 schemas for API request/response validation.

数据流向：
1. 前端 -> SearchParams (搜索参数)
2. 后端处理 -> 各 Response 模型 (响应数据)
"""

from typing import Annotated, Optional

from pydantic import BaseModel, Field, field_validator


# =============================================================================
# Common Fields - 可复用的字段类型定义
# =============================================================================

# IntRange: 通用整数范围限制，用于需要限制数值范围的场景
# 使用示例: count: IntRange
IntRange = Annotated[int, Field(ge=1, le=1000, description="整数范围限制")]

# PageSize: 分页大小，限制每页最多100条
# 使用示例: page_size: PageSize
PageSize = Annotated[int, Field(ge=1, le=100, description="分页大小")]


# =============================================================================
# Search Schemas - 搜索相关参数
# =============================================================================

class SearchParams(BaseModel):
    """
    搜索查询参数模型。
    
    Attributes:
        name: 姓名关键字，支持空格分隔多关键字AND搜索
        school: 毕业院校关键字
        position: 职位关键字（可搜索职位名、隶属关、职位代码）
        district: 关区名称（精确匹配）
        education: 学历（精确匹配）
        gender: 性别（精确匹配）
        page: 页码，从1开始
        page_size: 每页数量，1-100
    """
    name: Optional[str] = Field(default=None, description="姓名关键字，支持空格分隔多关键字AND搜索")
    school: Optional[str] = Field(default=None, description="毕业院校关键字")
    position: Optional[str] = Field(default=None, description="职位关键字（支持职位名/隶属关/代码）")
    district: Optional[str] = Field(default=None, description="关区名称（精确匹配）")
    education: Optional[str] = Field(default=None, description="学历（精确匹配）")
    gender: Optional[str] = Field(default=None, description="性别（精确匹配）")
    page: int = Field(default=1, ge=1, description="页码，从1开始")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量，最大100")

    @field_validator("page", "page_size", mode="before")
    @classmethod
    def validate_positive_int(cls, v):
        """
        验证并转换分页参数为正整数。
        
        处理边界情况：
        - None 值转为 1
        - 非数字类型尝试转换
        - 转换失败返回默认值 1
        """
        if v is None:
            return 1
        try:
            return int(v)
        except (ValueError, TypeError):
            return 1


# =============================================================================
# Response Schemas - API 响应模型
# =============================================================================

class OverviewResponse(BaseModel):
    """
    总体统计数据响应（首页概览卡片使用）。
    """
    total: int = Field(..., description="总录用人数")
    districts: int = Field(..., description="关区数量")
    schools: int = Field(..., description="院校数量")
    positions: int = Field(..., description="职位数量")


class DistrictInfo(BaseModel):
    """
    单个关区信息（关区列表展示）。
    """
    关区: str = Field(..., description="关区名称")
    人数: int = Field(..., description="录用人数")
    官网: Optional[str] = Field(default=None, description="关区官网地址")


class DistrictsResponse(BaseModel):
    """关区列表响应。"""
    districts: list[DistrictInfo] = Field(default_factory=list)


class SchoolInfo(BaseModel):
    """
    单个院校信息（院校列表展示）。
    """
    毕业院校: str = Field(..., description="毕业院校名称")
    人数: int = Field(..., description="录用人数")


class EducationStat(BaseModel):
    """
    学历分布统计项（饼图数据格式）。
    
    Attributes:
        name: 学历名称（如：本科、硕士研究生）
        value: 该学历录用人数
    """
    name: str = Field(..., description="学历名称")
    value: int = Field(..., description="人数")


class GenderStat(BaseModel):
    """
    性别分布统计项（饼图数据格式）。
    """
    name: str = Field(..., description="性别")
    value: int = Field(..., description="人数")


class PositionStat(BaseModel):
    """
    职位统计项。
    """
    name: str = Field(..., description="职位名称")
    count: int = Field(..., description="人数")


class DistrictDetailResponse(BaseModel):
    """
    关区详情响应（点击关区弹窗展示）。
    """
    district: str = Field(..., description="关区名称")
    total: int = Field(..., description="总人数")
    male: int = Field(default=0, description="男性人数")
    female: int = Field(default=0, description="女性人数")
    education: list[EducationStat] = Field(default_factory=list, description="学历分布")
    gender: list[GenderStat] = Field(default_factory=list, description="性别分布")
    top_positions: list[PositionStat] = Field(default_factory=list, description="热门职位 Top5")
    top_schools: list[SchoolInfo] = Field(default_factory=list, description="来源院校 Top5")


class JobTypeCount(BaseModel):
    """
    职位类型统计项（职位分析图表使用）。
    """
    name: str = Field(..., description="职位类型")
    value: int = Field(..., description="人数")


class LevelCount(BaseModel):
    """
    级别分布统计项（职位分析图表使用）。
    
    级别分类：一级主办、二级主办、三级主办、四级主办 等
    """
    name: str = Field(..., description="级别")
    value: int = Field(..., description="人数")


class SubDistrictCount(BaseModel):
    """
    子关区统计项（隶属关分布图表使用）。
    """
    name: str = Field(..., description="关区名称")
    value: int = Field(..., description="人数")


class PositionAnalysisResponse(BaseModel):
    """
    职位分析响应（数据分析模块使用）。
    """
    total_positions: int = Field(..., description="职位总数（不同职位类型的数量）")
    job_type_counts: dict[str, int] = Field(default_factory=dict, description="职位类型统计 {职位名: 人数}")
    level_counts: dict[str, int] = Field(default_factory=dict, description="级别分布统计 {级别: 人数}")
    sub_district_counts: dict[str, int] = Field(default_factory=dict, description="隶属关分布统计 {关区: 人数}")


class SearchResultItem(BaseModel):
    """
    搜索结果项（表格行数据格式）。
    
    注意：职位字段由 parse_position_field() 解析生成
    - 隶属关：解析自"拟录用职位及代码"字段
    - 职务职位：解析自"拟录用职位及代码"字段
    - 职位代码：12位代码，如 300110101001
    """
    姓名: str = Field(default="", description="姓名")
    性别: Optional[str] = Field(default=None, description="性别")
    毕业院校: Optional[str] = Field(default=None, description="毕业院校")
    学历: Optional[str] = Field(default=None, description="学历")
    关区: Optional[str] = Field(default=None, description="关区（行政区划）")
    隶属关: Optional[str] = Field(default=None, description="隶属关（实际工作海关）")
    职务职位: Optional[str] = Field(default=None, description="职务职位名称")
    职位代码: Optional[str] = Field(default=None, description="职位代码（12位）")


class SearchResponse(BaseModel):
    """
    搜索响应（分页结果）。
    
    Attributes:
        items: 当前页的搜索结果列表
        total: 满足条件的总记录数
        page: 当前页码
        page_size: 每页记录数
        total_pages: 总页数
    """
    items: list[SearchResultItem] = Field(default_factory=list)
    total: int = Field(default=0, description="满足条件的总记录数")
    page: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=20, description="每页记录数")
    total_pages: int = Field(default=0, description="总页数")


class ErrorResponse(BaseModel):
    """
    错误响应（API 异常时返回）。
    """
    detail: str = Field(..., description="错误详情")


class HealthResponse(BaseModel):
    """
    健康检查响应（/api/health 端点返回）。
    """
    status: str = Field(..., description="服务状态（healthy/unhealthy）")
    data_loaded: bool = Field(..., description="数据是否已加载")
    record_count: int = Field(default=0, description="已加载的数据记录数")
