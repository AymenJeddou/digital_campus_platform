import { cookies } from 'next/headers';
import { SESSION_COOKIE } from '@/lib/session';
import Landing from './Landing';

export default async function Page() {
  return <Landing signedIn={(await cookies()).has(SESSION_COOKIE)} />;
}
