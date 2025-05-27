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
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Clock, Globe, Zap, AlertCircle, Eye, Server, Timer } from 'lucide-react'
import { useScrapeHistory } from '@/hooks/useApi'
import { ScrapeRecord } from '@/lib/api'

interface ScrapeDetailsProps {
  scrape: ScrapeRecord
}

function ScrapeDetails({ scrape }: ScrapeDetailsProps) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <h4 className="text-sm font-semibold mb-2">Request Details</h4>
          <div className="space-y-1 text-sm">
            <div><span className="font-medium">URL:</span> {scrape.url}</div>
            <div><span className="font-medium">Method:</span> {scrape.method.toUpperCase()}</div>
            <div><span className="font-medium">Status:</span> 
              <Badge className={`ml-2 ${getStatusColor(scrape.status)}`}>
                {scrape.status}
              </Badge>
            </div>
          </div>
        </div>
        <div>
          <h4 className="text-sm font-semibold mb-2">Performance</h4>
          <div className="space-y-1 text-sm">
            <div><span className="font-medium">Response Time:</span> {formatResponseTime(scrape.response_time)}</div>
            <div><span className="font-medium">Content Length:</span> {formatBytes(scrape.content_length)}</div>
            <div><span className="font-medium">Runner:</span> {scrape.runner_id || 'Unknown'}</div>
            <div><span className="font-medium">Proxy:</span> {scrape.proxy_used || 'None'}</div>
          </div>
        </div>
      </div>
      
      {scrape.error_message && (
        <div>
          <h4 className="text-sm font-semibold mb-2 text-red-600">Error Details</h4>
          <div className="p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
            {scrape.error_message}
          </div>
        </div>
      )}

      <div>
        <h4 className="text-sm font-semibold mb-2">Additional Information</h4>
        <div className="space-y-1 text-sm">
          <div><span className="font-medium">Scrape ID:</span> {scrape.id}</div>
          <div><span className="font-medium">Created:</span> {new Date(scrape.created_at).toLocaleString()}</div>
          {scrape.api_key_id && (
            <div><span className="font-medium">API Key:</span> {scrape.api_key_id}</div>
          )}
        </div>
      </div>
    </div>
  )
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'success':
      return 'bg-green-100 text-green-800'
    case 'failed':
      return 'bg-red-100 text-red-800'
    case 'timeout':
      return 'bg-yellow-100 text-yellow-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

const formatBytes = (bytes?: number) => {
  if (!bytes) return 'N/A'
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  if (bytes === 0) return '0 Bytes'
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
}

const formatResponseTime = (time?: number) => {
  if (!time) return 'N/A'
  if (time < 1) return `${Math.round(time * 1000)}ms`
  return `${time.toFixed(2)}s`
}

export function ScrapeHistory() {
  const { scrapes, loading, error } = useScrapeHistory(true, 5000) // Auto-refresh every 5 seconds

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <Zap className="h-3 w-3" />
      case 'failed':
        return <AlertCircle className="h-3 w-3" />
      case 'timeout':
        return <Clock className="h-3 w-3" />
      default:
        return <Globe className="h-3 w-3" />
    }
  }

  const formatTime = (timeString: string) => {
    try {
      const date = new Date(timeString)
      const now = new Date()
      const diffMs = now.getTime() - date.getTime()
      const diffMins = Math.floor(diffMs / 60000)
      
      if (diffMins < 1) return 'Just now'
      if (diffMins < 60) return `${diffMins}m ago`
      if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`
      return date.toLocaleDateString()
    } catch {
      return timeString
    }
  }

  const formatUrl = (url: string) => {
    try {
      const urlObj = new URL(url)
      return `${urlObj.hostname}${urlObj.pathname}`
    } catch {
      return url
    }
  }

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Timer className="h-5 w-5" />
            Recent Scrapes
            <Badge variant="outline" className="text-xs">
              Auto-refreshing
            </Badge>
          </CardTitle>
          <CardDescription>Latest scraping activity</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">Loading scrape history...</div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Timer className="h-5 w-5" />
            Recent Scrapes
            <Badge variant="outline" className="text-xs">
              Auto-refreshing
            </Badge>
          </CardTitle>
          <CardDescription>Latest scraping activity</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-red-500">
            Error loading scrape history: {error}
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Timer className="h-5 w-5" />
          Recent Scrapes
          <Badge variant="outline" className="text-xs">
            Auto-refreshing every 5s
          </Badge>
        </CardTitle>
        <CardDescription>
          {scrapes.length} recent scraping {scrapes.length !== 1 ? 'operations' : 'operation'}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {scrapes.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            No scrapes yet. Start scraping to see activity here.
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>URL</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Method</TableHead>
                <TableHead>Response Time</TableHead>
                <TableHead>Runner</TableHead>
                <TableHead>Time</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {scrapes.map((scrape) => (
                <TableRow key={scrape.id}>
                  <TableCell>
                    <div className="flex items-center space-x-2">
                      <Globe className="h-4 w-4 text-muted-foreground" />
                      <div>
                        <div className="font-medium text-sm">
                          {formatUrl(scrape.url)}
                        </div>
                        {scrape.error_message && (
                          <div className="text-xs text-red-500 truncate max-w-48">
                            {scrape.error_message}
                          </div>
                        )}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge className={getStatusColor(scrape.status)}>
                      <div className="flex items-center space-x-1">
                        {getStatusIcon(scrape.status)}
                        <span>{scrape.status}</span>
                      </div>
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <span className="text-sm font-mono">
                      {scrape.method.toUpperCase()}
                    </span>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center space-x-1">
                      <Timer className="h-3 w-3 text-muted-foreground" />
                      <span className="text-sm">
                        {formatResponseTime(scrape.response_time)}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center space-x-1">
                      <Server className="h-3 w-3 text-muted-foreground" />
                      <span className="text-sm text-muted-foreground">
                        {scrape.runner_id || 'Unknown'}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <span className="text-sm text-muted-foreground">
                      {formatTime(scrape.created_at)}
                    </span>
                  </TableCell>
                  <TableCell>
                    <Dialog>
                      <DialogTrigger asChild>
                        <Button variant="outline" size="sm">
                          <Eye className="h-3 w-3 mr-1" />
                          Details
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="max-w-2xl">
                        <DialogHeader>
                          <DialogTitle>Scrape Details</DialogTitle>
                          <DialogDescription>
                            Detailed information about this scraping operation
                          </DialogDescription>
                        </DialogHeader>
                        <ScrapeDetails scrape={scrape} />
                      </DialogContent>
                    </Dialog>
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
