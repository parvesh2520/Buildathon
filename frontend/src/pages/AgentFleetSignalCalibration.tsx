import { useState } from 'react';

const personaRows = [
  {
    name: 'CTO / VP Engineering',
    sub: 'Technical Peer Profile',
    selected: true,
    chips: ['Direct / Code', 'Fluff 0%', 'PR Commit Lag', 'Soft Async CTA'],
  },
  {
    name: 'Head of Infra',
    sub: 'Reliability & SLA Owner',
    selected: false,
    chips: ['Pragmatic Ops', 'No Buzzwords', 'Runner Queue SLA', 'Friction Audit'],
  },
  {
    name: 'Founder / CEO',
    sub: 'Bottom-Line Impact',
    selected: false,
    chips: ['Concise ROI', 'Ultra Punchy', 'ARR / Dev Speed', '2-Min Breakdown'],
  },
];

function MetricTile({
  icon,
  label,
  value,
  green = false,
}: {
  icon: string;
  label: string;
  value: string;
  green?: boolean;
}) {
  return (
    <div className={`rounded-xl border p-4 ${green ? 'border-[#83d9ba] bg-[#c9f3e2]' : 'border-[#e8dfd1] bg-[#f6efe4]'}`}>
      <div className="mb-2 flex items-center gap-2 text-[11px] font-bold uppercase tracking-wide text-[#756c5f]">
        <span className="material-symbols-outlined text-[16px]">{icon}</span>
        {label}
      </div>
      <div className="font-serif text-lg font-bold text-[#27231d]">{value}</div>
    </div>
  );
}

