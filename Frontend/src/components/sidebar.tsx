import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { 
  LayoutDashboard, 
  Plus, 
  ScrollText, 
  Activity,
  Settings
} from "lucide-react"

const routes = [
  {
    label: "Dashboard",
    icon: LayoutDashboard,
    href: "/",
    color: "text-sky-500",
  },
  {
    label: "New Scrape",
    icon: Plus,
    href: "/scrape",
    color: "text-violet-500",
  },
  {
    label: "Logs",
    icon: ScrollText,
    color: "text-pink-700",
    href: "/logs",
  },
  {
    label: "Runner Health",
    icon: Activity,
    color: "text-orange-700",
    href: "/health",
  },
  {
    label: "Settings",
    icon: Settings,
    color: "text-gray-500",
    href: "/settings",
  }
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <div className="space-y-4 py-4 flex flex-col h-full bg-[#111827] text-white">
      <div className="px-3 py-2 flex-1">
        <Link href="/" className="flex items-center pl-3 mb-14">
          <h1 className="text-2xl font-bold">
            ScrapeEngine
          </h1>
        </Link>
        <div className="space-y-1">
          {routes.map((route) => (
            <Link
              key={route.href}
              href={route.href}
              className={cn(
                "text-sm group flex p-3 w-full justify-start font-medium cursor-pointer hover:text-white hover:bg-white/10 rounded-lg transition",
                pathname === route.href ? "text-white bg-white/10" : "text-zinc-400",
              )}
            >
              <div className="flex items-center flex-1">
                <route.icon className={cn("h-5 w-5 mr-3", route.color)} />
                {route.label}
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
} 