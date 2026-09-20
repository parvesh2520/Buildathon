import { useEffect, useMemo, useState } from 'react';
import { getCampaigns } from '@/api/campaigns';
import { getProspects } from '@/api/prospects';
import { Campaign, Prospect } from '@/types';

const locations = ['San Francisco Bay Area', 'Remote (US)'];
const titles = ['CTO', 'VP Engineering', 'Head of Platform'];
const seniority = ['C-Level / Exec', 'VP / Director', 'Staff / Principal', 'Lead Engineer'];
const stack = ['Cloud Native', 'Kubernetes', 'Go / Rust'];
const industries = ['B2B SaaS', 'Developer Tools', 'Cloud Infrastructure'];
const exclusions = ['Datadog', 'competitor.io', 'stealth.ai'];

function initials(name: string) {
  return name.split(' ').map((part) => part[0]).join('').slice(0, 2).toUpperCase();
}

function FilterBlock({
  title,
  hint,
  items,
  warm = false,
  green = false,
  wide = false,
}: {
  title: string;
  hint?: string;
  items: string[];
  warm?: boolean;
  green?: boolean;
  wide?: boolean;
}) {
  return (
    <div className={`rounded-xl bg-[#f1ebe2] p-3 ${wide ? 'min-h-[74px]' : ''}`}>
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-[12px] font-bold">{title}</h3>
        {hint && <span className="text-xs text-[#756c5f]">{hint}</span>}
      </div>
      <div className="flex flex-wrap gap-2">
        {items.map((item) => (
          <span
            key={item}
            className={`rounded-full px-3 py-1 text-sm font-semibold ${
              green
                ? 'bg-[#b7f0d9] text-[#1f5e48]'
                : warm
                ? 'bg-[#f5d082] text-[#5c430a]'
                : 'bg-white text-[#2f2a23]'
            }`}
          >
            {item} x
          </span>
        ))}
      </div>
    </div>
  );
}

