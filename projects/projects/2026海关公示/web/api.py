"""
2026海关公示数据分析 API
基于 FastAPI + Pandas，提供多维度数据查询与分析服务。
"""

import re
from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from schemas import (
    DistrictsResponse,
    DistrictDetailResponse,
    DistrictInfo,
    EducationStat,
    ErrorResponse,
    GenderStat,
    JobTypeCount,
    LevelCount,
    OverviewResponse,
    PositionAnalysisResponse,
    PositionStat,
    SchoolInfo,
    SearchParams,
    SearchResponse,
    SearchResultItem,
    SubDistrictCount,
)

# =============================================================================
# Constants & Config
# =============================================================================

BASE_DIR = Path(__file__).parent
CSV_PATH = BASE_DIR / ".." / "output" / "2026" / "2026海关公示汇总.csv"

DISTRICT_URLS: dict[str, str] = {
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

ELITE_SCHOOLS: set[str] = {
    "北京大学", "清华大学", "复旦大学", "上海交通大学", "浙江大学",
    "南京大学", "中国人民大学", "中国科学技术大学", "华中科技大学",
    "武汉大学", "中山大学", "四川大学", "西安交通大学", "哈尔滨工业大学",
    "北京航空航天大学", "同济大学", "北京师范大学", "东南大学",
    "中国人民大学", "南开大学",
}

LEVEL_PATTERNS: list[tuple[str, str]] = [
    (r"一级(?:主任|主办|行政执法员)", "一级"),
    (r"二级(?:主任|主办|行政执法员)", "二级"),
    (r"三级(?:主任|主办|行政执法员)", "三级"),
    (r"四级(?:主任|主办|行政执法员)", "四级"),
    (r"一级行政执法员", "一级行政执法员"),
]

REGEX_PATTERNS = {k: re.compile(v) for k, v in [
    ("level", r"(?:一级|二级|三级|四级)(?:主任|主办|行政执法员)"),
    ("level_rank", r"(?:一级|二级|三级|四级)"),
]}

# =============================================================================
# Data Loading
# =============================================================================

_df_cache: pd.DataFrame | None = None


def get_df() -> pd.DataFrame:
    """Get cached DataFrame."""
    global _df_cache
    return _df_cache


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    global _df_cache
    _df_cache = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    yield
    _df_cache = None


# =============================================================================
# Utilities
# =============================================================================

def safe_to_dict(df: pd.DataFrame) -> list[dict]:
    """Convert DataFrame to list of dicts with None for NaN."""
    return df.replace({np.nan: None}).to_dict("records")


def filter_by_keywords(df: pd.DataFrame, column: str, keywords: str) -> pd.DataFrame:
    """Filter DataFrame by space-separated keywords (AND logic)."""
    return df if not keywords else (
        df[df[column].fillna("").str.contains(keywords, case=False, regex=True)]
        if " " not in keywords.strip()
        else df[
            pd.concat([
                df[column].fillna("").str.contains(kw.strip(), case=False, regex=True)
                for kw in keywords.split()
            ], axis=1).all(axis=1)
        ]
    )


def classify_school(school: str | None) -> str:
    """Classify school tier."""
    return "985/211" if school and school in ELITE_SCHOOLS else "其他"


def extract_level(position: str | None) -> str:
    """Extract position level from job title."""
    if not position:
        return "其他"
    for pattern, label in LEVEL_PATTERNS:
        if REGEX_PATTERNS["level"].search(position):
            return label
    return "其他"


# =============================================================================
# API Routes
# =============================================================================

app = FastAPI(
    title="2026海关公示数据分析API",
    description="提供海关公务员录用数据的多维度查询与分析",
    version="1.0.0",
    lifespan=lifespan,
    responses={400: {"model": ErrorResponse}},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from fastapi.responses import FileResponse

# =============================================================================

app = FastAPI(
    title="2026海关公示数据分析API",
    description="提供海关公务员录用数据的多维度查询与分析",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    responses={400: {"model": ErrorResponse}},
)

# Serve frontend index at root
@app.get("/", include_in_schema=False)
async def root():
    """Serve frontend application."""
    index_path = DIST_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "Frontend not found"}


@app.get("/api/overview", response_model=OverviewResponse, tags=["统计"])
async def get_overview() -> OverviewResponse:
    """获取总体统计数据。"""
    df = get_df()
    return OverviewResponse(
        total=len(df),
        districts=df["关区"].nunique(),
        schools=df["毕业院校"].nunique(),
        positions=df["拟录用职位及代码"].nunique(),
    )


@app.get("/api/districts", response_model=DistrictsResponse, tags=["关区"])
async def get_districts() -> DistrictsResponse:
    """获取所有关区列表及录用人数。"""
    df = get_df()
    grouped = df.groupby("关区").size().reset_index(name="人数")
    grouped = grouped.sort_values("人数", ascending=False)

    districts = [
        DistrictInfo(关区=row["关区"], 人数=int(row["人数"]), 官网=DISTRICT_URLS.get(row["关区"]))
        for row in grouped.to_dict("records")
    ]
    return DistrictsResponse(districts=districts)


@app.get("/api/district/{district}", response_model=DistrictDetailResponse, tags=["关区"])
async def get_district_detail(district: str) -> DistrictDetailResponse:
    """获取指定关区的详细统计信息。"""
    df = get_df()
    district_df = df[df["关区"] == district]
    if district_df.empty:
        raise HTTPException(status_code=404, detail=f"关区 '{district}' 不存在")

    gender_counts = district_df["性别"].fillna("未知").value_counts().to_dict()

    education_counts = district_df["学历"].fillna("未知").value_counts()
    education_stats = [EducationStat(name=k, value=int(v)) for k, v in education_counts.items()]

    gender_stats = [
        GenderStat(name=k, value=int(v))
        for k, v in {"男": gender_counts.get("男", 0), "女": gender_counts.get("女", 0)}.items()
    ]

    position_counts = district_df["拟录用职位及代码"].value_counts().head(5)
    top_positions = [PositionStat(name=k, count=int(v)) for k, v in position_counts.items()]

    school_counts = district_df["毕业院校"].value_counts().head(5)
    top_schools = [SchoolInfo(毕业院校=k, 人数=int(v)) for k, v in school_counts.items()]

    return DistrictDetailResponse(
        district=district,
        total=len(district_df),
        male=gender_counts.get("男", 0),
        female=gender_counts.get("女", 0),
        education=education_stats,
        gender=gender_stats,
        top_positions=top_positions,
        top_schools=top_schools,
    )


@app.get("/api/schools", response_model=list[SchoolInfo], tags=["院校"])
async def get_schools(
    top: int = Query(default=20, ge=1, le=100, description="返回数量"),
) -> list[SchoolInfo]:
    """获取录用人数最多的院校排名。"""
    df = get_df()
    grouped = df.groupby("毕业院校").size().reset_index(name="人数")
    grouped = grouped.sort_values("人数", ascending=False).head(top)
    return [SchoolInfo(毕业院校=row["毕业院校"], 人数=int(row["人数"])) for row in grouped.to_dict("records")]


@app.get("/api/positions/analysis", response_model=PositionAnalysisResponse, tags=["拟录用职位及代码"])
async def get_position_analysis() -> PositionAnalysisResponse:
    """获取职位分析统计。"""
    df = get_df()

    job_type_counts = df["拟录用职位及代码"].fillna("未知").value_counts().to_dict()
    level_counts = df["拟录用职位及代码"].apply(extract_level).value_counts().to_dict()
    sub_district_counts = df["关区"].value_counts().to_dict()

    return PositionAnalysisResponse(
        total_positions=len(df["拟录用职位及代码"].unique()),
        job_type_counts=job_type_counts,
        level_counts=level_counts,
        sub_district_counts=sub_district_counts,
    )


@app.get("/api/search", response_model=SearchResponse, tags=["搜索"])
async def search(
    name: str | None = Query(default=None, description="姓名关键字"),
    school: str | None = Query(default=None, description="毕业院校关键字"),
    position: str | None = Query(default=None, description="职位关键字"),
    district: str | None = Query(default=None, description="关区名称"),
    education: str | None = Query(default=None, description="学历"),
    gender: str | None = Query(default=None, description="性别"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
) -> SearchResponse:
    """多条件搜索录用人员信息。"""
    df = get_df()
    params = SearchParams(name=name, school=school, position=position, district=district, education=education, gender=gender, page=page, page_size=page_size)

    df = filter_by_keywords(df, "姓名", params.name or "")
    df = filter_by_keywords(df, "毕业院校", params.school or "")
    df = filter_by_keywords(df, "拟录用职位及代码", params.position or "")
    df = df[df["关区"] == params.district] if params.district else df
    df = df[df["学历"] == params.education] if params.education else df
    df = df[df["性别"] == params.gender] if params.gender else df

    total = len(df)
    total_pages = (total + params.page_size - 1) // params.page_size
    start = (params.page - 1) * params.page_size
    page_df = df.iloc[start:start + params.page_size]

    items = [
        SearchResultItem(
            姓名=row.get("姓名", ""),
            性别=row.get("性别"),
            毕业院校=row.get("毕业院校"),
            学历=row.get("学历"),
            关区=row.get("关区"),
            职位=row.get("拟录用职位及代码"),
            隶属海关=row.get("隶属海关"),
        )
        for row in page_df.to_dict("records")
    ]

    return SearchResponse(
        items=items,
        total=total,
        page=params.page,
        page_size=params.page_size,
        total_pages=total_pages,
    )


if __name__ == "__main__":
    import uvicorn
    port = int(__import__("os").getenv("PORT", "5000"))
    uvicorn.run("api:app", host="0.0.0.0", port=port, reload=False)

# =============================================================================
# Static Files (Serve frontend)
# =============================================================================
DIST_DIR = BASE_DIR / "frontend" / "dist"


@app.get("/")
def serve_index():
    """Serve the frontend index.html"""
    index_path = DIST_DIR / "index.html"
    if index_path.exists():
        from fastapi.responses import FileResponse
        return FileResponse(str(index_path))
    raise HTTPException(status_code=404, detail="Frontend not found")


@app.get("/{full_path:path}")
def serve_static(full_path: str):
    """Serve frontend static files for client-side routing"""
    file_path = DIST_DIR / full_path
    if file_path.exists() and file_path.is_file():
        return FileResponse(str(file_path))
    # Fallback to index.html for SPA routing
    index_path = DIST_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    raise HTTPException(status_code=404, detail="Not found")


if DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(DIST_DIR / "assets")), name="static")
