import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { api } from "@/lib/api"

// Force dynamic rendering
export const dynamic = 'force-dynamic'
export const revalidate = 15 // revalidate every 15 seconds

function formatUptime(seconds: number): string {
  const days = Math.floor(seconds / (24 * 60 * 60))
  const hours = Math.floor((seconds % (24 * 60 * 60)) / (60 * 60))
  const minutes = Math.floor((seconds % (60 * 60)) / 60)
  return `${days}d ${hours}h ${minutes}m`
}

export default async function RunnersPage() {
  const runners = await api.getRunnerHealth()

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Runner Health</h1>

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