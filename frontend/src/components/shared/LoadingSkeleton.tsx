import { cn } from '@/lib/utils';

export function TableSkeleton({ rows = 5, cols = 5 }: { rows?: number; cols?: number }) {
  return (
    <div className="space-y-0">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex items-center gap-4 px-4 py-3 border-b border-border-light">
          {Array.from({ length: cols }).map((_, j) => (
            <div
              key={j}
              className={cn(
                'h-3.5 bg-slate-100 rounded animate-pulse',
                j === 0 ? 'w-32' : j === cols - 1 ? 'w-16' : 'w-24 flex-1'
              )}
            />
          ))}
        </div>
      ))}
    </div>
  );
}

export function CardSkeleton({ count = 4 }: { count?: number }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="card p-5 space-y-3">
          <div className="h-3 w-20 bg-slate-100 rounded animate-pulse" />
          <div className="h-7 w-16 bg-slate-100 rounded animate-pulse" />
        </div>
      ))}
    </div>
  );
}
