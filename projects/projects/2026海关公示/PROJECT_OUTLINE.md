# 2026海关公示项目设计大纲

## 一、项目概述

### 1.1 项目背景
2026年海关公务员招录信息公示系统，用于展示全国海关的招录数据，包括关区信息、高校分布、职位分析等。

### 1.2 项目定位
- **面向对象**：准备报考海关公务员的考生
- **核心价值**：整合分散的海关公示信息，提供便捷的查询和分析服务
- **数据规模**：2500+ 条公示记录，覆盖 42 个关区，618 所高校

---

## 二、技术架构设计

### 2.1 整体架构（前后端分离）

```
┌─────────────────────────────────────────────────────────┐
│                      用户浏览器                          │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                    CDN / Nginx                           │
│              (静态资源加速 + 反向代理)                    │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        ▼                                       ▼
┌───────────────────┐               ┌───────────────────┐
│     前端 (React)   │               │   后端 (FastAPI)   │
│                   │               │                   │
│  - 页面渲染       │   REST API    │  - 业务逻辑        │
│  - 用户交互       │◄─────────────►│  - 数据处理        │
│  - 状态管理       │               │  - 数据存储        │
└───────────────────┘               └───────────────────┘
```

### 2.2 技术栈

| 层级 | 技术选型 | 说明 |
|------|---------|------|
| **前端框架** | React 18 + TypeScript | 类型安全，生态丰富 |
| **构建工具** | Vite | 快速的开发体验 |
| **样式方案** | CSS Variables + 原生CSS | 轻量，无依赖 |
| **后端框架** | FastAPI | 高性能，自动文档 |
| **数据处理** | Pandas + Python | 数据清洗和分析 |
| **数据存储** | JSON 文件 | 轻量，无需数据库 |

### 2.3 分层架构

```
┌─────────────────────────────────────────────────────────┐
│                    表现层 (Presentation)                │
│         前端：React 组件、CSS 样式、用户交互            │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                    接口层 (API)                          │
│              RESTful API、请求验证、响应格式化           │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                    业务逻辑层 (Service)                  │
│         数据处理、业务规则、数据聚合、搜索过滤            │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                    数据访问层 (Data Access)              │
│              数据加载、缓存管理、文件读取                 │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                    数据存储 (Storage)                     │
│                   JSON 数据文件                          │
└─────────────────────────────────────────────────────────┘
```

---

## 三、目录结构设计

### 3.1 项目整体结构

```
2026海关公示/
├── web/                          # Web 应用目录
│   ├── frontend/                 # 前端目录
│   │   ├── src/                 # 源代码
│   │   │   ├── components/      # 组件
│   │   │   ├── hooks/           # 自定义 Hooks
│   │   │   ├── services/        # API 服务
│   │   │   ├── types/           # TypeScript 类型
│   │   │   ├── utils/           # 工具函数
│   │   │   ├── App.tsx          # 主组件
│   │   │   ├── main.tsx         # 入口文件
│   │   │   └── index.css        # 全局样式
│   │   ├── public/               # 静态资源
│   │   ├── dist/                 # 构建输出
│   │   ├── node_modules/         # 依赖
│   │   ├── package.json          # 项目配置
│   │   ├── tsconfig.json         # TS 配置
│   │   ├── vite.config.ts        # Vite 配置
│   │   └── index.html            # HTML 入口
│   └── api.py                    # 后端 API
│
├── customs_pipeline/              # 数据处理目录
│   ├── config.py                 # 配置文件
│   ├── extractor.py              # 数据提取器
│   ├── constants.py              # 常量定义
│   └── processor.py              # 数据处理器
│
├── data/                         # 数据目录
│   └── 2026/
│       ├── raw/                  # 原始数据
│       └── processed/            # 处理后数据
│
├── scripts/                      # 脚本目录
│   ├── data_process.py           # 数据处理脚本
│   ├── coze-preview-build.sh     # 预览构建脚本
│   ├── coze-preview-run.sh       # 预览运行脚本
│   ├── coze-deploy-build.sh      # 部署构建脚本
│   └── coze-deploy-run.sh        # 部署运行脚本
│
├── output/                       # 输出目录
│   └── 2026/
│       └── 海关公务员招录公示.json
│
├── tests/                        # 测试目录
│   ├── unit/                    # 单元测试
│   └── integration/              # 集成测试
│
├── docs/                         # 文档目录
│   ├── API.md                    # API 文档
│   └── DATA_DICTIONARY.md        # 数据字典
│
├── .coze                         # Coze 配置
├── AGENTS.md                     # Agent 记忆
├── TECH_DOC.md                   # 技术文档
├── README.md                     # 项目说明
└── requirements.txt              # Python 依赖
```

