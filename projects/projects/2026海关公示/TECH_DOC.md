# 2026海关公示数据分析系统 - 技术文档

> 本文档基于《前端项目技术文档生成器》模板自动生成

---

## 1. 项目概述（Project Overview）

### 1.1 项目功能、用途、业务定位

**项目名称**：2026海关公示数据分析系统

**核心功能**：从国家公务员局专题网站抓取海关系统2026年度公务员招录公示数据，自动提取结构化信息并生成汇总表格，通过可视化前端页面展示。

**业务定位**：
- 数据采集：自动化抓取各地海关公示公告（Word格式）
- 数据处理：解析文档、提取人员信息、汇总统计
- 数据展示：提供交互式Web界面进行数据查询和分析

**数据来源**：`bm.scs.gov.cn` 国家公务员局专题网站

**数据范围**：2026年度海关系统公务员招录公示，覆盖42个直属海关关区

### 1.2 前端技术栈

| 类别 | 技术 |
|------|------|
| 框架 | React 18 + TypeScript |
| 构建工具 | Vite 5 |
| HTTP客户端 | 原生 fetch API |
| 样式 | CSS3 (CSS Variables) |
| 图表 | 原生 CSS（移除ECharts） |

### 1.3 后端技术栈

| 类别 | 技术 |
|------|------|
| 框架 | FastAPI |
| 数据处理 | pandas |
| 文档解析 | python-docx |
| 服务器 | Uvicorn |
| 验证 | Pydantic v2 |

### 1.4 项目亮点和架构意图

- **自动化数据采集**：从政府网站自动抓取公示文档，减少人工操作
- **数据结构化**：将非结构化Word文档转换为标准化CSV数据
- **前后端分离**：FastAPI后端 + React前端，便于独立开发和部署
- **响应式设计**：三端适配（PC/平板/手机）
- **零外部图表依赖**：使用原生CSS实现图表效果，减少包体积（160KB）

---

## 2. 项目目录结构（Project Structure）

```
2026海关公示/
├── customs_pipeline/           # 数据处理核心模块 ⭐
│   ├── __init__.py
│   ├── config.py              # 路径配置（年份目录支持）
│   ├── constants.py            # 共享常量（高校名单、关区URL等）
│   ├── crawler.py              # 网站爬虫
│   ├── converter.py            # doc → docx 转换
│   ├── extractor.py            # 信息提取（正则匹配）
│   ├── exporter.py              # CSV/Excel 导出
│   ├── validator.py             # 数据验证
│   ├── normalizer.py            # 文件名规范化
│   └── cleanup.py              # 临时文件清理
│
├── web/                        # Web服务 ⭐
│   ├── api.py                  # FastAPI 后端入口
│   ├── schemas.py              # Pydantic 数据模型
│   ├── requirements.txt        # Python 依赖
│   │
│   ├── frontend/               # React 前端 ⭐
│   │   ├── src/
│   │   │   ├── App.tsx         # 主应用组件（核心UI）
│   │   │   ├── App.jsx         # JSX 别名入口
│   │   │   ├── main.tsx        # React 入口
│   │   │   ├── types.ts        # TypeScript 类型定义
│   │   │   └── index.css       # 全局样式
│   │   ├── index.html
│   │   ├── package.json
│   │   ├── pnpm-lock.yaml
│   │   ├── tsconfig.json
│   │   └── vite.config.ts
│   │
│   ├── start-api.sh            # 后端启动脚本
│   └── start.sh                # 一键启动脚本
│
├── scripts/                    # Coze 平台脚本
│   ├── coze-preview-build.sh   # 预览构建
│   ├── coze-preview-run.sh     # 预览运行
│   ├── coze-deploy-build.sh    # 部署构建
│   └── coze-deploy-run.sh      # 部署运行
│
├── downloads/                  # 原始下载文件
│   └── 2026/
│       ├── 2026上海海关.doc
│       └── ...
│
├── temp/                      # 临时文件
│   └── 2026/
│       └── docx/
│
├── output/                     # 输出结果 ⭐
│   └── 2026/
│       └── 2026海关公示汇总.csv  # 唯一真实数据源
│
├── main.py                     # 主入口脚本
├── validate.py                 # 数据验证脚本
├── readme.md                   # 使用说明
├── .coze                       # Coze 平台配置
└── AGENTS.md                   # Agent 记忆文件
```

