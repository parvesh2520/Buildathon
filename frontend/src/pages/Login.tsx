import { FormEvent, useEffect, useState } from 'react';
import { ArrowRight, Building2, Eye, Mail, ShieldCheck, Sparkles } from 'lucide-react';
import { Navigate, useNavigate } from 'react-router-dom';
import toast, { Toaster } from 'react-hot-toast';
import {
  consumeOAuthHash,
  getStoredSession,
  signInWithPassword,
  signUpWithPassword,
} from '@/lib/auth';

export function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('ramya@stratosphere.io');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [mode, setMode] = useState<'signin' | 'signup'>('signin');
  const [rememberDevice, setRememberDevice] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [hasSession, setHasSession] = useState(() => Boolean(getStoredSession()));

  useEffect(() => {
    const session = consumeOAuthHash();
    if (session) {
      toast.success('Signed in with Google Workspace');
      setHasSession(true);
      navigate('/dashboard', { replace: true });
    }
  }, [navigate]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (mode === 'signup' && password !== confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }

    setLoading(true);
    try {
      if (mode === 'signup') {
        const session = await signUpWithPassword(email.trim(), password);
        if (session) {
          toast.success('Account created. Welcome to Nectar.');
          navigate('/dashboard', { replace: true });
        } else {
          toast.success('Account created. Check your email to confirm your signup.');
          setMode('signin');
        }
      } else {
        await signInWithPassword(email.trim(), password);
        toast.success('Welcome back to Nectar');
        navigate('/dashboard', { replace: true });
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : mode === 'signup' ? 'Signup failed' : 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  if (hasSession) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="min-h-screen overflow-hidden bg-[#faf6ee] text-[#27231d]">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_32%_18%,rgba(232,168,37,0.16),transparent_30%),radial-gradient(circle_at_70%_82%,rgba(77,132,112,0.16),transparent_26%)]" />
      <header className="relative z-10 flex items-center justify-between px-8 py-8">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#e6a219] shadow-sm">
            <Sparkles size={18} className="text-[#3a2b05]" />
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="font-serif text-xl font-bold">Nectar</span>
            <span className="text-sm font-medium text-[#4d463c]">SDR Workspace</span>
          </div>
        </div>

        <div className="hidden items-center gap-2 rounded-full bg-white/45 px-4 py-2 text-xs font-bold uppercase tracking-wide text-[#357766] shadow-sm sm:flex">
          <span className="h-2.5 w-2.5 rounded-full bg-[#357766]" />
          Operations Normal
        </div>
      </header>

      <main className="relative z-10 flex min-h-[calc(100vh-190px)] items-center justify-center px-5 py-8">
        <section className="w-full max-w-[600px] rounded-[18px] border border-white/75 bg-white/88 px-10 py-11 text-center shadow-[0_26px_70px_rgba(39,35,29,0.14)] backdrop-blur">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-[#302e2a]">
            <span className="material-symbols-outlined text-[32px] text-[#f4d5a2]">grain</span>
          </div>

          <div className="mb-3 flex items-center justify-center gap-2">
            <span className="font-serif text-lg font-bold">Nectar</span>
            <span className="text-xs font-bold uppercase tracking-wide text-[#8a6718]">Workspace</span>
          </div>
          <p className="text-[15px] text-[#4f463c]">Autonomous SDR Fleet & Outbound Intelligence</p>

          <h1 className="mt-9 font-serif text-4xl font-bold leading-tight tracking-normal">
            {mode === 'signin' ? 'Welcome back to your fleet.' : 'Create your Nectar workspace.'}
          </h1>
          <p className="mx-auto mt-5 max-w-[430px] text-base leading-7 text-[#4f463c]">
            {mode === 'signin'
              ? 'Enter your enterprise credentials to access the command cockpit.'
              : 'Create your workspace account with your work email credentials.'}
          </p>

          <div className="my-8 flex items-center gap-3">
            <span className="h-px flex-1 bg-[#e4dbcc]" />
            <span className="text-xs font-bold uppercase text-[#5b5145]">Enter email</span>
            <span className="h-px flex-1 bg-[#e4dbcc]" />
          </div>

          <form onSubmit={handleSubmit} className="space-y-5 text-left">
            <label className="block">
              <span className="mb-2 block text-sm font-bold">Work Email</span>
              <span className="flex h-14 items-center gap-3 rounded-2xl bg-[#f4efe6] px-5">
                <input
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  type="email"
                  required
                  className="min-w-0 flex-1 bg-transparent text-base outline-none placeholder:text-[#9a8f80]"
                  placeholder="you@company.com"
                />
                <Building2 size={18} className="text-[#b7a994]" />
              </span>
            </label>

            {mode === 'signup' && (
              <label className="block">
                <span className="mb-2 block text-sm font-bold">Confirm Password</span>
                <span className="flex h-14 items-center gap-3 rounded-2xl bg-[#f4efe6] px-5">
                  <input
                    value={confirmPassword}
                    onChange={(event) => setConfirmPassword(event.target.value)}
                    type={showPassword ? 'text' : 'password'}
                    required
                    className="min-w-0 flex-1 bg-transparent text-base outline-none placeholder:text-[#9a8f80]"
                    placeholder="Repeat password"
                  />
                  <Mail size={18} className="text-[#b7a994]" />
                </span>
              </label>
            )}

            <label className="block">
              <span className="mb-2 flex items-center justify-between text-sm font-bold">
                Password
                <button type="button" className="text-xs font-bold text-[#8a6718]">
                  Forgot password?
                </button>
              </span>
              <span className="flex h-14 items-center gap-3 rounded-2xl bg-[#f4efe6] px-5">
                <input
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  type={showPassword ? 'text' : 'password'}
                  required
                  className="min-w-0 flex-1 bg-transparent text-base outline-none placeholder:text-[#9a8f80]"
                  placeholder="Enter password"
                />
                <button type="button" onClick={() => setShowPassword((value) => !value)}>
                  <Eye size={18} className="text-[#b7a994]" />
                </button>
              </span>
            </label>

            <label className="flex items-center gap-3 text-sm text-[#4f463c]">
              <input
                checked={rememberDevice}
                onChange={(event) => setRememberDevice(event.target.checked)}
                type="checkbox"
                className="h-7 w-7 rounded-lg accent-[#e6a219]"
              />
              Remember this device for 30 days
            </label>

            <button
              type="submit"
              disabled={loading}
              className="flex h-14 w-full items-center justify-center gap-3 rounded-full bg-[#e6a219] text-base font-bold text-[#211b12] shadow-[0_12px_28px_rgba(230,162,25,0.25)] transition hover:bg-[#d79714] disabled:cursor-not-allowed disabled:opacity-70"
            >
              {loading
                ? mode === 'signup'
                  ? 'Creating Account...'
                  : 'Entering Workspace...'
                : mode === 'signup'
                ? 'Create Account'
                : 'Enter Workspace'}
              <ArrowRight size={19} />
            </button>
          </form>

          <div className="mt-6 text-center text-sm text-[#4f463c]">
            {mode === 'signin' ? "Don't have an account?" : 'Already have an account?'}{' '}
            <button
              type="button"
              onClick={() => {
                setMode((value) => (value === 'signin' ? 'signup' : 'signin'));
                setPassword('');
                setConfirmPassword('');
              }}
              className="font-bold text-[#8a6718] underline-offset-4 hover:underline"
            >
              {mode === 'signin' ? 'Sign up' : 'Sign in'}
            </button>
          </div>

          <div className="mt-8 flex items-center justify-between rounded-2xl bg-[#f4efe6] px-5 py-4 text-sm">
            <span className="flex items-center gap-2 font-bold uppercase text-[#357766]">
              <span className="h-2.5 w-2.5 rounded-full bg-[#357766]" />
              Fleet Daemon Active
            </span>
            <span className="font-medium">8 Agents Standby · 99.4% Uptime</span>
          </div>
        </section>
      </main>

      <footer className="relative z-10 flex flex-col items-center gap-3 px-8 pb-8 text-sm text-[#5b5145]">
        <div>
          Need an enterprise invitation?{' '}
          <a href="mailto:security@nectar.local" className="font-bold text-[#8a6718]">
            Request access
          </a>
        </div>
        <div className="flex items-center gap-2 text-xs font-semibold text-[#c0b4a4]">
          <ShieldCheck size={14} />
          SOC2 Type II & GDPR Compliant · Zero-Data Training Guarantee
        </div>
      </footer>

      <Toaster position="top-right" />
    </div>
  );
}
