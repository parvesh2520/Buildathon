import { useEffect, useState } from 'react';
import { ActivityEvent, ActivityCategory } from '@/types';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { getActivityEvents } from '@/api/sdr';
import { cn } from '@/lib/utils';

type Filter = ActivityCategory | 'all';

const FILTERS: { id: Filter; label: string }[] = [
  { id: 'all', label: 'All' },
  { id: 'research', label: 'Research' },
  { id: 'qualification', label: 'Qualification' },
  { id: 'strategy', label: 'Strategy' },
  { id: 'personalisation', label: 'Personalisation' },
  { id: 'conversation', label: 'Conversation' },
  { id: 'follow-up', label: 'Follow-up' },
  { id: 'voice', label: 'Voice' },
];

const categoryColors: Record<ActivityCategory, string> = {
  research: 'bg-blue-100 text-blue-600',
  qualification: 'bg-violet-100 text-violet-600',
  strategy: 'bg-amber-100 text-amber-600',
  personalisation: 'bg-pink-100 text-pink-600',
  conversation: 'bg-emerald-100 text-emerald-600',
  'follow-up': 'bg-teal-100 text-teal-600',
  voice: 'bg-orange-100 text-orange-600',
  campaign: 'bg-indigo-100 text-indigo-600',
};

export function Activity() {
  const [filter, setFilter] = useState<Filter>('all');
  const [activity, setActivity] = useState<ActivityEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getActivityEvents()
      .then(setActivity)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load activity'))
      .finally(() => setLoading(false));
  }, []);

  const filtered: ActivityEvent[] =
    filter === 'all' ? activity : activity.filter((a) => a.category === filter);

  return (
    <div className="p-6 max-w-[900px] mx-auto">
      <div className="page-header">
        <h1 className="text-xl font-bold text-slate-900">Activity</h1>
        <p className="text-sm text-slate-500 mt-1">Global autonomous agent execution timeline.</p>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-1.5 mb-6 flex-wrap">
        {FILTERS.map((f) => (
          <button
            key={f.id}
            onClick={() => setFilter(f.id)}
            className={cn(
              'px-3 py-1.5 rounded-lg text-xs font-medium transition-colors',
              filter === f.id
                ? 'bg-brand text-white'
                : 'bg-white border border-border text-slate-600 hover:bg-surface-secondary'
            )}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Timeline */}
      <div className="relative">
        <div className="absolute left-[19px] top-0 bottom-0 w-px bg-border" />
        <div className="space-y-1">
          {loading && (
            <div className="card px-4 py-5 text-sm text-slate-500">Loading backend activity...</div>
          )}
          {error && (
            <div className="card px-4 py-5 text-sm text-red-600">{error}</div>
          )}
          {!loading && !error && filtered.length === 0 && (
            <div className="card px-4 py-5 text-sm text-slate-500">No backend execution activity found yet.</div>
          )}
          {filtered.map((event) => (
            <div key={event.id} className="flex items-start gap-4 group">
              {/* dot */}
              <div className={cn(
                'w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 z-10 text-sm mt-2',
                categoryColors[event.category]
              )}>
                {event.category[0].toUpperCase()}
              </div>
              {/* content */}
              <div className="flex-1 card px-4 py-3 mb-2 hover:shadow-sm transition-shadow">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-xs font-semibold text-slate-800">{event.agentName}</p>
                    <p className="text-xs text-slate-500 mt-0.5">{event.action}</p>
                    <div className="flex items-center gap-3 mt-1.5">
                      {event.prospect && (
                        <span className="text-2xs text-brand font-medium">{event.prospect}</span>
                      )}
                      {event.campaign && (
                        <span className="text-2xs text-slate-400">{event.campaign}</span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 ml-4 flex-shrink-0">
                    <StatusBadge status={event.status} />
                    <span className="text-2xs text-slate-400 tabular-nums">{event.timestamp}</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