### 目录职责说明

| 目录 | 作用 | 核心业务 |
|------|------|---------|
| `customs_pipeline/` | 数据采集与处理 | ✅ 核心业务 |
| `web/` | Web服务层 | ✅ 核心业务 |
| `web/frontend/` | 前端应用 | ✅ 核心业务 |
| `scripts/` | 平台部署脚本 | 配置目录 |
| `output/` | 数据输出 | 数据目录 |
| `downloads/` | 原始数据 | 数据目录 |

---

## 3. 核心模块分析（Core Modules）

### 3.1 前端核心模块

#### 3.1.1 API请求模块

**文件**：`web/frontend/src/App.tsx` (内嵌)

**职责**：封装fetch请求，统一错误处理

**核心逻辑**：
```typescript
// useFetch Hook - 数据获取抽象
function useFetch<T>(url: string): FetchState<T> {
  const [state, setState] = useState<FetchState<T>>({
    loading: true,
    data: null,
    error: null
  });
  
  useEffect(() => {
    fetch(url)
      .then(res => res.json())
      .then(data => setState({ loading: false, data, error: null }))
      .catch(error => setState({ loading: false, data: null, error }));
  }, [url]);
  
  return state;
}
```

**API端点映射**：
| Hook | URL | 数据 |
|------|-----|------|
| `overviewState` | `/api/overview` | 总览统计 |
| `districtsState` | `/api/districts` | 关区列表 |
| `schoolsState` | `/api/schools` | 院校统计 |
| `positionsState` | `/api/positions/analysis` | 职位分析 |

#### 3.1.2 状态管理

**方案**：React useState + useEffect（无外部状态库）

**全局状态**：
```typescript
// 页面状态
const [activeTab, setActiveTab] = useState('overview');
const [isSidebarOpen, setIsSidebarOpen] = useState(false);

// 筛选状态
const [selectedDistrict, setSelectedDistrict] = useState('');
const [selectedEducation, setSelectedEducation] = useState('');
const [selectedGender, setSelectedGender] = useState('');

// 查询状态
const [searchQuery, setSearchQuery] = useState('');
```

#### 3.1.3 组件库

| 组件 | 文件位置 | 职责 |
|------|---------|------|
| `StatCard` | App.tsx 内联 | 统计卡片显示 |
| `BarChart` | App.tsx 内联 | 柱状图（CSS实现） |
| `PieChart` | App.tsx 内联 | 饼图（CSS实现） |
| `DataTable` | App.tsx 内联 | 数据表格 |
| `DistrictDetailModal` | App.tsx 内联 | 关区详情弹窗 |
| `SearchPanel` | App.tsx 内联 | 搜索筛选面板 |

### 3.2 后端核心模块

#### 3.2.1 API路由模块

**文件**：`web/api.py`

**职责**：提供RESTful API接口

**核心端点**：
```python
# 健康检查
GET /api/health

# 数据统计
GET /api/overview      # 总体统计 + Top10
GET /api/districts      # 关区统计
GET /api/schools        # 院校统计
GET /api/positions      # 职位统计

# 数据分析
GET /api/education      # 学历分布
GET /api/gender         # 性别分布
GET /api/employment     # 应届/在职

# 数据查询
GET /api/district/{name}  # 关区详情
GET /api/search           # 多条件查询
```

#### 3.2.2 数据模型

**文件**：`web/schemas.py`

```python
class OverviewResponse(BaseModel):
    total: int                    # 总人数
    districts: int                # 关区数
    schools: int                  # 院校数
    positions: int                # 职位数
    top_districts: List[Dict]     # Top10关区
    top_schools: List[Dict]       # Top10院校
    education_stats: List[Dict]   # 学历统计
    gender_stats: List[Dict]      # 性别统计
```

#### 3.2.3 数据处理模块

**文件**：`customs_pipeline/extractor.py`

**职责**：从Word文档提取结构化数据

