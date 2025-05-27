'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { 
  MoreHorizontal, 
  Activity, 
  Cpu,
  HardDrive,
  Wifi,
  Power,
  PowerOff
} from 'lucide-react'
import { useRunners } from '@/hooks/useApi'

export function RunnersTable() {
  const { runners, loading, error } = useRunners()

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800'
      case 'idle':
        return 'bg-yellow-100 text-yellow-800'
      case 'offline':
        return 'bg-gray-100 text-gray-800'
      case 'error':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getUsageColor = (usage: number) => {
    if (usage > 80) return 'text-red-600'
    if (usage > 60) return 'text-yellow-600'
    return 'text-green-600'
  }

  const formatLastHeartbeat = (heartbeat: string) => {
    try {
      const date = new Date(heartbeat)
      const now = new Date()
      const diffMs = now.getTime() - date.getTime()
      const diffSecs = Math.floor(diffMs / 1000)
      
      if (diffSecs < 60) return `${diffSecs} seconds ago`
      if (diffSecs < 3600) return `${Math.floor(diffSecs / 60)} minutes ago`
      return `${Math.floor(diffSecs / 3600)} hours ago`
    } catch {
      return heartbeat
    }
  }

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Runners</CardTitle>
          <CardDescription>Manage distributed scraping runners</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">Loading runners...</div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Runners</CardTitle>
          <CardDescription>Manage distributed scraping runners</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-red-500">
            Error loading runners: {error}
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Runners</CardTitle>
        <CardDescription>
          {runners.length} runner{runners.length !== 1 ? 's' : ''} registered
        </CardDescription>
      </CardHeader>
      <CardContent>
        {runners.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            No runners registered yet. Make sure your runners are connecting to the distributor.
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Runner</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Current Job</TableHead>
                <TableHead>System Stats</TableHead>
                <TableHead>Completed Jobs</TableHead>
                <TableHead>Last Heartbeat</TableHead>
                <TableHead>Version</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {runners.map((runner) => (
                <TableRow key={runner.id}>
                  <TableCell>
                    <div className="flex items-center gap-3">
                      <Activity className="h-4 w-4 text-muted-foreground" />
                      <div>
                        <div className="font-medium">{runner.name}</div>
                        <div className="text-sm text-muted-foreground">{runner.id}</div>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge className={getStatusColor(runner.status)}>
                      {runner.status}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="max-w-32 truncate">
                      {runner.current_job ? (
                        <span className="text-sm">{runner.current_job}</span>
                      ) : (
                        <span className="text-sm text-muted-foreground">None</span>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 text-xs">
                        <Cpu className="h-3 w-3" />
                        <span className={getUsageColor(runner.cpu_usage)}>
                          {runner.cpu_usage}%
                        </span>
                      </div>
                      <div className="flex items-center gap-2 text-xs">
                        <HardDrive className="h-3 w-3" />
                        <span className={getUsageColor(runner.memory_usage)}>
                          {runner.memory_usage}%
                        </span>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <span className="font-medium">{runner.completed_jobs}</span>
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    <div className="flex items-center gap-2">
                      <Wifi className="h-3 w-3" />
                      {formatLastHeartbeat(runner.last_heartbeat)}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="text-sm">{runner.version}</div>
                    <div className="text-xs text-muted-foreground">
                      Uptime: {runner.uptime}
                    </div>
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" className="h-8 w-8 p-0">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem>
                          <Power className="mr-2 h-4 w-4" />
                          Restart Runner
                        </DropdownMenuItem>
                        <DropdownMenuItem className="text-red-600">
                          <PowerOff className="mr-2 h-4 w-4" />
                          Stop Runner
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  )
}
