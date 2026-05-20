"""
2026海关公示数据分析 API
基于 FastAPI + Pandas，提供多维度数据查询与分析服务。
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径，确保可以导入 customs_pipeline
_current_file = Path(__file__).resolve()
_project_root = _current_file.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import re
from contextlib import asynccontextmanager
from typing import Any
from urllib.parse import quote

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
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

# 添加项目根目录到 Python 路径，以便导入 customs_pipeline 模块
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

# 基础路径配置
BASE_DIR = Path(__file__).parent                          # web/ 目录
DIST_DIR = BASE_DIR / "frontend" / "dist"                # 前端构建产物目录
CSV_PATH = BASE_DIR / ".." / "output" / "2026" / "2026海关公示汇总.csv"  # 数据文件路径

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
    """
    加载 CSV 文件并返回 DataFrame。
    
    加载时执行以下预处理：
    1. 验证必需列是否存在
    2. 解析职位字段，提取隶属关、职务职位、职位代码
    
    Returns:
        预处理后的 DataFrame
    
    Raises:
        FileNotFoundError: 数据文件不存在
        ValueError: 数据缺少必需列
    """
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"数据文件不存在: {CSV_PATH}")

    # 使用 utf-8-sig 编码读取（处理 BOM）
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

    # 数据验证：确保必需列存在
    # 如有缺失会抛出异常，避免运行时错误
    required_columns = {"关区", "姓名", "性别", "学历", "毕业院校", "拟录用职位及代码"}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        raise ValueError(f"数据缺少必需列: {missing_columns}")

    # 解析职位字段，生成新列
    # 原始字段格式: "XX海关XX职位(300110101001)"
    # 解析后生成: 隶属关、职务职位、职位代码 三列
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
    """
    按空格分隔的关键字过滤 DataFrame（AND 逻辑）。
    
    支持两种搜索模式：
    - 单关键字：直接匹配
    - 多关键字（空格分隔）：所有关键字都必须匹配
    
    Args:
        df: 原始 DataFrame
        column: 要搜索的列名
        keywords: 搜索关键字，空格分隔多关键字
    
    Returns:
        过滤后的 DataFrame
    """
    # 参数校验：关键字为空或列不存在时返回原数据
    if not keywords or column not in df.columns:
        return df

    keywords = keywords.strip()
    
    # 使用 re.escape() 转义正则元字符，防止用户输入破坏正则表达式
    # 例如：用户输入 "海关(北京)" 会被转义为 "海关\(北京\)"
    escaped = re.escape(keywords)
    
    # 单关键字模式：直接使用 contains 匹配（转义后作为普通字符串）
    if " " not in escaped:
        return df[df[column].fillna("").str.contains(escaped, case=False, regex=True)]

    # 多关键字模式：AND 逻辑（所有关键字都必须匹配）
    # 1. 分割关键字
    # 2. 为每个关键字创建匹配掩码
    # 3. 使用 all(axis=1) 确保所有条件都满足
    # 注意：转义后空格不会被改变，所以 split(" ") 仍然有效
    keyword_list = [kw.strip() for kw in escaped.split(" ") if kw.strip()]
    if not keyword_list:
        return df

    # 使用 pd.concat 创建多列掩码，然后 all(axis=1)
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
# Exception Handlers - 友好错误页面
# =============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """自定义 HTTP 异常处理，返回友好 HTML 页面。"""
    # API 请求返回 JSON
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail}
        )
    
    # 页面请求返回 HTML
    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{exc.status_code} - 2026海关公示</title>
        <style>
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                display: flex; 
                justify-content: center; 
                align-items: center; 
                min-height: 100vh; 
                margin: 0; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #333;
            }}
            .error-container {{ 
                text-align: center; 
                background: white; 
                padding: 48px; 
                border-radius: 16px; 
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                max-width: 90%;
            }}
            .error-code {{ 
                font-size: 72px; 
                font-weight: 700; 
                color: #667eea; 
                margin: 0;
            }}
            .error-message {{ 
                font-size: 18px; 
                color: #666; 
                margin: 16px 0 32px;
            }}
            .home-link {{ 
                display: inline-block; 
                padding: 12px 32px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white; 
                text-decoration: none; 
                border-radius: 8px; 
                font-weight: 500;
                transition: transform 0.2s;
            }}
            .home-link:hover {{ transform: scale(1.05); }}
        </style>
    </head>
    <body>
        <div class="error-container">
            <h1 class="error-code">{exc.status_code}</h1>
            <p class="error-message">{exc.detail}</p>
            <a href="/" class="home-link">返回首页</a>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=exc.status_code)


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理。"""
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=500,
            content={"error": "服务器内部错误，请稍后重试"}
        )
    
    html_content = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>500 - 2026海关公示</title>
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                display: flex; 
                justify-content: center; 
                align-items: center; 
                min-height: 100vh; 
                margin: 0; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }
            .error-container { 
                text-align: center; 
                background: white; 
                padding: 48px; 
                border-radius: 16px; 
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }
            .error-code { font-size: 48px; color: #e53e3e; margin: 0; }
            .error-message { color: #666; margin: 16px 0; }
            .home-link { 
                display: inline-block; 
                padding: 12px 32px; 
                background: #667eea; 
                color: white; 
                text-decoration: none; 
                border-radius: 8px;
            }
        </style>
    </head>
    <body>
        <div class="error-container">
            <h1 class="error-code">500</h1>
            <p class="error-message">服务器开小差了，请稍后重试</p>
            <a href="/" class="home-link">返回首页</a>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=500)


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
    """
    获取职位分析统计数据。
    
    统计维度：
    - 职位类型分布（职务职位）
    - 职位级别分布（一级/二级/三级/四级主办等）
    - 隶属关分布
    
    Returns:
        包含各类统计计数的响应
    """
    df = get_df()

    # 职务职位分布：使用解析后的职务职位字段
    job_type_counts = df["职务职位"].fillna("未知").value_counts().to_dict()
    # 职位级别分布：从原始职位字段提取级别
    level_counts = df["拟录用职位及代码"].apply(extract_level).value_counts().to_dict()
    # 隶属关分布：使用解析后的隶属关字段
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
    position: str | None = Query(default=None, description="职位关键字（支持姓名、院校、职位代码）"),
    district: str | None = Query(default=None, description="关区名称（精确匹配）"),
    education: str | None = Query(default=None, description="学历（精确匹配）"),
    gender: str | None = Query(default=None, description="性别（精确匹配）"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
) -> SearchResponse:
    """
    多条件搜索录用人员信息。
    
    搜索逻辑：
    - 关键字搜索（name/school/position）：模糊匹配，支持空格分隔多关键字 AND 搜索
    - 精确匹配（district/education/gender）：完全相等匹配
    
    搜索职位时同时匹配：职位名称、隶属关、职位代码
    
    Returns:
        包含分页结果的搜索响应
    """
    df = get_df()

    # 关键字搜索：支持模糊匹配 + 多关键字 AND
    df = filter_by_keywords(df, "姓名", name or "")
    df = filter_by_keywords(df, "毕业院校", school or "")
    
    # 职位搜索优化：
    # - 如果是纯数字（可能是职位代码），优先精确匹配职位代码
    # - 否则使用模糊匹配（原字段包含隶属关+职位名）
    if position:
        position = position.strip()
        # 检测是否为纯数字（可能是职位代码）
        is_code = re.match(r'^[\d\s]+$', position)
        if is_code:
            # 纯数字搜索：精确匹配职位代码
            code_keywords = position.split()
            for code in code_keywords:
                df = df[df["职位代码"].fillna("").str.contains(code, case=False)]
        else:
            # 普通关键字：模糊匹配原字段
            df = filter_by_keywords(df, "拟录用职位及代码", position)

    # 精确匹配过滤
    if district:
        df = df[df["关区"] == district]
    if education:
        df = df[df["学历"] == education]
    if gender:
        df = df[df["性别"] == gender]

    # 分页计算
    total = len(df)
    # 计算总页数，向上取整
    total_pages = max(1, (total + page_size - 1) // page_size)
    # 确保页码在有效范围内
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
# Export API - 数据导出
# =============================================================================

@app.get("/api/export", tags=["导出"])
async def export_data(
    name: str | None = Query(default=None, description="姓名关键字"),
    school: str | None = Query(default=None, description="毕业院校关键字"),
    position: str | None = Query(default=None, description="职位关键字"),
    district: str | None = Query(default=None, description="关区名称"),
    education: str | None = Query(default=None, description="学历"),
    gender: str | None = Query(default=None, description="性别"),
    format: str = Query(default="csv", pattern="^(csv|xlsx)$", description="导出格式：csv 或 xlsx"),
) -> Response:
    """
    导出筛选后的数据为 CSV 或 Excel 文件。
    
    导出字段：姓名、性别、学历、毕业院校、关区、隶属关、职务职位、职位代码
    
    注意：
    - 最大导出 10000 条记录
    - 支持与搜索接口相同的筛选条件
    """
    df = get_df()

    # 应用筛选条件（与 search 接口相同）
    df = filter_by_keywords(df, "姓名", name or "")
    df = filter_by_keywords(df, "毕业院校", school or "")
    
    # 职位搜索优化
    if position:
        position = position.strip()
        is_code = re.match(r'^[\d\s]+$', position)
        if is_code:
            code_keywords = position.split()
            for code in code_keywords:
                df = df[df["职位代码"].fillna("").str.contains(code, case=False)]
        else:
            df = filter_by_keywords(df, "拟录用职位及代码", position)
    
    if district:
        df = df[df["关区"] == district]
    if education:
        df = df[df["学历"] == education]
    if gender:
        df = df[df["性别"] == gender]

    # 限制导出数量
    max_export = 10000
    if len(df) > max_export:
        df = df.head(max_export)

    # 选择导出的列
    export_columns = ["姓名", "性别", "学历", "毕业院校", "关区", "隶属关", "职务职位", "职位代码"]
    export_df = df[export_columns].copy()

    # 生成文件
    timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    
    if format == "csv":
        # CSV 导出
        content = export_df.to_csv(index=False, encoding="utf-8-sig")
        filename = f"海关公示数据_{timestamp}.csv"
        # 使用 RFC 5987 编码格式（filename*）支持中文
        encoded_filename = quote(filename, safe='')
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
        )
    else:
        # Excel 导出（需要 openpyxl）
        try:
            import io
            from openpyxl import Workbook
            from openpyxl.utils.dataframe import dataframe_to_rows

            wb = Workbook()
            ws = wb.active
            ws.title = "海关公示数据"

            # 写入数据
            for r_idx, row in enumerate(dataframe_to_rows(export_df, index=False, header=True), 1):
                for c_idx, value in enumerate(row, 1):
                    ws.cell(row=r_idx, column=c_idx, value=value)

            # 保存到字节流
            buffer = io.BytesIO()
            wb.save(buffer)
            buffer.seek(0)
            content = buffer.getvalue()

            filename = f"海关公示数据_{timestamp}.xlsx"
            encoded_filename = quote(filename, safe='')
            return Response(
                content=content,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
            )
        except ImportError:
            # openpyxl 未安装，回退到 CSV
            content = export_df.to_csv(index=False, encoding="utf-8-sig")
            filename = f"海关公示数据_{timestamp}.csv"
            encoded_filename = quote(filename, safe='')
            return Response(
                content=content,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
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
