import { useEffect, useState } from 'react';
import { Campaign } from '@/types';
import { getCampaigns } from '@/api/campaigns';
import { CampaignTable } from '@/components/campaign/CampaignTable';
import { CreateCampaignModal } from '@/components/campaign/CreateCampaignModal';

export function Campaigns() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [search, setSearch] = useState('');

  useEffect(() => {
    getCampaigns().then(setCampaigns).finally(() => setLoading(false));

    const handleUpdate = () => {
      getCampaigns().then(setCampaigns);
    };
    window.addEventListener('prospects-updated', handleUpdate);
    return () => window.removeEventListener('prospects-updated', handleUpdate);
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
    <div className="w-full bg-surface min-h-screen px-space-lg py-space-lg">
      {/* Breadcrumb + header row */}
      <div className="flex flex-wrap items-center justify-between gap-space-sm mb-space-md">
        <div className="flex items-center gap-space-xs font-body-sm text-body-sm text-on-surface-variant">
          <span>Home</span>
          <span className="material-symbols-outlined text-[15px] text-outline">chevron_right</span>
          <span className="font-label-md text-label-md text-on-surface font-medium">Campaigns</span>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-1.5 px-4 py-2 rounded-full bg-primary-container text-on-primary-container hover:bg-inverse-primary font-label-md text-label-md shadow-sm transition-all active:scale-95"
        >
          <span className="material-symbols-outlined text-[18px]">add_circle</span>
          Create Campaign
        </button>
      </div>

      {/* Page heading */}
      <div className="mb-space-lg">
        <h1 className="font-headline-lg text-headline-lg text-on-surface tracking-tight leading-snug">
          Campaigns
        </h1>
        <p className="font-body-md text-body-md text-on-surface-variant mt-1">
          Create and manage autonomous SDR campaigns.
        </p>
      </div>

      {/* Search */}
      <div className="relative mb-space-md max-w-sm">
        <span className="material-symbols-outlined absolute left-3 top-2.5 text-[18px] text-outline select-none">search</span>
        <input
          type="text"
          placeholder="Search campaigns..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full bg-surface-container-lowest rounded-xl pl-9 pr-space-sm py-2 font-body-sm text-body-sm text-on-surface placeholder:text-outline focus:outline-none focus:bg-surface-container transition-colors shadow-sm border border-outline-variant/20"
        />
      </div>

      {/* Table / states */}
      {loading ? (
        <div className="rounded-2xl bg-surface-container-lowest shadow-sm p-space-lg">
          <div className="flex flex-col gap-3">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-10 rounded-xl bg-surface-container animate-pulse" />
            ))}
          </div>
        </div>
      ) : filtered.length === 0 ? (
        <div className="rounded-2xl bg-surface-container-lowest shadow-sm p-space-xl flex flex-col items-center gap-space-md text-center">
          <div className="w-12 h-12 rounded-2xl bg-primary-fixed/30 flex items-center justify-center">
            <span className="material-symbols-outlined text-[24px] text-on-primary-fixed-variant">campaign</span>
          </div>
          <div>
            <h3 className="font-headline-sm text-headline-sm text-on-surface">
              {search ? 'No matching campaigns' : 'No campaigns yet'}
            </h3>
            <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">
              {search ? 'Try a different search term.' : 'Create your first campaign to start prospecting.'}
            </p>
          </div>
          {!search && (
            <button
              onClick={() => setShowCreate(true)}
              className="flex items-center gap-1.5 px-4 py-2 rounded-full bg-primary-container text-on-primary-container font-label-md text-label-md shadow-sm hover:bg-inverse-primary transition-all"
            >
              <span className="material-symbols-outlined text-[18px]">add_circle</span>
              Create Campaign
            </button>
          )}
        </div>
      ) : (
        <CampaignTable
          campaigns={filtered}
          onStatusChange={handleStatusChange}
          onDeleted={(id) => setCampaigns((prev) => prev.filter((c) => c.id !== id))}
        />
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
