"use client"

import * as React from "react"
import { useEffect, useState, useCallback } from "react"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { api } from "@/lib/api"
import { ScrapeLog, LogsResponse } from "@/lib/api"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Eye, Copy, Check, Trash2 } from "lucide-react"
import { useToast } from "@/components/ui/use-toast"

type BadgeVariant = 'default' | 'secondary' | 'destructive' | 'outline'

interface CopiedStates {
  [key: string]: boolean;
}

export default function LogsPage() {
  const [logsData, setLogsData] = useState<LogsResponse | null>(null)
  const [selectedLog, setSelectedLog] = useState<ScrapeLog | null>(null)
  const [isDetailsOpen, setIsDetailsOpen] = useState(false)
  const [isDeleteConfirmOpen, setIsDeleteConfirmOpen] = useState(false)
  const [isDeleteAllConfirmOpen, setIsDeleteAllConfirmOpen] = useState(false)
  const [copiedStates, setCopiedStates] = useState<CopiedStates>({})
  const { toast } = useToast()

  const handleCopy = async (text: string, key: string) => {
    await navigator.clipboard.writeText(text)
    setCopiedStates((prev: CopiedStates) => ({ ...prev, [key]: true }))
    setTimeout(() => setCopiedStates((prev: CopiedStates) => ({ ...prev, [key]: false })), 2000)
  }

  const handleDeleteLog = async (logId: number) => {
    try {
      await api.deleteLog(logId)
      toast({
        title: "Success",
        description: "Log entry deleted successfully",
        duration: 3000,
      })
      fetchLogs()
    } catch (err) {
      console.error('Failed to delete log:', err)
      toast({
        title: "Error",
        description: "Failed to delete log entry",
        variant: "destructive",
        duration: 3000,
      })
    }
  }

  const handleDeleteAllLogs = async () => {
    try {
      await api.deleteAllLogs()
      toast({
        title: "Success",
        description: "All logs deleted successfully",
        duration: 3000,
      })
      fetchLogs()
    } catch (err) {
      console.error('Failed to delete all logs:', err)
      toast({
        title: "Error",
        description: "Failed to delete logs",
        variant: "destructive",
        duration: 3000,
      })
    }
  }

  const fetchLogs = useCallback(async () => {
    try {
      const data = await api.getScrapeLogs()
      setLogsData(data)
    } catch (error) {
      console.error('Failed to fetch logs:', error)
    }
  }, [])

  useEffect(() => {
    fetchLogs()
    const interval = setInterval(fetchLogs, 5000)
    return () => clearInterval(interval)
  }, [fetchLogs])

  const getBadgeVariant = (status: string): BadgeVariant => {
    return status === 'success' ? 'default' : 'destructive'
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Scraping Logs</h1>
        <div className="flex items-center gap-4">
          <Badge variant="outline">Live Updates</Badge>
          <Button 
            variant="destructive" 
            size="sm"
            onClick={() => setIsDeleteAllConfirmOpen(true)}
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Delete All Logs
          </Button>
        </div>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Timestamp</TableHead>
              <TableHead>Runner ID</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>URL</TableHead>
              <TableHead>Duration (s)</TableHead>
              <TableHead>Details</TableHead>
              <TableHead className="w-[100px]">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {logsData?.logs.map((log: ScrapeLog) => (
              <TableRow key={log.timestamp}>
                <TableCell>{new Date(log.timestamp).toLocaleString()}</TableCell>
                <TableCell>{log.runner_id}</TableCell>
                <TableCell>
                  <Badge variant={getBadgeVariant(log.status)}>
                    {log.status}
                  </Badge>
                </TableCell>
                <TableCell className="max-w-[200px] truncate">{log.url}</TableCell>
                <TableCell>{log.duration?.toFixed(2) || '-'}</TableCell>
                <TableCell className="max-w-[200px] truncate">{log.details}</TableCell>
                <TableCell>
                  <div className="flex gap-2">
                    <Button variant="ghost" size="icon" onClick={() => { setSelectedLog(log); setIsDetailsOpen(true); }}>
                      <Eye className="h-4 w-4" />
                    </Button>
                    <Button 
                      variant="ghost" 
                      size="icon"
                      onClick={() => {
                        setSelectedLog(log)
                        setIsDeleteConfirmOpen(true)
                      }}
                    >
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
            {(!logsData?.logs || logsData.logs.length === 0) && (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-4 text-muted-foreground">
                  No logs available
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      <Dialog open={isDetailsOpen} onOpenChange={setIsDetailsOpen}>
        <DialogContent className="sm:max-w-[600px] md:max-w-[800px] lg:max-w-[900px]">
          <DialogHeader>
            <DialogTitle>Scraping Details</DialogTitle>
          </DialogHeader>
          {selectedLog && (
            <div className="relative w-full">
              <ScrollArea className="h-[80vh]">
                <div className="flex flex-col gap-4 pr-6">
                  <div>
                    <h3 className="font-semibold mb-2">Basic Information</h3>
                    <div className="grid grid-cols-[120px,1fr] gap-2 text-sm">
                      <div className="font-medium">Timestamp</div>
                      <div className="text-right">{new Date(selectedLog.timestamp).toLocaleString()}</div>
                      <div className="font-medium">Runner ID</div>
                      <div className="text-right">{selectedLog.runner_id}</div>
                      <div className="font-medium">Status</div>
                      <div className="text-right">
                        <Badge variant={getBadgeVariant(selectedLog.status)}>
                          {selectedLog.status}
                        </Badge>
                      </div>
                      <div className="font-medium">URL</div>
                      <div className="text-right break-words">{selectedLog.url}</div>
                      <div className="font-medium">Duration</div>
                      <div className="text-right">{selectedLog.duration?.toFixed(2) || '-'} seconds</div>
                    </div>
                  </div>

                  {selectedLog.config && (
                    <div>
                      <h3 className="font-semibold mb-2">Configuration Used</h3>
                      <div className="grid grid-cols-[120px,1fr] gap-2 text-sm">
                        <div className="font-medium">URL</div>
                        <div className="text-right break-words">{selectedLog.config.url}</div>
                        <div className="font-medium">Stealth Mode</div>
                        <div className="text-right">{selectedLog.config.stealth ? "Yes" : "No"}</div>
                        <div className="font-medium">Use Playwright</div>
                        <div className="text-right">{selectedLog.config.render ? "Yes" : "No"}</div>
                        <div className="font-medium">Parse Content</div>
                        <div className="text-right">{selectedLog.config.parse ? "Yes" : "No"}</div>
                        <div className="font-medium">Proxy</div>
                        <div className="text-right break-words">{selectedLog.config.proxy}</div>
                      </div>
                    </div>
                  )}

                  {selectedLog.result && (
                    <div>
                      <h3 className="font-semibold mb-2">Response Data</h3>
                      <div className="grid grid-cols-[120px,1fr] gap-2 text-sm mb-4">
                        <div className="font-medium">Proxy Used</div>
                        <div className="text-right break-words">{selectedLog.result.proxy_used}</div>
                        <div className="font-medium">Runner Used</div>
                        <div className="text-right break-words">{selectedLog.result.runner_used}</div>
                        <div className="font-medium">Method Used</div>
                        <div className="text-right">{selectedLog.result.method_used}</div>
                        <div className="font-medium">Response Time</div>
                        <div className="text-right">{selectedLog.result.response_time?.toFixed(2)}s</div>
                      </div>

                      {selectedLog.result?.content && (
                        <div className="space-y-4">
                          <div>
                            <div className="flex justify-between items-center mb-2">
                              <h4 className="font-medium">Title</h4>
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => handleCopy(selectedLog.result?.content?.title || '', 'title')}
                                className="h-6 w-6"
                              >
                                {copiedStates['title'] ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                              </Button>
                            </div>
                            <div className="bg-muted p-2 rounded-md break-words">
                              {selectedLog.result?.content?.title || 'No title found'}
                            </div>
                          </div>

                          {selectedLog.result?.content?.text_content && (
                            <div>
                              <div className="flex justify-between items-center mb-2">
                                <h4 className="font-medium">Text Content</h4>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  onClick={() => handleCopy(selectedLog.result?.content?.text_content || '', 'text')}
                                  className="h-6 w-6"
                                >
                                  {copiedStates['text'] ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                                </Button>
                              </div>
                              <div className="bg-muted p-2 rounded-md max-h-[200px] overflow-auto break-words">
                                {selectedLog.result?.content?.text_content}
                              </div>
                            </div>
                          )}

                          {selectedLog.result?.content?.links && selectedLog.result?.content?.links.length > 0 && (
                            <div>
                              <div className="flex justify-between items-center mb-2">
                                <h4 className="font-medium">Links</h4>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  onClick={() => handleCopy(
                                    selectedLog.result?.content?.links?.map((link: { text: string; href: string }) => `${link.text} - ${link.href}`).join('\n') || '',
                                    'links'
                                  )}
                                  className="h-6 w-6"
                                >
                                  {copiedStates['links'] ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                                </Button>
                              </div>
                              <div className="bg-muted p-2 rounded-md max-h-[200px] overflow-auto">
                                <ul className="list-disc list-inside space-y-1">
                                  {selectedLog.result?.content?.links.map((link: { text: string; href: string }, index: number) => (
                                    <li key={index}>
                                      <span className="font-mono text-sm break-all">
                                        {link.text} - {link.href}
                                      </span>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            </div>
                          )}

                          {selectedLog.result?.content?.parse_error && (
                            <div>
                              <h4 className="font-medium mb-2 text-destructive">Parse Error</h4>
                              <div className="bg-destructive/10 text-destructive p-2 rounded-md break-words text-right">
                                {selectedLog.result?.content?.parse_error}
                              </div>
                            </div>
                          )}

                          <div>
                            <div className="flex justify-between items-center mb-2">
                              <h4 className="font-medium">Raw Content</h4>
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => handleCopy(selectedLog.result?.content?.raw_content || '', 'raw')}
                                className="h-6 w-6"
                              >
                                {copiedStates['raw'] ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                              </Button>
                            </div>
                            <pre className="bg-muted p-2 rounded-md overflow-auto text-sm max-h-[200px] whitespace-pre-wrap">
                              {selectedLog.result?.content?.raw_content}
                            </pre>
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {selectedLog.error && (
                    <div>
                      <h3 className="font-semibold mb-2 text-destructive">Error Details</h3>
                      <pre className="bg-destructive/10 text-destructive p-4 rounded-md text-sm whitespace-pre-wrap text-right">
                        {selectedLog.error}
                      </pre>
                    </div>
                  )}
                </div>
              </ScrollArea>
            </div>
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={isDeleteConfirmOpen} onOpenChange={setIsDeleteConfirmOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Log Entry</DialogTitle>
          </DialogHeader>
          <p>Are you sure you want to delete this log entry? This action cannot be undone.</p>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDeleteConfirmOpen(false)}>Cancel</Button>
            <Button 
              variant="destructive" 
              onClick={() => {
                if (selectedLog?.id) {
                  handleDeleteLog(selectedLog.id)
                  setIsDeleteConfirmOpen(false)
                }
              }}
            >
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={isDeleteAllConfirmOpen} onOpenChange={setIsDeleteAllConfirmOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete All Logs</DialogTitle>
          </DialogHeader>
          <p>Are you sure you want to delete all log entries? This action cannot be undone.</p>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDeleteAllConfirmOpen(false)}>Cancel</Button>
            <Button 
              variant="destructive" 
              onClick={() => {
                handleDeleteAllLogs()
                setIsDeleteAllConfirmOpen(false)
              }}
            >
              Delete All
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}