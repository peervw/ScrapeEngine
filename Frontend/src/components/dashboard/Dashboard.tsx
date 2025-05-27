'use client'

import { useState } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { 
  Activity, 
  Settings, 
  BarChart3
} from 'lucide-react'
import { StatsOverview } from './StatsOverview'
import { JobsTable } from './JobsTable'
import { RunnersTable } from './RunnersTable'
import { SystemHealth } from './SystemHealth'
import { ScrapeHistory } from './ScrapeHistory'
import { APIKeyManager } from './APIKeyManager'

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState('overview')

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Scraper Dashboard</h1>
            <p className="text-muted-foreground">
              Monitor and manage your distributed web scraping system
              <Badge variant="outline" className="ml-2 text-xs">
                Auto-updating
              </Badge>
            </p>
          </div>
        </div>

        {/* Stats Overview */}
        <StatsOverview />

        {/* Main Content */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="overview" className="flex items-center gap-2">
              <Activity className="h-4 w-4" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="jobs" className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Jobs
            </TabsTrigger>
            <TabsTrigger value="runners" className="flex items-center gap-2">
              <Settings className="h-4 w-4" />
              Runners
            </TabsTrigger>
            <TabsTrigger value="history" className="flex items-center gap-2">
              <Activity className="h-4 w-4" />
              History
            </TabsTrigger>
            <TabsTrigger value="settings" className="flex items-center gap-2">
              <Settings className="h-4 w-4" />
              Settings
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview">
            <div className="grid gap-6">
              <SystemHealth />
              <ScrapeHistory />
            </div>
          </TabsContent>

          <TabsContent value="jobs">
            <JobsTable />
          </TabsContent>

          <TabsContent value="runners">
            <RunnersTable />
          </TabsContent>

          <TabsContent value="history">
            <ScrapeHistory />
          </TabsContent>

          <TabsContent value="settings">
            <APIKeyManager />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