**核心流程**：
1. 读取Word表格
2. 匹配表头列名
3. 提取人员信息
4. 分类高校（985/211/其他）
5. 汇总输出CSV

---

## 4. 关键代码深度解析（Important Code Insight）

### 4.1 前端入口文件

**文件**：`web/frontend/src/main.tsx`

```typescript
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

// 直接挂载，移除 StrictMode 避免开发环境重复渲染
ReactDOM.createRoot(document.getElementById('root')!).render(
  <App />
)
```

**关键决策**：
- 移除 `React.StrictMode`：避免开发环境双重调用导致的潜在问题
- 单一路由入口：SPA架构，所有页面在App组件内切换

### 4.2 主应用组件

**文件**：`web/frontend/src/App.tsx`

**核心结构**：
```
App
├── Header (侧边栏/顶部栏)
├── Main Content
│   ├── Overview Tab (统计概览)
│   ├── Districts Tab (关区分析)
│   ├── Schools Tab (院校分析)
│   ├── Positions Tab (职位分析)
│   └── Search Tab (数据查询)
├── DistrictDetailModal (详情弹窗)
└── Loading State
```

**数据获取流程**：
```typescript
// 初始化时并行请求所有数据
useEffect(() => {
  if (!overviewState?.data) return;
  if (!districtsState?.data) return;
  if (!schoolsState?.data) return;
  if (!positionsState?.data) return;
  
  setIsReady(true);
}, [overviewState?.data, districtsState?.data, 
    schoolsState?.data, positionsState?.data]);
```

### 4.3 后端数据加载

**文件**：`web/api.py`

```python
# 全局数据加载（启动时执行）
try:
    df = pd.read_csv(CSV_PATH, encoding='utf-8')
    REQUIRED_COLUMNS = ['关区', '姓名', '毕业院校', ...]
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        print(f"警告：缺失列 {missing}")
        df = pd.DataFrame()
    DATA_LOADED = True
except Exception as e:
    print(f"数据加载失败: {e}")
    df = pd.DataFrame()
    DATA_LOADED = False
```

**安全措施**：
- 启动时验证必需列
- 缺失列时使用空DataFrame防止崩溃
- `/api/health` 接口提供数据状态检查

---

## 5. 前端架构设计（Architecture）

### 5.1 分层结构

```
┌─────────────────────────────────────────┐
│         Presentation Layer              │
│   (StatCard, BarChart, DataTable)      │
├─────────────────────────────────────────┤
│          Page Layer                     │
│   (Overview, Districts, Schools, etc.)   │
├─────────────────────────────────────────┤
│         State Layer                     │
│   (useState, useFetch, activeTab)        │
├─────────────────────────────────────────┤
│         Service Layer                   │
│   (API calls via fetch)                 │
├─────────────────────────────────────────┤
│          Backend Layer                  │
│   (FastAPI + pandas + CSV)              │
└─────────────────────────────────────────┘
```

### 5.2 数据流动方式

```
User Action
    ↓
setState() 更新本地状态
    ↓
useEffect 监听状态变化
    ↓
触发 API 请求 (useFetch)
    ↓
fetch() → /api/* 
    ↓
后端 pandas 处理 CSV
    ↓
JSON 响应返回
    ↓
更新组件状态
    ↓
React 重新渲染
```

### 5.3 组件通信方式

| 方式 | 示例 | 用途 |
|------|------|------|
| Props 向下传递 | `<StatCard value={2506} />` | 展示数据 |
| State 上报 | `setActiveTab('overview')` | 切换页面 |
| 条件渲染 | `{activeTab === 'overview' && <Overview />}` | 页面切换 |

### 5.4 可视化架构图

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  StatCard   │     │  BarChart   │     │  PieChart   │
│  (统计卡片)  │     │  (柱状图)   │     │  (饼图)     │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                    ┌──────▼──────┐
                    │   Overview  │
                    │   Component │
                    └──────┬──────┘
                           │
       ┌───────────────────┼───────────────────┐
       │                   │                   │
