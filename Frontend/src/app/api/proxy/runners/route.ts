const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://distributor:8080'

export async function GET() {
  try {
    const response = await fetch(`${BACKEND_URL}/api/runners`, {
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.json()
    return Response.json(data)
  } catch (error) {
    console.error('Failed to fetch runners:', error)
    return Response.json({ error: 'Failed to fetch runners' }, { status: 500 })
  }
}
