import { redirect } from 'next/navigation'
import { stackServerApp } from '@/stack'
import Dashboard from '@/components/dashboard/Dashboard'

export default async function Home() {
  const user = await stackServerApp.getUser()
  
  if (!user) {
    redirect('/handler/sign-in')
  }

  return <Dashboard />
}