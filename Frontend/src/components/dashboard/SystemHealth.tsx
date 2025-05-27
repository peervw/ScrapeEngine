'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { 
  CheckCircle, 
  AlertCircle, 
  XCircle,
  Server,
  Database,
  Wifi,
  Shield,
  Activity,
  Clock
} from 'lucide-react'

interface HealthMetric {
  name: string
  status: 'healthy' | 'warning' | 'critical'
  value: string
  description: string
  icon: React.ElementType
  lastChecked: string
}

interface SystemComponent {
  name: string
  status: 'online' | 'degraded' | 'offline'
  uptime: string
  responseTime: string
  version: string
}

export function SystemHealth() {
  const healthMetrics: HealthMetric[] = [
    {
      name: "API Response Time",
      status: "healthy",
      value: "120ms",
      description: "Average response time across all endpoints",
      icon: Activity,
      lastChecked: "30 seconds ago"
    },
    {
      name: "Database Connection",
      status: "healthy", 
      value: "Connected",
      description: "All database connections are stable",
      icon: Database,
      lastChecked: "1 minute ago"
    },
    {
      name: "Proxy Pool Health",
      status: "warning",
      value: "87%",
      description: "13% of proxies are currently unavailable",
      icon: Shield,
      lastChecked: "2 minutes ago"
    },
    {
      name: "Memory Usage",
      status: "healthy",
      value: "68%",
      description: "System memory utilization",
      icon: Server,
      lastChecked: "30 seconds ago"
    },
    {
      name: "Network Connectivity",
      status: "healthy",
      value: "Stable",
      description: "All network connections are functioning",
      icon: Wifi,
      lastChecked: "1 minute ago"
    },
    {
      name: "Error Rate",
      status: "critical",
      value: "2.3%",
      description: "Higher than normal error rate detected",
      icon: AlertCircle,
      lastChecked: "1 minute ago"
    }
  ]

  const systemComponents: SystemComponent[] = [
    {
      name: "Distributor Service",
      status: "online",
      uptime: "99.98%",
      responseTime: "45ms",
      version: "v2.1.0"
    },
    {
      name: "Runner Pool",
      status: "degraded",
      uptime: "98.7%",
      responseTime: "120ms", 
      version: "v1.8.3"
    },
    {
      name: "Proxy Manager",
      status: "online",
      uptime: "99.5%",
      responseTime: "80ms",
      version: "v1.4.2"
    },
    {
      name: "Job Scheduler",
      status: "online",
      uptime: "99.9%",
      responseTime: "25ms",
      version: "v3.2.1"
    }
  ]

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'online':
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case 'warning':
      case 'degraded':
        return <AlertCircle className="h-4 w-4 text-yellow-600" />
      case 'critical':
      case 'offline':
        return <XCircle className="h-4 w-4 text-red-600" />
      default:
        return <AlertCircle className="h-4 w-4 text-gray-600" />
    }
  }

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      healthy: 'bg-green-100 text-green-800',
      online: 'bg-green-100 text-green-800',
      warning: 'bg-yellow-100 text-yellow-800',
      degraded: 'bg-yellow-100 text-yellow-800',
      critical: 'bg-red-100 text-red-800',
      offline: 'bg-red-100 text-red-800'
    }
    
    return <Badge className={statusConfig[status as keyof typeof statusConfig] || 'bg-gray-100 text-gray-800'}>{status}</Badge>
  }

  return (
    <div className="space-y-6">
      {/* Overall System Status */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg">System Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-3">
              <CheckCircle className="h-8 w-8 text-green-600" />
              <div>
                <div className="font-semibold text-green-600">Operational</div>
                <div className="text-sm text-muted-foreground">All systems running</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg">Uptime</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="text-2xl font-bold">99.2%</div>
              <Progress value={99.2} className="h-2" />
              <div className="text-sm text-muted-foreground">Last 30 days</div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg">Active Alerts</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-3">
              <AlertCircle className="h-8 w-8 text-yellow-600" />
              <div>
                <div className="font-semibold">2 Warnings</div>
                <div className="text-sm text-muted-foreground">Require attention</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Health Metrics */}
      <Card>
        <CardHeader>
          <CardTitle>Health Metrics</CardTitle>
          <CardDescription>
            Real-time monitoring of system health indicators
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {healthMetrics.map((metric, index) => (
              <div key={index} className="p-4 border rounded-lg space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <metric.icon className="h-4 w-4 text-muted-foreground" />
                    <span className="font-medium text-sm">{metric.name}</span>
                  </div>
                  {getStatusIcon(metric.status)}
                </div>
                <div className="space-y-1">
                  <div className="text-xl font-bold">{metric.value}</div>
                  <div className="text-xs text-muted-foreground">{metric.description}</div>
                </div>
                <div className="flex items-center justify-between">
                  {getStatusBadge(metric.status)}
                  <div className="flex items-center gap-1 text-xs text-muted-foreground">
                    <Clock className="h-3 w-3" />
                    {metric.lastChecked}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* System Components */}
      <Card>
        <CardHeader>
          <CardTitle>System Components</CardTitle>
          <CardDescription>
            Status of individual system components and services
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {systemComponents.map((component, index) => (
              <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center gap-3">
                  {getStatusIcon(component.status)}
                  <div>
                    <div className="font-medium">{component.name}</div>
                    <div className="text-sm text-muted-foreground">Version {component.version}</div>
                  </div>
                </div>
                <div className="flex items-center gap-6 text-sm">
                  <div className="text-center">
                    <div className="font-medium">{component.uptime}</div>
                    <div className="text-muted-foreground">Uptime</div>
                  </div>
                  <div className="text-center">
                    <div className="font-medium">{component.responseTime}</div>
                    <div className="text-muted-foreground">Response</div>
                  </div>
                  {getStatusBadge(component.status)}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
