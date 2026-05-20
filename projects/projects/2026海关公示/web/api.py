"""
2026海关公示数据分析 API
基于 FastAPI + Pandas，提供多维度数据查询与分析服务。
"""

import os
import re
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from customs_pipeline.constants import (
    DISTRICT_URLS,
    ELITE_SCHOOLS,
    LEVEL_PATTERNS,
    COMPILED_PATTERNS,
    classify_school,
    extract_level,
    get_district_url,
    parse_position_field,
)
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
# Path Configuration
# =============================================================================

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

BASE_DIR = Path(__file__).parent
DIST_DIR = BASE_DIR / "frontend" / "dist"
CSV_PATH = BASE_DIR / ".." / "output" / "2026" / "2026海关公示汇总.csv"

# =============================================================================
# Data Loading & Caching
# =============================================================================

_df_cache: pd.DataFrame | None = None


def get_df() -> pd.DataFrame:
    """获取缓存的 DataFrame，若未加载则抛出错误。"""
    global _df_cache
    if _df_cache is None:
        raise HTTPException(
            status_code=503,
            detail="数据未加载，请等待服务启动完成"
        )
    return _df_cache


def _load_csv() -> pd.DataFrame:
    """加载 CSV 文件并返回 DataFrame，解析职位代码。"""
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"数据文件不存在: {CSV_PATH}")

    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

    # 数据验证
    required_columns = {"关区", "姓名", "性别", "学历", "毕业院校", "拟录用职位及代码"}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        raise ValueError(f"数据缺少必需列: {missing_columns}")

    # 解析职位代码：隶属关 + 职务职位 + 职位代码
    from customs_pipeline.constants import parse_position_field
    parsed = df["拟录用职位及代码"].apply(parse_position_field)
    df["隶属关"] = parsed.apply(lambda x: x["隶属关"])
    df["职务职位"] = parsed.apply(lambda x: x["职务职位"])
    df["职位代码"] = parsed.apply(lambda x: x["职位代码"])

    return df


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动时加载数据，关闭时清理缓存。"""
    global _df_cache
    try:
        _df_cache = _load_csv()
        print(f"[启动] 数据加载完成，共 {len(_df_cache)} 条记录")
    except Exception as e:
        print(f"[警告] 数据加载失败: {e}")
        _df_cache = pd.DataFrame()  # 使用空 DataFrame 避免运行时错误
    yield
    _df_cache = None
    print("[关闭] 数据缓存已清理")


# =============================================================================
# Utility Functions
# =============================================================================

def safe_to_dict(df: pd.DataFrame) -> list[dict]:
    """将 DataFrame 转换为字典列表，NaN 转为 None。"""
    return df.replace({np.nan: None}).to_dict("records")


def filter_by_keywords(df: pd.DataFrame, column: str, keywords: str) -> pd.DataFrame:
    """按空格分隔的关键字过滤 DataFrame（AND 逻辑）。"""
    if not keywords or column not in df.columns:
        return df

    keywords = keywords.strip()
    # 无空格：普通匹配
    if " " not in keywords:
        return df[df[column].fillna("").str.contains(keywords, case=False, regex=True)]

    # 有空格：AND 逻辑
    keyword_list = [kw.strip() for kw in keywords.split() if kw.strip()]
    if not keyword_list:
        return df

    mask = pd.concat([
        df[column].fillna("").str.contains(kw, case=False, regex=True)
        for kw in keyword_list
    ], axis=1).all(axis=1)
    return df[mask]


def ensure_int(value: Any) -> int:
    """安全转换为整数。"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="2026海关公示数据分析API",
    description="提供海关公务员录用数据的多维度查询与分析",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Health Check
# =============================================================================

@app.get("/api/health", tags=["系统"])
async def health_check():
    """健康检查接口。"""
    global _df_cache
    return {
        "status": "healthy",
        "data_loaded": _df_cache is not None,
        "record_count": len(_df_cache) if _df_cache is not None else 0,
    }


# =============================================================================
# Overview Statistics
# =============================================================================

@app.get("/api/overview", response_model=OverviewResponse, tags=["统计"])
async def get_overview() -> OverviewResponse:
    """获取总体统计数据概览。"""
    df = get_df()
    return OverviewResponse(
        total=ensure_int(len(df)),
        districts=ensure_int(df["关区"].nunique()),
        schools=ensure_int(df["毕业院校"].nunique()),
        positions=ensure_int(df["拟录用职位及代码"].nunique()),
    )


# =============================================================================
# District APIs
# =============================================================================

