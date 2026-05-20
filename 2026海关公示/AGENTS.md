# 2026海关公示项目

## 项目概述
- **功能**：整理海关拟录用人员公示文件，提取结构化数据并提供可视化分析
- **数据规模**：2506人、42个关区、618所高校、1736个职位

## 技术栈
- **后端**：Python 3.12 + FastAPI + Pandas
- **前端**：React 18 + TypeScript + Vite + 原生 CSS
- **数据**：2506条汇总记录

## 目录结构
```
├── customs_pipeline/   # Python 数据处理模块
│   └── constants.py   # 包含 parse_position_field() 等工具函数
├── output/2026/      # 汇总数据 (CSV/Excel)
├── web/              # Web 可视化系统
│   ├── api.py        # FastAPI 后端 (端口 5000)
│   ├── schemas.py    # Pydantic 数据模型
│   └── frontend/     # React 前端
├── scripts/          # 构建/预览脚本
└── readme.md        # 项目文档
```

## 核心入口
- **后端**：`web/api.py` → 启动 `PYTHONPATH=. python api.py`
- **前端**：`web/frontend/` → `pnpm build`
- **数据文件**：`output/2026/2026海关公示汇总.csv`

## 预览链路
- **类型**：Web 预览型项目
- **入口**：`/workspace/projects/.coze`（根 `.coze`）
- **子项目**：`/workspace/projects/2026海关公示/.coze`
- **预览命令**：
  - Build：`bash 2026海关公示/scripts/coze-preview-build.sh`
  - Run：`bash 2026海关公示/scripts/coze-preview-run.sh`
- **端口**：5000（IPv4 全接口 `0.0.0.0:5000`）
- **技术说明**：后端 FastAPI 同时提供静态文件服务，预览时无需独立前端服务

## API 端点
| 端点 | 说明 |
|------|------|
| `/api/health` | 健康检查 |
| `/api/overview` | 统计概览 |
| `/api/districts` | 关区列表 |
| `/api/schools` | 高校列表 |
| `/api/positions` | 职位列表 |
| `/api/search` | 搜索筛选 |

## 职位字段解析
- **原始字段**：`拟录用职位及代码`（如"上海浦东国际机场海关海关业务二级主办及以下职位(300110101001)"）
- **解析函数**：`customs_pipeline.constants.parse_position_field()`
- **解析结果**：
  - `隶属关`：隶属关区名称（如"上海浦东国际机场海关"，已处理重复"海关"）
  - `职务职位`：职务职位名称（如"业务二级主办及以下职位"）
  - `职位代码`：12位职位代码
- **应用范围**：`/api/search`、`/api/positions/analysis` 均使用解析后的字段

## 可复用变量/常量

### 后端 (customs_pipeline/constants.py)
| 变量/函数 | 说明 | 使用场景 |
|-----------|------|----------|
| `parse_position_field(text)` | 解析职位字段，返回字典 {隶属关, 职务职位, 职位代码} | search、positions/analysis 接口 |

> **算法说明**：找到所有"海关"的位置，使用倒数第二个"海关"作为分隔点。正确处理：
> - "XX海关海关YY" → 隶属关="XX海关"，职务职位="海关YY..."（保留职位中的"海关"前缀）
> - "XX海关YY" → 隶属关="XX海关"，职务职位="YY..."
| `extract_level(text)` | 提取职位级别（一级主办/二级主办等） | positions/analysis 接口 |
| `filter_by_keywords(df, col, keywords)` | 关键字过滤，支持多关键字 AND，使用 re.escape() 转义正则元字符防止注入 | search 接口 |
| 职位搜索优化 | 纯数字输入 → 精确匹配职位代码；关键字输入 → 模糊匹配职务职位 | search 接口 position 参数 |

### 新增接口

| 接口 | 说明 | 参数 |
|------|------|------|
| `/api/export` | 导出筛选数据为 CSV/Excel | format(csv/xlsx), name, school, position, district, education, gender |
| `ensure_int(val)` | 安全转换为整数 | 所有统计接口 |
| `SAFE_DEFAULTS` | 各字段的安全默认值 | 数据加载时填充空值 |

### 后端 (schemas.py)
| 类型 | 说明 | 使用场景 |
|------|------|----------|
| `IntRange` | 整数范围限制 [1-1000] | 需要限制数值的字段 |
| `PageSize` | 分页大小限制 [1-100] | search 接口 page_size |

### 前端 (types.ts)
| 类型 | 说明 | 对应后端 |
|------|------|----------|
| `Overview` | 概览数据 | OverviewResponse |
| `SearchItem` | 搜索结果项 | SearchResultItem |
| `PositionAnalysis` | 职位分析 | PositionAnalysisResponse |
| `FetchState<T>` | 数据获取状态 | useFetch hook |

### 前端 CSS 变量 (index.css)
| 变量 | 说明 |
|------|------|
| `--primary` | 主色调（蓝色） |
| `--success/warning/danger` | 语义色 |
| `--shadow-sm/md/lg/xl` | 阴影层级 |
| `--radius-sm/md/lg/xl` | 圆角层级 |
| `--transition-fast/normal/slow` | 过渡动画时长 |

### CSS 类控制
| 类名 | 说明 |
|------|------|
| `.show-on-desktop` | 仅桌面端显示 |
| `.hide-on-desktop` | 仅移动端显示 |

## 响应式断点
- **桌面端**：>= 1024px，完整布局
- **平板端**：768px - 1023px，简化布局
- **手机端**：< 768px，搜索 + 数据分析模块

## 运行命令
```bash
# 后端
cd web && PYTHONPATH=/path/to/project python api.py

# 前端
cd web/frontend && pnpm build
```

## 注意事项
- 前端使用原生 CSS（无 ECharts 等图表库）
- 所有 useFetch 返回值需安全访问：`?.data ?? fallback`
- 数据文件路径：`output/2026/2026海关公示汇总.csv`
- 职位字段解析返回字典，使用 `?.get()` 安全访问
