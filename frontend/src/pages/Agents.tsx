import { useState, useEffect } from 'react';
import { X, CheckCircle2, Clock } from 'lucide-react';
import { Agent } from '@/types';
import { AgentCard } from '@/components/agent/AgentCard';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { demoAgents } from '@/data/demo/agents';
import { AgentPipeline } from '@/components/agent/AgentPipeline';
import { getAgents } from '@/api/sdr';
import { getOperationalControls, toggleAgentPause } from '@/api/system';
import toast from 'react-hot-toast';

export function Agents() {
  const [agents, setAgents] = useState<Agent[]>(demoAgents);
  const [selected, setSelected] = useState<Agent | null>(null);
  const [pausedAgents, setPausedAgents] = useState<string[]>([]);

  useEffect(() => {
    getAgents().then(setAgents);
    getOperationalControls().then((ctrl) => {
      if (ctrl?.paused_agents) setPausedAgents(ctrl.paused_agents);
    });
  }, []);

  const handleToggleAgent = async (agentName: string) => {
    const isPaused = pausedAgents.includes(agentName);
    try {
      const updated = await toggleAgentPause(agentName, !isPaused);
      setPausedAgents(updated.paused_agents);
      toast.success(`${agentName} ${isPaused ? 'resumed' : 'paused'}`);
    } catch {
      toast.error(`Failed to update ${agentName}`);
    }
  };

  return (
    <div className="p-6 max-w-[1200px] mx-auto">
      <div className="page-header">
        <h1 className="text-xl font-bold text-slate-900">Agents</h1>
        <p className="text-sm text-slate-500 mt-1">
          Agent execution happens autonomously through DronaHQ. Monitor status and performance here.
        </p>
      </div>

      {/* Pipeline visualization */}
      <div className="card p-6 mb-6">
        <div className="flex items-start justify-between mb-5">
          <div>
            <h2 className="text-sm font-semibold text-slate-700">Autonomous SDR Pipeline</h2>
            <p className="text-xs text-slate-400 mt-0.5">End-to-end multi-agent execution flow</p>
          </div>
          <div className="flex items-center gap-4 text-xs text-slate-500">
            <div className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-emerald-400" /> Completed</div>
            <div className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-brand animate-pulse" /> Running</div>
            <div className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-slate-200" /> Waiting</div>
          </div>
        </div>
        <div className="flex justify-center">
          <AgentPipeline />
        </div>
      </div>

      {/* Agent cards */}
      <h2 className="text-sm font-semibold text-slate-700 mb-4 uppercase tracking-wide">Agent Control Center</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {agents.map((agent) => (
          <AgentCard
            key={agent.id}
            agent={agent}
            paused={pausedAgents.includes(agent.name)}
            onTogglePause={() => handleToggleAgent(agent.name)}
            onClick={() => setSelected(agent)}
          />
        ))}
      </div>

      {/* Agent detail modal */}
      {selected && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-xl max-h-[85vh] overflow-y-auto">
            <div className="flex items-center justify-between px-6 py-4 border-b border-border sticky top-0 bg-white rounded-t-2xl">
              <div className="flex items-center gap-2">
                <h2 className="text-base font-semibold text-slate-900">{selected.name}</h2>
                <StatusBadge status={selected.status} />
              </div>
              <button onClick={() => setSelected(null)} className="text-slate-400 hover:text-slate-600 p-1 rounded hover:bg-surface-secondary">
                <X size={16} />
              </button>
            </div>

            <div className="px-6 py-5 space-y-5">
              <div>
                <p className="text-xs font-medium text-slate-500 mb-1">Description</p>
                <p className="text-sm text-slate-700">{selected.description}</p>
              </div>

              <div>
                <p className="text-xs font-medium text-slate-500 mb-2">Responsibilities</p>
                <ul className="space-y-1.5">
                  {selected.responsibilities.map((r, i) => (
                    <li key={i} className="flex items-start gap-2 text-xs text-slate-600">
                      <span className="text-brand mt-0.5">•</span> {r}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div className="card p-3">
                  <p className="text-2xs text-slate-400">Executions</p>
                  <p className="text-lg font-bold text-slate-900 tabular-nums">{selected.executions.toLocaleString()}</p>
                </div>
                <div className="card p-3">
                  <p className="text-2xs text-slate-400">Success Rate</p>
                  <p className="text-lg font-bold text-emerald-600 tabular-nums">{selected.successRate}%</p>
                </div>
                <div className="card p-3">
                  <p className="text-2xs text-slate-400">Avg Duration</p>
                  <p className="text-lg font-bold text-slate-900 tabular-nums">{selected.avgDuration}s</p>
                </div>
              </div>

              {selected.recentExecutions && selected.recentExecutions.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-slate-500 mb-2">Recent Executions</p>
                  <div className="space-y-2">
                    {selected.recentExecutions.map((ex) => (
                      <div key={ex.id} className="flex items-center justify-between p-3 rounded-lg bg-surface-secondary text-xs">
                        <div>
                          <p className="font-medium text-slate-700">{ex.prospect}</p>
                          <p className="text-slate-400">{ex.output}</p>
                        </div>
                        <div className="text-right">
                          <StatusBadge status={ex.status} />
                          <p className="text-slate-400 mt-1">{ex.startedAt}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
