import React, { useState, useEffect, useCallback, useRef, Component, ReactNode } from 'react'
import type { FetchState, TabType, Overview, DistrictsResponse, DistrictDetail, PositionAnalysis, SearchResult } from './types'

// =============================================================================
// Error Boundary
// =============================================================================

interface ErrorBoundaryProps {
  children: ReactNode
  fallback?: ReactNode
}

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('React Error:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div style={{ textAlign: 'center', padding: '48px', color: '#ef4444' }}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>⚠️</div>
          <p style={{ marginBottom: '16px', color: '#64748b' }}>渲染出错: {this.state.error?.message}</p>
          <button 
            onClick={() => this.setState({ hasError: false, error: null })} 
            className="btn-primary"
          >
            重试
          </button>
        </div>
      )
    }
    return this.props.children
  }
}

// =============================================================================
// Constants
// =============================================================================

const API_BASE = '/api'



// =============================================================================
// Hooks
// =============================================================================

function useFetch<T>(url: string | null): FetchState<T> {
  const [state, setState] = useState<FetchState<T>>({ data: null, loading: !!url, error: null })

  useEffect(() => {
    if (!url) return
    let cancelled = false
    setState(s => ({ ...s, loading: true, error: null }))

    fetch(url)
      .then(r => r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`)))
      .then(d => { if (!cancelled) setState({ data: d, loading: false, error: null }) })
      .catch(e => { if (!cancelled) setState({ data: null, loading: false, error: e.message }) })

    return () => { cancelled = true }
  }, [url])

  return state
}

// =============================================================================
// Components
// =============================================================================

function ErrorMessage({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div style={{ textAlign: 'center', padding: '48px', color: '#ef4444' }}>
      <div style={{ fontSize: '48px', marginBottom: '16px' }}>⚠️</div>
      <p style={{ marginBottom: '16px', color: '#64748b' }}>{message}</p>
      <button onClick={onRetry} className="btn-primary">
        重新加载
      </button>
    </div>
  )
}

function LoadingSpinner() {
  return (
    <div className="loading">
      <div className="loading-spinner" />
      <p>加载中...</p>
    </div>
  )
}

function StatCard({ label, value, icon, colorClass }: { label: string; value: number | string; icon: string; colorClass: string }) {
  return (
    <div className={`stat-card ${colorClass} fade-in-up`}>
      <div className="stat-icon">{icon}</div>
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  )
}

// 简单的条形图组件 - 使用纯 HTML/CSS 避免 ECharts 兼容性问题
function SimpleBarChart({ data, height = '280px', title = '' }: { data: Array<{ name: string; value: number }> | null | undefined; height?: string; title?: string }) {
  if (!data || !Array.isArray(data) || data.length === 0) {
    return (
      <div className="card" style={{ height }}>
        <div className="card-header">{title}</div>
        <div className="card-content" style={{ height: 'calc(100% - 50px)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b' }}>暂无数据</div>
      </div>
    )
  }
  
  const maxValue = Math.max(...data.map(d => d.value))
  const displayData = data.slice(0, 15) // 最多显示15条
  
  return (
    <div className="card" style={{ height }}>
      <div className="card-header">{title}</div>
      <div className="card-content" style={{ height: 'calc(100% - 50px)', overflow: 'auto', padding: '12px' }}>
        {displayData.map((item, idx) => (
          <div key={idx} style={{ display: 'flex', alignItems: 'center', marginBottom: '10px' }}>
            <div style={{ width: '100px', fontSize: '12px', color: '#475569', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flexShrink: 0 }}>
              {item.name}
            </div>
            <div style={{ flex: 1, height: '22px', background: '#f1f5f9', borderRadius: '4px', margin: '0 10px', overflow: 'hidden' }}>
              <div style={{ 
                width: `${(item.value / maxValue) * 100}%`, 
                height: '100%', 
                background: 'linear-gradient(90deg, #0ea5e9, #38bdf8)',
                borderRadius: '4px',
                transition: 'width 0.5s ease',
                display: 'flex',
                alignItems: 'center',
                paddingLeft: '8px',
                color: 'white',
                fontSize: '11px',
                fontWeight: 500,
                minWidth: '30px'
              }}>
                {item.value}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// 简单的饼图组件 - 使用纯 HTML/CSS
function SimplePieChart({ data, height = '220px', title = '' }: { data: Array<{ name: string; value: number }> | null | undefined; height?: string; title?: string }) {
  if (!data || !Array.isArray(data) || data.length === 0) {
    return (
      <div className="card" style={{ height }}>
        <div className="card-header">{title}</div>
        <div className="card-content" style={{ height: 'calc(100% - 50px)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b' }}>暂无数据</div>
      </div>
    )
  }
  
  const total = data.reduce((sum, d) => sum + d.value, 0)
  const colors = ['#0ea5e9', '#38bdf8', '#7dd3fc', '#f472b6', '#a78bfa', '#fb923c', '#4ade80', '#facc15', '#94a3b8', '#fb7185']
  const displayData = data.slice(0, 10)
  
  return (
    <div className="card" style={{ height }}>
      <div className="card-header">{title}</div>
      <div className="card-content" style={{ height: 'calc(100% - 50px)', display: 'flex', overflow: 'auto', padding: '12px' }}>
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: '8px' }}>
          {displayData.map((item, idx) => (
            <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{ width: '12px', height: '12px', borderRadius: '2px', background: colors[idx % colors.length], flexShrink: 0 }} />
              <div style={{ fontSize: '12px', color: '#475569', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {item.name}
              </div>
              <div style={{ fontSize: '12px', color: '#64748b', minWidth: '40px', textAlign: 'right' }}>
                {item.value}
              </div>
              <div style={{ fontSize: '11px', color: '#94a3b8', minWidth: '40px', textAlign: 'right' }}>
                {((item.value / total) * 100).toFixed(1)}%
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function highlightText(text: string | undefined, keywords: string): React.ReactNode {
  if (!text || !keywords.trim()) return text ?? '-'
  const parts = keywords.trim().split(/\s+/).filter(Boolean)
  if (parts.length === 1) {
    const idx = text.toLowerCase().indexOf(parts[0].toLowerCase())
    return idx >= 0 ? <>{text.slice(0, idx)}<mark className="highlight">{text.slice(idx, idx + parts[0].length)}</mark>{text.slice(idx + parts[0].length)}</> : text
  }
  let result: React.ReactNode = text
  const intervals: [number, number][] = []
  for (const kw of parts) {
    let pos = 0
    while (pos < result.toString().length) {
      const i = result.toString().toLowerCase().indexOf(kw.toLowerCase(), pos)
      if (i < 0) break
      intervals.push([i, i + kw.length])
      pos = i + 1
    }
  }
  if (!intervals.length) return text
  intervals.sort((a, b) => a[0] - b[0])
  const merged: [number, number][] = []
  for (const [s, e] of intervals) {
    if (!merged.length || s > merged[merged.length - 1][1]) merged.push([s, e])
    else merged[merged.length - 1][1] = Math.max(merged[merged.length - 1][1], e)
  }
  const nodes: React.ReactNode[] = []
  let last = 0
  for (const [s, e] of merged) {
    if (s > last) nodes.push(result.toString().slice(last, s))
    nodes.push(<mark key={s} className="highlight">{result.toString().slice(s, e)}</mark>)
    last = e
  }
  if (last < result.toString().length) nodes.push(result.toString().slice(last))
  return <>{nodes}</>
}

function SearchPanel({ onSearch, filters, onFilterChange }: { onSearch: () => void; filters: Record<string, string>; onFilterChange: (k: string, v: string) => void }) {
  return (
    <div>
      <div className="filter-row">
        {[['name', '姓名'], ['school', '毕业院校'], ['position', '职位']].map(([k, label]) => (
          <input 
            key={k} 
            type="text" 
            placeholder={`按${label}搜索（空格分隔多关键字）`} 
            value={filters[k]} 
            onChange={e => onFilterChange(k, e.target.value)}
            className="filter-input"
          />
        ))}
      </div>
      <div className="filter-row">
        <input 
          type="text" 
          placeholder="关区" 
          value={filters.district} 
          onChange={e => onFilterChange('district', e.target.value)}
          className="filter-input"
        />
        <input 
          type="text" 
          placeholder="学历" 
          value={filters.education} 
          onChange={e => onFilterChange('education', e.target.value)}
          className="filter-input"
        />
        <select 
          value={filters.gender} 
          onChange={e => onFilterChange('gender', e.target.value)}
          className="filter-select"
        >
          <option value="">性别</option>
          <option value="男">男</option>
          <option value="女">女</option>
        </select>
        <button onClick={onSearch} className="btn-primary">🔍 查询</button>
      </div>
    </div>
  )
}

function DistrictDetailModal({ district, data, loading, error, onClose, onRetry }: { district: string; data: DistrictDetail | null; loading: boolean; error: string | null; onClose: () => void; onRetry: () => void }) {
  if (!district) return null

  // 安全提取数据
  const safeData = data ?? {
    total: 0, male: 0, female: 0,
    education: [], gender: [], top_positions: [], top_schools: []
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>🏛️ {district}</h3>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        {loading && <LoadingSpinner />}
        {error && <ErrorMessage message={error} onRetry={onRetry} />}

        {!loading && !error && (
          <>
            <div className="modal-stats">
              <div className="modal-stat">
                <div className="modal-stat-value">{safeData.total}</div>
                <div className="modal-stat-label">总人数</div>
              </div>
              <div className="modal-stat">
                <div className="modal-stat-value" style={{ color: '#ec4899' }}>{safeData.female}</div>
                <div className="modal-stat-label">女性</div>
              </div>
              <div className="modal-stat">
                <div className="modal-stat-value" style={{ color: '#10b981' }}>{safeData.male}</div>
                <div className="modal-stat-label">男性</div>
              </div>
            </div>

            <div className="modal-grid">
              <div className="modal-section">
                <h4>学历构成</h4>
                {safeData.education.length > 0 ? (
                  <SimplePieChart data={safeData.education} height="180px" title="学历分布" />
                ) : (
                  <div className="no-data">暂无数据</div>
                )}
              </div>
              <div className="modal-section">
                <h4>性别分布</h4>
                {safeData.gender.length > 0 ? (
                  <SimplePieChart data={safeData.gender} height="180px" title="性别分布" />
                ) : (
                  <div className="no-data">暂无数据</div>
                )}
              </div>
            </div>

            <div className="modal-grid">
              <div className="modal-section">
                <h4>职位 Top5</h4>
                {safeData.top_positions.length > 0 ? (
                  <div className="top-list">
                    {safeData.top_positions.map((p, i) => (
                      <div key={i} className="top-item">
                        <span className="top-rank">{i + 1}</span>
                        <span className="top-text">{p.name}</span>
                        <span className="top-count">{p.count}人</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="no-data">暂无数据</div>
                )}
              </div>
              <div className="modal-section">
                <h4>毕业院校 Top5</h4>
                {safeData.top_schools.length > 0 ? (
                  <div className="top-list">
                    {safeData.top_schools.map((s, i) => (
                      <div key={i} className="top-item">
                        <span className="top-rank">{i + 1}</span>
                        <span className="top-text">{s.毕业院校}</span>
                        <span className="top-count">{s.人数}人</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="no-data">暂无数据</div>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

function SchoolPanel({ data, loading, error, onRetry }: { data: any; loading: boolean; error: string | null; onRetry: () => void }) {
  if (loading) return <LoadingSpinner />
  if (error) return <ErrorMessage message={error} onRetry={onRetry} />
  if (!data || !Array.isArray(data) || data.length === 0) return <p style={{ textAlign: 'center', color: '#94a3b8', padding: '48px' }}>暂无数据</p>

  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            <th style={{ width: '80px' }}>排名</th>
            <th>毕业院校</th>
            <th className="right" style={{ width: '120px' }}>录用人数</th>
          </tr>
        </thead>
        <tbody>
          {data.map((s: any, i: number) => (
            <tr key={i}>
              <td>
                <span className={i < 3 ? 'rank-gold' : 'rank-default'}>
                  {i + 1}
                </span>
              </td>
              <td className="fw500">{s.毕业院校}</td>
              <td className="right fw600" style={{ color: '#0ea5e9' }}>{s.人数}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function PositionPanel({ data, loading, error, onRetry }: { data: PositionAnalysis | null; loading: boolean; error: string | null; onRetry: () => void }) {
  if (loading) return <LoadingSpinner />
  if (error) return <ErrorMessage message={error} onRetry={onRetry} />

  // 安全提取数据
  const safeData = data ?? { job_type_counts: {}, level_counts: {}, sub_district_counts: {}, total_positions: 0 }
  const jobTypeData = Object.entries(safeData.job_type_counts).map(([name, value]) => ({ name, value })).sort((a, b) => b.value - a.value).slice(0, 10)
  const levelData = Object.entries(safeData.level_counts).map(([name, value]) => ({ name, value })).sort((a, b) => b.value - a.value)
  const subDistrictData = Object.entries(safeData.sub_district_counts).map(([name, value]) => ({ name, value })).sort((a, b) => b.value - a.value).slice(0, 15)

  return (
    <div>
      <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)', marginBottom: '24px' }}>
        <StatCard label="职位类型数" value={safeData.total_positions} icon="📋" colorClass="blue" />
        <StatCard label="一级主办" value={safeData.level_counts['一级'] || 0} icon="🏅" colorClass="orange" />
        <StatCard label="二级主办" value={safeData.level_counts['二级'] || 0} icon="🥈" colorClass="green" />
      </div>

      <div className="two-col" style={{ marginBottom: '20px' }}>
        <div className="card" style={{ marginBottom: 0 }}>
          <div className="card-title">
            <span className="card-title-icon">📊</span>
            职位类型分布 Top10
          </div>
          <SimpleBarChart data={jobTypeData} height="280px" title="职位类型分布" />
        </div>
        <div className="card" style={{ marginBottom: 0 }}>
          <div className="card-title">
            <span className="card-title-icon">📈</span>
            职位层级分布
          </div>
          <SimplePieChart data={levelData} height="280px" title="级别分布" />
        </div>
      </div>

      <div className="card">
        <div className="card-title">
          <span className="card-title-icon">🗺️</span>
          隶属关区分布 Top15
        </div>
        <SimpleBarChart data={subDistrictData} height="350px" title="子关区分布" />
      </div>
    </div>
  )
}

// =============================================================================
// Navigation Icons
// =============================================================================

const NAV_ITEMS: { id: TabType; label: string; icon: string }[] = [
  { id: 'search', label: '录用查询', icon: '🔍' },
  { id: 'districts', label: '关区数据', icon: '🏛️' },
  { id: 'schools', label: '毕业院校', icon: '🎓' },
  { id: 'positions', label: '职位分析', icon: '📋' },
]

// =============================================================================
// Main App
// =============================================================================

export default function App() {
  return (
    <ErrorBoundary>
      <AppContent />
    </ErrorBoundary>
  )
}

function AppContent() {
  const [tab, setTab] = useState<TabType>('search')
  const [filters, setFilters] = useState({ name: '', school: '', position: '', district: '', education: '', gender: '' })
  const [searchKey, setSearchKey] = useState(0)
  const [isReady, setIsReady] = useState(false)

  const overviewState = useFetch<Overview>(`${API_BASE}/overview`)
  const districtsState = useFetch<DistrictsResponse>(`${API_BASE}/districts`)
  const schoolsState = useFetch<any[]>(`${API_BASE}/schools?top=50`)
  const positionsState = useFetch<PositionAnalysis>(`${API_BASE}/positions/analysis`)

  // 等待所有主要数据加载完成
  useEffect(() => {
    if (overviewState.data && districtsState.data && schoolsState.data && positionsState.data) {
      const timer = setTimeout(() => setIsReady(true), 100)
      return () => clearTimeout(timer)
    }
  }, [overviewState.data, districtsState.data, schoolsState.data, positionsState.data])

  const searchParams = new URLSearchParams()
  Object.entries(filters).forEach(([k, v]) => v && searchParams.set(k, v))
  searchParams.set('page', '1')
  searchParams.set('page_size', '20')

  const searchState = useFetch<SearchResult>(tab === 'search' ? `${API_BASE}/search?${searchParams}` : null)

  const [detailDistrict, setDetailDistrict] = useState('')
  const detailParams = detailDistrict ? `${API_BASE}/district/${encodeURIComponent(detailDistrict)}` : null
  const detailState = useFetch<DistrictDetail>(detailParams)

  // 安全访问状态
  const overview = overviewState?.data
  const districts = districtsState?.data
  const schools = schoolsState?.data
  const positions = positionsState?.data
  const search = searchState?.data
  const detailData = detailState?.data
  const detailLoading = detailState?.loading ?? false
  const detailError = detailState?.error

  const districtsData = districts?.districts ?? []
  const searchItems = search?.items ?? []
  const searchTotal = search?.total ?? 0
  const searchLoading = searchState?.loading ?? false
  const searchError = searchState?.error

  const handleSearch = useCallback(() => { setSearchKey(k => k + 1); setTab('search') }, [])
  const handleFilterChange = useCallback((k: string, v: string) => setFilters(f => ({ ...f, [k]: v })), [])
  const handleDistrictClick = useCallback((d: string) => { setDetailDistrict(d) }, [])
  const handleModalRetry = useCallback(() => { setDetailDistrict(''); setTimeout(() => setDetailDistrict(detailDistrict), 50) }, [detailDistrict])

  // 初始加载时显示 loading
  if (!isReady) {
    return (
      <div className="app">
        <LoadingSpinner />
      </div>
    )
  }

  return (
    <div className="app">
      {/* Desktop Sidebar */}
      <aside className="sidebar-desktop">
        <div className="sidebar-brand">
          <div className="sidebar-icon">🏛️</div>
          <div className="sidebar-title">海关公示数据分析</div>
          <div className="sidebar-sub">2026年度公务员录用</div>
        </div>
        <nav className="sidebar-nav">
          <div className="nav-section">
            <div className="nav-section-title">数据查询</div>
            {NAV_ITEMS.map(item => (
              <button
                key={item.id}
                className={`nav-item ${tab === item.id ? 'active' : ''}`}
                onClick={() => setTab(item.id)}
              >
                <span className="nav-icon">{item.icon}</span>
                {item.label}
              </button>
            ))}
          </div>
        </nav>
      </aside>

      {/* Tablet Navigation */}
      <nav className="nav-tablet">
        <div className="nav-tablet-brand">
          <div className="nav-tablet-icon">🏛️</div>
          <div className="nav-tablet-title">海关公示数据分析</div>
        </div>
        <div className="nav-tablet-scroll">
          {NAV_ITEMS.map(item => (
            <button
              key={item.id}
              className={`nav-tablet-item ${tab === item.id ? 'active' : ''}`}
              onClick={() => setTab(item.id)}
            >
              {item.icon} {item.label}
            </button>
          ))}
        </div>
      </nav>

      {/* Mobile Header */}
      <header className="header-mobile">
        <div>
          <div className="header-mobile-title">海关公示数据分析</div>
          <div className="header-mobile-sub">2026年度公务员录用</div>
        </div>
        <div className="header-mobile-icon">🏛️</div>
      </header>

      {/* Mobile Bottom Navigation */}
      <nav className="nav-mobile">
        {NAV_ITEMS.map(item => (
          <button
            key={item.id}
            className={`nav-mobile-item ${tab === item.id ? 'active' : ''}`}
            onClick={() => setTab(item.id)}
          >
            <span className="nav-mobile-icon">{item.icon}</span>
            <span className="nav-mobile-label">{item.label}</span>
          </button>
        ))}
      </nav>

      {/* Main Content */}
      <main className="main-content">
        <div className="page-header">
          <h1>{NAV_ITEMS.find(i => i.id === tab)?.label || '录用查询'}</h1>
          <p>2026年海关公务员考试录用名单数据分析平台</p>
        </div>

        {/* Stats Overview */}
        {overview && overview.total > 0 && (
          <div className="stats-grid">
            <StatCard 
              label="录用总数" 
              value={overview.total.toLocaleString()} 
              icon="👥" 
              colorClass="blue" 
            />
            <StatCard 
              label="关区数" 
              value={overview.districts} 
              icon="🏛️" 
              colorClass="green" 
            />
            <StatCard 
              label="院校数" 
              value={overview.schools} 
              icon="🎓" 
              colorClass="purple" 
            />
            <StatCard 
              label="职位数" 
              value={overview.positions} 
              icon="📋" 
              colorClass="orange" 
            />
          </div>
        )}

        {/* Tab Content */}
        <div className="card">
          {tab === 'search' && (
            <>
              <div className="card-header">
                <div className="card-title">
                  <span className="card-title-icon">🔍</span>
                  录用人员查询
                </div>
              </div>
              <SearchPanel onSearch={handleSearch} filters={filters} onFilterChange={handleFilterChange} />
              
              {searchLoading && <LoadingSpinner />}
              {searchError && <ErrorMessage message={searchError} onRetry={handleSearch} />}
              
              {search?.data && (
                <>
                  <p style={{ color: '#64748b', marginBottom: '16px' }}>
                    共找到 <strong style={{ color: '#0ea5e9' }}>{searchTotal.toLocaleString()}</strong> 条记录
                  </p>
                  <div className="table-wrap">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>姓名</th>
                          <th style={{ width: '60px' }}>性别</th>
                          <th>毕业院校</th>
                          <th style={{ width: '80px' }}>学历</th>
                          <th>关区</th>
                          <th>职位</th>
                          <th>隶属海关</th>
                        </tr>
                      </thead>
                      <tbody>
                        {searchItems.map((item, i) => (
                          <tr key={i}>
                            <td className="fw500">{highlightText(item.姓名, filters.name)}</td>
                            <td className="center">{item.性别 ?? '-'}</td>
                            <td>{highlightText(item.毕业院校, filters.school)}</td>
                            <td>{item.学历 ?? '-'}</td>
                            <td>
                              <span 
                                onClick={() => item.关区 && handleDistrictClick(item.关区)} 
                                className="link"
                              >
                                {item.关区 ?? '-'}
                              </span>
                            </td>
                            <td>{highlightText(item.职位, filters.position)}</td>
                            <td>{item.隶属海关 ?? '-'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              )}
            </>
          )}

          {tab === 'districts' && (
            <>
              <div className="card-header">
                <div className="card-title">
                  <span className="card-title-icon">🏛️</span>
                  各关区录用情况
                </div>
              </div>
              {districts.loading && <LoadingSpinner />}
              {districts.error && <ErrorMessage message={districts.error} onRetry={() => {}} />}
              {districts?.data && (
                <div className="table-wrap">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>关区</th>
                        <th className="right" style={{ width: '100px' }}>人数</th>
                        <th className="center" style={{ width: '100px' }}>官网</th>
                      </tr>
                    </thead>
                    <tbody>
                      {districtsData.map((d, i) => (
                        <tr key={i}>
                          <td>
                            <span onClick={() => handleDistrictClick(d.关区)} className="link">
                              {d.关区}
                            </span>
                          </td>
                          <td className="right fw600">{d.人数.toLocaleString()}</td>
                          <td className="center">
                            {d.官网 && (
                              <a 
                                href={d.官网} 
                                target="_blank" 
                                rel="noopener noreferrer" 
                                className="external-link"
                              >
                                访问 →
                              </a>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}

          {tab === 'schools' && (
            <>
              <div className="card-header">
                <div className="card-title">
                  <span className="card-title-icon">🎓</span>
                  毕业院校分布 Top50
                </div>
              </div>
              <SchoolPanel data={schools?.data} loading={schoolsState?.loading ?? false} error={schoolsState?.error} onRetry={() => {}} />
            </>
          )}

          {tab === 'positions' && (
            <>
              <div className="card-header">
                <div className="card-title">
                  <span className="card-title-icon">📊</span>
                  职位分析
                </div>
              </div>
              <PositionPanel data={positions?.data} loading={positionsState?.loading ?? false} error={positionsState?.error} onRetry={() => {}} />
            </>
          )}
        </div>
      </main>

      {/* District Detail Modal */}
      <DistrictDetailModal 
        district={detailDistrict} 
        data={detailData} 
        loading={detailLoading} 
        error={detailError} 
        onClose={() => setDetailDistrict('')} 
        onRetry={handleModalRetry} 
      />
    </div>
  )
}
