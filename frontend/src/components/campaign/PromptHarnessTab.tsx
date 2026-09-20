import { useState, useEffect } from 'react';
import { Sparkles, Save, RotateCcw, Check, History, BookOpen, AlertCircle } from 'lucide-react';
import { getCampaignPrompts, saveCampaignPrompts, rollbackCampaignPrompts } from '@/api/campaigns';
import toast from 'react-hot-toast';
import { cn } from '@/lib/utils';

interface PromptHarnessTabProps {
  campaignId: string;
}

const AGENT_LABELS: Record<string, { label: string; role: string }> = {
  icp_fitment: { label: '1. ICP Fitment Agent', role: 'Qualifies or rejects leads against ICP thresholds' },
  lead_research: { label: '2. Lead Research Agent', role: 'Scrapes domain & detects technical infrastructure' },
  outreach_strategy: { label: '3. Outreach Strategy Agent', role: 'Determines optimal channel & pitch angle' },
  personalisation: { label: '4. Personalisation Agent', role: 'Synthesizes targeted copy under token constraints' },
  conversation: { label: '5. Conversation Agent', role: 'Parses inbound replies & determines objection action' },
  follow_up: { label: '6. Follow-up Agent', role: 'Calculates multi-touch cadence & cooldown stops' },
  voice_sdr: { label: '7. Voice SDR Agent', role: 'Synthesizes Twilio speech prompts & handles objections' },
};

export function PromptHarnessTab({ campaignId }: PromptHarnessTabProps) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [systemPrompt, setSystemPrompt] = useState('');
  const [agentPrompts, setAgentPrompts] = useState<Record<string, string>>({});
  const [currentVersion, setCurrentVersion] = useState('v1.0');
  const [history, setHistory] = useState<any[]>([]);
  const [selectedHistoryVer, setSelectedHistoryVer] = useState<string | null>(null);

  useEffect(() => {
    loadPrompts();
  }, [campaignId]);

  const loadPrompts = async () => {
    setLoading(true);
    try {
      const data = await getCampaignPrompts(campaignId);
      if (data?.current) {
        setSystemPrompt(data.current.system_prompt || '');
        setAgentPrompts(data.current.agent_prompts || {});
        setCurrentVersion(data.current.version || 'v1.0');
        setHistory(data.history || []);
      }
    } catch {
      toast.error('Failed to load prompts');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveNewVersion = async () => {
    setSaving(true);
    try {
      const updated = await saveCampaignPrompts(campaignId, systemPrompt, agentPrompts);
      setCurrentVersion(updated.current.version);
      setHistory(updated.history);
      toast.success(`Saved new harness version: ${updated.current.version}`);
    } catch {
      toast.error('Failed to save prompt version');
    } finally {
      setSaving(false);
    }
  };

  const handleRollback = async (version: string) => {
    if (!window.confirm(`Are you sure you want to roll back prompts to ${version}?`)) return;
    try {
      await rollbackCampaignPrompts(campaignId, version);
      toast.success(`Rolled back active harness to ${version}`);
      loadPrompts();
    } catch {
      toast.error('Rollback failed');
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-xs text-slate-400">Loading AI Prompt Harness...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="card p-5 bg-gradient-to-r from-brand/5 via-white to-brand/5 border-brand/20 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Sparkles size={16} className="text-brand" />
            <h3 className="text-sm font-bold text-slate-800">Campaign AI Prompt & Harness Control</h3>
            <span className="bg-brand text-white font-mono text-2xs px-2 py-0.5 rounded-full font-semibold">
              Active: {currentVersion}
            </span>
          </div>
          <p className="text-xs text-slate-500">
            Configure system prompts, agent instructions, guardrails, and rollback past iterations with 1 click.
          </p>
        </div>

        <button
          onClick={handleSaveNewVersion}
          disabled={saving}
          className="btn-primary text-xs flex items-center gap-1.5 cursor-pointer shadow-xs"
        >
          <Save size={13} />
          {saving ? 'Saving Version...' : 'Save New Version'}
        </button>
      </div>

      <div className="grid grid-cols-[1fr_280px] gap-6">
        {/* Main Editor */}
        <div className="space-y-5">
          {/* Campaign System Prompt */}
          <div className="card p-5 space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold text-slate-700 uppercase tracking-wide">
                Campaign-Level System Prompt & Guardrails
              </label>
              <span className="text-2xs text-slate-400 font-mono">Shared context across all 7 agents</span>
            </div>
            <textarea
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              rows={4}
              className="w-full text-xs text-slate-700 bg-surface-secondary p-3 rounded-lg border border-border focus:bg-white focus:outline-none focus:ring-1 focus:ring-brand font-mono leading-relaxed"
            />
          </div>

          {/* Per-Agent Prompts */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wide">
              Per-Agent Operational Prompts (7 Multi-Agent Suite)
            </h4>

            {Object.entries(AGENT_LABELS).map(([key, info]) => (
              <div key={key} className="card p-4 space-y-1.5">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-xs font-bold text-slate-800">{info.label}</span>
                    <span className="text-2xs text-slate-400 ml-2 font-medium">({info.role})</span>
                  </div>
                </div>
                <textarea
                  value={agentPrompts[key] || ''}
                  onChange={(e) =>
                    setAgentPrompts({ ...agentPrompts, [key]: e.target.value })
                  }
                  rows={2}
                  className="w-full text-xs text-slate-700 bg-surface-secondary p-2.5 rounded-lg border border-border focus:bg-white focus:outline-none focus:ring-1 focus:ring-brand font-sans leading-relaxed"
                  placeholder={`Instructions for ${info.label}...`}
                />
              </div>
            ))}
          </div>
        </div>

        {/* Version History & Rollback Sidebar */}
        <div className="space-y-4">
          <div className="card p-4 space-y-3">
            <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800 border-b border-border pb-2">
              <History size={14} className="text-slate-500" />
              <span>Prompt Version History</span>
            </div>

            <div className="space-y-2">
              {history.map((ver, i) => {
                const isCurrent = ver.version === currentVersion;
                return (
                  <div
                    key={i}
                    className={cn(
                      'p-3 rounded-xl border text-xs transition-all space-y-1',
                      isCurrent
                        ? 'border-brand/40 bg-brand/5'
                        : 'border-border bg-white hover:border-slate-300'
                    )}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold font-mono text-slate-800">{ver.version}</span>
                      {isCurrent ? (
                        <span className="text-3xs bg-brand text-white px-1.5 py-0.5 rounded font-semibold">
                          Active
                        </span>
                      ) : (
                        <button
                          onClick={() => handleRollback(ver.version)}
                          className="text-3xs text-brand hover:underline font-semibold flex items-center gap-0.5 cursor-pointer"
                        >
                          <RotateCcw size={10} /> Rollback
                        </button>
                      )}
                    </div>
                    <p className="text-2xs text-slate-500">By: {ver.author || 'Operator'}</p>
                    <p className="text-3xs text-slate-400">
                      {ver.updated_at ? new Date(ver.updated_at).toLocaleDateString() : 'Initial'}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="card p-4 bg-surface-secondary border-dashed text-xs text-slate-500 space-y-1.5">
            <div className="flex items-center gap-1 text-slate-700 font-semibold">
              <AlertCircle size={13} className="text-brand" />
              <span>Prompt Isolation Policy</span>
            </div>
            <p className="text-2xs leading-relaxed text-slate-500">
              Changes to this campaign’s prompts are strictly isolated and will never affect other concurrent campaigns.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
