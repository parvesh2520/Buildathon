const recencyWindows = [
  { label: 'LinkedIn Activity TTL', value: '30 Days Max', decay: 'Decay: 30d', active: 'Strict Window', pct: 32 },
  { label: 'Job & Hiring Surges', value: '90 Days Max', decay: 'Decay: 90d', active: 'Active Window', pct: 58 },
  { label: 'Tech Stack / K8s Shift', value: '180 Days (6 mo)', decay: 'Decay: 180d', active: 'Active Window', pct: 72 },
  { label: 'Funding & Leadership', value: '365 Days (12 mo)', decay: 'Decay: 365d', active: 'Active Window', pct: 48 },
];

const pillars = [
  {
    id: 'A',
    title: 'Company Intelligence',
    body: 'Retrieves structural, financial, and detected infrastructure parameters.',
    tags: ['Legal Name & Domain', 'Headcount & Eng Size', 'Funding History & Round', 'Tech Stack (K8s, CI/CD)', 'ARR & Velocity'],
    footer: 'Min Pillar Confidence',
    pct: '85%',
  },
  {
    id: 'B',
    title: 'Person & Leadership',
    body: 'Discovers key champions, mandates, speaking engagements, and pain points.',
    tags: ['Career Trajectory & Past Roles', 'Current Mandates & OKRs', 'LinkedIn Posts & Vents', 'Public Footprint', 'Decision Authority Tier'],
    footer: 'Min Pillar Confidence',
    pct: '90%',
  },
  {
    id: 'C',
    title: 'Casual Link Engine',
    body: 'Synthesizes raw observable company facts into SDR positioning angles.',
    tags: ['Observable Fact', 'Technical Friction', 'SDR High-Yield Value Proposition'],
    footer: 'Mode: Multi-source corroboration',
    pct: 'Strict Lineage',
    gold: true,
  },
  {
    id: 'D',
    title: 'Trigger Classification',
    body: 'Detects high-intent urgency windows and sets triage weights.',
    tags: ['Hiring Surges (<90d)', 'EKS/Cloud Migrations', 'New Exec Transitions', 'Funding Series A-C', 'Audit & Compliance'],
    footer: 'Urgency Weighting',
    pct: 'High / Med',
  },
  {
    id: 'E',
    title: 'CRM & Context Enrichment',
    body: 'Cross-references CRM database to avoid duplicates and map warm intros.',
    tags: ['HubSpot Touch History', 'Domain Do-Not-Contact', '1st-Degree Warm Path', 'DronaHQ Deal Records'],
    footer: 'Bi-directional Sync',
    pct: 'Ready',
  },
  {
    id: 'F',
    title: 'Evidence Gates & Validation',
    body: 'Minimum confidence floor before dossiers route downstream to Agent 2.',
    tags: ['Confidence >= 0.85', 'Anti-Hallucination', 'Route to Human Review'],
    footer: 'Below 0.85:',
    pct: 'Human Review',
    mint: true,
  },
];

const queue = [
  { initials: 'AV', name: 'Alex Vance', role: 'VP Engineering - CloudScale Technologies', urgency: 'HIGH < 30D', trigger: 'Hiring surge for 6 Senior Go & K8s engineers; public LinkedIn vent on slow CI/CD test flakiness.', evidence: 'careers.cloudscale.io (8d ago) + LinkedIn post (12d ago)', score: '0.96', tone: 'photo' },
  { initials: 'ER', name: 'Elena Rostova', role: 'CTO - DevSync Platform', urgency: 'HIGH < 30D', trigger: 'Closed $18M Series A; actively migrating 30 microservices to AWS multi-cluster EKS.', evidence: 'SEC Form D (14d ago) + GitHub public repo commits', score: '0.93' },
  { initials: 'MC', name: 'Marcus Chen', role: 'Head of Infrastructure - DataPulse Analytics', urgency: 'HIGH < 30D', trigger: 'Published public RFC on Terraform state drift and unexpected AWS NAT gateway bill spikes.', evidence: 'Substack Eng Blog (19d ago) + X Tech Thread', score: '0.91' },
  { initials: 'SL', name: 'Sarah Lin', role: 'VP Platform - OmniPay', urgency: 'MEDIUM < 60D', trigger: 'Kubernetes workload migration with upcoming PCI-DSS Level 1 compliance audit deadline.', evidence: 'Fintech Weekly Podcast (42d ago) + Team Job Board', score: '0.88' },
];

function StatCard({ label, value, sub }: { label: string; value: string; sub: string }) {
  return (
    <div className="rounded-2xl bg-[#f6efe4] p-4 shadow-sm">
      <div className="text-[11px] font-bold uppercase tracking-wide text-[#7c7163]">{label}</div>
      <div className="mt-2 font-serif text-3xl font-bold text-[#27231d]">{value}</div>
      <div className="mt-1 text-xs font-semibold text-[#7c7163]">{sub}</div>
    </div>
  );
}

