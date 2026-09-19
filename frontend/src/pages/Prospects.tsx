import { useEffect, useState } from 'react';
import { Plus, Search } from 'lucide-react';
import { Prospect } from '@/types';
import { getProspects } from '@/api/prospects';
import { ProspectTable } from '@/components/prospect/ProspectTable';
import { ProspectDrawer } from '@/components/prospect/ProspectDrawer';
import { AddProspectModal } from '@/components/prospect/AddProspectModal';
import { TableSkeleton } from '@/components/shared/LoadingSkeleton';

export function Prospects() {
  const [prospects, setProspects] = useState<Prospect[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedProspect, setSelectedProspect] = useState<Prospect | null>(null);
  const [showAdd, setShowAdd] = useState(false);

  useEffect(() => {
    getProspects().then(setProspects).finally(() => setLoading(false));
  }, []);

  const filtered = prospects.filter(
    (p) =>
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.company.toLowerCase().includes(search.toLowerCase()) ||
      p.email.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="p-6 max-w-[1400px] mx-auto">
      <div className="flex items-start justify-between page-header">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Prospects</h1>
          <p className="text-sm text-slate-500 mt-1">Manage and track your sales prospects.</p>
        </div>
        <button className="btn-primary" onClick={() => setShowAdd(true)}>
          <Plus size={15} />
          Add Prospect
        </button>
      </div>

      <div className="relative mb-5 max-w-xs">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
        <input
          className="input pl-8"
          placeholder="Search prospects..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {loading ? (
        <div className="card"><TableSkeleton rows={6} cols={8} /></div>
      ) : (
        <ProspectTable prospects={filtered} onSelectProspect={setSelectedProspect} />
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
