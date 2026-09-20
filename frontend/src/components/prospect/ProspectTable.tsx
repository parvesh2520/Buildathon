import { Prospect } from '@/types';
import { deleteProspect } from '@/api/prospects';
import { cn } from '@/lib/utils';
import toast from 'react-hot-toast';
import { useState } from 'react';

interface ProspectTableProps {
  prospects: Prospect[];
  onSelectProspect: (p: Prospect) => void;
  onDeleted?: (id: string) => void;
}

const statusColors: Record<string, string> = {
  DISCOVERED: 'bg-surface-container text-on-surface-variant',
  SELECTED: 'bg-primary-fixed/30 text-on-primary-fixed-variant',
  QUEUED: 'bg-primary-container/40 text-on-primary-container',
  PROCESSING: 'bg-tertiary/10 text-tertiary',
  FIT: 'bg-tertiary/10 text-tertiary',
  REVIEW: 'bg-primary-container/40 text-on-primary-container',
  NO_FIT: 'bg-secondary-container/30 text-on-secondary-container',
  CONTACTED: 'bg-primary-fixed/20 text-on-primary-fixed-variant',
  SENT: 'bg-primary-fixed/20 text-on-primary-fixed-variant',
  COMPLETED: 'bg-tertiary/10 text-tertiary',
  REPLIED: 'bg-inverse-surface/10 text-on-surface',
  MEETING: 'bg-tertiary/20 text-tertiary font-semibold',
  REJECTED: 'bg-secondary-container/30 text-on-secondary-container',
};

const channelIcons: Record<string, string> = {
  EMAIL: 'mail',
  SMS: 'sms',
  PHONE: 'phone',
  LINKEDIN: 'group',
};

export function ProspectTable({ prospects, onSelectProspect, onDeleted }: ProspectTableProps) {
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleDelete = async (event: React.MouseEvent, prospect: Prospect) => {
    event.stopPropagation();
    if (!window.confirm(`Delete prospect "${prospect.name}"?`)) return;
    setDeletingId(prospect.id);
    try {
      await deleteProspect(prospect.id);
      toast.success(`Deleted ${prospect.name}`);
      onDeleted?.(prospect.id);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to delete prospect');
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="rounded-2xl bg-surface-container-lowest shadow-sm overflow-hidden border border-outline-variant/10">
      <table className="w-full">
        <thead>
          <tr className="border-b border-outline-variant/20 bg-surface-container/50">
            {['Name', 'Title', 'Company', 'Campaign', 'ICP Score', 'Status', 'Channel', 'Last Activity', ''].map((h) => (
              <th key={h} className="px-4 py-3 text-left font-label-sm text-label-sm uppercase tracking-wider text-outline first:pl-5">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {prospects.map((p) => (
            <tr
              key={p.id}
              onClick={() => onSelectProspect(p)}
              className="border-b border-outline-variant/10 last:border-0 hover:bg-surface-container/40 cursor-pointer transition-colors"
            >
              <td className="px-4 py-3.5 pl-5">
                <div className="flex items-center gap-space-sm">
                  <div className="w-8 h-8 rounded-full bg-primary-container flex items-center justify-center flex-shrink-0">
                    <span className="font-label-sm text-label-sm text-on-primary-container font-bold">
                      {p.name.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()}
                    </span>
                  </div>
                  <div>
                    <p className="font-label-md text-label-md text-on-surface font-medium">{p.name}</p>
                    <p className="font-label-sm text-label-sm text-outline">
                      {p.email}
                      {p.phone && <span className="ml-1.5 text-primary">· {p.phone}</span>}
                    </p>
                  </div>
                </div>
              </td>
              <td className="px-4 py-3.5 font-body-sm text-body-sm text-on-surface-variant">{p.title}</td>
              <td className="px-4 py-3.5 font-body-sm text-body-sm text-on-surface-variant">{p.company}</td>
              <td className="px-4 py-3.5 font-body-sm text-body-sm text-outline">{p.campaignName ?? '—'}</td>
              <td className="px-4 py-3.5">
                {p.icpScore != null ? (
                  <span className={cn(
                    'inline-block px-2 py-0.5 rounded-full font-label-sm text-label-sm font-bold tabular-nums',
                    p.icpScore >= 80 ? 'bg-tertiary/10 text-tertiary' : p.icpScore >= 60 ? 'bg-primary-container/50 text-on-primary-container' : 'bg-surface-container text-outline'
                  )}>
                    {p.icpScore}
                  </span>
                ) : (
                  <span className="font-body-sm text-body-sm text-outline">—</span>
                )}
              </td>
              <td className="px-4 py-3.5">
                {p.status ? (
                  <span className={cn('px-2.5 py-0.5 rounded-full font-label-sm text-label-sm', statusColors[p.status] ?? 'bg-surface-container text-outline')}>
                    {p.status}
                  </span>
                ) : <span className="text-outline font-body-sm text-body-sm">—</span>}
              </td>
              <td className="px-4 py-3.5">
                {p.channel ? (
                  <span className="flex items-center gap-1 font-label-sm text-label-sm text-on-surface-variant">
                    <span className="material-symbols-outlined text-[15px] text-outline">{channelIcons[p.channel] ?? 'send'}</span>
                    {p.channel}
                  </span>
                ) : <span className="text-outline font-body-sm text-body-sm">—</span>}
              </td>
              <td className="px-4 py-3.5 font-body-sm text-body-sm text-outline">{p.lastActivity ?? '—'}</td>
              <td className="px-4 py-3.5 text-right">
                <button
                  onClick={(event) => handleDelete(event, p)}
                  disabled={deletingId === p.id}
                  className="p-1.5 rounded-lg text-outline hover:text-rose-600 hover:bg-rose-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  title="Delete prospect"
                >
                  <span className="material-symbols-outlined text-[16px]">delete</span>
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
