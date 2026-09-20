import React, { useState, useEffect, useRef } from 'react';

const SUPABASE_URL = (import.meta.env.VITE_SUPABASE_URL || 'https://ueostzaevpteuxdmxnww.supabase.co/rest/v1/').replace(/\/+$/, '') + '/';
const SUPABASE_KEY = import.meta.env.VITE_SUPABASE_KEY || 'sb_publishable_w-qzzDRNu57d5YZ3EQ9NNw_d19zjgeW';

interface Message {
  isUser: boolean;
  text: string;
}

interface Campaign {
  id: string;
  name: string;
  status: string;
  enabled_channels?: string[];
  description?: string;
}

interface Prospect {
  id: string;
  name: string;
  title: string;
  company: string;
  icp_score: number | null;
  status: string;
}

interface OutreachMessage {
  recipient: string;
  subject: string;
  status: string;
  provider: string;
  content: string;
}

interface KnowledgeBaseItem {
  title: string;
  campaign_id: string;
  content: string;
}

interface AgentResult {
  agent_type: string;
  score: number;
  summary: string;
}

const FALLBACK_CASE_STUDIES: KnowledgeBaseItem[] = [
  {
    title: 'FinTech Cloud Infrastructure Playbook',
    campaign_id: 'US Enterprise Cloud',
    content: 'Led zero-trust architecture transition reducing latency by 42% and eliminating $1.2M annual compliance penalties.'
  },
  {
    title: 'Healthcare SaaS Security Grounding',
    campaign_id: 'Global B2B Security',
    content: 'HIPAA-grade multi-tenant automation playbook featuring sub-120ms webhook dispatch and cryptographically audited event logs.'
  }
];

