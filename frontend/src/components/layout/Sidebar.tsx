import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Megaphone,
  Compass,
  Users,
  Bot,
  Activity,
  BarChart3,
  Settings,
  Zap,
  Inbox,
  BrainCircuit,
} from 'lucide-react';
import { cn } from '@/lib/utils';

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/campaigns', icon: Megaphone, label: 'Campaigns' },
  { to: '/discovery', icon: Compass, label: 'Prospect Discovery' },
  { to: '/prospects', icon: Users, label: 'Prospects' },
  { to: '/agents', icon: Bot, label: 'Agents' },
  { to: '/inbox', icon: Inbox, label: 'Inbox' },
  { to: '/chatbot', icon: BrainCircuit, label: 'Intelligence Desk' },
  { to: '/activity', icon: Activity, label: 'Activity' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
];

export function Sidebar() {
  const location = useLocation();

  return (
    <aside className="w-56 min-h-screen bg-sidebar-bg flex flex-col border-r border-sidebar-border flex-shrink-0">
      {/* Logo */}
      <div className="px-4 py-5 flex items-center gap-2.5 border-b border-sidebar-border">
        <div className="w-7 h-7 rounded-lg bg-brand flex items-center justify-center flex-shrink-0">
          <Zap size={14} className="text-white" />
        </div>
        <span className="text-sm font-semibold text-sidebar-textActive leading-tight">
          Autonomous SDR
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 py-3 space-y-0.5">
        {navItems.map(({ to, icon: Icon, label }) => {
          const isActive = location.pathname === to || (to !== '/dashboard' && location.pathname.startsWith(to));
          return (
            <NavLink
              key={to}
              to={to}
              className={cn('sidebar-link', isActive && 'sidebar-link-active')}
            >
              <Icon size={15} />
              <span>{label}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Bottom section */}
      <div className="px-2 py-3 border-t border-sidebar-border space-y-0.5">
        <NavLink
          to="/settings"
          className={cn(
            'sidebar-link',
            location.pathname === '/settings' && 'sidebar-link-active'
          )}
        >
          <Settings size={15} />
          <span>Settings</span>
        </NavLink>

        {/* System status */}
        <div className="px-3 py-3 mt-1">
          <p className="text-2xs text-sidebar-text font-medium uppercase tracking-widest mb-2">
            System Status
          </p>
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs text-sidebar-text">All systems operational</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