### 3.2 前端目录结构

```
frontend/
├── src/
│   ├── components/               # 业务组件
│   │   ├── Header.tsx           # 顶部导航
│   │   ├── Sidebar.tsx          # 侧边栏
│   │   ├── StatsCard.tsx        # 统计卡片
│   │   ├── DataTable.tsx        # 数据表格
│   │   ├── SearchBar.tsx        # 搜索栏
│   │   ├── FilterPanel.tsx      # 筛选面板
│   │   ├── DistrictCard.tsx     # 关区卡片
│   │   ├── SchoolPanel.tsx      # 高校面板
│   │   ├── PositionPanel.tsx    # 职位面板
│   │   └── Modal.tsx            # 弹窗组件
│   │
│   ├── hooks/                   # 自定义 Hooks
│   │   ├── useFetch.ts          # 数据获取
│   │   ├── useDebounce.ts       # 防抖
│   │   └── useLocalStorage.ts   # 本地存储
│   │
│   ├── services/                # API 服务
│   │   └── api.ts               # API 调用
│   │
│   ├── types/                   # 类型定义
│   │   └── index.ts             # 类型导出
│   │
│   ├── utils/                   # 工具函数
│   │   ├── formatters.ts        # 格式化
│   │   └── validators.ts         # 验证
│   │
│   ├── App.tsx                  # 主组件
│   ├── main.tsx                 # 入口文件
│   └── index.css                # 全局样式
│
├── public/                       # 静态资源
│   └── favicon.ico
│
├── package.json
├── tsconfig.json
├── vite.config.ts
└── index.html
```

### 3.3 后端目录结构

```
backend/
├── api.py                        # API 主入口
├── schemas.py                    # 请求/响应模型
│
├── customs_pipeline/             # 数据处理模块
│   ├── __init__.py
│   ├── config.py                 # 配置
│   ├── constants.py              # 常量
│   ├── extractor.py              # 数据提取
│   ├── processor.py              # 数据处理
│   └── models.py                 # 数据模型
│
├── data/                         # 数据存储
│   └── 2026/
│       └── 海关公务员招录公示.json
│
└── requirements.txt
```

---

## 四、功能模块设计

### 4.1 功能列表

| 模块 | 功能点 | 优先级 | 状态 |
|------|--------|--------|------|
| **数据展示** | 统计概览（总人数/关区/高校/职位） | P0 | ✅ |
| **数据展示** | 关区列表展示 | P0 | ✅ |
| **数据展示** | 高校列表展示 | P0 | ✅ |
| **数据展示** | 职位列表展示 | P0 | ✅ |
| **查询功能** | 按姓名搜索 | P1 | ✅ |
| **查询功能** | 按关区筛选 | P1 | ✅ |
| **查询功能** | 按高校类型筛选 | P1 | ✅ |
| **查询功能** | 按职位级别筛选 | P1 | ✅ |
| **详情查看** | 关区详情弹窗 | P1 | ✅ |
| **数据导出** | Excel 导出 | P2 | 🔲 |
| **数据分析** | 柱状图/饼图展示 | P2 | 🔲 |
| **用户交互** | 分页功能 | P1 | ✅ |
| **用户交互** | 排序功能 | P2 | 🔲 |

### 4.2 页面结构

```
┌─────────────────────────────────────────────────────────┐
│  Header: 标题 + Logo + 数据更新时间                      │
├──────────┬──────────────────────────────────────────────┤
│          │                                              │
│ Sidebar  │  Main Content                                │
│          │                                              │
│ - 概览   │  ┌─────────────────────────────────────────┐ │
│ - 关区   │  │  Stats Cards (4个统计卡片)              │ │
│ - 高校   │  └─────────────────────────────────────────┘ │
│ - 职位   │                                              │
│ - 搜索   │  ┌─────────────────────────────────────────┐ │
│          │  │  Filter Panel (筛选面板)                │ │
│          │  └─────────────────────────────────────────┘ │
│          │                                              │
│          │  ┌─────────────────────────────────────────┐ │
│          │  │  Content Area                           │ │
│          │  │  - 数据表格 / 卡片列表                   │ │
│          │  │  - 分页控制                             │ │
│          │  └─────────────────────────────────────────┘ │
│          │                                              │
└──────────┴──────────────────────────────────────────────┘
```

---

## 五、API 接口设计

### 5.1 接口规范

- **协议**：HTTP/HTTPS
- **格式**：JSON
- **编码**：UTF-8
- **版本**：v1

### 5.2 接口列表

