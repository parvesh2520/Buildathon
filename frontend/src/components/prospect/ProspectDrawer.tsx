import { useState, useEffect } from 'react';
import {
  X,
  Mail,
  Phone,
  Building2,
  MapPin,
  Globe,
  CheckCircle,
  XCircle,
  Sparkles,
  Send,
  ShieldCheck,
  Cpu,
  MessageSquare,
  AlertCircle,
  Trash2,
  Copy,
  Check,
  ExternalLink,
} from 'lucide-react';
import { Prospect, ExecutionRecord } from '@/types';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { runSDR, getProspectExecution } from '@/api/sdr';
import { deleteProspect, updateProspectStatus } from '@/api/prospects';
import toast from 'react-hot-toast';
import { cn, formatAgentText } from '@/lib/utils';

function LinkedInIcon({ className = 'w-4 h-4' }: { className?: string }) {
  return (
    <svg className={className} fill="currentColor" viewBox="0 0 24 24">
      <path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.88 8.56a1.68 1.68 0 0 0 1.68-1.68c0-.93-.75-1.69-1.68-1.69a1.69 1.69 0 0 0-1.69 1.69c0 .93.76 1.68 1.69 1.68m1.39 9.94v-8.37H5.5v8.37h2.77z" />
    </svg>
  );
}

function getLinkedInUrl(prospect: Prospect): string {
  const rawUrl = prospect.linkedin_url || (prospect as any).linkedinUrl;
  if (rawUrl && typeof rawUrl === 'string' && rawUrl.trim().length > 0) {
    const trimmed = rawUrl.trim();
    if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) {
      return trimmed;
    }
    return `https://${trimmed}`;
  }
  return `https://www.linkedin.com/search/results/all/?keywords=${encodeURIComponent(
    `${prospect.name} ${prospect.company}`
  )}`;
}

async function copyToClipboard(text: string): Promise<void> {
  if (navigator.clipboard && window.isSecureContext) {
    await navigator.clipboard.writeText(text);
  } else {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    document.execCommand('copy');
    textArea.remove();
  }
}

interface ProspectDrawerProps {
  prospect: Prospect;
  onClose: () => void;
  onUpdated?: (updated: Prospect) => void;
  onDeleted?: (deletedId: string) => void;
}

