import { useEffect, useState } from 'react';
import { getOperationalControls, toggleKillSwitch, toggleAgentPause } from '@/api/system';
import { OperationalControls } from '@/types';

const agentCards = [
  {
    id: '0',
    title: 'Sourcing Scout',
    badge: '99.4% Dedup Acc.',
    sections: [
      { label: 'Target Roles', chips: ['CTO', 'VP Eng', 'Head of Platform', '+ Role'] },
      { label: 'Tech Stack Signals', chips: ['Cloud Native', 'K8s', 'Go / Rust', 'Bazel'] },
    ],
    panels: ['Geo-fence: US & Canada Only', 'Exclude Competitors: 18 Locked Brands'],
    footer: '150 Target / day',
  },
  {
    id: '1',
    title: 'Deep Research & TTL',
    badge: 'Evidence Gate ≥ 0.85',
    sections: [
      { label: 'Signal Recency TTLs', chips: ['LinkedIn 30d', 'Hiring 90d', 'Tech Stack 180d', 'Funding 365d'] },
      { label: '6-Pillar Intelligence Mesh', chips: ['1. Company Signals', '2. Leadership Moves', '3. Casual Engine', '4. Trigger Classify', '5. CRM Enrichment', '6. Evidence Gate'] },
    ],
    panels: ['Signal Fusion Algorithm', 'Harmonic Mean Confidence Bias'],
    footer: 'Autonomous Decay Daemon Active',
  },
  {
    id: '2',
    title: 'ICP Decision Gate',
    badge: 'Zero-Token-Loss',
    sections: [
      { label: 'Quality Cutoff Threshold', chips: ['75 / 100'] },
      { label: 'Deterministic Reject Gates', chips: ['Competitor Exclude', 'Geo Mismatch Drop', 'Company Size 25-2k', 'Role Mismatch Drop', 'DNC / Blacklist Halt', 'MX Bounce Verified'] },
    ],
    panels: ['Sub-threshold Action', 'Immediate Token Halt'],
    footer: 'Strict fit filtering enabled',
  },
  {
    id: '3',
    title: 'Timing & Cadence',
    badge: 'Prospect TZ Auto-Sync',
    sections: [
      { label: 'Engagement Windows', chips: ['Morning Slot 09:00-11:30', 'Lunch Auto-Pause', 'Afternoon Sweet Spot 14:00-16:30', 'Max Touch: 1 Call + 2 Emails / wk'] },
    ],
    panels: ['Prospect Timezone Normalizer', 'Skip Federal / Regional Holidays'],
    footer: 'Adaptive Dispatch',
  },
  {
    id: '4',
    title: 'Tone & Editorial Voice',
    badge: 'Peer-to-Peer',
    sections: [
      { label: 'Target Word Limit', chips: ['<45 Ultra-Concise', '45-65 Sweet Spot', '70-100 Consultative'] },
      { label: 'Active Persona Tuning', chips: ['CTO / Technical', 'Enterprise Exec', 'Founder Agile'] },
    ],
    panels: ['Fluff & Synergy Stripper', 'Plain-Text Only'],
    footer: 'Corporate pleasantries stripped',
  },
  {
    id: '5',
    title: 'Intent & Risk Governor',
    badge: 'Freeze <100ms',
    dark: true,
    sections: [
      { label: 'Hard Escalation Locks', chips: ['Hostility / Rage', 'Pricing Pledges', 'Legal & GDPR', 'Disparagement'] },
      { label: '8-Intent Classification', chips: ['Demo Request', 'Tech Clarification', 'Forwarded', 'Timing Bad', 'Budget Block', 'DNC'] },
    ],
    panels: ['Sentiment Tracker', 'Positive / Neutral / Frozen'],
    footer: 'Freeze to Ramya',
  },
];