┌──────▼──────┐     ┌──────▼──────┐     ┌──────▼──────┐
│ /api/overview│     │/api/districts│     │/api/schools │
└─────────────┘     └─────────────┘     └─────────────┘
```

---

## 6. 应用运行流程（Runtime Flow）

### 6.1 前端启动流程

```
1. 浏览器访问 http://localhost:5000
   ↓
2. FastAPI 返回 index.html
   ↓
3. 浏览器加载 index.html
   ↓
4. 加载 index-BVu5WIBz.js (bundle)
   ↓
5. ReactDOM.createRoot().render(<App />)
   ↓
6. App 组件初始化
   ↓
7. 并行发起 4 个 API 请求
   ↓
8. 等待所有数据返回
   ↓
9. setIsReady(true)
   ↓
10. 渲染主界面
```

### 6.2 后端请求处理

```
GET /api/overview
    ↓
FastAPI 路由匹配
    ↓
读取全局 df DataFrame
    ↓
pandas 统计分析
    - 总人数统计
    - Top10 关区排行
    - 学历分布计算
    - 性别分布计算
    ↓
构造响应 JSON
    ↓
返回 {"total": 2506, "districts": 42, ...}
```

### 6.3 页面切换流程

```
用户点击 "院校分析"
    ↓
setActiveTab('schools')
    ↓
触发条件渲染
    ↓
显示 SchoolsContent 组件
    ↓
读取 schoolsState?.data
    ↓
渲染院校统计表格
```

---

## 7. 工程化配置分析（Build & Tooling）

### 7.1 构建工具

**Vite 配置**：`web/frontend/vite.config.js`

```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:5000'
    }
  }
})
```

### 7.2 TypeScript 配置

**文件**：`web/frontend/tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"]
}
```

### 7.3 环境变量

| 变量 | 说明 |
|------|------|
| `PYTHONPATH` | 必须包含项目根目录，确保 customs_pipeline 可导入 |
| 端口 5000 | FastAPI 服务端口 |

### 7.4 包管理

**前端**：pnpm（禁止使用 npm/yarn）
```bash
pnpm install
pnpm dev      # 开发服务器
pnpm build    # 生产构建
```

**后端**：pip
```bash
pip install -r web/requirements.txt
```

---

## 8. 启动 & 开发指南（Run & Development Guide）

### 8.1 快速启动

**方式一：一键启动**
```bash
cd /workspace/projects/projects/projects/2026海关公示
bash scripts/coze-preview-run.sh
```

**方式二：分别启动**
```bash
# 后端
cd web
PYTHONPATH="/workspace/projects/projects/projects/2026海关公示:$PYTHONPATH" python api.py

# 前端（开发模式）
cd web/frontend
pnpm dev
```

### 8.2 生产构建

```bash
# 构建前端
cd web/frontend
pnpm build  # 输出到 dist/

# 构建并运行
bash scripts/coze-preview-build.sh
bash scripts/coze-preview-run.sh
```

### 8.3 调试建议

**浏览器调试**：
- 打开 F12 开发者工具
- Network 标签查看 API 请求
- Console 标签查看错误信息
- Elements 标签检查 DOM 结构

**后端调试**：
```bash
# 查看日志
tail -f /tmp/api.log

# 测试 API
curl http://localhost:5000/api/health
```

### 8.4 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| `ModuleNotFoundError` | PYTHONPATH 未设置 | 添加 `PYTHONPATH` 环境变量 |
| 数据未加载 | CSV 文件不存在或路径错误 | 检查 `output/2026/2026海关公示汇总.csv` |
| 页面空白 | 数据加载中或 API 请求失败 | 检查 F12 控制台错误 |
| 端口占用 | 5000 端口被占用 | `fuser -k 5000/tcp` 释放端口 |

---

## 9. 新人快速上手指南（Onboarding Guide）

### 9.1 先看哪些文件？

**必读**：
1. `AGENTS.md` - 项目整体说明
2. `readme.md` - 使用说明
3. `web/api.py` - 后端入口
4. `web/frontend/src/App.tsx` - 前端入口

**数据相关**：
- `output/2026/2026海关公示汇总.csv` - 真实数据

### 9.2 如何运行项目？

```bash
# 1. 克隆项目（已在 /workspace）

