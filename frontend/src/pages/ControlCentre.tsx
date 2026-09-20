import React, { useState, useEffect } from 'react';
import { getOperationalControls, toggleKillSwitch, toggleAgentPause } from '@/api/system';
import { OperationalControls } from '@/types';

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

  return (
    <div className="w-full bg-surface min-h-screen px-space-lg py-space-lg">
      <div className="flex flex-col w-full gap-space-lg pb-space-xl">
        {/* Top Masthead & Global Controls */}
        <div className="flex flex-col gap-space-md">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-space-md">
            <div className="flex flex-col gap-1">
              <div className="flex items-center gap-space-xs text-outline font-label-sm text-label-sm">
                <span>Fleet Orchestration</span>
                <span className="material-symbols-outlined text-[14px]">arrow_forward</span>
                <span className="text-on-surface">Policies &amp; Guardrails</span>
              </div>
              <div className="flex flex-wrap items-baseline gap-space-sm">
                <h1 className="font-headline-xl text-headline-xl text-on-surface tracking-tight">Master Control Centre</h1>
                <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-surface-container text-tertiary font-label-sm text-label-sm">
                  <span className="w-2 h-2 rounded-full bg-tertiary animate-pulse"></span>
                  <span>All 7 Autonomous Nodes Synced</span>
                </div>
              </div>
            </div>
            <div className="flex items-center flex-wrap gap-space-sm">
              <button className="px-4 py-2 rounded-full bg-surface-container-lowest text-on-surface font-label-md text-label-md shadow-sm hover:bg-surface-container transition-all flex items-center gap-2">
                <span className="material-symbols-outlined text-[18px] text-outline">science</span>
                <span>Dry-Run Guardrails</span>
              </button>
              <button className="px-5 py-2 rounded-full bg-primary-container text-on-primary-container font-label-md text-label-md shadow-sm hover:brightness-105 transition-all flex items-center gap-2">
                <span className="material-symbols-outlined text-[18px]">publish</span>
                <span>Deploy Live Changes</span>
              </button>
              <button
                onClick={handleKillSwitch}
                disabled={killLoading}
                className={`px-4 py-2 rounded-full font-label-md text-label-md shadow-sm transition-all flex items-center gap-1.5 disabled:opacity-60 ${
                  killActive
                    ? 'bg-error text-on-error hover:brightness-95 animate-pulse'
                    : 'bg-error-container text-on-error-container hover:brightness-95'
                }`}
              >
                <span className="material-symbols-outlined text-[18px]">power_settings_new</span>
                <span>{killLoading ? 'Updating…' : killActive ? 'KILL SWITCH ACTIVE — Resume' : 'Kill Switch'}</span>
              </button>
            </div>
          </div>

          {/* Live Telemetry KPI Ribbon */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-space-sm">
            <div className="bg-surface-container-lowest rounded-xl p-space-md shadow-sm flex flex-col justify-between">
              <span className="font-label-sm text-label-sm text-outline uppercase tracking-wider">Active Fleet Rules</span>
              <div className="flex items-baseline justify-between mt-2">
                <span className="font-display-stat text-display-stat text-on-surface leading-none">38</span>
                <span className="font-label-sm text-label-sm text-tertiary bg-surface-container px-2 py-0.5 rounded-md">Live</span>
              </div>
            </div>
            <div className="bg-surface-container-lowest rounded-xl p-space-md shadow-sm flex flex-col justify-between">
              <span className="font-label-sm text-label-sm text-outline uppercase tracking-wider">Auto Threshold</span>
              <div className="flex items-baseline justify-between mt-2">
                <span className="font-display-stat text-display-stat text-on-surface leading-none">≥88%</span>
                <span className="font-label-sm text-label-sm text-on-surface-variant bg-surface-container px-2 py-0.5 rounded-md">P95</span>
              </div>
            </div>
            <div className="bg-surface-container-lowest rounded-xl p-space-md shadow-sm flex flex-col justify-between">
              <div className="flex items-center justify-between">
                <span className="font-label-sm text-label-sm text-outline uppercase tracking-wider">Global Burn Cap</span>
                <span className="font-label-sm text-label-sm text-outline">$84 / $120</span>
              </div>
              <div className="mt-2 flex flex-col gap-1.5">
                <div className="flex items-baseline justify-between">
                  <span className="font-display-stat text-display-stat text-on-surface leading-none">70<span className="text-headline-sm font-headline-sm">%</span></span>
                  <span className="font-label-sm text-label-sm text-primary">Normal Burn</span>
                </div>
                <div className="w-full h-1.5 bg-surface-container rounded-full overflow-hidden">
                  <div className="h-full bg-primary-container rounded-full" style={{ width: '70%' }}></div>
                </div>
              </div>
            </div>
            <div className="bg-surface-container-lowest rounded-xl p-space-md shadow-sm flex flex-col justify-between">
              <span className="font-label-sm text-label-sm text-outline uppercase tracking-wider">Handover Latency</span>
              <div className="flex items-baseline justify-between mt-2">
                <span className="font-display-stat text-display-stat text-tertiary leading-none">118<span className="text-headline-sm font-headline-sm">ms</span></span>
                <span className="font-label-sm text-label-sm text-tertiary bg-surface-container px-2 py-0.5 rounded-md">&lt;120ms Cap</span>
              </div>
            </div>
            <div className="col-span-2 md:col-span-1 bg-surface-container-lowest rounded-xl p-space-md shadow-sm flex flex-col justify-between">
              <span className="font-label-sm text-label-sm text-outline uppercase tracking-wider">Supervisor Mode</span>
              <div className="flex items-center justify-between mt-2">
                <span className="font-headline-md text-headline-md text-on-surface">Strict Active</span>
                <div className="w-3 h-3 rounded-full bg-primary animate-ping"></div>
              </div>
            </div>
          </div>
        </div>

        {/* Central Multi-Agent Rule Matrix Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-space-md">
          {/* Node 0: Sourcing Scout */}
          <div className={`bg-surface-container-lowest rounded-xl p-space-md shadow-sm flex flex-col justify-between gap-space-md ${controls?.paused_agents.includes('0') ? 'opacity-60' : ''}`}>
            <div className="flex flex-col gap-space-sm">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-6 h-6 rounded-md bg-surface-container flex items-center justify-center font-label-sm text-label-sm text-on-surface">0</span>
                  <h2 className="font-headline-md text-headline-md text-on-surface">Sourcing Scout</h2>
                </div>
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded-full bg-surface-container font-label-sm text-label-sm text-tertiary">99.4% Dedup Acc.</span>
                  <button onClick={() => handleAgentToggle('0')} title={controls?.paused_agents.includes('0') ? 'Resume agent' : 'Pause agent'}
                    className={`w-9 h-5 rounded-full relative p-0.5 flex items-center transition-colors ${controls?.paused_agents.includes('0') ? 'bg-outline' : 'bg-inverse-surface'}`}>
                    <span className={`w-4 h-4 rounded-full bg-surface-container-lowest transition-transform ${controls?.paused_agents.includes('0') ? 'translate-x-0' : 'translate-x-4'}`}></span>
                  </button>
                </div>
              </div>
              <div className="flex flex-wrap gap-1.5 pt-1">
                {['K8s', 'Go', 'Bazel', 'Rust'].map((t) => (
                  <span key={t} className="px-2 py-0.5 rounded-md bg-surface-container-low font-label-sm text-label-sm text-on-surface-variant">{t}</span>
                ))}
                <span className="px-2 py-0.5 rounded-md bg-surface-container-high font-label-sm text-label-sm text-on-surface font-semibold">CTO / VP Eng</span>
              </div>
              <div className="bg-surface-container-low rounded-lg p-space-sm flex items-center justify-between">
                <span className="font-body-sm text-body-sm text-on-surface-variant">Min Commit Velocity</span>
                <span className="font-label-md text-label-md text-on-surface">&gt;15 commits / mo</span>
              </div>
            </div>
            <div className="flex flex-col gap-space-sm pt-space-xs">
              {['Auto-Enrich Profile', 'Dedup Against CRM'].map((label) => (
                <div key={label} className="flex items-center justify-between py-1">
                  <span className="font-body-sm text-body-sm text-on-surface">{label}</span>
                  <button className="w-10 h-6 bg-inverse-surface rounded-full relative p-0.5 flex items-center transition-colors">
                    <span className="w-5 h-5 rounded-full bg-surface-container-lowest translate-x-4 transition-transform"></span>
                  </button>
                </div>
              ))}
              <div className="flex items-center justify-between py-1 bg-surface-container rounded-lg px-space-sm">
                <span className="font-body-sm text-body-sm text-outline">Scrape Speed Limit</span>
                <span className="font-label-md text-label-md text-on-surface">1,500 / hr</span>
              </div>
            </div>
          </div>

          {/* Node 1: Deep Research */}
          <div className="bg-surface-container-lowest rounded-xl p-space-md shadow-sm flex flex-col justify-between gap-space-md">
            <div className="flex flex-col gap-space-sm">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-6 h-6 rounded-md bg-surface-container flex items-center justify-center font-label-sm text-label-sm text-on-surface">1</span>
                  <h2 className="font-headline-md text-headline-md text-on-surface">Deep Research</h2>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="font-label-sm text-label-sm text-outline">Precision</span>
                  <button className="w-8 h-5 bg-inverse-surface rounded-full relative p-0.5 flex items-center">
                    <span className="w-4 h-4 rounded-full bg-surface-container-lowest translate-x-3 transition-transform"></span>
                  </button>
                </div>
              </div>
              <div className="flex flex-col gap-2.5 pt-2">
                {[
                  { label: 'Seniority Multiplier', val: '95%', w: '95%', bar: 'bg-primary-container' },
                  { label: 'Build Frustration Signal', val: '90%', w: '90%', bar: 'bg-primary-container' },
                  { label: 'Tech Stack Relevance', val: '85%', w: '85%', bar: 'bg-tertiary-container' },
                  { label: 'Funding Stage Signal', val: '80%', w: '80%', bar: 'bg-secondary-fixed-dim' },
                ].map((s) => (
                  <div key={s.label}>
                    <div className="flex justify-between font-label-sm text-label-sm mb-1">
                      <span className="text-on-surface-variant">{s.label}</span>
                      <span className="text-on-surface font-semibold">{s.val}</span>
                    </div>
                    <div className="h-2 bg-surface-container rounded-full overflow-hidden">
                      <div className={`h-full ${s.bar} rounded-full`} style={{ width: s.w }}></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div className="flex items-center justify-between p-2 rounded-lg bg-surface-container-low font-label-sm text-label-sm text-outline">
              <span>Signal Fusion Matrix</span>
              <span className="text-on-surface font-semibold">Harmonic Mean</span>
            </div>
          </div>

          {/* Node 2: ICP Decision Gate */}
          <div className="bg-surface-container-lowest rounded-xl p-space-md shadow-sm flex flex-col justify-between gap-space-md">
            <div className="flex flex-col gap-space-sm">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-6 h-6 rounded-md bg-surface-container flex items-center justify-center font-label-sm text-label-sm text-on-surface">2</span>
                  <h2 className="font-headline-md text-headline-md text-on-surface">ICP Decision Gate</h2>
                </div>
                <span className="px-2 py-0.5 rounded-full bg-surface-container font-label-sm text-label-sm text-primary">Burn Lock $120/d</span>
              </div>
              <div className="bg-surface-container-low rounded-xl p-space-sm flex flex-col gap-2">
                <div className="flex justify-between items-baseline">
                  <span className="font-label-sm text-label-sm text-outline">Min Quality Cutoff Score</span>
                  <span className="font-display-stat text-display-stat text-on-surface leading-none">78<span className="text-label-md text-outline">/100</span></span>
                </div>
                <div className="w-full flex items-center gap-2">
                  <span className="font-label-sm text-label-sm text-outline">50</span>
                  <div className="relative w-full h-2 bg-surface-container rounded-full">
                    <div className="absolute h-full bg-primary rounded-full" style={{ width: '78%' }}></div>
                    <div className="absolute w-3.5 h-3.5 bg-surface-container-lowest rounded-full -top-0.5 shadow-sm" style={{ left: 'calc(78% - 7px)' }}></div>
                  </div>
                  <span className="font-label-sm text-label-sm text-outline">100</span>
                </div>
              </div>
              <div className="flex flex-col gap-1.5 pt-1">
                {['Non-US Geography Drop', 'Engineering Headcount ≥ 10', 'MX & Domain Hard Verification'].map((label) => (
                  <div key={label} className="flex items-center justify-between py-1">
                    <span className="font-body-sm text-body-sm text-on-surface">{label}</span>
                    <button className="w-9 h-5 bg-inverse-surface rounded-full relative p-0.5 flex items-center">
                      <span className="w-4 h-4 rounded-full bg-surface-container-lowest translate-x-4 transition-transform"></span>
                    </button>
                  </div>
                ))}
              </div>
            </div>
            <div className="text-right">
              <span className="font-label-sm text-label-sm text-tertiary">Zero-Loss Policy Active</span>
            </div>
          </div>

          {/* Node 3: Outreach Timing & Cadence */}
          <div className="bg-surface-container-lowest rounded-xl p-space-md shadow-sm flex flex-col justify-between gap-space-md">
            <div className="flex flex-col gap-space-sm">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-6 h-6 rounded-md bg-surface-container flex items-center justify-center font-label-sm text-label-sm text-on-surface">3</span>
                  <h2 className="font-headline-md text-headline-md text-on-surface">Timing &amp; Cadence</h2>
                </div>
                <span className="font-label-sm text-label-sm text-outline">Local TZ Sync</span>
              </div>
              <div className="flex flex-col gap-2">
                <span className="font-label-sm text-label-sm text-on-surface-variant">Engagement Windows (Local Recipient)</span>
                <div className="h-6 w-full bg-surface-container rounded-md flex overflow-hidden p-0.5 gap-1">
                  <div className="h-full bg-surface-container-lowest rounded-sm text-[9px] font-label-sm flex items-center justify-center text-outline" style={{ width: '25%' }}>Off</div>
                  <div className="h-full bg-primary-container rounded-sm text-[9px] font-label-sm flex items-center justify-center text-on-primary-container font-semibold" style={{ width: '25%' }}>9:00 - 11:30</div>
                  <div className="h-full bg-surface-container-lowest rounded-sm text-[9px] font-label-sm flex items-center justify-center text-outline" style={{ width: '15%' }}>Lunch</div>
                  <div className="h-full bg-primary-container rounded-sm text-[9px] font-label-sm flex items-center justify-center text-on-primary-container font-semibold" style={{ width: '25%' }}>14:00 - 16:30</div>
                  <div className="h-full bg-surface-container-lowest rounded-sm text-[9px] font-label-sm flex items-center justify-center text-outline" style={{ width: '10%' }}>Off</div>
                </div>
              </div>
              <div className="bg-surface-container-low rounded-lg p-space-sm flex items-center justify-between mt-1">
                <span className="font-body-sm text-body-sm text-on-surface-variant">Max Touch Frequency</span>
                <span className="font-label-md text-label-md text-on-surface">1 Call + 2 Emails / wk</span>
              </div>
            </div>
            <div className="flex flex-col gap-2">
              {['Auto-Pause Lunch Dip', 'Skip Federal Holidays'].map((label) => (
                <div key={label} className="flex items-center justify-between">
                  <span className="font-body-sm text-body-sm text-on-surface">{label}</span>
                  <button className="w-9 h-5 bg-inverse-surface rounded-full relative p-0.5 flex items-center">
                    <span className="w-4 h-4 rounded-full bg-surface-container-lowest translate-x-4 transition-transform"></span>
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Node 4: Tone & Brevity */}
          <div className="bg-surface-container-lowest rounded-xl p-space-md shadow-sm flex flex-col justify-between gap-space-md">
            <div className="flex flex-col gap-space-sm">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-6 h-6 rounded-md bg-surface-container flex items-center justify-center font-label-sm text-label-sm text-on-surface">4</span>
                  <h2 className="font-headline-md text-headline-md text-on-surface">Tone &amp; Brevity</h2>
                </div>
                <span className="px-2 py-0.5 rounded-full bg-surface-container-high font-label-sm text-label-sm text-on-surface">Peer-to-Peer</span>
              </div>
              <div className="flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <span className="font-label-sm text-label-sm text-outline">Target Length Limit</span>
                  <span className="font-label-md text-label-md text-on-surface">45 – 65 Words</span>
                </div>
                <div className="relative w-full h-2 bg-surface-container rounded-full">
                  <div className="absolute h-full bg-tertiary rounded-full" style={{ left: '35%', width: '25%' }}></div>
                </div>
              </div>
              <div className="flex flex-col gap-2 pt-1">
                <div className="flex items-center justify-between">
                  <span className="font-body-sm text-body-sm text-on-surface">Zero-Fluff Sentence Stripper</span>
                  <button className="w-9 h-5 bg-inverse-surface rounded-full relative p-0.5 flex items-center">
                    <span className="w-4 h-4 rounded-full bg-surface-container-lowest translate-x-4 transition-transform"></span>
                  </button>
                </div>
                <div className="flex items-center justify-between">
                  <span className="font-body-sm text-body-sm text-on-surface">Jargon Blacklist Filter</span>
                  <span className="px-2 py-0.5 rounded-full bg-surface-container font-label-sm text-label-sm text-outline">34 Banned Terms</span>
                </div>
              </div>
            </div>
            <div className="bg-surface-container-low rounded-lg p-2 text-on-surface-variant font-label-sm text-label-sm flex items-center gap-2">
              <span className="material-symbols-outlined text-[16px] text-tertiary">check_circle</span>
              <span>Corporate pleasantries disabled</span>
            </div>
          </div>

          {/* Node 5: Safety & Routing */}
          <div className="bg-surface-container-lowest rounded-xl p-space-md shadow-sm flex flex-col justify-between gap-space-md">
            <div className="flex flex-col gap-space-sm">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-6 h-6 rounded-md bg-surface-container flex items-center justify-center font-label-sm text-label-sm text-on-surface">5</span>
                  <h2 className="font-headline-md text-headline-md text-on-surface">Safety &amp; Routing</h2>
                </div>
                <span className="px-2 py-0.5 rounded-full bg-surface-container font-label-sm text-label-sm text-error">Freeze to Ramya</span>
              </div>
              <div className="flex flex-col gap-2">
                <span className="font-label-sm text-label-sm text-outline uppercase tracking-wider">Armed Stop-Words Registry</span>
                <div className="flex flex-wrap gap-1">
                  {['lawyer', 'pricing', 'discount', 'gdpr', 'unsubscribe'].map((word) => (
                    <span key={word} className="px-2 py-0.5 rounded-md bg-error-container text-on-error-container font-label-sm text-label-sm flex items-center gap-1">
                      {word}
                      <span className="material-symbols-outlined text-[12px]">lock</span>
                    </span>
                  ))}
                </div>
              </div>
              <div className="flex items-center justify-between py-1">
                <span className="font-body-sm text-body-sm text-on-surface">Human Handover Trigger</span>
                <span className="font-label-md text-label-md text-on-surface">&lt; 72% Conf.</span>
              </div>
            </div>
            <div className="p-2 rounded-lg bg-surface-container-low flex justify-between items-center font-label-sm text-label-sm">
              <span className="text-outline">Auto-Reply (FAQ only)</span>
              <span className="text-tertiary font-semibold">≥ 88% Confidence</span>
            </div>
          </div>

          {/* Node 6: Voice AI - spans full width */}
          <div className="bg-surface-container-lowest rounded-xl p-space-md shadow-sm flex flex-col justify-between gap-space-md md:col-span-2 lg:col-span-3">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-space-sm">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-md bg-surface-container flex items-center justify-center font-label-sm text-label-sm text-on-surface">6</span>
                <h2 className="font-headline-md text-headline-md text-on-surface">Voice AI &amp; Synthesizer Engine</h2>
                <span className="ml-2 px-2 py-0.5 rounded-full bg-surface-container-high font-label-sm text-label-sm text-on-surface">Low Latency Telephony</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="font-label-sm text-label-sm text-outline">Timbre: Warm Executive Neutral</span>
                <span className="material-symbols-outlined text-[20px] text-tertiary">graphic_eq</span>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-space-md pt-2">
              <div className="bg-surface-container-low rounded-lg p-space-sm flex flex-col justify-between gap-2">
                <div className="flex justify-between items-center">
                  <span className="font-body-sm text-body-sm text-on-surface">Max Speech Latency</span>
                  <span className="font-label-md text-label-md text-tertiary">240ms cap</span>
                </div>
                <div className="w-full h-1.5 bg-surface-container rounded-full overflow-hidden">
                  <div className="h-full bg-tertiary rounded-full" style={{ width: '45%' }}></div>
                </div>
              </div>
              <div className="bg-surface-container-low rounded-lg p-space-sm flex items-center justify-between">
                <div className="flex flex-col">
                  <span className="font-body-sm text-body-sm text-on-surface">Barge-in Cutoff</span>
                  <span className="font-label-sm text-label-sm text-outline">&lt;180ms cutoff response</span>
                </div>
                <button className="w-9 h-5 bg-inverse-surface rounded-full relative p-0.5 flex items-center">
                  <span className="w-4 h-4 rounded-full bg-surface-container-lowest translate-x-4 transition-transform"></span>
                </button>
              </div>
              <div className="bg-surface-container-low rounded-lg p-space-sm flex items-center justify-between">
                <div className="flex flex-col">
                  <span className="font-body-sm text-body-sm text-on-surface">Live Whisper Supervisor</span>
                  <span className="font-label-sm text-label-sm text-outline">On competitor mention</span>
                </div>
                <button className="w-9 h-5 bg-inverse-surface rounded-full relative p-0.5 flex items-center">
                  <span className="w-4 h-4 rounded-full bg-surface-container-lowest translate-x-4 transition-transform"></span>
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Master Fleet Overrides */}
        <div className="bg-surface-container-low rounded-2xl p-space-lg shadow-sm flex flex-col gap-space-md">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <h3 className="font-headline-md text-headline-md text-on-surface">Fleet Governance &amp; Universal Policies</h3>
              <p className="font-body-sm text-body-sm text-outline">Overarching guardrails that supersede individual agent parameters.</p>
            </div>
            <div className="flex items-center gap-2 text-tertiary font-label-sm text-label-sm bg-surface-container px-3 py-1 rounded-full w-fit">
              <span className="material-symbols-outlined text-[16px]">verified</span>
              <span>Cryptographic Audit Trail Active</span>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-space-md pt-space-xs">
            {[
              { label: '90-Day Universal Cold-Off', desc: 'Locks domain if no positive reply within 3 sequences.' },
              { label: 'One-Voice Enterprise Lock', desc: 'Restricts concurrent outbound touches to a single rep/agent.' },
              { label: 'Supervisor Delay Alert', desc: 'Notifies Ramya via Slack if pending human approval > 4 hrs.' },
            ].map((rule) => (
              <div key={rule.label} className="bg-surface-container-lowest rounded-xl p-space-md flex items-start justify-between gap-space-sm shadow-sm">
                <div className="flex flex-col gap-1">
                  <span className="font-label-lg text-label-lg text-on-surface">{rule.label}</span>
                  <span className="font-body-sm text-body-sm text-outline">{rule.desc}</span>
                </div>
                <button className="w-10 h-6 bg-inverse-surface rounded-full relative p-0.5 flex items-center shrink-0">
                  <span className="w-5 h-5 rounded-full bg-surface-container-lowest translate-x-4 transition-transform"></span>
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