@app.get("/api/districts", response_model=DistrictsResponse, tags=["关区"])
async def get_districts() -> DistrictsResponse:
    """获取所有关区列表及录用人数。"""
    df = get_df()
    grouped = df.groupby("关区").size().reset_index(name="人数")
    grouped = grouped.sort_values("人数", ascending=False)

    districts = [
        DistrictInfo(
            关区=row["关区"],
            人数=ensure_int(row["人数"]),
            官网=get_district_url(row["关区"])
        )
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

    education_stats = [
        EducationStat(name=k, value=ensure_int(v))
        for k, v in education_counts.items()
    ]

    gender_stats = [
        GenderStat(name=k, value=ensure_int(v))
        for k, v in {"男": gender_counts.get("男", 0), "女": gender_counts.get("女", 0)}.items()
    ]

    position_counts = district_df["拟录用职位及代码"].value_counts().head(5)
    top_positions = [
        PositionStat(name=k, count=ensure_int(v))
        for k, v in position_counts.items()
    ]

    school_counts = district_df["毕业院校"].value_counts().head(5)
    top_schools = [
        SchoolInfo(毕业院校=k, 人数=ensure_int(v))
        for k, v in school_counts.items()
    ]

    return DistrictDetailResponse(
        district=district,
        total=ensure_int(len(district_df)),
        male=gender_counts.get("男", 0),
        female=gender_counts.get("女", 0),
        education=education_stats,
        gender=gender_stats,
        top_positions=top_positions,
        top_schools=top_schools,
    )


# =============================================================================
# School APIs
# =============================================================================

@app.get("/api/schools", response_model=list[SchoolInfo], tags=["院校"])
async def get_schools(
    top: int = Query(default=20, ge=1, le=100, description="返回数量"),
) -> list[SchoolInfo]:
    """获取录用人数最多的院校排名。"""
    df = get_df()
    grouped = df.groupby("毕业院校").size().reset_index(name="人数")
    grouped = grouped.sort_values("人数", ascending=False).head(top)

    return [
        SchoolInfo(毕业院校=row["毕业院校"], 人数=ensure_int(row["人数"]))
        for row in grouped.to_dict("records")
    ]


# =============================================================================
# Position APIs
# =============================================================================

@app.get("/api/positions/analysis", response_model=PositionAnalysisResponse, tags=["职位"])
async def get_position_analysis() -> PositionAnalysisResponse:
    """获取职位分析统计数据。"""
    df = get_df()

    # 使用解析后的职位字段
    job_type_counts = df["职务职位"].fillna("未知").value_counts().to_dict()
    level_counts = df["拟录用职位及代码"].apply(extract_level).value_counts().to_dict()
    sub_district_counts = df["隶属关"].fillna("未知").value_counts().to_dict()

    return PositionAnalysisResponse(
        total_positions=ensure_int(len(df["职务职位"].unique())),
        job_type_counts={k: ensure_int(v) for k, v in job_type_counts.items()},
        level_counts={k: ensure_int(v) for k, v in level_counts.items()},
        sub_district_counts={k: ensure_int(v) for k, v in sub_district_counts.items()},
    )


# =============================================================================
# Search API
# =============================================================================

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

    # 逐条件过滤
    df = filter_by_keywords(df, "姓名", name or "")
    df = filter_by_keywords(df, "毕业院校", school or "")
    df = filter_by_keywords(df, "拟录用职位及代码", position or "")

    if district:
        df = df[df["关区"] == district]
    if education:
        df = df[df["学历"] == education]
    if gender:
        df = df[df["性别"] == gender]

    # 分页计算
    total = len(df)
    total_pages = max(1, (total + page_size - 1) // page_size)
    page = min(page, total_pages)
    start = (page - 1) * page_size
    page_df = df.iloc[start:start + page_size]

    items = []
    for row in page_df.to_dict("records"):
        position = row.get("拟录用职位及代码", "")
        parsed = parse_position_field(position)
        items.append(
            SearchResultItem(
                姓名=row.get("姓名", ""),
                性别=row.get("性别"),
                毕业院校=row.get("毕业院校"),
                学历=row.get("学历"),
                关区=row.get("关区"),
                隶属关=parsed.get("隶属关", ""),
                职务职位=parsed.get("职务职位", ""),
                职位代码=parsed.get("职位代码", ""),
            )
        )

    return SearchResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


# =============================================================================
# Static Files (SPA Routing)
# =============================================================================

@app.get("/", include_in_schema=False)
async def serve_index():
    """服务前端 index.html。"""
    index_path = DIST_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    raise HTTPException(status_code=404, detail="Frontend not found")


@app.get("/{full_path:path}", include_in_schema=False)
async def serve_static(full_path: str):
    """服务前端静态文件，支持 SPA 路由。"""
    file_path = DIST_DIR / full_path
    if file_path.exists() and file_path.is_file():
        return FileResponse(str(file_path))

    # 回退到 index.html（SPA 路由）
    index_path = DIST_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))

    raise HTTPException(status_code=404, detail="Not found")


# 挂载静态资源目录
if DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(DIST_DIR / "assets")), name="static")


# =============================================================================
# Application Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "5000"))
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info",
    )