function Toggle() {
  return (
    <div className="flex h-6 w-11 items-center justify-end rounded-full bg-[#3f7f6a] p-1 shadow-inner">
      <span className="h-4 w-4 rounded-full bg-white shadow-sm" />
    </div>
  );
}

export function Agent1DeepResearch() {
  return (
    <div className="min-h-screen w-full bg-[#fbf6ec] px-5 py-5 text-[#27231d]">
      <div className="mx-auto flex max-w-[1120px] flex-col gap-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-sm text-[#756c5f]">
            <span>Workspace</span>
            <span className="material-symbols-outlined text-[15px]">chevron_right</span>
            <span className="font-bold text-[#2b261f]">Outreach Pipeline</span>
          </div>
        </div>

        <section className="rounded-[18px] border border-[#eee4d7] bg-white p-7 shadow-sm">
          <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
            <div>
              <div className="mb-3 flex flex-wrap items-center gap-2">
                <span className="rounded-full bg-[#e6a219] px-3 py-1 text-[11px] font-black uppercase text-[#2c2210]">Agent 01 Architecture</span>
                <span className="rounded-full bg-[#b7f0d9] px-3 py-1 text-xs font-bold text-[#1f5e48]">Autonomous Evidence Synthesis - v4.2 Active</span>
                <span className="rounded-full bg-[#f2eadf] px-3 py-1 text-xs font-bold text-[#5d5246]">Casual Link Engine Enabled</span>
              </div>
              <h1 className="max-w-[650px] font-serif text-[38px] font-bold leading-[0.96] tracking-tight">
                Deep Research &amp; Dossier Configuration Cockpit
              </h1>
              <p className="mt-4 max-w-[640px] text-[15px] leading-6 text-[#655c51]">
                Global extraction rules, 6-pillar intelligence calibration, anti-hallucination gates, and intent trigger governance for all incoming accounts.
              </p>
            </div>
            <div className="grid grid-cols-4 overflow-hidden rounded-2xl border-8 border-[#f6efe4] bg-white">
              <StatCard label="Ingested Fleet" value="150" sub="From Agent 0" />
              <StatCard label="Min Confidence" value="0.85" sub="Threshold Gate" />
              <StatCard label="Active Fields" value="24" sub="Configured Across Pillars" />
              <StatCard label="Casual Bridges" value="148" sub="Ready for Agent 2" />
            </div>
          </div>
        </section>

        <section className="rounded-[18px] border border-[#eee4d7] bg-white p-5 shadow-sm">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="font-serif text-lg font-bold">Global Signal Recency Windows &amp; TTL Calibration</h2>
              <p className="text-sm text-[#6f665b]">Defines freshness decay thresholds across all 150 fleet prospects before signals convert to historical context.</p>
            </div>
            <span className="rounded-full bg-[#edf4f0] px-4 py-2 text-xs font-bold text-[#3f7f6a]">Live Rule Enforced</span>
          </div>
          <div className="grid gap-3 md:grid-cols-4">
            {recencyWindows.map((item) => (
              <div key={item.label} className="rounded-xl bg-[#f6efe4] p-4">
                <div className="flex items-center justify-between gap-2 text-[11px] font-bold uppercase text-[#7c7163]">
                  <span>{item.label}</span>
                  <span>{item.value}</span>
                </div>
                <div className="mt-4 h-2 rounded-full bg-[#e0d6c8]">
                  <div className="h-full rounded-full bg-[#3f7f6a]" style={{ width: `${item.pct}%` }} />
                </div>
                <div className="mt-3 flex justify-between text-xs font-semibold text-[#4d463d]">
                  <span>{item.decay}</span>
                  <span>{item.active}</span>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-4 rounded-xl bg-[#f6efe4] px-4 py-3 text-xs font-semibold text-[#5f5449]">
            <span className="mr-2 uppercase text-[#897c6c]">Policy:</span>
            Downgrade expired signals to historical background. Cross-reference GitHub AST &amp; SEC filings.
          </div>
        </section>

        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <span className="rounded-lg bg-[#e6a219] px-2.5 py-2 text-sm font-black">6P</span>
            <h2 className="font-serif text-[28px] font-bold">Pillar Retrieval Calibration</h2>
            <span className="rounded-full bg-[#f2eadf] px-3 py-1 text-xs font-bold text-[#655c51]">Applies to All Ingested Accounts</span>
          </div>
          <span className="text-xs font-semibold text-[#6f665b]">Enforcing Anti-Hallucination Constraints</span>
        </div>

        <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {pillars.map((pillar) => (
            <article key={pillar.id} className="rounded-[18px] border border-[#eee4d7] bg-white p-5 shadow-sm">
              <div className="mb-4 flex items-start justify-between gap-3">
                <div className="flex items-center gap-3">
                  <span className={`rounded-md px-2.5 py-1 text-xs font-black ${pillar.gold ? 'bg-[#e6a219]' : pillar.mint ? 'bg-[#b7f0d9]' : 'bg-[#f2eadf]'}`}>
                    {pillar.id}
                  </span>
                  <h3 className="font-serif text-lg font-bold leading-tight">{pillar.title}</h3>
                </div>
                <Toggle />
              </div>
              <p className="min-h-[44px] text-sm leading-5 text-[#6f665b]">{pillar.body}</p>
              <div className="mt-4 flex flex-col gap-2">
                {pillar.tags.map((tag, index) => (
                  <span
                    key={tag}
                    className={`rounded-md px-3 py-1.5 text-xs font-bold ${
                      pillar.id === 'D' && index === 0
                        ? 'bg-[#ffe1dd] text-[#9a2922]'
                        : index === 2 && pillar.gold
                          ? 'bg-[#e6a219] text-[#31220a]'
                          : 'bg-[#f6efe4] text-[#4d463d]'
                    }`}
                  >
                    {index + 1 <= 2 && pillar.gold ? `${index + 1}  ` : ''}
                    {tag}
                    {!pillar.gold && index < 4 ? '  ✓' : ''}
                  </span>
                ))}
              </div>
              <div className="mt-6 border-t border-[#eee4d7] pt-4">
                <div className="flex items-center justify-between text-xs font-semibold text-[#6f665b]">
                  <span>{pillar.footer}</span>
                  <span>{pillar.pct}</span>
                </div>
                {!pillar.gold && (
                  <div className="mt-2 h-1.5 rounded-full bg-[#e0d6c8]">
                    <div className="h-full rounded-full bg-[#3f7f6a]" style={{ width: pillar.id === 'B' ? '90%' : pillar.id === 'A' ? '85%' : '76%' }} />
                  </div>
                )}
              </div>
            </article>
          ))}
        </section>

        <section className="rounded-[18px] border border-[#eee4d7] bg-white p-5 shadow-sm">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <h2 className="font-serif text-lg font-bold">High-Urgency Signal Feed &amp; Ingested Profiles (Agent 1 Output Queue)</h2>
            <span className="text-xs font-semibold text-[#6f665b]">Active Fleet: 150 accounts • 4 Priority Signals Ready</span>
          </div>
          <div className="flex flex-col gap-3">
            {queue.map((lead) => (
              <article key={lead.name} className="grid gap-4 rounded-2xl bg-[#f6efe4] p-4 md:grid-cols-[54px_1fr_70px_150px] md:items-center">
                <div className={`flex h-12 w-12 items-center justify-center overflow-hidden rounded-xl font-serif text-lg font-bold text-white ${lead.initials === 'MC' ? 'bg-[#8a5f00]' : lead.initials === 'SL' ? 'bg-[#3f7f6a]' : 'bg-[#25231f]'}`}>
                  {lead.tone === 'photo' ? <span className="material-symbols-outlined text-[28px]">person</span> : lead.initials}
                </div>
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="font-serif text-lg font-bold">{lead.name}</h3>
                    <span className="rounded-full bg-white px-3 py-1 text-xs font-bold text-[#4d463d]">{lead.role}</span>
                    <span className="rounded bg-[#ffe1dd] px-2 py-1 text-[11px] font-black text-[#a52821]">{lead.urgency}</span>
                  </div>
                  <p className="mt-1 text-sm font-semibold text-[#3c352e]">Trigger: {lead.trigger}</p>
                  <p className="mt-1 text-xs text-[#7c7163]">Evidence: {lead.evidence}</p>
                </div>
                <div className="text-center">
                  <div className="font-serif text-2xl font-bold text-[#3f7f6a]">{lead.score}</div>
                  <div className="text-xs font-bold text-[#7c7163]">Score</div>
                </div>
                <div className="text-right">
                  <span className="inline-flex items-center gap-1 rounded-full bg-[#f2eadf] px-3 py-1.5 text-xs font-bold text-[#5d5246]">
                    <span className="material-symbols-outlined text-[15px] text-[#3f7f6a]">check_circle</span>
                    Verified
                  </span>
                </div>
              </article>
            ))}
          </div>
        </section>

        <footer className="flex flex-wrap items-center justify-between gap-4 rounded-[18px] border border-[#eee4d7] bg-white p-5 shadow-sm">
          <div className="flex items-center gap-3 text-sm text-[#6f665b]">
            <span className="material-symbols-outlined text-[18px] text-[#3f7f6a]">verified_user</span>
            Configuration calibrated. Agent 1 ready to process and route all 150 prospects.
          </div>
        </footer>
      </div>
    </div>
  );
}
