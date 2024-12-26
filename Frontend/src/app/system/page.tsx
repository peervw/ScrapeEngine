"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { api } from "@/lib/api"
import { Loader2 } from "lucide-react"
import type { SystemMetrics } from "@/lib/api"

export default function SystemPage() {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null)
  const [events, setEvents] = useState<{ title: string; description: string }[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [metricsData, eventsData] = await Promise.all([
          api.getSystemMetrics(),
          api.getSystemEvents(),
        ])
        setMetrics(metricsData)
        setEvents(eventsData)
        setError(null)
      } catch (err) {
        console.error('Failed to fetch system data:', err)
        setError(err instanceof Error ? err.message : 'Failed to fetch system data')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
    const interval = setInterval(fetchData, 15000) // refresh every 15 seconds
    return () => clearInterval(interval)
  }, [])

  if (loading || !metrics) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  const isHealthy = metrics.cpu_usage < 80 && 
    (metrics.memory_usage.used / metrics.memory_usage.total) < 0.8 &&
    metrics.network.latency < 500

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">System Status</h1>
        <div className="flex gap-2">
          <Badge variant="outline">Auto-refreshing</Badge>
          <Badge 
            className={isHealthy ? 'bg-green-500' : 'bg-yellow-500'}
          >
            {isHealthy ? 'All Systems Operational' : 'Performance Degraded'}
          </Badge>
        </div>
      </div>

      {error && (
        <div className="bg-destructive/10 text-destructive px-4 py-2 rounded-md">
          {error}
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>System Resources</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <div className="flex justify-between mb-1 text-sm">
                <span>CPU Usage</span>
                <span>{metrics.cpu_usage.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-secondary h-2 rounded-full">
                <div 
                  className="bg-primary h-2 rounded-full" 
                  style={{ width: `${metrics.cpu_usage}%` }}
                ></div>
              </div>
            </div>

            <div>
              <div className="flex justify-between mb-1 text-sm">
                <span>Memory Usage</span>
                <span>
                  {(metrics.memory_usage.used / 1024).toFixed(1)}GB / 
                  {(metrics.memory_usage.total / 1024).toFixed(1)}GB
                </span>
              </div>
              <div className="w-full bg-secondary h-2 rounded-full">
                <div 
                  className="bg-primary h-2 rounded-full" 
                  style={{ 
                    width: `${(metrics.memory_usage.used / metrics.memory_usage.total) * 100}%` 
                  }}
                ></div>
              </div>
            </div>

            <div>
              <div className="flex justify-between mb-1 text-sm">
                <span>Disk Usage</span>
                <span>
                  {(metrics.disk_usage.used / 1024).toFixed(1)}GB / 
                  {(metrics.disk_usage.total / 1024).toFixed(1)}GB
                </span>
              </div>
              <div className="w-full bg-secondary h-2 rounded-full">
                <div 
                  className="bg-primary h-2 rounded-full" 
                  style={{ 
                    width: `${(metrics.disk_usage.used / metrics.disk_usage.total) * 100}%` 
                  }}
                ></div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Network Status</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Active Connections</span>
              <span>{metrics.network.active_connections}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Network Throughput</span>
              <span>{metrics.network.throughput.toFixed(1)} MB/s</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Average Latency</span>
              <span>{metrics.network.latency}ms</span>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="space-y-4">
        <h2 className="text-xl font-semibold">Recent System Events</h2>
        
        {events.map((event, index) => (
          <Alert key={index}>
            <AlertTitle>{event.title}</AlertTitle>
            <AlertDescription>
              {event.description}
            </AlertDescription>
          </Alert>
        ))}
      </div>
    </div>
  )
} 