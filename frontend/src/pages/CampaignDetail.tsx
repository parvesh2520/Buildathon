import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Play, Pause, ChevronRight, CheckCircle2, Clock, Copy, ShieldAlert, Radio } from 'lucide-react';
import { Campaign, Prospect } from '@/types';
import { getCampaign, updateCampaignStatus, duplicateCampaign } from '@/api/campaigns';
import { getProspects } from '@/api/prospects';
import { runSDR } from '@/api/sdr';
import { getOperationalControls, toggleChannelPause } from '@/api/system';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { StatCard } from '@/components/shared/StatCard';
import { ProspectTable } from '@/components/prospect/ProspectTable';
import { ProspectDrawer } from '@/components/prospect/ProspectDrawer';
import { AgentPipeline } from '@/components/agent/AgentPipeline';
import { PromptHarnessTab } from '@/components/campaign/PromptHarnessTab';
import { RepAssignmentTab } from '@/components/campaign/RepAssignmentTab';
import { ConflictScannerModal } from '@/components/campaign/ConflictScannerModal';
import { demoActivity } from '@/data/demo/activity';
import toast from 'react-hot-toast';
import { cn } from '@/lib/utils';

type Tab = 'overview' | 'prospects' | 'prompts' | 'reps' | 'activity' | 'outreach' | 'analytics';

const funnelStages = [
  { label: 'Prospects', value: 842, pct: 100 },
  { label: 'ICP Qualified', value: 614, pct: 72.9 },
  { label: 'Outreach Generated', value: 614, pct: 100 },
  { label: 'Messages Sent', value: 590, pct: 96.1 },
  { label: 'Replies', value: 73, pct: 12.4 },
  { label: 'Meetings', value: 18, pct: 24.7 },
];

const agentSteps = [
  { label: 'Lead Research', done: true },
  { label: 'ICP Fitment', done: true },
  { label: 'Outreach Strategy', done: true },
  { label: 'Personalisation', done: true },
  { label: 'Conversation', done: false, waiting: true },
  { label: 'Follow-up', done: false, waiting: true },
  { label: 'Voice SDR', done: false, ready: true },
];

const sampleOutreach = {
  prospect: 'James Carter',
  channel: 'EMAIL' as const,
  subject: 'Re: Developer productivity at CloudPeak',
  body: `Hi James,

I noticed CloudPeak's engineering team has grown significantly over the past 6 months — congrats on the growth! 

At companies at your stage, developer velocity often becomes the silent bottleneck. We help engineering teams like yours ship 40% faster without adding headcount, by automating the repetitive parts of the SDLC.

Happy to share a 10-minute walkthrough that's specific to SaaS teams at your scale. Would Thursday at 2pm PT work?

Best,
The Autonomous SDR`,
  generatedBy: 'Personalisation Agent',
  timestamp: '12:42 today',
  requiresApproval: false,
};

