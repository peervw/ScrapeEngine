import Link from 'next/link'

const links = [
  { name: "Dashboard", href: "/" },
  { name: "New Scrape", href: "/scrape" },
  { name: "Logs", href: "/logs" },
  { name: "Settings", href: "/settings" }
]

export function Nav() {
  return (
    <nav className="flex items-center space-x-4">
      {links.map((link) => (
        <Link
          key={link.href}
          href={link.href}
          className="text-sm font-medium text-muted-foreground hover:text-foreground"
        >
          {link.name}
        </Link>
      ))}
    </nav>
  )
} 