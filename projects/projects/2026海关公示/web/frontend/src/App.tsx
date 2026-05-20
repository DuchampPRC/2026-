import React, { useState, useEffect, useCallback, useRef } from 'react'
import * as echarts from 'echarts'
import type { FetchState, TabType, Overview, DistrictsResponse, DistrictDetail, PositionAnalysis, SearchResult } from './types'

// =============================================================================
// Constants
// =============================================================================

const API_BASE = '/api'

const COLORS = {
  primary: '#0ea5e9',
  success: '#10b981',
  warning: '#f59e0b',
  danger: '#ef4444',
  purple: '#8b5cf6',
  pink: '#ec4899',
  gradient: { blue: ['#0ea5e9', '#3b82f6'], green: ['#10b981', '#34d399'], purple: ['#8b5cf6', '#a78bfa'] },
}

const CHART_COLORS = ['#0ea5e9', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16']

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
    <div style={{ textAlign: 'center', padding: '40px', color: COLORS.danger }}>
      <p style={{ marginBottom: '16px' }}>加载失败: {message}</p>
      <button onClick={onRetry} style={{ padding: '8px 24px', background: COLORS.primary, color: '#fff', border: 'none', borderRadius: '8px', cursor: 'pointer' }}>
        重试
      </button>
    </div>
  )
}

function LoadingSpinner() {
  return (
    <div style={{ textAlign: 'center', padding: '60px' }}>
      <div style={{ width: '40px', height: '40px', border: '4px solid #e5e7eb', borderTopColor: COLORS.primary, borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '0 auto' }} />
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}

function StatCard({ label, value, color }: { label: string; value: number | string; color: string }) {
  return (
    <div style={{ background: `linear-gradient(135deg, ${color}, ${color}dd)`, borderRadius: '12px', padding: '20px', textAlign: 'center', color: '#fff', flex: 1 }}>
      <div style={{ fontSize: '28px', fontWeight: 'bold' }}>{value}</div>
      <div style={{ fontSize: '14px', opacity: 0.9 }}>{label}</div>
    </div>
  )
}

function EChartsPie({ data, height = '250px' }: { data: Array<{ name: string; value: number }>; height?: string }) {
  const chartRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!chartRef.current) return
    const chart = echarts.init(chartRef.current)
    chart.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      series: [{ type: 'pie', radius: ['40%', '70%'], data, itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 }, label: { show: false } }],
      color: CHART_COLORS,
    })
    const observer = new ResizeObserver(() => chart.resize())
    observer.observe(chartRef.current)
    return () => { observer.disconnect(); chart.dispose() }
  }, [data])

  return <div ref={chartRef} style={{ width: '100%', height }} />
}

function EChartsBar({ data, height = '300px' }: { data: Array<{ name: string; value: number }>; height?: string }) {
  const chartRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!chartRef.current) return
    const chart = echarts.init(chartRef.current)
    chart.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: { type: 'value' },
      yAxis: { type: 'category', data: data.map(d => d.name).reverse(), axisLabel: { fontSize: 12 } },
      series: [{ type: 'bar', data: data.map(d => d.value).reverse(), itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: COLORS.primary }, { offset: 1, color: '#3b82f6' }]), borderRadius: [0, 4, 4, 0] }, barWidth: '60%' }],
    })
    const observer = new ResizeObserver(() => chart.resize())
    observer.observe(chartRef.current)
    return () => { observer.disconnect(); chart.dispose() }
  }, [data])

  return <div ref={chartRef} style={{ width: '100%', height }} />
}

function highlightText(text: string | undefined, keywords: string): React.ReactNode {
  if (!text || !keywords.trim()) return text ?? '-'
  const parts = keywords.trim().split(/\s+/).filter(Boolean)
  if (parts.length === 1) {
    const idx = text.toLowerCase().indexOf(parts[0].toLowerCase())
    return idx >= 0 ? <>{text.slice(0, idx)}<mark style={{ background: '#fef08a', padding: '0 2px' }}>{text.slice(idx, idx + parts[0].length)}</mark>{text.slice(idx + parts[0].length)}</> : text
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
    nodes.push(<mark key={s} style={{ background: '#fef08a', padding: '0 2px' }}>{result.toString().slice(s, e)}</mark>)
    last = e
  }
  if (last < result.toString().length) nodes.push(result.toString().slice(last))
  return <>{nodes}</>
}

