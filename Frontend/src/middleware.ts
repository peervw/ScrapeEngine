import { NextResponse } from 'next/server';

export function middleware() {
  // For all paths, let the client-side handle auth redirects
  // This is because we can't access localStorage from middleware
  return NextResponse.next();
}

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico).*)',
  ],
};