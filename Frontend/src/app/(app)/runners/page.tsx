"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { api } from "@/lib/api"
import { Loader2 } from "lucide-react"
import type { RunnerHealth } from "@/lib/api"

function formatUptime(seconds: number): string {
  const days = Math.floor(seconds / (24 * 60 * 60))
  const hours = Math.floor((seconds % (24 * 60 * 60)) / (60 * 60))
  const minutes = Math.floor((seconds % (60 * 60)) / 60)
  return `${days}d ${hours}h ${minutes}m`
}

export default function RunnersPage() {
  const [runners, setRunners] = useState<RunnerHealth[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await api.getRunnerHealth()
        setRunners(data)
        setError(null)
      } catch (err) {
        console.error('Failed to fetch runner health:', err)
        setError(err instanceof Error ? err.message : 'Failed to fetch runner health')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
    const interval = setInterval(fetchData, 15000) // refresh every 15 seconds
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Runner Health</h1>
        <Badge variant="outline">Auto-refreshing</Badge>
      </div>

      {error && (
        <div className="bg-destructive/10 text-destructive px-4 py-2 rounded-md">
          {error}
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {runners.map((runner) => (
          <Card key={runner.id}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0">
              <CardTitle className="text-xl">{runner.id}</CardTitle>
              <Badge 
                className={runner.status === 'active' ? 'bg-green-500' : undefined}
                variant={runner.status === 'active' ? undefined : 'destructive'}
              >
                {runner.status === 'active' ? 'Active' : 'Offline'}
              </Badge>
            </CardHeader>
            <CardContent className="space-y-2">
              {runner.status === 'active' ? (
                <>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">CPU Usage</span>
                    <span>{runner.cpu_usage.toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Memory Usage</span>
                    <span>
                      {(runner.memory_usage.used / 1024).toFixed(1)}GB / 
                      {(runner.memory_usage.total / 1024).toFixed(1)}GB
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Active Jobs</span>
                    <span>{runner.active_jobs}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Uptime</span>
                    <span>{formatUptime(runner.uptime)}</span>
                  </div>
                </>
              ) : (
                <>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Last Seen</span>
                    <span>{runner.last_seen}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Last Status</span>
                    <span>{runner.last_status}</span>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
} 