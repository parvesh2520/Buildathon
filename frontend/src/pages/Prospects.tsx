import { useEffect, useState } from 'react';
import { Prospect } from '@/types';
import { getProspects } from '@/api/prospects';
import { getActiveDiscoveries } from '@/api/discovery';
import { ProspectTable } from '@/components/prospect/ProspectTable';
import { ProspectDrawer } from '@/components/prospect/ProspectDrawer';
import { AddProspectModal } from '@/components/prospect/AddProspectModal';
import { ProspectDiscoveryLoadingCard, ProspectDiscoveryLoadingBanner } from '@/components/prospect/ProspectDiscoveryLoading';

export function Prospects() {
  const [prospects, setProspects] = useState<Prospect[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedProspect, setSelectedProspect] = useState<Prospect | null>(null);
  const [showAdd, setShowAdd] = useState(false);
  const [activeDiscoveries, setActiveDiscoveries] = useState<Record<string, { count: number; timestamp: number }>>(() => getActiveDiscoveries());

  useEffect(() => {
    getProspects().then(setProspects).finally(() => setLoading(false));

    const handleUpdate = () => {
      getProspects().then(setProspects);
      setActiveDiscoveries(getActiveDiscoveries());
    };
    const handleStart = () => {
      setActiveDiscoveries(getActiveDiscoveries());
    };
    const handleEnd = () => {
      setActiveDiscoveries(getActiveDiscoveries());
    };

    window.addEventListener('prospects-updated', handleUpdate);
    window.addEventListener('agent0-discovery-start', handleStart);
    window.addEventListener('agent0-discovery-end', handleEnd);

    return () => {
      window.removeEventListener('prospects-updated', handleUpdate);
      window.removeEventListener('agent0-discovery-start', handleStart);
      window.removeEventListener('agent0-discovery-end', handleEnd);
    };
  }, []);

  const filtered = prospects.filter(
    (p) =>
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.company.toLowerCase().includes(search.toLowerCase()) ||
      p.email.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="w-full bg-surface min-h-screen px-space-lg py-space-lg">
      {/* Breadcrumb + header */}
      <div className="flex flex-wrap items-center justify-between gap-space-sm mb-space-md">
        <div className="flex items-center gap-space-xs font-body-sm text-body-sm text-on-surface-variant">
          <span>Home</span>
          <span className="material-symbols-outlined text-[15px] text-outline">chevron_right</span>
          <span className="font-label-md text-label-md text-on-surface font-medium">Prospects</span>
          {!loading && (
            <span className="ml-space-xs px-2 py-0.5 rounded-full bg-tertiary/10 text-tertiary font-label-sm text-label-sm flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-tertiary"></span>
              {prospects.length} total
            </span>
          )}
        </div>
        <button
          onClick={() => setShowAdd(true)}
          className="flex items-center gap-1.5 px-4 py-2 rounded-full bg-primary-container text-on-primary-container hover:bg-inverse-primary font-label-md text-label-md shadow-sm transition-all active:scale-95"
        >
          <span className="material-symbols-outlined text-[18px]">person_add</span>
          Add Prospect
        </button>
      </div>

      {/* Heading */}
      <div className="mb-space-lg">
        <h1 className="font-headline-lg text-headline-lg text-on-surface tracking-tight leading-snug">
          Prospects
        </h1>
        <p className="font-body-md text-body-md text-on-surface-variant mt-1">
          Manage and track your sales prospects.
        </p>
      </div>

      {/* Search */}
      <div className="relative mb-space-md max-w-sm">
        <span className="material-symbols-outlined absolute left-3 top-2.5 text-[18px] text-outline select-none">search</span>
        <input
          type="text"
          placeholder="Search by name, company, email…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full bg-surface-container-lowest rounded-xl pl-9 pr-space-sm py-2 font-body-sm text-body-sm text-on-surface placeholder:text-outline focus:outline-none focus:bg-surface-container transition-colors shadow-sm border border-outline-variant/20"
        />
      </div>

      {/* Active discovery banner if prospects exist */}
      {Object.keys(activeDiscoveries).length > 0 && filtered.length > 0 && (
        <ProspectDiscoveryLoadingBanner
          count={Object.values(activeDiscoveries).reduce((acc, curr) => acc + curr.count, 0)}
        />
      )}

      {/* Table / loading / empty */}
      {loading ? (
        <div className="rounded-2xl bg-surface-container-lowest shadow-sm p-space-lg flex flex-col gap-3">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-10 rounded-xl bg-surface-container animate-pulse" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        Object.keys(activeDiscoveries).length > 0 && !search ? (
          <ProspectDiscoveryLoadingCard
            count={Object.values(activeDiscoveries).reduce((acc, curr) => acc + curr.count, 0)}
          />
        ) : (
          <div className="rounded-2xl bg-surface-container-lowest shadow-sm p-space-xl flex flex-col items-center gap-space-md text-center">
            <div className="w-12 h-12 rounded-2xl bg-primary-fixed/30 flex items-center justify-center">
              <span className="material-symbols-outlined text-[24px] text-on-primary-fixed-variant">people</span>
            </div>
            <div>
              <h3 className="font-headline-sm text-headline-sm text-on-surface">
                {search ? 'No matching prospects' : 'No prospects yet'}
              </h3>
              <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">
                {search ? 'Try a different search term.' : 'Add your first prospect to start the pipeline.'}
              </p>
            </div>
            {!search && (
              <button
                onClick={() => setShowAdd(true)}
                className="flex items-center gap-1.5 px-4 py-2 rounded-full bg-primary-container text-on-primary-container font-label-md text-label-md shadow-sm hover:bg-inverse-primary transition-all"
              >
                <span className="material-symbols-outlined text-[18px]">person_add</span>
                Add Prospect
              </button>
            )}
          </div>
        )
      ) : (
        <ProspectTable
          prospects={filtered}
          onSelectProspect={setSelectedProspect}
          onDeleted={(id) => setProspects((prev) => prev.filter((p) => p.id !== id))}
        />
      )}

      {selectedProspect && (
        <ProspectDrawer
          prospect={selectedProspect}
          onClose={() => setSelectedProspect(null)}
          onDeleted={(id) => {
            setProspects((prev) => prev.filter((p) => p.id !== id));
            setSelectedProspect(null);
          }}
          onUpdated={(updated) => {
            setProspects((prev) => prev.map((p) => (p.id === updated.id ? updated : p)));
          }}
        />
      )}

      {showAdd && (
        <AddProspectModal
          onClose={() => setShowAdd(false)}
          onCreated={(p) => setProspects((prev) => [p, ...prev])}
        />
      )}
    </div>
  );
}
