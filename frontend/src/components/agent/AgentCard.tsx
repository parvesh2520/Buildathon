import { Agent } from '@/types';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { cn } from '@/lib/utils';
import { Pause, Play } from 'lucide-react';

interface AgentCardProps {
  agent: Agent;
  onClick: () => void;
  paused?: boolean;
  onTogglePause?: (e: React.MouseEvent) => void;
}

const statusDot: Record<Agent['status'], string> = {
  ACTIVE: 'bg-emerald-400',
  IDLE: 'bg-slate-300',
  ERROR: 'bg-red-400',
};

export function AgentCard({ agent, onClick, paused, onTogglePause }: AgentCardProps) {
  return (
    <div
      className={cn(
        'card p-5 hover:shadow-md transition-shadow cursor-pointer',
        paused && 'bg-amber-50/20 border-amber-200'
      )}
      onClick={onClick}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className={cn('w-2 h-2 rounded-full flex-shrink-0', paused ? 'bg-amber-400' : statusDot[agent.status])} />
          <h3 className="text-sm font-semibold text-slate-800">{agent.name}</h3>
        </div>
        <div className="flex items-center gap-1.5" onClick={(e) => e.stopPropagation()}>
          {onTogglePause && (
            <button
              onClick={onTogglePause}
              className={cn(
                'px-2 py-0.5 rounded text-3xs font-semibold border flex items-center gap-1 transition-all cursor-pointer',
                paused
                  ? 'bg-amber-100 text-amber-800 border-amber-300 hover:bg-amber-200'
                  : 'bg-slate-100 text-slate-600 border-slate-200 hover:bg-slate-200'
              )}
              title={paused ? 'Resume this agent' : 'Pause this agent'}
            >
              {paused ? <Play size={10} /> : <Pause size={10} />}
              <span>{paused ? 'Resume' : 'Pause'}</span>
            </button>
          )}
          <StatusBadge status={paused ? ('PAUSED' as any) : agent.status} />
        </div>
      </div>

      <p className="text-xs text-slate-500 leading-relaxed mb-4">{agent.description}</p>

      <div className="grid grid-cols-3 gap-3">
        <div>
          <p className="text-2xs text-slate-400 font-medium">Executions</p>
          <p className="text-sm font-bold text-slate-800 tabular-nums">{agent.executions.toLocaleString()}</p>
        </div>
        <div>
          <p className="text-2xs text-slate-400 font-medium">Success Rate</p>
          <p className={cn('text-sm font-bold tabular-nums', agent.successRate >= 95 ? 'text-emerald-600' : agent.successRate >= 85 ? 'text-amber-600' : 'text-red-500')}>
            {agent.successRate}%
          </p>
        </div>
        <div>
          <p className="text-2xs text-slate-400 font-medium">Last Run</p>
          <p className="text-xs text-slate-600">{agent.lastRun ?? '—'}</p>
        </div>
      </div>
    </div>
  );
}
