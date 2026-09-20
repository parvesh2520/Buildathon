import React from 'react';

export const TransitVelocity: React.FC = () => {
  const steps = [
    { num: '0', label: 'Source', value: '1,420', bg: 'bg-[#E6A219]', text: 'text-white' },
    { num: '1', label: 'Enrich', value: '1,280', bg: 'bg-[#366853]', text: 'text-white' },
    { num: '2', label: 'Gate Cut', value: '172 pass', bg: 'bg-surface-container-lowest border-2 border-error', text: 'text-error' },
    { num: '3–4', label: 'Dispatched', value: '172 sent', bg: 'bg-[#7F5700]', text: 'text-white' },
    { num: '5', label: 'Replies', value: '38 resp', bg: 'bg-[#86BAA1]', text: 'text-[#174B38]' },
    { num: '✓', label: 'Booked', value: '14 calls', bg: 'bg-inverse-surface', text: 'text-white' },
  ];

  return (
    <div className="bg-surface-container-lowest rounded-2xl p-space-lg shadow-sm border border-outline-variant/40 flex flex-col gap-space-md">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <span className="font-label-sm text-label-sm text-outline uppercase tracking-wider block font-medium">
            Realtime Conversion Trajectory
          </span>
          <h2 className="font-headline-md text-headline-md text-on-surface font-serif mt-0.5">
            Fleet Transit Velocity &amp; Pipeline Health
          </h2>
        </div>
        <span className="px-3 py-1 rounded-full bg-surface-container text-on-surface-variant font-label-sm text-label-sm font-semibold self-start sm:self-auto">
          Cohort: Last 24 Hours
        </span>
      </div>

      {/* Stepper Graphic */}
      <div className="py-3 px-2 overflow-x-auto">
        <div className="min-w-[620px] flex items-center justify-between relative">
          {/* Connector Line */}
          <div className="absolute left-6 right-6 top-5 h-0.5 bg-outline-variant/50 -z-0" />

          {steps.map((step) => (
            <div key={step.label} className="relative z-10 flex flex-col items-center gap-2">
              <div
                className={`w-10 h-10 rounded-full ${step.bg} ${step.text} flex items-center justify-center font-serif font-bold text-sm shadow-sm`}
              >
                {step.num}
              </div>
              <div className="text-center">
                <span className="font-label-sm text-label-sm text-outline block">{step.label}</span>
                <span className="font-headline-sm text-[15px] font-serif font-semibold text-on-surface">
                  {step.value}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Health Badge Footer */}
      <div className="p-3 bg-surface-container-low rounded-xl flex flex-wrap items-center justify-between gap-3 text-body-sm text-body-sm">
        <div className="flex items-center gap-2 font-medium text-tertiary">
          <span className="material-symbols-outlined text-[18px] text-tertiary select-none">
            check_circle
          </span>
          <span className="font-semibold">Pipeline Health: Pristine</span>
        </div>

        <div className="flex items-center gap-3 text-on-surface-variant flex-wrap font-medium">
          <span className="px-2.5 py-0.5 rounded-full bg-[#EDF4F0] text-tertiary font-label-sm text-label-sm font-semibold">
            Zero Bottlenecks
          </span>
          <span>• 2.8x Industry Reply Avg</span>
          <span>• 0 Spam Traps</span>
        </div>
      </div>
    </div>
  );
};
