import { useState } from 'react';
import { CampaignCreate, Campaign } from '@/types';
import { createCampaign } from '@/api/campaigns';
import { runDiscoveryAgent, setCampaignDiscovering } from '@/api/discovery';
import toast from 'react-hot-toast';
import { cn } from '@/lib/utils';

interface CreateCampaignModalProps {
  onClose: () => void;
  onCreated: (campaign: Campaign) => void;
}

const emptyForm: CampaignCreate = {
  name: '', icp: '', status: 'LIVE', description: '',
  goal: '', targetGeo: '', targetRoles: '', companySize: '', industry: '', product: '',
};

export function CreateCampaignModal({ onClose, onCreated }: CreateCampaignModalProps) {
  const [form, setForm] = useState<CampaignCreate>(emptyForm);
  const [targetProspectCount, setTargetProspectCount] = useState<number>(5);
  const [autoStartAgent0, setAutoStartAgent0] = useState<boolean>(true);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Partial<Record<keyof CampaignCreate, string>>>({});

  const set = (field: keyof CampaignCreate, value: string) => {
    setForm((f) => ({ ...f, [field]: value }));
    if (errors[field]) setErrors((e) => ({ ...e, [field]: '' }));
  };

  const validate = () => {
    const e: Partial<Record<keyof CampaignCreate, string>> = {};
    if (!form.name.trim()) e.name = 'Required';
    if (!form.icp.trim()) e.icp = 'Required';
    return e;
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length > 0) { setErrors(errs); return; }
    setLoading(true);
    try {
      const campaign = await createCampaign(form);
      toast.success(`Campaign "${campaign.name}" created!`);
      onCreated(campaign);
      onClose();

      // Run Agent 0 in background (non-blocking)
      if (autoStartAgent0 && targetProspectCount > 0) {
        setCampaignDiscovering(campaign.id, true, targetProspectCount);
        window.dispatchEvent(new CustomEvent('agent0-discovery-start', { detail: { campaignId: campaign.id, count: targetProspectCount } }));

        toast.loading(`Agent 0 running in background: discovering ${targetProspectCount} prospects…`, {
          id: `agent-0-${campaign.id}`,
          duration: 4000,
        });

        runDiscoveryAgent(campaign.id, targetProspectCount, form.icp)
          .then((res) => {
            const countFound = res.stored_count || res.prospects?.length || targetProspectCount;
            toast.success(`Agent 0 completed: ${countFound} prospects discovered & enrolled into "${campaign.name}"!`, {
              id: `agent-0-${campaign.id}`,
              duration: 5000,
            });
            window.dispatchEvent(new CustomEvent('prospects-updated', { detail: { campaignId: campaign.id } }));
          })
          .catch((err) => {
            console.error('Agent 0 discovery notice:', err);
            const message =
              err instanceof Error && err.message.includes('VITE_API_BASE_URL')
                ? 'Agent 0 could not reach the backend. Add VITE_API_BASE_URL to your Vercel environment pointing to your Render API.'
                : 'Agent 0 background discovery notice: check campaign prospects';

            toast.error(message, {
              id: `agent-0-${campaign.id}`,
            });
          })
          .finally(() => {
            setCampaignDiscovering(campaign.id, false);
            window.dispatchEvent(new CustomEvent('agent0-discovery-end', { detail: { campaignId: campaign.id } }));
          });
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to create campaign');
    } finally {
      setLoading(false);
    }
  };

  const Field = ({
    k, label, placeholder, required = false, textarea = false,
  }: { k: keyof CampaignCreate; label: string; placeholder: string; required?: boolean; textarea?: boolean }) => (
    <div className="flex flex-col gap-1">
      <label className="font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider">
        {label}{required && <span className="text-primary ml-0.5">*</span>}
      </label>
      {textarea ? (
        <textarea
          value={(form[k] as string) ?? ''}
          onChange={(e) => set(k, e.target.value)}
          placeholder={placeholder}
          rows={3}
          className={cn(
            'bg-surface-container rounded-xl px-3 py-2 font-body-sm text-body-sm text-on-surface placeholder:text-outline border focus:outline-none focus:bg-surface-container-low transition-colors resize-none',
            errors[k] ? 'border-secondary' : 'border-outline-variant/20'
          )}
        />
      ) : (
        <input
          value={(form[k] as string) ?? ''}
          onChange={(e) => set(k, e.target.value)}
          placeholder={placeholder}
          className={cn(
            'bg-surface-container rounded-xl px-3 py-2 font-body-sm text-body-sm text-on-surface placeholder:text-outline border focus:outline-none focus:bg-surface-container-low transition-colors',
            errors[k] ? 'border-secondary' : 'border-outline-variant/20'
          )}
        />
      )}
      {errors[k] && <p className="font-label-sm text-label-sm text-secondary">{errors[k]}</p>}
    </div>
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-inverse-surface/20 backdrop-blur-sm">
      <div className="bg-surface-container-lowest rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto border border-outline-variant/20">

        {/* Header */}
        <div className="flex items-center justify-between px-space-lg py-space-md border-b border-outline-variant/20 sticky top-0 bg-surface-container-lowest rounded-t-2xl">
          <div className="flex items-center gap-space-sm">
            <div className="w-8 h-8 rounded-xl bg-primary-container flex items-center justify-center">
              <span className="material-symbols-outlined text-on-primary-container text-[18px]">campaign</span>
            </div>
            <div>
              <h2 className="font-headline-sm text-headline-sm text-on-surface">Create Campaign</h2>
              <p className="font-label-sm text-label-sm text-outline">Configure a new autonomous SDR campaign</p>
            </div>
          </div>
          <button onClick={onClose} className="w-8 h-8 flex items-center justify-center rounded-xl hover:bg-surface-container text-outline hover:text-on-surface transition-colors">
            <span className="material-symbols-outlined text-[20px]">close</span>
          </button>
        </div>

        <form onSubmit={submit} className="px-space-lg py-space-md flex flex-col gap-space-md">

          {/* Name + Status */}
          <div className="grid grid-cols-2 gap-space-sm">
            <Field k="name" label="Campaign Name" placeholder="US SaaS CTOs" required />
            <div className="flex flex-col gap-1">
              <label className="font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider">Status</label>
              <select
                value={form.status}
                onChange={(e) => set('status', e.target.value as Campaign['status'])}
                className="bg-surface-container rounded-xl px-3 py-2 font-body-sm text-body-sm text-on-surface border border-outline-variant/20 focus:outline-none focus:bg-surface-container-low transition-colors"
              >
                <option value="PAUSED">Paused</option>
                <option value="LIVE">Live</option>
              </select>
            </div>
          </div>

          {/* ICP */}
          <Field k="icp" label="ICP Definition" placeholder="CTO / VP Engineering at SaaS companies, 50–500 employees, US-based" required textarea />

          {/* Goal + Product */}
          <div className="grid grid-cols-2 gap-space-sm">
            <Field k="goal" label="Campaign Goal" placeholder="Book discovery calls with technical decision makers" />
            <Field k="product" label="Product / Offering" placeholder="AI-powered developer productivity platform" />
          </div>

          {/* Geo + Roles */}
          <div className="grid grid-cols-2 gap-space-sm">
            <Field k="targetGeo" label="Target Geography" placeholder="United States" />
            <Field k="targetRoles" label="Target Roles" placeholder="CTO, VP Engineering" />
          </div>

          {/* Size + Industry */}
          <div className="grid grid-cols-2 gap-space-sm">
            <Field k="companySize" label="Company Size" placeholder="50–500 employees" />
            <Field k="industry" label="Industry" placeholder="SaaS / Software" />
          </div>

          {/* Agent 0 Autonomous Prospect Discovery */}
          <div className="rounded-2xl border border-primary/20 bg-primary-fixed/10 p-space-md flex flex-col gap-space-sm">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-primary-container flex items-center justify-center flex-shrink-0">
                  <span className="material-symbols-outlined text-[18px] text-on-primary-container">travel_explore</span>
                </div>
                <div>
                  <h4 className="font-label-md text-label-md text-on-surface font-semibold flex items-center gap-1.5">
                    Agent 0: Autonomous Prospect Discovery
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-primary text-on-primary">Active</span>
                  </h4>
                  <p className="font-body-sm text-body-sm text-outline">Directly search and enroll qualified prospects matching this campaign</p>
                </div>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoStartAgent0}
                  onChange={(e) => setAutoStartAgent0(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-surface-container-high peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-outline-variant/30 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
              </label>
            </div>

            {autoStartAgent0 && (
              <div className="pt-space-xs border-t border-primary/10 flex items-center justify-between gap-space-md mt-1">
                <div className="flex-1">
                  <label className="font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider">
                    Number of Prospects to Find
                  </label>
                  <p className="font-body-sm text-body-sm text-outline">How many leads Agent 0 will search, qualify, and enroll upon creation</p>
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    min={1}
                    max={50}
                    value={targetProspectCount}
                    onChange={(e) => setTargetProspectCount(Math.max(1, Math.min(50, parseInt(e.target.value) || 1)))}
                    className="w-20 text-center font-label-md text-label-md font-semibold bg-surface-container-lowest rounded-xl px-3 py-1.5 border border-primary/30 text-on-surface focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                  <span className="font-label-sm text-label-sm text-outline">leads</span>
                </div>
              </div>
            )}
          </div>

          {/* Knowledge Base */}
          <div>
            <p className="font-label-sm text-label-sm uppercase tracking-wider text-outline mb-space-sm">Knowledge Base</p>
            <div className="grid grid-cols-3 gap-space-sm">
              {['Product Information', 'Case Studies', 'Sales Playbook', 'ICP Definition', 'Objection Handling', 'Example Messages'].map((item) => (
                <div key={item} className="flex items-center gap-1.5 px-3 py-2 rounded-xl border border-dashed border-outline-variant/40 hover:border-primary-container hover:bg-primary-fixed/10 cursor-pointer transition-colors font-body-sm text-body-sm text-outline hover:text-on-surface">
                  <span className="material-symbols-outlined text-[15px]">add</span>
                  {item}
                </div>
              ))}
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
                <><span className="material-symbols-outlined text-[16px] animate-spin">refresh</span>Creating…</>
              ) : (
                <><span className="material-symbols-outlined text-[16px]">add_circle</span>Create Campaign</>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