function SearchPanel({ onSearch, filters, onFilterChange, onDetail }: { onSearch: () => void; filters: Record<string, string>; onFilterChange: (k: string, v: string) => void; onDetail: (district: string) => void }) {
  return (
    <div style={{ marginBottom: '24px' }}>
      <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginBottom: '12px' }}>
        {[['name', '姓名'], ['school', '毕业院校'], ['position', '职位']].map(([k, label]) => (
          <input key={k} type="text" placeholder={`${label}（空格分隔多关键字）`} value={filters[k]} onChange={e => onFilterChange(k, e.target.value)} style={{ flex: '1 1 200px', padding: '10px 14px', border: '1px solid #e5e7eb', borderRadius: '8px', fontSize: '14px' }} />
        ))}
      </div>
      <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
        {[['district', '关区'], ['education', '学历']].map(([k, label]) => (
          <input key={k} type="text" placeholder={label} value={filters[k]} onChange={e => onFilterChange(k, e.target.value)} style={{ width: '150px', padding: '10px 14px', border: '1px solid #e5e7eb', borderRadius: '8px', fontSize: '14px' }} />
        ))}
        <select value={filters.gender} onChange={e => onFilterChange('gender', e.target.value)} style={{ padding: '10px 14px', border: '1px solid #e5e7eb', borderRadius: '8px', fontSize: '14px', minWidth: '100px' }}>
          <option value="">性别</option>
          <option value="男">男</option>
          <option value="女">女</option>
        </select>
        <button onClick={onSearch} style={{ padding: '10px 28px', background: COLORS.primary, color: '#fff', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: '500' }}>查询</button>
      </div>
    </div>
  )
}