export const SdrCopilotOverlay: React.FC = () => {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      isUser: false,
      text: `👋 Hi! I'm your <strong>SDR Operations Copilot</strong>. I have direct access to our Supabase database and campaign playbooks.<br><br>Ask me anything about our pipeline, prospects, sent emails, or battlecards!`
    }
  ]);
  const [input, setInput] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isOpen]);

  // Listen for global custom events to open copilot and ask queries (e.g. from Dashboard assistant)
  useEffect(() => {
    const handleOpenCopilot = (event: Event) => {
      const customEvent = event as CustomEvent<{ query?: string }>;
      setIsOpen(true);
      if (customEvent.detail?.query) {
        handleSend(customEvent.detail.query);
      }
    };

    window.addEventListener('open-sdr-copilot', handleOpenCopilot);
    return () => window.removeEventListener('open-sdr-copilot', handleOpenCopilot);
  }, []);

  async function queryDB<T>(table: string): Promise<T[]> {
    try {
      const resp = await fetch(`${SUPABASE_URL}${table}?select=*`, {
        headers: {
          apikey: SUPABASE_KEY,
          Authorization: `Bearer ${SUPABASE_KEY}`
        }
      });
      const data = await resp.json();
      return Array.isArray(data) ? (data as T[]) : [];
    } catch (e) {
      console.error(`Error querying ${table}:`, e);
      return [];
    }
  }

  async function handleSend(queryText?: string): Promise<void> {
    const q = (queryText || input).trim();
    if (!q) return;

    const userMsg: Message = { isUser: true, text: q };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    const lower = q.toLowerCase();
    let botReply = '';

    try {
      if (lower.includes('campaign')) {
        const campaigns = await queryDB<Campaign>('campaigns');
        botReply = `<strong>Live Campaigns (${campaigns.length}):</strong>
          <div class="mt-2 overflow-x-auto">
            <table class="w-full text-xs text-left border border-slate-700">
              <tr class="bg-slate-800 text-slate-300">
                <th class="p-2">Name</th>
                <th class="p-2">Status</th>
                <th class="p-2">Channels</th>
              </tr>
              ${campaigns
                .map(
                  c => `<tr class="border-t border-slate-700">
                    <td class="p-2 font-bold">${c.name}</td>
                    <td class="p-2 text-emerald-400">${c.status}</td>
                    <td class="p-2">${c.enabled_channels ? c.enabled_channels.join(', ') : 'EMAIL'}</td>
                  </tr>`
                )
                .join('')}
            </table>
          </div>`;
      } else if (
        lower.includes('prospect') ||
        lower.includes('lead') ||
        lower.includes('parvesh') ||
        lower.includes('rajesh') ||
        lower.includes('review') ||
        lower.includes('contacted') ||
        lower.includes('who')
      ) {
        let prospects = await queryDB<Prospect>('prospects');
        let filterTitle = `Discovered Prospects (${prospects.length}):`;

        if (lower.includes('review') || lower.includes('replied')) {
          prospects = prospects.filter(p => p.status === 'REVIEW' || p.status === 'REPLIED');
          filterTitle = `Prospects Pending Review / Replied (${prospects.length}):`;
        } else if (lower.includes('contacted') || lower.includes('sent')) {
          prospects = prospects.filter(p => p.status === 'CONTACTED' || p.status === 'SENT');
          filterTitle = `Contacted Prospects (${prospects.length}):`;
        } else if (lower.includes('qualified') || lower.includes('top') || lower.includes('fit')) {
          prospects = prospects.filter(p => (p.icp_score ?? 0) >= 60);
          filterTitle = `Top Qualified Prospects (${prospects.length}):`;
        }

        botReply = `<strong>${filterTitle}</strong>
          <div class="mt-2 overflow-x-auto">
            <table class="w-full text-xs text-left border border-slate-700">
              <tr class="bg-slate-800 text-slate-300">
                <th class="p-2">Name</th>
                <th class="p-2">Title</th>
                <th class="p-2">Company</th>
                <th class="p-2">Score</th>
                <th class="p-2">Status</th>
              </tr>
              ${prospects.slice(0, 15)
                .map(
                  p => `<tr class="border-t border-slate-700">
                    <td class="p-2 font-bold">${p.name}</td>
                    <td class="p-2">${p.title || 'Prospect'}</td>
                    <td class="p-2">${p.company || 'Company'}</td>
                    <td class="p-2 font-bold text-cyan-400">${p.icp_score ?? 'N/A'}</td>
                    <td class="p-2 font-bold ${
                      p.status === 'CONTACTED' || p.status === 'SENT' ? 'text-emerald-400' : p.status === 'REVIEW' ? 'text-amber-400' : 'text-slate-300'
                    }">${p.status}</td>
                  </tr>`
                )
                .join('')}
            </table>
            ${prospects.length > 15 ? `<div class="p-1 text-[11px] text-slate-400">...and ${prospects.length - 15} more in database</div>` : ''}
          </div>`;
      } else if (lower.includes('email') || lower.includes('outreach') || lower.includes('sent')) {
        const msgs = await queryDB<OutreachMessage>('outreach_messages');
        botReply = `<strong>Sent Outreach Messages (${msgs.length}):</strong><br/>
          ${msgs
            .map(
              m => `<div class="mt-2 p-2.5 bg-slate-900 border border-slate-700 rounded-lg text-xs">
                <strong>To:</strong> ${m.recipient}<br/>
                <strong>Subject:</strong> <em>${m.subject}</em><br/>
                <strong>Status:</strong> <span class="text-emerald-400 font-semibold">${m.status}</span> via ${m.provider}
                <div class="mt-1.5 p-2 bg-slate-950 border-l-2 border-emerald-500 text-slate-300 whitespace-pre-wrap font-mono text-[11px]">${m.content}</div>
              </div>`
            )
            .join('')}`;
      } else if (lower.includes('case') || lower.includes('study') || lower.includes('kb') || lower.includes('battlecard')) {
        let kb = await queryDB<KnowledgeBaseItem>('knowledge_base');
        if (kb.length === 0) {
          kb = FALLBACK_CASE_STUDIES;
        }
        botReply = `<strong>Knowledge Base & Case Studies (${kb.length}):</strong><br/>
          ${kb
            .map(
              k => `<div class="mt-2 p-2 bg-slate-900 border border-slate-700 rounded-lg text-xs">
                <strong class="text-emerald-400 font-semibold">${k.title}</strong> (${k.campaign_id})
                <div class="text-slate-300 mt-1">${k.content}</div>
              </div>`
            )
            .join('')}`;
      } else {
        const results = await queryDB<AgentResult>('agent_results');
        botReply = `<strong>Agent Execution Analysis:</strong><br>Found ${results.length} qualification records in Supabase.<br/><br/>
          ${
            results.length > 0
              ? `Latest: <code>${results[0].agent_type}</code> | Score: <strong>${results[0].score}</strong><br/>${results[0].summary}`
              : 'No execution traces found.'
          }`;
      }
    } catch (e: unknown) {
      const err = e as Error;
      botReply = `⚠️ Error querying database: ${err.message}`;
    }

    setMessages(prev => [...prev, { isUser: false, text: botReply }]);
    setLoading(false);
  }

  return (
    <div className="fixed bottom-6 right-6 z-[999999] font-sans">
      {/* Floating Action Button (FAB) */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Toggle SDR Copilot"
        title="Open SDR Copilot AI"
        className="w-14 h-14 rounded-full bg-emerald-500 hover:bg-emerald-600 text-white shadow-xl shadow-emerald-500/30 flex items-center justify-center transition-all hover:scale-105 active:scale-95 cursor-pointer"
      >
        <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
          />
        </svg>
      </button>

      {/* Slide-out Chat Panel */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 w-96 max-w-[calc(100vw-3rem)] h-[580px] max-h-[calc(100vh-8rem)] bg-slate-950 border border-slate-800 rounded-2xl shadow-2xl flex flex-col overflow-hidden animate-in fade-in slide-in-from-bottom-5 duration-200">
          {/* Header */}
          <div className="p-4 bg-slate-900 border-b border-slate-800 flex justify-between items-center">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
              <div>
                <h3 className="font-bold text-sm text-slate-100">SDR Copilot AI</h3>
                <p className="text-[10px] text-slate-400">Live Supabase Database RAG</p>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="text-slate-400 hover:text-white text-lg cursor-pointer p-1"
            >
              ✕
            </button>
          </div>

          {/* Message Stream */}
          <div className="flex-1 p-4 overflow-y-auto space-y-3 text-xs">
            {messages.map((m, idx) => (
              <div
                key={idx}
                className={`p-3 rounded-xl max-w-[88%] leading-relaxed ${
                  m.isUser
                    ? 'ml-auto bg-emerald-600 text-white rounded-br-sm'
                    : 'mr-auto bg-slate-900 border border-slate-800 text-slate-200 rounded-bl-sm'
                }`}
                dangerouslySetInnerHTML={{ __html: m.text }}
              />
            ))}
            {loading && (
              <div className="mr-auto bg-slate-900 border border-slate-800 text-slate-400 p-2.5 rounded-xl text-xs flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-bounce"></span>
                <span>Querying Supabase...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Filter Chips */}
          <div className="px-4 py-2 bg-slate-900/40 border-t border-slate-800/60 flex flex-wrap gap-1.5">
            {[
              'Show all campaigns',
              'Show qualified prospects',
              'Who needs review?',
              'What emails were sent?',
              'Show case studies'
            ].map((chip, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(chip)}
                className="text-[11px] px-2.5 py-1 bg-slate-900 hover:bg-emerald-500 hover:text-white border border-slate-700 text-slate-300 rounded-lg transition cursor-pointer"
              >
                {chip}
              </button>
            ))}
          </div>

          {/* Input Bar */}
          <div className="p-3 bg-slate-900 border-t border-slate-800 flex gap-2">
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSend()}
              placeholder="Ask about prospects, campaigns, emails..."
              className="min-w-0 flex-1 bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500 placeholder:text-slate-500"
            />
            <button
              onClick={() => handleSend()}
              className="bg-emerald-500 hover:bg-emerald-600 text-white px-3.5 py-2 rounded-xl text-xs font-semibold cursor-pointer transition shrink-0"
            >
              Send
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default SdrCopilotOverlay;
