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
  id: number;
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
  webshare_token: string;
}

export interface LogsResponse {
  total: number;
  offset: number;
  limit: number;
  logs: ScrapeLog[];
}

export interface ProxyStats {
  host: string;
  port: string;
  last_used: string | null;
  success_rate: number;
  avg_response_time: number | null;
  failures: number;
}

export interface ProxyListResponse {
  total_proxies: number;
  available_proxies: number;
  proxies: ProxyStats[];
}

export interface ProxyCreate {
  host: string;
  port: string;
  username?: string;
  password?: string;
}

class ApiClient {
  private apiKey: string | null = null;
  private baseUrl: string;

  constructor() {
    this.baseUrl = '/api';
  }

  private async fetch<T>(path: string, options: RequestInit = {}, requiresAuth: boolean = true): Promise<T> {
    if (requiresAuth && !this.apiKey && path !== '/settings/api-key') {
      try {
        const response = await this.getApiKey();
        this.apiKey = response.key;
        console.log("Retrieved API key:", this.apiKey?.substring(0, 10) + "...");
      } catch (error) {
        console.error("Failed to get API key:", error);
        throw error;
      }
    }

    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    if (requiresAuth && this.apiKey) {
      headers['Authorization'] = `Bearer ${this.apiKey}`;
      console.log("Using Authorization header:", headers['Authorization'].substring(0, 20) + "...");
    }

    const cleanPath = path.startsWith('/api/') ? path.substring(4) : path;
    const url = new URL(`${this.baseUrl}${cleanPath.startsWith('/') ? cleanPath : '/' + cleanPath}`, window.location.origin).toString();
    
    console.log(`Making request to: ${url}`);

    const response = await fetch(url, {
      ...options,
      headers: {
        ...headers,
        ...options.headers,
      },
    });

    if (!response.ok) {
      console.error(`API Error (${url}):`, {
        status: response.status,
        statusText: response.statusText,
        headers: Object.fromEntries(response.headers.entries()),
      });
      throw new Error(`API request failed: ${response.statusText}`);
    }

    return response.json();
  }

  async getRunnerHealth(): Promise<RunnerHealth[]> {
    return this.fetch<RunnerHealth[]>('/runners/health');
  }

  async getScrapeLogs(limit: number = 50, offset: number = 0): Promise<LogsResponse> {
    const params = new URLSearchParams({ 
      limit: limit.toString(),
      offset: offset.toString()
    });
    return this.fetch<LogsResponse>(`/logs?${params}`);
  }

  async getSystemMetrics(): Promise<SystemMetrics> {
    return this.fetch<SystemMetrics>('/metrics');
  }

  async getSystemEvents(): Promise<{ title: string; description: string }[]> {
    return this.fetch<{ title: string; description: string }[]>('/events');
  }

  async submitScrapeRequest(config: ScrapeRequest): Promise<ScrapingResult> {
    return this.fetch<ScrapingResult>('/scrape', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async getSettings(): Promise<SystemSettings> {
    return this.fetch<SystemSettings>('/settings');
  }

  async updateSettings(settings: Partial<SystemSettings>): Promise<{ message: string }> {
    return this.fetch<{ message: string }>('/settings', {
      method: 'POST',
      body: JSON.stringify(settings),
    });
  }

  async getApiKey(): Promise<{ key: string }> {
    return this.fetch<{ key: string }>('/settings/api-key', {}, false);
  }

  async regenerateApiKey(): Promise<{ key: string }> {
    const response = await this.fetch<{ key: string }>('/settings/api-key/regenerate', {
      method: 'POST'
    }, false);
    this.apiKey = response.key;
    return response;
  }

  async getProxies(): Promise<ProxyListResponse> {
    return this.fetch<ProxyListResponse>('/proxies');
  }

  async addProxy(proxy: ProxyCreate): Promise<{ status: string; message: string }> {
    return this.fetch<{ status: string; message: string }>('/proxies', {
      method: 'POST',
      body: JSON.stringify(proxy),
    });
  }

  async deleteProxy(host: string): Promise<{ status: string; message: string }> {
    return this.fetch<{ status: string; message: string }>(`/proxies/${encodeURIComponent(host)}`, {
      method: 'DELETE',
    });
  }

  async setWebshareToken(token: string): Promise<{ status: string; message: string }> {
    return this.fetch<{ status: string; message: string }>('/proxies/webshare', {
      method: 'POST',
      body: JSON.stringify({ token }),
    });
  }

  async refreshProxies(): Promise<{ status: string; message: string }> {
    return this.fetch<{ status: string; message: string }>('/proxies/refresh', {
      method: 'POST',
    });
  }

  async deleteAllLogs(): Promise<{ status: string; message: string }> {
    return this.fetch<{ status: string; message: string }>('/logs', {
      method: 'DELETE',
    });
  }

  async deleteLog(logId: number): Promise<{ status: string; message: string }> {
    return this.fetch<{ status: string; message: string }>(`/logs/${logId}`, {
      method: 'DELETE',
    });
  }
}

export const api = new ApiClient(); 