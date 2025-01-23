import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
    // Get the pathname of the request
    const path = request.nextUrl.pathname;

    // Define public paths that don't require authentication
    const isPublicPath = path === '/login';

    // Check if user is authenticated
    const token = request.cookies.get('pb_auth')?.value;

    // Redirect authenticated users away from public paths
    if (isPublicPath && token) {
        return NextResponse.redirect(new URL('/', request.url));
    }

    // Redirect unauthenticated users to login
    if (!isPublicPath && !token) {
        return NextResponse.redirect(new URL('/login', request.url));
    }

    return NextResponse.next();
}

// Configure which paths should be protected
export const config = {
    matcher: [
        /*
         * Match all request paths except for the ones starting with:
         * - login (public)
         * - health/public (public API endpoint)
         * - _next/static (static files)
         * - _next/image (image optimization files)
         * - favicon.ico (favicon file)
         */
        '/((?!login|_next/static|_next/image|favicon.ico|health/public).*)',
    ],
}; 