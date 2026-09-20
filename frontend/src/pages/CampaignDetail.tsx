import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ActivityEvent, Campaign, OutreachMessage, Prospect } from '@/types';
import { getCampaign, updateCampaignStatus, duplicateCampaign, enrollLeadsInCampaign } from '@/api/campaigns';
import { getProspects } from '@/api/prospects';
import { getActivityEvents, getCampaignOutreach } from '@/api/sdr';
import { startSdrPipeline, runDiscoveryAgent, isCampaignDiscovering, setCampaignDiscovering } from '@/api/discovery';
import { getOperationalControls, toggleChannelPause } from '@/api/system';
import { ProspectTable } from '@/components/prospect/ProspectTable';
import { ProspectDrawer } from '@/components/prospect/ProspectDrawer';
import { AddProspectModal } from '@/components/prospect/AddProspectModal';
import { ProspectDiscoveryLoadingCard, ProspectDiscoveryLoadingBanner } from '@/components/prospect/ProspectDiscoveryLoading';
import { PromptHarnessTab } from '@/components/campaign/PromptHarnessTab';
import { RepAssignmentTab } from '@/components/campaign/RepAssignmentTab';
import { ConflictScannerModal } from '@/components/campaign/ConflictScannerModal';
import toast from 'react-hot-toast';
import { cn } from '@/lib/utils';

type Tab = 'overview' | 'prospects' | 'prompts' | 'reps' | 'activity' | 'outreach' | 'analytics';

const agentSteps = [
  { label: 'Lead Research', done: true },
  { label: 'ICP Fitment', done: true },
  { label: 'Outreach Strategy', done: true },
  { label: 'Personalisation', done: true },
  { label: 'Conversation', done: false, waiting: true },
  { label: 'Follow-up', done: false, waiting: true },
  { label: 'Voice SDR', done: false, ready: true },
];