export function AgentFleetSignalCalibration() {
  const [wordTarget, setWordTarget] = useState(54);
  const [activeLength, setActiveLength] = useState(55);
  const [channel, setChannel] = useState('Email (Cold)');

  return (
    <div className="min-h-screen w-full bg-[#fbf6ec] px-5 py-4 text-[#27231d]">
      <div className="mx-auto flex max-w-[1080px] flex-col gap-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-sm text-[#756c5f]">
            <span>Workspace</span>
            <span className="material-symbols-outlined text-[15px]">chevron_right</span>
            <span>Outreach Pipeline</span>
            <span className="material-symbols-outlined text-[15px]">chevron_right</span>
            <span className="rounded-full bg-[#f1ebe2] px-3 py-1 font-bold text-[#2b261f]">
              Agent 04 Personalization
            </span>
          </div>
          <div className="flex items-center gap-3">
            <span className="rounded-full bg-[#edf4f0] px-5 py-2 text-sm font-bold text-[#366853]">v4.2-active</span>
            <button className="rounded-xl bg-white px-6 py-2 text-sm font-bold shadow-sm">Dry-Run 10 Drafts</button>
            <button className="rounded-xl bg-[#e6a219] px-7 py-2 text-sm font-bold text-[#2a2110] shadow-sm">
              Deploy Tone Rules
            </button>
          </div>
        </div>

        <section className="rounded-[18px] border border-[#e8dfd1] bg-white p-6 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-5">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl border-2 border-[#8a5f00] bg-[#ffe38f] font-serif text-xl font-bold">
                04
              </div>
              <div>
                <div className="flex flex-wrap items-center gap-3">
                  <h1 className="font-serif text-[27px] font-bold leading-tight">Tone & Personalization Cockpit</h1>
                  <span className="rounded-full bg-[#b7f0d9] px-3 py-1 text-xs font-bold text-[#1f5e48]">LIVE ACTIVE</span>
                </div>
                <p className="mt-1 text-sm text-[#756c5f]">
                  Target Outbound Engine <span className="mx-2">•</span> Brevity Guard v4.2
                </p>
              </div>
            </div>
          </div>

          <div className="mt-5 grid gap-3 md:grid-cols-3">
            <MetricTile icon="straighten" label="Target" value={`${wordTarget}w (Max 65w)`} />
            <MetricTile icon="settings_suggest" label="Guardrail" value="0 Fluff Enforced" green />
            <MetricTile icon="psychology" label="Parity" value="98.2% Human" green />
          </div>
        </section>

        <div className="grid gap-5 lg:grid-cols-[1fr_390px]">
          <main className="flex flex-col gap-5">
            <section className="rounded-[18px] border border-[#e8dfd1] bg-white p-5 shadow-sm">
              <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <span className="rounded-md bg-[#fff2cc] px-3 py-1 text-xs font-bold uppercase">Section 01</span>
                  <h2 className="font-serif text-lg font-bold">Brevity Target & Length Bounds</h2>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm text-[#756c5f]">Ceiling:</span>
                  <span className="rounded-md bg-[#ffe38f] px-4 py-2 text-sm font-bold">{wordTarget} / 65 words</span>
                </div>
              </div>

              <div className="grid gap-3 md:grid-cols-3">
                {[35, 55, 75].map((length) => (
                  <button
                    key={length}
                    onClick={() => {
                      setActiveLength(length);
                      setWordTarget(length === 75 ? 65 : length - 1);
                    }}
                    className={`rounded-2xl border p-5 text-left ${
                      activeLength === length ? 'border-[#8a5f00] bg-white shadow-sm' : 'border-[#e8dfd1] bg-[#f6efe4]'
                    }`}
                  >
                    <div className="mb-3 flex items-center justify-between">
                      <span className={`h-5 w-5 rounded-full border-2 ${activeLength === length ? 'border-[#8a5f00] bg-[#8a5f00]' : 'border-[#cfc5b6]'}`} />
                      <span className="rounded bg-[#e9e1d6] px-2 py-1 text-[10px] font-bold">
                        {length === 35 ? 'SMS / DM' : length === 55 ? 'ACTIVE' : 'ADVISORY'}
                      </span>
                    </div>
                    <div className="font-serif text-2xl font-bold">{length} <span className="text-sm font-normal text-[#756c5f]">words</span></div>
                    <p className="mt-1 text-sm font-semibold text-[#756c5f]">
                      {length === 35 ? 'Ultra Punchy' : length === 55 ? 'Optimal Cold Peer' : 'Consultative'}
                    </p>
                  </button>
                ))}
              </div>

              <div className="mt-5 rounded-2xl bg-[#f1ebe2] p-4">
                <div className="mb-3 flex items-center justify-between">
                  <span className="flex items-center gap-2 font-bold">
                    <span className="material-symbols-outlined rounded bg-[#3f7f6a] p-0.5 text-[16px] text-white">check</span>
                    Mobile Viewport Safe
                  </span>
                  <span className="font-bold text-[#366853]">{wordTarget}w (83% Density)</span>
                </div>
                <div className="h-3 rounded-full bg-[#e5ddd1]">
                  <div className="h-3 rounded-full bg-[#8a5f00]" style={{ width: `${Math.min(100, (wordTarget / 65) * 100)}%` }} />
                </div>
                <div className="mt-2 flex justify-between text-xs text-[#756c5f]">
                  <span>0w Min</span>
                  <span>55w Target</span>
                  <span>65w Hard Stop</span>
                </div>
              </div>

              <div className="mt-5 grid gap-3 md:grid-cols-4">
                {['0 Exclamations', 'Plaintext Only', 'Lowercase Subj', 'Neutral Tone'].map((rule) => (
                  <div key={rule} className="rounded-xl border border-[#6ee7bd] bg-[#c8f7e4] p-4">
                    <div className="mb-3 flex items-center justify-between">
                      <span className="font-serif text-xl font-bold">{rule.split(' ')[0]}</span>
                      <span className="material-symbols-outlined rounded bg-[#3f7f6a] text-[16px] text-white">check</span>
                    </div>
                    <div className="font-bold">{rule.replace(rule.split(' ')[0], '').trim() || 'Exclamations'}</div>
                    <div className="mt-3 text-[11px] font-bold uppercase text-[#1f5e48]">
                      {rule === '0 Exclamations' ? 'Zero allowed' : rule === 'Plaintext Only' ? 'Strip divs/html' : rule === 'Lowercase Subj' ? 'Casual peer' : 'No competitor smear'}
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <section className="rounded-[18px] border border-[#e8dfd1] bg-white p-5 shadow-sm">
              <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <span className="rounded-md bg-[#f1ebe2] px-3 py-1 text-xs font-bold uppercase">Section 02</span>
                  <h2 className="font-serif text-lg font-bold">Persona Syntax & Tone Matrix</h2>
                </div>
                <span className="rounded-full bg-[#b7f0d9] px-4 py-2 text-xs font-bold text-[#1f5e48]">3 Personas Ready</span>
              </div>

              <div className="flex flex-col gap-3">
                {personaRows.map((persona) => (
                  <div
                    key={persona.name}
                    className={`rounded-2xl border p-5 ${persona.selected ? 'border-[#8a5f00] bg-white' : 'border-[#e8dfd1] bg-[#f6efe4]'}`}
                  >
                    <div className="flex flex-wrap items-center gap-4">
                      <span className={`h-6 w-6 rounded-full border-2 ${persona.selected ? 'border-[#8a5f00] bg-[#8a5f00]' : 'border-[#cfc5b6]'}`} />
                      <div className="w-36">
                        <div className="font-bold leading-tight">{persona.name}</div>
                        <div className="mt-1 text-xs text-[#756c5f]">{persona.sub}</div>
                      </div>
                      <div className="flex flex-1 flex-wrap gap-2">
                        {persona.chips.map((chip, index) => (
                          <span
                            key={chip}
                            className={`rounded-md px-3 py-1 text-xs font-bold ${
                              persona.selected && index === 1
                                ? 'bg-[#b7f0d9] text-[#1f5e48]'
                                : persona.selected && index === 3
                                ? 'bg-[#ffe3aa] text-[#7b5709]'
                                : 'bg-[#eee7dc] text-[#3f372f]'
                            }`}
                          >
                            {chip}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-5 flex flex-wrap items-center gap-4">
                <span className="text-lg font-bold uppercase text-[#756c5f]">Empathy Ratio:</span>
                <span className="rounded-md bg-[#ffe38f] px-4 py-1 font-bold">82%</span>
                <div className="h-3 min-w-[230px] flex-1 rounded-full bg-[#e6dfd4]">
                  <div className="h-3 rounded-full bg-gradient-to-r from-[#8a5f00] to-[#6aa985]" style={{ width: '82%' }} />
                </div>
                <span className="text-sm font-bold text-[#366853]">Engineer Peer Respect</span>
              </div>
            </section>
          </main>

          <aside className="flex flex-col gap-5">
            <section className="rounded-[18px] border border-[#e8dfd1] bg-white p-5 shadow-sm">
              <div className="mb-5 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="rounded-md bg-[#f1ebe2] px-3 py-2 text-xs font-bold uppercase">Section 03</span>
                  <h2 className="font-serif text-lg font-bold">Channel Selection & Syntax</h2>
                </div>
                <span className="rounded-md bg-[#f1ebe2] px-3 py-2 text-xs font-bold uppercase">Engine v4</span>
              </div>

              <div className="grid grid-cols-3 gap-3">
                {['Email (Cold)', 'LinkedIn DM', 'WhatsApp'].map((item) => (
                  <button
                    key={item}
                    onClick={() => setChannel(item)}
                    className={`rounded-xl border p-4 text-left ${channel === item ? 'border-[#8a5f00] bg-white' : 'border-[#e8dfd1] bg-[#f6efe4]'}`}
                  >
                    <div className="mb-4 flex items-center justify-between">
                      <span className="material-symbols-outlined text-[17px]">{item.startsWith('Email') ? 'mail' : item.startsWith('LinkedIn') ? 'chat' : 'sms'}</span>
                      <span className={`h-4 w-4 rounded border ${channel === item ? 'bg-[#8a5f00]' : 'bg-white'}`} />
                    </div>
                    <div className="font-bold">{item}</div>
                    <div className="mt-1 text-xs text-[#756c5f]">{channel === item ? 'Active Tab' : 'Ready'}</div>
                  </button>
                ))}
              </div>

              <div className="mt-4 grid grid-cols-2 gap-3">
                {['No Tracking Pixels', 'Lowercase Subject'].map((rule) => (
                  <div key={rule} className="flex items-center gap-2 rounded-xl bg-[#c8f7e4] px-4 py-3 text-sm font-bold text-[#1f5e48]">
                    <span className="material-symbols-outlined rounded bg-[#3f7f6a] text-[15px] text-white">check</span>
                    {rule}
                  </div>
                ))}
              </div>
            </section>

            <section className="rounded-[18px] border border-[#e8dfd1] bg-white p-5 shadow-sm">
              <div className="mb-5 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="rounded-md bg-[#c8f7e4] px-3 py-2 text-xs font-bold uppercase text-[#1f5e48]">
                    Section 04
                  </span>
                  <h2 className="font-serif text-lg font-bold">Live Inspector & Entities</h2>
                </div>
                <span className="rounded-lg bg-[#f6efe4] px-4 py-3 text-xs">
                  Target: <b>Alex Vance</b>
                </span>
              </div>

              <div className="mb-4 flex items-center justify-between rounded-xl bg-[#f6efe4] px-4 py-3">
                <span className="text-xs font-bold uppercase text-[#756c5f]">Subject:</span>
                <b>quick note on your ci build</b>
                <span className="rounded-full bg-[#b7f0d9] px-3 py-1 text-xs font-bold text-[#1f5e48]">PASS 100%</span>
              </div>

              <div className="rounded-2xl border border-[#e8dfd1] bg-[#f8f3eb] p-5 font-serif text-lg leading-8">
                <p>
                  Alex — noticed your team’s{' '}
                  <span className="rounded-md border border-[#e6a219] bg-[#fff2cc] px-2 py-1 font-bold text-[#7b5709]">
                    Go migration
                  </span>{' '}
                  and recent PR commits targeting the{' '}
                  <span className="rounded-md bg-[#c8f7e4] px-2 py-1 font-bold text-[#1f5e48]">38m build bottleneck</span>.
                  We helped Northwind cut test runner queues by 54% without touching their repo configuration.
                </p>
                <p className="mt-3 rounded-md border border-[#7dd3fc] bg-[#dff4ff] px-3 py-2 font-sans text-base font-bold text-[#0f4a6a]">
                  Open to seeing the 2-minute breakdown?
                </p>
                <div className="mt-5 flex items-center justify-between text-sm text-[#756c5f]">
                  <span>— Ramya (via Nectar Engine)</span>
                  <span className="rounded bg-[#eee7dc] px-3 py-2 text-xs">134ms • Claude 3.5 Sonnet</span>
                </div>
              </div>

              <div className="mt-4 grid grid-cols-4 gap-3">
                {[
                  ['Words', '48w', 'bg-[#f6efe4]'],
                  ['Fluff', '0 Clean', 'bg-[#c8f7e4]'],
                  ['Grade', '7.2', 'bg-[#f6efe4]'],
                  ['Parity', '98.2%', 'bg-[#b7f0d9]'],
                ].map(([label, value, bg]) => (
                  <div key={label} className={`rounded-xl ${bg} p-3 text-center`}>
                    <div className="text-xs font-bold uppercase text-[#756c5f]">{label}</div>
                    <div className="font-serif text-lg font-bold">{value}</div>
                  </div>
                ))}
              </div>
            </section>
          </aside>
        </div>
      </div>
    </div>
  );
}
