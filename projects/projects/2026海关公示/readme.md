# 海关公示数据整理与分析系统

本项目用于整理海关拟录用人员公示文件，将各关区 Word 公示表中的人员信息提取为结构化数据，并生成 CSV、Excel 以及可视化分析结果。

**数据来源**：国家公务员局专题网站 `bm.scs.gov.cn` 发布的各地海关公示文档（Word格式）。

**数据范围**：2026年度海关系统公务员招录公示，覆盖42个直属海关关区。

## 项目内容

项目围绕"公示文件整理 -> 数据抽取 -> 表格输出 -> 可视化分析"的流程展开：

- 批量规范化海关公示 Word 文件名称
- 从 Word 表格中提取拟录用人员信息
- 汇总生成 `2026海关公示汇总.csv`
- 将 CSV 转换为带表头样式、边框、自动列宽和冻结首行的 Excel 文件
- 基于汇总数据生成关区、学历、性别、院校、职位等分析图表

## 目录结构

```text
.
├── customs_pipeline/          # 核心功能模块
│   ├── config.py              # 路径、文件名、爬虫入口 URL 等配置
│   ├── crawler.py             # 爬取海关公示页面并下载附件
│   ├── normalizer.py          # 规范化 Word 文件名
│   ├── converter.py           # 将 .doc 批量转换为 .docx
│   ├── extractor.py           # 从 .docx 提取数据并生成 CSV
│   ├── exporter.py            # 将 CSV 导出为格式化 Excel
│   ├── validator.py           # 检查 42 个关区 .docx 是否齐全
│   └── cleanup.py             # 清理临时目录
├── downloads/                 # 原始海关公示 Word 文件
│   └── 2026/                  # 如：2026上海海关.doc、2026深圳海关.docx
├── temp/                      # 临时转换目录
│   └── 2026/
│       └── docx/              # 转换后的 .docx 文件
├── output/                    # 输出结果
│   └── 2026/
│       └── 2026海关公示汇总.csv
├── web/                       # Web 可视化系统
│   ├── api.py                 # FastAPI 后端分析接口
│   └── frontend/              # React + ECharts 前端
├── main.py                    # 一键运行爬取、转换、汇总和导出流程
├── requirements.txt           # Python 依赖清单
├── validate.py                # 检查 42 个关区 .docx 是否齐全
├── 海关公示数据分析.ipynb       # 数据分析与可视化 Notebook
└── readme.md                  # 项目说明文档
```

## 数据字段

CSV包含以下字段：

| 字段 | 说明 |
| --- | --- |
| 关区 | 海关关区或招录机关 |
| 拟录用职位及代码 | 公示表中的职位名称和职位代码 |
| 姓名 | 拟录用人员姓名 |
| 性别 | 拟录用人员性别 |
| 准考证号 | 公务员考试准考证号 |
| 学历 | 拟录用人员学历 |
| 毕业院校 | 毕业学校信息 |
| 工作单位 | 当前或原工作单位 |

## 环境依赖

建议使用 Python 3.9 或以上版本：

```bash
pip install -r requirements.txt
```

主要依赖：
- `requests`、`beautifulsoup4` — 爬取海关公示页面并解析附件链接
- `python-docx` — 读取 `.docx` 格式 Word 表格
- `pywin32` — Windows 环境中调用 Microsoft Word/WPS 将 `.doc` 转换为 `.docx`
- `openpyxl` — 生成格式化 Excel 文件
- `pandas`、`matplotlib`、`seaborn` — Notebook 数据分析和图表绘制
- `jupyter` — 运行 `海关公示数据分析.ipynb`
- `fastapi`、`uvicorn` — Web API 服务

## 使用步骤

### 一键运行

```bash
python main.py
```

流程会跳过联网爬取，依次执行文件名规范化、`.doc` 转 `.docx`、CSV 汇总和 Excel 导出。
转换后的 `.docx` 会保存到 `temp/2026/docx`，`downloads/2026` 保留原始下载文件。
在生成 CSV 前，`main.py` 会检查 `temp/2026/docx` 中是否已经具备 42 个关区的 `.docx` 文件；如果不齐全，会列出缺失关区并跳过本次 CSV 重新生成。

#### 爬取并处理

```bash
python main.py --crawl
```

也可以临时指定入口页：

```bash
python main.py --crawl "海关公示栏目页URL"
```

说明：`.doc` 转 `.docx` 依赖 `pywin32` 和本机 Microsoft Word/WPS；爬取依赖 `requests`、`beautifulsoup4` 和网络访问。

### Web 可视化系统

#### 启动后端 API

```bash
cd web
pip install -r requirements.txt
python api.py
```

访问 http://localhost:5000 查看可视化页面。

#### 启动前端开发服务器

```bash
cd web/frontend
pnpm install
pnpm dev
```

### 分步操作

#### 1. 爬取或准备原始文件

```bash
python -m customs_pipeline.crawler "海关公示栏目页URL"
```

也可以把入口页写入 `customs_pipeline/config.py` 的 `START_URLS`：

```python
START_URLS = [
    "海关公示栏目页URL",
]
```

然后直接运行：

```bash
python -m customs_pipeline.crawler
```

爬虫会在 `customs.gov.cn` 域名内查找包含关键词的页面，并下载附件到 `downloads/2026/` 目录，同时生成：

```text
output/2026/2026爬取公示附件记录.csv
```

#### 2. 规范文件名称

```bash
python -m customs_pipeline.normalizer
```

脚本会自动识别文件名中的"xx海关"字样，并输出重命名结果。

#### 3. 转换 doc 为 docx

```bash
python -m customs_pipeline.converter
```

转换结果保存到 `temp/2026/docx/`：

- 已存在同名 `.docx` 时默认跳过
- 如果未安装 `pywin32`，请先运行 `pip install pywin32`
- 确认本机已安装 Microsoft Word 或 WPS，且 Word 文件没有被其他程序打开
- 脚本会依次尝试 `Word.Application`、`KWPS.Application`、`WPS.Application`

#### 4. 生成 CSV 汇总表

完整性检查：

```bash
python validate.py
```

提取数据：

```bash
python -m customs_pipeline.extractor
```

生成：

```text
output/2026/2026海关公示汇总.csv
```

#### 5. 生成 Excel 文件

```bash
python -m customs_pipeline.exporter
```

生成：

```text
output/2026/2026海关公示汇总.xlsx
```

#### 6. 运行数据分析

打开并运行 Notebook：

```text
海关公示数据分析.ipynb
```

## 数据分析报告

基于 `output/2026/2026海关公示汇总.csv` 生成。

### 2026 年数据概览

- **公示录用人数**: 2,506 人
- **覆盖关区**: 42 个
- **涉及院校**: 约 800 所
- **职位种类**: 约 600 种

## 常见问题

1. **.doc 转 .docx 失败**: 确认已安装 pywin32 和 Microsoft Word/WPS
2. **42 个关区不完整**: 检查 downloads/2026/ 目录，确保所有关区文件已下载
3. **CSV 未生成**: 先运行转换脚本确保所有 .docx 齐全
4. **Web 服务无法启动**: 确认 5000 端口未被占用，或检查 `pip install -r web/requirements.txt`
