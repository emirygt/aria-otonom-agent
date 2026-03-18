import axios from 'axios'
import type { OverviewData, Campaign, Insight, User, IntegrationStatus, OperatorAction } from './types'

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080',
  headers: { 'Content-Type': 'application/json' },
})

// Token interceptor
api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('aria_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
  }
  return config
})

// 401 → login'e yönlendir
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && typeof window !== 'undefined') {
      localStorage.removeItem('aria_token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// Auth
export const login = async (email: string, password: string): Promise<string> => {
  const form = new URLSearchParams()
  form.append('username', email)
  form.append('password', password)
  const res = await api.post('/api/v1/auth/login', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return res.data.access_token
}

export const register = async (email: string, password: string, full_name: string): Promise<string> => {
  const res = await api.post('/api/v1/auth/register', { email, password, full_name })
  return res.data.access_token
}

export const getMe = async (): Promise<User> => {
  const res = await api.get('/api/v1/auth/me')
  return res.data
}

// Dashboard
export const getOverview = async (): Promise<OverviewData> => {
  const res = await api.get('/api/v1/dashboard/overview')
  return res.data
}

export const getCampaigns = async (): Promise<Campaign[]> => {
  const res = await api.get('/api/v1/dashboard/campaigns')
  return res.data
}

// Insights
export const getInsights = async (): Promise<Insight[]> => {
  const res = await api.get('/api/v1/insights')
  return res.data
}

export const generateInsights = async (): Promise<Insight[]> => {
  const res = await api.post('/api/v1/insights/generate')
  return res.data
}

export const dismissInsight = async (id: string): Promise<Insight> => {
  const res = await api.patch(`/api/v1/insights/${id}/dismiss`)
  return res.data
}

// Integrations
export const getIntegrationStatus = async (): Promise<IntegrationStatus> => {
  const res = await api.get('/api/v1/integrations/status')
  return res.data
}

export const getIntegrations = async () => {
  const res = await api.get('/api/v1/integrations')
  return res.data
}

export const saveGa4PropertyId = async (property_id: string) => {
  const res = await api.post('/api/v1/integrations/ga4/property', { property_id })
  return res.data
}

export const disconnectGa4 = async () => {
  const res = await api.delete('/api/v1/integrations/ga4')
  return res.data
}

// Trends
export const getTrends = async () => {
  const res = await api.get('/api/v1/dashboard/trends')
  return res.data
}

// Operator
export const getOperatorHistory = async (): Promise<OperatorAction[]> => {
  const res = await api.get('/api/v1/operator/history')
  return res.data
}

export const planOperatorAction = async (goal: string): Promise<{ token: string; plan: string; actions: string[] }> => {
  const res = await api.post('/api/v1/operator/plan', { goal })
  return res.data
}

export const confirmOperatorAction = async (token: string): Promise<OperatorAction> => {
  const res = await api.post(`/api/v1/operator/confirm/${token}`)
  return res.data
}

export default api
