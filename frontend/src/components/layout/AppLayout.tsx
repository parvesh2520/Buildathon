import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { NectarSidebar, NectarHeader } from '@/components/nectar';
import { Toaster } from 'react-hot-toast';
import { GlobalKillSwitchBanner } from './GlobalKillSwitchBanner';
import { useEffect } from 'react';
import { getStoredSession } from '@/lib/auth';

export function AppLayout() {
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (!getStoredSession()) {
      navigate('/login', { replace: true, state: { from: location.pathname } });
    }
  }, [location.pathname, navigate]);

  return (
    <div className="min-h-screen bg-background font-sans text-on-surface antialiased flex flex-col">
      {/* Warm Editorial Sidebar */}
      <NectarSidebar />

      {/* Warm Editorial Header */}
      <NectarHeader
        onNewContact={() => navigate('/discovery')}
        onRunSequence={() => navigate('/campaigns')}
      />

      {/* Main Content Pane */}
      <div className="pl-72 flex-1 flex flex-col">
        <GlobalKillSwitchBanner />
        <main className="w-full pt-16 flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>

      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            fontSize: '13px',
            borderRadius: '12px',
            background: '#ffffff',
            color: '#1c1c17',
            border: '1px solid #d5c4ae',
            boxShadow: '0 4px 14px rgba(39, 39, 42, 0.08)',
          },
          success: { iconTheme: { primary: '#e6a219', secondary: '#ffffff' } },
        }}
      />
    </div>
  );
}
