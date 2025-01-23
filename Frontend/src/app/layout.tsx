import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "ScrapeEngine Dashboard",
  description: "Monitor and manage your scraping operations",
}

export default function Layout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="m-0 p-0">
        {children}
      </body>
    </html>
  )
}
