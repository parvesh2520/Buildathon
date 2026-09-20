import { useEffect, useState, useRef } from 'react';
import {
  Search,
  Sparkles,
  Play,
  CheckSquare,
  Square,
  XCircle,
  Eye,
  ExternalLink,
  Phone,
  Mail,
  Filter,
  Users,
  Target,
  Clock,
  Layers,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Send,
  UserCheck,
  ShieldAlert,
  ArrowRight,
  Pause,
  Minimize2,
  Maximize2,
} from 'lucide-react';
import { Campaign, Prospect, StartPipelineResponse } from '@/types';
import { getCampaigns, updateCampaignStatus } from '@/api/campaigns';
import {
  getDiscoveredProspects,
  runDiscoveryAgent,
  updateDiscoveredProspect,
  startSdrPipeline,
} from '@/api/discovery';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { StatCard } from '@/components/shared/StatCard';
import { TableSkeleton } from '@/components/shared/LoadingSkeleton';
import { ProspectDrawer } from '@/components/prospect/ProspectDrawer';
import toast from 'react-hot-toast';
import { cn } from '@/lib/utils';

type FilterTab = 'ALL' | 'DISCOVERED' | 'SELECTED' | 'QUEUED' | 'PROCESSING' | 'COMPLETED' | 'NO_FIT' | 'REJECTED';