const policies = [
  ['90-Day Universal Cold-Off', 'Domain freeze if no reply within 3 multi-channel sequences.'],
  ['One-Voice Enterprise Lock', 'Restricts outbound touches to 1 rep/agent per target account.'],
  ['Human Bottleneck Slack Alert', 'Urgent dispatch to Ramya if pending review exceeds 4h.'],
  ['Cryptographic Audit Trail', 'Immutable ledger logging all automated AI touches and actions.'],
];

function Toggle({ active = true }: { active?: boolean }) {
  return (
    <span className={`flex h-6 w-11 items-center rounded-full p-1 shadow-inner ${active ? 'justify-end bg-[#33312d]' : 'justify-start bg-[#d8cec0]'}`}>
      <span className="h-4 w-4 rounded-full bg-white shadow-sm" />
    </span>
  );
}

function Metric({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="rounded-2xl border border-[#ece2d4] bg-white p-5 shadow-sm">
      <div className="text-[11px] font-bold uppercase tracking-wide text-[#83796c]">{label}</div>
      <div className="mt-3 font-serif text-[42px] font-bold leading-none text-[#2b261f]">{value}</div>
      {sub && <div className="mt-2 text-xs font-bold text-[#3f7f6a]">{sub}</div>}
    </div>
  );
}

