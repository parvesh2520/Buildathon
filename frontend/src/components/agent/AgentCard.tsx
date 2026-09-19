import { Agent } from '@/types';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { cn } from '@/lib/utils';

interface AgentCardProps {
  agent: Agent;
  onClick: () => void;
}

const statusDot: Record<Agent['status'], string> = {
  ACTIVE: 'bg-emerald-400',
  IDLE: 'bg-slate-300',
  ERROR: 'bg-red-400',
};

export function AgentCard({ agent, onClick }: AgentCardProps) {
  return (
    <div
      className="card p-5 hover:shadow-md transition-shadow cursor-pointer"
      onClick={onClick}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className={cn('w-2 h-2 rounded-full flex-shrink-0', statusDot[agent.status])} />
          <h3 className="text-sm font-semibold text-slate-800">{agent.name}</h3>
        </div>
        <StatusBadge status={agent.status} />
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