export function Agent0SourcingScout() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [prospects, setProspects] = useState<Prospect[]>([]);
  const [targetCount, setTargetCount] = useState(150);
  const [activeCampaignId, setActiveCampaignId] = useState('');

  useEffect(() => {
    getCampaigns()
      .then((items) => {
        setCampaigns(items);
        setActiveCampaignId(items.find((c) => c.status === 'LIVE')?.id || items[0]?.id || '');
      })
      .catch(() => {});

    getProspects().then(setProspects).catch(() => {});
  }, []);

  const activeCampaign = campaigns.find((campaign) => campaign.id === activeCampaignId);
  const campaignProspects = useMemo(
    () =>
      prospects.filter(
        (prospect) =>
          !activeCampaignId ||
          prospect.campaign_id === activeCampaignId ||
          prospect.campaignId === activeCampaignId
      ),
    [activeCampaignId, prospects]
  );

  const shortlist = campaignProspects
    .filter((prospect) => (prospect.icpScore ?? 0) >= 60 || ['FIT', 'DISCOVERED', 'CONTACTED'].includes(prospect.status || ''))
    .slice(0, 5);

  const droppedCount = Math.max(campaignProspects.length - shortlist.length, 0);

  return (
    <div className="min-h-screen w-full bg-[#fbf6ec] px-5 py-4 text-[#27231d]">
      <div className="mx-auto flex max-w-[980px] flex-col gap-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-sm text-[#756c5f]">
            <span>Workspace</span>
            <span className="material-symbols-outlined text-[15px]">chevron_right</span>
            <span>Outreach Pipeline</span>
            <span className="material-symbols-outlined text-[15px]">chevron_right</span>
            <span className="rounded-full bg-[#fff2cc] px-3 py-1 font-bold text-[#2b261f]">
              Agent 0: Sourcing Scout
            </span>
          </div>
        </div>

        <section className="rounded-[18px] border border-[#e8dfd1] bg-white p-6 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-[#2f2b25]">
              <span className="material-symbols-outlined text-[27px] text-[#e6a219]">radar</span>
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-3">
                <h1 className="font-serif text-[24px] font-bold leading-tight">Agent 0: Sourcing Scout Cockpit</h1>
                <span className="rounded-full bg-[#ffe3aa] px-3 py-1 text-[11px] font-bold uppercase text-[#7b5709]">
                  Autonomous Ingestion Engine - v4.3 Live
                </span>
              </div>
              <span className="mt-2 inline-flex items-center gap-1.5 rounded-full bg-[#dff2e9] px-3 py-1 text-xs font-bold text-[#366853]">
                <span className="material-symbols-outlined text-[14px]">verified_user</span>
                Proof Verification Active
              </span>
              <p className="mt-2 max-w-4xl text-[13px] leading-5 text-[#5d5245]">
                Synthesizes continuous boolean search queries across GitHub repositories, LinkedIn cache, and funding
                signals. Applies Tier-0 scoring with real-time anti-hallucination evidence gates.
              </p>
            </div>
          </div>
        </section>

        <section className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-[#e8dfd1] bg-white p-4 shadow-sm">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#fff7e8] text-[#8a6718]">
              <span className="material-symbols-outlined">flag</span>
            </div>
            <span className="text-xs font-bold uppercase tracking-wide text-[#756c5f]">Target Campaign</span>
            <select
              value={activeCampaignId}
              onChange={(event) => setActiveCampaignId(event.target.value)}
              className="rounded-full bg-[#f6efe4] px-4 py-2 text-sm font-bold outline-none"
            >
              {campaigns.map((campaign) => (
                <option key={campaign.id} value={campaign.id}>
                  {campaign.name} {campaign.status === 'LIVE' ? '(Active)' : ''}
                </option>
              ))}
            </select>
            <span className="rounded-full bg-[#ffe3aa] px-3 py-1 text-xs font-bold text-[#7b5709]">
              Live Scout Targeting
            </span>
          </div>
          <button className="rounded-full bg-[#f6efe4] px-5 py-2 text-xs font-bold text-[#2f2a23]">
            + New Campaign
          </button>
        </section>

        <section className="grid gap-5 rounded-[18px] border border-[#e8dfd1] bg-white p-5 shadow-sm lg:grid-cols-[1fr_230px]">
          <div>
            <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#fff7e8] text-[#8a6718]">
                  <span className="material-symbols-outlined">tune</span>
                </div>
                <div>
                  <h2 className="font-serif text-base font-bold">Filter & Ingestion Configuration</h2>
                  <p className="text-xs text-[#6b5f52]">
                    Define targeting vectors, exclusions, and output volume quota for Agent 0.
                  </p>
                </div>
              </div>
              <div className="flex gap-2">
                <button className="rounded-lg bg-[#f6efe4] px-5 py-2.5 text-xs font-semibold">Save Filter Preset</button>
                <button className="rounded-lg bg-[#8a5f00] px-5 py-2.5 text-xs font-bold text-white">
                  Apply Filters & Rerun Scout
                </button>
              </div>
            </div>

            <div className="mb-3 flex items-center justify-between text-xs font-bold uppercase tracking-wide">
              <span className="flex items-center gap-1 text-[#8a5f00]">
                <span className="material-symbols-outlined text-[14px]">manage_search</span>
                Search & Filter Criteria
              </span>
              <span className="text-[#8a5f00]">Advanced Boolean Operators</span>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <FilterBlock title="Location / Geography" hint="Geo-fence" items={locations} />
              <FilterBlock title="Target Job Titles & Roles" hint="Exact Match" items={titles} warm />
              <FilterBlock title="Seniority / Position Level" items={seniority} />
              <FilterBlock title="Tech Stack & Keywords" hint="Repo / Code signals" items={stack} green />
              <div className="md:col-span-2">
                <FilterBlock title="Industry & Sub-Industry" hint="Taxonomy & Signals" items={industries} wide />
              </div>
              <div className="md:col-span-2 rounded-xl bg-[#f1ebe2] p-3">
                <div className="mb-3 flex items-center justify-between gap-2">
                  <div>
                    <h3 className="text-sm font-bold text-[#2f2a23]">Excluded Companies / Domains</h3>
                    <p className="text-xs text-[#756c5f]">Block competitors, current customers, or specific accounts</p>
                  </div>
                  <span className="rounded-full bg-[#ffd8d8] px-3 py-1 text-xs font-bold text-[#9b2727]">
                    {exclusions.length} Rules Active
                  </span>
                </div>
                <div className="flex flex-wrap gap-2 rounded-xl bg-white p-2.5">
                  {exclusions.map((item) => (
                    <span key={item} className="rounded-full bg-[#ffe5e5] px-3 py-1 text-xs font-bold text-[#9b2727]">
                      {item} x
                    </span>
                  ))}
                  <input className="min-w-[220px] flex-1 bg-transparent text-sm outline-none" placeholder="Type company name or domain to exclude..." />
                  <button className="rounded-lg bg-[#f6efe4] px-3 py-1 text-xs font-bold">+ Exclude</button>
                </div>
              </div>
            </div>
          </div>

          <aside className="rounded-2xl bg-[#f1ebe2] p-4">
            <div className="rounded-2xl bg-white p-3">
              <div className="mb-4 flex items-center justify-between">
                <span className="text-xs font-bold uppercase text-[#756c5f]">Output Volume & Quota</span>
                <span className="rounded-md bg-[#f5d082] px-2 py-1 text-xs font-bold text-[#7b5709]">Agent 0 Stage</span>
              </div>
              <label className="mb-2 block text-sm font-bold">Candidates to Output</label>
              <input
                type="number"
                value={targetCount}
                onChange={(event) => setTargetCount(Number(event.target.value))}
                className="mb-3 w-full rounded-lg border border-[#e0d5c4] px-3 py-1.5 text-center text-sm font-bold outline-none"
              />
              <div className="mb-4 flex flex-wrap gap-2">
                {[50, 100, 150, 250, 500].map((count) => (
                  <button
                    key={count}
                    onClick={() => setTargetCount(count)}
                  className={`rounded-md px-2.5 py-1.5 text-xs font-bold ${
                      targetCount === count ? 'bg-[#8a5f00] text-white' : 'bg-[#f6efe4] text-[#2f2a23]'
                    }`}
                  >
                    {count}
                  </button>
                ))}
              </div>
              <div className="text-sm font-bold">Ingest Pool Target</div>
              <div className="mt-1 font-serif text-2xl font-bold">{campaignProspects.length}</div>
              <div className="mt-2 h-2 rounded-full bg-[#eadfce]">
                <div
                  className="h-2 rounded-full bg-[#8a5f00]"
                  style={{ width: `${Math.min(100, (shortlist.length / Math.max(targetCount, 1)) * 100)}%` }}
                />
              </div>
              <div className="mt-3 flex justify-between text-xs text-[#756c5f]">
                <span>Top {shortlist.length} passed</span>
                <span>{droppedCount} triaged out</span>
              </div>
            </div>
            <div className="mt-5 rounded-2xl bg-[#efe6d8] p-4 text-xs leading-5 text-[#5d5245]">
              <span className="material-symbols-outlined mr-1 align-middle text-[17px] text-[#366853]">info</span>
              Agent 0 automatically passes qualified candidate batches downstream to Agent 1 upon scout run completion.
            </div>
          </aside>
        </section>

        <section className="rounded-[18px] border border-[#e8dfd1] bg-white p-5 shadow-sm">
          <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-5">
              <h2 className="font-serif text-base font-bold">Top Shortlist Candidates</h2>
              <span className="rounded-full bg-[#f5d082] px-5 py-2 text-xs font-bold text-[#7b5709]">
                {shortlist.length} Ready
              </span>
              <span className="font-serif text-base text-[#756c5f]">Disqualification Audit Log</span>
              <span className="rounded-full bg-[#ffd8d8] px-5 py-2 text-xs font-bold text-[#9b2727]">
                {droppedCount} Dropped
              </span>
            </div>
            <div className="flex gap-2">
              <button className="rounded-lg bg-[#f6efe4] px-5 py-2.5 text-xs font-semibold">Export CSV</button>
              <button className="rounded-lg bg-[#ffd991] px-6 py-2.5 text-xs font-bold">Forward to Agent 1</button>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead>
                <tr className="border-b border-[#eee4d4] text-xs font-bold uppercase tracking-wide text-[#756c5f]">
                  <th className="py-3 pr-4">Candidate & Title</th>
                  <th className="py-3 pr-4">Company & Stage</th>
                  <th className="py-3 pr-4">Headcount & Geo</th>
                  <th className="py-3 pr-4">Tier-0 Score</th>
                  <th className="py-3 pr-4">Evidence Proof Link</th>
                  <th className="py-3">Sourcing Rationale</th>
                </tr>
              </thead>
              <tbody>
                {shortlist.map((prospect) => (
                  <tr key={prospect.id} className="border-b border-[#f1e8da] last:border-0">
                    <td className="py-3 pr-4">
                      <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#f6efe4] text-xs font-bold">
                          {initials(prospect.name)}
                        </div>
                        <div>
                          <div className="font-bold">{prospect.name}</div>
                          <div className="text-sm text-[#756c5f]">{prospect.title || 'Prospect'}</div>
                        </div>
                      </div>
                    </td>
                    <td className="py-3 pr-4">
                      <div className="font-semibold">{prospect.company || 'Company'}</div>
                      <div className="text-sm font-bold text-[#8a5f00]">{activeCampaign?.name || 'Campaign'}</div>
                    </td>
                    <td className="py-3 pr-4">
                      <div>{prospect.companySize || prospect.company_size || 'Unknown size'}</div>
                      <div className="text-sm text-[#756c5f]">{prospect.location || 'Unknown location'}</div>
                    </td>
                    <td className="py-3 pr-4">
                      <span className="rounded-full bg-[#b7f0d9] px-3 py-1 text-sm font-bold text-[#1f5e48]">
                        {prospect.icpScore ?? 0}
                      </span>
                    </td>
                    <td className="py-3 pr-4">
                      <span className="rounded-md bg-[#f6efe4] px-3 py-1 font-mono text-xs">
                        {prospect.linkedin_url || prospect.linkedinUrl || prospect.domain || 'No proof link'}
                      </span>
                    </td>
                    <td className="py-3 text-sm text-[#5d5245]">{prospect.notes || 'Matched current campaign targeting rules.'}</td>
                  </tr>
                ))}
                {shortlist.length === 0 && (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-sm text-[#756c5f]">
                      No qualified candidates found for the selected campaign yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>

        <section className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-[#e8dfd1] bg-[#f6efe4] p-4">
          <div className="flex items-center gap-2 text-sm text-[#5d5245]">
            <span className="material-symbols-outlined text-[18px] text-[#366853]">check_circle</span>
            Autosaved configuration. Agent 0 ready to supply Agent 1.
          </div>
        </section>
      </div>
    </div>
  );
}