export function CampaignDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [prospects, setProspects] = useState<Prospect[]>([]);
  const [selectedProspect, setSelectedProspect] = useState<Prospect | null>(null);
  const [tab, setTab] = useState<Tab>('overview');
  const [statusLoading, setStatusLoading] = useState(false);
  const [sdrState, setSdrState] = useState<'idle' | 'queued' | 'done'>('idle');
  const [loading, setLoading] = useState(true);

  // Operational Controls & Problem Statement additions
  const [duplicating, setDuplicating] = useState(false);
  const [showConflictRadar, setShowConflictRadar] = useState(false);
  const [pausedChannels, setPausedChannels] = useState<string[]>([]);

  useEffect(() => {
    if (!id) return;
    Promise.all([getCampaign(id), getProspects(), getOperationalControls()]).then(([c, all, ctrl]) => {
      setCampaign(c);
      setProspects(all.filter((p) => p.campaignId === id));
      if (ctrl?.paused_channels) setPausedChannels(ctrl.paused_channels);
    }).catch(() => toast.error('Campaign not found')).finally(() => setLoading(false));
  }, [id]);

  const handleDuplicate = async () => {
    if (!campaign) return;
    setDuplicating(true);
    try {
      const cloned = await duplicateCampaign(campaign.id);
      toast.success(`Duplicated variant created: ${cloned.name}`);
      navigate(`/campaigns/${cloned.id}`);
    } catch {
      toast.error('Failed to duplicate campaign');
    } finally {
      setDuplicating(false);
    }
  };

  const handleToggleChannel = async (channel: string) => {
    const isPaused = pausedChannels.includes(channel);
    try {
      const updated = await toggleChannelPause(channel, !isPaused);
      setPausedChannels(updated.paused_channels);
      toast.success(`${channel} ${isPaused ? 'resumed' : 'paused'} platform-wide`);
    } catch {
      toast.error(`Failed to update ${channel} status`);
    }
  };

  const toggleStatus = async () => {
    if (!campaign) return;
    setStatusLoading(true);
    try {
      const newStatus = campaign.status === 'LIVE' ? 'PAUSED' : 'LIVE';
      const updated = await updateCampaignStatus(campaign.id, newStatus);
      setCampaign(updated);
      toast.success(`Campaign ${newStatus === 'LIVE' ? 'activated' : 'paused'}`);
    } catch {
      toast.error('Failed to update status');
    } finally {
      setStatusLoading(false);
    }
  };

  const handleRunSDR = async () => {
    if (!campaign || prospects.length === 0) { toast.error('No prospects to run SDR on'); return; }
    setSdrState('queued');
    const targetProspect = prospects[0];
    try {
      const res = await runSDR({ campaign_id: campaign.id, prospect_id: targetProspect.id });
      setSdrState('done');
      if (res.status === 'FAILED' || res.status === 'BLOCKED') {
        toast.error(`SDR Execution ${res.status}: ${res.error || 'Execution encountered an issue'}`);
      } else {
        const ch = res.actual_channel || res.recommended_channel || (res as any).channel_result?.channel || targetProspect.channel || 'Outreach';
        toast.success(`Autonomous SDR Complete: ${ch} (${res.status})`);
        setProspects((prev) =>
          prev.map((p) =>
            p.id === targetProspect.id
              ? {
                  ...p,
                  status: (res.status === 'NO_FIT' ? 'NO_FIT' : 'CONTACTED') as any,
                  channel: (res.actual_channel || res.recommended_channel || (res as any).channel_result?.channel || p.channel || 'EMAIL') as any,
                  icpScore: (res as any).icp_result?.score ?? p.icpScore,
                }
              : p
          )
        );
      }
    } catch (err) {
      setSdrState('idle');
      toast.error(err instanceof Error ? err.message : 'SDR run failed');
    }
  };

  const tabs: { id: Tab; label: string }[] = [
    { id: 'overview', label: 'Overview' },
    { id: 'prospects', label: `Prospects (${prospects.length})` },
    { id: 'prompts', label: 'Prompts & AI Harness' },
    { id: 'reps', label: 'Reps & Quotas' },
    { id: 'activity', label: 'Agent Activity' },
    { id: 'outreach', label: 'Outreach' },
    { id: 'analytics', label: 'Analytics' },
  ];

  if (loading) return (
    <div className="p-6 flex items-center justify-center text-slate-400 text-sm">Loading campaign...</div>
  );

  if (!campaign) return (
    <div className="p-6 text-center text-slate-500 text-sm">Campaign not found.</div>
  );

  return (
    <div className="p-6 max-w-[1200px] mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3 mb-1">
        <button onClick={() => navigate('/campaigns')} className="text-slate-400 hover:text-slate-600 p-1 rounded hover:bg-surface-secondary">
          <ArrowLeft size={16} />
        </button>
        <span className="text-xs text-slate-400">Campaigns</span>
        <ChevronRight size={12} className="text-slate-300" />
        <span className="text-xs text-slate-600">{campaign.name}</span>
      </div>

      <div className="flex items-center justify-between mb-6 mt-3">
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-bold text-slate-900">{campaign.name}</h1>
          <StatusBadge status={campaign.status} />
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowConflictRadar(true)}
            className="btn-secondary text-xs flex items-center gap-1.5"
            title="Scan for cross-campaign prospect collisions"
          >
            <ShieldAlert size={13} className="text-amber-600" />
            Conflict Radar
          </button>
          <button
            onClick={handleDuplicate}
            disabled={duplicating}
            className="btn-secondary text-xs flex items-center gap-1.5"
            title="Duplicate as Variant B for A/B Testing"
          >
            <Copy size={13} />
            {duplicating ? 'Duplicating...' : 'Duplicate as Variant'}
          </button>
          <button
            onClick={handleRunSDR}
            disabled={sdrState !== 'idle'}
            className="btn-secondary text-xs"
          >
            {sdrState === 'idle' ? '▶ Run SDR' : sdrState === 'queued' ? '⏳ Queued...' : '✓ Queued'}
          </button>
          <button
            onClick={toggleStatus}
            disabled={statusLoading || campaign.status === 'COMPLETED'}
            className={cn('btn-primary', campaign.status === 'LIVE' ? 'bg-amber-500 hover:bg-amber-600' : '')}
          >
            {campaign.status === 'LIVE' ? <><Pause size={13} /> Pause</> : <><Play size={13} /> Activate</>}
          </button>
        </div>
      </div>

      {/* Channel Operational Controls (Section 3 - Channel Pause) */}
      <div className="card p-3.5 mb-6 bg-slate-50/70 border border-border flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Radio size={14} className="text-brand" />
          <span className="text-xs font-bold text-slate-700">Channel Operational Controls:</span>
          <span className="text-2xs text-slate-400">Pause/Resume individual outreach channels</span>
        </div>
        <div className="flex items-center gap-2">
          {['EMAIL', 'LINKEDIN', 'SMS', 'PHONE'].map((ch) => {
            const isPaused = pausedChannels.includes(ch);
            return (
              <button
                key={ch}
                onClick={() => handleToggleChannel(ch)}
                className={cn(
                  'px-2.5 py-1 rounded-md text-2xs font-semibold border transition-all cursor-pointer flex items-center gap-1',
                  isPaused
                    ? 'bg-rose-50 text-rose-700 border-rose-200 hover:bg-rose-100'
                    : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
                )}
              >
                <span className={cn('w-1.5 h-1.5 rounded-full', isPaused ? 'bg-rose-500' : 'bg-emerald-500')} />
                <span>{ch}</span>
                <span className="text-3xs text-slate-400 font-normal">({isPaused ? 'Paused' : 'Active'})</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Campaign info */}
      <div className="grid grid-cols-3 gap-4 mb-6 text-sm">
        <div className="card p-4">
          <p className="text-xs text-slate-400 mb-1">ICP</p>
          <p className="text-slate-700">{campaign.icp}</p>
        </div>
        <div className="card p-4">
          <p className="text-xs text-slate-400 mb-1">Target Geography</p>
          <p className="text-slate-700">{campaign.targetGeo ?? '—'}</p>
        </div>
        <div className="card p-4">
          <p className="text-xs text-slate-400 mb-1">Campaign Goal</p>
          <p className="text-slate-700 text-xs leading-relaxed">{campaign.goal ?? '—'}</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-6 gap-3 mb-6">
        <StatCard label="Total Prospects" value={(campaign.prospects ?? 0).toLocaleString()} />
        <StatCard label="Qualified" value={Math.round((campaign.prospects ?? 0) * 0.73).toLocaleString()} />
        <StatCard label="Outreach Sent" value={(campaign.messages ?? 0).toLocaleString()} />
        <StatCard label="Replies" value={campaign.replies ?? 0} />
        <StatCard label="Meetings" value={campaign.meetings ?? 0} />
        <StatCard label="Conv. Rate" value={`${((campaign.meetings ?? 0) / Math.max(campaign.prospects ?? 1, 1) * 100).toFixed(1)}%`} />
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-0 border-b border-border mb-6">
        {tabs.map((t) => (
          <button
            key={t.id}
            className={cn(
              'px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors',
              tab === t.id ? 'border-brand text-brand' : 'border-transparent text-slate-500 hover:text-slate-700'
            )}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {tab === 'overview' && (
        <div className="grid grid-cols-[1fr_220px] gap-6">
          {/* Funnel */}
          <div className="card p-5">
            <h3 className="text-sm font-semibold text-slate-700 mb-5">Conversion Funnel</h3>
            <div className="space-y-3">
              {funnelStages.map((stage, i) => (
                <div key={stage.label}>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs text-slate-600">{stage.label}</span>
                    <span className="text-xs font-semibold tabular-nums text-slate-800">{stage.value.toLocaleString()}</span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-2">
                    <div className="bg-brand h-2 rounded-full transition-all" style={{ width: `${stage.pct}%` }} />
                  </div>
                  {i < funnelStages.length - 1 && (
                    <p className="text-2xs text-slate-400 mt-1">↓ {funnelStages[i + 1].pct}% conversion</p>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Agent Pipeline */}
          <div className="card p-5">
            <h3 className="text-sm font-semibold text-slate-700 mb-4">Agent Pipeline</h3>
            <div className="space-y-2">
              {agentSteps.map((step, i) => (
                <div key={i} className="flex items-center gap-2.5">
                  {step.done ? (
                    <CheckCircle2 size={13} className="text-emerald-500 flex-shrink-0" />
                  ) : step.waiting ? (
                    <Clock size={13} className="text-slate-300 flex-shrink-0" />
                  ) : (
                    <div className="w-3 h-3 rounded-full border-2 border-violet-300 bg-violet-50 flex-shrink-0" />
                  )}
                  <span className={cn('text-xs', step.done ? 'text-slate-700' : step.ready ? 'text-violet-600 font-medium' : 'text-slate-400')}>
                    {step.label}
                    {step.done && <span className="text-emerald-500 ml-1 text-2xs">✓ Completed</span>}
                    {step.waiting && <span className="text-slate-300 ml-1 text-2xs">Waiting</span>}
                    {step.ready && <span className="text-violet-400 ml-1 text-2xs">Ready</span>}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {tab === 'prospects' && (
        <ProspectTable prospects={prospects} onSelectProspect={setSelectedProspect} />
      )}

      {tab === 'prompts' && (
        <PromptHarnessTab campaignId={campaign.id} />
      )}

      {tab === 'reps' && (
        <RepAssignmentTab campaignId={campaign.id} />
      )}

      {tab === 'activity' && (
        <div className="card divide-y divide-border-light">
          {demoActivity.filter((a) => a.campaign === campaign.name || !a.campaign).slice(0, 10).map((event) => (
            <div key={event.id} className="px-5 py-3.5">
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-xs font-semibold text-slate-700">{event.agentName}</span>
                  <p className="text-xs text-slate-500 mt-0.5">{event.action}</p>
                  {event.prospect && <p className="text-xs text-brand mt-0.5">{event.prospect}</p>}
                </div>
                <div className="flex items-center gap-2 text-right">
                  <span className="text-2xs text-slate-400">{event.timestamp}</span>
                  <StatusBadge status={event.status} />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === 'outreach' && (
        <div className="space-y-4">
          <div className="card p-5">
            <div className="flex items-start justify-between mb-3">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-semibold text-slate-800">{sampleOutreach.prospect}</span>
                  <StatusBadge status={sampleOutreach.channel} />
                </div>
                <p className="text-xs text-slate-500">Generated by {sampleOutreach.generatedBy} · {sampleOutreach.timestamp}</p>
              </div>
              <StatusBadge status="PENDING" />
            </div>
            <div className="bg-surface-secondary rounded-lg p-4 text-sm space-y-3">
              <p className="text-xs font-medium text-slate-500">Subject: <span className="text-slate-700">{sampleOutreach.subject}</span></p>
              <pre className="text-xs text-slate-600 whitespace-pre-wrap font-sans leading-relaxed">{sampleOutreach.body}</pre>
            </div>
            <div className="flex items-center gap-2 mt-4">
              <button className="btn-primary" onClick={() => toast.success('Message approved')}>Approve</button>
              <button className="btn-secondary" onClick={() => toast.success('Opened editor')}>Edit</button>
              <button className="btn-ghost text-red-500 hover:bg-red-50" onClick={() => toast.success('Message rejected')}>Reject</button>
            </div>
          </div>
        </div>
      )}

      {tab === 'analytics' && (
        <div className="card p-6 flex items-center justify-center text-slate-400 text-sm min-h-[200px]">
          <div className="text-center">
            <p className="font-medium text-slate-600">Campaign Analytics</p>
            <p className="text-xs mt-1">Full analytics available on the Analytics page.</p>
          </div>
        </div>
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

      {showConflictRadar && (
        <ConflictScannerModal onClose={() => setShowConflictRadar(false)} />
      )}
    </div>
  );
}
