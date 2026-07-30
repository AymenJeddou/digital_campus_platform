import { NextRequest, NextResponse } from 'next/server';

// Server-side guard for protected pages. Middleware can only read cookies (not
// localStorage), so it checks the `token` cookie that `setToken` mirrors. This
// redirects unauthenticated requests BEFORE any HTML ships (no dashboard-shell
// flash, works with JS disabled). It is a UX guard, NOT the security boundary —
// the cookie is client-settable; the real protection is the API's 401 and the
// backend's own route guard. The client-side layout guard stays as a 2nd layer.
export function middleware(request: NextRequest) {
  const token = request.cookies.get('token')?.value;
  if (!token) {
    const loginUrl = new URL('/login', request.url);
    return NextResponse.redirect(loginUrl);
  }
  return NextResponse.next();
}

// Match the real protected URLs. The pages live in the (protected) route group,
// but route groups don't appear in the URL — the matcher must list actual paths.
export const config = {
  matcher: [
    '/dashboard/:path*',
    '/chat/:path*',
    '/courses/:path*',
    '/profile/:path*',
    '/onboarding/:path*',
  ],
};
