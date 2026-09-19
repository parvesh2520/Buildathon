import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Toaster } from 'react-hot-toast';

export function AppLayout() {
  return (
    <div className="flex h-screen overflow-hidden bg-surface-secondary">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
      <Toaster
        position="top-right"
        toastOptions={{
          style: { fontSize: '13px', borderRadius: '10px', border: '1px solid #e4e7ef' },
          success: { iconTheme: { primary: '#6366f1', secondary: 'white' } },
        }}
      />
    </div>
  );
}
