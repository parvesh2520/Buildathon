import React, { useState, useEffect, useRef, useCallback } from 'react';
import { getCampaigns } from '@/api/campaigns';
import { getProspects } from '@/api/prospects';
import { getAgents, getExecutions } from '@/api/sdr';
import { getRAGDocuments } from '@/api/system';
import { formatAgentText } from '@/lib/utils';

async function sbGet<T>(table: string): Promise<T[]> {
  try {
    if (table === 'campaigns') {
      return (await getCampaigns()).map((campaign) => ({
        ...campaign,
        enabled_channels: (campaign as any).enabled_channels || ['EMAIL', 'SMS', 'LINKEDIN', 'PHONE'],
      })) as T[];
    }
    if (table === 'prospects') {
      return (await getProspects()).map((prospect) => ({
        ...prospect,
        icp_score: prospect.icpScore ?? null,
      })) as T[];
    }
    if (table === 'outreach_messages') {
      return (await getExecutions()).map((execution) => ({
        id: execution.execution_id,
        recipient: execution.prospect_id,
        subject: formatAgentText(execution.personalisation_result?.subject_line) || '',
        status: execution.status,
        provider: execution.actual_channel || execution.recommended_channel || 'SDR',
        content: formatAgentText(execution.personalisation_result?.content) || execution.error || '',
      })) as T[];
    }
    if (table === 'knowledge_base') {
      const data = await getRAGDocuments();
      return (data.documents || []) as T[];
    }
    if (table === 'agent_results') {
      return (await getAgents()).map((agent) => ({
        agent_type: agent.name,
        score: agent.successRate,
        summary: agent.description,
      })) as T[];
    }
    return [];
  } catch {
    return [];
  }
}

// ─── Data types ───────────────────────────────────────────────────────────────
interface Campaign {
  id: string; name: string; status: string;
  enabled_channels?: string[]; description?: string;
}
interface Prospect {
  id: string; name: string; title: string; company: string;
  icp_score: number | null; status: string; email?: string;
}
interface OutreachMsg {
  id?: string; recipient: string; subject: string;
  status: string; provider: string; content: string;
}
interface KBItem { title: string; campaign_id: string; content: string; }
interface AgentResult { agent_type: string; score: number; summary: string; }

// ─── Message content union ────────────────────────────────────────────────────
type BotContent =
  | { kind: 'loading' }
  | { kind: 'error'; text: string }
  | { kind: 'prospects'; items: Prospect[]; suggestion: string }
  | { kind: 'campaigns'; items: Campaign[] }
  | { kind: 'outreach'; items: OutreachMsg[] }
  | { kind: 'knowledge'; items: KBItem[] }
  | { kind: 'agents'; items: AgentResult[] };

interface ChatMsg {
  id: string;
  role: 'user' | 'bot';
  userText?: string;
  content?: BotContent;
  ts: Date;
}

// ─── helpers ──────────────────────────────────────────────────────────────────
function abbr(name: string) {
  return name.split(/\s+/).map(w => w[0]).join('').slice(0, 2).toUpperCase();
}
function tsLabel(d: Date) {
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}
function uid() { return Math.random().toString(36).slice(2); }

// ─── Card components ──────────────────────────────────────────────────────────

function ProspectCard({ p }: { p: Prospect }) {
  const statusTag =
    p.status === 'REPLIED' ? { label: '1x Reply', color: 'bg-emerald-100 text-emerald-700', icon: '↩' } :
    p.status === 'SENT' || p.status === 'CONTACTED' ? { label: '1x Outreach', color: 'bg-blue-50 text-blue-700', icon: '✉' } :
    p.status === 'REJECTED' || p.status === 'NO_FIT' ? { label: '1x Rejected', color: 'bg-red-50 text-red-600', icon: '✕' } :
    p.status === 'REVIEW' ? { label: '1x Review', color: 'bg-amber-50 text-amber-700', icon: '⚑' } :
    { label: p.status, color: 'bg-surface-container text-on-surface-variant', icon: '·' };

  const score = p.icp_score ?? 0;
  const scoreBg = score >= 75 ? 'bg-tertiary text-on-tertiary' : score >= 50 ? 'bg-primary-container text-on-primary-container' : 'bg-error-container text-on-error-container';

  return (
    <div className="flex flex-col gap-2 p-3 bg-white rounded-xl border border-outline-variant/30 shadow-sm min-w-0">
      <div className="flex items-center justify-between">
        <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${statusTag.color}`}>
          {statusTag.icon} {statusTag.label}
        </span>
        <span className="font-label-sm text-label-sm text-outline">{p.title?.split(' ').slice(0, 2).join(' ')}</span>
      </div>
      <div className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-md bg-on-surface/10 flex items-center justify-center font-label-sm text-label-sm font-bold text-on-surface flex-shrink-0">
          {abbr(p.company)}
        </div>
        <span className="font-label-md text-label-md text-on-surface font-semibold truncate">{p.company}</span>
      </div>
      <div className="flex items-center justify-between">
        <span className="font-body-sm text-body-sm text-outline truncate">{p.name}</span>
        <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full ${scoreBg}`}>{score}</span>
      </div>
    </div>
  );
}

