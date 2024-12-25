"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"

const items = [
  {
    title: "Dashboard",
    href: "/",
  },
  {
    title: "Scraping Logs",
    href: "/logs",
  },
  {
    title: "Runner Health",
    href: "/runners",
  },
  {
    title: "System Status",
    href: "/system",
  },
  {
    title: "Proxies",
    href: "/proxies",
  },
  {
    title: "New Scrape",
    href: "/scrape",
  },
  {
    title: "Settings",
    href: "/settings",
  },
]

export function MainNav() {
  const pathname = usePathname()

  return (
    <nav className="flex items-center space-x-4 lg:space-x-6">
      {items.map((item) => (
        <Link
          key={item.href}
          href={item.href}
          className={cn(
            "text-sm font-medium transition-colors hover:text-primary",
            pathname === item.href
              ? "text-primary"
              : "text-muted-foreground"
          )}
        >
          {item.title}
        </Link>
      ))}
    </nav>
  )
} 