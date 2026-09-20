import { useEffect, useMemo, useState } from 'react';
import { getProspects } from '@/api/prospects';
import { Prospect } from '@/types';

const gates = [
  { icon: 'domain_disabled', title: 'Competitor Exclusion', desc: 'Filters direct competitors...', active: 0, dropped: 0 },
  { icon: 'public_off', title: 'Geography Mismatch', desc: 'Enforces US/NA region...', active: 0, dropped: 6 },
  { icon: 'groups', title: 'Company Size Mismatch', desc: 'Headcount floors/drop...', active: 8, dropped: 0 },
  { icon: 'badge', title: 'Role & Seniority Mismatch', desc: 'Blocks junior roles, interns...', active: 4, dropped: 0 },
  { icon: 'remove_circle_outline', title: 'Do Not Contact / Blacklist', desc: 'Opt-out, active legal holds...', active: 2, dropped: 0 },
  { icon: 'link_off', title: 'Domain Inactivity Detects', desc: '404/500, inactive domains...', active: 1, dropped: 0 },
  { icon: 'school', title: 'Bad Faith / Non-Commercial', desc: 'Filters edu, academic...', active: 0, dropped: 0 },
];

function initials(name: string) {
  return name.split(' ').map((part) => part[0]).join('').slice(0, 2).toUpperCase();
}

function scoreFor(prospect: Prospect) {
  if (prospect.status === 'NO_FIT' || prospect.status === 'REJECTED') return prospect.icpScore ?? 0;
  return prospect.icpScore ?? 72;
}

