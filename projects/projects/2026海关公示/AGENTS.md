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
