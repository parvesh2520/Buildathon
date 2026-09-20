import React from 'react';

export const BestHoursChart: React.FC = () => {
  const hours = [
    { label: '8a', height: '18%', peak: false },
    { label: '9a', height: '70%', peak: true },
    { label: '10a', height: '88%', peak: true },
    { label: '11a', height: '62%', peak: true },
    { label: '12p', height: '24%', peak: false },
    { label: '1p', height: '32%', peak: false },
    { label: '2p', height: '78%', peak: true },
    { label: '3p', height: '74%', peak: true },
    { label: '4p', height: '36%', peak: false },
    { label: '5p', height: '16%', peak: false },
  ];

  return (
    <div className="bg-surface-container-lowest rounded-2xl p-space-lg shadow-sm border border-outline-variant/40 flex flex-col gap-space-md">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h3 className="font-headline-sm text-headline-sm text-on-surface font-serif font-semibold">
            Best hours to land replies
          </h3>
          <p className="font-body-sm text-body-sm text-on-surface-variant text-[13px] mt-0.5">
            Prospect local time zone normalized across 1,420 historical touches
          </p>
        </div>
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#EDF4F0] text-tertiary font-label-sm text-label-sm font-semibold self-start sm:self-auto border border-tertiary/20">
          <span className="w-2 h-2 rounded-full bg-tertiary" />
          <span>Peak: 10:15 AM &amp; 2:40 PM</span>
        </span>
      </div>

      {/* Bar Chart */}
      <div className="h-44 w-full flex items-end justify-between gap-2 pt-6 pb-2 px-1">
        {hours.map((h) => (
          <div key={h.label} className="flex-1 h-full flex flex-col items-center justify-end gap-2 group">
            <div className="w-full max-w-[42px] h-full flex items-end justify-center">
              <div
                style={{ height: h.height }}
                className={`w-full rounded-md transition-all duration-300 group-hover:opacity-90 ${
                  h.peak ? 'bg-[#E6A219]' : 'bg-surface-container-high'
                }`}
              />
            </div>
            <span className="font-label-sm text-label-sm text-outline font-medium">{h.label}</span>
          </div>
        ))}
      </div>

      {/* Footer Banner */}
      <div className="p-3 bg-surface-container-low rounded-xl flex items-center justify-between gap-2 text-body-sm text-body-sm flex-wrap">
        <div className="flex items-center gap-2 text-on-surface-variant">
          <span className="w-2 h-2 rounded-full bg-[#E6A219]" />
          <span>Optimal outbound dispatch window is auto-synced to each prospect's timezone</span>
        </div>
        <span className="font-label-sm text-label-sm font-semibold text-tertiary">
          99.1% delivered on-slot
        </span>
      </div>
    </div>
  );
};
