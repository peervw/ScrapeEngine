"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { api } from "@/lib/api"
import { Loader2, AlertCircle, Server, Globe, Database } from "lucide-react"
import type { SystemMetrics, SystemEvent } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { format } from "date-fns"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"

export default function SystemPage() {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null)
  const [events, setEvents] = useState<SystemEvent[]>([])
  const [totalEvents, setTotalEvents] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [eventType, setEventType] = useState<string | undefined>()
  const [offset, setOffset] = useState(0)
  const limit = 10

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [metricsData, eventsData] = await Promise.all([
          api.getSystemMetrics(),
          api.getSystemEvents(limit, offset, eventType),
        ])
        setMetrics(metricsData)
        setEvents(eventsData.events)
        setTotalEvents(eventsData.total)
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
  }, [offset, eventType])

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

  const getEventIcon = (type: string) => {
    switch (type) {
      case 'system':
        return <Server className="h-4 w-4" />
      case 'runner':
        return <Database className="h-4 w-4" />
      case 'proxy':
        return <Globe className="h-4 w-4" />
      case 'scrape':
        return <AlertCircle className="h-4 w-4" />
      default:
        return <AlertCircle className="h-4 w-4" />
    }
  }

  const severityColor = {
    info: "bg-blue-500",
    warning: "bg-yellow-500",
    error: "bg-red-500"
  }

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
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-semibold">Recent System Events</h2>
          <Select value={eventType || 'all'} onValueChange={(value: string) => {
            setEventType(value === 'all' ? undefined : value)
            setOffset(0)
          }}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Filter by type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Events</SelectItem>
              <SelectItem value="system">System</SelectItem>
              <SelectItem value="runner">Runner</SelectItem>
              <SelectItem value="proxy">Proxy</SelectItem>
              <SelectItem value="scrape">Scrape</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <Card>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[50px]"></TableHead>
                <TableHead>Event</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Severity</TableHead>
                <TableHead className="text-right">Time</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {events.map((event) => (
                <Dialog key={event.id}>
                  <DialogTrigger asChild>
                    <TableRow className="cursor-pointer hover:bg-muted/50">
                      <TableCell>
                        <div className="h-8 w-8 flex items-center justify-center">
                          {getEventIcon(event.event_type)}
                        </div>
                      </TableCell>
                      <TableCell className="font-medium">{event.title}</TableCell>
                      <TableCell>
                        <Badge variant="outline">
                          {event.event_type}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge className={severityColor[event.severity]}>
                          {event.severity}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right text-muted-foreground">
                        {format(new Date(event.timestamp), 'MMM d, HH:mm')}
                      </TableCell>
                    </TableRow>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>{event.title}</DialogTitle>
                      <DialogDescription>
                        {event.description}
                        {event.details && (
                          <pre className="mt-4 text-xs bg-muted p-4 rounded-md overflow-auto">
                            {JSON.stringify(event.details, null, 2)}
                          </pre>
                        )}
                      </DialogDescription>
                    </DialogHeader>
                  </DialogContent>
                </Dialog>
              ))}
            </TableBody>
          </Table>
        </Card>

        <div className="flex justify-between items-center mt-4">
          <Button
            variant="outline"
            onClick={() => setOffset(Math.max(0, offset - limit))}
            disabled={offset === 0}
          >
            Previous
          </Button>
          <span className="text-sm text-muted-foreground">
            Showing {offset + 1}-{Math.min(offset + limit, totalEvents)} of {totalEvents} events
          </span>
          <Button
            variant="outline"
            onClick={() => setOffset(offset + limit)}
            disabled={offset + limit >= totalEvents}
          >
            Next
          </Button>
        </div>
      </div>
    </div>
  )
} 