"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { api } from "@/lib/api"
import type { RunnerHealth, SystemMetrics } from "@/lib/api"
import { Loader2 } from "lucide-react"

export default function DashboardPage() {
  const [runners, setRunners] = useState<RunnerHealth[]>([])
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [runnersData, metricsData] = await Promise.all([
          api.getRunnerHealth(),
          api.getSystemMetrics(),
        ])
        setRunners(runnersData)
        setMetrics(metricsData)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch data')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
    const interval = setInterval(fetchData, 5000)
    return () => clearInterval(interval)
  }, [])

  const activeRunners = runners.filter(r => r.status === 'active').length
  const totalJobs = runners.reduce((sum, r) => sum + r.active_jobs, 0)

  if (loading) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <div className="text-sm text-muted-foreground">
          Auto-refreshing every 5s
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Runners</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeRunners}</div>
            <p className="text-xs text-muted-foreground">
              of {runners.length} total runners
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Jobs</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalJobs}</div>
            <p className="text-xs text-muted-foreground">
              across all runners
            </p>
          </CardContent>
        </Card>

        {metrics && (
          <>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">System CPU</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {(metrics.cpu_usage * 100).toFixed(1)}%
                </div>
                <p className="text-xs text-muted-foreground">
                  current usage
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Memory Usage</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {((metrics.memory_usage.used / metrics.memory_usage.total) * 100).toFixed(1)}%
                </div>
                <p className="text-xs text-muted-foreground">
                  {(metrics.memory_usage.used / 1024 / 1024 / 1024).toFixed(1)} GB of{' '}
                  {(metrics.memory_usage.total / 1024 / 1024 / 1024).toFixed(1)} GB
                </p>
              </CardContent>
            </Card>
          </>
        )}
      </div>

      {error && (
        <div className="bg-destructive/10 text-destructive px-4 py-2 rounded-md">
          {error}
        </div>
      )}
    </div>
  )
}