export function CampaignDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [prospects, setProspects] = useState<Prospect[]>([]);
  const [selectedProspect, setSelectedProspect] = useState<Prospect | null>(null);
  const [tab, setTab] = useState<Tab>('overview');
  const [statusLoading, setStatusLoading] = useState(false);
  const [sdrState, setSdrState] = useState<'idle' | 'queued' | 'done'>('idle');
  const [sdrProgress, setSdrProgress] = useState('');
  const [loading, setLoading] = useState(true);
  const [activity, setActivity] = useState<ActivityEvent[]>([]);
  const [outreach, setOutreach] = useState<OutreachMessage[]>([]);
  const [duplicating, setDuplicating] = useState(false);
  const [showConflictRadar, setShowConflictRadar] = useState(false);
  const [pausedChannels, setPausedChannels] = useState<string[]>([]);
  const [showAddProspectModal, setShowAddProspectModal] = useState(false);
  const [enrolling, setEnrolling] = useState(false);
  const [isDiscovering, setIsDiscovering] = useState<boolean>(() => {
    return id ? isCampaignDiscovering(id).discovering : false;
  });
  const [discoveryCount, setDiscoveryCount] = useState<number>(() => {
    return id ? (isCampaignDiscovering(id).count || 5) : 5;
  });

  const fetchCampaignData = useCallback(() => {
    if (!id) return;
    Promise.all([
      getCampaign(id),
      getProspects(),
      getOperationalControls(),
      getActivityEvents(id),
      getCampaignOutreach(id),
    ]).then(([c, all, ctrl, events, messages]) => {
      setCampaign(c);
      setProspects(all.filter((p) => p.campaignId === id || p.campaign_id === id));
      if (ctrl?.paused_channels) setPausedChannels(ctrl.paused_channels);
      setActivity(events);
      setOutreach(messages);
    }).catch(() => toast.error('Campaign not found')).finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    fetchCampaignData();
  }, [fetchCampaignData]);

  useEffect(() => {
    const handleUpdate = (e: Event) => {
      const customEvent = e as CustomEvent;
      if (!customEvent.detail?.campaignId || customEvent.detail?.campaignId === id) {
        fetchCampaignData();
      }
    };
    window.addEventListener('prospects-updated', handleUpdate);
    return () => window.removeEventListener('prospects-updated', handleUpdate);
  }, [id, fetchCampaignData]);

  useEffect(() => {
    if (!id) return;
    const handleStart = (e: Event) => {
      const customEvent = e as CustomEvent;
      if (!customEvent.detail?.campaignId || customEvent.detail?.campaignId === id) {
        setIsDiscovering(true);
        if (customEvent.detail?.count) setDiscoveryCount(customEvent.detail.count);
      }
    };
    const handleEnd = (e: Event) => {
      const customEvent = e as CustomEvent;
      if (!customEvent.detail?.campaignId || customEvent.detail?.campaignId === id) {
        setIsDiscovering(false);
      }
    };
    window.addEventListener('agent0-discovery-start', handleStart);
    window.addEventListener('agent0-discovery-end', handleEnd);
    return () => {
      window.removeEventListener('agent0-discovery-start', handleStart);
      window.removeEventListener('agent0-discovery-end', handleEnd);
    };
  }, [id]);

  const handleRunAgent0 = async () => {
    if (!campaign) return;
    setIsDiscovering(true);
    setCampaignDiscovering(campaign.id, true, 5);
    window.dispatchEvent(new CustomEvent('agent0-discovery-start', { detail: { campaignId: campaign.id, count: 5 } }));
    toast.loading(`Agent 0 running: discovering 5 prospects for "${campaign.name}"…`, {
      id: `agent-0-${campaign.id}`,
      duration: 4000,
    });
    try {
      const res = await runDiscoveryAgent(campaign.id, 5, campaign.icp);
      const countFound = res.stored_count || res.prospects?.length || 5;
      toast.success(`Agent 0 completed: ${countFound} prospects discovered & enrolled!`, {
        id: `agent-0-${campaign.id}`,
        duration: 5000,
      });
      fetchCampaignData();
      window.dispatchEvent(new CustomEvent('prospects-updated', { detail: { campaignId: campaign.id } }));
    } catch (err) {
      console.error('Agent 0 discovery notice:', err);
      toast.error('Agent 0 discovery notice: check campaign prospects', {
        id: `agent-0-${campaign.id}`,
      });
    } finally {
      setIsDiscovering(false);
      setCampaignDiscovering(campaign.id, false);
      window.dispatchEvent(new CustomEvent('agent0-discovery-end', { detail: { campaignId: campaign.id } }));
    }
  };

  const handleEnrollLeads = async () => {
    if (!campaign) return;
    setEnrolling(true);
    try {
      const res = await enrollLeadsInCampaign(campaign.id);
      toast.success(`Enrolled ${res.enrolled_count} leads into ${campaign.name}`);
      const allUpdated = await getProspects();
      setProspects(allUpdated.filter((p) => p.campaignId === campaign.id || p.campaign_id === campaign.id));
    } catch {
      toast.error('Failed to enroll leads');
    } finally {
      setEnrolling(false);
    }
  };

  const handleDuplicate = async () => {
    if (!campaign) return;
    setDuplicating(true);
    try {
      const cloned = await duplicateCampaign(campaign.id);
      toast.success(`Duplicated: ${cloned.name}`);
      navigate(`/campaigns/${cloned.id}`);
    } catch { toast.error('Failed to duplicate campaign'); }
    finally { setDuplicating(false); }
  };

  const handleToggleChannel = async (channel: string) => {
    const isPaused = pausedChannels.includes(channel);
    try {
      const updated = await toggleChannelPause(channel, !isPaused);
      setPausedChannels(updated.paused_channels);
      toast.success(`${channel} ${isPaused ? 'resumed' : 'paused'} platform-wide`);
    } catch { toast.error(`Failed to update ${channel} status`); }
  };

  const toggleStatus = async () => {
    if (!campaign) return;
    setStatusLoading(true);
    try {
      const newStatus = campaign.status === 'LIVE' ? 'PAUSED' : 'LIVE';
      const updated = await updateCampaignStatus(campaign.id, newStatus);
      setCampaign(updated);
      toast.success(`Campaign ${newStatus === 'LIVE' ? 'activated' : 'paused'}`);
    } catch { toast.error('Failed to update status'); }
    finally { setStatusLoading(false); }
  };

  const handleRunSDR = async () => {
    if (!campaign || prospects.length === 0) { toast.error('No prospects to run SDR on'); return; }
    setSdrState('queued');
    try {
      // Prioritize pending/uncontacted prospects, or up to 5 at a time for fast feedback
      const pending = prospects.filter((p) => p.status && !['CONTACTED', 'SENT', 'COMPLETED', 'NO_FIT'].includes(p.status));
      const prospectsToRun = pending.length > 0 ? pending.slice(0, 5) : prospects.slice(0, 5);
      const pIds = prospectsToRun.map((p) => p.id);

      setSdrProgress(`(${pIds.length} leads queued)`);
      setProspects((prev) => prev.map((p) => pIds.includes(p.id) ? { ...p, status: 'PROCESSING' as any } : p));

      const res = await startSdrPipeline(campaign.id, pIds);
      const results = res.results || [];

      setSdrState('done');
      const allUpdated = await getProspects();
      setProspects(allUpdated.filter((p) => p.campaignId === campaign.id || p.campaign_id === campaign.id));
      setActivity(await getActivityEvents(campaign.id));
      setOutreach(await getCampaignOutreach(campaign.id));

      const sentCount = results.filter((r) => r.execution_status === 'SENT' || r.status === 'COMPLETED').length;
      const noFitCount = results.filter((r) => r.status === 'NO_FIT' || r.execution_status === 'NO_FIT').length;
      toast.success(`SDR Complete: ${sentCount} sent, ${noFitCount} disqualified.`);
      setTimeout(() => { setSdrState('idle'); setSdrProgress(''); }, 4000);
    } catch (err) {
      setSdrState('idle'); setSdrProgress('');
      toast.error(err instanceof Error ? err.message : 'SDR run failed');
    }
  };

  const tabs: { id: Tab; label: string }[] = [
    { id: 'overview', label: 'Overview' },
    { id: 'prospects', label: `Prospects (${prospects.length})` },
    { id: 'prompts', label: 'Prompts & AI' },
    { id: 'reps', label: 'Reps & Quotas' },
    { id: 'activity', label: 'Agent Activity' },
    { id: 'outreach', label: 'Outreach' },
    { id: 'analytics', label: 'Analytics' },
  ];

  if (loading) return (
    <div className="w-full bg-surface min-h-screen px-space-lg py-space-lg flex items-center justify-center">
      <div className="flex flex-col items-center gap-space-sm">
        <div className="w-8 h-8 rounded-full border-2 border-primary-container border-t-transparent animate-spin" />
        <span className="font-body-sm text-body-sm text-on-surface-variant">Loading campaign…</span>
      </div>
    </div>
  );

  if (!campaign) return (
    <div className="w-full bg-surface min-h-screen px-space-lg py-space-lg flex items-center justify-center">
      <span className="font-body-md text-body-md text-on-surface-variant">Campaign not found.</span>
    </div>
  );

  const qualified = prospects.filter((p) => ['FIT', 'CONTACTED', 'SENT', 'COMPLETED', 'REPLIED', 'MEETING'].includes(p.status || '')).length;
  const sent = prospects.filter((p) => ['CONTACTED', 'SENT', 'COMPLETED', 'REPLIED', 'MEETING'].includes(p.status || '')).length;
  const replies = prospects.filter((p) => ['REPLIED', 'MEETING'].includes(p.status || '')).length;
  const meetings = prospects.filter((p) => p.status === 'MEETING').length;

  const funnelStages = [
    { label: 'Prospects', value: prospects.length, pct: 100 },
    { label: 'ICP Qualified', value: qualified, pct: prospects.length ? (qualified / prospects.length) * 100 : 0 },
    { label: 'Outreach Generated', value: outreach.length, pct: prospects.length ? (outreach.length / prospects.length) * 100 : 0 },
    { label: 'Messages Sent', value: sent, pct: prospects.length ? (sent / prospects.length) * 100 : 0 },
    { label: 'Replies', value: replies, pct: sent ? (replies / sent) * 100 : 0 },
    { label: 'Meetings', value: meetings, pct: replies ? (meetings / replies) * 100 : 0 },
  ];

  return (
    <div className="w-full bg-surface min-h-screen px-space-lg py-space-lg">

      {/* Breadcrumb */}
      <div className="flex items-center gap-space-xs font-body-sm text-body-sm text-on-surface-variant mb-space-md">
        <button onClick={() => navigate('/campaigns')} className="hover:text-on-surface transition-colors">Campaigns</button>
        <span className="material-symbols-outlined text-[15px] text-outline">chevron_right</span>
        <span className="font-label-md text-label-md text-on-surface font-medium">{campaign.name}</span>
        <span className={cn(
          'ml-space-xs px-2 py-0.5 rounded-full font-label-sm text-label-sm font-semibold',
          campaign.status === 'LIVE' ? 'bg-tertiary/10 text-tertiary' : 'bg-surface-container text-outline'
        )}>
          {campaign.status === 'LIVE' && <span className="inline-block w-1.5 h-1.5 rounded-full bg-tertiary animate-pulse mr-1 align-middle" />}
          {campaign.status}
        </span>
      </div>

      {/* Title row */}
      <div className="flex flex-wrap items-start justify-between gap-space-md mb-space-lg">
        <div>
          <h1 className="font-headline-lg text-headline-lg text-on-surface tracking-tight">{campaign.name}</h1>
          {campaign.description && (
            <p className="font-body-md text-body-md text-on-surface-variant mt-1 max-w-2xl">{campaign.description}</p>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-space-sm">
          <button
            onClick={handleRunAgent0}
            disabled={isDiscovering}
            className={cn(
              "flex items-center gap-1.5 px-3.5 py-1.5 rounded-full font-label-md text-label-md shadow-sm transition-all border disabled:opacity-60",
              isDiscovering
                ? "bg-primary/10 text-primary border-primary/30"
                : "bg-surface-container-lowest hover:bg-surface-container text-on-surface border-outline-variant/20"
            )}
            title="Run Agent 0 to automatically discover matching prospects"
          >
            <span className={cn("material-symbols-outlined text-[16px] text-primary", isDiscovering && "animate-spin")}>
              {isDiscovering ? 'radar' : 'travel_explore'}
            </span>
            {isDiscovering ? 'Agent 0 Sourcing…' : 'Agent 0 Sourcing'}
          </button>
          <button
            onClick={() => setShowAddProspectModal(true)}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-primary-container text-on-primary-container hover:bg-inverse-primary font-label-md text-label-md shadow-sm transition-all active:scale-95"
          >
            <span className="material-symbols-outlined text-[16px]">person_add</span>
            Add Prospect
          </button>
          <button
            onClick={handleEnrollLeads}
            disabled={enrolling}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-surface-container-lowest hover:bg-surface-container text-on-surface font-label-md text-label-md shadow-sm transition-colors border border-outline-variant/20 disabled:opacity-60"
            title="Enroll unassigned leads into this campaign"
          >
            <span className="material-symbols-outlined text-[16px] text-primary">bolt</span>
            {enrolling ? 'Enrolling…' : 'Enroll Leads'}
          </button>
          <button onClick={() => navigate('/discovery')} className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-surface-container-lowest hover:bg-surface-container text-on-surface font-label-md text-label-md shadow-sm transition-colors border border-outline-variant/20">
            <span className="material-symbols-outlined text-[16px] text-primary">travel_explore</span>
            Discover Prospects
          </button>
          <button onClick={() => setShowConflictRadar(true)} className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-surface-container-lowest hover:bg-surface-container text-on-surface font-label-md text-label-md shadow-sm transition-colors border border-outline-variant/20">
            <span className="material-symbols-outlined text-[16px] text-primary-container" style={{color:'#b45309'}}>radar</span>
            Conflict Radar
          </button>
          <button onClick={handleDuplicate} disabled={duplicating} className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-surface-container-lowest hover:bg-surface-container text-on-surface font-label-md text-label-md shadow-sm transition-colors border border-outline-variant/20 disabled:opacity-60">
            <span className="material-symbols-outlined text-[16px] text-outline">content_copy</span>
            {duplicating ? 'Duplicating…' : 'Duplicate'}
          </button>
          <button
            onClick={handleRunSDR}
            disabled={sdrState !== 'idle'}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-surface-container-lowest hover:bg-surface-container text-on-surface font-label-md text-label-md shadow-sm transition-colors border border-outline-variant/20 disabled:opacity-60"
          >
            {sdrState === 'idle' && <><span className="material-symbols-outlined text-[16px] text-tertiary">play_arrow</span>Run SDR Pipeline</>}
            {sdrState === 'queued' && <><span className="material-symbols-outlined text-[16px] text-primary animate-spin">refresh</span>Running {sdrProgress}…</>}
            {sdrState === 'done' && <><span className="material-symbols-outlined text-[16px] text-tertiary">check_circle</span>Completed</>}
          </button>
          <button
            onClick={toggleStatus}
            disabled={statusLoading || campaign.status === 'COMPLETED'}
            className={cn(
              'flex items-center gap-1.5 px-4 py-1.5 rounded-full font-label-md text-label-md shadow-sm transition-all active:scale-95 disabled:opacity-60',
              campaign.status === 'LIVE'
                ? 'bg-surface-container text-on-surface hover:bg-surface-container-high border border-outline-variant/30'
                : 'bg-primary-container text-on-primary-container hover:bg-inverse-primary'
            )}
          >
            <span className="material-symbols-outlined text-[18px]">{campaign.status === 'LIVE' ? 'pause' : 'play_arrow'}</span>
            {campaign.status === 'LIVE' ? 'Pause' : 'Activate'}
          </button>
        </div>
      </div>

      {/* Channel Controls */}
      <div className="rounded-2xl bg-surface-container-lowest shadow-sm border border-outline-variant/10 px-space-lg py-space-md mb-space-lg flex flex-wrap items-center justify-between gap-space-sm">
        <div className="flex items-center gap-space-sm">
          <span className="material-symbols-outlined text-[18px] text-primary">radio</span>
          <span className="font-label-md text-label-md text-on-surface font-semibold">Channel Controls</span>
          <span className="font-body-sm text-body-sm text-outline">Pause individual outreach channels platform-wide</span>
        </div>
        <div className="flex items-center gap-space-sm">
          {['EMAIL', 'LINKEDIN', 'SMS', 'PHONE'].map((ch) => {
            const isPaused = pausedChannels.includes(ch);
            return (
              <button
                key={ch}
                onClick={() => handleToggleChannel(ch)}
                className={cn(
                  'flex items-center gap-1.5 px-3 py-1 rounded-full font-label-sm text-label-sm border transition-all',
                  isPaused
                    ? 'bg-secondary-container/30 text-on-secondary-container border-secondary-container/40 hover:bg-secondary-container/50'
                    : 'bg-tertiary/10 text-on-surface border-tertiary/20 hover:bg-tertiary/20'
                )}
              >
                <span className={cn('w-1.5 h-1.5 rounded-full', isPaused ? 'bg-secondary' : 'bg-tertiary')} />
                {ch}
                <span className="text-outline font-normal">· {isPaused ? 'Paused' : 'Active'}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Info cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-space-sm mb-space-lg">
        {[
          { label: 'ICP', value: campaign.icp || '—', icon: 'person_search' },
          { label: 'Target Geography', value: (campaign as any).targetGeo ?? '—', icon: 'public' },
          { label: 'Campaign Goal', value: (campaign as any).goal ?? '—', icon: 'flag' },
        ].map((info) => (
          <div key={info.label} className="rounded-2xl bg-surface-container-lowest shadow-sm p-space-md">
            <div className="flex items-center gap-1.5 mb-1">
              <span className="material-symbols-outlined text-[16px] text-outline">{info.icon}</span>
              <span className="font-label-sm text-label-sm uppercase tracking-wider text-outline">{info.label}</span>
            </div>
            <p className="font-body-md text-body-md text-on-surface leading-snug">{info.value}</p>
          </div>
        ))}
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 sm:grid-cols-6 gap-space-sm mb-space-lg">
        {[
          {
            label: 'Prospects',
            value: (
              <span className="flex items-center gap-1.5">
                {prospects.length}
                {isDiscovering && (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-primary/10 text-primary font-label-xs text-xs">
                    <span className="material-symbols-outlined text-[12px] animate-spin">radar</span>
                    Sourcing
                  </span>
                )}
              </span>
            ),
          },
          { label: 'Qualified', value: qualified },
          { label: 'Outreach Sent', value: sent },
          { label: 'Replies', value: replies },
          { label: 'Meetings', value: meetings },
          { label: 'Conv. Rate', value: `${(prospects.length > 0 ? (qualified / prospects.length) * 100 : 0).toFixed(1)}%` },
        ].map((s) => (
          <div key={s.label} className="rounded-2xl bg-surface-container-lowest shadow-sm p-space-md flex flex-col justify-between">
            <span className="font-label-sm text-label-sm uppercase tracking-wider text-outline">{s.label}</span>
            <span className="font-display-stat text-display-stat text-on-surface tracking-tight mt-2">{s.value}</span>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-0 border-b border-outline-variant/20 mb-space-lg overflow-x-auto">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={cn(
              'px-4 py-2.5 font-label-md text-label-md border-b-2 -mb-px transition-colors whitespace-nowrap',
              tab === t.id
                ? 'border-primary text-primary font-semibold'
                : 'border-transparent text-on-surface-variant hover:text-on-surface'
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab: Overview */}
      {tab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_240px] gap-space-lg">
          <div className="rounded-2xl bg-surface-container-lowest shadow-sm p-space-lg">
            <h3 className="font-headline-sm text-headline-sm text-on-surface mb-space-md">Conversion Funnel</h3>
            <div className="flex flex-col gap-space-md">
              {funnelStages.map((stage, i) => (
                <div key={stage.label}>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-body-sm text-body-sm text-on-surface-variant">{stage.label}</span>
                    <span className="font-label-md text-label-md text-on-surface font-semibold tabular-nums">{stage.value.toLocaleString()}</span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-surface-container overflow-hidden">
                    <div className="h-full rounded-full bg-primary-container transition-all" style={{ width: `${Math.min(stage.pct, 100)}%` }} />
                  </div>
                  {i < funnelStages.length - 1 && (
                    <p className="font-label-sm text-label-sm text-outline mt-1">{funnelStages[i + 1].pct.toFixed(1)}% conversion</p>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-2xl bg-surface-container-lowest shadow-sm p-space-lg">
            <h3 className="font-headline-sm text-headline-sm text-on-surface mb-space-md">Agent Pipeline</h3>
            <div className="flex flex-col gap-3">
              {agentSteps.map((step, i) => (
                <div key={i} className="flex items-center gap-space-sm">
                  {step.done ? (
                    <span className="material-symbols-outlined text-[18px] text-tertiary flex-shrink-0">check_circle</span>
                  ) : step.waiting ? (
                    <span className="material-symbols-outlined text-[18px] text-outline flex-shrink-0">schedule</span>
                  ) : (
                    <span className="material-symbols-outlined text-[18px] text-primary flex-shrink-0">radio_button_unchecked</span>
                  )}
                  <span className={cn(
                    'font-body-sm text-body-sm',
                    step.done ? 'text-on-surface' : step.ready ? 'text-primary font-medium' : 'text-outline'
                  )}>
                    {step.label}
                    {step.done && <span className="ml-1.5 text-tertiary font-label-sm text-label-sm">✓</span>}
                    {step.waiting && <span className="ml-1.5 text-outline font-label-sm text-label-sm">Waiting</span>}
                    {step.ready && <span className="ml-1.5 text-primary font-label-sm text-label-sm">Ready</span>}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tab: Prospects */}
      {tab === 'prospects' && (
        <div className="flex flex-col gap-space-md">
          {/* Active discovery banner if prospects exist while sourcing more */}
          {isDiscovering && prospects.length > 0 && (
            <ProspectDiscoveryLoadingBanner count={discoveryCount} />
          )}

          {/* Active discovery card if no prospects yet */}
          {isDiscovering && prospects.length === 0 ? (
            <ProspectDiscoveryLoadingCard campaignName={campaign.name} count={discoveryCount} />
          ) : prospects.length > 0 ? (
            <ProspectTable prospects={prospects} onSelectProspect={setSelectedProspect} />
          ) : (
            <div className="rounded-2xl bg-surface-container-lowest shadow-sm p-space-xl flex flex-col items-center gap-space-md text-center border border-outline-variant/10">
              <div className="w-12 h-12 rounded-2xl bg-primary-fixed/30 flex items-center justify-center">
                <span className="material-symbols-outlined text-[24px] text-on-primary-fixed-variant">person_search</span>
              </div>
              <div>
                <h3 className="font-headline-sm text-headline-sm text-on-surface">No prospects enrolled yet</h3>
                <p className="font-body-sm text-body-sm text-on-surface-variant mt-1 max-w-md">
                  Run Agent 0 to automatically discover matching leads, add a lead manually, or enroll existing contacts.
                </p>
              </div>
              <div className="flex flex-wrap items-center justify-center gap-space-sm mt-2">
                <button
                  onClick={handleRunAgent0}
                  disabled={isDiscovering}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-full bg-primary-container text-on-primary-container hover:bg-inverse-primary font-label-md text-label-md shadow-sm transition-all active:scale-95"
                >
                  <span className="material-symbols-outlined text-[18px]">travel_explore</span>
                  Find Prospects with Agent 0
                </button>
                <button
                  onClick={() => setShowAddProspectModal(true)}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-full bg-surface-container hover:bg-surface-container-high text-on-surface font-label-md text-label-md shadow-sm transition-all"
                >
                  <span className="material-symbols-outlined text-[18px]">person_add</span>
                  Add Prospect
                </button>
                <button
                  onClick={handleEnrollLeads}
                  disabled={enrolling}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-full bg-surface-container hover:bg-surface-container-high text-on-surface font-label-md text-label-md shadow-sm transition-all"
                >
                  <span className="material-symbols-outlined text-[18px] text-primary">bolt</span>
                  {enrolling ? 'Enrolling…' : 'Enroll Available Leads'}
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab: Prompts */}
      {tab === 'prompts' && <PromptHarnessTab campaignId={campaign.id} />}

      {/* Tab: Reps */}
      {tab === 'reps' && <RepAssignmentTab campaignId={campaign.id} />}

      {/* Tab: Activity */}
      {tab === 'activity' && (
        <div className="rounded-2xl bg-surface-container-lowest shadow-sm overflow-hidden divide-y divide-outline-variant/10">
          {activity.length === 0 && (
            <div className="px-space-lg py-space-lg font-body-sm text-body-sm text-on-surface-variant">
              No backend execution activity found for this campaign yet.
            </div>
          )}
          {activity.slice(0, 10).map((event) => (
            <div key={event.id} className="px-space-lg py-space-md hover:bg-surface-container/30 transition-colors">
              <div className="flex items-start justify-between">
                <div>
                  <span className="font-label-md text-label-md text-on-surface font-semibold">{event.agentName}</span>
                  <p className="font-body-sm text-body-sm text-on-surface-variant mt-0.5">{event.action}</p>
                  {event.prospect && <p className="font-label-sm text-label-sm text-primary mt-0.5">{event.prospect}</p>}
                </div>
                <div className="flex items-center gap-space-sm text-right flex-shrink-0">
                  <span className="font-label-sm text-label-sm text-outline">{event.timestamp}</span>
                  <span className="px-2 py-0.5 rounded-full bg-surface-container font-label-sm text-label-sm text-on-surface-variant">{event.status}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tab: Outreach */}
      {tab === 'outreach' && (
        <div className="flex flex-col gap-space-md">
          {outreach.length === 0 && (
            <div className="rounded-2xl bg-surface-container-lowest shadow-sm p-space-lg font-body-sm text-body-sm text-on-surface-variant">
              No outreach messages found for this campaign yet.
            </div>
          )}
          {outreach.map((message) => (
            <div key={message.id} className="rounded-2xl bg-surface-container-lowest shadow-sm p-space-lg">
              <div className="flex items-start justify-between mb-space-md">
                <div>
                  <div className="flex items-center gap-space-sm mb-1">
                    <span className="font-label-md text-label-md text-on-surface font-semibold">{message.prospectName}</span>
                    <span className="px-2 py-0.5 rounded-full bg-surface-container font-label-sm text-label-sm text-on-surface-variant">{message.channel}</span>
                  </div>
                  <p className="font-body-sm text-body-sm text-outline">Generated by {message.generatedBy} · {message.timestamp}</p>
                </div>
                <span className={cn(
                  'px-2.5 py-0.5 rounded-full font-label-sm text-label-sm font-semibold',
                  message.status === 'SENT' ? 'bg-tertiary/10 text-tertiary' : 'bg-primary-container/30 text-on-primary-container'
                )}>{message.status}</span>
              </div>
              <div className="rounded-xl bg-surface-container p-space-md">
                {message.subject && (
                  <p className="font-label-sm text-label-sm text-outline mb-2">Subject: <span className="text-on-surface font-medium">{message.subject}</span></p>
                )}
                <pre className="font-body-sm text-body-sm text-on-surface-variant whitespace-pre-wrap leading-relaxed">{message.body || 'No message body.'}</pre>
              </div>
              <div className="flex items-center gap-space-sm mt-space-md">
                <button disabled={message.status === 'SENT'} onClick={() => toast.success('Handled by backend review queues')} className="px-4 py-1.5 rounded-full bg-primary-container text-on-primary-container font-label-md text-label-md shadow-sm hover:bg-inverse-primary disabled:opacity-40 transition-all">Approve</button>
                <button onClick={() => toast.success('Edit via Inbox replies')} className="px-4 py-1.5 rounded-full bg-surface-container text-on-surface font-label-md text-label-md hover:bg-surface-container-high transition-all">Edit</button>
                <button disabled={message.status === 'SENT'} onClick={() => toast.success('Handled by backend review queues')} className="px-4 py-1.5 rounded-full bg-secondary-container/20 text-on-secondary-container font-label-md text-label-md hover:bg-secondary-container/40 disabled:opacity-40 transition-all">Reject</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tab: Analytics */}
      {tab === 'analytics' && (
        <div className="rounded-2xl bg-surface-container-lowest shadow-sm p-space-xl flex items-center justify-center min-h-[200px]">
          <div className="text-center">
            <span className="material-symbols-outlined text-[32px] text-outline mb-space-sm block">query_stats</span>
            <p className="font-headline-sm text-headline-sm text-on-surface">Campaign Analytics</p>
            <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">Full analytics available on the Analytics page.</p>
          </div>
        </div>
      )}

      {selectedProspect && (
        <ProspectDrawer
          prospect={selectedProspect}
          onClose={() => setSelectedProspect(null)}
          onDeleted={(id) => { setProspects((prev) => prev.filter((p) => p.id !== id)); setSelectedProspect(null); }}
          onUpdated={(updated) => setProspects((prev) => prev.map((p) => (p.id === updated.id ? updated : p)))}
        />
      )}

      {showConflictRadar && <ConflictScannerModal onClose={() => setShowConflictRadar(false)} />}

      {showAddProspectModal && (
        <AddProspectModal
          onClose={() => setShowAddProspectModal(false)}
          onCreated={(p) => {
            setProspects((prev) => [...prev, p]);
            setShowAddProspectModal(false);
          }}
        />
      )}
    </div>
  );
}
