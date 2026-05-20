/**
 * TypeScript type definitions for customs data dashboard.
 * 
 * 类型与后端 schemas.py 的对应关系：
 * - Overview         -> OverviewResponse
 * - District         -> DistrictInfo
 * - DistrictDetail   -> DistrictDetailResponse
 * - PositionAnalysis -> PositionAnalysisResponse
 * - SearchItem       -> SearchResultItem
 * - SearchResult      -> SearchResponse
 */

// =============================================================================
// Overview - 首页概览数据
// =============================================================================

/**
 * 总体统计数据（首页概览卡片）
 * 
 * 对应后端：OverviewResponse
 */
export interface Overview {
  total: number       // 总录用人数
  districts: number   // 关区数量
  schools: number     // 院校数量
  positions: number   // 职位数量
}

// =============================================================================
// District - 关区相关类型
// =============================================================================

/**
 * 单个关区信息（关区列表展示）
 * 
 * 对应后端：DistrictInfo
 */
export interface District {
  关区: string    // 关区名称
  人数: number    // 录用人数
  官网?: string   // 关区官网地址（可选）
}

/**
 * 关区列表响应
 * 
 * 对应后端：DistrictsResponse
 */
export interface DistrictsResponse {
  districts: District[]
}

/**
 * 关区详情数据（点击关区弹窗展示）
 * 
 * 对应后端：DistrictDetailResponse
 */
export interface DistrictDetail {
  district: string                              // 关区名称
  total: number                                 // 总人数
  male: number                                  // 男性人数
  female: number                                // 女性人数
  education: Array<{ name: string; value: number }>  // 学历分布
  gender: Array<{ name: string; value: number }>     // 性别分布
  top_positions: Array<{ name: string; count: number }>  // 热门职位 Top5
  top_schools: Array<{ 毕业院校: string; 人数: number }>  // 来源院校 Top5
}

// =============================================================================
// School - 院校相关类型
// =============================================================================

/**
 * 院校统计信息（院校列表展示）
 * 
 * 对应后端：SchoolInfo
 */
export interface School {
  毕业院校: string   // 毕业院校名称
  人数: number       // 录用人数
}

// =============================================================================
// Position - 职位相关类型
// =============================================================================

/**
 * 职位分析统计数据（数据分析模块）
 * 
 * 对应后端：PositionAnalysisResponse
 */
export interface PositionAnalysis {
  total_positions: number           // 职位总数（不同职位类型数量）
  job_type_counts: Record<string, number>   // 职位类型分布 {职位名: 人数}
  level_counts: Record<string, number>      // 级别分布 {级别: 人数}
  sub_district_counts: Record<string, number>  // 隶属关分布 {关区: 人数}
}

// =============================================================================
// Search - 搜索相关类型
// =============================================================================

/**
 * 搜索结果项（表格行数据）
 * 
 * 职位字段由后端 parse_position_field() 解析生成：
 * - 隶属关：实际工作海关
 * - 职务职位：职务职位名称
 * - 职位代码：12位代码
 * 
 * 对应后端：SearchResultItem
 */
export interface SearchItem {
  姓名: string
  性别?: string
  毕业院校?: string
  学历?: string
  关区?: string       // 关区（行政区划）
  隶属关?: string     // 隶属关（实际工作海关）
  职务职位?: string   // 职务职位
  职位代码?: string   // 职位代码（12位）
}

/**
 * 搜索响应（分页结果）
 * 
 * 对应后端：SearchResponse
 */
export interface SearchResult {
  items: SearchItem[]     // 当前页的搜索结果列表
  total: number           // 满足条件的总记录数
  page: number            // 当前页码
  page_size: number       // 每页记录数
  total_pages: number     // 总页数
}

// =============================================================================
// UI State - UI 状态类型
// =============================================================================

/** Tab 类型枚举 */
export type TabType = 'search' | 'districts' | 'schools' | 'positions'

/**
 * 数据获取状态（用于 useFetch hook）
 * 
 * 用于处理异步数据加载的加载状态
 */
export interface FetchState<T> {
  data: T | null    // 获取到的数据，null 表示未加载或加载中
  loading: boolean  // 是否正在加载
  error: string | null  // 错误信息，null 表示无错误
}
