import React from 'react';

interface NectarHeaderProps {
  onNewContact?: () => void;
  onRunSequence?: () => void;
}

export const NectarHeader: React.FC<NectarHeaderProps> = ({
  onNewContact,
  onRunSequence,
}) => {
  return (
    <header className="fixed top-0 left-72 right-0 h-16 bg-surface/80 backdrop-blur-xl shadow-[0_1px_8px_rgba(0,0,0,0.04)] z-40 flex items-center justify-between px-space-lg border-b border-outline-variant/30">
      {/* Breadcrumb */}
      <div className="flex items-center gap-space-xs text-outline font-label-md text-label-md">
        <span className="hover:text-on-surface cursor-pointer">Workspace</span>
        <span className="material-symbols-outlined text-[16px] select-none">chevron_right</span>
        <span className="text-on-surface font-label-lg text-label-lg font-semibold">
          Outreach Pipeline
        </span>
      </div>

      {/* Action Controls */}
      <div className="flex items-center gap-space-md">
        <div className="flex items-center gap-space-sm">
          <button
            onClick={onNewContact}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-surface-container-lowest text-on-surface hover:bg-surface-container font-label-md text-label-md shadow-[0_1px_2px_rgba(39,39,42,0.04)] border border-outline-variant/40 transition-colors"
          >
            <span className="material-symbols-outlined text-[18px] text-outline select-none">add</span>
            <span>New Contact</span>
          </button>
          <button
            onClick={onRunSequence}
            className="flex items-center gap-1.5 px-4 py-1.5 rounded-full bg-primary-container text-on-primary-container hover:opacity-95 font-label-md text-label-md font-semibold shadow-[0_2px_6px_rgba(39,39,42,0.08)] transition-all"
          >
            <span className="material-symbols-outlined text-[18px] select-none">bolt</span>
            <span>Run Sequence</span>
          </button>
        </div>


        <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-on-primary">
          <span className="material-symbols-outlined text-[18px] select-none">person</span>
        </div>
      </div>
    </header>
  );
};
