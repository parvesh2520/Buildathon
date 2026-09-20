import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { getOperationalControls, toggleKillSwitch } from '@/api/system';
import { getProspects } from '@/api/prospects';

export function Agents() {
  const navigate = useNavigate();

  // Real backend states
  const [killSwitchActive, setKillSwitchActive] = useState(false);
  const [systemStatus, setSystemStatus] = useState('HEALTHY');
  const [liveCampaignsCount, setLiveCampaignsCount] = useState<number>(4);
  const [prospectCount, setProspectCount] = useState<number>(0);
  const [loadingControls, setLoadingControls] = useState(false);

  // Load real operational controls and prospect count from backend
  useEffect(() => {
    async function loadData() {
      try {
        const controls = await getOperationalControls();
        setKillSwitchActive(controls.global_kill_switch);
        setSystemStatus(controls.system_status);
        if (controls.campaign_summary) {
          setLiveCampaignsCount(controls.campaign_summary.live);
        }
      } catch (err) {
        // Fallback gracefully if backend is restarting
      }

      try {
        const prospects = await getProspects();
        setProspectCount(prospects.length);
      } catch (err) {
        // Non-blocking
      }
    }

    loadData();
  }, []);

  const handleToggleKillSwitch = async () => {
    setLoadingControls(true);
    try {
      const nextState = !killSwitchActive;
      const res = await toggleKillSwitch(
        nextState,
        nextState ? 'Halted via Fleet Operations' : undefined
      );
      setKillSwitchActive(res.global_kill_switch);
      setSystemStatus(res.system_status);
      if (nextState) {
        toast.error('Emergency Halt activated. All agent execution paused.');
      } else {
        toast.success('Fleet resumed. All autonomous agents operational.');
      }
    } catch (err: any) {
      toast.error(err.message || 'Failed to toggle kill switch.');
    } finally {
      setLoadingControls(false);
    }
  };

  const agentRoster = [
    {
      num: '#00',
      id: '0',
      name: 'Agent 0: Sourcing Scout',
      role: 'Discovery & Scraping',
      icon: 'person_search',
      accentColor: 'bg-primary-container',
      badgeColor: 'bg-primary-container/20 text-primary',
      desc: 'Discovers high-intent CTOs and engineering leaders by monitoring GitHub repository activity, Crunchbase Series B funding filings, and CSV uploads.',
      tags: ['GitHub Scraper', 'Crunchbase Series B', 'Apollo/CSV Ingest', 'Dedup Engine'],
      route: '/agents/0',
      btnLabel: 'Open Sourcing Console',
      isDark: false,
    },
    {
      num: '#01',
      id: '1',
      name: 'Agent 1: Deep Research',
      role: 'Signal Enrichment',
      icon: 'hub',
      accentColor: 'bg-tertiary',
      badgeColor: 'bg-tertiary-container/30 text-tertiary',
      desc: 'Performs multi-signal enrichment analyzing tech stack clues (Kubernetes, Go, Bazel), active hiring surges, and recent founder podcasts.',
      tags: ['Tech Stack Analysis', 'Hiring Surges', 'Podcast Intel', 'Signal Weights'],
      route: '/agents/1',
      btnLabel: 'Open Research Console',
      isDark: false,
    },
    {
      num: '#02',
      id: '2',
      name: 'Agent 2: ICP Decision Gate',
      role: 'Gate Qualification',
      icon: 'security',
      accentColor: 'bg-error',
      badgeColor: 'bg-error-container/40 text-error',
      desc: 'Strict qualification firewall enforcing a deterministic 78-point fitment threshold before any prospect is permitted into outreach queues.',
      tags: ['Hard 78-Pt Cutoff', 'Deterministic Gate', 'Disqualification', 'Fit Scoring'],
      route: '/agents/2',
      btnLabel: 'Open Gate Console',
      isDark: false,
    },
    {
      num: '#03',
      id: '3',
      name: 'Agent 3: Timing & Cadence',
      role: 'Cadence Engine',
      icon: 'schedule',
      accentColor: 'bg-secondary',
      badgeColor: 'bg-surface-container font-semibold text-secondary',
      desc: 'Guarantees touchpoints deliver strictly within each prospect’s local working hours window with calibrated multi-touch spacing.',
      tags: ['Timezone Optimization', 'Local Hours Window', 'Multi-Touch Cadence', 'Throttle Limits'],
      route: '/agents/3',
      btnLabel: 'Open Timing Console',
      isDark: false,
    },
    {
      num: '#04',
      id: '4',
      name: 'Agent 4: Tone & Personalization',
      role: 'Outbound Copy Rules',
      icon: 'rate_review',
      accentColor: 'bg-primary',
      badgeColor: 'bg-primary-container/40 text-primary',
      desc: 'Controls brevity limits, channel syntax, fluff guardrails, and persona tone rules before outbound drafts are deployed.',
      tags: ['Brevity Guard', 'Email Syntax', 'Persona Matrix', 'Tone Rules'],
      route: '/agents/4',
      btnLabel: 'Open Tone Console',
      isDark: false,
    },
    {
      num: '#05',
      id: '5',
      name: 'Agent 5: Reply Basket & Safety',
      role: 'Guardrails & Triage',
      icon: 'rule',
      accentColor: 'bg-tertiary',
      badgeColor: 'bg-tertiary-container/30 text-tertiary',
      desc: 'Classifies incoming prospect replies, immediately halts automation upon legal or pricing inquiries, and escalates high-intent leads to Ramya.',
      tags: ['Intent Classification', 'Legal/Pricing Freeze', 'Human Escalation', 'Follow-up Rules'],
      route: '/agents/5',
      btnLabel: 'Open Basket Console',
      isDark: false,
    },
    {
      num: '#06',
      id: '6',
      name: 'Agent 6: Voice AI & Telephony',
      role: 'Conversational Voice AI',
      icon: 'record_voice_over',
      accentColor: 'bg-primary-container',
      badgeColor: 'bg-white/10 text-primary-fixed',
      desc: 'Ultra-low latency conversational voice agent powered by Twilio and Groq AI (qwen/qwen3.8-27b at ~240ms) with full transcript logging and whisper support.',
      tags: ['Twilio Direct Calling', 'Groq AI Agent', 'Call Transcripts', 'Whisper & Barge-in'],
      route: '/agents/6',
      btnLabel: 'Open Voice AI Console',
      isDark: true,
    },
  ];

  return (
    <div className="w-full bg-surface min-h-screen px-space-lg py-space-lg">
      <div className="flex flex-col w-full max-w-[1440px] mx-auto gap-space-lg">
        {/* Breadcrumb & Global Quick Actions */}
        <div className="flex flex-wrap items-center justify-between gap-space-sm">
          <div className="flex items-center gap-2 text-outline font-label-md text-label-md">
            <span className="hover:text-on-surface cursor-pointer transition-colors">Workspace</span>
            <span className="material-symbols-outlined text-[16px]">chevron_right</span>
            <span className="hover:text-on-surface cursor-pointer transition-colors">Campaigns</span>
            <span className="material-symbols-outlined text-[16px]">chevron_right</span>
            <span className="text-primary font-label-lg text-label-lg font-semibold bg-surface-container-high px-2.5 py-0.5 rounded-full">
              Autonomous Fleet Hub
            </span>
          </div>

          <div className="flex items-center gap-space-sm">
            <button
              onClick={() => navigate('/discovery')}
              className="flex items-center gap-1.5 px-4 py-2 rounded-full bg-surface-container-lowest text-on-surface hover:bg-surface-container shadow-sm font-label-md text-label-md transition-all active:scale-95 border border-surface-container-high"
            >
              <span className="material-symbols-outlined text-[18px] text-primary">person_search</span>
              <span>Discover Prospects</span>
            </button>
            <button
              onClick={() => navigate('/agents/6')}
              className="flex items-center gap-2 px-5 py-2 rounded-full bg-primary-container text-on-primary-container hover:brightness-105 font-label-lg text-label-lg shadow-sm transition-all active:scale-95"
            >
              <span className="material-symbols-outlined text-[18px]">phone_in_talk</span>
              <span className="font-bold">Test Voice Agent</span>
            </button>
          </div>
        </div>

        {/* Hero Title Banner */}
        <div className="relative bg-surface-container-lowest rounded-2xl p-space-lg shadow-sm overflow-hidden border border-surface-container-high/60">
          <div className="absolute -right-16 -top-16 w-80 h-80 rounded-full bg-primary-container/10 blur-3xl pointer-events-none"></div>
          <div className="absolute left-1/3 -bottom-20 w-60 h-60 rounded-full bg-tertiary/10 blur-2xl pointer-events-none"></div>

          <div className="relative flex flex-col lg:flex-row lg:items-end justify-between gap-space-md">
            <div className="flex flex-col gap-1 max-w-2xl">
              <div className="flex items-center gap-2">
                <span className={`h-2.5 w-2.5 rounded-full ${killSwitchActive ? 'bg-error' : 'bg-tertiary animate-pulse'}`}></span>
                <span className="font-label-sm text-label-sm uppercase tracking-wider text-tertiary font-bold text-xs">
                  {killSwitchActive ? 'Operations Halted' : 'Autonomous Fleet • Live'}
                </span>
              </div>
              <h1 className="font-headline-xl text-headline-xl text-on-surface tracking-tight font-serif text-3xl md:text-4xl font-bold">
                Autonomous Agent Fleet
              </h1>
              <p className="font-body-md text-body-md text-on-surface-variant text-sm mt-1">
                Click any agent below to inspect its live configuration, test prompts, adjust rules, and monitor executions.
              </p>
            </div>

            {/* Real System Status Badges */}
            <div className="flex flex-wrap items-center gap-2 pt-2 lg:pt-0">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-surface-container-low text-tertiary font-label-sm text-label-sm border border-surface-container-high">
                <span className="h-2 w-2 rounded-full bg-tertiary"></span>
                <span className="font-semibold text-on-surface">6 Configured Agents</span>
              </div>
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-surface-container-low text-on-surface font-label-sm text-label-sm border border-surface-container-high">
                <span className="material-symbols-outlined text-[16px] text-primary">group</span>
                <span>{prospectCount} Ingested Prospects</span>
              </div>
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-surface-container-low text-on-surface font-label-sm text-label-sm border border-surface-container-high">
                <span className="material-symbols-outlined text-[16px] text-tertiary">campaign</span>
                <span>{liveCampaignsCount} Active Campaigns</span>
              </div>
            </div>
          </div>
        </div>

        {/* 6 Autonomous Agent Cards Grid */}
        <div>
          <div className="flex items-center justify-between mb-space-sm px-1">
            <div className="flex items-center gap-2">
              <span className="font-headline-sm text-headline-sm text-on-surface font-bold text-lg">
                Pipeline Roster
              </span>
              <span className="px-2.5 py-0.5 rounded-full bg-surface-container-highest text-on-surface-variant font-label-sm text-label-sm font-medium text-xs">
                Active Modules
              </span>
            </div>
            <span className="font-label-sm text-label-sm text-outline text-xs">
              Click an agent card to open its dedicated dashboard
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-space-lg">
            {agentRoster.map((agent) => (
              <div
                key={agent.id}
                onClick={() => navigate(agent.route)}
                className={`group cursor-pointer rounded-2xl p-space-lg shadow-sm hover:shadow-md transition-all duration-300 flex flex-col justify-between relative overflow-hidden border ${
                  agent.isDark
                    ? 'bg-[#1e1e1a] hover:bg-[#262621] text-white border-neutral-800 hover:border-primary-container/50'
                    : 'bg-surface-container-lowest hover:bg-surface-container-low border-surface-container-high/60 hover:border-primary-container/50'
                }`}
              >
                {/* Left accent bar */}
                <div className={`absolute top-0 left-0 w-1.5 h-full ${agent.accentColor}`}></div>

                <div>
                  {/* Top Bar */}
                  <div className="flex items-center justify-between mb-3">
                    <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full font-label-sm text-label-sm font-semibold text-xs ${agent.badgeColor}`}>
                      <span className="material-symbols-outlined text-[15px]">{agent.icon}</span>
                      <span>{agent.role}</span>
                    </div>
                    <span className={`text-sm font-bold ${agent.isDark ? 'text-white/40 group-hover:text-white' : 'text-outline group-hover:text-on-surface'}`}>
                      {agent.num}
                    </span>
                  </div>

                  {/* Title & Icon */}
                  <div className="flex items-center justify-between mb-2">
                    <h3 className={`font-bold text-lg transition-colors ${agent.isDark ? 'text-white group-hover:text-primary-fixed' : 'text-on-surface group-hover:text-primary'}`}>
                      {agent.name}
                    </h3>
                  </div>

                  {/* Description */}
                  <p className={`text-xs leading-relaxed mb-4 ${agent.isDark ? 'text-white/70' : 'text-on-surface-variant'}`}>
                    {agent.desc}
                  </p>

                  {/* Real Capability Tags */}
                  <div className="flex flex-wrap gap-1.5 mb-4">
                    {agent.tags.map((tag) => (
                      <span
                        key={tag}
                        className={`px-2 py-0.5 rounded-md text-[11px] font-medium ${
                          agent.isDark
                            ? 'bg-white/10 text-white/90 border border-white/10'
                            : 'bg-surface-container text-on-surface-variant border border-surface-container-high'
                        }`}
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Footer Action */}
                <div className={`pt-3 border-t flex items-center justify-between font-label-md text-label-md font-semibold text-xs ${
                  agent.isDark
                    ? 'border-white/10 text-primary-fixed'
                    : 'border-surface-container-high text-primary'
                }`}>
                  <span>{agent.btnLabel}</span>
                  <span className="material-symbols-outlined text-[18px] group-hover:translate-x-1 transition-transform">
                    arrow_forward
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Real Fleet Operations & Safety Controls Bar */}
        <div className="bg-surface-container-lowest rounded-2xl p-space-lg shadow-sm border border-surface-container-high/60 flex flex-col md:flex-row items-start md:items-center justify-between gap-space-md">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center font-bold shrink-0 ${
              killSwitchActive ? 'bg-error text-white' : 'bg-tertiary-container text-on-tertiary-container'
            }`}>
              <span className="material-symbols-outlined text-[22px]">
                {killSwitchActive ? 'emergency_home' : 'verified_user'}
              </span>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h4 className="font-bold text-on-surface text-base">Fleet Operations &amp; Kill Switch</h4>
                <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${
                  killSwitchActive
                    ? 'bg-error-container text-error'
                    : 'bg-tertiary-container/40 text-tertiary'
                }`}>
                  {systemStatus}
                </span>
              </div>
              <p className="text-xs text-on-surface-variant mt-0.5">
                {killSwitchActive
                  ? 'Autonomous outreach is paused. No emails or voice calls will dispatch.'
                  : 'All autonomous outreach guardrails, dedup filters, and voice agents are operational.'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 w-full md:w-auto justify-end">
            <button
              onClick={() => navigate('/control-centre')}
              className="px-4 py-2 rounded-full bg-surface-container text-on-surface hover:bg-surface-container-high font-label-md text-label-md text-xs font-semibold transition-colors"
            >
              Control Centre
            </button>
            <button
              onClick={handleToggleKillSwitch}
              disabled={loadingControls}
              className={`px-5 py-2 rounded-full font-label-md text-label-md text-xs font-bold transition-all shadow-sm ${
                killSwitchActive
                  ? 'bg-tertiary text-white hover:brightness-110'
                  : 'bg-error-container text-on-error-container hover:bg-error hover:text-white'
              }`}
            >
              {loadingControls
                ? 'Processing...'
                : killSwitchActive
                ? 'Resume Fleet Operations'
                : 'Emergency Fleet Halt'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