# 2. 安装前端依赖
cd web/frontend
pnpm install

# 3. 启动后端
cd ../..
cd web
PYTHONPATH="$(pwd)/.." python api.py &

# 4. 访问
open http://localhost:5000
```

### 9.3 如何新增 API 端点？

**Step 1**: 在 `web/api.py` 添加路由

```python
@ app.get("/api/new-endpoint")
def new_endpoint():
    # 你的逻辑
    return {"data": result}
```

**Step 2**: 前端添加请求

```typescript
const { data } = useFetch('/api/new-endpoint');
```

### 9.4 如何新增页面 Tab？

**Step 1**: 添加 Tab 按钮

```tsx
<button 
  className={activeTab === 'newtab' ? 'active' : ''}
  onClick={() => setActiveTab('newtab')}
>
  新页面
</button>
```

**Step 2**: 添加内容组件

```tsx
{activeTab === 'newtab' && (
  <div className="tab-content">
    {/* 你的内容 */}
  </div>
)}
```

### 9.5 组件开发规范

```tsx
// 1. 类型定义
interface Props {
  title: string;
  value: number | string;
}

// 2. 函数组件
function StatCard({ title, value }: Props) {
  return (
    <div className="stat-card">
      <span className="stat-title">{title}</span>
      <span className="stat-value">{value}</span>
    </div>
  );
}

// 3. 安全访问
const displayValue = data?.value ?? '—';
```

### 9.6 提交规范

```
feat: 新增院校分析页面
fix: 修复数据加载状态显示问题
refactor: 重构 API 请求逻辑
style: 优化卡片样式
docs: 更新技术文档
```

---

## 10. 技术债 & 改进建议（Technical Debt & Improvements）

### 10.1 已知问题

| 问题 | 严重度 | 说明 |
|------|--------|------|
| 保留未使用 import | 低 | `api.py` 中保留常量导入避免破坏调用链 |
| 部分类型定义宽松 | 低 | 某些 API 响应使用 `Dict` 而非具体类型 |
| 缺少单元测试 | 中 | 后端无 pytest 测试用例 |

### 10.2 可改进点

**前端**：
- [ ] 添加 React Router 实现真正的路由跳转
- [ ] 引入状态管理库（Zustand/Redux）替代 useState
- [ ] 添加分页组件支持大数据量表格
- [ ] 恢复 ECharts 实现更丰富的图表交互
- [ ] 添加 TypeScript 严格模式检查

**后端**：
- [ ] 添加数据库支持（SQLite/PostgreSQL）替代 CSV
- [ ] 添加缓存层（Redis）提升查询性能
- [ ] 实现 API 认证（JWT）
- [ ] 添加请求限流防止滥用

**数据处理**：
- [ ] 自动化数据更新脚本
- [ ] 数据质量监控
- [ ] 支持多年份数据对比

### 10.3 架构优化建议

**当前架构**：
```
CSV → pandas → FastAPI → React → Browser
```

**优化后架构**：
```
CSV/Database → API Service → State Management → React → Browser
                    ↓
              Redis Cache
```

---

## 附录：数据字典

### CSV 字段说明

| 字段名 | 类型 | 说明 | 示例 |
|--------|------|------|------|
| 关区 | string | 所属海关 | "上海海关" |
| 拟录用职位及代码 | string | 职位名称+代码 | "海关业务（一）212234001" |
| 姓名 | string | 录用人员姓名 | "张三" |
| 性别 | string | 男/女 | "女" |
| 准考证号 | string | 考生准考证号 | "123456789012" |
| 学历 | string | 学历层次 | "硕士研究生" |
| 毕业院校 | string | 学校全称 | "复旦大学" |
| 工作单位 | string | 原单位（应届为空） | "某科技有限公司" |

### 高校分类规则

| 类别 | 来源 | 说明 |
|------|------|------|
| 985 | constants.py | 39所985工程高校 |
| 211 | constants.py | 112所211工程高校 |
| 其他 | - | 非985/211高校 |

---

*文档生成时间：2024年*
*基于《前端项目技术文档生成器》Prompt模板*