| 方法 | 路径 | 描述 | 请求参数 | 响应 |
|------|------|------|---------|------|
| GET | `/api/health` | 健康检查 | - | `{status, data_loaded, record_count}` |
| GET | `/api/overview` | 数据概览 | - | `{total, districts, schools, positions}` |
| GET | `/api/districts` | 关区列表 | `top` | `{districts: [...]}` |
| GET | `/api/district/{name}` | 关区详情 | - | `{关区, 人数, 名单, ...}` |
| GET | `/api/schools` | 高校列表 | `top`, `type` | `{schools: [...]}` |
| GET | `/api/positions` | 职位列表 | `page`, `pageSize`, `keyword`, `district`, `level` | `{positions, total, page, pageSize}` |
| GET | `/api/positions/analysis` | 职位分析 | - | `{level_counts, job_type_counts, ...}` |
| GET | `/api/search` | 搜索 | `keyword` | `{results, total}` |
| GET | `/` | 首页 | - | HTML |

### 5.3 统一响应格式

```typescript
// 成功响应
{
  "data": any,           // 业务数据
  "success": true        // 成功标志
}

// 列表响应
{
  "items": any[],        // 数据列表
  "total": number,       // 总数
  "page": number,        // 当前页
  "pageSize": number     // 每页大小
}

// 错误响应
{
  "error": string,       // 错误信息
  "code": number,        // 错误码
  "success": false       // 失败标志
}
```

---

## 六、数据模型设计

### 6.1 核心数据结构

```typescript
// 公示记录
interface Record {
  姓名: string;           // 姓名
  性别: string;           // 性别
  学历: string;           // 学历
  学位: string;           // 学位
  毕业院校: string;       // 毕业高校
  高校类型: string;       // 985/211/普通
  关区: string;           // 所属海关
  职位: string;           // 职位名称
  职位代码: string;       // 职位代码
  职位级别: string;       // 一级/二级/三级
}

// 关区
interface District {
  关区: string;           // 关区名称
  人数: number;           // 招录人数
  官网: string;           // 官方网站
  职位数: number;         // 职位数量
  高校数: number;         // 来源高校数
}

// 高校
interface School {
  学校: string;            // 高校名称
  类型: string;           // 985/211/普通
  人数: number;           // 录用人数
  岗位: string[];         // 岗位列表
}
```

### 6.2 数据处理流程

```
原始数据 (Excel/PDF)
       │
       ▼
┌─────────────────┐
│  数据提取       │  - 读取 Excel/PDF
│  (extractor.py) │  - 解析表格结构
└─────────────────┘
       │
       ▼
┌─────────────────┐
│  数据清洗       │  - 去除空白
│  (processor.py)  │  - 标准化格式
│                  │  - 补充关区URL
└─────────────────┘
       │
       ▼
┌─────────────────┐
│  数据分类       │  - 识别高校类型
│  (processor.py)  │  - 提取职位级别
└─────────────────┘
       │
       ▼
JSON 数据文件
       │
       ▼
┌─────────────────┐
│  FastAPI 服务   │  - 加载数据
│  (api.py)       │  - 提供查询接口
└─────────────────┘
```

---

## 七、前端组件设计

### 7.1 组件层级

```
App (根组件)
├── Header (顶部导航)
├── Sidebar (侧边栏)
└── MainContent (主内容区)
    ├── StatsCards (统计卡片)
    ├── FilterPanel (筛选面板)
    ├── SearchBar (搜索栏)
    └── TabPanel (标签面板)
        ├── OverviewTab (概览)
        │   └── DistrictGrid (关区网格)
        ├── DistrictsTab (关区)
        │   └── DistrictTable (关区表格)
        ├── SchoolsTab (高校)
        │   └── SchoolTable (高校表格)
        └── PositionsTab (职位)
            └── PositionTable (职位表格)
```

### 7.2 组件职责

| 组件 | 职责 | Props | Events |
|------|------|-------|--------|
| `Header` | 显示标题、时间 | - | - |
| `Sidebar` | 导航菜单 | `activeTab` | `onTabChange` |
| `StatsCard` | 统计数字展示 | `title`, `value`, `icon`, `color` | - |
| `DataTable` | 通用表格 | `columns`, `data`, `loading` | `onRowClick` |
| `SearchBar` | 搜索输入 | `placeholder`, `value` | `onSearch` |
| `FilterPanel` | 筛选控件 | `filters`, `value` | `onChange` |
| `DistrictModal` | 关区详情 | `district`, `visible` | `onClose` |

---

## 八、状态管理设计

### 8.1 本地状态 vs 全局状态

| 状态类型 | 管理方式 | 示例 |
|---------|---------|------|
| 组件状态 | `useState` | 弹窗开关、输入值 |
| 共享状态 | Props Drilling | Tab 切换 |
| 服务器状态 | `useFetch` Hook | API 数据 |

