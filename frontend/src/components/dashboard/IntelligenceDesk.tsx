import React, { useState } from 'react';
import toast from 'react-hot-toast';

export const IntelligenceDesk: React.FC = () => {
  const [query, setQuery] = useState('');
  const [activePrompt, setActivePrompt] = useState('Why did the five people reject me?');
  const [nudgesConfirmed, setNudgesConfirmed] = useState(false);

  const samplePrompts = [
    'Why did the five people reject me?',
    'What were the top calls today?',
    'What has happened with David Miller from Acme?',
  ];

  const handleSend = () => {
    if (!query.trim()) return;
    setActivePrompt(query);
    setQuery('');
    toast.success('Analyzing live telemetry across campaigns and call transcripts...', {
      icon: '✨',
    });
  };

  const handleConfirmNudges = () => {
    setNudgesConfirmed(true);
    toast.success('Scheduled 3 check-ins for Nov 12th in cadence queue.', {
      icon: '✓',
    });
  };

  return (
    <div className="bg-surface-container-lowest rounded-2xl p-space-lg shadow-sm border border-outline-variant/40 flex flex-col gap-space-md">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-outline-variant/30 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-primary-container text-on-primary-container flex items-center justify-center font-bold shadow-sm">
            <span className="material-symbols-outlined text-[20px] select-none">auto_awesome</span>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="font-headline-sm text-headline-sm text-on-surface font-serif font-semibold">
                Nectar Intelligence Desk
              </h2>
              <span className="px-2 py-0.5 rounded-full bg-surface-container font-label-sm text-label-sm text-on-surface-variant">
                v2.4 Core
              </span>
            </div>
            <p className="font-body-sm text-body-sm text-on-surface-variant text-[13px]">
              Synthesized live across 4 active campaigns, 32 call transcripts &amp; 418 outbound touches
            </p>
          </div>
        </div>
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#EDF4F0] text-tertiary font-label-sm text-label-sm font-semibold self-start sm:self-auto border border-tertiary/20">
          <span className="material-symbols-outlined text-[15px] select-none">verified_user</span>
          <span>All data local to workspace</span>
        </span>
      </div>

      {/* Suggested Query Pills */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="font-label-sm text-label-sm text-outline uppercase font-semibold">
          Try asking:
        </span>
        {samplePrompts.map((p) => (
          <button
            key={p}
            type="button"
            onClick={() => setActivePrompt(p)}
            className={`px-3 py-1 rounded-full font-label-sm text-label-sm transition-all text-left flex items-center gap-1.5 ${
              activePrompt === p
                ? 'bg-primary-container text-on-primary-container font-semibold shadow-sm'
                : 'bg-surface-container hover:bg-surface-container-high text-on-surface-variant'
            }`}
          >
            <span className="material-symbols-outlined text-[14px] select-none">lightbulb</span>
            <span>{p}</span>
          </button>
        ))}
      </div>

      {/* Interactive Chat Output Box */}
      <div className="bg-surface-container-low rounded-xl p-space-md border border-outline-variant/30 flex flex-col gap-3">
        {/* User prompt message */}
        <div className="flex justify-end">
          <div className="px-4 py-2 rounded-2xl bg-surface-container-lowest text-on-surface font-body-sm text-body-sm shadow-sm border border-outline-variant/40 flex items-center gap-2">
            <span>{activePrompt}</span>
            <div className="w-5 h-5 rounded-full bg-[#7F5700] text-white flex items-center justify-center text-[10px] font-bold font-serif">
              R
            </div>
          </div>
        </div>

        {/* Overnight analysis answer card */}
        <div className="flex flex-col gap-3 bg-surface-container-lowest p-space-md rounded-xl border border-outline-variant/30 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-tertiary" />
              <span className="font-label-md text-label-md font-semibold text-on-surface">
                Overnight Analysis
              </span>
              <span className="text-outline-variant">•</span>
              <span className="font-label-sm text-label-sm text-tertiary font-medium">0 Lost Leads</span>
            </div>
            <span className="font-label-sm text-label-sm text-outline">6:42 AM</span>
          </div>

          {/* 3 Status Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {/* Card 1 */}
            <div className="p-3 rounded-lg bg-surface-container-low border border-outline-variant/30 flex flex-col justify-between gap-2">
              <div className="flex items-center justify-between">
                <span className="px-2 py-0.5 rounded-full bg-surface-container-highest text-on-surface-variant font-label-sm text-label-sm font-semibold">
                  3x Timing Freeze
                </span>
                <span className="font-label-sm text-label-sm text-outline">Nov 12</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-7 h-7 rounded bg-[#7F5700] text-white font-serif font-bold text-xs flex items-center justify-center">
                  NW
                </span>
                <div className="font-label-md text-label-md font-semibold text-on-surface truncate">
                  Northwind &amp; Stripe
                </div>
              </div>
              <div className="flex items-center justify-between text-xs text-on-surface-variant">
                <span>Q4 freeze until Nov</span>
                <span className="px-2 py-0.5 rounded bg-surface-container text-outline font-semibold">
                  Paused
                </span>
              </div>
            </div>

            {/* Card 2 */}
            <div className="p-3 rounded-lg bg-surface-container-low border border-outline-variant/30 flex flex-col justify-between gap-2">
              <div className="flex items-center justify-between">
                <span className="px-2 py-0.5 rounded-full bg-surface-container-highest text-on-surface-variant font-label-sm text-label-sm font-semibold">
                  1x Locked
                </span>
                <span className="font-label-sm text-label-sm text-outline">Oct 2026</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-7 h-7 rounded bg-[#366853] text-white font-serif font-bold text-xs flex items-center justify-center">
                  DD
                </span>
                <div className="font-label-md text-label-md font-semibold text-on-surface truncate">
                  Datadog Renewed
                </div>
              </div>
              <div className="flex items-center justify-between text-xs text-on-surface-variant">
                <span>Signed 2 yr deal</span>
                <span className="px-2 py-0.5 rounded bg-surface-container text-outline font-semibold">
                  Archived
                </span>
              </div>
            </div>

            {/* Card 3 */}
            <div className="p-3 rounded-lg bg-surface-container-low border border-outline-variant/30 flex flex-col justify-between gap-2">
              <div className="flex items-center justify-between">
                <span className="px-2 py-0.5 rounded-full bg-[#FEF7E6] text-[#7F5700] font-label-sm text-label-sm font-semibold">
                  1x Security
                </span>
                <span className="font-label-sm text-label-sm text-primary font-bold">High-Intent</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-7 h-7 rounded bg-[#BA1A1A] text-white font-serif font-bold text-xs flex items-center justify-center">
                  FT
                </span>
                <div className="font-label-md text-label-md font-semibold text-on-surface truncate">
                  FinTech On-Prem
                </div>
              </div>
              <div className="flex items-center justify-between text-xs text-on-surface-variant">
                <span>Sarah Rao req. SOC2</span>
                <span className="px-2 py-0.5 rounded bg-primary-container text-on-primary-container font-semibold">
                  Draft Ready
                </span>
              </div>
            </div>
          </div>

          {/* Action Nudge Bar */}
          <div className="p-3 bg-surface-container-low rounded-xl flex items-center justify-between gap-3 flex-wrap">
            <div className="flex items-center gap-2 text-on-surface font-body-sm text-body-sm font-medium">
              <span className="material-symbols-outlined text-[18px] text-primary select-none">bolt</span>
              <span>Schedule 3 check-ins for Nov 12th?</span>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                className="px-3 py-1 rounded-full text-on-surface-variant hover:bg-surface-container font-label-sm text-label-sm transition-colors"
              >
                Edit
              </button>
              <button
                type="button"
                onClick={handleConfirmNudges}
                disabled={nudgesConfirmed}
                className="px-4 py-1.5 rounded-full bg-primary-container text-on-primary-container hover:opacity-95 font-label-sm text-label-sm font-bold shadow-sm transition-all"
              >
                {nudgesConfirmed ? '✓ Confirmed' : '✓ Confirm Nudges'}
              </button>
            </div>
          </div>
        </div>

        {/* Input prompt field */}
        <div className="relative flex items-center">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask anything across leads, transcripts, objections, and logs..."
            className="w-full bg-surface-container-lowest rounded-xl pl-4 pr-24 py-3 font-body-sm text-body-sm text-on-surface placeholder:text-outline focus:outline-none shadow-sm border border-outline-variant/40 focus:border-primary transition-colors"
          />
          <div className="absolute right-2 flex items-center gap-1">
            <button
              type="button"
              className="w-8 h-8 rounded-full flex items-center justify-center text-outline hover:text-on-surface transition-colors"
            >
              <span className="material-symbols-outlined text-[18px] select-none">mic</span>
            </button>
            <button
              type="button"
              className="w-8 h-8 rounded-full flex items-center justify-center text-outline hover:text-on-surface transition-colors"
            >
              <span className="material-symbols-outlined text-[18px] select-none">attach_file</span>
            </button>
            <button
              type="button"
              onClick={handleSend}
              className="w-8 h-8 rounded-full bg-primary text-on-primary flex items-center justify-center hover:bg-primary-container hover:text-on-primary-container shadow-sm transition-all"
            >
              <span className="material-symbols-outlined text-[16px] select-none">arrow_upward</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
