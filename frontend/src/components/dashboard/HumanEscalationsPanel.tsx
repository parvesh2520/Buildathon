import React, { useState } from 'react';
import toast from 'react-hot-toast';

export const HumanEscalationsPanel: React.FC = () => {
  const [filter, setFilter] = useState<'all' | 'pricing' | 'security' | 'objections'>('all');
  const [approvedItems, setApprovedItems] = useState<string[]>([]);

  const handleApprove = (id: string, label: string) => {
    setApprovedItems((prev) => [...prev, id]);
    toast.success(`${label} approved and queued for delivery.`, {
      icon: '✓',
    });
  };

  const handleWhisper = () => {
    toast('Connecting whisper audio channel to David Miller...', {
      icon: '🎧',
    });
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="bg-surface-container-lowest rounded-2xl p-space-lg shadow-sm border border-outline-variant/40 flex flex-col gap-space-md">
        {/* Header */}
        <div className="flex items-start justify-between gap-2">
          <div>
            <h3 className="font-headline-sm text-headline-sm text-on-surface font-serif font-semibold">
              Escalations Pending Human Action
            </h3>
            <p className="font-body-sm text-body-sm text-on-surface-variant text-[13px] mt-1">
              Agents safely freeze outbounds whenever money, contracts, or high-intent warm objections occur.
            </p>
          </div>
          <span className="px-3 py-1 rounded-full bg-primary-container text-on-primary-container font-label-sm text-label-sm font-bold shadow-sm flex-shrink-0">
            8 require you
          </span>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-1.5 flex-wrap">
          {[
            { id: 'all', label: 'All (8)' },
            { id: 'pricing', label: 'Pricing (2)' },
            { id: 'security', label: 'Security (1)' },
            { id: 'objections', label: 'Objections (3)' },
          ].map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setFilter(tab.id as any)}
              className={`px-3 py-1 rounded-full font-label-sm text-label-sm font-medium transition-all ${
                filter === tab.id
                  ? 'bg-inverse-surface text-surface'
                  : 'bg-surface-container text-on-surface-variant hover:bg-surface-container-high'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Escalation Cards List */}
        <div className="flex flex-col gap-3">
          {/* 1. David Miller (Live Call) */}
          {(filter === 'all' || filter === 'objections') && (
            <div className="p-3.5 rounded-xl bg-surface-container-low border border-outline-variant/30 flex flex-col gap-2.5">
              <div className="flex items-center justify-between text-xs">
                <span className="inline-flex items-center gap-1.5 font-bold text-error tracking-wider uppercase">
                  <span className="w-2 h-2 rounded-full bg-error animate-pulse" />
                  LIVE CALL • 04:31
                </span>
                <span className="material-symbols-outlined text-[16px] text-error select-none">equalizer</span>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-full bg-[#E6A219]/20 text-[#7F5700] font-serif font-bold text-xs flex items-center justify-center">
                    DM
                  </div>
                  <div>
                    <div className="font-label-md text-label-md font-semibold text-on-surface leading-tight">
                      David Miller
                    </div>
                    <div className="text-xs text-on-surface-variant">VP Tech • Acme Corp</div>
                  </div>
                </div>
                <span className="px-2 py-0.5 rounded-md bg-[#EDF4F0] text-tertiary font-label-sm text-label-sm font-bold flex items-center gap-1">
                  <span>👍</span> 88%
                </span>
              </div>

              <div className="p-2.5 bg-surface-container-lowest rounded-lg text-body-sm text-body-sm text-on-surface italic border border-outline-variant/20">
                “Looking at a couple tools, honestly.”
              </div>

              <button
                type="button"
                onClick={handleWhisper}
                className="w-full py-2 rounded-xl bg-inverse-surface text-surface hover:bg-on-surface font-label-sm text-label-sm font-semibold flex items-center justify-center gap-1.5 shadow-sm transition-all"
              >
                <span className="material-symbols-outlined text-[16px] select-none">headphones</span>
                <span>Listen Live / Whisper</span>
              </button>
            </div>
          )}

          {/* 2. Tom Becker (Pricing) */}
          {(filter === 'all' || filter === 'pricing') && (
            <div className="p-3.5 rounded-xl bg-surface-container-low border border-outline-variant/30 flex flex-col gap-2.5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-full bg-[#7F5700]/20 text-[#7F5700] font-serif font-bold text-xs flex items-center justify-center">
                    TB
                  </div>
                  <div>
                    <div className="font-label-md text-label-md font-semibold text-on-surface leading-tight">
                      Tom Becker
                    </div>
                    <div className="text-xs text-on-surface-variant">Northwind • +40 Seats</div>
                  </div>
                </div>
                <span className="px-2 py-0.5 rounded-md bg-[#FEF7E6] text-[#7F5700] font-label-sm text-label-sm font-semibold">
                  Pricing Tier
                </span>
              </div>

              <div className="p-2.5 bg-surface-container-lowest rounded-lg text-body-sm text-body-sm text-on-surface italic border border-outline-variant/20">
                “Cost for 40 seats expansion next Q?”
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => handleApprove('tb', 'Tier 2 Quote')}
                  disabled={approvedItems.includes('tb')}
                  className="flex-1 py-1.5 rounded-full bg-primary-container text-on-primary-container hover:opacity-95 font-label-sm text-label-sm font-bold shadow-sm transition-all"
                >
                  {approvedItems.includes('tb') ? '✓ Quote Sent' : 'Send Tier 2 Quote'}
                </button>
                <button
                  type="button"
                  className="px-3 py-1.5 rounded-full bg-surface-container hover:bg-surface-container-high text-on-surface font-label-sm text-label-sm transition-colors"
                >
                  Take Over
                </button>
              </div>
            </div>
          )}

          {/* 3. Sarah Rao (Security) */}
          {(filter === 'all' || filter === 'security') && (
            <div className="p-3.5 rounded-xl bg-surface-container-low border border-outline-variant/30 flex flex-col gap-2.5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-full bg-[#366853]/20 text-[#366853] font-serif font-bold text-xs flex items-center justify-center">
                    SR
                  </div>
                  <div>
                    <div className="font-label-md text-label-md font-semibold text-on-surface leading-tight">
                      Sarah Rao
                    </div>
                    <div className="text-xs text-on-surface-variant">HDFC • Frankfurt Data</div>
                  </div>
                </div>
                <span className="px-2 py-0.5 rounded-md bg-[#EDF4F0] text-tertiary font-label-sm text-label-sm font-semibold">
                  SOC-2
                </span>
              </div>

              <div className="p-2.5 bg-surface-container-lowest rounded-lg text-body-sm text-body-sm text-on-surface italic border border-outline-variant/20">
                “Do you support Frankfurt data residency?”
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => handleApprove('sr', 'SOC-2 Snippet')}
                  disabled={approvedItems.includes('sr')}
                  className="flex-1 py-1.5 rounded-full bg-surface-container-lowest hover:bg-surface-container text-on-surface font-label-sm text-label-sm font-semibold border border-outline-variant/40 shadow-sm transition-all"
                >
                  {approvedItems.includes('sr') ? '✓ Approved' : '✓ Approve Snippet'}
                </button>
                <button
                  type="button"
                  className="px-3 py-1.5 rounded-full text-on-surface-variant hover:bg-surface-container font-label-sm text-label-sm transition-colors"
                >
                  Edit
                </button>
              </div>
            </div>
          )}

          {/* 4. Meera Krishnan (Referral) */}
          {(filter === 'all' || filter === 'objections') && (
            <div className="p-3.5 rounded-xl bg-surface-container-low border border-outline-variant/30 flex flex-col gap-2.5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-full bg-surface-container-highest text-on-surface font-serif font-bold text-xs flex items-center justify-center">
                    MK
                  </div>
                  <div>
                    <div className="font-label-md text-label-md font-semibold text-on-surface leading-tight">
                      Meera Krishnan
                    </div>
                    <div className="text-xs text-on-surface-variant">Paystack → Rohit (VP Eng)</div>
                  </div>
                </div>
                <span className="px-2 py-0.5 rounded-md bg-surface-container font-label-sm text-label-sm text-outline font-semibold">
                  Referral
                </span>
              </div>

              <div className="p-2.5 bg-surface-container-lowest rounded-lg text-body-sm text-body-sm text-on-surface italic border border-outline-variant/20">
                “Talk to Rohit over in Core Infra.”
              </div>

              <button
                type="button"
                onClick={() => handleApprove('mk', 'Rohit Outreach')}
                disabled={approvedItems.includes('mk')}
                className="w-full py-1.5 rounded-full bg-primary-container text-on-primary-container hover:opacity-95 font-label-sm text-label-sm font-bold shadow-sm transition-all flex items-center justify-center gap-1"
              >
                <span className="material-symbols-outlined text-[15px] select-none">play_arrow</span>
                <span>{approvedItems.includes('mk') ? '✓ Outreach Scheduled' : 'Approve Rohit Outreach'}</span>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Strict Human-in-the-Loop Active Note Box */}
      <div className="p-space-md rounded-2xl bg-[#FEF7E6] border border-[#E6A219]/30 text-body-sm text-body-sm flex flex-col gap-1.5 shadow-sm">
        <div className="flex items-center gap-2 text-[#7F5700] font-label-md text-label-md font-bold">
          <span className="material-symbols-outlined text-[18px] select-none">verified_user</span>
          <span>Strict Human-in-the-Loop Active</span>
        </div>
        <p className="text-on-surface-variant text-[13px] leading-relaxed">
          Zero automated messages are dispatched when negative sentiment or legal inquiries are identified. You remain in control of all contract boundaries.
        </p>
      </div>
    </div>
  );
};