function CampaignCard({ c }: { c: Campaign }) {
  return (
    <div className="flex items-center justify-between p-3 bg-white rounded-xl border border-outline-variant/30 shadow-sm">
      <div className="flex items-center gap-2.5">
        <div className="w-7 h-7 rounded-md bg-primary-fixed/40 flex items-center justify-center font-label-sm text-label-sm font-bold text-on-surface">
          {abbr(c.name)}
        </div>
        <div>
          <div className="font-label-md text-label-md text-on-surface font-semibold">{c.name}</div>
          {c.description && <div className="font-body-sm text-body-sm text-outline truncate max-w-48">{c.description}</div>}
        </div>
      </div>
      <div className="flex items-center gap-2">
        {c.enabled_channels?.map(ch => (
          <span key={ch} className="text-[10px] px-1.5 py-0.5 bg-surface-container rounded-full text-outline">{ch}</span>
        ))}
        <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${c.status === 'ACTIVE' ? 'bg-tertiary-fixed/40 text-tertiary' : 'bg-surface-container text-outline'}`}>
          {c.status}
        </span>
      </div>
    </div>
  );
}

function OutreachCard({ m }: { m: OutreachMsg }) {
  return (
    <div className="p-3 bg-white rounded-xl border border-outline-variant/30 shadow-sm">
      <div className="flex items-center justify-between mb-1.5">
        <span className="font-label-sm text-label-sm text-on-surface font-semibold">{m.recipient}</span>
        <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-full ${m.status === 'SENT' ? 'bg-tertiary-fixed/40 text-tertiary' : 'bg-surface-container text-outline'}`}>
          {m.status} · {m.provider}
        </span>
      </div>
      {m.subject && <div className="font-body-sm text-body-sm text-outline italic mb-1.5">{m.subject}</div>}
      <div className="text-[11px] text-on-surface-variant bg-surface-container rounded-lg px-2.5 py-2 font-mono leading-relaxed line-clamp-3">
        {m.content}
      </div>
    </div>
  );
}

