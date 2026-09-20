import { useEffect, useState } from 'react';
import { Campaign, ProspectCreate, Prospect } from '@/types';
import { createProspect } from '@/api/prospects';
import { runSDR } from '@/api/sdr';
import { getCampaigns } from '@/api/campaigns';
import toast from 'react-hot-toast';
import { cn } from '@/lib/utils';

interface AddProspectModalProps {
  onClose: () => void;
  onCreated: (prospect: Prospect) => void;
}

const emptyForm: ProspectCreate = {
  name: '', email: '', phone: '', title: '', company: '',
  domain: '', location: '', companySize: '', notes: '', campaignId: 'us_saas_cto',
};

export function AddProspectModal({ onClose, onCreated }: AddProspectModalProps) {
  const [form, setForm] = useState<ProspectCreate>(emptyForm);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [autoRunSdr, setAutoRunSdr] = useState(true);
  const [loading, setLoading] = useState(false);
  const [campaignLoading, setCampaignLoading] = useState(true);
  const [errors, setErrors] = useState<Partial<Record<keyof ProspectCreate, string>>>({});

  useEffect(() => {
    getCampaigns()
      .then((items) => {
        setCampaigns(items);
        if (items.length > 0) {
          setForm((f) => ({
            ...f,
            campaignId: items.some((c) => c.id === f.campaignId) ? f.campaignId : items[0].id,
          }));
        }
      })
      .catch(() => toast.error('Failed to load campaigns'))
      .finally(() => setCampaignLoading(false));
  }, []);

  const set = (field: keyof ProspectCreate, value: string) => {
    setForm((f) => ({ ...f, [field]: value }));
    if (errors[field]) setErrors((e) => ({ ...e, [field]: '' }));
  };

  const validate = () => {
    const e: Partial<Record<keyof ProspectCreate, string>> = {};
    if (!form.name.trim()) e.name = 'Required';
    if (!form.email.trim()) e.email = 'Required';
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) e.email = 'Invalid email';
    if (!form.title.trim()) e.title = 'Required';
    if (!form.company.trim()) e.company = 'Required';
    return e;
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length > 0) { setErrors(errs); return; }
    setLoading(true);
    try {
      const prospect = await createProspect(form);
      if (!prospect.channel || prospect.channel === 'EMAIL') {
        const n = (form.notes || '').toLowerCase();
        if (n.includes('sms')) prospect.channel = 'SMS';
        else if (n.includes('call') || n.includes('phone') || n.includes('voice')) prospect.channel = 'PHONE';
      }
      if (autoRunSdr && form.campaignId) {
        toast.loading('Running autonomous SDR…', { id: 'sdr-run' });
        try {
          const sdrRes = await runSDR({ campaign_id: form.campaignId, prospect_id: prospect.id });
          if (sdrRes.status === 'FAILED' || sdrRes.status === 'BLOCKED') {
            toast.error(`SDR ${sdrRes.status}: ${sdrRes.error || 'Execution issue'}`, { id: 'sdr-run' });
          } else {
            const ch = (sdrRes.actual_channel || sdrRes.recommended_channel || (sdrRes as any).channel_result?.channel || prospect.channel || 'Outreach') as any;
            toast.success(`SDR Complete: ${ch} (${sdrRes.status})`, { id: 'sdr-run' });
            prospect.status = sdrRes.status === 'NO_FIT' ? 'NO_FIT' : 'CONTACTED';
            prospect.channel = (sdrRes.actual_channel || sdrRes.recommended_channel || (sdrRes as any).channel_result?.channel || prospect.channel || 'EMAIL') as any;
            if ((sdrRes as any).icp_result?.score) prospect.icpScore = (sdrRes as any).icp_result.score;
          }
        } catch { toast.error('Prospect saved, SDR encountered an issue', { id: 'sdr-run' }); }
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

  const Field = ({ k, label, placeholder, required = false }: { k: keyof ProspectCreate; label: string; placeholder: string; required?: boolean }) => (
    <div className="flex flex-col gap-1">
      <label className="font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider">
        {label}{required && <span className="text-primary ml-0.5">*</span>}
      </label>
      <input
        value={(form[k] as string) ?? ''}
        onChange={(e) => set(k, e.target.value)}
        placeholder={placeholder}
        className={cn(
          'bg-surface-container rounded-xl px-3 py-2 font-body-sm text-body-sm text-on-surface placeholder:text-outline focus:outline-none focus:bg-surface-container-low transition-colors border',
          errors[k] ? 'border-secondary' : 'border-outline-variant/20'
        )}
      />
      {errors[k] && <p className="font-label-sm text-label-sm text-secondary">{errors[k]}</p>}
    </div>
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-inverse-surface/20 backdrop-blur-sm">
      <div className="bg-surface-container-lowest rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto border border-outline-variant/20">

        {/* Header */}
        <div className="flex items-center justify-between px-space-lg py-space-md border-b border-outline-variant/20 sticky top-0 bg-surface-container-lowest rounded-t-2xl">
          <div className="flex items-center gap-space-sm">
            <div className="w-8 h-8 rounded-xl bg-primary-container flex items-center justify-center">
              <span className="material-symbols-outlined text-on-primary-container text-[18px]">person_add</span>
            </div>
            <div>
              <h2 className="font-headline-sm text-headline-sm text-on-surface">Add Prospect</h2>
              <p className="font-label-sm text-label-sm text-outline">Add a new prospect to your autonomous pipeline</p>
            </div>
          </div>
          <button onClick={onClose} className="w-8 h-8 flex items-center justify-center rounded-xl hover:bg-surface-container text-outline hover:text-on-surface transition-colors">
            <span className="material-symbols-outlined text-[20px]">close</span>
          </button>
        </div>

        <form onSubmit={submit} className="px-space-lg py-space-md flex flex-col gap-space-md">

          {/* Row 1 */}
          <div className="grid grid-cols-2 gap-space-sm">
            <Field k="name" label="Full Name" placeholder="Jane Smith" required />
            <Field k="title" label="Job Title" placeholder="CTO" required />
          </div>

          {/* Row 2 */}
          <div className="grid grid-cols-2 gap-space-sm">
            <Field k="email" label="Email" placeholder="jane@example.com" required />
            <Field k="phone" label="Phone (SMS)" placeholder="+1 555 000 0000" />
          </div>

          {/* Row 3 */}
          <div className="grid grid-cols-2 gap-space-sm">
            <Field k="company" label="Company" placeholder="Acme Inc" required />
            <Field k="domain" label="Domain" placeholder="acme.com" />
          </div>

          {/* Row 4 */}
          <div className="grid grid-cols-2 gap-space-sm">
            <Field k="companySize" label="Company Size" placeholder="200 employees" />
            <Field k="location" label="Location" placeholder="San Francisco, CA" />
          </div>

          {/* Campaign */}
          <div className="flex flex-col gap-1">
            <label className="font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider">Campaign</label>
            <select
              value={form.campaignId ?? ''}
              onChange={(e) => set('campaignId', e.target.value)}
              disabled={campaignLoading || campaigns.length === 0}
              className="bg-surface-container rounded-xl px-3 py-2 font-body-sm text-body-sm text-on-surface border border-outline-variant/20 focus:outline-none focus:bg-surface-container-low transition-colors disabled:opacity-50"
            >
              {campaigns.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
            {!campaignLoading && campaigns.length === 0 && (
              <p className="font-label-sm text-label-sm text-secondary">No campaigns returned by backend.</p>
            )}
          </div>

          {/* Notes */}
          <div className="flex flex-col gap-1">
            <label className="font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider">Notes & Context</label>
            <textarea
              value={form.notes ?? ''}
              onChange={(e) => set('notes', e.target.value)}
              placeholder="E.g. Expanding engineering team, interested in AI automation…"
              rows={3}
              className="bg-surface-container rounded-xl px-3 py-2 font-body-sm text-body-sm text-on-surface placeholder:text-outline border border-outline-variant/20 focus:outline-none focus:bg-surface-container-low transition-colors resize-none"
            />
          </div>

          {/* Auto SDR toggle */}
          <div
            onClick={() => setAutoRunSdr(!autoRunSdr)}
            className={cn(
              'rounded-xl p-space-md flex items-start gap-space-sm cursor-pointer border transition-colors',
              autoRunSdr ? 'bg-primary-fixed/20 border-primary-container/40' : 'bg-surface-container border-outline-variant/20'
            )}
          >
            <div className={cn(
              'w-5 h-5 rounded-md border-2 flex items-center justify-center flex-shrink-0 mt-0.5 transition-colors',
              autoRunSdr ? 'bg-primary-container border-primary-container' : 'border-outline-variant/50'
            )}>
              {autoRunSdr && <span className="material-symbols-outlined text-on-primary-container text-[14px]">check</span>}
            </div>
            <div>
              <p className="font-label-md text-label-md text-on-surface font-semibold flex items-center gap-1.5">
                <span className="material-symbols-outlined text-[16px] text-primary">auto_awesome</span>
                Run Autonomous SDR Immediately
              </p>
              <p className="font-body-sm text-body-sm text-on-surface-variant mt-0.5">
                Research lead, qualify ICP, generate personalised outreach and send automatically.
              </p>
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end gap-space-sm pt-space-sm border-t border-outline-variant/20">
            <button type="button" onClick={onClose} className="px-4 py-2 rounded-full bg-surface-container hover:bg-surface-container-high text-on-surface font-label-md text-label-md transition-colors">
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex items-center gap-1.5 px-5 py-2 rounded-full bg-primary-container text-on-primary-container hover:bg-inverse-primary font-label-md text-label-md shadow-sm transition-all active:scale-95 disabled:opacity-60"
            >
              {loading ? (
                <><span className="material-symbols-outlined text-[16px] animate-spin">refresh</span>Processing…</>
              ) : autoRunSdr ? (
                <><span className="material-symbols-outlined text-[16px]">rocket_launch</span>Add & Send Outreach</>
              ) : (
                <><span className="material-symbols-outlined text-[16px]">person_add</span>Add Prospect</>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
