import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { MainNav } from "@/components/layout/main-nav";
import { cn } from "@/lib/utils";
import { Toaster } from "@/components/ui/toaster";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "ScrapeEngine Dashboard",
  description: "Monitor and manage your scraping operations",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={cn(
        "min-h-screen bg-background font-sans antialiased",
        inter.className
      )}>
        <div className="relative flex min-h-screen flex-col">
          <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
            <div className="container flex h-14 max-w-screen-2xl items-center px-8">
              <MainNav />
            </div>
          </header>
          <main className="flex-1">
            <div className="container max-w-screen-2xl px-8 py-6">
              {children}
            </div>
          </main>
        </div>
        <Toaster />
      </body>
    </html>
  );
}
