import { cn } from '@/lib/utils';
import {
  CampaignStatus,
  ProspectStatus,
  AgentStatus,
  ExecutionStatus,
  OutreachStatus,
  OutreachChannel,
} from '@/types';

type BadgeVariant =
  | CampaignStatus
  | ProspectStatus
  | AgentStatus
  | ExecutionStatus
  | OutreachStatus
  | OutreachChannel;

const variantStyles: Record<string, string> = {
  // Campaign
  LIVE: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  PAUSED: 'bg-amber-50 text-amber-700 border-amber-200',
  COMPLETED: 'bg-slate-100 text-slate-600 border-slate-200',
  // Prospect & Discovery
  DISCOVERED: 'bg-sky-50 text-sky-700 border-sky-200',
  SELECTED: 'bg-indigo-50 text-indigo-700 border-indigo-200',
  QUEUED: 'bg-amber-50 text-amber-700 border-amber-200',
  PROCESSING: 'bg-blue-50 text-blue-700 border-blue-200 animate-pulse',
  FIT: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  REVIEW: 'bg-amber-50 text-amber-700 border-amber-200',
  NO_FIT: 'bg-red-50 text-red-600 border-red-200',
  CONTACTED: 'bg-blue-50 text-blue-700 border-blue-200',
  REPLIED: 'bg-violet-50 text-violet-700 border-violet-200',
  MEETING: 'bg-teal-50 text-teal-700 border-teal-200',
  // Agent
  ACTIVE: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  IDLE: 'bg-slate-100 text-slate-500 border-slate-200',
  ERROR: 'bg-red-50 text-red-600 border-red-200',
  // Execution
  RUNNING: 'bg-blue-50 text-blue-700 border-blue-200',
  WAITING: 'bg-slate-100 text-slate-500 border-slate-200',
  FAILED: 'bg-red-50 text-red-600 border-red-200',
  // Outreach
  PENDING: 'bg-amber-50 text-amber-700 border-amber-200',
  APPROVED: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  REJECTED: 'bg-red-50 text-red-600 border-red-200',
  SENT: 'bg-blue-50 text-blue-700 border-blue-200',
  // Channels
  EMAIL: 'bg-indigo-50 text-indigo-700 border-indigo-200',
  LINKEDIN: 'bg-blue-50 text-blue-700 border-blue-200',
  SMS: 'bg-purple-50 text-purple-700 border-purple-200',
  PHONE: 'bg-teal-50 text-teal-700 border-teal-200',
};

interface StatusBadgeProps {
  status: BadgeVariant;
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const style = variantStyles[status] ?? 'bg-slate-100 text-slate-500 border-slate-200';
  return (
    <span
      className={cn(
        'inline-flex items-center px-2 py-0.5 rounded-md text-2xs font-semibold border tracking-wide uppercase',
        style,
        className
      )}
    >
      {status}
    </span>
  );
}
