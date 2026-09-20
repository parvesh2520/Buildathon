import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getProspects, updateProspectStatus } from '@/api/prospects';
import { Prospect } from '@/types';

type EscalationCard = {
  id: string;
  initials: string;
  name: string;
  meta: string;
  tag: string;
  tagTone: 'green' | 'amber' | 'neutral';
  quote: string;
  primary: string;
  secondary?: string;
  live?: boolean;
  prospect?: Prospect;
};

const starterPrompts = ['Show live prospects', 'Who needs review?', 'Which prospects were contacted?'];

const hourBars = ['8a', '9a', '10a', '11a', '12p', '1p', '2p', '3p', '4p', '5p'].map((label) => ({
  label,
  height: '8%',
  tone: 'quiet',
}));

export function Dashboard() {
  const navigate = useNavigate();
  const [prospects, setProspects] = useState<Prospect[]>([]);
  const [assistantInput, setAssistantInput] = useState('');
  const [actioningId, setActioningId] = useState<string | null>(null);
  const [escalationTab, setEscalationTab] = useState('All');

  useEffect(() => {
    getProspects().then(setProspects).catch(() => {});
  }, []);

  const stats = useMemo(() => {
    const voiceCalls = prospects.filter((p) => p.channel === 'PHONE').length;
    const contacted = prospects.filter((p) => p.status === 'SENT' || p.status === 'CONTACTED').length;
    const rejected = prospects.filter((p) => p.status === 'REJECTED' || p.status === 'NO_FIT').length;
    const needsReview = prospects.filter((p) => p.status === 'REPLIED' || p.status === 'REVIEW').length;

    return {
      voiceCalls,
      touches: contacted,
      politeNos: rejected,
      needsReview,
    };
  }, [prospects]);

  const liveCampaignCount = useMemo(
    () => new Set(prospects.map((p) => p.campaign_id || p.campaignId).filter(Boolean)).size,
    [prospects]
  );

  const liveEscalations = prospects
    .filter((p) => p.status === 'REPLIED' || p.status === 'REVIEW')
    .slice(0, 4)
    .map<EscalationCard>((p) => ({
      id: p.id,
      initials: p.name.split(' ').map((part) => part[0]).join('').slice(0, 2).toUpperCase(),
      name: p.name,
      meta: `${p.title || 'Prospect'} - ${p.company || 'Company'}`,
      tag: p.status === 'REPLIED' ? 'Replied' : 'Review',
      tagTone: 'amber',
      quote: p.notes || 'Needs human review before the next outbound touch.',
      primary: 'Approve & Book Meeting',
      secondary: 'Mark Handled',
      prospect: p,
    }));

  const escalations = useMemo(() => {
    if (escalationTab === 'All') return liveEscalations;
    return liveEscalations.filter((item) => item.tag.toLowerCase() === escalationTab.toLowerCase());
  }, [liveEscalations, escalationTab]);

  const handleEscalationAction = async (item: EscalationCard, status: string) => {
    if (!item.prospect) return;
    setActioningId(item.id);
    try {
      const updated = await updateProspectStatus(item.prospect.id, status);
      setProspects((prev) => prev.map((p) => (p.id === updated.id ? updated : p)));
    } finally {
      setActioningId(null);
    }
  };

  return (
    <div className="min-h-screen w-full bg-[#fbf6ec] px-7 py-6 text-[#27231d]">
      <div className="mx-auto flex max-w-[1160px] flex-col gap-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-sm text-[#756c5f]">
            <span>Home</span>
            <span className="material-symbols-outlined text-[15px]">chevron_right</span>
            <span className="font-semibold text-[#2b261f]">Dashboard</span>
            <span className="ml-1 rounded-full bg-[#edf4f0] px-3 py-1 text-xs font-bold text-[#366853]">
              {prospects.length} live prospects
            </span>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/campaigns')}
              className="flex items-center gap-2 rounded-full bg-white px-4 py-2 text-sm font-semibold text-[#2f2a23] shadow-sm hover:bg-[#faf5ee] transition-colors"
            >
              <span className="h-2.5 w-2.5 rounded-full bg-[#366853]" />
              {liveCampaignCount} campaigns active
              <span className="material-symbols-outlined text-[16px] text-[#9b907f]">arrow_forward</span>
            </button>
          </div>
        </div>

        <section>
          <h1 className="font-serif text-[34px] font-bold leading-tight tracking-normal text-[#201d19]">
            Good morning, Ramya.
          </h1>
          <p className="mt-2 max-w-3xl text-[15px] leading-6 text-[#51483d]">
            Ask anything, review escalations, or let the pipeline run quietly in the background. Every touch honors your
            calibrated rules.
          </p>
        </section>

        <section className="rounded-[18px] border border-[#e7ba4a] bg-[#fff7e8] p-6 shadow-[0_18px_40px_rgba(150,103,16,0.12)]">
          <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[#2f2b25]">
                <span className="material-symbols-outlined text-[27px] text-[#f2c15d]">auto_awesome</span>
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="font-serif text-lg font-bold">Your Assistant</h2>
                  <span className="rounded-full bg-[#e6a219] px-2 py-0.5 text-[10px] font-bold uppercase text-[#2a2110]">
                    v2.4 Core
                  </span>
                </div>
                <p className="text-sm text-[#5d5245]">
                  Synthesized live across {liveCampaignCount} active campaigns and {prospects.length} backend prospects
                </p>
              </div>
            </div>
            <span className="rounded-full bg-white px-4 py-2 text-xs font-bold text-[#366853] shadow-sm">
              Live Knowledge Graph Active
            </span>
          </div>

          <div className="flex items-center gap-3 rounded-2xl border border-[#d7c8b0] bg-white px-4 py-3 shadow-[0_10px_25px_rgba(55,43,23,0.1)]">
            <span className="material-symbols-outlined text-[22px] text-[#8a6718]">search</span>
            <span className="font-serif text-2xl tracking-[0.08em] text-[#8a6718]">ORK</span>
            <input
              value={assistantInput}
              onChange={(event) => setAssistantInput(event.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && assistantInput.trim()) {
                  navigate(`/chatbot?q=${encodeURIComponent(assistantInput.trim())}`);
                }
              }}
              className="min-w-0 flex-1 bg-transparent text-sm outline-none placeholder:text-[#8b8174]"
              placeholder="Ask anything across leads, transcripts, objections, and call logs..."
            />
            <button
              onClick={() => {
                if (assistantInput.trim()) {
                  navigate(`/chatbot?q=${encodeURIComponent(assistantInput.trim())}`);
                }
              }}
              className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#e6a219] text-[#2a2110] shadow-sm hover:bg-[#d69213] transition-colors"
              title="Search with AI Assistant"
            >
              <span className="material-symbols-outlined text-[22px]">arrow_upward</span>
            </button>
          </div>

          <div className="mt-4 flex flex-wrap items-center gap-2">
            <span className="mr-1 text-xs font-bold uppercase text-[#7c7162]">Starter prompts:</span>
            {starterPrompts.map((chip) => (
              <button
                key={chip}
                onClick={() => setAssistantInput(chip)}
                className="rounded-full bg-white px-3 py-1.5 text-xs font-semibold text-[#51483d] shadow-sm"
              >
                {chip}
              </button>
            ))}
          </div>
        </section>

        <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_360px]">
          <main className="flex flex-col gap-5">
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              {[
                { label: 'Voice Calls', value: stats.voiceCalls, sub: 'Phone channel prospects', active: false },
                { label: 'Touches', value: stats.touches, sub: 'Contacted prospects', active: false },
                { label: "Polite No's", value: stats.politeNos, sub: 'Rejected or no-fit', active: false },
                { label: 'Needs Ramya', value: stats.needsReview, sub: 'Escalated threads', active: true },
              ].map((metric) => (
                <section
                  key={metric.label}
                  className={`rounded-2xl border p-5 shadow-sm ${
                    metric.active ? 'border-[#e6a219] bg-[#fff2cc]' : 'border-[#ebe1d1] bg-white'
                  }`}
                >
                  <div className="text-[11px] font-bold uppercase tracking-wide text-[#7c7162]">{metric.label}</div>
                  <div className="mt-2 font-serif text-[44px] font-bold leading-none text-[#201d19]">{metric.value}</div>
                  <div className="mt-3 flex items-center gap-1 text-xs font-semibold text-[#675c4f]">
                    <span className="material-symbols-outlined text-[15px] text-[#8a6718]">
                      {metric.active ? 'flag' : 'trending_up'}
                    </span>
                    {metric.sub}
                  </div>
                </section>
              ))}
            </div>

            <section className="rounded-2xl border border-[#ebe1d1] bg-white p-6 shadow-sm">
              <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h2 className="font-serif text-xl font-bold text-[#201d19]">Best hours to land replies</h2>
                  <p className="mt-1 text-sm text-[#6f6457]">No historical touch-time data connected yet</p>
                </div>
                <span className="rounded-full bg-[#edf4f0] px-3 py-1 text-xs font-bold text-[#366853]">
                  Waiting for live activity
                </span>
              </div>

              <div className="flex h-52 items-end gap-3 px-2">
                {hourBars.map((hour) => (
                  <div key={hour.label} className="flex h-full flex-1 flex-col items-center justify-end gap-2">
                    <div
                      className={`w-full max-w-[42px] rounded-t-lg ${
                        hour.tone === 'dark' ? 'bg-[#8a6718]' : hour.tone === 'gold' ? 'bg-[#e6a219]' : 'bg-[#eee8df]'
                      }`}
                      style={{ height: hour.height }}
                    />
                    <span className="text-xs font-semibold text-[#7c7162]">{hour.label}</span>
                  </div>
                ))}
              </div>

              <div className="mt-4 flex flex-wrap items-center justify-between gap-2 rounded-xl bg-[#f7f1e8] px-4 py-3 text-xs text-[#5a5147]">
                <span className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full bg-[#8a6718]" />
                  Connect outreach event timestamps to populate reply-hour analysis
                </span>
                <span className="font-bold text-[#366853]">{stats.touches} contacted</span>
              </div>
            </section>
          </main>

          <aside className="flex flex-col gap-4">
            <section className="rounded-[18px] border border-[#d99c22] bg-[#2f2d28] p-5 text-white shadow-[0_16px_35px_rgba(36,31,24,0.22)]">
              <div className="mb-4 flex items-start justify-between gap-3">
                <div>
                  <div className="mb-1 flex items-center gap-2">
                    <span className="h-3 w-3 rounded-full bg-[#e6a219]" />
                    <h2 className="font-serif text-xl font-bold leading-tight">Escalations Pending Human Action</h2>
                  </div>
                  <p className="text-xs leading-5 text-[#d7d0c6]">
                    Agents safely freeze outbounds whenever money, contracts, or high-intent warm objections occur.
                  </p>
                </div>
                <span className="rounded-full bg-[#e6a219] px-3 py-2 text-center text-[10px] font-bold uppercase leading-tight text-[#2a2110]">
                  {stats.needsReview}
                  <br />
                  require you
                </span>
              </div>

              <div className="mb-4 flex gap-2 overflow-x-auto">
                {['All', 'Replied', 'Review'].map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setEscalationTab(tab)}
                    className={`shrink-0 rounded-full px-3 py-1 text-xs font-bold transition-colors ${
                      escalationTab === tab ? 'bg-white text-[#2f2d28]' : 'bg-white/12 text-[#f1eadf] hover:bg-white/20'
                    }`}
                  >
                    {tab === 'All' ? `All (${stats.needsReview})` : tab}
                  </button>
                ))}
              </div>

              <div className="flex flex-col gap-3">
                {escalations.map((item) => (
                  <div key={item.id} className="rounded-2xl border border-white/10 bg-white/14 p-3">
                    {item.live && (
                      <div className="mb-2 flex items-center justify-between text-[10px] font-bold uppercase tracking-wide text-[#ff4d42]">
                        <span className="flex items-center gap-1.5">
                          <span className="h-2 w-2 rounded-full bg-[#ff4d42]" />
                          Live call - 04:31
                        </span>
                        <span className="material-symbols-outlined text-[16px]">equalizer</span>
                      </div>
                    )}
                    <div className="mb-2 flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#f1eadf] text-xs font-bold text-[#2f2d28]">
                          {item.initials}
                        </div>
                        <div>
                          <div className="text-sm font-bold">{item.name}</div>
                          <div className="text-[11px] text-[#d7d0c6]">{item.meta}</div>
                        </div>
                      </div>
                      <span
                        className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${
                          item.tagTone === 'green'
                            ? 'bg-[#b7f0d9] text-[#1f5e48]'
                            : item.tagTone === 'amber'
                            ? 'bg-[#e6a219] text-[#2a2110]'
                            : 'bg-white/25 text-white'
                        }`}
                      >
                        {item.tag}
                      </span>
                    </div>
                    <div className="mb-3 rounded-lg bg-white/16 px-3 py-2 text-xs italic text-[#f1eadf]">"{item.quote}"</div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleEscalationAction(item, 'MEETING')}
                        disabled={actioningId === item.id}
                        className="flex-1 rounded-full bg-[#e6a219] px-3 py-2 text-xs font-bold text-[#2a2110] disabled:opacity-60"
                      >
                        {actioningId === item.id ? 'Saving...' : item.primary}
                      </button>
                      {item.secondary && (
                        <button
                          onClick={() => handleEscalationAction(item, 'CONTACTED')}
                          disabled={actioningId === item.id}
                          className="rounded-full bg-white/22 px-3 py-2 text-xs font-bold text-white disabled:opacity-60"
                        >
                          {item.secondary}
                        </button>
                      )}
                    </div>
                  </div>
                ))}
                {escalations.length === 0 && (
                  <div className="rounded-2xl border border-white/10 bg-white/14 p-4 text-sm text-[#f1eadf]">
                    No prospects currently need human action.
                  </div>
                )}
              </div>
            </section>

            <section className="rounded-2xl border border-[#e7ba4a] bg-[#fff7e8] p-5">
              <div className="flex items-start gap-3">
                <span className="material-symbols-outlined text-[22px] text-[#8a6718]">verified_user</span>
                <div>
                  <h3 className="font-serif text-base font-bold text-[#2a2110]">Strict Human-in-the-Loop Active</h3>
                  <p className="mt-1 text-xs leading-5 text-[#5d5245]">
                    Zero automated messages are dispatched when negative sentiment or legal inquiries are identified.
                    You remain in control of all contract boundaries.
                  </p>
                </div>
              </div>
            </section>
          </aside>
        </div>
      </div>
    </div>
  );
}
