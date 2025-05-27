'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { 
  Activity, 
  Users, 
  Globe, 
  Server
} from 'lucide-react'
import { useStats } from '@/hooks/useApi'

export function StatsOverview() {
  const { stats, loading, error } = useStats(true, 10000) // Auto-refresh every 10 seconds

  if (loading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-6">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <Card key={i}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium animate-pulse bg-gray-200 h-4 w-20 rounded"></CardTitle>
              <div className="animate-pulse bg-gray-200 h-4 w-4 rounded"></div>
            </CardHeader>
            <CardContent>
              <div className="animate-pulse bg-gray-200 h-8 w-16 rounded mb-2"></div>
              <div className="animate-pulse bg-gray-200 h-3 w-24 rounded"></div>
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  const formatResponseTime = (time?: number) => {
    if (!time) return "0ms"
    if (time < 1) return `${Math.round(time * 1000)}ms`
    return `${time.toFixed(2)}s`
  }

  const getHealthColor = (health?: number) => {
    if (!health) return "text-gray-600"
    if (health >= 90) return "text-emerald-600"
    if (health >= 70) return "text-yellow-600"
    return "text-red-600"
  }

  const statsData = [
    {
      title: "Active Jobs",
      value: stats?.active_jobs?.toString() || "0",
      change: error ? "Connection failed" : "Currently running",
      icon: Activity,
      color: "text-blue-600"
    },
    {
      title: "Connected Runners",
      value: stats?.connected_runners?.toString() || "0",
      change: error ? "Connection failed" : `${stats?.total_runners || 0} total`,
      icon: Users,
      color: "text-green-600"
    },
    {
      title: "Total Scraped",
      value: stats?.pages_scraped?.toString() || "0",
      change: error ? "Connection failed" : "All time",
      icon: Globe,
      color: "text-purple-600"
    },
    {
      title: "Today's Scrapes",
      value: stats?.total_scrapes_today?.toString() || "0",
      change: error ? "Connection failed" : "Since midnight",
      icon: Activity,
      color: "text-orange-600"
    },
    {
      title: "Avg Response",
      value: formatResponseTime(stats?.average_response_time),
      change: error ? "Connection failed" : "Last hour",
      icon: Server,
      color: "text-cyan-600"
    },
    {
      title: "System Health",
      value: `${stats?.system_health?.toFixed(1) || "0"}%`,
      change: error ? "Connection failed" : `${stats?.error_rate?.toFixed(1) || "0"}% error rate`,
      icon: Server,
      color: getHealthColor(stats?.system_health)
    }
  ]

  return (
    <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-6">
      {statsData.map((stat, index) => (
        <Card key={index}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              {stat.title}
            </CardTitle>
            <stat.icon className={`h-4 w-4 ${stat.color}`} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stat.value}</div>
            <p className={`text-xs ${error ? 'text-red-500' : 'text-muted-foreground'}`}>
              {stat.change}
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
