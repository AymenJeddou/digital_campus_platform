import { NextRequest, NextResponse } from 'next/server';
import { SESSION_COOKIE } from '@/lib/session';

// Redirect signed-out visitors before any protected HTML ships. This is a UX
// guard: the backend still checks the token on every API call.
export function proxy(request: NextRequest) {
  if (!request.cookies.has(SESSION_COOKIE)) {
    const login = new URL('/login', request.url);
    login.searchParams.set('next', request.nextUrl.pathname + request.nextUrl.search);
    return NextResponse.redirect(login);
  }
  return NextResponse.next();
}

// Route groups don't appear in URLs, so list the real protected paths.
export const config = {
  matcher: ['/dashboard/:path*', '/chat/:path*', '/courses/:path*', '/profile/:path*', '/onboarding/:path*', '/admin/:path*'],
};
