/**
 * TypeScript type definitions for customs data dashboard.
 */

export interface Overview {
  total: number
  districts: number
  schools: number
  positions: number
}

export interface District {
  关区: string
  人数: number
  官网?: string
}

export interface DistrictsResponse {
  districts: District[]
}

export interface DistrictDetail {
  district: string
  total: number
  male: number
  female: number
  education: Array<{ name: string; value: number }>
  gender: Array<{ name: string; value: number }>
  top_positions: Array<{ name: string; count: number }>
  top_schools: Array<{ 毕业院校: string; 人数: number }>
}

export interface School {
  毕业院校: string
  人数: number
}

export interface PositionAnalysis {
  total_positions: number
  job_type_counts: Record<string, number>
  level_counts: Record<string, number>
  sub_district_counts: Record<string, number>
}

export interface SearchItem {
  姓名: string
  性别?: string
  毕业院校?: string
  学历?: string
  关区?: string
  隶属关?: string      // 隶属关名称
  职务职位?: string   // 职务职位
  职位代码?: string   // 职位代码
}

export interface SearchResult {
  items: SearchItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export type TabType = 'search' | 'districts' | 'schools' | 'positions'

export interface FetchState<T> {
  data: T | null
  loading: boolean
  error: string | null
}
