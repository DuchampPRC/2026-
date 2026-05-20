"""Pydantic v2 schemas for API request/response validation."""

from typing import Optional
from pydantic import BaseModel, Field


class SearchParams(BaseModel):
    """Search query parameters."""
    name: Optional[str] = Field(default=None, description="姓名关键字，支持空格分隔多关键字AND搜索")
    school: Optional[str] = Field(default=None, description="毕业院校关键字")
    position: Optional[str] = Field(default=None, description="职位关键字")
    district: Optional[str] = Field(default=None, description="关区名称")
    education: Optional[str] = Field(default=None, description="学历")
    gender: Optional[str] = Field(default=None, description="性别")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")


class OverviewResponse(BaseModel):
    """Overview statistics response."""
    total: int
    districts: int
    schools: int
    positions: int


class DistrictInfo(BaseModel):
    """Single district information."""
    关区: str
    人数: int
    官网: Optional[str] = None


class DistrictsResponse(BaseModel):
    """Districts list response."""
    districts: list[DistrictInfo]


class SchoolInfo(BaseModel):
    """Single school information."""
    毕业院校: str
    人数: int


class EducationStat(BaseModel):
    """Education distribution stat."""
    name: str
    value: int


class GenderStat(BaseModel):
    """Gender distribution stat."""
    name: str
    value: int


class PositionStat(BaseModel):
    """Position stat with count."""
    name: str
    count: int


class DistrictDetailResponse(BaseModel):
    """District detail response."""
    district: str
    total: int
    male: int
    female: int
    education: list[EducationStat]
    gender: list[GenderStat]
    top_positions: list[PositionStat]
    top_schools: list[SchoolInfo]


class JobTypeCount(BaseModel):
    """Job type count."""
    name: str
    value: int


class LevelCount(BaseModel):
    """Level distribution count."""
    name: str
    value: int


class SubDistrictCount(BaseModel):
    """Sub-district count."""
    name: str
    value: int


class PositionAnalysisResponse(BaseModel):
    """Position analysis response."""
    total_positions: int
    job_type_counts: dict[str, int]
    level_counts: dict[str, int]
    sub_district_counts: dict[str, int]


class SearchResultItem(BaseModel):
    """Single search result item."""
    姓名: str
    性别: Optional[str] = None
    毕业院校: Optional[str] = None
    学历: Optional[str] = None
    关区: Optional[str] = None
    职位: Optional[str] = None
    隶属海关: Optional[str] = None


class SearchResponse(BaseModel):
    """Search results response."""
    items: list[SearchResultItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class ErrorResponse(BaseModel):
    """Error response schema."""
    detail: str
