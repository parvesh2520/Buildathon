import React, { useState } from 'react';

interface QuickOperationsProps {
  onHaltToggle?: (isHalted: boolean) => void;
}

export const QuickOperations: React.FC<QuickOperationsProps> = ({ onHaltToggle }) => {
  const [coldOffActive, setColdOffActive] = useState(true);
  const [oneVoiceActive, setOneVoiceActive] = useState(true);
  const [isHalted, setIsHalted] = useState(false);

  const handleHalt = () => {
    const nextState = !isHalted;
    setIsHalted(nextState);
    onHaltToggle?.(nextState);
  };

  return (
    <div className="bg-surface-container-lowest rounded-2xl p-space-lg shadow-sm border border-outline-variant/40 flex flex-col gap-space-md">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <span className="font-label-sm text-label-sm text-outline uppercase tracking-wider block font-medium">
            Deterministic Overrides
          </span>
          <h2 className="font-headline-md text-headline-md text-on-surface font-serif mt-0.5">
            Quick Fleet Operations
          </h2>
        </div>
        <span className="px-3 py-1 rounded-full bg-[#EDF4F0] text-tertiary font-label-sm text-label-sm font-semibold self-start sm:self-auto border border-tertiary/20">
          All Guardrails Active
        </span>
      </div>

      {/* 2x2 Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
        {/* 1. 90-Day Cold-off Rule */}
        <div className="bg-surface-container-low p-3.5 rounded-xl flex items-center justify-between gap-3">
          <div>
            <div className="font-label-md text-label-md font-semibold text-on-surface">
              90-Day Cold-off Rule
            </div>
            <div className="font-body-sm text-body-sm text-on-surface-variant text-[12px] mt-0.5">
              Prevents re-contacting any prospect after rejection
            </div>
          </div>
          <button
            type="button"
            onClick={() => setColdOffActive(!coldOffActive)}
            className={`w-11 h-6 rounded-full relative cursor-pointer flex items-center p-0.5 transition-colors flex-shrink-0 ${
              coldOffActive ? 'bg-inverse-surface' : 'bg-surface-container-high'
            }`}
          >
            <span
              className={`w-5 h-5 bg-surface-container-lowest rounded-full transition-transform shadow-sm ${
                coldOffActive ? 'translate-x-5' : 'translate-x-0'
              }`}
            />
          </button>
        </div>

        {/* 2. One-Voice per Company */}
        <div className="bg-surface-container-low p-3.5 rounded-xl flex items-center justify-between gap-3">
          <div>
            <div className="font-label-md text-label-md font-semibold text-on-surface">
              One-Voice per Company
            </div>
            <div className="font-body-sm text-body-sm text-on-surface-variant text-[12px] mt-0.5">
              Max 1 active outreach per domain at any time
            </div>
          </div>
          <button
            type="button"
            onClick={() => setOneVoiceActive(!oneVoiceActive)}
            className={`w-11 h-6 rounded-full relative cursor-pointer flex items-center p-0.5 transition-colors flex-shrink-0 ${
              oneVoiceActive ? 'bg-inverse-surface' : 'bg-surface-container-high'
            }`}
          >
            <span
              className={`w-5 h-5 bg-surface-container-lowest rounded-full transition-transform shadow-sm ${
                oneVoiceActive ? 'translate-x-5' : 'translate-x-0'
              }`}
            />
          </button>
        </div>

        {/* 3. Credit Burn Budget */}
        <div className="bg-surface-container-low p-3.5 rounded-xl flex items-center justify-between gap-3">
          <div>
            <div className="font-label-md text-label-md font-semibold text-on-surface">
              Credit Burn Budget
            </div>
            <div className="font-body-sm text-body-sm text-on-surface-variant text-[12px] mt-0.5">
              Hard freeze at $120.00/day across all 7 agents
            </div>
          </div>
          <span className="px-3 py-1.5 rounded-lg bg-surface-container-lowest font-headline-sm text-headline-sm text-on-surface font-serif font-bold shadow-sm border border-outline-variant/30 flex-shrink-0">
            $84 <span className="font-sans text-xs text-outline font-normal">/ $120</span>
          </span>
        </div>

        {/* 4. Emergency Fleet Halt */}
        <div className="bg-surface-container-low p-3.5 rounded-xl flex items-center justify-between gap-3">
          <div>
            <div className="font-label-md text-label-md font-semibold text-error">
              Emergency Fleet Halt
            </div>
            <div className="font-body-sm text-body-sm text-on-surface-variant text-[12px] mt-0.5">
              Instantly pauses all queued dispatches &amp; AI voice calls
            </div>
          </div>
          <button
            type="button"
            onClick={handleHalt}
            className={`px-4 py-1.5 rounded-full font-label-sm text-label-sm font-bold shadow-sm transition-all flex-shrink-0 ${
              isHalted
                ? 'bg-primary-container text-on-primary-container hover:opacity-90'
                : 'bg-error-container text-on-error-container hover:bg-error hover:text-on-error'
            }`}
          >
            {isHalted ? 'Resume Fleet' : 'Halt Fleet'}
          </button>
        </div>
      </div>
    </div>
  );
};
