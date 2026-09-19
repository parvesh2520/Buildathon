import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronRight, MoreHorizontal } from 'lucide-react';
import { Campaign } from '@/types';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { updateCampaignStatus } from '@/api/campaigns';
import toast from 'react-hot-toast';
import { cn } from '@/lib/utils';

interface CampaignTableProps {
  campaigns: Campaign[];
  onStatusChange: (id: string, status: Campaign['status']) => void;
}

function StatusToggle({
  campaign,
  onStatusChange,
}: {
  campaign: Campaign;
  onStatusChange: (id: string, status: Campaign['status']) => void;
}) {
  const [loading, setLoading] = useState(false);
  const isLive = campaign.status === 'LIVE';

  const toggle = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (campaign.status === 'COMPLETED') return;
    setLoading(true);
    try {
      const newStatus = isLive ? 'PAUSED' : 'LIVE';
      await updateCampaignStatus(campaign.id, newStatus);
      onStatusChange(campaign.id, newStatus);
      toast.success(`Campaign ${newStatus === 'LIVE' ? 'activated' : 'paused'}`);
    } catch {
      toast.error('Failed to update status');
    } finally {
      setLoading(false);
    }
  };

  if (campaign.status === 'COMPLETED') {
    return <StatusBadge status="COMPLETED" />;
  }

  return (
    <button
      onClick={toggle}
      disabled={loading}
      className={cn(
        'relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none',
        isLive ? 'bg-emerald-500' : 'bg-slate-200',
        loading && 'opacity-50 cursor-not-allowed'
      )}
      title={isLive ? 'Click to pause' : 'Click to activate'}
    >
      <span
        className={cn(
          'inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow transition-transform',
          isLive ? 'translate-x-4' : 'translate-x-0.5'
        )}
      />
    </button>
  );
}

export function CampaignTable({ campaigns, onStatusChange }: CampaignTableProps) {
  const navigate = useNavigate();

  return (
    <div className="card overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border bg-surface-secondary">
            <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide">Campaign</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide">ICP</th>
            <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wide">Prospects</th>
            <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wide">Messages</th>
            <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wide">Replies</th>
            <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wide">Meetings</th>
            <th className="px-4 py-3 text-center text-xs font-semibold text-slate-500 uppercase tracking-wide">Status</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide">Last Activity</th>
            <th className="px-4 py-3" />
          </tr>
        </thead>
        <tbody>
          {campaigns.map((c) => (
            <tr
              key={c.id}
              className="table-row-hover border-b border-border-light last:border-0"
              onClick={() => navigate(`/campaigns/${c.id}`)}
            >
              <td className="px-4 py-3">
                <div>
                  <p className="font-medium text-slate-800">{c.name}</p>
                  <p className="text-xs text-slate-400 font-mono mt-0.5">{c.id}</p>
                </div>
              </td>
              <td className="px-4 py-3">
                <p className="text-slate-600 text-xs max-w-[180px] truncate" title={c.icp}>{c.icp}</p>
              </td>
              <td className="px-4 py-3 text-right tabular-nums text-slate-700">{(c.prospects ?? 0).toLocaleString()}</td>
              <td className="px-4 py-3 text-right tabular-nums text-slate-700">{(c.messages ?? 0).toLocaleString()}</td>
              <td className="px-4 py-3 text-right tabular-nums text-slate-700">{c.replies ?? 0}</td>
              <td className="px-4 py-3 text-right tabular-nums text-slate-700">{c.meetings ?? 0}</td>
              <td className="px-4 py-3 text-center" onClick={(e) => e.stopPropagation()}>
                <div className="flex items-center justify-center gap-2">
                  <StatusToggle campaign={c} onStatusChange={onStatusChange} />
                </div>
              </td>
              <td className="px-4 py-3 text-xs text-slate-400">{c.lastActivity ?? '—'}</td>
              <td className="px-4 py-3">
                <ChevronRight size={14} className="text-slate-300" />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
