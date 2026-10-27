import { request } from './http'

export interface PublishPlanSummary {
  total_count: number
  pending_count: number
  success_count: number
  failed_count: number
}

export interface PublishPlanCalendarItem {
  id: number
  request_group_id: string
  date: string
  datetime?: string | null
  platform_type: number
  platform_code: string
  platform_name: string
  account_id: number
  account_name: string
  title: string
  cover_url?: string | null
  status: string
  publish_time_type: string
  scheduled_at?: string | null
  submitted_at?: string | null
}

export interface PublishPlanPendingItem {
  id: number
  request_group_id: string
  platform_type: number
  platform_code: string
  platform_name: string
  account_id: number
  account_name: string
  title: string
  cover_url?: string | null
  status: string
  status_message?: string | null
  publish_time_type: string
  scheduled_at?: string | null
  submitted_at?: string | null
}

export interface PublishPlanOverviewResponse {
  month: string
  summary: PublishPlanSummary
  calendar_items: PublishPlanCalendarItem[]
  pending_items: PublishPlanPendingItem[]
}

export interface DistributionContentItem {
  relation_id?: number | null
  account_id?: number | null
  account_name?: string | null
  account_avatar_url?: string | null
  platform_code: string
  platform_name: string
  content_id: string
  title: string
  content_kind: string
  cover_url?: string | null
  content_url?: string | null
  author_name?: string | null
  status: string
  status_label: string
  published_at?: string | null
  view_count: number
  liked_count: number
  comment_count: number
  share_count: number
  collected_at?: string | null
}

export interface DistributionContentListResponse {
  list: DistributionContentItem[]
  total: number
  platform_options: string[]
}

export const distributionApi = {
  getPublishPlanOverview(month: string) {
    return request<PublishPlanOverviewResponse>(
      `/api/v1/distribution/plans/overview?month=${encodeURIComponent(month)}`,
      {
        method: 'GET',
      },
    )
  },
  getDistributionItems(params?: { platformCode?: string; status?: string; keyword?: string }) {
    const search = new URLSearchParams()
    if (params?.platformCode) {
      search.set('platformCode', params.platformCode)
    }
    if (params?.status) {
      search.set('status', params.status)
    }
    if (params?.keyword) {
      search.set('keyword', params.keyword)
    }
    const query = search.toString()
    return request<DistributionContentListResponse>(`/api/v1/distribution/items${query ? `?${query}` : ''}`, {
      method: 'GET',
    })
  },
}
