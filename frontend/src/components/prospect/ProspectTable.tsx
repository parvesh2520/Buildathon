import { Prospect } from '@/types';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { EmptyState } from '@/components/shared/EmptyState';
import { Users } from 'lucide-react';

interface ProspectTableProps {
  prospects: Prospect[];
  onSelectProspect: (p: Prospect) => void;
}

export function ProspectTable({ prospects, onSelectProspect }: ProspectTableProps) {
  if (prospects.length === 0) {
    return (
      <div className="card">
        <EmptyState
          icon={<Users size={20} />}
          title="No prospects yet"
          description="Add your first prospect to start the autonomous SDR pipeline."
        />
      </div>
    );
  }

  return (
    <div className="card overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border bg-surface-secondary">
            <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide">Name</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide">Title</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide">Company</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide">Campaign</th>
            <th className="px-4 py-3 text-center text-xs font-semibold text-slate-500 uppercase tracking-wide">ICP Score</th>
            <th className="px-4 py-3 text-center text-xs font-semibold text-slate-500 uppercase tracking-wide">Status</th>
            <th className="px-4 py-3 text-center text-xs font-semibold text-slate-500 uppercase tracking-wide">Channel</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide">Last Activity</th>
          </tr>
        </thead>
        <tbody>
          {prospects.map((p) => (
            <tr
              key={p.id}
              className="table-row-hover border-b border-border-light last:border-0"
              onClick={() => onSelectProspect(p)}
            >
              <td className="px-4 py-3">
                <div>
                  <p className="font-medium text-slate-800">{p.name}</p>
                  <p className="text-xs text-slate-400">
                    {p.email}
                    {p.phone && <span className="text-brand font-mono ml-1.5 font-medium">· {p.phone}</span>}
                  </p>
                </div>
              </td>
              <td className="px-4 py-3 text-slate-600">{p.title}</td>
              <td className="px-4 py-3 text-slate-600">{p.company}</td>
              <td className="px-4 py-3 text-xs text-slate-500">{p.campaignName ?? '—'}</td>
              <td className="px-4 py-3 text-center">
                {p.icpScore != null ? (
                  <span className={`text-xs font-bold tabular-nums ${p.icpScore >= 80 ? 'text-emerald-600' : p.icpScore >= 60 ? 'text-amber-600' : 'text-slate-400'}`}>
                    {p.icpScore}
                  </span>
                ) : (
                  <span className="text-xs text-slate-300">—</span>
                )}
              </td>
              <td className="px-4 py-3 text-center">
                {p.status ? <StatusBadge status={p.status} /> : <span className="text-xs text-slate-300">—</span>}
              </td>
              <td className="px-4 py-3 text-center">
                {p.channel ? <StatusBadge status={p.channel} /> : <span className="text-xs text-slate-300">—</span>}
              </td>
              <td className="px-4 py-3 text-xs text-slate-400">{p.lastActivity ?? '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
