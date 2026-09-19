import { cn } from '@/lib/utils';
import { ExecutionStatus } from '@/types';
import {
  Search, Target, Lightbulb, Sparkles, Shield, Mail, MessageCircle, PhoneCall, RefreshCw,
} from 'lucide-react';

interface PipelineNode {
  id: string;
  label: string;
  icon: React.ReactNode;
  status: ExecutionStatus | 'READY';
}

const PIPELINE_NODES: PipelineNode[] = [
  { id: 'prospect', label: 'Prospect', icon: <Target size={14} />, status: 'COMPLETED' },
  { id: 'research', label: 'Lead Research', icon: <Search size={14} />, status: 'COMPLETED' },
  { id: 'icp', label: 'ICP Fitment', icon: <Target size={14} />, status: 'COMPLETED' },
  { id: 'strategy', label: 'Strategy', icon: <Lightbulb size={14} />, status: 'COMPLETED' },
  { id: 'personalisation', label: 'Personalisation', icon: <Sparkles size={14} />, status: 'COMPLETED' },
  { id: 'guardrail', label: 'Guardrail', icon: <Shield size={14} />, status: 'RUNNING' },
  { id: 'outreach', label: 'Outreach', icon: <Mail size={14} />, status: 'WAITING' },
  { id: 'conversation', label: 'Conversation', icon: <MessageCircle size={14} />, status: 'WAITING' },
  { id: 'followup', label: 'Follow-up', icon: <RefreshCw size={14} />, status: 'WAITING' },
];

const nodeStyles: Record<string, string> = {
  COMPLETED: 'bg-emerald-50 border-emerald-200 text-emerald-700',
  RUNNING: 'bg-brand/10 border-brand text-brand animate-pulse',
  WAITING: 'bg-slate-50 border-slate-200 text-slate-400',
  FAILED: 'bg-red-50 border-red-200 text-red-600',
  READY: 'bg-violet-50 border-violet-200 text-violet-600',
};

interface AgentPipelineProps {
  compact?: boolean;
}

export function AgentPipeline({ compact = false }: AgentPipelineProps) {
  return (
    <div className={cn('flex flex-col items-center', compact ? 'gap-1' : 'gap-2')}>
      {PIPELINE_NODES.map((node, i) => (
        <div key={node.id} className="flex flex-col items-center">
          <div
            className={cn(
              'flex items-center gap-2 px-3 py-2 rounded-lg border text-xs font-medium cursor-pointer hover:shadow-sm transition-all',
              compact ? 'px-2.5 py-1.5 text-2xs' : '',
              nodeStyles[node.status]
            )}
            title={`${node.label} — ${node.status}`}
          >
            {node.icon}
            <span>{node.label}</span>
            {node.status === 'RUNNING' && (
              <span className="w-1.5 h-1.5 rounded-full bg-brand animate-ping" />
            )}
            {node.status === 'COMPLETED' && (
              <span className="text-emerald-500 text-2xs">✓</span>
            )}
          </div>
          {i < PIPELINE_NODES.length - 1 && (
            <div className="w-px h-3 bg-slate-200" />
          )}
        </div>
      ))}
    </div>
  );
}