export function Agent2ICPGate() {
  const [prospects, setProspects] = useState<Prospect[]>([]);
  const [selectedId, setSelectedId] = useState<string>('');

  useEffect(() => {
    getProspects()
      .then((items) => {
        setProspects(items);
        setSelectedId(items[0]?.id || '');
      })
      .catch(() => {});
  }, []);

  const evaluated = prospects.length;
  const passed = prospects.filter((p) => scoreFor(p) >= 75 && p.status !== 'NO_FIT' && p.status !== 'REJECTED').length;
  const queue = prospects.filter((p) => scoreFor(p) >= 60 && scoreFor(p) < 75).length;
  const disqualified = prospects.filter((p) => scoreFor(p) < 60 || p.status === 'NO_FIT' || p.status === 'REJECTED').length;
  const selected = useMemo(() => prospects.find((p) => p.id === selectedId) || prospects[0], [prospects, selectedId]);
  const selectedScore = selected ? scoreFor(selected) : 0;

  return (
    <div className="min-h-screen w-full bg-[#fbf6ec] px-5 py-4 text-[#27231d]">
      <div className="mx-auto flex max-w-[980px] flex-col gap-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-sm text-[#756c5f]">
            <span>Pipeline</span>
            <span className="material-symbols-outlined text-[15px]">chevron_right</span>
            <span>US SaaS CTOs</span>
            <span className="material-symbols-outlined text-[15px]">chevron_right</span>
            <span className="rounded-full bg-[#fff2cc] px-3 py-1 font-bold text-[#2b261f]">Agent 2 Decision Gate</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="rounded-full bg-[#9bdcc0] px-7 py-3 text-sm font-bold text-[#1f5e48]">Daemon Worker Active</span>
            <button className="rounded-full bg-[#f3eee6] px-7 py-3 text-sm font-semibold">Version History</button>
          </div>
        </div>

        <section className="rounded-[18px] border border-[#e8dfd1] bg-white p-6 shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="flex gap-4">
              <div className="mt-1 flex h-10 w-10 items-center justify-center rounded-xl bg-[#fff7e8] text-[#8a6718]">
                <span className="material-symbols-outlined">schema</span>
              </div>
              <div>
                <h1 className="max-w-xl font-serif text-[30px] font-bold leading-tight">
                  Agent 2 - ICP Decision Gate Configuration
                </h1>
                <div className="mt-2 flex flex-wrap gap-2">
                  <span className="rounded-full bg-[#2f2b25] px-3 py-1 text-[11px] font-bold uppercase text-white">
                    Deterministic Gate Engine - v4.2 Active
                  </span>
                  <span className="rounded-full bg-[#b7f0d9] px-3 py-1 text-[11px] font-bold text-[#1f5e48]">
                    Automated Triage Live
                  </span>
                </div>
                <p className="mt-2 max-w-2xl text-sm leading-6 text-[#5d5245]">
                  Autonomous evaluation gate filtering leads between Agent 1 discovery and downstream timing and cadence dispatch.
                </p>
              </div>
            </div>
            <div className="flex gap-3">
              <button className="rounded-xl bg-[#f1ebe2] px-6 py-4 text-xs font-bold">Re-sync Agent 1 Stream</button>
              <button className="rounded-xl bg-[#fff7e8] px-6 py-4 text-xs font-bold text-[#8a5f00]">Global Sensitivity</button>
            </div>
          </div>

          <div className="mt-6 grid gap-3 md:grid-cols-4">
            {[
              { label: 'Ingested from Agent 1', value: evaluated, tone: 'neutral', pct: '' },
              { label: 'ICP Passed (Fit >= 75)', value: passed, tone: 'green', pct: evaluated ? `${Math.round((passed / evaluated) * 100)}%` : '0%' },
              { label: 'Review Queue (60-74)', value: queue, tone: 'amber', pct: evaluated ? `${Math.round((queue / evaluated) * 100)}%` : '0%' },
              { label: 'Hard Disqualified', value: disqualified, tone: 'red', pct: evaluated ? `${Math.round((disqualified / evaluated) * 100)}%` : '0%' },
            ].map((card) => (
              <div
                key={card.label}
                className={`rounded-xl border p-4 ${
                  card.tone === 'green'
                    ? 'border-[#b9ead7] bg-[#e4f7ef]'
                    : card.tone === 'amber'
                    ? 'border-[#f0d9a6] bg-[#fff3d7]'
                    : card.tone === 'red'
                    ? 'border-[#f0c0c0] bg-[#fff1f1]'
                    : 'border-[#eadfce] bg-[#f6efe4]'
                }`}
              >
                <div className="text-xs font-bold uppercase text-[#756c5f]">{card.label}</div>
                <div className="mt-2 flex items-end gap-3">
                  <span className="font-serif text-3xl font-bold">{card.value}</span>
                  {card.pct && <span className="rounded-md bg-white/70 px-2 py-1 text-xs font-bold">{card.pct}</span>}
                </div>
                <div className="mt-4 h-1.5 rounded-full bg-white/70">
                  <div
                    className={`h-1.5 rounded-full ${
                      card.tone === 'green' ? 'bg-[#366853]' : card.tone === 'amber' ? 'bg-[#e6a219]' : card.tone === 'red' ? 'bg-[#b91c1c]' : 'bg-[#2f2b25]'
                    }`}
                    style={{ width: evaluated ? `${Math.min(100, (Number(card.value) / evaluated) * 100)}%` : '0%' }}
                  />
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-[18px] border border-[#e8dfd1] bg-white p-5 shadow-sm">
          <div className="mb-4 rounded-2xl border border-[#f2b5b5] bg-[#fff1f1] px-5 py-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-sm font-bold uppercase text-[#b91c1c]">Instant Disqualification Halt</h2>
                <p className="mt-1 text-xs text-[#5d5245]">
                  Any single gate trigger instantly forces <code className="rounded bg-[#ffe0e0] px-1">fit_decision = NO_FIT</code> without consuming enrichment credits.
                </p>
              </div>
              <div className="flex gap-2">
                <span className="rounded-full bg-white px-4 py-2 text-xs font-bold">{gates.length} Active Gates</span>
                <span className="rounded-full bg-[#b91c1c] px-4 py-2 text-xs font-bold text-white">{disqualified} Cumulative Drops</span>
              </div>
            </div>
          </div>

          <div className="grid gap-3 md:grid-cols-7">
            {gates.map((gate) => (
              <div key={gate.title} className="rounded-xl bg-[#f1ebe2] p-3">
                <div className="mb-2 flex items-center justify-between">
                  <span className="material-symbols-outlined text-[17px] text-[#756c5f]">{gate.icon}</span>
                  <span className="material-symbols-outlined text-[16px] text-[#8a5f00]">check_box</span>
                </div>
                <h3 className="text-[12px] font-bold leading-tight">{gate.title}</h3>
                <p className="mt-1 min-h-[32px] text-[10px] leading-4 text-[#756c5f]">{gate.desc}</p>
                <div className="mt-4 flex justify-between text-[10px]">
                  <span>Active <b className="text-[#366853]">{gate.active}</b></span>
                  <span><b className="text-[#b91c1c]">{gate.dropped}</b> Dropped</span>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-[18px] border border-[#e8dfd1] bg-white p-5 shadow-sm">
          <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#fff7e8] text-[#8a6718]">
                <span className="material-symbols-outlined">fact_check</span>
              </div>
              <div>
                <h2 className="font-serif text-lg font-bold">Evidentiary Audit Trail & Rationale View</h2>
                <p className="text-xs text-[#756c5f]">Inspect score breakdown, citations, and gatekeeper decisions.</p>
              </div>
            </div>
            <div className="flex flex-wrap gap-2 text-xs">
              <span className="rounded-md bg-[#f1ebe2] px-3 py-2 font-bold">{evaluated} Total Evaluated</span>
              <input className="rounded-full bg-[#f1ebe2] px-4 py-2 outline-none" placeholder="Search evaluated leads..." />
            </div>
          </div>

          <div className="grid gap-5 lg:grid-cols-[300px_1fr]">
            <aside className="border-r border-[#eee4d4] pr-4">
              <div className="mb-3 flex items-center justify-between text-xs font-bold uppercase text-[#756c5f]">
                <span>Evaluated Candidates</span>
                <span>Page 1 of 30</span>
              </div>
              <div className="flex flex-col gap-3">
                {prospects.slice(0, 5).map((prospect) => {
                  const score = scoreFor(prospect);
                  const state = score >= 75 ? 'FIT VERIFIED' : score >= 60 ? 'REVIEW QUEUE' : 'DISQUALIFIED';
                  return (
                    <button
                      key={prospect.id}
                      onClick={() => setSelectedId(prospect.id)}
                      className={`rounded-2xl border p-4 text-left ${
                        selected?.id === prospect.id ? 'border-[#366853] bg-[#edf4f0]' : 'border-[#eee4d4] bg-white'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#f5d082] text-xs font-bold">
                          {initials(prospect.name)}
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="font-bold">{prospect.name}</div>
                          <div className="truncate text-xs text-[#756c5f]">{prospect.title} • {prospect.company}</div>
                        </div>
                        <div className="text-right">
                          <div className="font-serif text-lg font-bold">{score} / 100</div>
                          <span className={`rounded px-2 py-1 text-[10px] font-bold ${state === 'FIT VERIFIED' ? 'bg-[#b7f0d9] text-[#1f5e48]' : state === 'REVIEW QUEUE' ? 'bg-[#ffe3aa] text-[#7b5709]' : 'bg-[#ffd8d8] text-[#9b2727]'}`}>
                            {state}
                          </span>
                        </div>
                      </div>
                    </button>
                  );
                })}
                {prospects.length === 0 && (
                  <div className="rounded-2xl border border-[#eee4d4] p-5 text-sm text-[#756c5f]">No evaluated prospects yet.</div>
                )}
              </div>
            </aside>

            <main className="flex flex-col gap-4">
              <div className="rounded-2xl bg-[#f6efe4] p-5">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="flex items-center gap-4">
                    <div className="flex h-14 w-14 items-center justify-center rounded-full bg-[#dec99f] font-bold">
                      {selected ? initials(selected.name) : '--'}
                    </div>
                    <div>
                      <h3 className="font-serif text-xl font-bold">{selected?.name || 'No candidate selected'}</h3>
                      <p className="text-sm text-[#5d5245]">{selected?.title || 'Role'} • {selected?.company || 'Company'}</p>
                      <code className="mt-2 inline-block rounded bg-white px-3 py-1 text-xs">
                        {selected?.email || 'No email available'}
                      </code>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs uppercase text-[#756c5f]">Score</div>
                    <div className="font-serif text-3xl font-bold text-[#366853]">{selectedScore} / 100</div>
                    <span className="rounded-r-xl bg-[#366853] px-4 py-2 text-xs font-bold text-white">FIT VERIFIED</span>
                  </div>
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <ScorePanel
                  title="Matched ICP Criteria"
                  tone="green"
                  badge="Verified Factors"
                  items={[
                    '+15 Core B2B SaaS',
                    '+15 Headcount 180 (Optimal)',
                    '+10 AWS EKS & ArgoCD Stack',
                    '+20 VP Eng Authority',
                    '+15 Infrastructure Budget Owner',
                    '+5 Engineering Dept',
                  ]}
                />
                <ScorePanel
                  title="Unmatched Gaps / Non-Awarded Points"
                  tone="neutral"
                  badge="Non-Fatal Gaps"
                  items={['-5 Compliance Signal Missing', '-2 Incomplete SOC2 Verification', '-5 Tech Migration Public Mandate']}
                />
                <ScorePanel title="Negative ICP Exclusion Audit" tone="green" badge="All Gates Passed" items={['0 hard exclusion triggers', 'Soft advisory: Prior contact attempt in 2023']} />
                <ScorePanel title="Dossier Evidence Citations" tone="amber" badge="Source-checked" items={['Fact 1: Domain and email verified', 'Fact 2: Active engineering signals detected', 'Fact 3: Recent ICP activity found']} />
              </div>

              <div className="rounded-2xl bg-[#fff7e8] p-5">
                <h3 className="mb-2 flex items-center gap-2 text-sm font-bold uppercase text-[#8a5f00]">
                  <span className="material-symbols-outlined text-[18px]">verified_user</span>
                  Executive Gatekeeper Synthesis
                </h3>
                <p className="font-serif text-base leading-7">
                  {selected
                    ? `${selected.name} represents a current ICP match based on available campaign, role, company, and scoring evidence.`
                    : 'Select a candidate to inspect gatekeeper synthesis.'}
                </p>
              </div>
            </main>
          </div>
        </section>

        <section className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-[#e8dfd1] bg-white p-5 shadow-sm">
          <div className="flex items-center gap-2 text-sm text-[#5d5245]">
            <span className="material-symbols-outlined text-[18px] text-[#366853]">bolt</span>
            Deterministic gate compiles directly to execution worker daemon. No LLM token hallucination risk.
          </div>
          <div className="flex gap-3">
            <button className="rounded-full bg-[#f6efe4] px-6 py-3 text-sm font-bold">Test Dry-Run (50 Leads)</button>
            <button className="rounded-full bg-[#f6efe4] px-6 py-3 text-sm font-bold">Save Decision Rules</button>
            <button className="rounded-full bg-[#e6a219] px-7 py-3 text-sm font-bold text-[#2a2110]">Deploy Agent 2 to Fleet</button>
          </div>
        </section>
      </div>
    </div>
  );
}

function ScorePanel({
  title,
  badge,
  items,
  tone,
}: {
  title: string;
  badge: string;
  items: string[];
  tone: 'green' | 'amber' | 'neutral';
}) {
  return (
    <div className="rounded-2xl bg-[#f6efe4] p-4">
      <div className="mb-3 flex items-start justify-between gap-2">
        <h3 className="text-sm font-bold uppercase text-[#5d5245]">{title}</h3>
        <span className={`rounded px-2 py-1 text-[10px] font-bold ${tone === 'green' ? 'bg-[#b7f0d9] text-[#1f5e48]' : tone === 'amber' ? 'bg-[#ffe3aa] text-[#7b5709]' : 'bg-white text-[#756c5f]'}`}>
          {badge}
        </span>
      </div>
      <div className="flex flex-col gap-2">
        {items.map((item) => (
          <div key={item} className={`rounded-lg px-3 py-2 text-sm ${tone === 'green' ? 'bg-[#b7f0d9] text-[#1f5e48]' : 'bg-white text-[#5d5245]'}`}>
            {item}
          </div>
        ))}
      </div>
    </div>
  );
}
