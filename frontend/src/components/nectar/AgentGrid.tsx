import React from 'react';

interface AgentGridProps {
  onSelectAgent: (agentId: number) => void;
}

export const AgentGrid: React.FC<AgentGridProps> = ({ onSelectAgent }) => {
  return (
    <section className="flex flex-col gap-space-md">
      {/* Section Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div className="flex items-center gap-2.5">
          <h2 className="font-headline-md text-headline-md text-on-surface font-serif">
            Continuous Outreach Engine
          </h2>
          <span className="px-2.5 py-0.5 rounded-full bg-surface-container-high text-on-surface-variant font-label-sm text-label-sm font-semibold">
            Synchronized
          </span>
        </div>
        <div className="text-outline font-label-sm text-label-sm">
          Interactive Matrix • Realtime Latency: <span className="text-on-surface font-medium">42ms</span>
        </div>
      </div>

      {/* Row 1: 3 Larger Primary Agent Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Agent 0: Sourcing Scout */}
        <div
          onClick={() => onSelectAgent(0)}
          className="group relative bg-surface-container-lowest rounded-2xl p-space-lg shadow-sm border border-outline-variant/40 hover:shadow-md hover:border-primary/50 transition-all cursor-pointer flex flex-col justify-between"
        >
          <div className="absolute left-0 top-6 bottom-6 w-1.5 rounded-r-full bg-[#E6A219]" />
          <div className="pl-2">
            {/* Header badges */}
            <div className="flex items-center justify-between">
              <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#FEF7E6] text-[#7F5700] font-label-sm text-label-sm font-semibold border border-[#E6A219]/30">
                <span className="material-symbols-outlined text-[15px] select-none">explore</span>
                <span>Discovery</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-label-sm text-label-sm text-outline font-bold">#00</span>
                <span className="material-symbols-outlined text-[18px] text-outline select-none">travel_explore</span>
              </div>
            </div>

            {/* Title */}
            <h3 className="font-headline-md text-headline-md text-on-surface font-serif mt-3 group-hover:text-primary transition-colors">
              Agent 0: Sourcing Scout
            </h3>

            {/* Tags */}
            <div className="flex flex-wrap items-center gap-1.5 mt-2.5">
              <span className="px-2.5 py-0.5 rounded-full bg-surface-container text-on-surface-variant font-label-sm text-label-sm">
                GitHub
              </span>
              <span className="px-2.5 py-0.5 rounded-full bg-surface-container text-on-surface-variant font-label-sm text-label-sm">
                Series B
              </span>
              <span className="px-2.5 py-0.5 rounded-full bg-surface-container text-on-surface-variant font-label-sm text-label-sm">
                LinkedIn
              </span>
            </div>

            {/* Progress Bar */}
            <div className="mt-4 flex flex-col gap-1.5">
              <div className="flex items-center justify-between text-label-sm font-semibold">
                <span className="text-outline">Target Ingestion</span>
                <span className="text-on-surface font-serif text-[15px]">99.4%</span>
              </div>
              <div className="h-1.5 w-full bg-surface-container-high rounded-full overflow-hidden">
                <div className="h-full bg-[#E6A219] rounded-full" style={{ width: '99.4%' }} />
              </div>
            </div>

            {/* Metrics */}
            <div className="mt-4 pt-3 border-t border-outline-variant/30 flex items-center justify-between">
              <div>
                <span className="font-label-sm text-label-sm uppercase tracking-wider text-outline block">
                  Velocity
                </span>
                <span className="font-headline-sm text-headline-sm text-on-surface font-serif">
                  1,420<span className="font-sans text-xs text-outline font-normal">/hr</span>
                </span>
              </div>
              <div>
                <span className="font-label-sm text-label-sm uppercase tracking-wider text-outline block">
                  Dedup
                </span>
                <span className="font-headline-sm text-headline-sm text-tertiary font-serif">99.4%</span>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-2 flex items-center justify-end text-primary group-hover:translate-x-0.5 transition-transform">
            <span className="font-label-sm text-label-sm font-semibold flex items-center gap-1">
              Filter Rules <span className="text-xs">↗</span>
            </span>
          </div>
        </div>

        {/* Agent 1: Deep Research */}
        <div
          onClick={() => onSelectAgent(1)}
          className="group relative bg-surface-container-lowest rounded-2xl p-space-lg shadow-sm border border-outline-variant/40 hover:shadow-md hover:border-tertiary/50 transition-all cursor-pointer flex flex-col justify-between"
        >
          <div className="absolute left-0 top-6 bottom-6 w-1.5 rounded-r-full bg-[#366853]" />
          <div className="pl-2">
            {/* Header badges */}
            <div className="flex items-center justify-between">
              <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#EDF4F0] text-[#366853] font-label-sm text-label-sm font-semibold border border-[#366853]/20">
                <span className="material-symbols-outlined text-[15px] select-none">psychology</span>
                <span>Signal Enrichment</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-label-sm text-label-sm text-outline font-bold">#01</span>
                <span className="material-symbols-outlined text-[18px] text-tertiary select-none">hub</span>
              </div>
            </div>

            {/* Title */}
            <h3 className="font-headline-md text-headline-md text-on-surface font-serif mt-3 group-hover:text-tertiary transition-colors">
              Agent 1: Deep Research
            </h3>

            {/* Tags */}
            <div className="flex flex-wrap items-center gap-1.5 mt-2.5">
              <span className="px-2.5 py-0.5 rounded-full bg-surface-container text-on-surface-variant font-label-sm text-label-sm">
                Tech Stack
              </span>
              <span className="px-2.5 py-0.5 rounded-full bg-surface-container text-on-surface-variant font-label-sm text-label-sm">
                Hiring Surges
              </span>
              <span className="px-2.5 py-0.5 rounded-full bg-surface-container text-on-surface-variant font-label-sm text-label-sm">
                Podcasts
              </span>
            </div>

            {/* Progress Bar */}
            <div className="mt-4 flex flex-col gap-1.5">
              <div className="flex items-center justify-between text-label-sm font-semibold">
                <span className="text-outline">Signal Confidence</span>
                <span className="text-on-surface font-serif text-[15px]">94.8%</span>
              </div>
              <div className="h-1.5 w-full bg-surface-container-high rounded-full overflow-hidden">
                <div className="h-full bg-[#366853] rounded-full" style={{ width: '94.8%' }} />
              </div>
            </div>

            {/* Metrics */}
            <div className="mt-4 pt-3 border-t border-outline-variant/30 flex items-center justify-between">
              <div>
                <span className="font-label-sm text-label-sm uppercase tracking-wider text-outline block">
                  Streams
                </span>
                <span className="font-headline-sm text-headline-sm text-on-surface font-serif">
                  42<span className="font-sans text-xs text-outline font-normal"> live</span>
                </span>
              </div>
              <div>
                <span className="font-label-sm text-label-sm uppercase tracking-wider text-outline block">
                  Score
                </span>
                <span className="font-headline-sm text-headline-sm text-tertiary font-serif">94.8%</span>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-2 flex items-center justify-end text-tertiary group-hover:translate-x-0.5 transition-transform">
            <span className="font-label-sm text-label-sm font-semibold flex items-center gap-1">
              Signal Weights <span className="text-xs">↗</span>
            </span>
          </div>
        </div>

        {/* Agent 2: ICP Decision Gate */}
        <div
          onClick={() => onSelectAgent(2)}
          className="group relative bg-surface-container-lowest rounded-2xl p-space-lg shadow-sm border border-outline-variant/40 hover:shadow-md hover:border-error/40 transition-all cursor-pointer flex flex-col justify-between"
        >
          <div className="absolute left-0 top-6 bottom-6 w-1.5 rounded-r-full bg-[#BA1A1A]" />
          <div className="pl-2">
            {/* Header badges */}
            <div className="flex items-center justify-between">
              <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#FFDAD6]/50 text-[#BA1A1A] font-label-sm text-label-sm font-semibold border border-[#BA1A1A]/20">
                <span className="material-symbols-outlined text-[15px] select-none">block</span>
                <span>Gate Cut</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-label-sm text-label-sm text-outline font-bold">#02</span>
                <span className="material-symbols-outlined text-[18px] text-error select-none">security</span>
              </div>
            </div>

            {/* Title */}
            <h3 className="font-headline-md text-headline-md text-on-surface font-serif mt-3 group-hover:text-error transition-colors">
              Agent 2: ICP Decision Gate
            </h3>

            {/* Tags */}
            <div className="flex flex-wrap items-center gap-1.5 mt-2.5">
              <span className="px-2.5 py-0.5 rounded-full bg-surface-container text-on-surface-variant font-label-sm text-label-sm">
                Deterministic
              </span>
              <span className="px-2.5 py-0.5 rounded-full bg-surface-container text-on-surface-variant font-label-sm text-label-sm">
                Hard 78 Cutoff
              </span>
            </div>

            {/* Progress Bar */}
            <div className="mt-4 flex flex-col gap-1.5">
              <div className="flex items-center justify-between text-label-sm font-semibold">
                <span className="text-outline">Threshold Strictness</span>
                <span className="text-error font-serif text-[15px]">78 / 100</span>
              </div>
              <div className="h-1.5 w-full bg-surface-container-high rounded-full overflow-hidden">
                <div className="h-full bg-[#BA1A1A] rounded-full" style={{ width: '78%' }} />
              </div>
            </div>

            {/* Metrics */}
            <div className="mt-4 pt-3 border-t border-outline-variant/30 flex items-center justify-between">
              <div>
                <span className="font-label-sm text-label-sm uppercase tracking-wider text-outline block">
                  Cutoff
                </span>
                <span className="font-headline-sm text-headline-sm text-on-surface font-serif">
                  78<span className="font-sans text-xs text-outline font-normal"> pts</span>
                </span>
              </div>
              <div>
                <span className="font-label-sm text-label-sm uppercase tracking-wider text-outline block">
                  Filtered
                </span>
                <span className="font-headline-sm text-headline-sm text-error font-serif">1,108</span>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-2 flex items-center justify-end text-error group-hover:translate-x-0.5 transition-transform">
            <span className="font-label-sm text-label-sm font-semibold flex items-center gap-1">
              Cutoff Thresholds <span className="text-xs">↗</span>
            </span>
          </div>
        </div>
      </div>

      {/* Row 2: 4 Secondary Agent Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Agent 3: Timing */}
        <div
          onClick={() => onSelectAgent(3)}
          className="group relative bg-surface-container-lowest rounded-2xl p-space-md shadow-sm border border-outline-variant/40 hover:shadow-md hover:border-primary/40 transition-all cursor-pointer flex flex-col justify-between"
        >
          <div className="absolute left-0 top-4 bottom-4 w-1.5 rounded-r-full bg-[#837562]" />
          <div className="pl-2">
            <div className="flex items-center justify-between">
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-surface-container text-on-surface-variant font-label-sm text-label-sm font-medium">
                <span className="material-symbols-outlined text-[13px] select-none">schedule</span>
                <span>Cadence</span>
              </span>
              <span className="font-label-sm text-label-sm text-outline font-bold">#03</span>
            </div>

            <h3 className="font-headline-md text-headline-md text-on-surface font-serif mt-2 group-hover:text-primary transition-colors">
              Agent 3: Timing
            </h3>
            <div className="flex items-center gap-1.5 text-on-surface-variant font-body-sm text-body-sm mt-1">
              <span className="material-symbols-outlined text-[14px] text-tertiary select-none">schedule</span>
              <span>9:00 – 11:30 AM PST</span>
            </div>

            <div className="mt-3 pt-2 border-t border-outline-variant/30 flex items-center justify-between">
              <div>
                <span className="font-label-sm text-label-sm text-outline uppercase block text-[10px]">
                  Next Window
                </span>
                <span className="font-headline-sm text-headline-sm text-on-surface font-serif">9:04 AM</span>
              </div>
              <span className="px-2 py-0.5 rounded-md bg-surface-container font-label-sm text-label-sm text-on-surface-variant">
                1/day
              </span>
            </div>
          </div>

          <div className="mt-3 pt-1 flex items-center justify-end text-primary group-hover:translate-x-0.5 transition-transform">
            <span className="font-label-sm text-label-sm font-semibold flex items-center gap-1">
              Timezone Config <span className="text-xs">↗</span>
            </span>
          </div>
        </div>

        {/* Agent 4: Style */}
        <div
          onClick={() => onSelectAgent(4)}
          className="group relative bg-surface-container-lowest rounded-2xl p-space-md shadow-sm border border-outline-variant/40 hover:shadow-md hover:border-primary/40 transition-all cursor-pointer flex flex-col justify-between"
        >
          <div className="absolute left-0 top-4 bottom-4 w-1.5 rounded-r-full bg-[#E6A219]" />
          <div className="pl-2">
            <div className="flex items-center justify-between">
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-surface-container text-on-surface-variant font-label-sm text-label-sm font-medium">
                <span className="material-symbols-outlined text-[13px] select-none">format_quote</span>
                <span>Tone</span>
              </span>
              <span className="font-label-sm text-label-sm text-outline font-bold">#04</span>
            </div>

            <h3 className="font-headline-md text-headline-md text-on-surface font-serif mt-2 group-hover:text-primary transition-colors">
              Agent 4: Style
            </h3>
            <div className="flex items-center gap-1.5 text-on-surface-variant font-body-sm text-body-sm mt-1">
              <span className="material-symbols-outlined text-[14px] text-primary select-none">edit_note</span>
              <span>Concise • Zero Fluff</span>
            </div>

            <div className="mt-3 pt-2 border-t border-outline-variant/30 flex items-center justify-between">
              <div>
                <span className="font-label-sm text-label-sm text-outline uppercase block text-[10px]">
                  Avg Length
                </span>
                <span className="font-headline-sm text-headline-sm text-on-surface font-serif">58 w</span>
              </div>
              <span className="px-2 py-0.5 rounded-md bg-[#FEF7E6] text-[#7F5700] font-label-sm text-label-sm font-semibold">
                Direct
              </span>
            </div>
          </div>

          <div className="mt-3 pt-1 flex items-center justify-end text-primary group-hover:translate-x-0.5 transition-transform">
            <span className="font-label-sm text-label-sm font-semibold flex items-center gap-1">
              Tone Settings <span className="text-xs">↗</span>
            </span>
          </div>
        </div>

        {/* Agent 5: Reply Basket */}
        <div
          onClick={() => onSelectAgent(5)}
          className="group relative bg-surface-container-lowest rounded-2xl p-space-md shadow-sm border border-outline-variant/40 hover:shadow-md hover:border-tertiary/40 transition-all cursor-pointer flex flex-col justify-between"
        >
          <div className="absolute left-0 top-4 bottom-4 w-1.5 rounded-r-full bg-[#366853]" />
          <div className="pl-2">
            <div className="flex items-center justify-between">
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-[#EDF4F0] text-tertiary font-label-sm text-label-sm font-medium">
                <span className="material-symbols-outlined text-[13px] select-none">shield</span>
                <span>Guardrails</span>
              </span>
              <span className="font-label-sm text-label-sm text-outline font-bold">#05</span>
            </div>

            <h3 className="font-headline-md text-headline-md text-on-surface font-serif mt-2 group-hover:text-tertiary transition-colors">
              Agent 5: Reply Basket
            </h3>
            <div className="flex items-center gap-1.5 text-on-surface-variant font-body-sm text-body-sm mt-1">
              <span className="material-symbols-outlined text-[14px] text-tertiary select-none">check_circle</span>
              <span>Instant Legal Freeze</span>
            </div>

            <div className="mt-3 pt-2 border-t border-outline-variant/30 flex items-center justify-between">
              <div>
                <span className="font-label-sm text-label-sm text-outline uppercase block text-[10px]">
                  Errors
                </span>
                <span className="font-headline-sm text-headline-sm text-tertiary font-serif">0</span>
              </div>
              <span className="px-2 py-0.5 rounded-md bg-[#EDF4F0] text-tertiary font-label-sm text-label-sm font-semibold">
                Active
              </span>
            </div>
          </div>

          <div className="mt-3 pt-1 flex items-center justify-end text-tertiary group-hover:translate-x-0.5 transition-transform">
            <span className="font-label-sm text-label-sm font-semibold flex items-center gap-1">
              Basket Logic <span className="text-xs">↗</span>
            </span>
          </div>
        </div>

        {/* Agent 6: Voice (Dark Card) */}
        <div
          onClick={() => onSelectAgent(6)}
          className="group relative bg-inverse-surface rounded-2xl p-space-md shadow-md hover:shadow-lg border border-outline-variant/30 transition-all cursor-pointer flex flex-col justify-between text-inverse-on-surface"
        >
          <div className="absolute left-0 top-4 bottom-4 w-1.5 rounded-r-full bg-primary-container" />
          <div className="pl-2">
            <div className="flex items-center justify-between">
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-white/10 text-primary-fixed font-label-sm text-label-sm font-medium">
                <span className="material-symbols-outlined text-[13px] select-none">mic</span>
                <span>Voice AI</span>
              </span>
              <span className="font-label-sm text-label-sm text-surface-dim font-bold">#06</span>
            </div>

            <h3 className="font-headline-md text-headline-md text-inverse-on-surface font-serif mt-2 group-hover:text-primary-fixed transition-colors">
              Agent 6: Voice
            </h3>
            <div className="flex items-center gap-1.5 text-inverse-on-surface/80 font-body-sm text-body-sm mt-1">
              <span className="material-symbols-outlined text-[14px] text-primary-fixed select-none">record_voice_over</span>
              <span>Live Whisper Coach</span>
            </div>

            <div className="mt-3 pt-2 border-t border-white/10 flex items-center justify-between">
              <div>
                <span className="font-label-sm text-label-sm text-inverse-on-surface/60 uppercase block text-[10px]">
                  Traffic
                </span>
                <span className="font-headline-sm text-headline-sm text-white font-serif">48 calls</span>
              </div>
              <span className="px-2 py-0.5 rounded-md bg-white/10 text-primary-fixed font-label-sm text-label-sm font-semibold">
                240ms
              </span>
            </div>
          </div>

          <div className="mt-3 pt-1 flex items-center justify-end text-primary-fixed group-hover:translate-x-0.5 transition-transform">
            <span className="font-label-sm text-label-sm font-semibold flex items-center gap-1">
              Latency &amp; Barge <span className="text-xs">↗</span>
            </span>
          </div>
        </div>
      </div>
    </section>
  );
};
