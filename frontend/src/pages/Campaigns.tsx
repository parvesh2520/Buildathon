import { useEffect, useState } from 'react';
import { Plus, Search } from 'lucide-react';
import { Campaign } from '@/types';
import { getCampaigns } from '@/api/campaigns';
import { CampaignTable } from '@/components/campaign/CampaignTable';
import { CreateCampaignModal } from '@/components/campaign/CreateCampaignModal';
import { EmptyState } from '@/components/shared/EmptyState';
import { TableSkeleton } from '@/components/shared/LoadingSkeleton';
import { Megaphone } from 'lucide-react';

export function Campaigns() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [search, setSearch] = useState('');

  useEffect(() => {
    getCampaigns().then(setCampaigns).finally(() => setLoading(false));
  }, []);

  const filtered = campaigns.filter(
    (c) =>
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      c.id.toLowerCase().includes(search.toLowerCase())
  );

  const handleStatusChange = (id: string, status: Campaign['status']) => {
    setCampaigns((prev) => prev.map((c) => (c.id === id ? { ...c, status } : c)));
  };

  return (
    <div className="p-6 max-w-[1400px] mx-auto">
      <div className="flex items-start justify-between page-header">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Campaigns</h1>
          <p className="text-sm text-slate-500 mt-1">Create and manage autonomous SDR campaigns.</p>
        </div>
        <button className="btn-primary" onClick={() => setShowCreate(true)}>
          <Plus size={15} />
          Create Campaign
        </button>
      </div>

      {/* Search */}
      <div className="relative mb-5 max-w-xs">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
        <input
          className="input pl-8"
          placeholder="Search campaigns..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {loading ? (
        <div className="card"><TableSkeleton rows={4} cols={8} /></div>
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={<Megaphone size={20} />}
          title={search ? 'No matching campaigns' : 'No campaigns yet'}
          description={search ? 'Try a different search term.' : 'Create your first campaign to start prospecting.'}
          action={!search && (
            <button className="btn-primary" onClick={() => setShowCreate(true)}>
              <Plus size={14} /> Create Campaign
            </button>
          )}
        />
      ) : (
        <CampaignTable campaigns={filtered} onStatusChange={handleStatusChange} />
      )}

      {showCreate && (
        <CreateCampaignModal
          onClose={() => setShowCreate(false)}
          onCreated={(c) => setCampaigns((prev) => [c, ...prev])}
        />
      )}
    </div>
  );
}
