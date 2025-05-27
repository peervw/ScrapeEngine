'use client'

import { useState, useEffect } from 'react'
import { apiClient, Job, Runner, Stats, ScrapeRecord, APIKey } from '@/lib/api'

export function useJobs(autoRefresh = true, refreshInterval = 30000) {
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchJobs = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await apiClient.getJobs()
      setJobs(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch jobs')
      setJobs([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchJobs()
    if (autoRefresh) {
      const interval = setInterval(fetchJobs, refreshInterval)
      return () => clearInterval(interval)
    }
  }, [autoRefresh, refreshInterval])

  return { jobs, loading, error, refetch: fetchJobs }
}

export function useRunners(autoRefresh = true, refreshInterval = 10000) {
  const [runners, setRunners] = useState<Runner[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchRunners = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await apiClient.getRunners()
      setRunners(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch runners')
      setRunners([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchRunners()
    if (autoRefresh) {
      const interval = setInterval(fetchRunners, refreshInterval)
      return () => clearInterval(interval)
    }
  }, [autoRefresh, refreshInterval])

  return { runners, loading, error, refetch: fetchRunners }
}

export function useStats(autoRefresh = true, refreshInterval = 15000) {
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchStats = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await apiClient.getStats()
      setStats(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch stats')
      setStats({
        active_jobs: 0,
        connected_runners: 0,
        total_runners: 0,
        pages_scraped: 0,
        system_health: 0.0,
        total_scrapes_today: 0,
        total_scrapes_all_time: 0,
        average_response_time: 0.0,
        error_rate: 0.0,
        timestamp: new Date().toISOString()
      })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStats()
    if (autoRefresh) {
      const interval = setInterval(fetchStats, refreshInterval)
      return () => clearInterval(interval)
    }
  }, [autoRefresh, refreshInterval])

  return { stats, loading, error, refetch: fetchStats }
}

export function useSystemHealth(autoRefresh = true, refreshInterval = 30000) {
  const [health, setHealth] = useState<{ status: string; timestamp: string } | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchHealth = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await apiClient.getHealth()
      setHealth(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch health')
      setHealth({
        status: 'healthy',
        timestamp: new Date().toISOString()
      })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchHealth()
    if (autoRefresh) {
      const interval = setInterval(fetchHealth, refreshInterval)
      return () => clearInterval(interval)
    }
  }, [autoRefresh, refreshInterval])

  return { health, loading, error, refetch: fetchHealth }
}

export function useScrapeHistory(autoRefresh = true, refreshInterval = 10000) {
  const [scrapes, setScrapes] = useState<ScrapeRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchScrapes = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await apiClient.getScrapeHistory()
      setScrapes(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch scrape history')
      setScrapes([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchScrapes()
    if (autoRefresh) {
      const interval = setInterval(fetchScrapes, refreshInterval)
      return () => clearInterval(interval)
    }
  }, [autoRefresh, refreshInterval])

  return { scrapes, loading, error, refetch: fetchScrapes }
}

export function useAPIKeys() {
  const [apiKeys, setAPIKeys] = useState<APIKey[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchAPIKeys = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await apiClient.getAPIKeys()
      setAPIKeys(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch API keys')
      setAPIKeys([])
    } finally {
      setLoading(false)
    }
  }

  const createAPIKey = async (name: string) => {
    try {
      const result = await apiClient.createAPIKey(name)
      await fetchAPIKeys()
      return result
    } catch (err) {
      throw err
    }
  }

  const deactivateAPIKey = async (keyId: string) => {
    try {
      await apiClient.deactivateAPIKey(keyId)
      await fetchAPIKeys()
    } catch (err) {
      throw err
    }
  }

  useEffect(() => {
    fetchAPIKeys()
  }, [])

  return { 
    apiKeys, 
    loading, 
    error, 
    refetch: fetchAPIKeys,
    createAPIKey,
    deactivateAPIKey
  }
}
