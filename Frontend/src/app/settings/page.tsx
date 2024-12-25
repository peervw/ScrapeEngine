"use client"

import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { toast } from "sonner"

export default function SettingsPage() {
  const [logRetentionDays, setLogRetentionDays] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [apiKey, setApiKey] = useState<string | null>(null)
  const [showApiKey, setShowApiKey] = useState(false)
  const [isLoadingKey, setIsLoadingKey] = useState(true)

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const settings = await api.getSettings()
        setLogRetentionDays(settings.log_retention_days)
      } catch (error) {
        console.error('Failed to fetch settings:', error)
        toast.error('Failed to load settings')
      }
    }
    fetchSettings()
  }, [])

  useEffect(() => {
    const fetchApiKey = async () => {
      try {
        const apiKeyData = await api.getApiKey()
        setApiKey(apiKeyData.key)
      } catch (error) {
        console.error('Failed to fetch API key:', error)
        // Don't show error toast as this is expected when no key exists
      } finally {
        setIsLoadingKey(false)
      }
    }
    fetchApiKey()
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    try {
      await api.updateSettings({
        log_retention_days: logRetentionDays
      })
      toast.success('Settings updated successfully')
    } catch (error) {
      console.error('Failed to update settings:', error)
      toast.error('Failed to update settings')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Settings</h1>

      <Card>
        <CardHeader>
          <CardTitle>System Configuration</CardTitle>
          <CardDescription>
            Configure system-wide settings for the scraping engine
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="logRetention">Log Retention (days)</Label>
              <Input
                id="logRetention"
                type="number"
                min="1"
                max="90"
                value={logRetentionDays}
                onChange={(e) => setLogRetentionDays(e.target.value)}
                placeholder="Enter log retention period in days"
              />
            </div>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? "Saving..." : "Save Settings"}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>API Key Management</CardTitle>
          <CardDescription>
            Manage your API key for accessing the scraping engine
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center space-x-4">
              <div className="flex-1 font-mono bg-background border rounded-md">
                <div className="px-3 py-2 overflow-x-auto">
                  {isLoadingKey ? (
                    "Loading..."
                  ) : apiKey ? (
                    showApiKey ? apiKey : "•".repeat(64)
                  ) : (
                    "No API key exists yet. Click 'Regenerate' to create one."
                  )}
                </div>
              </div>
              <Button
                variant="outline"
                onClick={() => setShowApiKey(!showApiKey)}
                disabled={!apiKey}
              >
                {showApiKey ? "Hide" : "Show"}
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  if (apiKey) {
                    navigator.clipboard.writeText(apiKey)
                    toast.success('API key copied to clipboard')
                  }
                }}
                disabled={!apiKey}
              >
                Copy
              </Button>
              <Button
                variant="destructive"
                onClick={async () => {
                  if (apiKey && !confirm("Are you sure you want to regenerate your API key? The old key will stop working immediately.")) {
                    return
                  }
                  setIsLoading(true)
                  try {
                    const newKey = await api.regenerateApiKey()
                    setApiKey(newKey.key)
                    setShowApiKey(true)  // Show the new key automatically
                    toast.success('New API key generated')
                  } catch (error) {
                    console.error('Failed to regenerate API key:', error)
                    toast.error('Failed to generate new API key')
                  } finally {
                    setIsLoading(false)
                  }
                }}
                disabled={isLoading}
              >
                {apiKey ? 'Regenerate' : 'Generate'}
              </Button>
            </div>
            <p className="text-sm text-muted-foreground">
              This API key is required to authenticate requests to the scraping engine. Keep it secure and do not share it.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 