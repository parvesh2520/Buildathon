import React from 'react';

interface AutonomousFleetBannerProps {
  onDryRun?: () => void;
  onDeployFleet?: () => void;
  activeAgentsCount?: number;
  criticalErrorsCount?: number;
  actionsTodayCount?: number;
}

export const AutonomousFleetBanner: React.FC<AutonomousFleetBannerProps> = ({
  onDryRun,
  onDeployFleet,
  activeAgentsCount = 7,
  criticalErrorsCount = 0,
  actionsTodayCount = 418,
}) => {
  return (
    <div className="flex flex-col gap-space-md">
      {/* Sub navigation context bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-1 border-b border-outline-variant/30">
        <div className="flex items-center gap-2 text-outline font-label-md text-label-md flex-wrap">
          <span className="hover:text-on-surface cursor-pointer">Workspace</span>
          <span className="material-symbols-outlined text-[15px] text-outline-variant select-none">
            chevron_right
          </span>
          <span className="hover:text-on-surface cursor-pointer">Campaigns</span>
          <span className="material-symbols-outlined text-[15px] text-outline-variant select-none">
            chevron_right
          </span>
          <span className="text-on-surface font-semibold">US SaaS CTOs</span>
          <span className="material-symbols-outlined text-[15px] text-outline-variant select-none">
            chevron_right
          </span>
          <span className="px-3 py-0.5 rounded-full bg-surface-container-high text-on-surface-variant font-label-sm text-label-sm font-semibold">
            Autonomous Fleet
          </span>
        </div>

        {/* Global actions */}
        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={onDryRun}
            className="flex items-center gap-1.5 px-4 py-2 rounded-full bg-surface-container-lowest text-on-surface hover:bg-surface-container font-label-md text-label-md shadow-[0_1px_2px_rgba(39,39,42,0.04)] border border-outline-variant/40 transition-all"
          >
            <span className="material-symbols-outlined text-[18px] text-outline select-none">science</span>
            <span>Dry Run Test</span>
          </button>
          <button
            onClick={onDeployFleet}
            className="flex items-center gap-1.5 px-4 py-2 rounded-full bg-primary-container text-on-primary-container hover:opacity-95 font-label-md text-label-md font-semibold shadow-[0_2px_6px_rgba(39,39,42,0.08)] transition-all"
          >
            <span className="material-symbols-outlined text-[18px] select-none">rocket_launch</span>
            <span>Deploy Fleet Updates</span>
          </button>
        </div>
      </div>

      {/* Main headline row */}
      <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-space-md pt-2">
        <div className="flex flex-col gap-1.5">
          <div className="inline-flex items-center gap-2 text-tertiary font-label-sm text-label-sm font-semibold tracking-wider uppercase">
            <span className="w-2 h-2 rounded-full bg-tertiary animate-pulse" />
            <span>PIPELINE V4.2 • LIVE FLEET</span>
          </div>

          <h1 className="font-headline-xl text-headline-xl text-on-surface tracking-tight font-serif">
            Your 7 Autonomous Agents
          </h1>

          <div className="flex items-center gap-2 text-on-surface-variant font-body-sm text-body-sm">
            <span className="material-symbols-outlined text-[16px] text-outline select-none">tune</span>
            <span>Select an agent to tune decision weights and guardrails</span>
          </div>
        </div>

        {/* Status badges */}
        <div className="flex flex-wrap items-center gap-2">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-surface-container-lowest text-on-surface font-label-sm text-label-sm border border-outline-variant/40 shadow-sm">
            <span className="w-2 h-2 rounded-full bg-tertiary" />
            <span>{activeAgentsCount} agents active</span>
          </div>

          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-surface-container-lowest text-on-surface font-label-sm text-label-sm border border-outline-variant/40 shadow-sm">
            <span className="material-symbols-outlined text-[15px] text-tertiary select-none">check_circle</span>
            <span>{criticalErrorsCount} critical errors</span>
          </div>

          <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-primary-container text-on-primary-container font-label-sm text-label-sm font-semibold shadow-sm">
            <span className="material-symbols-outlined text-[16px] select-none">bolt</span>
            <span>{actionsTodayCount} actions today</span>
          </div>
        </div>
      </div>
    </div>
  );
};
