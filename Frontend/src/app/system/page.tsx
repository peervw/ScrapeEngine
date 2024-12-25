import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { api } from "@/lib/api"

// Force dynamic rendering
export const dynamic = 'force-dynamic'
export const revalidate = 15 // revalidate every 15 seconds

export default async function SystemPage() {
  const [metrics, events] = await Promise.all([
    api.getSystemMetrics(),
    api.getSystemEvents(),
  ])

  const isHealthy = metrics.cpu_usage < 80 && 
    (metrics.memory_usage.used / metrics.memory_usage.total) < 0.8 &&
    metrics.network.latency < 500

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">System Status</h1>
        <Badge 
          variant="outline" 
          className={isHealthy ? 'bg-green-500' : 'bg-yellow-500'}
        >
          {isHealthy ? 'All Systems Operational' : 'Performance Degraded'}
        </Badge>
      </div>

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