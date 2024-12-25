export interface ScrapingConfig {
  stealth: boolean;
  render: boolean;
  parse: boolean;
}

export interface ScrapeRequest extends ScrapingConfig {
  url: string;
}

export interface ScrapingResult {
  url: string;
  stealth: boolean;
  render: boolean;
  parse: boolean;
  proxy_used: string;
  runner_used: string;
  method_used: string;
  content: {
    html?: string;
    text?: string;
    metadata?: Record<string, string>;
    links?: string[];
    images?: string[];
    parsed_data?: Record<string, unknown>;
  };
}

export interface ScrapeLog {
  timestamp: string;
  runner_id: string;
  status: 'success' | 'failed';
  url: string;
  duration: number;
  details: string;
  config?: {
    url: string;
    stealth: boolean;
    render: boolean;
    parse: boolean;
    proxy: string;
  };
  result?: {
    proxy_used: string;
    runner_used: string;
    method_used: string;
    response_time: number;
    content: {
      raw_content?: string;
      text_content?: string;
      title?: string;
      links?: { href: string; text: string }[];
      parse_error?: string;
    };
  };
  error?: string;
}

export interface RunnerHealth {
  id: string;
  status: 'active' | 'offline';
  cpu_usage: number;
  memory_usage: {
    used: number;
    total: number;
  };
  active_jobs: number;
  uptime: number;
  last_seen?: string;
  last_status?: string;
}

export interface SystemMetrics {
  cpu_usage: number;
  memory_usage: {
    used: number;
    total: number;
  };
  disk_usage: {
    used: number;
    total: number;
  };
  network: {
    active_connections: number;
    throughput: number;
    latency: number;
  };
}

export interface SystemSettings {
  num_runners: string;
  log_retention_days: string;
}

export interface LogsResponse {
  total: number;
  offset: number;
  limit: number;
  logs: ScrapeLog[];
}

class ApiClient {
  private apiKey: string | null = null;
  private apiKeyPromise: Promise<string> | null = null;

  private async ensureApiKey(): Promise<string> {
    if (this.apiKey) {
      return this.apiKey;
    }

    if (this.apiKeyPromise) {
      return this.apiKeyPromise;
    }

    this.apiKeyPromise = (async () => {
      try {
        const response = await this.fetch<{ key: string }>('/api/settings/api-key', {}, false);
        this.apiKey = response.key;
        return this.apiKey;
      } finally {
        this.apiKeyPromise = null;
      }
    })();

    return this.apiKeyPromise;
  }

  private async getHeaders(requiresAuth: boolean = true): Promise<HeadersInit> {
    const headers: HeadersInit = {
      'Content-Type': 'application/json'
    };
    
    if (requiresAuth) {
      const apiKey = await this.ensureApiKey();
      headers['Authorization'] = `Bearer ${apiKey}`;
    }
    
    return headers;
  }

  private getBaseUrl(): string {
    if (typeof window !== 'undefined') {
      return '';
    }
    return process.env.INTERNAL_API_URL || 'http://distributor:8080';
  }

  private async fetch<T>(endpoint: string, options: RequestInit = {}, requiresAuth: boolean = true): Promise<T> {
    const baseUrl = this.getBaseUrl();
    const url = baseUrl ? `${baseUrl}${endpoint}` : endpoint;
    const headers = await this.getHeaders(requiresAuth);

    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          ...headers,
          ...options.headers,
        },
      });
      
      if (!response.ok) {
        if (response.status === 401 && requiresAuth && this.apiKey) {
          this.apiKey = null;
          return this.fetch<T>(endpoint, options, requiresAuth);
        }

        const error = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(error.detail || `API error: ${response.statusText}`);
      }
      return response.json();
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  async getRunnerHealth(): Promise<RunnerHealth[]> {
    return this.fetch<RunnerHealth[]>('/api/runners/health');
  }

  async getScrapeLogs(limit: number = 50, offset: number = 0): Promise<LogsResponse> {
    const params = new URLSearchParams({ 
      limit: limit.toString(),
      offset: offset.toString()
    });
    return this.fetch<LogsResponse>(`/api/logs?${params}`);
  }

  async getSystemMetrics(): Promise<SystemMetrics> {
    return this.fetch<SystemMetrics>('/api/metrics');
  }

  async getSystemEvents(): Promise<{ title: string; description: string }[]> {
    return this.fetch<{ title: string; description: string }[]>('/api/events');
  }

  async submitScrapeRequest(config: ScrapeRequest): Promise<ScrapingResult> {
    return this.fetch<ScrapingResult>('/api/scrape', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async getSettings(): Promise<SystemSettings> {
    return this.fetch<SystemSettings>('/api/settings', {}, false);
  }

  async updateSettings(settings: Partial<SystemSettings>): Promise<{ status: string }> {
    return this.fetch<{ status: string }>('/api/settings', {
      method: 'POST',
      body: JSON.stringify(settings),
    }, false);
  }

  async getApiKey(): Promise<{ key: string }> {
    return this.fetch<{ key: string }>('/api/settings/api-key', {}, false);
  }

  async regenerateApiKey(): Promise<{ key: string }> {
    const response = await this.fetch<{ key: string }>('/api/settings/api-key/regenerate', {
      method: 'POST'
    }, false);
    this.apiKey = response.key;
    return response;
  }
}

export const api = new ApiClient(); 