export function ProspectDiscovery() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [selectedCampaignId, setSelectedCampaignId] = useState<string>('');
  const [prospects, setProspects] = useState<Prospect[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [activeTab, setActiveTab] = useState<FilterTab>('ALL');
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  // Discovery Agent Modal state
  const [showDiscoveryModal, setShowDiscoveryModal] = useState(false);
  const [discoveryCount, setDiscoveryCount] = useState<number>(5);
  const [discoveryCriteria, setDiscoveryCriteria] = useState<string>('');
  const [isDiscovering, setIsDiscovering] = useState(false);

  // Pipeline Execution state
  const [isStartingPipeline, setIsStartingPipeline] = useState(false);
  const [isPipelineMinimized, setIsPipelineMinimized] = useState(false);
  const pipelineAbortedRef = useRef(false);
  const [pipelineCurrentIndex, setPipelineCurrentIndex] = useState(0);
  const [pipelineTotalCount, setPipelineTotalCount] = useState(0);
  const [pipelineCurrentProspectName, setPipelineCurrentProspectName] = useState('');
  const [pipelineRunResults, setPipelineRunResults] = useState<StartPipelineResponse['results'] | null>(null);

  // Prospect Drawer & Raw Inspector
  const [selectedProspectForDrawer, setSelectedProspectForDrawer] = useState<Prospect | null>(null);
  const [inspectedProspect, setInspectedProspect] = useState<Prospect | null>(null);

  // 1. Fetch campaigns on mount
  useEffect(() => {
    getCampaigns()
      .then((cList) => {
        setCampaigns(cList);
        if (cList.length > 0) {
          setSelectedCampaignId(cList[0].id);
        }
      })
      .catch(() => toast.error('Failed to load campaigns'))
      .finally(() => setLoading(false));
  }, []);

  // 2. Fetch discovered prospects whenever campaign changes
  const loadProspects = async (campaignId: string) => {
    if (!campaignId) return;
    setLoading(true);
    try {
      const data = await getDiscoveredProspects(campaignId);
      setProspects(data);
      // Automatically keep selection if still present
      setSelectedIds(new Set());
    } catch {
      toast.error('Failed to load discovered prospects');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedCampaignId) {
      loadProspects(selectedCampaignId);
    }
  }, [selectedCampaignId]);

  const activeCampaign = campaigns.find((c) => c.id === selectedCampaignId);

  const handleToggleCampaignStatus = async () => {
    if (!activeCampaign) return;
    const newStatus = activeCampaign.status === 'LIVE' ? 'PAUSED' : 'LIVE';
    try {
      const updated = await updateCampaignStatus(activeCampaign.id, newStatus);
      setCampaigns((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
      toast.success(`Campaign '${activeCampaign.name}' is now ${newStatus}`);
    } catch {
      toast.error('Failed to update campaign status');
    }
  };

  // Filtered prospects
  const filteredProspects = prospects.filter((p) => {
    const matchesSearch =
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.company.toLowerCase().includes(search.toLowerCase()) ||
      p.title.toLowerCase().includes(search.toLowerCase()) ||
      (p.email && p.email.toLowerCase().includes(search.toLowerCase()));

    if (!matchesSearch) return false;

    if (activeTab === 'ALL') return true;
    const st = (p.status || 'DISCOVERED').toUpperCase();
    if (activeTab === 'QUEUED') return st === 'QUEUED' || st === 'PROCESSING';
    if (activeTab === 'COMPLETED') return st === 'COMPLETED' || st === 'SENT' || st === 'CONTACTED' || st === 'FIT';
    if (activeTab === 'NO_FIT') return st === 'NO_FIT';
    return st === activeTab;
  });

  // Selection handlers
  const handleToggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const handleSelectAll = () => {
    if (selectedIds.size === filteredProspects.length && filteredProspects.length > 0) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(filteredProspects.map((p) => p.id)));
    }
  };

  const handleMarkSelected = async (targetId: string, currentStatus?: string) => {
    const newStatus = currentStatus === 'SELECTED' ? 'DISCOVERED' : 'SELECTED';
    try {
      await updateDiscoveredProspect(targetId, newStatus);
      setProspects((prev) =>
        prev.map((p) => (p.id === targetId ? { ...p, status: newStatus as any } : p))
      );
      if (newStatus === 'SELECTED') {
        setSelectedIds((prev) => new Set(prev).add(targetId));
      } else {
        setSelectedIds((prev) => {
          const next = new Set(prev);
          next.delete(targetId);
          return next;
        });
      }
    } catch {
      toast.error('Failed to update prospect status');
    }
  };

  const handleRejectProspect = async (targetId: string) => {
    try {
      await updateDiscoveredProspect(targetId, 'REJECTED');
      setProspects((prev) =>
        prev.map((p) => (p.id === targetId ? { ...p, status: 'REJECTED' as any } : p))
      );
      setSelectedIds((prev) => {
        const next = new Set(prev);
        next.delete(targetId);
        return next;
      });
      toast.success('Prospect rejected');
    } catch {
      toast.error('Failed to reject prospect');
    }
  };

  const handleRejectAllSelected = async () => {
    if (selectedIds.size === 0) return;
    const ids = Array.from(selectedIds);
    try {
      await Promise.all(ids.map((id) => updateDiscoveredProspect(id, 'REJECTED')));
      setProspects((prev) =>
        prev.map((p) => (selectedIds.has(p.id) ? { ...p, status: 'REJECTED' as any } : p))
      );
      setSelectedIds(new Set());
      toast.success(`Rejected ${ids.length} prospects`);
    } catch {
      toast.error('Failed to reject some prospects');
    }
  };

  // Run Discovery Agent handler with user-specified count
  const handleTriggerDiscovery = async () => {
    if (!selectedCampaignId) return;
    if (discoveryCount < 1) {
      toast.error('Please enter a valid count (at least 1)');
      return;
    }

    setIsDiscovering(true);
    try {
      const res = await runDiscoveryAgent(
        selectedCampaignId,
        discoveryCount,
        discoveryCriteria || undefined
      );
      toast.success(
        `Discovery Agent found ${res.stored_count + res.updated_count} prospects!`
      );
      setShowDiscoveryModal(false);
      setDiscoveryCriteria('');
      loadProspects(selectedCampaignId);
    } catch (err: any) {
      toast.error(err.message || 'Discovery agent failed to run');
    } finally {
      setIsDiscovering(false);
    }
  };

  // Stop SDR Pipeline handler
  const handleStopPipeline = () => {
    pipelineAbortedRef.current = true;
    toast('Stopping SDR pipeline after current lead finishes...', { icon: '🛑' });
  };

  // Start SDR Pipeline handler
  const handleStartPipeline = async () => {
    if (!selectedCampaignId) return;
    if (selectedIds.size === 0) {
      toast.error('Select at least one prospect to start the SDR pipeline');
      return;
    }

    const idsToRun = Array.from(selectedIds);
    pipelineAbortedRef.current = false;
    setIsStartingPipeline(true);
    setIsPipelineMinimized(false);
    setPipelineTotalCount(idsToRun.length);
    setPipelineCurrentIndex(0);

    // Optimistically update table to QUEUED
    setProspects((prev) =>
      prev.map((p) =>
        selectedIds.has(p.id) ? { ...p, status: 'QUEUED' as any } : p
      )
    );

    const accumulatedResults: StartPipelineResponse['results'] = [];

    try {
      for (let i = 0; i < idsToRun.length; i++) {
        if (pipelineAbortedRef.current) {
          toast('Pipeline stopped by user.', { icon: '⏹️' });
          const remainingIds = new Set(idsToRun.slice(i));
          setProspects((prev) =>
            prev.map((p) =>
              remainingIds.has(p.id) && (p.status === 'QUEUED' || p.status === 'PROCESSING')
                ? { ...p, status: 'DISCOVERED' as any }
                : p
            )
          );
          break;
        }
        const pid = idsToRun[i];
        setPipelineCurrentIndex(i);
        const currentP = prospects.find((p) => p.id === pid);
        setPipelineCurrentProspectName(currentP?.name || `Prospect ${i + 1}`);

        // Update single row to PROCESSING in UI
        setProspects((prev) =>
          prev.map((p) => (p.id === pid ? { ...p, status: 'PROCESSING' as any } : p))
        );

        try {
          const response = await startSdrPipeline(selectedCampaignId, [pid]);
          if (response.results && response.results.length > 0) {
            const r = response.results[0];
            accumulatedResults.push(r);
            const isSent = r.execution_status === 'SENT' || r.status === 'COMPLETED';
            const isNoFit = r.status === 'NO_FIT' || r.execution_status === 'NO_FIT';
            const displaySt = isSent ? 'COMPLETED' : isNoFit ? 'NO_FIT' : r.status;
            setProspects((prev) =>
              prev.map((p) =>
                p.id === pid
                  ? {
                      ...p,
                      status: displaySt as any,
                      channel: (r.channel as any) || p.channel,
                      icpScore: r.icp_score ?? p.icpScore,
                      lastActivity: isSent
                        ? 'Outreach dispatched'
                        : isNoFit
                        ? 'Disqualified (No Fit)'
                        : p.lastActivity,
                    }
                  : p
              )
            );
          }
        } catch (itemErr: any) {
          accumulatedResults.push({
            prospect_id: pid,
            name: currentP?.name || 'Prospect',
            company: currentP?.company || 'Company',
            status: 'FAILED',
            execution_status: 'FAILED',
            error: itemErr.message || 'Execution failed',
          });
          setProspects((prev) =>
            prev.map((p) => (p.id === pid ? { ...p, status: 'FAILED' as any } : p))
          );
        }
      }

      setPipelineRunResults(accumulatedResults);

      const sentCount = accumulatedResults.filter(
        (r) => r.execution_status === 'SENT' || r.status === 'COMPLETED'
      ).length;
      const noFitCount = accumulatedResults.filter(
        (r) => r.status === 'NO_FIT' || r.execution_status === 'NO_FIT'
      ).length;
      const failedCount = accumulatedResults.filter(
        (r) => r.status === 'FAILED' || r.execution_status === 'FAILED'
      ).length;

      if (sentCount > 0 && noFitCount === 0) {
        toast.success(`Autonomous outreach dispatched for ${sentCount} prospect(s)!`);
      } else if (noFitCount > 0) {
        toast(
          `SDR complete: ${sentCount} outreach sent, ${noFitCount} disqualified by ICP agent`,
          { icon: 'ℹ️' }
        );
      } else if (failedCount > 0) {
        toast.error(`SDR execution completed with ${failedCount} issue(s)`);
      } else if (accumulatedResults.length > 0 && !pipelineAbortedRef.current) {
        toast.success(`SDR Pipeline finished for ${accumulatedResults.length} prospects!`);
      }

      // Refresh prospect statuses
      await loadProspects(selectedCampaignId);
      setSelectedIds(new Set());
    } catch (err: any) {
      toast.error(err.message || 'Failed to execute SDR pipeline');
      loadProspects(selectedCampaignId);
    } finally {
      setIsStartingPipeline(false);
      setIsPipelineMinimized(false);
      pipelineAbortedRef.current = false;
    }
  };

  // Metrics computation
  const totalDiscovered = prospects.length;
  const countSelected = prospects.filter((p) => p.status === 'SELECTED').length;
  const countInPipeline = prospects.filter(
    (p) => p.status === 'QUEUED' || p.status === 'PROCESSING'
  ).length;
  const countCompleted = prospects.filter(
    (p) => p.status === 'COMPLETED' || p.status === 'FIT' || p.status === 'CONTACTED' || p.status === 'SENT'
  ).length;
  const countNoFit = prospects.filter((p) => p.status === 'NO_FIT').length;

  return (
    <div className="w-full bg-surface min-h-screen px-space-lg py-space-lg">
      <div className="flex flex-col gap-space-lg">

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-space-md">
        <div>
          <div className="flex items-center gap-2.5 mb-1">
            <h1 className="font-headline-lg text-headline-lg text-on-surface tracking-tight">Prospect Discovery Management</h1>
            <span className="px-2.5 py-0.5 rounded-full font-label-sm text-label-sm bg-surface-container text-on-surface-variant border border-outline-variant">
              Pre-Pipeline Stage
            </span>
          </div>
          <p className="font-body-md text-body-md text-on-surface-variant">
            Review, qualify, and selectively dispatch autonomous agent-discovered prospects to the SDR pipeline.
          </p>
        </div>
        <div className="flex items-center gap-space-sm flex-shrink-0">
          <button
            onClick={() => setShowDiscoveryModal(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-full bg-surface-container-lowest text-on-surface font-label-md text-label-md shadow-sm hover:bg-surface-container transition-all border border-outline-variant"
          >
            <Sparkles size={15} className="text-primary-container" />
            <span>Run Discovery Agent</span>
          </button>
          <button
            onClick={handleStartPipeline}
            disabled={selectedIds.size === 0 || isStartingPipeline}
            className={cn(
              'flex items-center gap-2 px-5 py-2 rounded-full font-label-md text-label-md shadow-sm transition-all',
              selectedIds.size === 0 || isStartingPipeline
                ? 'opacity-50 cursor-not-allowed bg-surface-container text-on-surface-variant'
                : 'bg-primary-container text-on-primary-container hover:bg-inverse-primary active:scale-95'
            )}
          >
            {isStartingPipeline ? (
              <RefreshCw size={15} className="animate-spin" />
            ) : (
              <Play size={15} className="fill-current" />
            )}
            <span>Start SDR Pipeline</span>
            {selectedIds.size > 0 && (
              <span className="ml-1 px-1.5 py-0.5 rounded-full font-label-sm text-label-sm bg-on-primary-container/20 font-bold">
                {selectedIds.size}
              </span>
            )}
          </button>
        </div>
      </div>

      {/* Campaign Selector Banner */}
      <div className="bg-surface-container-lowest rounded-2xl p-space-md shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-space-md">
          <div className="flex items-center gap-space-sm">
            <div className="w-9 h-9 rounded-xl bg-primary-fixed/40 flex items-center justify-center flex-shrink-0">
              <Target size={18} className="text-on-primary-fixed-variant" />
            </div>
            <div>
              <span className="font-label-sm text-label-sm text-outline uppercase tracking-wider">Active Campaign</span>
              <div className="flex items-center gap-2 mt-0.5">
                <select
                  value={selectedCampaignId}
                  onChange={(e) => setSelectedCampaignId(e.target.value)}
                  className="bg-surface-container-low border border-outline-variant rounded-xl px-3 py-1.5 font-label-md text-label-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/30"
                >
                  {campaigns.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name} ({c.status})
                    </option>
                  ))}
                </select>
                {activeCampaign && (
                  <div className="flex items-center gap-2">
                    <span className={cn(
                      'px-2.5 py-0.5 rounded-full font-label-sm text-label-sm font-semibold',
                      activeCampaign.status === 'LIVE'
                        ? 'bg-tertiary-fixed/40 text-on-tertiary-fixed'
                        : 'bg-surface-container text-on-surface-variant'
                    )}>
                      {activeCampaign.status}
                    </span>
                    <button
                      onClick={handleToggleCampaignStatus}
                      className={cn(
                        'px-2.5 py-0.5 rounded-full font-label-sm text-label-sm flex items-center gap-1 transition-colors',
                        activeCampaign.status === 'LIVE'
                          ? 'bg-surface-container text-on-surface-variant hover:bg-surface-container-high'
                          : 'bg-tertiary-container/30 text-on-tertiary-container hover:bg-tertiary-container/50'
                      )}
                    >
                      {activeCampaign.status === 'LIVE' ? (
                        <><Pause size={10} /><span>Pause</span></>
                      ) : (
                        <><Play size={10} className="fill-current text-tertiary" /><span>Activate</span></>
                      )}
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>

          {activeCampaign && (
            <div className="flex-1 max-w-xl md:border-l md:border-outline-variant md:pl-space-md">
              <span className="font-label-sm text-label-sm text-outline">Target ICP Criteria</span>
              <p className="font-body-sm text-body-sm text-on-surface font-medium mt-0.5 line-clamp-2">
                {activeCampaign.icp}
              </p>
            </div>
          )}

          <button
            onClick={() => loadProspects(selectedCampaignId)}
            className="p-2 text-outline hover:text-on-surface hover:bg-surface-container rounded-xl transition"
            title="Refresh prospects"
          >
            <RefreshCw size={15} />
          </button>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-space-sm">
        {[
          { label: 'Discovered Leads', value: totalDiscovered },
          { label: 'Selected for SDR', value: countSelected },
          { label: 'In Pipeline', value: countInPipeline },
          { label: 'Contacted / Sent', value: countCompleted },
          { label: 'Disqualified (No Fit)', value: countNoFit },
        ].map((card) => (
          <div key={card.label} className="bg-surface-container-lowest rounded-2xl p-space-md shadow-sm flex flex-col gap-2">
            <span className="font-label-sm text-label-sm text-outline uppercase tracking-wider">{card.label}</span>
            <span className="font-display-stat text-display-stat text-on-surface leading-none">{card.value}</span>
          </div>
        ))}
      </div>

      {/* Filter and Action Toolbar */}
      <div className="bg-surface-container-lowest rounded-2xl p-space-md shadow-sm flex flex-col gap-space-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-space-sm">
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 md:pb-0">
            {(
              [
                { id: 'ALL', label: 'All' },
                { id: 'DISCOVERED', label: 'Discovered' },
                { id: 'SELECTED', label: 'Selected' },
                { id: 'QUEUED', label: 'In Pipeline' },
                { id: 'COMPLETED', label: 'Contacted / Sent' },
                { id: 'NO_FIT', label: 'Disqualified (No Fit)' },
                { id: 'REJECTED', label: 'Rejected' },
              ] as { id: FilterTab; label: string }[]
            ).map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  'px-3 py-1.5 rounded-full font-label-md text-label-md whitespace-nowrap transition-colors',
                  activeTab === tab.id
                    ? 'bg-on-surface text-surface shadow-sm'
                    : 'text-on-surface-variant hover:bg-surface-container'
                )}
              >
                {tab.label}
              </button>
            ))}
          </div>
          <div className="relative w-full md:w-64">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-outline" />
            <input
              type="text"
              className="w-full bg-surface-container-low border border-outline-variant rounded-xl pl-9 pr-3 py-2 font-body-sm text-body-sm text-on-surface placeholder:text-outline focus:outline-none focus:ring-2 focus:ring-primary/20"
              placeholder="Search leads, companies, titles..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </div>

        <div className="flex items-center justify-between pt-space-xs border-t border-outline-variant font-label-sm text-label-sm text-on-surface-variant">
          <button
            onClick={handleSelectAll}
            className="flex items-center gap-1.5 font-medium hover:text-on-surface"
          >
            {selectedIds.size > 0 && selectedIds.size === filteredProspects.length ? (
              <CheckSquare size={14} className="text-primary" />
            ) : (
              <Square size={14} className="text-outline" />
            )}
            <span>
              {selectedIds.size === 0
                ? 'Select all in view'
                : `${selectedIds.size} of ${filteredProspects.length} selected`}
            </span>
          </button>
          {selectedIds.size > 0 && (
            <button
              onClick={handleRejectAllSelected}
              className="flex items-center gap-1 text-error hover:text-error font-medium px-2.5 py-1 rounded-full hover:bg-error-container transition-colors"
            >
              <XCircle size={13} />
              <span>Reject Selected ({selectedIds.size})</span>
            </button>
          )}
        </div>
      </div>

      {/* Prospects Table */}
      {loading ? (
        <div className="bg-surface-container-lowest rounded-2xl shadow-sm p-12 flex flex-col items-center gap-4">
          <div className="w-10 h-10 rounded-full border-2 border-primary-container border-t-primary animate-spin"></div>
          <span className="font-body-md text-body-md text-on-surface-variant">Loading prospects…</span>
        </div>
      ) : filteredProspects.length === 0 ? (
        <div className="bg-surface-container-lowest rounded-2xl p-12 text-center shadow-sm">
          <div className="w-14 h-14 rounded-2xl bg-primary-fixed/20 text-on-primary-fixed-variant flex items-center justify-center mx-auto mb-space-sm">
            <Sparkles size={24} />
          </div>
          <h3 className="font-headline-md text-headline-md text-on-surface">No prospects found</h3>
          <p className="font-body-md text-body-md text-on-surface-variant max-w-md mx-auto mt-1">
            {search
              ? 'No prospects match your current search query.'
              : 'Trigger the Discovery Agent to automatically find qualified leads for this campaign.'}
          </p>
          <button
            onClick={() => setShowDiscoveryModal(true)}
            className="mt-space-md inline-flex items-center gap-2 px-5 py-2 rounded-full bg-primary-container text-on-primary-container font-label-md text-label-md shadow-sm hover:bg-inverse-primary transition-all"
          >
            <Sparkles size={14} />
            Run Discovery Agent
          </button>
        </div>
      ) : (
        <div className="bg-surface-container-lowest rounded-2xl overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-surface-container-low border-b border-outline-variant">
                  <th className="py-3 px-4 w-10">
                    <input
                      type="checkbox"
                      checked={selectedIds.size > 0 && selectedIds.size === filteredProspects.length}
                      onChange={handleSelectAll}
                      className="rounded border-outline-variant"
                    />
                  </th>
                  {['Prospect', 'Company & Domain', 'Contact Info', 'Channel', 'ICP Score', 'Discovery Source', 'Status', 'Actions'].map((h) => (
                    <th key={h} className={cn('py-3 px-4 font-label-sm text-label-sm text-outline uppercase tracking-wider', h === 'Channel' || h === 'ICP Score' ? 'text-center' : h === 'Actions' ? 'text-right' : '')}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-outline-variant/40">
                {filteredProspects.map((p) => {
                  const isSelected = selectedIds.has(p.id);
                  const isQueuedOrProcessing = p.status === 'QUEUED' || p.status === 'PROCESSING';

                  return (
                    <tr
                      key={p.id}
                      className={cn(
                        'hover:bg-surface-container-low transition-colors cursor-pointer group',
                        isSelected && 'bg-primary-fixed/10'
                      )}
                    >
                      <td className="py-3 px-4" onClick={(e) => e.stopPropagation()}>
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => handleToggleSelect(p.id)}
                          disabled={isQueuedOrProcessing}
                          className="rounded border-outline-variant"
                        />
                      </td>

                      <td className="py-3 px-4" onClick={() => setSelectedProspectForDrawer(p)}>
                        <div className="flex items-center gap-2.5">
                          <div className="w-8 h-8 rounded-full bg-surface-container-high text-on-surface font-bold flex items-center justify-center font-label-md text-label-md flex-shrink-0 group-hover:bg-primary-fixed group-hover:text-on-primary-fixed transition-colors">
                            {p.name.charAt(0)}
                          </div>
                          <div>
                            <div className="font-label-md text-label-md text-on-surface group-hover:text-primary transition-colors flex items-center gap-1.5">
                              <span>{p.name}</span>
                              <UserCheck size={12} className="opacity-0 group-hover:opacity-100 transition-opacity" />
                            </div>
                            <div className="font-body-sm text-body-sm text-outline">{p.title}</div>
                          </div>
                        </div>
                      </td>

                      <td className="py-3 px-4" onClick={() => setSelectedProspectForDrawer(p)}>
                        <div className="font-label-md text-label-md text-on-surface">{p.company}</div>
                        <div className="font-body-sm text-body-sm text-outline flex items-center gap-1">
                          {p.domain || `${p.company.toLowerCase().replace(/\s+/g, '')}.com`}
                          {p.companySize && <span>• {p.companySize}</span>}
                        </div>
                      </td>

                      <td className="py-3 px-4" onClick={(e) => e.stopPropagation()}>
                        <div className="flex flex-col gap-1">
                          {p.email && (
                            <div className="flex items-center gap-1.5 font-body-sm text-body-sm text-on-surface-variant">
                              <Mail size={12} className="text-outline flex-shrink-0" />
                              <span className="truncate max-w-[160px]">{p.email}</span>
                            </div>
                          )}
                          {p.phone && (
                            <div className="flex items-center gap-1.5 font-body-sm text-body-sm text-on-surface-variant">
                              <Phone size={12} className="text-outline flex-shrink-0" />
                              <span>{p.phone}</span>
                            </div>
                          )}
                          {p.linkedin_url && (
                            <a href={p.linkedin_url} target="_blank" rel="noreferrer"
                              className="inline-flex items-center gap-1 text-primary hover:underline font-label-sm text-label-sm">
                              <svg className="w-3 h-3 fill-current" viewBox="0 0 24 24">
                                <path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.88 8.56a1.68 1.68 0 0 0 1.68-1.68c0-.93-.75-1.69-1.68-1.69a1.69 1.69 0 0 0-1.69 1.69c0 .93.76 1.68 1.69 1.68m1.39 9.94v-8.37H5.5v8.37h2.77z" />
                              </svg>
                              <span>Profile</span>
                              <ExternalLink size={9} />
                            </a>
                          )}
                          {!p.email && !p.phone && !p.linkedin_url && (
                            <span className="font-body-sm text-body-sm text-outline italic">No contact info</span>
                          )}
                        </div>
                      </td>

                      <td className="py-3 px-4 text-center" onClick={() => setSelectedProspectForDrawer(p)}>
                        {p.channel ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full font-label-sm text-label-sm bg-surface-container text-on-surface border border-outline-variant">
                            {p.channel === 'EMAIL' && <Mail size={11} className="text-primary" />}
                            {p.channel === 'SMS' && <Phone size={11} className="text-tertiary" />}
                            {p.channel === 'LINKEDIN' && (
                              <svg className="w-2.5 h-2.5 fill-primary" viewBox="0 0 24 24">
                                <path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.88 8.56a1.68 1.68 0 0 0 1.68-1.68c0-.93-.75-1.69-1.68-1.69a1.69 1.69 0 0 0-1.69 1.69c0 .93.76 1.68 1.69 1.68m1.39 9.94v-8.37H5.5v8.37h2.77z" />
                              </svg>
                            )}
                            <span>{p.channel}</span>
                          </span>
                        ) : (
                          <span className="text-outline font-body-sm text-body-sm">—</span>
                        )}
                      </td>

                      <td className="py-3 px-4 text-center" onClick={() => setSelectedProspectForDrawer(p)}>
                        {p.icpScore != null ? (
                          <span className={cn(
                            'font-label-md text-label-md tabular-nums px-2.5 py-0.5 rounded-full',
                            p.icpScore >= 75
                              ? 'bg-tertiary-fixed/40 text-on-tertiary-fixed'
                              : p.icpScore >= 50
                              ? 'bg-primary-fixed/40 text-on-primary-fixed-variant'
                              : 'bg-error-container text-on-error-container'
                          )}>
                            {p.icpScore}
                          </span>
                        ) : (
                          <span className="text-outline font-body-sm text-body-sm">—</span>
                        )}
                      </td>

                      <td className="py-3 px-4" onClick={() => setSelectedProspectForDrawer(p)}>
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full font-label-sm text-label-sm bg-primary-fixed/20 text-on-primary-fixed-variant border border-primary-fixed/40">
                          <Sparkles size={10} className="text-primary-container" />
                          <span>{p.discovery_source || 'Discovery Agent'}</span>
                        </span>
                        {p.lastActivity && (
                          <div className="font-body-sm text-body-sm text-outline mt-0.5 line-clamp-1 max-w-[150px]">
                            {p.lastActivity}
                          </div>
                        )}
                      </td>

                      <td className="py-3 px-4" onClick={() => setSelectedProspectForDrawer(p)}>
                        <StatusBadge status={(p.status || 'DISCOVERED') as any} />
                      </td>

                      <td className="py-3 px-4 text-right" onClick={(e) => e.stopPropagation()}>
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            onClick={() => setSelectedProspectForDrawer(p)}
                            className="p-1.5 rounded-lg text-outline hover:text-primary hover:bg-surface-container transition"
                            title="View profile"
                          >
                            <UserCheck size={14} />
                          </button>
                          <button
                            onClick={() => setInspectedProspect(p)}
                            className="p-1.5 rounded-lg text-outline hover:text-on-surface hover:bg-surface-container transition"
                            title="Inspect raw data"
                          >
                            <Eye size={14} />
                          </button>
                          <button
                            onClick={() => handleMarkSelected(p.id, p.status)}
                            disabled={isQueuedOrProcessing}
                            className={cn(
                              'px-2.5 py-1 rounded-full font-label-sm text-label-sm transition-colors disabled:opacity-50',
                              p.status === 'SELECTED'
                                ? 'bg-primary-fixed text-on-primary-fixed-variant hover:bg-primary-fixed-dim'
                                : 'bg-surface-container text-on-surface hover:bg-surface-container-high border border-outline-variant'
                            )}
                          >
                            {p.status === 'SELECTED' ? 'Selected' : 'Select'}
                          </button>
                          {p.status !== 'REJECTED' && (
                            <button
                              onClick={() => handleRejectProspect(p.id)}
                              disabled={isQueuedOrProcessing}
                              className="p-1.5 rounded-lg text-outline hover:text-error hover:bg-error-container transition disabled:opacity-50"
                              title="Reject"
                            >
                              <XCircle size={14} />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Discovery Agent Modal */}
      {showDiscoveryModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-surface-container-lowest rounded-2xl max-w-md w-full shadow-2xl overflow-hidden">
            <div className="px-space-lg py-space-md border-b border-outline-variant flex items-center justify-between">
              <div className="flex items-center gap-space-sm">
                <div className="w-9 h-9 rounded-xl bg-primary-fixed/30 flex items-center justify-center">
                  <Sparkles size={18} className="text-on-primary-fixed-variant" />
                </div>
                <div>
                  <h3 className="font-headline-sm text-headline-sm text-on-surface">Run Discovery Agent</h3>
                  <p className="font-body-sm text-body-sm text-outline">Autonomous lead generation for campaign</p>
                </div>
              </div>
              <button onClick={() => setShowDiscoveryModal(false)} className="text-outline hover:text-on-surface p-1 rounded-lg hover:bg-surface-container">
                <XCircle size={18} />
              </button>
            </div>

            <div className="p-space-lg flex flex-col gap-space-md">
              <div>
                <label className="font-label-md text-label-md text-on-surface mb-1 block">Target Campaign</label>
                <div className="font-body-md text-body-md bg-surface-container-low rounded-xl px-3 py-2 text-on-surface-variant">
                  {activeCampaign?.name || 'Selected Campaign'}
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="font-label-md text-label-md text-on-surface">Number of Prospects to Find</label>
                  <span className="font-label-md text-label-md text-primary">{discoveryCount} prospects</span>
                </div>
                <input
                  type="number" min={1} max={50}
                  value={discoveryCount}
                  onChange={(e) => setDiscoveryCount(Math.max(1, parseInt(e.target.value) || 1))}
                  className="w-full bg-surface-container-low border border-outline-variant rounded-xl px-3 py-2 font-body-md text-body-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/20"
                />
                <div className="flex items-center gap-1.5 mt-2">
                  {[3, 5, 10, 20].map((preset) => (
                    <button key={preset} type="button" onClick={() => setDiscoveryCount(preset)}
                      className={cn(
                        'px-3 py-1 rounded-full font-label-sm text-label-sm transition-colors',
                        discoveryCount === preset
                          ? 'bg-primary-container text-on-primary-container'
                          : 'bg-surface-container text-on-surface-variant hover:bg-surface-container-high'
                      )}>
                      {preset} leads
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="font-label-md text-label-md text-on-surface mb-1 block">ICP Refinements (Optional)</label>
                <textarea
                  rows={2}
                  value={discoveryCriteria}
                  onChange={(e) => setDiscoveryCriteria(e.target.value)}
                  placeholder={`Default: ${activeCampaign?.icp || 'Campaign ICP criteria'}`}
                  className="w-full bg-surface-container-low border border-outline-variant rounded-xl px-3 py-2 font-body-sm text-body-sm text-on-surface placeholder:text-outline focus:outline-none focus:ring-2 focus:ring-primary/20 resize-none"
                />
              </div>
            </div>

            <div className="px-space-lg py-space-md bg-surface-container-low border-t border-outline-variant flex items-center justify-end gap-space-sm">
              <button onClick={() => setShowDiscoveryModal(false)} disabled={isDiscovering}
                className="px-4 py-2 rounded-full bg-surface-container-lowest text-on-surface font-label-md text-label-md shadow-sm hover:bg-surface-container transition-all border border-outline-variant">
                Cancel
              </button>
              <button onClick={handleTriggerDiscovery} disabled={isDiscovering}
                className="px-4 py-2 rounded-full bg-primary-container text-on-primary-container font-label-md text-label-md shadow-sm hover:bg-inverse-primary transition-all flex items-center gap-2 disabled:opacity-60">
                {isDiscovering ? <><RefreshCw size={13} className="animate-spin" /><span>Discovering…</span></> : <><Sparkles size={13} /><span>Find {discoveryCount} Prospects</span></>}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Raw Data Inspector Modal */}
      {inspectedProspect && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-surface-container-lowest rounded-2xl max-w-xl w-full shadow-2xl overflow-hidden">
            <div className="px-space-lg py-space-md border-b border-outline-variant flex items-center justify-between">
              <div>
                <h3 className="font-headline-sm text-headline-sm text-on-surface">Agent Metadata Inspector</h3>
                <p className="font-body-sm text-body-sm text-outline">{inspectedProspect.name} · {inspectedProspect.company}</p>
              </div>
              <button onClick={() => setInspectedProspect(null)} className="text-outline hover:text-on-surface p-1 rounded-lg hover:bg-surface-container">
                <XCircle size={18} />
              </button>
            </div>
            <div className="p-space-lg max-h-[60vh] overflow-y-auto">
              <p className="font-body-sm text-body-sm text-on-surface-variant mb-2">Raw payload from Discovery Agent:</p>
              <pre className="p-space-md rounded-xl bg-inverse-surface text-primary-fixed-dim font-mono text-xs overflow-x-auto">
                {JSON.stringify(inspectedProspect.raw_data || { id: inspectedProspect.id, name: inspectedProspect.name, title: inspectedProspect.title, company: inspectedProspect.company, email: inspectedProspect.email, domain: inspectedProspect.domain, discovery_source: inspectedProspect.discovery_source, metadata: inspectedProspect.metadata }, null, 2)}
              </pre>
            </div>
            <div className="px-space-lg py-space-sm bg-surface-container-low border-t border-outline-variant flex justify-end">
              <button onClick={() => setInspectedProspect(null)}
                className="px-4 py-2 rounded-full bg-surface-container-lowest text-on-surface font-label-md text-label-md shadow-sm hover:bg-surface-container transition-all border border-outline-variant">
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Pipeline Minimized Widget */}
      {isStartingPipeline && isPipelineMinimized && (
        <div className="fixed bottom-6 right-6 z-50 w-96 bg-surface-container-lowest/95 backdrop-blur-md rounded-2xl shadow-2xl p-space-md">
          <div className="flex items-center justify-between pb-space-sm border-b border-outline-variant">
            <div className="flex items-center gap-2">
              <span className="relative flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-primary"></span>
              </span>
              <span className="font-label-md text-label-md text-on-surface">SDR Pipeline Running</span>
            </div>
            <div className="flex items-center gap-1">
              <button onClick={() => setIsPipelineMinimized(false)}
                className="flex items-center gap-1 font-label-sm text-label-sm text-on-surface-variant hover:text-on-surface bg-surface-container hover:bg-surface-container-high px-2 py-1 rounded-full transition">
                <Maximize2 size={12} /><span>Expand</span>
              </button>
              <button onClick={handleStopPipeline}
                className="flex items-center gap-1 font-label-sm text-label-sm text-error bg-error-container hover:brightness-95 px-2 py-1 rounded-full transition">
                <Square size={10} fill="currentColor" /><span>Stop</span>
              </button>
            </div>
          </div>
          <div className="mt-space-sm flex flex-col gap-2">
            <div className="flex items-center justify-between font-label-sm text-label-sm">
              <span className="text-on-surface-variant">Lead <span className="font-bold text-on-surface">{pipelineCurrentIndex + 1}</span> of <span className="font-bold text-on-surface">{pipelineTotalCount}</span></span>
              <span className="font-medium text-primary bg-primary-fixed/20 px-2 py-0.5 rounded-full truncate max-w-[170px]">{pipelineCurrentProspectName || 'Processing…'}</span>
            </div>
            <div className="w-full bg-surface-container rounded-full h-2 overflow-hidden">
              <div className="bg-primary h-2 rounded-full transition-all duration-300" style={{ width: `${Math.round(((pipelineCurrentIndex + 0.5) / Math.max(pipelineTotalCount, 1)) * 100)}%` }} />
            </div>
          </div>
        </div>
      )}

      {/* Pipeline Expanded Modal */}
      {isStartingPipeline && !isPipelineMinimized && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
          <div className="bg-surface-container-lowest rounded-2xl max-w-md w-full p-space-lg shadow-2xl flex flex-col gap-space-md">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
                </span>
                <span className="font-label-sm text-label-sm text-outline uppercase tracking-wider">Live Execution</span>
              </div>
              <div className="flex items-center gap-2">
                <button onClick={() => setIsPipelineMinimized(true)}
                  className="flex items-center gap-1 font-label-md text-label-md text-on-surface-variant bg-surface-container hover:bg-surface-container-high px-3 py-1.5 rounded-full transition">
                  <Minimize2 size={13} /><span>Minimize</span>
                </button>
                <button onClick={handleStopPipeline}
                  className="flex items-center gap-1 font-label-md text-label-md text-error bg-error-container hover:brightness-95 px-3 py-1.5 rounded-full transition">
                  <Square size={11} fill="currentColor" /><span>Stop</span>
                </button>
              </div>
            </div>

            <div className="flex flex-col items-center text-center gap-space-sm">
              <div className="w-14 h-14 rounded-2xl bg-primary-fixed/20 flex items-center justify-center">
                <RefreshCw size={28} className="animate-spin text-primary" />
              </div>
              <div>
                <h3 className="font-headline-md text-headline-md text-on-surface">Autonomous SDR Pipeline Running</h3>
                <p className="font-body-md text-body-md text-on-surface-variant mt-1">
                  Processing prospect <span className="font-semibold text-primary">{pipelineCurrentIndex + 1}</span> of <span className="font-semibold text-on-surface">{pipelineTotalCount}</span>
                </p>
                <span className="mt-1 inline-block px-3 py-1 bg-primary-fixed/20 rounded-full font-label-md text-label-md text-on-primary-fixed-variant">
                  {pipelineCurrentProspectName || 'Initializing…'}
                </span>
                <div className="w-full bg-surface-container rounded-full h-1.5 mt-3 overflow-hidden">
                  <div className="bg-primary h-1.5 rounded-full transition-all duration-300" style={{ width: `${Math.round(((pipelineCurrentIndex + 0.5) / Math.max(pipelineTotalCount, 1)) * 100)}%` }} />
                </div>
              </div>
            </div>

            <div className="bg-surface-container-low rounded-xl p-space-sm flex flex-col gap-2">
              {[
                { n: '1', label: 'Groq Deep Lead Research (6-Pillar Profile)', color: 'bg-primary-fixed/30 text-on-primary-fixed-variant' },
                { n: '2', label: 'ICP Fitment & Exclusion Qualification', color: 'bg-secondary-container text-on-secondary-container' },
                { n: '3', label: 'Outreach Strategy & Channel Routing', color: 'bg-primary-fixed/30 text-on-primary-fixed-variant' },
                { n: '4', label: 'Personalisation & Message Synthesis', color: 'bg-tertiary-fixed/30 text-on-tertiary-fixed' },
                { n: '5', label: 'Channel Dispatcher (Email / SMS / LinkedIn)', color: 'bg-surface-container-high text-on-surface-variant' },
              ].map((step) => (
                <div key={step.n} className="flex items-center gap-2 font-body-sm text-body-sm text-on-surface-variant">
                  <span className={`w-5 h-5 rounded-full ${step.color} font-label-sm text-label-sm flex items-center justify-center flex-shrink-0`}>{step.n}</span>
                  <span>{step.label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Pipeline Results Modal */}
      {pipelineRunResults && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
          <div className="bg-surface-container-lowest rounded-2xl max-w-2xl w-full max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
            <div className="px-space-lg py-space-md border-b border-outline-variant flex items-center justify-between bg-surface-container-low">
              <div className="flex items-center gap-space-sm">
                <div className="w-9 h-9 rounded-xl bg-tertiary-fixed/30 flex items-center justify-center">
                  <CheckCircle2 size={18} className="text-tertiary" />
                </div>
                <div>
                  <h3 className="font-headline-sm text-headline-sm text-on-surface">SDR Pipeline Execution Report</h3>
                  <p className="font-body-sm text-body-sm text-outline">Lead Research → ICP → Strategy → Outreach</p>
                </div>
              </div>
              <button onClick={() => setPipelineRunResults(null)} className="text-outline hover:text-on-surface p-1 rounded-lg hover:bg-surface-container">
                <XCircle size={18} />
              </button>
            </div>

            <div className="p-space-lg overflow-y-auto flex flex-col gap-space-md">
              <div className="grid grid-cols-3 gap-space-sm text-center">
                <div className="p-space-md bg-tertiary-fixed/20 rounded-xl">
                  <span className="font-label-sm text-label-sm text-on-tertiary-fixed">Outreach Sent</span>
                  <p className="font-display-stat text-display-stat text-on-tertiary-fixed mt-1">{pipelineRunResults.filter((r) => r.execution_status === 'SENT' || r.status === 'COMPLETED').length}</p>
                </div>
                <div className="p-space-md bg-primary-fixed/20 rounded-xl">
                  <span className="font-label-sm text-label-sm text-on-primary-fixed-variant">Disqualified</span>
                  <p className="font-display-stat text-display-stat text-on-primary-fixed-variant mt-1">{pipelineRunResults.filter((r) => r.status === 'NO_FIT' || r.execution_status === 'NO_FIT').length}</p>
                </div>
                <div className="p-space-md bg-surface-container rounded-xl">
                  <span className="font-label-sm text-label-sm text-outline">Total Processed</span>
                  <p className="font-display-stat text-display-stat text-on-surface mt-1">{pipelineRunResults.length}</p>
                </div>
              </div>

              <div className="flex flex-col gap-space-sm">
                <span className="font-label-md text-label-md text-on-surface">Prospect Breakdown</span>
                {pipelineRunResults.map((res) => {
                  const isSent = res.execution_status === 'SENT' || res.status === 'COMPLETED';
                  const isNoFit = res.status === 'NO_FIT' || res.execution_status === 'NO_FIT';
                  const fullProspect = prospects.find((p) => p.id === res.prospect_id);
                  return (
                    <div key={res.prospect_id} className="p-space-sm rounded-xl border border-outline-variant bg-surface-container-low flex flex-col sm:flex-row sm:items-center justify-between gap-space-sm hover:bg-surface-container transition-colors">
                      <div className="flex flex-col gap-1">
                        <div className="flex items-center gap-2">
                          <span className="font-label-md text-label-md text-on-surface">{res.name}</span>
                          <span className="font-body-sm text-body-sm text-outline">· {res.company}</span>
                          {res.icp_score != null && (
                            <span className="px-1.5 py-0.5 rounded-full font-label-sm text-label-sm bg-surface-container text-on-surface-variant">ICP: {res.icp_score}</span>
                          )}
                        </div>
                        {isSent && <p className="font-label-sm text-label-sm text-tertiary flex items-center gap-1"><CheckCircle2 size={12} />Dispatched via {res.channel || 'EMAIL'}</p>}
                        {isNoFit && <p className="font-label-sm text-label-sm text-on-primary-fixed-variant flex items-start gap-1"><ShieldAlert size={12} className="flex-shrink-0 mt-0.5" />{res.icp_reasoning || 'Disqualified by ICP agent'}</p>}
                        {!isSent && !isNoFit && res.error && <p className="font-label-sm text-label-sm text-error flex items-center gap-1"><AlertCircle size={12} />{res.error}</p>}
                      </div>
                      {fullProspect && (
                        <button onClick={() => setSelectedProspectForDrawer(fullProspect)}
                          className="flex items-center gap-1 px-3 py-1.5 rounded-full bg-surface-container-lowest text-on-surface font-label-sm text-label-sm shadow-sm hover:bg-surface-container transition-all border border-outline-variant">
                          <UserCheck size={12} /><span>View Profile</span>
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="px-space-lg py-space-sm bg-surface-container-low border-t border-outline-variant flex justify-end">
              <button onClick={() => setPipelineRunResults(null)}
                className="px-4 py-2 rounded-full bg-primary-container text-on-primary-container font-label-md text-label-md shadow-sm hover:bg-inverse-primary transition-all">
                Close Report
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Prospect Drawer */}
      {selectedProspectForDrawer && (
        <ProspectDrawer
          prospect={selectedProspectForDrawer}
          onClose={() => setSelectedProspectForDrawer(null)}
          onUpdated={(up) => {
            setProspects((prev) => prev.map((p) => (p.id === up.id ? up : p)));
            setSelectedProspectForDrawer(up);
          }}
          onDeleted={(delId) => {
            setProspects((prev) => prev.filter((p) => p.id !== delId));
            setSelectedProspectForDrawer(null);
          }}
        />
      )}

      </div>
    </div>
  );
}