// ─── Bot message renderer ─────────────────────────────────────────────────────
function BotMessage({ content, ts }: { content: BotContent; ts: Date }) {
  if (content.kind === 'loading') {
    return (
      <div className="flex items-center gap-2 px-4 py-3 bg-white rounded-2xl rounded-tl-sm border border-outline-variant/30 shadow-sm w-fit">
        <span className="w-1.5 h-1.5 rounded-full bg-primary-container animate-bounce [animation-delay:0ms]" />
        <span className="w-1.5 h-1.5 rounded-full bg-primary-container animate-bounce [animation-delay:150ms]" />
        <span className="w-1.5 h-1.5 rounded-full bg-primary-container animate-bounce [animation-delay:300ms]" />
        <span className="font-body-sm text-body-sm text-outline ml-1">Querying database…</span>
      </div>
    );
  }

  if (content.kind === 'error') {
    return (
      <div className="px-4 py-3 bg-error-container rounded-2xl rounded-tl-sm border border-error/20 text-error font-body-sm text-body-sm">
        ⚠ {content.text}
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl rounded-tl-sm border border-outline-variant/30 shadow-sm overflow-hidden max-w-2xl w-full">
      {/* Card header */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-outline-variant/20">
        <div className="flex items-center gap-2">
          {content.kind === 'prospects' && (
            <>
              <span className="flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block" /> Overnight Analysis
              </span>
              <span className="text-[11px] text-outline">
                · {content.items.filter(p => p.status === 'REPLIED').length} Replies · {content.items.length} Prospects
              </span>
            </>
          )}
          {content.kind === 'campaigns' && (
            <span className="flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-primary-fixed/30 text-on-surface">
              <span className="material-symbols-outlined text-[13px] text-primary">campaign</span> Live Campaigns
            </span>
          )}
          {content.kind === 'outreach' && (
            <span className="flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-blue-50 text-blue-700">
              <span className="material-symbols-outlined text-[13px]">mail</span> Sent Outreach ({content.items.length})
            </span>
          )}
          {content.kind === 'knowledge' && (
            <span className="flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-amber-50 text-amber-700">
              <span className="material-symbols-outlined text-[13px]">book</span> Knowledge Base
            </span>
          )}
          {content.kind === 'agents' && (
            <span className="flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-surface-container text-on-surface">
              <span className="material-symbols-outlined text-[13px]">smart_toy</span> Agent Results
            </span>
          )}
        </div>
        <span className="font-label-sm text-label-sm text-outline">{tsLabel(ts)}</span>
      </div>

      {/* Card body */}
      <div className="p-3 flex flex-col gap-2">
        {content.kind === 'prospects' && (
          <>
            <div className="grid grid-cols-3 gap-2">
              {content.items.slice(0, 6).map(p => <ProspectCard key={p.id} p={p} />)}
            </div>
            {content.items.length === 0 && (
              <p className="font-body-sm text-body-sm text-outline text-center py-4">No prospects found.</p>
            )}
          </>
        )}

        {content.kind === 'campaigns' && (
          <div className="flex flex-col gap-2">
            {content.items.map(c => <CampaignCard key={c.id} c={c} />)}
            {content.items.length === 0 && (
              <p className="font-body-sm text-body-sm text-outline text-center py-4">No campaigns found.</p>
            )}
          </div>
        )}

        {content.kind === 'outreach' && (
          <div className="flex flex-col gap-2">
            {content.items.slice(0, 5).map((m, i) => <OutreachCard key={i} m={m} />)}
            {content.items.length === 0 && (
              <p className="font-body-sm text-body-sm text-outline text-center py-4">No outreach messages sent yet.</p>
            )}
          </div>
        )}

        {content.kind === 'knowledge' && (
          <div className="flex flex-col gap-2">
            {content.items.map((k, i) => (
              <div key={i} className="p-3 bg-white rounded-xl border border-outline-variant/30 shadow-sm">
                <div className="font-label-md text-label-md text-on-surface font-semibold mb-1">📌 {k.title}</div>
                <div className="text-[11px] text-on-surface-variant bg-surface-container rounded-lg px-2.5 py-2 leading-relaxed">{k.content}</div>
              </div>
            ))}
          </div>
        )}

        {content.kind === 'agents' && (
          <div className="flex flex-col gap-2">
            {content.items.slice(0, 5).map((a, i) => (
              <div key={i} className="flex items-start gap-3 p-3 bg-white rounded-xl border border-outline-variant/30 shadow-sm">
                <span className="text-[11px] font-mono bg-surface-container px-2 py-0.5 rounded-full text-outline flex-shrink-0">{a.agent_type}</span>
                <div className="flex-1 min-w-0">
                  <div className="font-body-sm text-body-sm text-on-surface-variant line-clamp-2">{a.summary}</div>
                </div>
                <span className="text-[11px] font-bold text-primary flex-shrink-0">Score {a.score}</span>
              </div>
            ))}
            {content.items.length === 0 && (
              <p className="font-body-sm text-body-sm text-outline text-center py-4">No agent results found.</p>
            )}
          </div>
        )}
      </div>

      {/* Action suggestion row — only for prospects */}
      {content.kind === 'prospects' && content.items.length > 0 && content.suggestion && (
        <div className="flex items-center justify-between px-4 py-2.5 border-t border-outline-variant/20 bg-surface-container/40">
          <span className="flex items-center gap-1.5 font-body-sm text-body-sm text-on-surface">
            <span className="material-symbols-outlined text-[15px] text-primary-container">bolt</span>
            {content.suggestion}
          </span>
          <div className="flex items-center gap-2">
            <button className="px-3 py-1 rounded-full text-[11px] font-semibold border border-outline-variant text-on-surface hover:bg-surface-container transition-colors">
              Edit
            </button>
            <button className="px-3 py-1 rounded-full text-[11px] font-semibold bg-primary-container text-on-primary-container hover:opacity-90 transition-opacity flex items-center gap-1">
              <span className="material-symbols-outlined text-[13px]">check</span> Confirm Nudges
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────
const TRY_ASKING = [
  { icon: 'lightbulb', label: 'Why did prospects reject me?' },
  { icon: 'call', label: 'What were the top calls today?' },
  { icon: 'person_search', label: 'Show all active prospects' },
  { icon: 'bar_chart', label: 'Show signals with >75 ICP score' },
];

async function resolveQuery(q: string): Promise<BotContent> {
  const lower = q.toLowerCase();

  if (lower.includes('campaign')) {
    const items = await sbGet<Campaign>('campaigns');
    return { kind: 'campaigns', items };
  }

  if (
    lower.includes('prospect') || lower.includes('lead') ||
    lower.includes('reject') || lower.includes('signal') ||
    lower.includes('score') || lower.includes('call') ||
    lower.includes('top') || lower.includes('active')
  ) {
    const items = await sbGet<Prospect>('prospects');
    const filtered = lower.includes('reject')
      ? items.filter(p => p.status === 'REJECTED' || p.status === 'NO_FIT')
      : lower.includes('score') || lower.includes('signal')
      ? items.filter(p => (p.icp_score ?? 0) >= 75)
      : items;
    const suggestion = filtered.length > 0
      ? `Follow up with ${Math.min(filtered.length, 3)} prospects via their preferred channel?`
      : undefined;
    return { kind: 'prospects', items: filtered.length > 0 ? filtered : items, suggestion: suggestion ?? '' };
  }

  if (lower.includes('email') || lower.includes('outreach') || lower.includes('sent') || lower.includes('message')) {
    const items = await sbGet<OutreachMsg>('outreach_messages');
    return { kind: 'outreach', items };
  }

  if (lower.includes('case') || lower.includes('study') || lower.includes('kb') || lower.includes('knowledge') || lower.includes('battlecard')) {
    const items = await sbGet<KBItem>('knowledge_base');
    return { kind: 'knowledge', items };
  }

  // Fallback: agent results
  const items = await sbGet<AgentResult>('agent_results');
  return { kind: 'agents', items };
}

export function NectarIntelligenceDesk() {
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [input, setInput] = useState('');
  const [stats, setStats] = useState({ campaigns: 0, prospects: 0 });
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Load quick stats
  useEffect(() => {
    Promise.all([sbGet<Campaign>('campaigns'), sbGet<Prospect>('prospects')]).then(([c, p]) => {
      setStats({ campaigns: c.length, prospects: p.length });
    });
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const send = useCallback(async (text?: string) => {
    const q = (text ?? input).trim();
    if (!q) return;
    setInput('');

    const userMsg: ChatMsg = { id: uid(), role: 'user', userText: q, ts: new Date() };
    const loadingId = uid();
    const loadingMsg: ChatMsg = { id: loadingId, role: 'bot', content: { kind: 'loading' }, ts: new Date() };
    setMessages(prev => [...prev, userMsg, loadingMsg]);

    try {
      const result = await resolveQuery(q);
      setMessages(prev => prev.map(m => m.id === loadingId ? { ...m, content: result, ts: new Date() } : m));
    } catch (e: any) {
      setMessages(prev => prev.map(m =>
        m.id === loadingId ? { ...m, content: { kind: 'error', text: e.message ?? 'Query failed' } } : m
      ));
    }
  }, [input]);

  return (
    <div className="flex flex-col bg-surface overflow-hidden" style={{ height: '100dvh' }}>
      {/* ── Header ─────────────────────────────────────────────────────── */}
      <div className="flex-shrink-0 px-space-lg py-4 border-b border-outline-variant bg-surface-container-lowest">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-on-surface flex items-center justify-center flex-shrink-0">
              <span className="material-symbols-outlined text-surface text-[20px]">spark</span>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="font-headline-sm text-headline-sm text-on-surface">Nectar Intelligence Desk</h1>
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full border border-outline-variant text-outline">v2.4 Core</span>
              </div>
              <p className="font-body-sm text-body-sm text-outline">
                Synthesized live across {stats.campaigns} active campaigns &amp; {stats.prospects} prospects in pipeline
              </p>
            </div>
          </div>
          <span className="flex items-center gap-1.5 font-label-sm text-label-sm text-outline border border-outline-variant rounded-full px-3 py-1">
            <span className="material-symbols-outlined text-[14px]">verified_user</span>
            All data local to workspace
          </span>
        </div>

        {/* Try asking chips */}
        <div className="flex items-center gap-2 mt-3 flex-wrap">
          <span className="font-label-sm text-label-sm text-outline uppercase tracking-wider text-[10px]">Try asking:</span>
          {TRY_ASKING.map(chip => (
            <button
              key={chip.label}
              onClick={() => send(chip.label)}
              className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-surface-container-lowest border border-outline-variant text-on-surface-variant font-label-sm text-label-sm hover:bg-primary-fixed/20 hover:border-primary/30 transition-colors shadow-sm"
            >
              <span className="material-symbols-outlined text-[14px] text-outline">{chip.icon}</span>
              {chip.label}
            </button>
          ))}
        </div>
      </div>

      {/* ── Message stream ──────────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto px-space-lg py-space-md flex flex-col gap-space-lg" style={{ minHeight: 0 }}>
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full gap-4 select-none">
            <div className="w-16 h-16 rounded-2xl bg-surface-container-lowest border border-outline-variant shadow-sm flex items-center justify-center">
              <span className="material-symbols-outlined text-[32px] text-outline">chat_bubble_outline</span>
            </div>
            <div className="text-center">
              <h3 className="font-headline-sm text-headline-sm text-on-surface">Ask me anything</h3>
              <p className="font-body-md text-body-md text-on-surface-variant mt-1 max-w-sm">
                I have live access to your backend pipeline — prospects, campaigns, outreach messages, and case studies.
              </p>
            </div>
          </div>
        )}

        {messages.map(msg => (
          <div key={msg.id} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
            {/* Avatar */}
            <div className={`w-8 h-8 rounded-full flex items-center justify-center font-label-md text-label-md font-bold flex-shrink-0 mt-0.5 shadow-sm ${
              msg.role === 'user'
                ? 'bg-on-surface text-surface'
                : 'bg-primary-container text-on-primary-container'
            }`}>
              {msg.role === 'user'
                ? 'PK'
                : <span className="material-symbols-outlined text-[16px]">spark</span>
              }
            </div>

            {/* Bubble */}
            {msg.role === 'user' ? (
              <div className="max-w-lg px-4 py-2.5 bg-surface-container-lowest border border-outline-variant rounded-2xl rounded-tr-sm shadow-sm font-body-md text-body-md text-on-surface">
                {msg.userText}
              </div>
            ) : (
              <div className="flex-1 min-w-0">
                {msg.content && <BotMessage content={msg.content} ts={msg.ts} />}
              </div>
            )}
          </div>
        ))}

        <div ref={bottomRef} />
      </div>

      {/* ── Bottom input dock ───────────────────────────────────────────── */}
      <div className="flex-shrink-0 border-t border-outline-variant bg-surface-container-lowest px-space-lg py-3">
        <div className="flex items-center gap-3 bg-white rounded-2xl border border-outline-variant shadow-sm px-4 py-2.5">
          {/* Left: logo area */}
          <div className="flex items-center gap-2 flex-shrink-0">
            <span className="material-symbols-outlined text-[18px] text-outline">search</span>
            <span className="font-label-sm text-label-sm text-outline/60 font-mono tracking-tight hidden sm:block">_RK</span>
          </div>

          <div className="w-px h-4 bg-outline-variant flex-shrink-0" />

          {/* Input */}
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && send()}
            placeholder="Ask anything across leads, transcripts, objections, and logs..."
            className="flex-1 bg-transparent font-body-md text-body-md text-on-surface placeholder:text-outline focus:outline-none"
          />

          {/* Right: action buttons */}
          <div className="flex items-center gap-2 flex-shrink-0">
            <button className="w-8 h-8 rounded-full flex items-center justify-center text-outline hover:bg-surface-container transition-colors" title="Voice input">
              <span className="material-symbols-outlined text-[18px]">mic</span>
            </button>
            <button className="w-8 h-8 rounded-full flex items-center justify-center text-outline hover:bg-surface-container transition-colors" title="Attach file">
              <span className="material-symbols-outlined text-[18px]">attach_file</span>
            </button>
            <button
              onClick={() => send()}
              disabled={!input.trim()}
              className="w-9 h-9 rounded-full bg-primary-container text-on-primary-container hover:opacity-90 flex items-center justify-center shadow-sm transition-all active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <span className="material-symbols-outlined text-[18px]">arrow_upward</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
