"""
Pydantic v2 schemas for API request/response validation.
"""

from typing import Annotated, Optional

from pydantic import BaseModel, Field, field_validator


# =============================================================================
# Common Fields
# =============================================================================

IntRange = Annotated[int, Field(ge=1, le=1000, description="整数范围限制")]
PageSize = Annotated[int, Field(ge=1, le=100, description="分页大小")]


# =============================================================================
# Search Schemas
# =============================================================================

class SearchParams(BaseModel):
    """搜索查询参数。"""
    name: Optional[str] = Field(default=None, description="姓名关键字，支持空格分隔多关键字AND搜索")
    school: Optional[str] = Field(default=None, description="毕业院校关键字")
    position: Optional[str] = Field(default=None, description="职位关键字")
    district: Optional[str] = Field(default=None, description="关区名称")
    education: Optional[str] = Field(default=None, description="学历")
    gender: Optional[str] = Field(default=None, description="性别")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")

    @field_validator("page", "page_size", mode="before")
    @classmethod
    def validate_positive_int(cls, v):
        if v is None:
            return 1
        try:
            return int(v)
        except (ValueError, TypeError):
            return 1


# =============================================================================
# Response Schemas
# =============================================================================

class OverviewResponse(BaseModel):
    """总体统计数据响应。"""
    total: int = Field(..., description="总录用人数")
    districts: int = Field(..., description="关区数量")
    schools: int = Field(..., description="院校数量")
    positions: int = Field(..., description="职位数量")


class DistrictInfo(BaseModel):
    """单个关区信息。"""
    关区: str = Field(..., description="关区名称")
    人数: int = Field(..., description="录用人数")
    官网: Optional[str] = Field(default=None, description="关区官网地址")


class DistrictsResponse(BaseModel):
    """关区列表响应。"""
    districts: list[DistrictInfo] = Field(default_factory=list)


class SchoolInfo(BaseModel):
    """单个院校信息。"""
    毕业院校: str = Field(..., description="毕业院校名称")
    人数: int = Field(..., description="录用人数")


class EducationStat(BaseModel):
    """学历分布统计。"""
    name: str = Field(..., description="学历名称")
    value: int = Field(..., description="人数")


class GenderStat(BaseModel):
    """性别分布统计。"""
    name: str = Field(..., description="性别")
    value: int = Field(..., description="人数")


class PositionStat(BaseModel):
    """职位统计。"""
    name: str = Field(..., description="职位名称")
    count: int = Field(..., description="人数")


class DistrictDetailResponse(BaseModel):
    """关区详情响应。"""
    district: str = Field(..., description="关区名称")
    total: int = Field(..., description="总人数")
    male: int = Field(default=0, description="男性人数")
    female: int = Field(default=0, description="女性人数")
    education: list[EducationStat] = Field(default_factory=list, description="学历分布")
    gender: list[GenderStat] = Field(default_factory=list, description="性别分布")
    top_positions: list[PositionStat] = Field(default_factory=list, description="热门职位 Top5")
    top_schools: list[SchoolInfo] = Field(default_factory=list, description="来源院校 Top5")


class JobTypeCount(BaseModel):
    """职位类型统计。"""
    name: str = Field(..., description="职位类型")
    value: int = Field(..., description="人数")


class LevelCount(BaseModel):
    """级别分布统计。"""
    name: str = Field(..., description="级别")
    value: int = Field(..., description="人数")


class SubDistrictCount(BaseModel):
    """子关区统计。"""
    name: str = Field(..., description="关区名称")
    value: int = Field(..., description="人数")


class PositionAnalysisResponse(BaseModel):
    """职位分析响应。"""
    total_positions: int = Field(..., description="职位总数")
    job_type_counts: dict[str, int] = Field(default_factory=dict, description="职位类型统计")
    level_counts: dict[str, int] = Field(default_factory=dict, description="级别分布统计")
    sub_district_counts: dict[str, int] = Field(default_factory=dict, description="关区分布统计")


class SearchResultItem(BaseModel):
    """搜索结果项。"""
    姓名: str = Field(default="", description="姓名")
    性别: Optional[str] = Field(default=None, description="性别")
    毕业院校: Optional[str] = Field(default=None, description="毕业院校")
    学历: Optional[str] = Field(default=None, description="学历")
    关区: Optional[str] = Field(default=None, description="关区")
    隶属关: Optional[str] = Field(default=None, description="隶属关")
    职务职位: Optional[str] = Field(default=None, description="职务职位")
    职位代码: Optional[str] = Field(default=None, description="职位代码")


class SearchResponse(BaseModel):
    """搜索响应。"""
    items: list[SearchResultItem] = Field(default_factory=list)
    total: int = Field(default=0, description="总记录数")
    page: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=20, description="每页数量")
    total_pages: int = Field(default=0, description="总页数")


class ErrorResponse(BaseModel):
    """错误响应。"""
    detail: str = Field(..., description="错误详情")


class HealthResponse(BaseModel):
    """健康检查响应。"""
    status: str = Field(..., description="服务状态")
    data_loaded: bool = Field(..., description="数据是否已加载")
    record_count: int = Field(default=0, description="数据记录数")
