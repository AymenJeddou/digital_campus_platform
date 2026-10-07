// Backend proxy (backend-for-frontend). The browser only ever talks to this
// origin; the login token lives in an httpOnly cookie that page scripts can't
// read, and is attached here as a Bearer header. Streams (SSE) pass through.
import { NextRequest, NextResponse } from 'next/server';
import { SESSION_COOKIE } from '@/lib/session';

const API_URL = (process.env.API_URL ?? 'http://localhost:8000').replace(/\/$/, '');
const PASS_HEADERS = ['content-type', 'cache-control', 'content-disposition'];

function tokenExpiry(token: string): Date | undefined {
  try {
    const payload = JSON.parse(Buffer.from(token.split('.')[1], 'base64url').toString());
    return typeof payload.exp === 'number' ? new Date(payload.exp * 1000) : undefined;
  } catch {
    return undefined;
  }
}

async function handle(req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  const { path } = await ctx.params;
  const route = path.join('/');
  const headers = new Headers();
  for (const name of ['content-type', 'accept', 'x-forwarded-for']) {
    const value = req.headers.get(name);
    if (value) headers.set(name, value);
  }
  const token = req.cookies.get(SESSION_COOKIE)?.value;
  if (token) headers.set('authorization', `Bearer ${token}`);

  let upstream: Response;
  try {
    upstream = await fetch(`${API_URL}/${path.map(encodeURIComponent).join('/')}${req.nextUrl.search}`, {
      method: req.method,
      headers,
      body: req.method === 'GET' || req.method === 'HEAD' ? undefined : await req.arrayBuffer(),
      redirect: 'manual',
      cache: 'no-store',
    });
  } catch {
    return NextResponse.json({ detail: 'Backend unreachable' }, { status: 502 });
  }

  const secure = req.nextUrl.protocol === 'https:';
  if (route === 'auth/login' && upstream.ok) {
    const { access_token } = await upstream.json();
    const res = NextResponse.json({ ok: true });
    res.cookies.set(SESSION_COOKIE, access_token, {
      httpOnly: true,
      sameSite: 'lax',
      secure,
      path: '/',
      expires: tokenExpiry(access_token),
    });
    return res;
  }

  const res = new NextResponse(upstream.body, { status: upstream.status });
  for (const name of PASS_HEADERS) {
    const value = upstream.headers.get(name);
    if (value) res.headers.set(name, value);
  }
  if (res.headers.get('content-type')?.includes('text/event-stream')) {
    res.headers.set('cache-control', 'no-cache, no-transform');
    res.headers.set('x-accel-buffering', 'no');
  }
  // A logout, or a token the backend no longer accepts, ends the session here too.
  if (route === 'auth/logout' || upstream.status === 401) res.cookies.delete(SESSION_COOKIE);
  return res;
}

export { handle as GET, handle as POST, handle as PATCH, handle as DELETE, handle as PUT };
