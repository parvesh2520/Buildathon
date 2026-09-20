import React, { useState, useEffect, useRef } from 'react';
import { getCampaigns } from '@/api/campaigns';
import { getProspects } from '@/api/prospects';
import { getAgents, getExecutions } from '@/api/sdr';
import { getRAGDocuments } from '@/api/system';
import { formatAgentText } from '@/lib/utils';

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

export const SdrCopilotOverlay: React.FC = () => {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      isUser: false,
      text: `Hi! I'm your <strong>SDR Operations Copilot</strong>. I query the backend API for campaign data and playbooks.<br><br>Ask me anything about the pipeline, prospects, sent emails, or battlecards!`
    }
  ]);
  const [input, setInput] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function queryDB<T>(table: string): Promise<T[]> {
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
    } catch (e) {
      console.error(`Error querying backend ${table}:`, e);
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
        lower.includes('rajesh')
      ) {
        const prospects = await queryDB<Prospect>('prospects');
        botReply = `<strong>Discovered Prospects (${prospects.length}):</strong>
          <div class="mt-2 overflow-x-auto">
            <table class="w-full text-xs text-left border border-slate-700">
              <tr class="bg-slate-800 text-slate-300">
                <th class="p-2">Name</th>
                <th class="p-2">Title</th>
                <th class="p-2">Company</th>
                <th class="p-2">Score</th>
                <th class="p-2">Status</th>
              </tr>
              ${prospects
                .map(
                  p => `<tr class="border-t border-slate-700">
                    <td class="p-2 font-bold">${p.name}</td>
                    <td class="p-2">${p.title}</td>
                    <td class="p-2">${p.company}</td>
                    <td class="p-2 font-bold text-cyan-400">${p.icp_score ?? 'N/A'}</td>
                    <td class="p-2 font-bold ${
                      p.status === 'CONTACTED' ? 'text-emerald-400' : 'text-rose-400'
                    }">${p.status}</td>
                  </tr>`
                )
                .join('')}
            </table>
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
      } else if (lower.includes('case') || lower.includes('study') || lower.includes('kb')) {
        const kb = await queryDB<KnowledgeBaseItem>('knowledge_base');
        botReply = `<strong>Knowledge Base Case Studies:</strong><br/>
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
        botReply = `<strong>Agent Execution Analysis:</strong><br>Found ${results.length} agent telemetry records from the backend.<br/><br/>
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
                <p className="text-[10px] text-slate-400">Live Backend API RAG</p>
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
                    ? 'ml-auto bg-emerald-600 text-white rounded-br-xs'
                    : 'mr-auto bg-slate-900 border border-slate-800 text-slate-200 rounded-bl-xs'
                }`}
                dangerouslySetInnerHTML={{ __html: m.text }}
              />
            ))}
            {loading && (
              <div className="mr-auto bg-slate-900 border border-slate-800 text-slate-400 p-2.5 rounded-xl text-xs flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-bounce"></span>
                <span>Querying backend...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Filter Chips */}
          <div className="px-4 py-2 bg-slate-900/40 border-t border-slate-800/60 flex flex-wrap gap-1.5">
            {[
              'Show all campaigns',
              'Show qualified prospects',
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
              className="flex-1 bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500 placeholder:text-slate-500"
            />
            <button
              onClick={() => handleSend()}
              className="bg-emerald-500 hover:bg-emerald-600 text-white px-3.5 py-2 rounded-xl text-xs font-semibold cursor-pointer transition"
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
