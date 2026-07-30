// auth helpers
//
// The JWT lives in localStorage (the axios client reads it there and sends it
// as a Bearer header — the real auth boundary is the API's 401). We ALSO mirror
// it into a readable `token` cookie so Next middleware, which cannot read
// localStorage, can redirect unauthenticated requests for protected pages
// before any HTML ships. The cookie is NOT httpOnly and is client-settable, so
// it is a UX guard (no HTML flash / works with JS disabled), not a security
// boundary. Keep the two in lockstep: every set/clear touches both.

const TOKEN_COOKIE = 'token';

const writeCookie = (token: string) => {
  const secure = window.location.protocol === 'https:' ? '; Secure' : '';
  // Session cookie (no Max-Age) so it clears when the browser closes; SameSite
  // Lax is enough for same-site navigations and blocks CSRF-style cross-site sends.
  document.cookie = `${TOKEN_COOKIE}=${token}; Path=/; SameSite=Lax${secure}`;
};

const clearCookie = () => {
  document.cookie = `${TOKEN_COOKIE}=; Path=/; Max-Age=0; SameSite=Lax`;
};

export const getToken = () => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('token');
  }
  return null;
};

export const setToken = (token: string) => {
  if (typeof window !== 'undefined') {
    localStorage.setItem('token', token);
    writeCookie(token);
  }
};

export const removeToken = () => {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('token');
    clearCookie();
  }
};
