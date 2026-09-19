import { cn } from '@/lib/utils';

interface StatCardProps {
  label: string;
  value: string | number;
  delta?: string;
  positive?: boolean;
  className?: string;
}

export function StatCard({ label, value, delta, positive, className }: StatCardProps) {
  return (
    <div className={cn('stat-card', className)}>
      <p className="text-xs text-slate-500 font-medium">{label}</p>
      <p className="text-2xl font-bold text-slate-900 tabular-nums">{value}</p>
      {delta && (
        <p className={cn('text-xs font-medium', positive ? 'text-emerald-600' : 'text-red-500')}>
          {delta}
        </p>
      )}
    </div>
  );
}
