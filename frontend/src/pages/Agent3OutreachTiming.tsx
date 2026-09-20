import { useState } from 'react';

export function Agent3OutreachTiming() {
  const [deployText, setDeployText] = useState<{ icon: string; label: string }>({ icon: 'rocket_launch', label: 'Deploy Timing Rules' });
  const [simText, setSimText] = useState<{ icon: string; label: string }>({ icon: 'science', label: 'Simulate 7-Day Dispatch' });

  const handleDeploy = () => {
    setDeployText({ icon: 'sync', label: 'Validating Rules...' });
    setTimeout(() => {
      setDeployText({ icon: 'done', label: 'Rules Deployed!' });
      setTimeout(() => setDeployText({ icon: 'rocket_launch', label: 'Deploy Timing Rules' }), 1800);
    }, 700);
  };

  const handleSim = () => {
    setSimText({ icon: 'check', label: 'Simulation Passed: 0 Spacing Collisions' });
    setTimeout(() => setSimText({ icon: 'science', label: 'Simulate 7-Day Dispatch' }), 2400);
  };

  const heatBars = [
    { h: '18%', val: '12%' }, { h: '26%', val: '19%' },
    { h: '72%', val: '36%', peak: true }, { h: '88%', val: '41%', peak: true },
    { h: '96%', val: '42%', peak: true, star: true }, { h: '80%', val: '39%', peak: true },
    { h: '64%', val: '31%', peak: true }, { h: '34%', val: '16%' },
    { h: '15%', val: '9%' }, { h: '14%', val: '8%' },
    { h: '19%', val: '11%' }, { h: '28%', val: '15%' },
    { h: '68%', val: '32%', aft: true }, { h: '84%', val: '38%', aft: true },
    { h: '78%', val: '35%', aft: true }, { h: '60%', val: '29%', aft: true },
    { h: '48%', val: '22%', aft: true }, { h: '30%', val: '14%' },
    { h: '16%', val: '7%' },
  ];

  return (
    <div className="w-full bg-surface min-h-screen px-space-lg py-space-lg">
      <div className="flex flex-col w-full relative">
        <div className="relative w-full max-w-5xl mx-auto my-auto bg-surface-container-lowest rounded-2xl shadow-2xl flex flex-col overflow-hidden">
          {/* Modal Header */}
          <div className="px-space-xl pt-space-xl pb-space-lg bg-surface-container-low/70 flex flex-col gap-space-md">
            <div className="flex items-center justify-between">
              <div className="flex flex-wrap items-center gap-2">
                <span className="px-2.5 py-0.5 rounded-full bg-inverse-surface text-inverse-on-surface font-label-sm text-label-sm tracking-wider uppercase">Node 03</span>
                <span className="px-2.5 py-0.5 rounded-full bg-surface-container-high text-on-surface-variant font-label-sm text-label-sm">Temporal Dispatch &amp; Cadence Engine</span>
                <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-tertiary-fixed text-on-tertiary-fixed font-label-sm text-label-sm">
                  <span className="w-1.5 h-1.5 rounded-full bg-tertiary animate-pulse"></span>
                  Timezone Synced
                </span>
              </div>
            </div>
            <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-2">
              <h2 className="font-headline-lg text-headline-lg text-on-surface tracking-tight">Agent 3: Outreach Timing &amp; Cadence</h2>
              <span className="font-label-md text-label-md text-outline">Cluster US-EAST-02 • Active Rule Matrix v4.12</span>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5 pt-1">
              {[
                { icon: 'schedule', label: 'Window', value: '9:00 AM – 4:30 PM', bg: 'bg-primary-fixed text-on-primary-fixed' },
                { icon: 'speed', label: 'Max Touch', value: '1 Call + 2 Emails / wk', bg: 'bg-tertiary-fixed text-on-tertiary-fixed' },
                { icon: 'public', label: 'Coverage', value: '4 US Zones', bg: 'bg-secondary-fixed text-on-secondary-fixed' },
                { icon: 'check_circle', label: 'On-Time Dispatch', value: '99.1% Fidelity', bg: 'bg-surface-container-highest text-tertiary' },
              ].map(stat => (
                <div key={stat.label} className="bg-surface-container-lowest/80 px-3.5 py-2.5 rounded-xl shadow-sm flex items-center gap-3">
                  <div className={`w-7 h-7 rounded-lg ${stat.bg} flex items-center justify-center`}>
                    <span className="material-symbols-outlined text-[18px]">{stat.icon}</span>
                  </div>
                  <div className="flex flex-col min-w-0">
                    <span className="font-label-sm text-label-sm text-outline uppercase tracking-wider">{stat.label}</span>
                    <span className="font-label-md text-label-md text-on-surface font-semibold truncate">{stat.value}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Body */}
          <div className="p-space-xl overflow-y-auto flex flex-col gap-space-xl">
            {/* Heatmap Section */}
            <div className="flex flex-col gap-space-md">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
                <div className="flex flex-col">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-primary-container"></span>
                    <h3 className="font-headline-md text-headline-md text-on-surface">Visual Dispatch Window Heatmap &amp; Best Hours</h3>
                  </div>
                  <p className="font-body-sm text-body-sm text-on-surface-variant">Calibrated against 14,280 recorded touches across B2B technology decision makers.</p>
                </div>
                <div className="flex items-center gap-3 self-start md:self-auto bg-surface-container-low px-3 py-1.5 rounded-xl">
                  <span className="font-label-sm text-label-sm text-outline uppercase">Target View:</span>
                  <div className="flex items-center gap-1 font-label-sm text-label-sm">
                    <button className="px-2 py-0.5 rounded-md bg-surface-container-lowest shadow-sm text-on-surface font-semibold">PT</button>
                    <button className="px-2 py-0.5 rounded-md text-on-surface-variant hover:text-on-surface">MT</button>
                    <button className="px-2 py-0.5 rounded-md text-on-surface-variant hover:text-on-surface">CT</button>
                    <button className="px-2 py-0.5 rounded-md text-on-surface-variant hover:text-on-surface">ET</button>
                  </div>
                </div>
              </div>
              <div className="bg-surface-container-low/60 rounded-xl p-space-lg flex flex-col gap-space-lg shadow-sm">
                <div className="flex flex-col gap-3">
                  <div className="flex items-center justify-between text-label-sm font-label-sm text-outline px-1">
                    {['08:00 AM', '10:00 AM', '12:00 PM', '02:00 PM', '04:00 PM', '06:00 PM'].map(t => <span key={t}>{t}</span>)}
                  </div>
                  <div className="w-full h-36 bg-surface-container-lowest rounded-xl p-3 flex items-end justify-between gap-1.5 shadow-inner">
                    {heatBars.map((bar, i) => (
                      <div key={i} className="flex-1 flex flex-col items-center gap-1 group relative h-full justify-end">
                        <div
                          className={`w-full rounded-t transition-all duration-300 ${bar.star ? 'shadow-md' : ''} ${bar.peak ? 'bg-primary-container shadow-sm' : bar.aft ? 'bg-primary-container/80' : 'bg-surface-container-highest/60'}`}
                          style={{ height: bar.h }}
                        >
                          {bar.star && <span className="absolute -top-3 left-1/2 -translate-x-1/2 text-[10px] text-primary font-bold">★</span>}
                        </div>
                        <span className="font-label-sm text-label-sm text-outline opacity-0 group-hover:opacity-100 transition-opacity absolute -top-6 text-[10px]">{bar.val}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div className="bg-primary-fixed/40 p-3.5 rounded-xl flex items-start gap-3">
                    <span className="w-2.5 h-2.5 rounded-full bg-primary-container mt-1 shrink-0"></span>
                    <div className="flex flex-col">
                      <span className="font-label-md text-label-md text-on-surface font-semibold">9:00 AM – 11:30 AM</span>
                      <span className="font-body-sm text-body-sm text-on-surface-variant leading-snug">Peak morning window • <strong className="text-on-surface font-semibold">42% reply probability</strong>. Optimal for initial outreach touches.</span>
                    </div>
                  </div>
                  <div className="bg-surface-container-highest/50 p-3.5 rounded-xl flex items-start gap-3">
                    <span className="w-2.5 h-2.5 rounded-full bg-outline/40 mt-1 shrink-0"></span>
                    <div className="flex flex-col">
                      <span className="font-label-md text-label-md text-on-surface font-semibold">11:30 AM – 2:00 PM</span>
                      <span className="font-body-sm text-body-sm text-on-surface-variant leading-snug">Lunch dip • Sequence auto-pauses dispatches to prevent spam filters &amp; inbox skips.</span>
                    </div>
                  </div>
                  <div className="bg-primary-fixed/30 p-3.5 rounded-xl flex items-start gap-3">
                    <span className="w-2.5 h-2.5 rounded-full bg-primary-container mt-1 shrink-0"></span>
                    <div className="flex flex-col">
                      <span className="font-label-md text-label-md text-on-surface font-semibold">2:00 PM – 4:30 PM</span>
                      <span className="font-body-sm text-body-sm text-on-surface-variant leading-snug">Afternoon sweet spot • <strong className="text-on-surface font-semibold">38% reply probability</strong>. Best performance on voice follow-ups.</span>
                    </div>
                  </div>
                </div>
                <div className="bg-surface-container-lowest p-3.5 rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-sm">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-lg bg-surface-container flex items-center justify-center text-primary">
                      <span className="material-symbols-outlined text-[20px]">sync_saved_locally</span>
                    </div>
                    <div className="flex flex-col">
                      <div className="flex items-center gap-2">
                        <span className="font-label-md text-label-md text-on-surface font-semibold">Prospect Timezone Auto-Normalizer</span>
                        <span className="px-2 py-0.5 rounded-full bg-tertiary-fixed text-on-tertiary-fixed font-label-sm text-label-sm">Active • PT/MT/CT/ET</span>
                      </div>
                      <span className="font-body-sm text-body-sm text-on-surface-variant">Converts each prospect's corporate headquarters and LinkedIn geocodes into local dispatch schedules automatically.</span>
                    </div>
                  </div>
                  <button aria-pressed="true" className="relative w-11 h-6 bg-inverse-surface rounded-full transition-colors flex items-center px-0.5 shrink-0 self-start sm:self-auto cursor-pointer">
                    <div className="w-5 h-5 bg-surface rounded-full shadow-sm transform translate-x-5 transition-transform"></div>
                  </button>
                </div>
              </div>
            </div>

            {/* Cadence Sequence */}
            <div className="flex flex-col gap-space-md">
              <div className="flex flex-col">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-tertiary"></span>
                  <h3 className="font-headline-md text-headline-md text-on-surface">Cadence Sequence &amp; Frequency Caps</h3>
                </div>
                <p className="font-body-sm text-body-sm text-on-surface-variant">Autonomous progression path for unreached prospects over a 10-day evaluation interval.</p>
              </div>
              <div className="relative flex flex-col gap-4 pl-6 md:pl-8 before:content-[''] before:absolute before:left-3 md:before:left-4 before:top-4 before:bottom-4 before:w-0.5 before:bg-surface-container-highest">
                {[
                  { dot: 'bg-primary', icon: 'person_add', iconBg: 'bg-primary-fixed text-on-primary-fixed', step: 'Step 01 • Day 1', time: '10:15 AM Local', tag: 'Morning Prime', tagColor: 'bg-primary-container/20 text-primary', title: 'Hyper-personalized LinkedIn invite / hook', desc: 'Leverages recent company engineering blog post or verified hiring intent trigger.', channel: 'LinkedIn' },
                  { dot: 'bg-primary-container', icon: 'alternate_email', iconBg: 'bg-surface-container-high text-on-surface', step: 'Step 02 • Day 3', time: '2:30 PM Local', tag: '+48h Spacing', tagColor: 'bg-secondary-container text-on-secondary-container', title: 'Follow-up contextual Email (52 words concise)', desc: 'Direct mention of architecture bottleneck; clean single-question call-to-action.', channel: 'Work Email' },
                  { dot: 'bg-tertiary', icon: 'mic', iconBg: 'bg-tertiary-fixed text-on-tertiary-fixed', step: 'Step 03 • Day 6', time: '11:00 AM Local', tag: 'Conditional Trigger', tagColor: 'bg-tertiary/10 text-tertiary', title: 'Autonomous Voice Agent touch (if no reply)', desc: 'Executes 45-second discovery inquiry or drops natural conversational voicemail.', channel: 'Direct Phone' },
                  { dot: 'bg-outline', icon: 'outgoing_mail', iconBg: 'bg-surface-container-high text-outline', step: 'Step 04 • Day 10', time: '3:15 PM Local', tag: 'Graceful Exit', tagColor: 'bg-surface-container-highest text-outline', title: 'Gentle sign-off nudge', desc: 'Archives contact record and transfers prospect to low-frequency quarterly newsletter list.', channel: 'Work Email' },
                ].map(step => (
                  <div key={step.step} className="relative bg-surface-container-low/50 hover:bg-surface-container-low rounded-xl p-4 transition-all shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-3">
                    <span className={`absolute -left-6 md:-left-8 top-5 w-4 h-4 rounded-full ${step.dot} ring-4 ring-surface-container-lowest`}></span>
                    <div className="flex items-start gap-3.5">
                      <div className={`w-10 h-10 rounded-xl ${step.iconBg} flex items-center justify-center shrink-0`}>
                        <span className="material-symbols-outlined text-[20px]">{step.icon}</span>
                      </div>
                      <div className="flex flex-col">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-headline-sm text-headline-sm text-on-surface">{step.step}</span>
                          <span className="px-2 py-0.5 rounded-full bg-surface-container-highest font-label-sm text-label-sm text-on-surface">{step.time}</span>
                          <span className={`px-2 py-0.5 rounded-full font-label-sm text-label-sm font-semibold ${step.tagColor}`}>{step.tag}</span>
                        </div>
                        <p className="font-body-md text-body-md text-on-surface mt-0.5">{step.title}</p>
                        <p className="font-body-sm text-body-sm text-on-surface-variant">{step.desc}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 self-start md:self-auto shrink-0">
                      <span className="px-2.5 py-1 rounded-lg bg-surface-container text-outline font-label-sm text-label-sm">Channel: {step.channel}</span>
                      <span className="material-symbols-outlined text-[18px] text-outline">tune</span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Guardrails */}
              <div className="bg-surface-container-low rounded-xl p-space-lg flex flex-col gap-4">
                <span className="font-label-sm text-label-sm uppercase tracking-wider text-outline font-semibold">Strict Guardrails &amp; Safety Compliance</span>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {[
                    { title: 'Weekend & Holiday Freeze', desc: 'Never dispatch outreach on Saturdays, Sundays, or statutory federal holidays.' },
                    { title: '48h Touch Spacing', desc: 'Enforces 48-hour minimum quiet cooldown buffer between touches across all channels.' },
                    { title: 'Immediate Reply Lock', desc: 'Auto-pauses sequence immediately upon inbound human response or manual SDR tag.' },
                  ].map(g => (
                    <div key={g.title} className="bg-surface-container-lowest p-4 rounded-xl flex flex-col justify-between gap-3 shadow-sm">
                      <div className="flex flex-col gap-1">
                        <span className="font-label-md text-label-md text-on-surface font-semibold">{g.title}</span>
                        <p className="font-body-sm text-body-sm text-on-surface-variant">{g.desc}</p>
                      </div>
                      <div className="flex items-center justify-between pt-2">
                        <span className="font-label-sm text-label-sm text-tertiary font-semibold flex items-center gap-1">
                          <span className="material-symbols-outlined text-[14px]">verified</span> Enforced
                        </span>
                        <button aria-pressed="true" className="relative w-10 h-5 bg-inverse-surface rounded-full transition-colors flex items-center px-0.5 shrink-0 cursor-pointer">
                          <div className="w-4 h-4 bg-surface rounded-full shadow-sm transform translate-x-5 transition-transform"></div>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="px-space-xl py-space-md bg-surface-container-low/90 backdrop-blur-md flex flex-col sm:flex-row items-center justify-between gap-space-md">
            <div className="flex items-center gap-2 text-on-surface-variant font-body-sm text-body-sm">
              <span className="material-symbols-outlined text-[18px] text-tertiary">check_circle</span>
              <span>Cadence simulation predicts <strong>+24.6% reply lift</strong> vs static schedule.</span>
            </div>
            <div className="flex items-center gap-3 w-full sm:w-auto justify-end">
              <button
                className="px-4 py-2 rounded-full bg-surface-container-lowest hover:bg-surface-container text-on-surface font-label-md text-label-md shadow-sm transition-all flex items-center gap-1.5"
                onClick={handleSim}
                type="button"
              >
                <span className={`material-symbols-outlined text-[18px] text-outline ${simText.label.startsWith('Simulation') ? 'animate-pulse text-tertiary' : ''}`}>{simText.icon}</span>
                <span>{simText.label}</span>
              </button>
              <button
                className="px-6 py-2 rounded-full bg-primary-container hover:bg-inverse-primary text-on-primary-container font-label-lg text-label-lg shadow-md hover:shadow-lg transition-all flex items-center gap-2"
                onClick={handleDeploy}
                type="button"
              >
                <span className={`material-symbols-outlined text-[18px] ${deployText.label === 'Validating Rules...' ? 'animate-spin' : ''}`}>{deployText.icon}</span>
                <span>{deployText.label}</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