function DistrictDetailModal({ district, data, loading, error, onClose, onRetry }: { district: string; data: DistrictDetail | null; loading: boolean; error: string | null; onClose: () => void; onRetry: () => void }) {
  if (!district) return null

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, padding: '20px' }} onClick={onClose}>
      <div style={{ background: '#fff', borderRadius: '16px', width: '100%', maxWidth: '700px', maxHeight: '85vh', overflow: 'auto', padding: '24px' }} onClick={e => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h2 style={{ margin: 0, fontSize: '20px' }}>{district}</h2>
          <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: '24px', cursor: 'pointer', color: '#6b7280' }}>×</button>
        </div>

        {loading && <LoadingSpinner />}
        {error && <ErrorMessage message={error} onRetry={onRetry} />}

        {data && (
          <>
            <div style={{ display: 'flex', gap: '12px', marginBottom: '24px' }}>
              <StatCard label="总人数" value={data.total} color={COLORS.primary} />
              <StatCard label="女性" value={data.female} color={COLORS.pink} />
              <StatCard label="男性" value={data.male} color={COLORS.success} />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px', marginBottom: '24px' }}>
              <div style={{ background: '#f9fafb', borderRadius: '12px', padding: '16px' }}>
                <h4 style={{ margin: '0 0 12px', fontSize: '14px', color: '#6b7280' }}>学历构成</h4>
                <EChartsPie data={data.education} height="200px" />
              </div>
              <div style={{ background: '#f9fafb', borderRadius: '12px', padding: '16px' }}>
                <h4 style={{ margin: '0 0 12px', fontSize: '14px', color: '#6b7280' }}>性别分布</h4>
                <EChartsPie data={data.gender} height="200px" />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '16px' }}>
              <div>
                <h4 style={{ margin: '0 0 12px', fontSize: '14px', color: '#6b7280' }}>职位 Top5</h4>
                {data.top_positions.map((p, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '8px 0', borderBottom: '1px solid #f3f4f6' }}>
                    <span style={{ width: '22px', height: '22px', borderRadius: '6px', background: i < 3 ? '#fbbf24' : COLORS.primary, color: '#fff', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: '12px', fontWeight: 'bold' }}>{i + 1}</span>
                    <span style={{ flex: 1, fontSize: '13px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.name}</span>
                    <span style={{ color: '#6b7280', fontSize: '13px' }}>{p.count}人</span>
                  </div>
                ))}
              </div>
              <div>
                <h4 style={{ margin: '0 0 12px', fontSize: '14px', color: '#6b7280' }}>毕业院校 Top5</h4>
                {data.top_schools.map((s, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '8px 0', borderBottom: '1px solid #f3f4f6' }}>
                    <span style={{ width: '22px', height: '22px', borderRadius: '6px', background: i < 3 ? '#fbbf24' : COLORS.success, color: '#fff', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: '12px', fontWeight: 'bold' }}>{i + 1}</span>
                    <span style={{ flex: 1, fontSize: '13px' }}>{s.毕业院校}</span>
                    <span style={{ color: '#6b7280', fontSize: '13px' }}>{s.人数}人</span>
                  </div>
                ))}
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
  if (!data?.length) return <p style={{ textAlign: 'center', color: '#6b7280' }}>暂无数据</p>

  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ background: '#f9fafb' }}>
            <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', borderBottom: '2px solid #e5e7eb' }}>排名</th>
            <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', borderBottom: '2px solid #e5e7eb' }}>毕业院校</th>
            <th style={{ padding: '12px', textAlign: 'right', fontWeight: '600', borderBottom: '2px solid #e5e7eb' }}>录用人数</th>
          </tr>
        </thead>
        <tbody>
          {data.map((s: any, i: number) => (
            <tr key={i} style={{ borderBottom: '1px solid #f3f4f6' }}>
              <td style={{ padding: '12px' }}>
                <span style={{ width: '24px', height: '24px', borderRadius: '6px', background: i < 3 ? '#fbbf24' : COLORS.primary, color: '#fff', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: '12px', fontWeight: 'bold' }}>{i + 1}</span>
              </td>
              <td style={{ padding: '12px' }}>{s.毕业院校}</td>
              <td style={{ padding: '12px', textAlign: 'right', fontWeight: '500', color: COLORS.primary }}>{s.人数}</td>
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
  if (!data) return null

  const jobTypeData = Object.entries(data.job_type_counts).map(([name, value]) => ({ name, value })).sort((a, b) => b.value - a.value).slice(0, 10)
  const levelData = Object.entries(data.level_counts).map(([name, value]) => ({ name, value })).sort((a, b) => b.value - a.value)
  const subDistrictData = Object.entries(data.sub_district_counts).map(([name, value]) => ({ name, value })).sort((a, b) => b.value - a.value).slice(0, 20)

  return (
    <div>
      <div style={{ display: 'flex', gap: '16px', marginBottom: '24px' }}>
        <StatCard label="职位类型数" value={data.total_positions} color={COLORS.purple} />
        <StatCard label="一级主办" value={data.level_counts['一级'] || 0} color={COLORS.warning} />
        <StatCard label="二级主办" value={data.level_counts['二级'] || 0} color={COLORS.success} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '20px', marginBottom: '24px' }}>
        <div style={{ background: '#f9fafb', borderRadius: '12px', padding: '16px' }}>
          <h4 style={{ margin: '0 0 12px', fontSize: '14px', color: '#6b7280' }}>职位类型分布 Top10</h4>
          <EChartsBar data={jobTypeData} height="300px" />
        </div>
        <div style={{ background: '#f9fafb', borderRadius: '12px', padding: '16px' }}>
          <h4 style={{ margin: '0 0 12px', fontSize: '14px', color: '#6b7280' }}>职位层级分布</h4>
          <EChartsPie data={levelData} height="300px" />
        </div>
      </div>

      <div style={{ background: '#f9fafb', borderRadius: '12px', padding: '16px' }}>
        <h4 style={{ margin: '0 0 12px', fontSize: '14px', color: '#6b7280' }}>隶属关区分布 Top20</h4>
        <EChartsBar data={subDistrictData} height="400px" />
      </div>
    </div>
  )
}