export function ControlCentre() {
  const [controls, setControls] = useState<OperationalControls | null>(null);
  const [killLoading, setKillLoading] = useState(false);

  useEffect(() => {
    getOperationalControls().then(setControls).catch(() => {});
  }, []);

  const handleKillSwitch = async () => {
    if (!controls) return;
    const newVal = !controls.global_kill_switch;
    const reason = newVal ? window.prompt('Reason for emergency stop (optional):') ?? 'Emergency Operator Action' : undefined;
    setKillLoading(true);
    try {
      const updated = await toggleKillSwitch(newVal, reason ?? undefined);
      setControls(updated);
    } finally {
      setKillLoading(false);
    }
  };

  const handleAgentToggle = async (agentId: string) => {
    if (!controls) return;
    const paused = !controls.paused_agents.includes(agentId);
    try {
      const updated = await toggleAgentPause(agentId, paused);
      setControls(updated);
    } catch {}
  };

  const killActive = controls?.global_kill_switch ?? false;
  const isPaused = (agentId: string) => controls?.paused_agents.includes(agentId) ?? false;

  return (
    <div className="min-h-screen w-full bg-[#fbf6ec] px-5 py-5 text-[#27231d]">
      <div className="mx-auto flex max-w-[1140px] flex-col gap-5">
        <header className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-[#7b7164]">
              <span>Workspace</span>
              <span className="material-symbols-outlined text-[15px]">chevron_right</span>
              <span>Outreach Pipeline</span>
            </div>
            <div className="text-xs font-bold text-[#7b7164]">Fleet Orchestration <span className="mx-1">→</span> Policies & Guardrails Synthesizer</div>
            <h1 className="font-serif text-[38px] font-bold leading-tight">Master Control Centre</h1>
            <span className="mt-2 inline-flex items-center gap-2 rounded-full bg-[#edf4f0] px-4 py-1.5 text-xs font-bold text-[#3f7f6a]">
              <span className="h-2 w-2 rounded-full bg-[#3f7f6a]" />
              All 7 Autonomous Nodes Synced & Active
            </span>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={handleKillSwitch}
              disabled={killLoading || !controls}
              className={`rounded-full px-6 py-3 text-sm font-black text-white shadow-sm disabled:opacity-60 ${killActive ? 'bg-[#9f1f1a]' : 'bg-[#be2020]'}`}
            >
              {killLoading ? 'Updating...' : killActive ? 'Resume Fleet' : 'Kill Switch'}
            </button>
          </div>
        </header>

        <section className="grid gap-3 md:grid-cols-5">
          <Metric label="Total Active Rules" value="46" sub="Live" />
          <Metric label="Fleet Auto Threshold" value="≥88%" sub="P95 Gate" />
          <div className="rounded-2xl border border-[#ece2d4] bg-white p-5 shadow-sm">
            <div className="flex justify-between text-[11px] font-bold uppercase text-[#83796c]">
              <span>Global Burn Cap</span>
              <span>$84 / $120</span>
            </div>
            <div className="mt-3 font-serif text-[42px] font-bold leading-none">70<span className="text-lg">%</span></div>
            <div className="mt-3 h-2 rounded-full bg-[#e5dccf]">
              <div className="h-full w-[70%] rounded-full bg-[#8a5f00]" />
            </div>
          </div>
          <Metric label="P95 Handover Latency" value="118ms" sub="<120ms Cap" />
          <div className="rounded-2xl border border-[#ece2d4] bg-white p-5 shadow-sm">
            <div className="text-[11px] font-bold uppercase tracking-wide text-[#83796c]">Supervisor Daemon</div>
            <div className="mt-5 flex items-center justify-between">
              <div>
                <div className="font-serif text-2xl font-bold">Strict Active</div>
                <div className="mt-1 text-xs font-bold text-[#3f7f6a]">Fail-Safe Ready</div>
              </div>
              <span className="h-3 w-3 rounded-full bg-[#3f7f6a]" />
            </div>
          </div>
        </section>

        <section className="grid gap-5 lg:grid-cols-3">
          {agentCards.map((agent) => (
            <article
              key={agent.id}
              className={`rounded-[18px] border p-5 shadow-sm ${agent.dark ? 'border-[#332e28] bg-[#28241f] text-white' : 'border-[#ece2d4] bg-white'} ${isPaused(agent.id) ? 'opacity-60' : ''}`}
            >
              <div className="mb-5 flex items-start justify-between gap-3">
                <div className="flex items-start gap-3">
                  <span className={`flex h-7 w-7 items-center justify-center rounded-md text-sm font-black ${agent.dark ? 'bg-white text-[#28241f]' : 'bg-[#2d2a25] text-white'}`}>
                    {agent.id}
                  </span>
                  <h2 className="font-serif text-xl font-bold leading-tight">{agent.title}</h2>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`rounded-full px-3 py-1 text-[11px] font-black ${agent.dark ? 'bg-[#be2020] text-white' : 'bg-[#e9f5ef] text-[#3f7f6a]'}`}>
                    {agent.badge}
                  </span>
                  <button onClick={() => handleAgentToggle(agent.id)} disabled={!controls} title={isPaused(agent.id) ? 'Resume agent' : 'Pause agent'}>
                    <Toggle active={!isPaused(agent.id)} />
                  </button>
                </div>
              </div>

              <div className="flex flex-col gap-4">
                {agent.sections.map((section) => (
                  <div key={section.label}>
                    <div className={`mb-2 text-[11px] font-bold uppercase tracking-wide ${agent.dark ? 'text-[#cbbfae]' : 'text-[#83796c]'}`}>{section.label}</div>
                    <div className="flex flex-wrap gap-2">
                      {section.chips.map((chip, index) => (
                        <span
                          key={chip}
                          className={`rounded-md px-3 py-1.5 text-xs font-bold ${
                            agent.dark
                              ? index < 2
                                ? 'bg-[#4a443c] text-white'
                                : 'bg-[#f7d7d3] text-[#9f1f1a]'
                              : index === 1 && agent.id === '4'
                                ? 'bg-[#e6a219] text-[#2b1f0b]'
                                : 'bg-[#f3ede4] text-[#403931]'
                          }`}
                        >
                          {chip}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-5 grid gap-3 sm:grid-cols-2">
                {agent.panels.map((panel) => (
                  <div key={panel} className={`rounded-xl p-4 text-sm font-semibold ${agent.dark ? 'bg-[#3a352f] text-[#eee7dd]' : 'bg-[#f6efe4] text-[#4a4238]'}`}>
                    {panel}
                  </div>
                ))}
              </div>

              <div className={`mt-5 rounded-xl px-4 py-3 text-xs font-bold ${agent.dark ? 'bg-[#3a352f] text-[#d8cec0]' : 'bg-[#f6efe4] text-[#6e6255]'}`}>
                {agent.footer}
              </div>
            </article>
          ))}
        </section>

        <section className="rounded-[18px] border border-[#ece2d4] bg-white p-5 shadow-sm">
          <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <span className="flex h-7 w-7 items-center justify-center rounded-md bg-[#2d2a25] text-sm font-black text-white">6</span>
              <h2 className="font-serif text-xl font-bold">Telephony, Voice AI & Battlecards</h2>
              <span className="rounded-full bg-[#f2eadf] px-3 py-1 text-xs font-bold">Sub-240ms Speech Engine</span>
            </div>
            <span className="text-xs font-semibold text-[#7b7164]">Active Timbre: Warm Executive Neutral</span>
          </div>
          <div className="grid gap-4 md:grid-cols-4">
            <div className="rounded-xl bg-[#f6efe4] p-4">
              <div className="text-[11px] font-bold uppercase text-[#83796c]">Call Budget Dial</div>
              <div className="mt-2 font-serif text-[42px] font-bold leading-none">90<span className="text-sm"> sec cap</span></div>
              <div className="mt-4 h-2 rounded-full bg-[#e0d6c8]"><div className="h-full w-[68%] rounded-full bg-[#8a5f00]" /></div>
            </div>
            <div className="rounded-xl bg-[#f6efe4] p-4">
              <div className="text-[11px] font-bold uppercase text-[#83796c]">Audio Latency Cap</div>
              <div className="mt-2 font-serif text-[42px] font-bold leading-none text-[#3f7f6a]">218<span className="text-sm text-[#27231d]"> ms</span></div>
              <div className="mt-4 h-2 rounded-full bg-[#e0d6c8]"><div className="h-full w-[52%] rounded-full bg-[#3f7f6a]" /></div>
            </div>
            <div className="rounded-xl bg-[#f6efe4] p-4">
              <div className="text-[11px] font-bold uppercase text-[#83796c]">Cultural Persona Switcher</div>
              {['US SaaS CTO Cadence', 'Indian BFSI CIO Protocol', 'Voice AI Founders Pitch'].map((item, index) => (
                <div key={item} className={`mt-2 rounded-md px-3 py-2 text-xs font-bold ${index === 0 ? 'bg-white text-[#2b261f]' : 'bg-[#eee5d9] text-[#6e6255]'}`}>
                  {item}{index === 0 ? ' ✓' : ''}
                </div>
              ))}
            </div>
            <div className="rounded-xl bg-[#f6efe4] p-4">
              <div className="flex items-center justify-between gap-3">
                <div className="text-sm font-bold">1-Sentence Pivot Rule</div>
                <Toggle />
              </div>
              <div className="mt-7 flex items-center justify-between gap-3">
                <div className="text-sm font-bold">DronaHQ KB Grounding</div>
                <Toggle />
              </div>
            </div>
          </div>
        </section>

        <section className="rounded-[24px] border border-[#e6dccf] bg-[#f6efe4] p-7 shadow-sm">
          <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="font-serif text-2xl font-bold">Fleet Governance & Universal Policies</h2>
              <p className="text-sm text-[#7b7164]">Overarching multi-agent guardrails that strictly supersede individual agent parameters.</p>
            </div>
            <span className="rounded-full bg-[#edf4f0] px-4 py-2 text-xs font-bold text-[#3f7f6a]">Cryptographic Audit Trail Active</span>
          </div>
          <div className="grid gap-5 md:grid-cols-4">
            {policies.map(([title, desc]) => (
              <article key={title} className="rounded-xl bg-white p-5 shadow-sm">
                <div className="mb-5 flex items-start justify-between gap-4">
                  <h3 className="font-serif text-lg font-bold leading-tight">{title}</h3>
                  <Toggle />
                </div>
                <p className="text-sm leading-5 text-[#7b7164]">{desc}</p>
              </article>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
