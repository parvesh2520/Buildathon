import React from 'react';

export const SignalsWinningReplies: React.FC = () => {
  const signals = [
    {
      icon: 'person_add',
      title: 'Engineering hiring surge (>5 DevOps roles open)',
      rate: '27%',
      width: '27%',
      barColor: 'bg-[#366853]',
    },
    {
      icon: 'article',
      title: 'Recent engineering blog post on CI bottlenecks',
      rate: '21%',
      width: '21%',
      barColor: 'bg-[#E6A219]',
    },
    {
      icon: 'attach_money',
      title: 'New Series B / Growth funding announcement',
      rate: '17%',
      width: '17%',
      barColor: 'bg-[#7F5700]',
    },
    {
      icon: 'layers',
      title: 'Modern stack migration (Kubernetes / Datadog mentions)',
      rate: '12%',
      width: '12%',
      barColor: 'bg-inverse-surface',
    },
  ];

  return (
    <div className="bg-surface-container-lowest rounded-2xl p-space-lg shadow-sm border border-outline-variant/40 flex flex-col gap-space-md">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-headline-sm text-headline-sm text-on-surface font-serif font-semibold">
            Signals winning replies right now
          </h3>
          <p className="font-body-sm text-body-sm text-on-surface-variant text-[13px] mt-0.5">
            Which intent triggers generate conversational replies
          </p>
        </div>
        <button
          type="button"
          className="font-label-sm text-label-sm font-semibold text-primary hover:underline flex items-center gap-1"
        >
          Signal rules <span>↗</span>
        </button>
      </div>

      {/* Signal Rows */}
      <div className="flex flex-col gap-3 pt-1">
        {signals.map((s) => (
          <div key={s.title} className="flex flex-col gap-1.5">
            <div className="flex items-center justify-between text-body-sm text-body-sm">
              <div className="flex items-center gap-2 text-on-surface font-medium">
                <span className="material-symbols-outlined text-[16px] text-outline select-none">
                  {s.icon}
                </span>
                <span>{s.title}</span>
              </div>
              <span className="font-label-sm text-label-sm font-bold text-on-surface font-serif">
                {s.rate} <span className="font-sans font-normal text-outline text-xs">reply rate</span>
              </span>
            </div>
            <div className="h-2 w-full bg-surface-container-high rounded-full overflow-hidden">
              <div
                className={`h-full ${s.barColor} rounded-full transition-all duration-500`}
                style={{ width: s.width }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
