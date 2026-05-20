# 2026海关公示数据分析

## 项目概述

从国家公务员局专题网站抓取海关系统2026年度公务员招录公示数据，提取结构化信息并生成汇总表格，最终通过前端可视化展示。

**数据来源**：国家公务员局专题网站 `bm.scs.gov.cn` 发布的各地海关公示文档（Word格式）。

**数据范围**：2026年度海关系统公务员招录公示，覆盖42个直属海关关区。

**真实数据文件**：
- `output/2026/2026海关公示汇总.csv` — 唯一真实数据文件（从Word文档提取）

## 技术栈

| 层级 | 技术 |
|------|------|
| 数据采集 | Python + requests（抓取公告列表） |
| 文档处理 | python-docx（解析Word） |
| 数据转换 | pandas（CSV汇总） |
| 后端API | FastAPI + Uvicorn |
| 前端 | React 18 + Vite + ECharts |

## 目录结构

```
2026海关公示/
├── customs_pipeline/      # 核心处理模块
│   ├── config.py          # 路径配置（支持按年份目录）
│   ├── constants.py       # 共享常量（关区URL、高校名单等）
│   ├── crawler.py         # 网站爬取
│   ├── converter.py       # doc转docx
│   ├── extractor.py       # 信息提取
│   ├── exporter.py        # CSV转Excel
│   ├── validator.py       # 文件验证
│   ├── normalizer.py      # 文件重命名
│   └── cleanup.py         # 临时文件清理
├── web/
│   ├── api.py             # FastAPI后端
│   ├── schemas.py         # Pydantic 数据模型
│   ├── requirements.txt   # 后端依赖
│   ├── frontend/          # React前端
│   │   ├── src/
│   │   │   ├── App.jsx    # 主应用组件
│   │   │   ├── main.jsx   # 入口
│   │   │   └── index.css  # 样式
│   │   ├── index.html
│   │   ├── package.json
│   │   └── vite.config.js
│   ├── start-api.sh       # API启动脚本
│   └── start.sh           # 一键启动
├── scripts/
│   ├── coze-preview-build.sh
│   └── coze-preview-run.sh
├── downloads/             # 原始Word文件
│   └── 2026/              # 2026年原始文件
│       ├── 2026上海海关.doc
│       ├── 2026深圳海关.docx
│       └── ...
├── temp/                  # 临时文件
│   └── 2026/
│       └── docx/          # 转换后的docx
├── output/                # 输出结果
│   └── 2026/
│       └── 2026海关公示汇总.csv
├── main.py                # 主入口脚本
├── validate.py            # 验证脚本
├── readme.md              # 使用说明
└── AGENTS.md              # 本文件
```

## 关键入口

- `python main.py` — 本地处理（跳过爬取）
- `python main.py --crawl` — 爬取+处理
- `python validate.py` — 验证数据完整性
- `python web/api.py` — 启动后端服务
- `cd web/frontend && pnpm dev` — 前端开发服务器

## 数据字段

CSV包含以下字段：
- **关区** — 所属海关关区（如"上海海关"）
- **拟录用职位及代码** — 具体职位名称
- **姓名** — 拟录用人员姓名
- **性别** — 男/女
- **准考证号** — 考生准考证号
- **学历** — 博士研究生/硕士研究生/大学本科/大学专科
- **毕业院校** — 毕业学校全称
- **工作单位** — 原工作单位（应届生为空）

## 后端API

| 接口 | 说明 |
|------|------|
| GET `/api/overview` | 总体统计 + Top10排行 |
| GET `/api/districts` | 各关区录用人数及占比 |
| GET `/api/education` | 学历分布 + 关区构成 |
| GET `/api/gender` | 性别分布 + 关区构成 |
| GET `/api/schools` | 院校统计（985/211/其他） |
| GET `/api/positions` | 职位排行 |
| GET `/api/employment` | 应届/在职统计 |
| GET `/api/district/{name}` | 指定关区详情 |
| GET `/api/search` | 多条件查询（关键词/关区/学历/性别） |

## 前端功能

- **总体概览**：统计卡片 + 学历/在职饼图 + Top10 排行柱状图
- **关区分析**：排行柱状图 + 性别堆叠图 + 可点击详情弹窗
- **学历分析**：饼图 + 柱状图 + 各关区构成表格
- **性别分析**：统计卡片 + 饼图 + 堆叠图
- **院校分析**：985/211/其他饼图 + Top20 院校排行
- **数据查询**：多条件筛选面板 + 高亮结果表格 + 分页

## 三端适配

- **电脑网页（≥1024px）**：左侧 220px 展开侧边栏，点击汉堡菜单可收起为 64px 图标栏；4列统计卡片，双列图表网格
- **平板端（768px-1023px）**：默认 64px 收起图标栏，点击汉堡菜单展开为 220px；2列统计卡片
- **手机端（<768px）**：侧边栏作为抽屉从左侧滑入（260px），点击汉堡菜单打开，点击遮罩层关闭；单列布局，表格横向滚动
- **小屏手机（<480px）**：单列统计卡片，更紧凑的间距和字体

## 数据规模

| 年份 | 公示录用 | 关区数 | 院校数 |
|------|---------|--------|--------|
| 2026 | 2,506   | 42     | 约800  |

## 常见问题

**Word解析失败**
- 确保python-docx >= 0.8.11
- 尝试antiword或手动转换

**数据异常值**
- 上海海关学院毕业生最多（专业性院校）
- 部分院校名称存在简写/全称不一致

**前后端端口**
- 预览：FastAPI 托管静态文件，统一 5000 端口
- 开发：前端 Vite 代理 /api 到后端

## 代码优化记录

### 健壮性优化

**api.py**
- 修复 FastAPI 应用重复定义问题（删除第二个 `app = FastAPI()`）
- 添加数据加载验证：启动时检查必需列是否存在
- 添加健康检查接口 `/api/health`
- 改进错误处理：使用空 DataFrame 防止启动失败
- 添加 `ensure_int()` 辅助函数防止类型转换错误
- 修复路由顺序：`/{full_path:path}` 放在所有 API 路由之后

**schemas.py**
- 使用 Pydantic v2 `Annotated` 添加字段验证
- 添加 `field_validator` 验证输入参数
- 添加 `HealthResponse` schema
- 增强默认值处理

**config.py**
- 使用 `pathlib.Path` 替代 `os.path`
- 使用 `Final` 类型注解确保常量不可变
- 添加 `ensure_dir()` 和 `validate_year()` 工具函数
- 统一使用 Path 类型

**extractor.py**
- 预编译正则表达式，提升性能
- 抽取列名映射配置，支持多种表头命名
- 添加 `should_skip_name()` 辅助函数
- 添加 `build_column_map()` 列映射构建函数
- 改进异常处理和日志输出

### 可复用性优化

**新增 constants.py**
- 统一管理所有共享常量
- 985/211 高校名单
- 海关关区 URL 映射
- 职位级别匹配模式
- 预编译正则表达式
- 提供 `classify_school()`, `extract_level()`, `get_district_url()` 等工具函数

**启动脚本**
- 添加 `PYTHONPATH` 环境变量设置
- 确保 `customs_pipeline` 模块可正确导入

### 技术债务
- 保留 api.py 中部分未使用的 import（DISTRICT_URLS 等），避免破坏现有调用链