// =============================================================================
// Main App
// =============================================================================

export default function App() {
  const [tab, setTab] = useState<TabType>('search')
  const [filters, setFilters] = useState({ name: '', school: '', position: '', district: '', education: '', gender: '' })
  const [searchKey, setSearchKey] = useState(0)

  const { data: overview } = useFetch<Overview>(`${API_BASE}/overview`)
  const { data: districts } = useFetch<DistrictsResponse>(`${API_BASE}/districts`)
  const { data: schools } = useFetch<any[]>(`${API_BASE}/schools?top=50`)
  const { data: positions } = useFetch<PositionAnalysis>(`${API_BASE}/positions/analysis`)

  const searchParams = new URLSearchParams()
  Object.entries(filters).forEach(([k, v]) => v && searchParams.set(k, v))
  searchParams.set('page', '1')
  searchParams.set('page_size', '20')

  const { data: search } = useFetch<SearchResult>(tab === 'search' ? `${API_BASE}/search?${searchParams}` : null)

  const [detailDistrict, setDetailDistrict] = useState('')
  const detailParams = detailDistrict ? `${API_BASE}/district/${encodeURIComponent(detailDistrict)}` : null
  const { data: detailData, loading: detailLoading, error: detailError } = useFetch<DistrictDetail>(detailParams)

  const handleSearch = useCallback(() => { setSearchKey(k => k + 1); setTab('search') }, [])
  const handleFilterChange = useCallback((k: string, v: string) => setFilters(f => ({ ...f, [k]: v })), [])

  const handleDistrictClick = useCallback((d: string) => { setDetailDistrict(d) }, [])
  const handleModalRetry = useCallback(() => { setDetailDistrict(''); setTimeout(() => setDetailDistrict(detailDistrict), 50) }, [detailDistrict])

  const districtsData = districts.data?.districts ?? []
  const searchItems = search.data?.items ?? []

  return (
    <div style={{ minHeight: '100vh', background: '#f5f7fa' }}>
      <header style={{ background: 'linear-gradient(135deg, #1e3a5f 0%, #0ea5e9 100%)', color: '#fff', padding: '20px 24px' }}>
        <h1 style={{ margin: 0, fontSize: '24px', fontWeight: '600' }}>2026 海关公示数据分析</h1>
        <p style={{ margin: '8px 0 0', opacity: 0.9, fontSize: '14px' }}>2026年海关公务员考试录用名单分析</p>
      </header>

      <main style={{ maxWidth: '1400px', margin: '0 auto', padding: '24px' }}>
        <div style={{ display: 'flex', gap: '12px', marginBottom: '24px' }}>
          {overview.data && [
            { label: '录用总数', value: overview.data.total, color: COLORS.primary },
            { label: '关区数', value: overview.data.districts, color: COLORS.success },
            { label: '院校数', value: overview.data.schools, color: COLORS.warning },
          ].map(({ label, value, color }) => (
            <div key={label} style={{ flex: 1, background: '#fff', borderRadius: '12px', padding: '16px', textAlign: 'center', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
              <div style={{ fontSize: '28px', fontWeight: 'bold', color }}>{value}</div>
              <div style={{ fontSize: '13px', color: '#6b7280', marginTop: '4px' }}>{label}</div>
            </div>
          ))}
        </div>

        <nav style={{ display: 'flex', gap: '8px', marginBottom: '24px', borderBottom: '1px solid #e5e7eb', paddingBottom: '1px' }}>
          {(['search', 'districts', 'schools', 'positions'] as TabType[]).map(t => (
            <button key={t} onClick={() => setTab(t)} style={{ padding: '10px 20px', background: 'none', border: 'none', borderBottom: tab === t ? `2px solid ${COLORS.primary}` : '2px solid transparent', color: tab === t ? COLORS.primary : '#6b7280', cursor: 'pointer', fontWeight: '500', transition: 'all 0.2s' }}>
              {{ search: '录用查询', districts: '关区', schools: '院校', positions: '职位' }[t]}
            </button>
          ))}
        </nav>

        <div style={{ background: '#fff', borderRadius: '16px', padding: '24px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          {tab === 'search' && (
            <>
              <SearchPanel onSearch={handleSearch} filters={filters} onFilterChange={handleFilterChange} onDetail={handleDistrictClick} />
              {search.loading && <LoadingSpinner />}
              {search.error && <ErrorMessage message={search.error} onRetry={handleSearch} />}
              {search.data && (
                <>
                  <p style={{ color: '#6b7280', marginBottom: '16px' }}>共找到 <strong style={{ color: COLORS.primary }}>{search.data.total}</strong> 条记录</p>
                  <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                      <thead>
                        <tr style={{ background: '#f9fafb' }}>
                          {['姓名', '性别', '毕业院校', '学历', '关区', '职位', '隶属海关'].map(h => (
                            <th key={h} style={{ padding: '12px', textAlign: 'left', fontWeight: '600', fontSize: '13px', borderBottom: '2px solid #e5e7eb', whiteSpace: 'nowrap' }}>{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {searchItems.map((item, i) => (
                          <tr key={i} style={{ borderBottom: '1px solid #f3f4f6' }}>
                            <td style={{ padding: '10px 12px' }}>{highlightText(item.姓名, filters.name)}</td>
                            <td style={{ padding: '10px 12px' }}>{item.性别 ?? '-'}</td>
                            <td style={{ padding: '10px 12px' }}>{highlightText(item.毕业院校, filters.school)}</td>
                            <td style={{ padding: '10px 12px' }}>{item.学历 ?? '-'}</td>
                            <td style={{ padding: '10px 12px' }}>
                              <span onClick={() => item.关区 && handleDistrictClick(item.关区)} style={{ color: COLORS.primary, cursor: 'pointer', textDecoration: 'none' }}>{item.关区 ?? '-'}</span>
                            </td>
                            <td style={{ padding: '10px 12px' }}>{highlightText(item.职位, filters.position)}</td>
                            <td style={{ padding: '10px 12px' }}>{item.隶属海关 ?? '-'}</td>
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
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ background: '#f9fafb' }}>
                    <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', borderBottom: '2px solid #e5e7eb' }}>关区</th>
                    <th style={{ padding: '12px', textAlign: 'right', fontWeight: '600', borderBottom: '2px solid #e5e7eb' }}>人数</th>
                    <th style={{ padding: '12px', textAlign: 'center', fontWeight: '600', borderBottom: '2px solid #e5e7eb' }}>官网</th>
                  </tr>
                </thead>
                <tbody>
                  {districtsData.map((d, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid #f3f4f6' }}>
                      <td style={{ padding: '12px' }}>
                        <span onClick={() => handleDistrictClick(d.关区)} style={{ color: COLORS.primary, cursor: 'pointer' }}>{d.关区}</span>
                      </td>
                      <td style={{ padding: '12px', textAlign: 'right', fontWeight: '500' }}>{d.人数}</td>
                      <td style={{ padding: '12px', textAlign: 'center' }}>
                        {d.官网 && <a href={d.官网} target="_blank" rel="noopener noreferrer" style={{ color: COLORS.success, textDecoration: 'none', fontSize: '13px' }}>访问 →</a>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {tab === 'schools' && <SchoolPanel data={schools.data} loading={schools.loading} error={schools.error} onRetry={() => {}} />}
          {tab === 'positions' && <PositionPanel data={positions.data} loading={positions.loading} error={positions.error} onRetry={() => {}} />}
        </div>
      </main>

      <DistrictDetailModal district={detailDistrict} data={detailData} loading={detailLoading} error={detailError} onClose={() => setDetailDistrict('')} onRetry={handleModalRetry} />
    </div>
  )
}
