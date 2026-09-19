import { useState } from 'react';
import { X } from 'lucide-react';
import { CampaignCreate, Campaign } from '@/types';
import { createCampaign } from '@/api/campaigns';
import toast from 'react-hot-toast';

interface CreateCampaignModalProps {
  onClose: () => void;
  onCreated: (campaign: Campaign) => void;
}

const emptyForm: CampaignCreate = {
  name: '',
  icp: '',
  status: 'PAUSED',
  description: '',
  goal: '',
  targetGeo: '',
  targetRoles: '',
  companySize: '',
  industry: '',
  product: '',
};

export function CreateCampaignModal({ onClose, onCreated }: CreateCampaignModalProps) {
  const [form, setForm] = useState<CampaignCreate>(emptyForm);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Partial<Record<keyof CampaignCreate, string>>>({});

  const set = (field: keyof CampaignCreate, value: string) => {
    setForm((f) => ({ ...f, [field]: value }));
    if (errors[field]) setErrors((e) => ({ ...e, [field]: '' }));
  };

  const validate = () => {
    const e: Partial<Record<keyof CampaignCreate, string>> = {};
    if (!form.name.trim()) e.name = 'Campaign name is required';
    if (!form.icp.trim()) e.icp = 'ICP definition is required';
    return e;
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length > 0) { setErrors(errs); return; }
    setLoading(true);
    try {
      const campaign = await createCampaign(form);
      onCreated(campaign);
      toast.success('Campaign created');
      onClose();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to create campaign');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border sticky top-0 bg-white rounded-t-2xl">
          <div>
            <h2 className="text-base font-semibold text-slate-900">Create Campaign</h2>
            <p className="text-xs text-slate-500 mt-0.5">Configure a new autonomous SDR campaign</p>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 transition-colors p-1 rounded-lg hover:bg-surface-secondary">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={submit} className="p-6 space-y-5">
          {/* Basic info */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Campaign Name *</label>
              <input className={`input ${errors.name ? 'border-red-400' : ''}`} value={form.name} onChange={(e) => set('name', e.target.value)} placeholder="US SaaS CTOs" />
              {errors.name && <p className="text-xs text-red-500 mt-1">{errors.name}</p>}
            </div>
            <div>
              <label className="label">Status</label>
              <select className="input" value={form.status} onChange={(e) => set('status', e.target.value as Campaign['status'])}>
                <option value="PAUSED">Paused</option>
                <option value="LIVE">Live</option>
              </select>
            </div>
          </div>

          <div>
            <label className="label">ICP Definition *</label>
            <textarea className={`input min-h-[80px] resize-none ${errors.icp ? 'border-red-400' : ''}`} value={form.icp} onChange={(e) => set('icp', e.target.value)} placeholder="CTO / VP Engineering at SaaS companies, 50–500 employees, US-based" />
            {errors.icp && <p className="text-xs text-red-500 mt-1">{errors.icp}</p>}
          </div>

          <div>
            <label className="label">Campaign Goal</label>
            <input className="input" value={form.goal ?? ''} onChange={(e) => set('goal', e.target.value)} placeholder="Book discovery calls with technical decision makers" />
          </div>

          <div>
            <label className="label">Product / Offering</label>
            <input className="input" value={form.product ?? ''} onChange={(e) => set('product', e.target.value)} placeholder="AI-powered developer productivity platform" />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Target Geography</label>
              <input className="input" value={form.targetGeo ?? ''} onChange={(e) => set('targetGeo', e.target.value)} placeholder="United States" />
            </div>
            <div>
              <label className="label">Target Roles</label>
              <input className="input" value={form.targetRoles ?? ''} onChange={(e) => set('targetRoles', e.target.value)} placeholder="CTO, VP Engineering" />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Company Size</label>
              <input className="input" value={form.companySize ?? ''} onChange={(e) => set('companySize', e.target.value)} placeholder="50–500 employees" />
            </div>
            <div>
              <label className="label">Industry</label>
              <input className="input" value={form.industry ?? ''} onChange={(e) => set('industry', e.target.value)} placeholder="SaaS / Software" />
            </div>
          </div>

          {/* Knowledge Base section */}
          <div>
            <p className="text-xs font-semibold text-slate-700 mb-3 uppercase tracking-wide">Knowledge Base</p>
            <div className="grid grid-cols-3 gap-2">
              {['Product Information', 'Case Studies', 'Sales Playbook', 'ICP Definition', 'Objection Handling', 'Example Messages'].map((item) => (
                <div key={item} className="flex items-center gap-2 p-2.5 rounded-lg border border-dashed border-border hover:border-brand hover:bg-brand/5 cursor-pointer transition-colors text-xs text-slate-500">
                  + {item}
                </div>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-2 border-t border-border">
            <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
            <button type="submit" disabled={loading} className="btn-primary">
              {loading ? 'Creating...' : 'Create Campaign'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
