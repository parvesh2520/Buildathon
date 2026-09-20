import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Campaign } from '@/types';
import { updateCampaignStatus, duplicateCampaign, deleteCampaign } from '@/api/campaigns';
import toast from 'react-hot-toast';
import { cn } from '@/lib/utils';

interface CampaignTableProps {
  campaigns: Campaign[];
  onStatusChange: (id: string, status: Campaign['status']) => void;
  onDeleted?: (id: string) => void;
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
    return (
      <span className="px-2 py-0.5 rounded-full bg-surface-container text-on-surface-variant font-label-sm text-label-sm">
        Completed
      </span>
    );
  }

  return (
    <button
      onClick={toggle}
      disabled={loading}
      className={cn(
        'relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none',
        isLive ? 'bg-tertiary' : 'bg-surface-container-high',
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

export function CampaignTable({ campaigns, onStatusChange, onDeleted }: CampaignTableProps) {
  const navigate = useNavigate();
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleDelete = async (campaign: Campaign) => {
    if (!window.confirm(`Delete campaign "${campaign.name}"?`)) return;
    setDeletingId(campaign.id);
    try {
      await deleteCampaign(campaign.id);
      toast.success(`Deleted ${campaign.name}`);
      onDeleted?.(campaign.id);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to delete campaign');
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="rounded-2xl bg-surface-container-lowest shadow-sm overflow-hidden border border-outline-variant/10">
      <table className="w-full">
        <thead>
          <tr className="border-b border-outline-variant/20 bg-surface-container/50">
            <th className="px-4 py-3 text-left font-label-sm text-label-sm uppercase tracking-wider text-outline">Campaign</th>
            <th className="px-4 py-3 text-left font-label-sm text-label-sm uppercase tracking-wider text-outline">ICP</th>
            <th className="px-4 py-3 text-right font-label-sm text-label-sm uppercase tracking-wider text-outline">Prospects</th>
            <th className="px-4 py-3 text-right font-label-sm text-label-sm uppercase tracking-wider text-outline">Messages</th>
            <th className="px-4 py-3 text-right font-label-sm text-label-sm uppercase tracking-wider text-outline">Replies</th>
            <th className="px-4 py-3 text-right font-label-sm text-label-sm uppercase tracking-wider text-outline">Meetings</th>
            <th className="px-4 py-3 text-center font-label-sm text-label-sm uppercase tracking-wider text-outline">Status</th>
            <th className="px-4 py-3 text-left font-label-sm text-label-sm uppercase tracking-wider text-outline">Last Activity</th>
            <th className="px-4 py-3" />
          </tr>
        </thead>
        <tbody>
          {campaigns.map((c) => (
            <tr
              key={c.id}
              className="border-b border-outline-variant/10 last:border-0 hover:bg-surface-container/40 cursor-pointer transition-colors"
              onClick={() => navigate(`/campaigns/${c.id}`)}
            >
              <td className="px-4 py-3.5">
                <p className="font-label-md text-label-md text-on-surface font-medium">{c.name}</p>
                <p className="font-label-sm text-label-sm text-outline font-mono mt-0.5 truncate max-w-[200px]">{c.id}</p>
              </td>
              <td className="px-4 py-3.5">
                <p className="font-body-sm text-body-sm text-on-surface-variant max-w-[180px] truncate" title={c.icp}>{c.icp}</p>
              </td>
              <td className="px-4 py-3.5 text-right font-label-md text-label-md text-on-surface tabular-nums">{(c.prospects ?? 0).toLocaleString()}</td>
              <td className="px-4 py-3.5 text-right font-label-md text-label-md text-on-surface tabular-nums">{(c.messages ?? 0).toLocaleString()}</td>
              <td className="px-4 py-3.5 text-right font-label-md text-label-md text-on-surface tabular-nums">{c.replies ?? 0}</td>
              <td className="px-4 py-3.5 text-right font-label-md text-label-md text-on-surface tabular-nums">{c.meetings ?? 0}</td>
              <td className="px-4 py-3.5 text-center" onClick={(e) => e.stopPropagation()}>
                <div className="flex items-center justify-center">
                  <StatusToggle campaign={c} onStatusChange={onStatusChange} />
                </div>
              </td>
              <td className="px-4 py-3.5 font-body-sm text-body-sm text-outline">{c.lastActivity ?? '—'}</td>
              <td className="px-4 py-3.5" onClick={(e) => e.stopPropagation()}>
                <div className="flex items-center justify-end gap-2">
                  <button
                    onClick={async () => {
                      try {
                        const cloned = await duplicateCampaign(c.id);
                        toast.success(`Duplicated: ${cloned.name}`);
                        navigate(`/campaigns/${cloned.id}`);
                      } catch {
                        toast.error('Failed to duplicate');
                      }
                    }}
                    className="p-1.5 rounded-lg text-outline hover:text-on-surface hover:bg-surface-container transition-colors"
                    title="Duplicate"
                  >
                    <span className="material-symbols-outlined text-[16px]">content_copy</span>
                  </button>
                  <button
                    onClick={() => handleDelete(c)}
                    disabled={deletingId === c.id}
                    className="p-1.5 rounded-lg text-outline hover:text-rose-600 hover:bg-rose-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    title="Delete campaign"
                  >
                    <span className="material-symbols-outlined text-[16px]">delete</span>
                  </button>
                  <span className="material-symbols-outlined text-[18px] text-outline">chevron_right</span>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