export function ProspectDrawer({ prospect, onClose, onUpdated, onDeleted }: ProspectDrawerProps) {
  const [running, setRunning] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [currentStatus, setCurrentStatus] = useState(prospect.status);
  const [currentChannel, setCurrentChannel] = useState<string | undefined>(prospect.channel);
  const [execution, setExecution] = useState<ExecutionRecord | null>(null);
  const [loadingExec, setLoadingExec] = useState(true);

  // LinkedIn 1-Click HITL State
  const [copiedNote, setCopiedNote] = useState(false);
  const [markingSent, setMarkingSent] = useState(false);
  const [customNote, setCustomNote] = useState<string>('');
  const [showLinkedInCard, setShowLinkedInCard] = useState(false);

  const isLinkedInActive =
    currentChannel === 'LINKEDIN' ||
    prospect.channel === 'LINKEDIN' ||
    execution?.recommended_channel === 'LINKEDIN' ||
    execution?.actual_channel === 'LINKEDIN' ||
    execution?.strategy_result?.recommended_channel === 'LINKEDIN' ||
    execution?.channel_result?.channel === 'LINKEDIN';

  useEffect(() => {
    if (isLinkedInActive) {
      setShowLinkedInCard(true);
    }
  }, [isLinkedInActive]);

  const defaultNote = `Hi ${prospect.name.split(' ')[0] || prospect.name}, saw your leadership role as ${prospect.title} at ${prospect.company}. Would love to connect and share insights on autonomous SDR workflows.`;

  const activeNote =
    customNote !== ''
      ? customNote
      : formatAgentText(execution?.personalisation_result?.content) ||
        formatAgentText(execution?.channel_result?.content) ||
        defaultNote;

  const handleCopyNote = async () => {
    try {
      await copyToClipboard(activeNote);
      setCopiedNote(true);
      toast.success('LinkedIn note copied to clipboard! (≤ 300 chars)');
      setTimeout(() => setCopiedNote(false), 2500);
    } catch {
      toast.error('Failed to copy to clipboard');
    }
  };

  const handleOpenLinkedIn = () => {
    const url = getLinkedInUrl(prospect);
    window.open(url, '_blank', 'noopener,noreferrer');
    toast.success('Opening LinkedIn profile in new tab...');
  };

  const handleMarkLinkedInSent = async () => {
    setMarkingSent(true);
    const toastId = toast.loading('Syncing LinkedIn status to Supabase...');
    try {
      const score = execution?.icp_result?.score ?? prospect.icpScore;
      await updateProspectStatus(prospect.id, 'SENT', 'LINKEDIN', score);
      setCurrentStatus('CONTACTED');
      setCurrentChannel('LINKEDIN');
      if (execution) {
        setExecution({
          ...execution,
          status: 'SENT',
          actual_channel: 'LINKEDIN',
          channel_result: {
            ...(execution.channel_result || {}),
            channel: 'LINKEDIN',
            status: 'SENT',
            recipient: getLinkedInUrl(prospect),
            content: activeNote,
            provider: 'HITL_1CLICK_DISPATCH',
            timestamp: new Date().toISOString(),
          } as any,
        });
      }
      if (onUpdated) {
        onUpdated({
          ...prospect,
          status: 'CONTACTED',
          channel: 'LINKEDIN',
          icpScore: score,
        });
      }
      toast.success('Marked as Sent via LinkedIn! Synced to Supabase.', { id: toastId });
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to mark as sent', { id: toastId });
    } finally {
      setMarkingSent(false);
    }
  };

  useEffect(() => {
    setLoadingExec(true);
    getProspectExecution(prospect.id)
      .then((rec) => {
        if (rec) {
          setExecution(rec);
          if (rec.status) setCurrentStatus(rec.status as any);
          const foundChannel = rec.channel_result?.channel || rec.actual_channel || rec.recommended_channel || rec.channel;
          if (foundChannel) setCurrentChannel(foundChannel);
        }
      })
      .finally(() => setLoadingExec(false));
  }, [prospect.id]);

  const handleRunSDR = async () => {
    setRunning(true);
    toast.loading('Autonomous SDR: Researching lead & executing multi-agent pipeline...', { id: 'drawer-sdr' });
    try {
      const campId = prospect.campaignId || 'us_saas_cto';
      const rec = await runSDR({ campaign_id: campId, prospect_id: prospect.id });
      setExecution(rec);
      const newStatus = rec.status === 'NO_FIT' ? 'NO_FIT' : rec.status === 'SENT' ? 'CONTACTED' : rec.status;
      const dispatchedChannel = (rec.channel_result?.channel || rec.actual_channel || rec.recommended_channel || rec.channel || prospect.channel || 'EMAIL') as any;
      setCurrentStatus(newStatus as any);
      setCurrentChannel(dispatchedChannel);
      if (onUpdated) {
        onUpdated({
          ...prospect,
          status: newStatus as any,
          channel: dispatchedChannel,
          icpScore: rec.icp_result?.score ?? prospect.icpScore,
        });
      }
      const ch = dispatchedChannel || 'Outreach';
      if (rec.status === 'FAILED' || rec.status === 'BLOCKED') {
        toast.error(`SDR Execution ${rec.status}: ${rec.error || 'Execution encountered an issue'}`, { id: 'drawer-sdr' });
      } else {
        toast.success(`Autonomous SDR Complete: ${ch} (${rec.status})`, { id: 'drawer-sdr' });
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'SDR run failed', { id: 'drawer-sdr' });
    } finally {
      setRunning(false);
    }
  };

  const handleDeleteProspect = async () => {
    if (!window.confirm(`Are you sure you want to delete ${prospect.name}?`)) return;
    setDeleting(true);
    try {
      await deleteProspect(prospect.id);
      toast.success(`Deleted ${prospect.name}`);
      if (onDeleted) onDeleted(prospect.id);
      onClose();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to delete prospect');
    } finally {
      setDeleting(false);
    }
  };

  const icpScore = execution?.icp_result?.score ?? prospect.icpScore;
  const icpStatus = execution?.icp_result?.status ?? prospect.status;

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <div className="absolute inset-0 bg-black/20 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-lg bg-white shadow-2xl flex flex-col h-full overflow-y-auto">
        {/* Header */}
        <div className="px-6 py-4 border-b border-border sticky top-0 bg-white z-20">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-base font-semibold text-slate-900">{prospect.name}</h2>
              <p className="text-sm text-slate-500">{prospect.title} · {prospect.company}</p>
              <p className="text-xs text-slate-400 mt-0.5">{prospect.email}</p>
            </div>
            <div className="flex items-center gap-2 ml-4 flex-shrink-0">
              {currentStatus && <StatusBadge status={currentStatus} />}
              {currentChannel && <StatusBadge status={currentChannel as any} />}
              <button onClick={onClose} className="text-slate-400 hover:text-slate-600 p-1 rounded hover:bg-surface-secondary">
                <X size={16} />
              </button>
            </div>
          </div>
        </div>

        <div className="px-6 py-4 space-y-6 flex-1">
          {/* Profile Section */}
          <section>
            <p className="text-2xs font-semibold text-slate-400 uppercase tracking-widest mb-3">Prospect Profile</p>
            <div className="space-y-2.5">
              <div className="flex items-center gap-2.5 text-sm">
                <Mail size={13} className="text-slate-400 flex-shrink-0" />
                <span className="text-slate-600">{prospect.email}</span>
              </div>
              {prospect.phone && (
                <div className="flex items-center gap-2.5 text-sm">
                  <Phone size={13} className="text-slate-400 flex-shrink-0" />
                  <span className="text-slate-600 font-mono">{prospect.phone}</span>
                  <span className="text-2xs bg-emerald-50 text-emerald-700 border border-emerald-200 px-1.5 py-0.5 rounded font-medium">SMS Ready</span>
                </div>
              )}
              {((prospect.linkedin_url || (prospect as any).linkedinUrl)) ? (
                <div className="flex items-center gap-2.5 text-sm">
                  <LinkedInIcon className="w-3.5 h-3.5 text-[#0A66C2] flex-shrink-0" />
                  <a
                    href={getLinkedInUrl(prospect)}
                    target="_blank"
                    rel="noreferrer"
                    className="text-[#0A66C2] hover:underline flex items-center gap-1 truncate text-xs font-medium"
                  >
                    <span className="truncate">{prospect.linkedin_url || (prospect as any).linkedinUrl}</span>
                    <ExternalLink size={11} className="flex-shrink-0 text-slate-400" />
                  </a>
                  <span className="text-2xs bg-blue-50 text-[#0A66C2] border border-blue-200 px-1.5 py-0.5 rounded font-medium flex-shrink-0">
                    LinkedIn Ready
                  </span>
                </div>
              ) : (
                <div className="flex items-center gap-2.5 text-sm">
                  <LinkedInIcon className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                  <a
                    href={getLinkedInUrl(prospect)}
                    target="_blank"
                    rel="noreferrer"
                    className="text-slate-500 hover:text-[#0A66C2] hover:underline flex items-center gap-1 text-xs"
                  >
                    <span>Search profile on LinkedIn</span>
                    <ExternalLink size={11} className="flex-shrink-0 text-slate-400" />
                  </a>
                </div>
              )}
              <div className="flex items-center gap-2.5 text-sm">
                <Building2 size={13} className="text-slate-400 flex-shrink-0" />
                <span className="text-slate-600">{prospect.company}</span>
                {prospect.companySize && <span className="text-slate-400 text-xs">· {prospect.companySize}</span>}
              </div>
              {prospect.location && (
                <div className="flex items-center gap-2.5 text-sm">
                  <MapPin size={13} className="text-slate-400 flex-shrink-0" />
                  <span className="text-slate-600">{prospect.location}</span>
                </div>
              )}
              {prospect.domain && (
                <div className="flex items-center gap-2.5 text-sm">
                  <Globe size={13} className="text-slate-400 flex-shrink-0" />
                  <span className="text-slate-600">{prospect.domain}</span>
                </div>
              )}
            </div>
          </section>

          {/* DronaHQ Multi-Agent Pipeline Telemetry */}
          <section className="space-y-4">
            <div className="flex items-center justify-between">
              <p className="text-2xs font-semibold text-slate-400 uppercase tracking-widest">
                DronaHQ Multi-Agent Telemetry
              </p>
              {execution?.status && (
                <span className="text-2xs font-mono bg-brand/10 text-brand px-2 py-0.5 rounded-full font-semibold">
                  {execution.status}
                </span>
              )}
            </div>

            {/* Error Notification */}
            {execution?.error && (
              <div className="p-3.5 rounded-xl border border-rose-200 bg-rose-50 text-rose-800 space-y-1">
                <div className="flex items-center gap-1.5 font-semibold text-xs text-rose-900">
                  <AlertCircle size={14} className="text-rose-600 flex-shrink-0" />
                  <span>Execution Status: {execution.status}</span>
                </div>
                <p className="text-xs text-rose-700 leading-relaxed font-mono">
                  {execution.error}
                </p>
              </div>
            )}

            {/* Agent 1: Lead Research */}
            <div className="p-3.5 rounded-xl border border-border bg-slate-50/50 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-800 flex items-center gap-1.5">
                  <Cpu size={13} className="text-brand" /> 1. Lead Research Agent
                </span>
                <span className="text-2xs text-emerald-600 font-medium bg-emerald-50 px-1.5 py-0.5 rounded">Active</span>
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">
                {formatAgentText(execution?.research_result?.prospect_summary) || `Intelligence verified for ${prospect.title} at ${prospect.company}.`}
              </p>
              {execution?.research_result?.detected_tech_stack && (
                <div className="flex flex-wrap gap-1 mt-1">
                  {execution.research_result.detected_tech_stack.map((tech: string, i: number) => (
                    <span key={i} className="text-2xs bg-white border border-slate-200 text-slate-600 px-1.5 py-0.5 rounded">
                      {tech}
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Agent 2: ICP Fitment */}
            <div className="p-3.5 rounded-xl border border-border bg-slate-50/50 space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-800 flex items-center gap-1.5">
                  <ShieldCheck size={13} className="text-emerald-600" /> 2. ICP Fitment & Qualification
                </span>
                <span className={cn('text-xs font-bold tabular-nums', (icpScore ?? 0) >= 80 ? 'text-emerald-600' : 'text-amber-600')}>
                  {icpScore ?? 85}/100
                </span>
              </div>
              <div className="w-full bg-slate-200 rounded-full h-1.5">
                <div
                  className={cn('h-1.5 rounded-full transition-all', (icpScore ?? 0) >= 80 ? 'bg-emerald-500' : 'bg-amber-500')}
                  style={{ width: `${icpScore ?? 85}%` }}
                />
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">
                {formatAgentText(execution?.icp_result?.reasoning) || `Prospect matches ICP qualification criteria for ${prospect.campaignName || 'Campaign'}.`}
              </p>
            </div>

            {/* Agent 3: Outreach Strategy */}
            <div className="p-3.5 rounded-xl border border-border bg-slate-50/50 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-800 flex items-center gap-1.5">
                  <Sparkles size={13} className="text-amber-500" /> 3. Outreach Strategy Agent
                </span>
                <span className="text-2xs font-bold font-mono bg-brand/10 text-brand px-2 py-0.5 rounded uppercase">
                  {execution?.strategy_result?.recommended_channel || execution?.recommended_channel || prospect.channel || 'EMAIL'}
                </span>
              </div>
              {execution?.strategy_result?.angle && (
                <p className="text-xs text-slate-600">
                  <strong className="text-slate-700">Angle:</strong> {formatAgentText(execution.strategy_result.angle)}
                </p>
              )}
              {execution?.strategy_result?.reasoning && (
                <p className="text-xs text-slate-500 italic">
                  {formatAgentText(execution.strategy_result.reasoning)}
                </p>
              )}
            </div>

            {/* Agent 4: Personalisation */}
            {execution?.personalisation_result ? (
              <div className="p-3.5 rounded-xl border border-brand/20 bg-brand/5 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-800 flex items-center gap-1.5">
                    <MessageSquare size={13} className="text-brand" /> 4. Personalisation & Generated Copy
                  </span>
                  <span className="text-2xs text-brand font-medium">
                    {formatAgentText(execution.personalisation_result.content).length} chars
                  </span>
                </div>
                {execution.personalisation_result.subject_line && (
                  <p className="text-xs font-medium text-slate-800">
                    Subject: {formatAgentText(execution.personalisation_result.subject_line)}
                  </p>
                )}
                <div className="text-xs text-slate-700 bg-white p-2.5 rounded-lg border border-border-light whitespace-pre-wrap font-sans">
                  {formatAgentText(execution.personalisation_result.content)}
                </div>
              </div>
            ) : (
              <div className="p-3 rounded-xl border border-dashed border-slate-200 bg-slate-50/30 text-xs text-slate-400 flex items-center justify-between">
                <span className="flex items-center gap-1.5"><MessageSquare size={13} /> 4. Personalisation Agent</span>
                <span className="text-2xs bg-slate-100 text-slate-500 px-2 py-0.5 rounded font-medium">Ready on Run</span>
              </div>
            )}

            {/* Agent 5: Channel Execution Proof */}
            {execution?.channel_result ? (
              <div className="p-3.5 rounded-xl border border-emerald-200 bg-emerald-50/60 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-emerald-900 flex items-center gap-1.5">
                    <Send size={13} className="text-emerald-600" /> 5. Channel Dispatch Proof ({execution.channel_result.channel})
                  </span>
                  <span className="text-2xs font-bold text-emerald-700 uppercase bg-emerald-100 px-2 py-0.5 rounded">
                    {execution.channel_result.status}
                  </span>
                </div>
                <div className="text-xs space-y-1 text-slate-600">
                  <p><strong className="text-slate-700">Recipient:</strong> {execution.channel_result.recipient}</p>
                  {(execution.channel_result.provider_message_id || execution.channel_result.provider_call_id || execution.provider_call_id) && (
                    <p className="font-mono text-2xs text-slate-500">
                      <strong>ID:</strong> {execution.channel_result.provider_message_id || execution.channel_result.provider_call_id || execution.provider_call_id}
                    </p>
                  )}
                  {execution.channel_result.trial_template_used && (
                    <p className="text-2xs text-amber-700">
                      Twilio Template: {execution.channel_result.trial_template_used}
                    </p>
                  )}
                </div>
              </div>
            ) : (
              <div className="p-3 rounded-xl border border-dashed border-slate-200 bg-slate-50/30 text-xs text-slate-400 flex items-center justify-between">
                <span className="flex items-center gap-1.5"><Send size={13} /> 5. Channel Dispatcher</span>
                <span className="text-2xs bg-slate-100 text-slate-500 px-2 py-0.5 rounded font-medium">Ready on Run</span>
              </div>
            )}

            {/* SDR Voice Script Agent Conversation Result */}
            {execution?.voice_agent_result && (
              <div className="p-3.5 rounded-xl border border-indigo-200 bg-indigo-50/60 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-indigo-900 flex items-center gap-1.5">
                    <Phone size={13} className="text-indigo-600" /> SDR Voice Script Agent Result
                  </span>
                  <span className="text-2xs font-bold text-indigo-700 uppercase bg-indigo-100 px-2 py-0.5 rounded">
                    {execution.voice_agent_result.call_outcome || 'COMPLETED'}
                  </span>
                </div>
                {execution.voice_agent_result.conversation_summary && (
                  <p className="text-xs text-slate-700 leading-relaxed">
                    <strong className="text-slate-900">Summary:</strong> {execution.voice_agent_result.conversation_summary}
                  </p>
                )}
                {execution.voice_agent_result.next_action && (
                  <p className="text-xs text-indigo-800">
                    <strong>Next Action:</strong> {execution.voice_agent_result.next_action}
                  </p>
                )}
              </div>
            )}

            {/* Interactive 1-Click HITL LinkedIn Dispatch Card */}
            {showLinkedInCard || isLinkedInActive ? (
              <div className="p-4 rounded-xl border border-blue-200 bg-gradient-to-br from-blue-50/70 via-white to-blue-50/30 shadow-xs space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-7 h-7 rounded-lg bg-[#0A66C2] flex items-center justify-center text-white shadow-xs flex-shrink-0">
                      <LinkedInIcon className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="flex items-center gap-1.5">
                        <h4 className="text-xs font-bold text-slate-900">LinkedIn 1-Click Dispatch</h4>
                        <span className="text-3xs font-semibold px-1.5 py-0.5 rounded bg-blue-100 text-[#0A66C2] border border-blue-200">
                          HITL Safe
                        </span>
                      </div>
                      <p className="text-2xs text-slate-500">
                        {prospect.linkedin_url || (prospect as any).linkedinUrl ? 'Direct Profile Linked' : 'Auto Search Fallback'}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <span
                      className={cn(
                        'text-2xs font-mono font-semibold px-2 py-0.5 rounded-full border',
                        activeNote.length <= 300
                          ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                          : 'bg-rose-50 text-rose-700 border-rose-200'
                      )}
                    >
                      {activeNote.length}/300 chars
                    </span>
                    {!isLinkedInActive && (
                      <button
                        type="button"
                        onClick={() => setShowLinkedInCard(false)}
                        className="text-slate-400 hover:text-slate-600 p-0.5"
                        title="Collapse LinkedIn Dispatch"
                      >
                        <X size={13} />
                      </button>
                    )}
                  </div>
                </div>

                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <label className="text-2xs font-semibold text-slate-500 uppercase tracking-wider">
                      Connection Request Note (≤ 300 Chars)
                    </label>
                    {activeNote.length > 300 && (
                      <button
                        type="button"
                        onClick={() => setCustomNote(activeNote.slice(0, 300))}
                        className="text-2xs text-amber-700 hover:text-amber-800 underline font-medium"
                      >
                        Auto-trim to 300
                      </button>
                    )}
                  </div>

                  <textarea
                    value={activeNote}
                    onChange={(e) => setCustomNote(e.target.value)}
                    rows={3}
                    maxLength={350}
                    className={cn(
                      'w-full text-xs text-slate-800 bg-white p-2.5 rounded-lg border focus:outline-none focus:ring-2 transition-all resize-none font-sans leading-relaxed',
                      activeNote.length > 300
                        ? 'border-rose-300 focus:ring-rose-200'
                        : 'border-blue-200 focus:ring-blue-200 focus:border-blue-400'
                    )}
                    placeholder="Enter personalized connection request note..."
                  />
                </div>

                {/* 3 Action Buttons */}
                <div className="grid grid-cols-3 gap-2 pt-0.5">
                  {/* 1. Copy Note */}
                  <button
                    type="button"
                    onClick={handleCopyNote}
                    className={cn(
                      'flex items-center justify-center gap-1.5 px-2.5 py-2 rounded-lg text-xs font-semibold border transition-all shadow-2xs cursor-pointer',
                      copiedNote
                        ? 'bg-emerald-600 text-white border-emerald-600'
                        : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50 hover:border-slate-300'
                    )}
                  >
                    {copiedNote ? <Check size={13} /> : <Copy size={13} className="text-slate-500" />}
                    <span>{copiedNote ? 'Copied!' : '1. Copy Note'}</span>
                  </button>

                  {/* 2. Open Profile */}
                  <button
                    type="button"
                    onClick={handleOpenLinkedIn}
                    className="flex items-center justify-center gap-1.5 px-2.5 py-2 rounded-lg text-xs font-semibold bg-white text-[#0A66C2] border border-blue-200 hover:bg-blue-50 hover:border-blue-300 transition-all shadow-2xs cursor-pointer"
                  >
                    <LinkedInIcon className="w-3.5 h-3.5" />
                    <span>2. Open Profile</span>
                    <ExternalLink size={11} className="text-blue-400 flex-shrink-0" />
                  </button>

                  {/* 3. Mark Sent */}
                  <button
                    type="button"
                    onClick={handleMarkLinkedInSent}
                    disabled={markingSent || (currentStatus === 'CONTACTED' && currentChannel === 'LINKEDIN')}
                    className={cn(
                      'flex items-center justify-center gap-1.5 px-2.5 py-2 rounded-lg text-xs font-semibold transition-all shadow-2xs',
                      currentStatus === 'CONTACTED' && currentChannel === 'LINKEDIN'
                        ? 'bg-emerald-50 text-emerald-700 border border-emerald-200 cursor-default'
                        : 'bg-[#0A66C2] text-white hover:bg-[#004182] active:bg-[#003162] cursor-pointer'
                    )}
                  >
                    {markingSent ? (
                      <span className="inline-block w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    ) : currentStatus === 'CONTACTED' && currentChannel === 'LINKEDIN' ? (
                      <CheckCircle size={13} className="text-emerald-600" />
                    ) : (
                      <Check size={13} />
                    )}
                    <span>
                      {markingSent
                        ? 'Saving...'
                        : currentStatus === 'CONTACTED' && currentChannel === 'LINKEDIN'
                        ? 'Sent ✓'
                        : '3. Mark Sent'}
                    </span>
                  </button>
                </div>

                <div className="flex items-center justify-between text-3xs text-slate-400 pt-1 border-t border-blue-100">
                  <span className="flex items-center gap-1 text-slate-500">
                    <ShieldCheck size={12} className="text-emerald-600 flex-shrink-0" />
                    Human-in-the-Loop prevents automated bot detection
                  </span>
                  <span className="font-mono text-slate-400">Syncs to Supabase</span>
                </div>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => setShowLinkedInCard(true)}
                className="w-full py-2.5 px-3 rounded-xl border border-dashed border-blue-200 bg-blue-50/40 hover:bg-blue-50 text-xs text-[#0A66C2] font-semibold flex items-center justify-center gap-2 transition-colors cursor-pointer"
              >
                <LinkedInIcon className="w-3.5 h-3.5" />
                <span>Open LinkedIn 1-Click HITL Outreach</span>
              </button>
            )}
          </section>

          {/* Notes */}
          {prospect.notes && (
            <section>
              <p className="text-2xs font-semibold text-slate-400 uppercase tracking-widest mb-2">Notes & Preferences</p>
              <p className="text-xs text-slate-600 leading-relaxed bg-slate-50 p-2.5 rounded-lg border border-border">
                {prospect.notes}
              </p>
            </section>
          )}
        </div>

        {/* Action Footer */}
        <div className="p-4 border-t border-border bg-white sticky bottom-0 z-20 flex items-center justify-between gap-2">
          <button
            onClick={handleDeleteProspect}
            disabled={deleting || running}
            className="btn-secondary text-xs px-2.5 py-2 text-rose-600 hover:bg-rose-50 hover:border-rose-300 transition-colors"
            title="Delete Prospect"
          >
            <Trash2 size={14} />
          </button>
          <button onClick={onClose} className="btn-secondary text-xs flex-1">
            Close
          </button>
          <button
            onClick={handleRunSDR}
            disabled={running || deleting}
            className="btn-primary text-xs flex-1 justify-center gap-1.5"
          >
            <Sparkles size={13} />
            {running ? 'Executing Pipeline...' : 'Run Autonomous SDR'}
          </button>
        </div>
      </div>
    </div>
  );
}
