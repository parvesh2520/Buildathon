import React from 'react';

interface MetricProps {
  voiceCalls?: number;
  touches?: number;
  politeNos?: number;
  needsRamya?: number;
}

export const DashboardMetrics: React.FC<MetricProps> = ({
  voiceCalls = 48,
  touches = 312,
  politeNos = 19,
  needsRamya = 8,
}) => {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {/* 1. Voice Calls */}
      <div className="bg-surface-container-lowest rounded-2xl p-space-lg shadow-sm border border-outline-variant/40 flex flex-col justify-between">
        <span className="font-label-sm text-label-sm text-outline uppercase tracking-wider font-semibold">
          Voice Calls
        </span>
        <div className="my-2">
          <span className="font-display-stat text-[38px] lg:text-[44px] text-on-surface font-serif font-semibold leading-none">
            {voiceCalls}
          </span>
        </div>
        <div className="flex items-center gap-1.5 text-tertiary font-label-sm text-label-sm font-semibold">
          <span className="material-symbols-outlined text-[16px] select-none">trending_up</span>
          <span>+14% vs yesterday</span>
        </div>
      </div>

      {/* 2. Touches */}
      <div className="bg-surface-container-lowest rounded-2xl p-space-lg shadow-sm border border-outline-variant/40 flex flex-col justify-between">
        <span className="font-label-sm text-label-sm text-outline uppercase tracking-wider font-semibold">
          Touches
        </span>
        <div className="my-2">
          <span className="font-display-stat text-[38px] lg:text-[44px] text-on-surface font-serif font-semibold leading-none">
            {touches}
          </span>
        </div>
        <div className="flex items-center gap-1.5 text-tertiary font-label-sm text-label-sm font-medium">
          <span className="material-symbols-outlined text-[16px] select-none">done_all</span>
          <span>96% delivered safely</span>
        </div>
      </div>

      {/* 3. Polite No's */}
      <div className="bg-surface-container-lowest rounded-2xl p-space-lg shadow-sm border border-outline-variant/40 flex flex-col justify-between">
        <span className="font-label-sm text-label-sm text-outline uppercase tracking-wider font-semibold">
          Polite 'No's
        </span>
        <div className="my-2">
          <span className="font-display-stat text-[38px] lg:text-[44px] text-on-surface font-serif font-semibold leading-none">
            {politeNos}
          </span>
        </div>
        <div className="flex items-center gap-1.5 text-on-surface-variant font-body-sm text-body-sm text-[12px]">
          <span className="material-symbols-outlined text-[16px] text-outline select-none">inventory_2</span>
          <span>Analyzed &amp; filed</span>
        </div>
      </div>

      {/* 4. Needs Ramya */}
      <div className="bg-[#FEF7E6] rounded-2xl p-space-lg shadow-sm border border-[#E6A219]/40 flex flex-col justify-between">
        <span className="font-label-sm text-label-sm text-[#7F5700] uppercase tracking-wider font-bold">
          Needs Ramya
        </span>
        <div className="my-2">
          <span className="font-display-stat text-[38px] lg:text-[44px] text-[#7F5700] font-serif font-bold leading-none">
            {needsRamya}
          </span>
        </div>
        <div className="flex items-center gap-1.5 text-[#7F5700] font-label-sm text-label-sm font-semibold">
          <span className="material-symbols-outlined text-[16px] select-none">flag</span>
          <span>Escalated threads</span>
        </div>
      </div>
    </div>
  );
};
