"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Loader2 } from "lucide-react"
import { ScrapingResult, api } from "@/lib/api"

export default function ScrapePage() {
  const [url, setUrl] = useState("")
  const [stealth, setStealth] = useState(false)
  const [render, setRender] = useState(false)
  const [parse, setParse] = useState(true)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<ScrapingResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const data = await api.submitScrapeRequest({
        url,
        stealth,
        render,
        parse
      })
      setResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to scrape')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Scrape Request</h1>

      <form onSubmit={handleSubmit} className="space-y-8">
        <Card>
          <CardHeader>
            <CardTitle>URL Configuration</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid w-full items-center gap-1.5">
              <Label htmlFor="url">URL to Scrape</Label>
              <Input
                id="url"
                type="url"
                placeholder="https://example.com"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                required
              />
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label htmlFor="stealth">Stealth Mode</Label>
                <Switch
                  id="stealth"
                  checked={stealth}
                  onCheckedChange={setStealth}
                />
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="render">Use Playwright</Label>
                <Switch
                  id="render"
                  checked={render}
                  onCheckedChange={setRender}
                />
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="parse">Parse Content</Label>
                <Switch
                  id="parse"
                  checked={parse}
                  onCheckedChange={setParse}
                />
              </div>
            </div>

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Scraping...
                </>
              ) : (
                'Start Scraping'
              )}
            </Button>
          </CardContent>
        </Card>
      </form>

      {error && (
        <Alert variant="destructive">
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {result && (
        <Card>
          <CardHeader>
            <CardTitle>Scraping Result</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="whitespace-pre-wrap bg-secondary p-4 rounded-lg text-sm">
              {JSON.stringify(result, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  )
} 