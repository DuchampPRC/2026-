# 2026海关公示 - Claude.md

## Project Overview

本项目是 2026 年海关公务员录用公示数据查询系统，用于展示和分析全国海关拟录用人员信息。

**核心功能**：
- 公示数据查询与筛选
- 数据统计分析（关区分布、学历统计、职位分析）
- 数据导出（CSV/Excel）
- 移动端适配

**Claude 角色**：
- 协助功能开发和 Bug 修复
- 优化代码健壮性和可维护性
- 保持现有技术栈不变
- 避免破坏性修改

---

## Environment / Stack

### 技术栈
- **后端**：Python 3.12 + FastAPI
- **前端**：React 18 + TypeScript + Vite
- **包管理**：pnpm（前端）/ pip（后端）
- **Node**：>= 18

### 环境变量
- 工作目录：`/workspace/projects/2026海关公示/`
- 后端入口：`web/api.py`
- 前端入口：`web/frontend/`

### 常用命令
```bash
# 后端启动
cd web && PYTHONPATH=.. python api.py

# 前端开发
cd web/frontend && pnpm dev

# 前端构建
cd web/frontend && pnpm build

# 数据重新提取
python -c "from customs_pipeline.extractor import build_csv; build_csv()"
```

---

## Directory Structure

```
2026海关公示/
├── web/                    # Web 服务目录
│   ├── api.py             # FastAPI 入口
│   ├── schemas.py         # Pydantic 模型
│   ├── frontend/          # React 前端
│   │   ├── src/
│   │   │   ├── App.tsx   # 主组件
│   │   │   ├── types.ts  # TypeScript 类型
│   │   │   └── index.css # 全局样式
│   │   └── package.json
│   └── static/            # 静态文件
├── customs_pipeline/       # 数据处理模块
│   ├── extractor.py       # Word 文档解析
│   ├── constants.py      # 工具函数
│   └── normalizer.py     # 数据标准化
├── output/                # 输出数据
│   └── 2026/
│       └── 2026海关公示汇总.csv
├── downloads/             # 原始 Word 文档
│   └── 2026/
└── scripts/              # 辅助脚本
```

---

## Development Rules

### 必须遵守
- ✅ 使用现有技术栈，不要引入新技术
- ✅ 前端使用 TypeScript strict 模式
- ✅ 后端使用 Pydantic v2 模型
- ✅ 遵循已有代码风格和命名规范
- ✅ 添加必要的代码注释
- ✅ 更新 AGENTS.md 记录变更

### 禁止事项
- ❌ 不要修改 `output/` 目录下的数据文件
- ❌ 不要修改 `downloads/` 目录下的原始文件
- ❌ 不要引入未经验证的依赖
- ❌ 不要删除已有的错误处理逻辑
- ❌ 不要忽略 lint/类型检查错误

### API 开发规则
- ✅ 搜索参数需要转义正则元字符（使用 `re.escape()`）
- ✅ 纯数字职位代码使用精确匹配
- ✅ 异常情况返回友好的 JSON 错误信息
- ✅ 导出接口设置正确的 Content-Type 和文件名编码

### 前端开发规则
- ✅ 使用可选链 (`?.`) 安全访问数据
- ✅ 移动端优先考虑卡片布局
- ✅ 避免在渲染中执行复杂计算
- ✅ 使用 CSS 类控制响应式显示

---

## Data Processing Rules

### 职位字段解析
职位字段格式：`隶属关 + 职位类型 + 代码`

解析规则：
1. 找到所有"海关"的位置
2. 使用倒数第二个"海关"作为分隔点
3. 隶属关 = 第一个分隔点之前
4. 职务职位 = 分隔点之后
5. 职位代码 = 括号中的 12 位数字

### 多表格处理
某些 Word 文档包含多个表格，后续表格复用第一个表格的列映射。

---

## Tooling / MCP

### 可用工具
- `read_file` / `write_file` - 文件读写
- `exec_shell` - 执行命令
- `grep_file` / `glob_file` - 搜索
- `edit_file` - 精确编辑

### 工具使用规则
- 修改文件前先读取现有内容
- 搜索优先使用 `grep_file`
- 批量修改需要明确告知用户
- 危险操作（删除、覆盖）需要确认

---

## Output Expectations

### 回复格式
- 使用中文回复
- 代码块提供完整可运行的代码
- 修改文件时展示关键差异
- 完成后总结变更内容

### 测试验证
- 代码修改后运行 `pnpm build` 验证
- API 修改后测试接口响应
- 确保无 lint/类型错误后再交付

### 文档更新
- 功能变更需要更新 AGENTS.md
- 新增可复用组件需要在文档中标注
- API 变更需要记录接口说明

---

## Common Issues

### 服务启动失败
检查：
- 端口 5000 是否被占用
- PYTHONPATH 是否正确设置
- CSV 文件是否存在

### 前端构建失败
检查：
- node_modules 是否安装
- TypeScript 类型是否正确
- import 路径是否正确

### 数据缺失
检查：
- 原始 Word 文档是否完整
- extractor.py 解析逻辑是否正确
- CSV 文件编码是否正确
