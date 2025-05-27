// Always use Next.js API routes as proxy to avoid mixed content issues
// This works on both HTTP (local) and HTTPS (server) environments
const API_BASE_URL = '/api/proxy'

export interface Job {
  id: string
  name: string
  status: 'running' | 'completed' | 'paused' | 'failed' | 'queued'
  progress: number
  pages_scraped: number
  total_pages: number
  created_at: string
  updated_at: string
  assigned_runner?: string
}

export interface Runner {
  id: string
  name: string
  status: 'active' | 'idle' | 'offline' | 'error'
  current_job?: string
  last_heartbeat: string
  cpu_usage: number
  memory_usage: number
  completed_jobs: number
  uptime: string
  version: string
}

export interface Stats {
  active_jobs: number
  connected_runners: number
  total_runners: number
  pages_scraped: number
  system_health: number
  total_scrapes_today: number
  total_scrapes_all_time: number
  average_response_time: number
  error_rate: number
  timestamp: string
}

export interface ScrapeRecord {
  id: string
  url: string
  method: string
  status: 'success' | 'failed' | 'timeout'
  runner_id?: string
  proxy_used?: string
  response_time?: number
  content_length?: number
  created_at: string
  error_message?: string
  api_key_id?: string
}

export interface APIKey {
  id: string
  name: string
  created_at: string
  last_used?: string
  is_active: boolean
  usage_count: number
  key_preview: string
}

class ApiClient {
  private baseURL: string

  constructor() {
    this.baseURL = API_BASE_URL
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseURL}${endpoint}`
    
    try {
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
        ...options,
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error)
      throw error
    }
  }

  // Jobs
  async getJobs(): Promise<Job[]> {
    return this.request<Job[]>('/jobs')
  }

  async getJob(id: string): Promise<Job> {
    return this.request<Job>(`/jobs/${id}`)
  }

  async pauseJob(id: string): Promise<void> {
    return this.request<void>(`/jobs/${id}/pause`, { method: 'POST' })
  }

  async resumeJob(id: string): Promise<void> {
    return this.request<void>(`/jobs/${id}/resume`, { method: 'POST' })
  }

  async stopJob(id: string): Promise<void> {
    return this.request<void>(`/jobs/${id}/stop`, { method: 'POST' })
  }

  // Runners
  async getRunners(): Promise<Runner[]> {
    return this.request<Runner[]>('/runners')
  }

  async getRunner(id: string): Promise<Runner> {
    return this.request<Runner>(`/runners/${id}`)
  }

  async restartRunner(id: string): Promise<void> {
    return this.request<void>(`/runners/${id}/restart`, { method: 'POST' })
  }

  async stopRunner(id: string): Promise<void> {
    return this.request<void>(`/runners/${id}/stop`, { method: 'POST' })
  }

  // Stats
  async getStats(): Promise<Stats> {
    return this.request<Stats>('/stats')
  }

  // Scrape Records
  async getScrapeHistory(): Promise<ScrapeRecord[]> {
    return this.request<ScrapeRecord[]>('/scrapes')
  }

  // API Key Management (admin only)
  async getAPIKeys(): Promise<APIKey[]> {
    return this.request<APIKey[]>('/admin/api-keys')
  }

  async createAPIKey(name: string): Promise<{ key_id: string; name: string; key: string; message: string }> {
    return this.request('/admin/api-keys', {
      method: 'POST',
      body: JSON.stringify({ name })
    })
  }

  async deactivateAPIKey(keyId: string): Promise<{ message: string }> {
    return this.request(`/admin/api-keys/${keyId}`, {
      method: 'DELETE'
    })
  }

  // Health check
  async getHealth(): Promise<{ status: string; timestamp: string }> {
    return this.request<{ status: string; timestamp: string }>('/health')
  }
}

export const apiClient = new ApiClient()
