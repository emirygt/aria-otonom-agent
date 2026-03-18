export interface MetricValue {
  value: number
  change_pct: number
  trend: 'up' | 'down' | 'stable'
}

export interface HealthScoreSummary {
  score: number
  trend: string
  top_issues: string[]
}

export interface OverviewData {
  health_score: HealthScoreSummary
  revenue_tl: MetricValue
  sessions: MetricValue
  conversion_rate: MetricValue
  roas: MetricValue
  data_source?: string
}

export interface Campaign {
  name: string
  spend_tl: number
  revenue_tl: number
  roas: number
  status: string
  trend: string
}

export interface Insight {
  id: string
  title: string
  category: string
  severity: 'critical' | 'warning' | 'opportunity'
  finding: string
  cause: string
  action: string
  impact_tl: number | null
  status: string
}

export interface User {
  id: string
  email: string
  full_name: string
  plan: string
  is_active: boolean
}

export interface Integration {
  id: string
  platform: string
  status: string
  last_sync: string | null
}

export interface IntegrationStatus {
  ga4: boolean
  google_ads: boolean
  meta: boolean
  shopify: boolean
  ticimax: boolean
}

export interface OperatorAction {
  id: string
  action_type: string
  parameters: Record<string, unknown>
  status: 'pending' | 'confirmed' | 'executed' | 'failed'
  result: Record<string, unknown> | null
  confirmation_token: string | null
  created_at: string
}
