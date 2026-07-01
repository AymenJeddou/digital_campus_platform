'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { authService } from '@/lib/services/auth';
import { toast } from 'sonner';
import Link from 'next/link';
import { GraduationCap, Mail, ArrowRight, CheckCircle2, Loader2 } from 'lucide-react';

function VerifyContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const [token, setToken] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isAutoVerifying, setIsAutoVerifying] = useState(false);

    useEffect(() => {
        const urlToken = searchParams.get('token');
        if (urlToken) {
            setToken(urlToken);
            handleVerify(urlToken);
        }
    }, [searchParams]);

    const handleVerify = async (verifyToken: string) => {
        if (!verifyToken) return;

        setIsLoading(true);
        try {
            await authService.verifyEmail(verifyToken);
            toast.success('Email verified successfully! You can now sign in.');
            router.push('/login');
        } catch (error: any) {
            toast.error(error.response?.data?.detail || 'Verification failed. The link might be expired.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        handleVerify(token);
    };

    return (
        <div className="min-h-screen bg-background flex items-center justify-center p-4">
            <div className="w-full max-w-md bg-card border border-border shadow-sm rounded-2xl p-8">
                <div className="flex flex-col items-center text-center mb-8">
                    <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 mb-4">
                        <Mail className="h-6 w-6 text-primary" />
                    </div>
                    <h1 className="text-2xl font-bold tracking-tight">Verify your email</h1>
                    <p className="mt-2 text-sm text-muted-foreground">
                        We've sent a verification link to your email address. Please enter the code below or click the link in the email.
                    </p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="space-y-2">
                        <label htmlFor="token" className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                            Verification Code
                        </label>
                        <input
                            id="token"
                            type="text"
                            required
                            placeholder="Enter your verification token"
                            value={token}
                            onChange={(e) => setToken(e.target.value)}
                            className="w-full px-4 py-3 rounded-lg text-sm font-medium bg-secondary/50 border border-border focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all"
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={isLoading || !token}
                        className="w-full flex items-center justify-center gap-2 bg-primary hover:bg-primary/90 text-primary-foreground text-sm font-semibold py-3 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {isLoading ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                            'Verify Email'
                        )}
                    </button>
                </form>

                <div className="mt-8 text-center">
                    <p className="text-sm text-muted-foreground">
                        Didn't receive the email? Check your spam folder or{' '}
                        <button className="text-primary font-medium hover:underline">resend</button>
                    </p>
                    <div className="mt-6 pt-6 border-t border-border">
                        <Link href="/login" className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors flex items-center justify-center gap-2">
                            Back to sign in
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default function VerifyPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen flex items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        }>
            <VerifyContent />
        </Suspense>
    );
}
