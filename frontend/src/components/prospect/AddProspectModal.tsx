import { useState } from 'react';
import { X, Sparkles } from 'lucide-react';
import { ProspectCreate, Prospect } from '@/types';
import { createProspect } from '@/api/prospects';
import { runSDR } from '@/api/sdr';
import { demoCampaigns } from '@/data/demo/campaigns';
import toast from 'react-hot-toast';

interface AddProspectModalProps {
  onClose: () => void;
  onCreated: (prospect: Prospect) => void;
}

const emptyForm: ProspectCreate = {
  name: '',
  email: '',
  phone: '',
  title: '',
  company: '',
  domain: '',
  location: '',
  companySize: '',
  notes: '',
  campaignId: 'us_saas_cto',
};

export function AddProspectModal({ onClose, onCreated }: AddProspectModalProps) {
  const [form, setForm] = useState<ProspectCreate>(emptyForm);
  const [autoRunSdr, setAutoRunSdr] = useState(true);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Partial<Record<keyof ProspectCreate, string>>>({});

  const set = (field: keyof ProspectCreate, value: string) => {
    setForm((f) => ({ ...f, [field]: value }));
    if (errors[field]) setErrors((e) => ({ ...e, [field]: '' }));
  };

  const validate = () => {
    const e: Partial<Record<keyof ProspectCreate, string>> = {};
    if (!form.name.trim()) e.name = 'Name is required';
    if (!form.email.trim()) e.email = 'Email is required';
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) e.email = 'Invalid email';
    if (!form.title.trim()) e.title = 'Title is required';
    if (!form.company.trim()) e.company = 'Company is required';
    return e;
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length > 0) { setErrors(errs); return; }
    setLoading(true);
    try {
      const prospect = await createProspect(form);

      if (autoRunSdr && form.campaignId) {
        toast.loading('Autonomous SDR: Researching lead & dispatching outreach...', { id: 'sdr-run' });
        try {
          const sdrRes = await runSDR({ campaign_id: form.campaignId, prospect_id: prospect.id });
          if (sdrRes.status === 'FAILED' || sdrRes.status === 'BLOCKED') {
            toast.error(`SDR Execution ${sdrRes.status}: ${sdrRes.error || 'Execution encountered an issue'}`, { id: 'sdr-run' });
          } else {
            const ch = sdrRes.actual_channel || sdrRes.recommended_channel || 'Outreach';
            toast.success(`Autonomous SDR Complete: ${ch} (${sdrRes.status})`, { id: 'sdr-run' });
            prospect.status = sdrRes.status === 'NO_FIT' ? 'NO_FIT' : 'CONTACTED';
          }
        } catch (sdrErr) {
          toast.error('Prospect saved, but SDR run encountered an issue', { id: 'sdr-run' });
        }
      } else {
        toast.success('Prospect added to pipeline');
      }

      onCreated(prospect);
      onClose();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to add prospect');
    } finally {
      setLoading(false);
    }
  };

  const field = (key: keyof ProspectCreate, label: string, placeholder: string, required = false) => (
    <div>
      <label className="label">{label}{required && ' *'}</label>
      <input className={`input ${errors[key] ? 'border-red-400' : ''}`} value={(form[key] as string) ?? ''} onChange={(e) => set(key, e.target.value)} placeholder={placeholder} />
      {errors[key] && <p className="text-xs text-red-500 mt-1">{errors[key]}</p>}
    </div>
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between px-6 py-4 border-b border-border sticky top-0 bg-white rounded-t-2xl">
          <div>
            <h2 className="text-base font-semibold text-slate-900">Add Prospect</h2>
            <p className="text-xs text-slate-500 mt-0.5">Add a new prospect to your autonomous pipeline</p>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-surface-secondary">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={submit} className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            {field('name', 'Full Name', 'Jane Smith', true)}
            {field('title', 'Job Title', 'CTO', true)}
          </div>
          <div className="grid grid-cols-2 gap-4">
            {field('email', 'Email Address', 'jane@example.com', true)}
            {field('phone', 'Phone Number (for SMS)', '+917419045750')}
          </div>
          <div className="grid grid-cols-2 gap-4">
            {field('company', 'Company', 'Acme Inc', true)}
            {field('domain', 'Domain', 'acme.com')}
          </div>
          <div className="grid grid-cols-2 gap-4">
            {field('companySize', 'Company Size', '200 employees')}
            {field('location', 'Location', 'San Francisco, CA')}
          </div>

          <div>
            <label className="label">Campaign</label>
            <select className="input" value={form.campaignId ?? ''} onChange={(e) => set('campaignId', e.target.value)}>
              {demoCampaigns.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="label">Notes & Context</label>
            <textarea className="input min-h-[70px] resize-none" value={form.notes ?? ''} onChange={(e) => set('notes', e.target.value)} placeholder="E.g. Expanding engineering team, interested in AI automation..." />
          </div>

          {/* Autonomous Outreach Option */}
          <div className="p-3 bg-brand/5 border border-brand/20 rounded-xl flex items-start gap-3 cursor-pointer" onClick={() => setAutoRunSdr(!autoRunSdr)}>
            <input
              type="checkbox"
              id="autoRunSdr"
              checked={autoRunSdr}
              onChange={(e) => setAutoRunSdr(e.target.checked)}
              className="mt-0.5 h-4 w-4 rounded border-gray-300 text-brand focus:ring-brand"
            />
            <label htmlFor="autoRunSdr" className="text-xs cursor-pointer select-none">
              <span className="font-semibold text-slate-800 flex items-center gap-1.5">
                <Sparkles size={13} className="text-brand" /> Run Autonomous SDR Immediately
              </span>
              <span className="text-slate-500 block mt-0.5">
                Automatically research lead, qualify ICP with DronaHQ, generate personalized outreach, and send email.
              </span>
            </label>
          </div>

          <div className="flex items-center justify-end gap-3 pt-2 border-t border-border">
            <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
            <button type="submit" disabled={loading} className="btn-primary">
              {loading ? 'Processing...' : autoRunSdr ? 'Add & Send Outreach' : 'Add Prospect'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
