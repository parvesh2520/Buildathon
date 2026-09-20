import React from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import { clearStoredSession } from '@/lib/auth';

interface NectarSidebarProps {
  onSearch?: (term: string) => void;
}

export const NectarSidebar: React.FC<NectarSidebarProps> = ({ onSearch }) => {
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    clearStoredSession();
    navigate('/login', { replace: true });
  };

  const navItems = [
    { to: '/dashboard', icon: 'space_dashboard', label: 'Dashboard' },
    { to: '/campaigns', icon: 'campaign', label: 'Campaigns' },
    { to: '/prospects', icon: 'people', label: 'Prospects' },
    { to: '/agents', icon: 'smart_toy', label: 'Agents', badge: '7' },
    { to: '/control-centre', icon: 'tune', label: 'Control Centre' },
    { to: '/inbox', icon: 'inbox', label: 'Inbox', badge: '12', badgeType: 'primary' },
    { to: '/chatbot', icon: 'neurology', label: 'Intelligence Desk' },
  ];

  return (
    <aside className="fixed left-0 top-0 h-full w-72 bg-surface-container-low shadow-[0_1px_8px_rgba(0,0,0,0.04)] z-50 flex flex-col justify-between pt-space-lg pb-space-lg">
      <div className="flex flex-col gap-space-md px-space-md overflow-y-auto">
        {/* Logo */}
        <div className="flex items-center gap-space-sm px-space-xs">
          <div className="w-9 h-9 rounded-xl bg-inverse-surface flex items-center justify-center shadow-[0_2px_8px_rgba(39,39,42,0.08)]">
            <span className="font-headline-sm text-headline-sm text-surface font-serif">N</span>
          </div>
          <div className="flex flex-col">
            <span className="font-headline-sm text-headline-sm text-on-surface leading-tight font-serif">Nectar</span>
            <span className="font-label-sm text-label-sm tracking-wider uppercase text-on-surface-variant font-medium">
              SDR Workspace
            </span>
          </div>
        </div>

        {/* Search */}
        <div className="relative w-full">
          <span className="material-symbols-outlined absolute left-3 top-2.5 text-[18px] text-outline select-none">
            search
          </span>
          <input
            type="text"
            placeholder="Search people, companies..."
            onChange={(e) => onSearch?.(e.target.value)}
            className="w-full bg-surface-container rounded-xl pl-9 pr-space-sm py-2 font-body-sm text-body-sm text-on-surface placeholder:text-outline focus:outline-none focus:bg-surface-container-lowest transition-colors shadow-[inset_0_1px_2px_rgba(24,24,27,0.04)]"
          />
        </div>

        {/* Navigation */}
        <nav className="flex flex-col gap-1">
          {navItems.map((item) => {
            const isActive =
              location.pathname === item.to ||
              (item.to === '/dashboard' && location.pathname === '/');

            return (
              <NavLink
                key={item.label}
                to={item.to}
                className={`flex items-center justify-between px-3 py-2 rounded-xl transition-colors ${
                  isActive
                    ? 'bg-primary-container text-on-primary-container font-label-md font-semibold shadow-sm'
                    : 'text-on-surface-variant hover:bg-surface-container hover:text-on-surface'
                }`}
              >
                <div className="flex items-center gap-space-sm">
                  <span className="material-symbols-outlined text-[20px] select-none">
                    {item.icon}
                  </span>
                  <span className="font-label-md text-label-md">{item.label}</span>
                </div>
                {item.badge && (
                  <span
                    className={`px-2 py-0.5 rounded-full font-label-sm text-label-sm font-semibold ${
                      item.badgeType === 'primary'
                        ? 'bg-primary text-on-primary'
                        : 'bg-surface-container-highest text-on-surface'
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
              </NavLink>
            );
          })}
        </nav>

      </div>

      {/* Profile Footer */}
      <div className="px-space-md">
        <div className="bg-surface-container-lowest rounded-xl p-space-sm flex items-center justify-between shadow-[0_2px_8px_rgba(39,39,42,0.03)] border border-outline-variant/30">
          <div className="flex items-center gap-space-sm">
            <div className="relative">
              <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
                <span className="material-symbols-outlined text-on-primary text-[18px] select-none">
                  person
                </span>
              </div>
              <span className="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full bg-tertiary border-2 border-surface-container-lowest" />
            </div>
            <div className="flex flex-col">
              <span className="font-label-md text-label-md text-on-surface leading-snug font-semibold">
                Ramya
              </span>
              <span className="font-label-sm text-label-sm text-tertiary flex items-center gap-1 leading-tight">
                Online
              </span>
            </div>
          </div>
          <button
            type="button"
            onClick={handleLogout}
            className="w-8 h-8 rounded-full flex items-center justify-center text-outline hover:text-rose-600 hover:bg-rose-50 transition-colors"
            title="Log out"
            aria-label="Log out"
          >
            <span className="material-symbols-outlined text-[18px] select-none">
              logout
            </span>
          </button>
        </div>
      </div>
    </aside>
  );
};
