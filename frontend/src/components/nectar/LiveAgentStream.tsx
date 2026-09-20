import React, { useState } from 'react';

interface StreamEvent {
  id: string;
  icon: string;
  iconBg: string;
  iconColor: string;
  title: string;
  subtitle: string;
  timestamp: string;
}

export const LiveAgentStream: React.FC = () => {
  const [refreshing, setRefreshing] = useState(false);

  const events: StreamEvent[] = [
    {
      id: '1',
      icon: 'explore',
      iconBg: 'bg-[#FEF7E6]',
      iconColor: 'text-[#7F5700]',
      title: 'Alex Vance (CTO, ScaleTech...)',
      subtitle: 'Series B Crunchbase filing',
      timestamp: '2m',
    },
    {
      id: '2',
      icon: 'block',
      iconBg: 'bg-[#FFDAD6]',
      iconColor: 'text-[#BA1A1A]',
      title: 'Profile filtered out (Score: 6...)',
      subtitle: 'GitHub inactive > 18 mos',
      timestamp: '4m',
    },
    {
      id: '3',
      icon: 'mark_chat_read',
      iconBg: 'bg-[#EDF4F0]',
      iconColor: 'text-[#366853]',
      title: 'DevFlow CTO replied: Secu...',
      subtitle: 'Escalated to Ramya',
      timestamp: '11m',
    },
    {
      id: '4',
      icon: 'phone_in_talk',
      iconBg: 'bg-inverse-surface',
      iconColor: 'text-primary-fixed',
      title: 'Voice call booked with VP E...',
      subtitle: 'Duration: 1m 45s',
      timestamp: '19m',
    },
    {
      id: '5',
      icon: 'auto_stories',
      iconBg: 'bg-[#FEF7E6]',
      iconColor: 'text-[#E6A219]',
      title: '52-word technical note dis...',
      subtitle: 'Target: PyTorch AI Infra CTOs',
      timestamp: '27m',
    },
  ];

  const handleRefresh = () => {
    setRefreshing(true);
    setTimeout(() => setRefreshing(false), 600);
  };

  return (
    <div className="bg-surface-container-lowest rounded-2xl p-space-lg shadow-sm border border-outline-variant/40 flex flex-col justify-between h-full">
      <div className="flex flex-col gap-space-md">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <span className="font-label-sm text-label-sm text-outline uppercase tracking-wider block font-medium">
              Realtime Activity
            </span>
            <h2 className="font-headline-md text-headline-md text-on-surface font-serif mt-0.5">
              Live Agent Stream
            </h2>
          </div>
          <span className="w-2.5 h-2.5 rounded-full bg-tertiary animate-pulse" />
        </div>

        {/* Events Feed */}
        <div className="flex flex-col gap-2.5">
          {events.map((evt) => (
            <div
              key={evt.id}
              className="flex items-center justify-between p-2.5 rounded-xl bg-surface-container-low hover:bg-surface-container transition-colors gap-3"
            >
              <div className="flex items-center gap-3 min-w-0">
                <div
                  className={`w-9 h-9 rounded-full ${evt.iconBg} ${evt.iconColor} flex items-center justify-center flex-shrink-0 shadow-sm`}
                >
                  <span className="material-symbols-outlined text-[18px] select-none">
                    {evt.icon}
                  </span>
                </div>
                <div className="flex flex-col min-w-0">
                  <span className="font-label-md text-label-md text-on-surface font-semibold truncate leading-snug">
                    {evt.title}
                  </span>
                  <span className="font-body-sm text-body-sm text-on-surface-variant truncate text-[12px]">
                    {evt.subtitle}
                  </span>
                </div>
              </div>
              <span className="font-label-sm text-label-sm text-outline flex-shrink-0">
                {evt.timestamp}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="pt-4 mt-4 border-t border-outline-variant/30 flex items-center justify-between text-body-sm text-body-sm">
        <span className="text-on-surface-variant font-medium">Logging 418 actions today</span>
        <button
          type="button"
          onClick={handleRefresh}
          className="flex items-center gap-1.5 font-label-sm text-label-sm font-semibold text-primary hover:text-on-surface transition-colors"
        >
          <span
            className={`material-symbols-outlined text-[16px] select-none ${
              refreshing ? 'animate-spin' : ''
            }`}
          >
            refresh
          </span>
          <span>Refresh stream</span>
        </button>
      </div>
    </div>
  );
};
