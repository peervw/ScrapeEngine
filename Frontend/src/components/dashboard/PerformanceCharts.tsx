'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar
} from 'recharts'

const performanceData = [
  { time: '00:00', jobs: 4, pages: 120, errors: 2 },
  { time: '04:00', jobs: 6, pages: 180, errors: 1 },
  { time: '08:00', jobs: 12, pages: 360, errors: 3 },
  { time: '12:00', jobs: 15, pages: 450, errors: 2 },
  { time: '16:00', jobs: 18, pages: 540, errors: 4 },
  { time: '20:00', jobs: 14, pages: 420, errors: 1 },
  { time: '24:00', jobs: 8, pages: 240, errors: 2 }
]

const responseTimeData = [
  { time: '00:00', avgResponse: 1.2, p95Response: 2.1 },
  { time: '04:00', avgResponse: 1.1, p95Response: 1.9 },
  { time: '08:00', avgResponse: 1.4, p95Response: 2.3 },
  { time: '12:00', avgResponse: 1.6, p95Response: 2.8 },
  { time: '16:00', avgResponse: 1.8, p95Response: 3.2 },
  { time: '20:00', avgResponse: 1.3, p95Response: 2.2 },
  { time: '24:00', avgResponse: 1.1, p95Response: 1.8 }
]

const successRateData = [
  { time: '00:00', success: 96.5, failed: 3.5 },
  { time: '04:00', success: 98.2, failed: 1.8 },
  { time: '08:00', success: 94.7, failed: 5.3 },
  { time: '12:00', success: 97.1, failed: 2.9 },
  { time: '16:00', success: 93.8, failed: 6.2 },
  { time: '20:00', success: 98.8, failed: 1.2 },
  { time: '24:00', success: 97.3, failed: 2.7 }
]

export function PerformanceCharts() {
  return (
    <div className="grid gap-6 md:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Jobs & Pages Over Time</CardTitle>
          <CardDescription>
            Track the number of active jobs and pages scraped throughout the day
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={performanceData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Line 
                type="monotone" 
                dataKey="jobs" 
                stroke="#8884d8" 
                strokeWidth={2}
                name="Active Jobs"
              />
              <Line 
                type="monotone" 
                dataKey="pages" 
                stroke="#82ca9d" 
                strokeWidth={2}
                name="Pages Scraped"
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Response Times</CardTitle>
          <CardDescription>
            Average and 95th percentile response times
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={responseTimeData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Area 
                type="monotone" 
                dataKey="avgResponse" 
                stackId="1" 
                stroke="#8884d8" 
                fill="#8884d8"
                name="Average Response (s)"
              />
              <Area 
                type="monotone" 
                dataKey="p95Response" 
                stackId="2" 
                stroke="#82ca9d" 
                fill="#82ca9d"
                name="95th Percentile (s)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Success Rate</CardTitle>
          <CardDescription>
            Percentage of successful vs failed scraping attempts
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={successRateData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Area 
                type="monotone" 
                dataKey="success" 
                stackId="1" 
                stroke="#10b981" 
                fill="#10b981"
                name="Success Rate (%)"
              />
              <Area 
                type="monotone" 
                dataKey="failed" 
                stackId="1" 
                stroke="#ef4444" 
                fill="#ef4444"
                name="Failure Rate (%)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Error Distribution</CardTitle>
          <CardDescription>
            Number of errors encountered over time
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={performanceData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Bar 
                dataKey="errors" 
                fill="#ef4444"
                name="Errors"
              />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  )
}
