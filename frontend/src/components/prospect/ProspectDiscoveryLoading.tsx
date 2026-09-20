import React from 'react';

interface ProspectDiscoveryLoadingCardProps {
  campaignName?: string;
  count?: number;
}

export const ProspectDiscoveryLoadingCard: React.FC<ProspectDiscoveryLoadingCardProps> = ({
  campaignName,
  count = 5,
}) => {
  return (
    <div className="rounded-2xl bg-surface-container-lowest shadow-md overflow-hidden border border-outline-variant/20">
      {/* Header ribbon with pulsing gradient */}
      <div className="h-1.5 w-full bg-gradient-to-r from-primary via-tertiary to-primary-container animate-pulse" />

      <div className="p-space-lg sm:p-space-xl flex flex-col items-center text-center">
        {/* Animated Radar Icon */}
        <div className="relative mb-space-md">
          <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center text-primary relative z-10">
            <span className="material-symbols-outlined text-[32px] animate-spin" style={{ animationDuration: '3s' }}>
              radar
            </span>
          </div>
          {/* Pulsing halo rings */}
          <div className="absolute inset-0 rounded-full bg-primary/20 animate-ping opacity-75" />
          <div className="absolute -inset-2 rounded-full border border-primary/30 animate-pulse" />
        </div>

        {/* Title and descriptions */}
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary font-label-sm text-label-sm font-semibold mb-2">
          <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
          AGENT 0 SOURCING SCOUT ACTIVE
        </div>

        <h3 className="font-headline-md text-headline-md text-on-surface font-semibold tracking-tight">
          Discovering &amp; Enrolling Leads...
        </h3>

        <p className="font-body-md text-body-md text-on-surface-variant mt-1.5 max-w-lg">
          Agent 0 is querying real-time B2B data sources, verifying ICP fit, and sourcing{' '}
          <span className="font-semibold text-primary">{count} qualified prospects</span>
          {campaignName ? ` for "${campaignName}"` : ''}.
        </p>

        {/* Live Step Progress indicators */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 w-full max-w-xl mt-space-lg pt-2 text-left">
          <div className="flex items-center gap-2.5 p-3 rounded-xl bg-surface-container-low/80 border border-outline-variant/15">
            <span className="material-symbols-outlined text-[18px] text-tertiary animate-spin" style={{ animationDuration: '2s' }}>
              sync
            </span>
            <div className="flex flex-col min-w-0">
              <span className="font-label-sm text-label-sm font-semibold text-on-surface">1. Sourcing Profiles</span>
              <span className="font-label-xs text-xs text-outline">Targeting roles &amp; geo</span>
            </div>
          </div>

          <div className="flex items-center gap-2.5 p-3 rounded-xl bg-surface-container-low/80 border border-outline-variant/15">
            <span className="material-symbols-outlined text-[18px] text-primary animate-pulse">
              verified
            </span>
            <div className="flex flex-col min-w-0">
              <span className="font-label-sm text-label-sm font-semibold text-on-surface">2. Evaluating ICP</span>
              <span className="font-label-xs text-xs text-outline">Gating score criteria</span>
            </div>
          </div>

          <div className="flex items-center gap-2.5 p-3 rounded-xl bg-surface-container-low/80 border border-outline-variant/15">
            <span className="material-symbols-outlined text-[18px] text-tertiary">
              cloud_sync
            </span>
            <div className="flex flex-col min-w-0">
              <span className="font-label-sm text-label-sm font-semibold text-on-surface">3. Enrolling Leads</span>
              <span className="font-label-xs text-xs text-outline">Persisting into Supabase</span>
            </div>
          </div>
        </div>

        {/* Shimmering Skeleton Rows to preview incoming prospects */}
        <div className="w-full max-w-2xl mt-space-lg flex flex-col gap-2.5 opacity-80">
          <div className="text-left font-label-xs text-xs uppercase tracking-wider text-outline px-1">
            Live Stream Placeholder
          </div>
          {[1, 2, 3].map((idx) => (
            <div
              key={idx}
              className="flex items-center justify-between p-3.5 rounded-xl bg-surface-container/40 border border-outline-variant/10 animate-pulse"
              style={{ animationDelay: `${idx * 200}ms` }}
            >
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-full bg-surface-container-high/60" />
                <div className="flex flex-col gap-1.5 text-left">
                  <div className="h-3.5 w-36 bg-surface-container-high/60 rounded" />
                  <div className="h-2.5 w-48 bg-surface-container-high/40 rounded" />
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="h-4 w-16 bg-surface-container-high/40 rounded-full" />
                <div className="h-6 w-20 bg-primary/10 rounded-full" />
              </div>
            </div>
          ))}
        </div>

        <p className="font-label-sm text-label-sm text-outline mt-space-md flex items-center gap-1.5">
          <span className="material-symbols-outlined text-[16px]">info</span>
          Prospects will auto-populate and appear live once Agent 0 finishes verification.
        </p>
      </div>
    </div>
  );
};

interface ProspectDiscoveryLoadingBannerProps {
  count?: number;
}

export const ProspectDiscoveryLoadingBanner: React.FC<ProspectDiscoveryLoadingBannerProps> = ({
  count = 5,
}) => {
  return (
    <div className="flex items-center justify-between gap-3 p-3.5 mb-space-md rounded-2xl bg-primary-container/20 border border-primary/30 text-on-surface shadow-sm animate-pulse">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-xl bg-primary/10 flex items-center justify-center text-primary shrink-0">
          <span className="material-symbols-outlined text-[20px] animate-spin" style={{ animationDuration: '3s' }}>
            radar
          </span>
        </div>
        <div className="flex flex-col">
          <span className="font-label-md text-label-md font-semibold text-primary flex items-center gap-1.5">
            Agent 0 Discovery in Progress
            <span className="w-2 h-2 rounded-full bg-primary animate-ping inline-block" />
          </span>
          <span className="font-body-sm text-body-sm text-on-surface-variant">
            Actively discovering {count} additional prospects matching campaign ICP. Newly found leads will automatically enroll below.
          </span>
        </div>
      </div>
      <div className="hidden sm:flex items-center gap-2 px-3 py-1 rounded-full bg-surface-container-lowest text-primary font-label-sm text-label-sm font-semibold border border-primary/20">
        <span className="material-symbols-outlined text-[16px] animate-spin">refresh</span>
        Scouting B2B DB...
      </div>
    </div>
  );
};