### 8.2 数据获取策略

```typescript
// useFetch Hook 设计
interface FetchState<T> {
  data: T | null;       // 数据
  loading: boolean;      // 加载中
  error: string | null;  // 错误信息
}

function useFetch<T>(url: string): FetchState<T> {
  // 1. 初始状态: loading=true, data=null
  // 2. 请求中: loading=true
  // 3. 成功: loading=false, data=response
  // 4. 失败: loading=false, error=message
}
```

---

## 九、样式系统设计

### 9.1 CSS 变量定义

```css
:root {
  /* 主题色 */
  --primary: #06b6d4;
  --primary-hover: #0891b2;
  --primary-light: #ecfeff;
  
  /* 成功/警告/错误 */
  --success: #10b981;
  --warning: #f59e0b;
  --danger: #ef4444;
  
  /* 文本颜色 */
  --text-primary: #1e293b;
  --text-secondary: #64748b;
  --text-muted: #94a3b8;
  
  /* 背景色 */
  --bg-primary: #ffffff;
  --bg-secondary: #f8fafc;
  --bg-tertiary: #f1f5f9;
  
  /* 边框 */
  --border: #e2e8f0;
  --border-light: #f1f5f9;
  
  /* 圆角 */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  
  /* 阴影 */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --shadow-md: 0 4px 6px rgba(0,0,0,0.07);
  --shadow-lg: 0 10px 15px rgba(0,0,0,0.1);
}
```

### 9.2 响应式断点

```css
/* 手机端 */
@media (max-width: 767px) { }

/* 平板端 */
@media (min-width: 768px) and (max-width: 1023px) { }

/* 桌面端 */
@media (min-width: 1024px) { }
```

---

## 十、项目管理

### 10.1 开发流程

```
需求分析 → 架构设计 → 编码开发 → 代码审查 → 测试验证 → 部署上线
    │            │           │           │           │           │
    ▼            ▼           ▼           ▼           ▼           ▼
  PRD        架构图       组件开发    PR/MR      集成测试     发布版本
```

### 10.2 Git 分支策略

```
main (生产分支)
│
├── develop (开发分支)
│   ├── feature/xxx (功能分支)
│   ├── fix/xxx (修复分支)
│   └── refactor/xxx (重构分支)
│
└── release/v1.0 (发布分支)
```

### 10.3 版本规范

- **主版本号**：架构重大调整
- **次版本号**：新增功能
- **修订号**：Bug 修复

---

## 十一、质量保障

### 11.1 代码质量

| 检查项 | 工具 | 配置 |
|--------|------|------|
| 类型检查 | TypeScript | `tsconfig.json` |
| 代码格式 | Prettier | `.prettierrc` |
| 代码规范 | ESLint | `.eslintrc.js` |
| 提交规范 | CommitLint | `commitlint.config.js` |

### 11.2 测试策略

| 测试类型 | 覆盖范围 | 工具 |
|---------|---------|------|
| 单元测试 | 工具函数、组件逻辑 | Vitest / Jest |
| 集成测试 | API 接口、组件交互 | Playwright |
| E2E 测试 | 完整用户流程 | Playwright |

---

## 十二、部署架构

### 12.1 开发环境

```
本地开发服务器 (localhost:5000)
├── 前端: Vite Dev Server
└── 后端: FastAPI (Python)
```

### 12.2 生产环境

```
用户请求
    │
    ▼
Nginx (端口 80/443)
├── 静态资源 → /frontend/dist
└── API 请求 → :5000/FastAPI
                   │
                   ▼
               JSON 数据文件
```

### 12.3 构建脚本

```bash
# 预览构建
pnpm build  # 前端构建
python api.py  # 启动服务

# 部署构建
pnpm build && docker build .
```

---

## 十三、后续规划

### 13.1 功能增强

- [ ] Excel/CSV 数据导出
- [ ] 数据可视化图表
- [ ] 用户收藏功能
- [ ] 数据对比功能
- [ ] 移动端适配优化

### 13.2 技术升级

- [ ] 引入状态管理 (Zustand/Redux)
- [ ] 添加单元测试
- [ ] 引入数据库 (SQLite/PostgreSQL)
- [ ] 添加缓存层 (Redis)
- [ ] 实现 SSR (Next.js)

---

## 十四、参考资源

- [前后端分离架构设计最佳实践](https://juejin.cn/post/7329033690204438578)
- [软件工程项目设计文档模板](https://wenku.csdn.net/answer/4uj65vqatb)
- [分层架构详解](https://blog.csdn.net/ZxqSoftWare/article/details/149742242)
- [前端项目技术文档生成器](https://juejin.cn/post/7576218673049452595)
