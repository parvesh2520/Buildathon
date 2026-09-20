import React, { useState, useEffect } from 'react';

interface AgentCalibrationModalProps {
  agentId: number | null;
  onClose: () => void;
  onSave?: (agentId: number, config: any) => void;
}

export const AgentCalibrationModal: React.FC<AgentCalibrationModalProps> = ({
  agentId,
  onClose,
  onSave,
}) => {
  if (agentId === null) return null;

  // Local state for interactive sliders
  const [icpCutoff, setIcpCutoff] = useState(78);
  const [cloudWeight, setCloudWeight] = useState(75);
  const [hiresWeight, setHiresWeight] = useState(85);
  const [selectedTone, setSelectedTone] = useState('Understated');

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  const configs: Record<
    number,
    { badge: string; title: string; subtitle: string; icon: string; content: React.ReactNode }
  > = {
    0: {
      badge: 'Discovery Engine',
      title: 'Agent 0: Sourcing Scout Calibration',
      subtitle: 'Define real-time discovery criteria for automated prospect scraping across data partners.',
      icon: 'explore',
      content: (
        <div className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="font-label-sm text-label-sm uppercase text-outline font-semibold">
              Target Roles &amp; Titles (Comma Separated)
            </label>
            <input
              type="text"
              defaultValue="CTO, VP of Engineering, Head of Infrastructure, Chief Architect"
              className="w-full bg-surface-container-low rounded-xl px-3 py-2 text-on-surface font-body-md border border-outline-variant/30 focus:outline-none focus:bg-surface-container-lowest"
            />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="font-label-sm text-label-sm uppercase text-outline font-semibold">
                Minimum Funding Stage
              </label>
              <select
                defaultValue="Series B+ ($15M+)"
                className="w-full bg-surface-container-low rounded-xl px-3 py-2 text-on-surface font-body-md border border-outline-variant/30 focus:outline-none"
              >
                <option>Series A or B (Strict)</option>
                <option>Series B+ ($15M+)</option>
                <option>Seed to Growth</option>
              </select>
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="font-label-sm text-label-sm uppercase text-outline font-semibold">
                Geographic Boundary
              </label>
              <select
                defaultValue="United States & Canada Only"
                className="w-full bg-surface-container-low rounded-xl px-3 py-2 text-on-surface font-body-md border border-outline-variant/30 focus:outline-none"
              >
                <option>United States &amp; Canada Only</option>
                <option>North America + Western Europe</option>
                <option>Global (Exclude sanctioned regions)</option>
              </select>
            </div>
          </div>
          <div className="p-3.5 bg-surface-container-low rounded-xl flex items-center justify-between">
            <div>
              <div className="font-label-md text-label-md font-semibold text-on-surface">
                Auto-crosscheck GitHub Commits
              </div>
              <div className="font-body-sm text-body-sm text-on-surface-variant text-xs">
                Validate technical activity within the last 90 days
              </div>
            </div>
            <input type="checkbox" defaultChecked className="w-4 h-4 accent-primary" />
          </div>
        </div>
      ),
    },
    1: {
      badge: 'Signal Enrichment',
      title: 'Agent 1: Deep Research Signal Weights',
      subtitle:
        'Calibrate priority weights for intent signals. The research agent synthesizes podcast transcripts, SEC filings, and tech stacks.',
      icon: 'psychology',
      content: (
        <div className="flex flex-col gap-4">
          <div className="flex flex-col gap-2">
            <div className="flex justify-between items-center">
              <span className="font-label-md text-label-md font-semibold text-on-surface">
                Cloud Migration Mentions (Weight: {cloudWeight}%)
              </span>
              <span className="font-label-sm text-label-sm font-bold text-primary">High Priority</span>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              value={cloudWeight}
              onChange={(e) => setCloudWeight(Number(e.target.value))}
              className="w-full accent-primary cursor-pointer"
            />
          </div>

          <div className="flex flex-col gap-2">
            <div className="flex justify-between items-center">
              <div>
                <span className="font-label-md text-label-md font-semibold text-on-surface">
                  Recent Senior Engineering Hires
                </span>
                <p className="font-body-sm text-body-sm text-on-surface-variant text-xs">
                  Surges of &gt;3 DevOps / Infra engineers in 60 days
                </p>
              </div>
              <span className="font-headline-sm text-headline-sm text-tertiary font-serif">
                {hiresWeight}%
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              value={hiresWeight}
              onChange={(e) => setHiresWeight(Number(e.target.value))}
              className="w-full accent-tertiary cursor-pointer"
            />
          </div>

          <div className="p-3.5 bg-surface-container-low rounded-xl flex items-center justify-between">
            <span className="font-label-md text-label-md font-semibold text-on-surface">
              Podcast &amp; Tech Talk Transcript OCR
            </span>
            <span className="px-2.5 py-1 rounded-md bg-tertiary-container text-on-tertiary-container font-label-sm text-label-sm font-bold">
              Active (Whisper-v3)
            </span>
          </div>
        </div>
      ),
    },
    2: {
      badge: 'Disqualification Gate',
      title: 'Agent 2: Strict ICP Decision Scoring Gate',
      subtitle: 'Hard gate disqualification before any outreach touches prospects.',
      icon: 'block',
      content: (
        <div className="flex flex-col gap-4">
          <div className="p-3.5 bg-error-container/40 rounded-xl border border-error/20 text-on-surface text-body-sm">
            <strong className="font-semibold text-error">Deterministic Guardrail:</strong> No prospect below
            the cutoff will receive outbound messages under any circumstance.
          </div>

          <div className="flex flex-col gap-2">
            <div className="flex justify-between items-center">
              <label className="font-label-sm text-label-sm uppercase text-outline font-semibold">
                Minimum Pass Cutoff Score
              </label>
              <span className="font-headline-md text-headline-md text-error font-serif font-bold">
                {icpCutoff} / 100
              </span>
            </div>
            <input
              type="range"
              min="50"
              max="95"
              value={icpCutoff}
              onChange={(e) => setIcpCutoff(Number(e.target.value))}
              className="w-full accent-error cursor-pointer"
            />
          </div>

          <div className="flex flex-col gap-2">
            <label className="font-label-sm text-label-sm uppercase text-outline font-semibold">
              Instant Disqualification Tags
            </label>
            <div className="flex flex-wrap gap-2">
              <span className="px-3 py-1 rounded-full bg-surface-container font-label-sm text-label-sm">
                Company size &lt; 20
              </span>
              <span className="px-3 py-1 rounded-full bg-surface-container font-label-sm text-label-sm">
                Consultancies / Agencies
              </span>
              <span className="px-3 py-1 rounded-full bg-surface-container font-label-sm text-label-sm">
                Inactive on LinkedIn &gt; 1 yr
              </span>
            </div>
          </div>
        </div>
      ),
    },
    3: {
      badge: 'Cadence Engine',
      title: 'Agent 3: Outreach Timing & Scheduling',
      subtitle: 'Lock dispatching strictly to recipients local business hours.',
      icon: 'schedule',
      content: (
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="font-label-sm text-label-sm uppercase text-outline font-semibold">
                Morning Window
              </label>
              <input
                type="text"
                defaultValue="9:00 AM – 11:30 AM"
                className="w-full bg-surface-container-low rounded-xl px-3 py-2 text-on-surface font-body-md border border-outline-variant/30"
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="font-label-sm text-label-sm uppercase text-outline font-semibold">
                Afternoon Window
              </label>
              <input
                type="text"
                defaultValue="2:00 PM – 4:30 PM"
                className="w-full bg-surface-container-low rounded-xl px-3 py-2 text-on-surface font-body-md border border-outline-variant/30"
              />
            </div>
          </div>
          <div className="p-3.5 bg-surface-container-low rounded-xl flex items-center justify-between">
            <span className="font-label-md text-label-md font-semibold text-on-surface">
              Strict 1 touch per 24 hour cap
            </span>
            <input type="checkbox" defaultChecked className="w-4 h-4 accent-primary" />
          </div>
        </div>
      ),
    },
    4: {
      badge: 'Editorial Tone',
      title: 'Agent 4: Personalization, Tone & Voice',
      subtitle: 'Executive peers communicate with brevity. Restricts copy to concise, high-signal language.',
      icon: 'format_quote',
      content: (
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-3 gap-3">
            {['Understated', 'Direct Inquiry', 'Technical Whitepaper'].map((tone) => (
              <button
                key={tone}
                type="button"
                onClick={() => setSelectedTone(tone)}
                className={`p-3 rounded-xl border text-center transition-all ${
                  selectedTone === tone
                    ? 'bg-primary-container/20 border-primary font-bold'
                    : 'bg-surface-container-low border-transparent'
                }`}
              >
                <div className="font-label-md text-label-md text-on-surface">{tone}</div>
                <div className="text-xs text-on-surface-variant mt-0.5">
                  {tone === 'Understated'
                    ? 'Under 65 words'
                    : tone === 'Direct Inquiry'
                    ? 'Problem-led'
                    : 'Signal cite'}
                </div>
              </button>
            ))}
          </div>
          <div className="flex flex-col gap-1.5">
            <label className="font-label-sm text-label-sm uppercase text-outline font-semibold">
              Salutation Pattern
            </label>
            <input
              type="text"
              defaultValue="Hi [First_Name] — noticed your team's migration to Kubernetes 1.29..."
              className="w-full bg-surface-container-low rounded-xl px-3 py-2 text-on-surface font-body-md border border-outline-variant/30"
            />
          </div>
        </div>
      ),
    },
    5: {
      badge: 'Safety & Handoff',
      title: 'Agent 5: Conversation Basket & Rule Inspector',
      subtitle: 'Inspect deterministic routing baskets. Immediate legal quarantine on sensitive keywords.',
      icon: 'shield',
      content: (
        <div className="flex flex-col gap-3">
          <div className="p-3.5 bg-surface-container-low rounded-xl flex items-center justify-between">
            <div>
              <span className="font-label-md text-label-md font-bold text-tertiary">
                Questions &amp; Interest
              </span>
              <p className="text-xs text-on-surface-variant">AI crafts draft • Ramya 1-click approve</p>
            </div>
            <span className="font-label-sm text-label-sm font-semibold bg-tertiary-container/40 text-on-tertiary-container px-2.5 py-1 rounded-md">
              Auto-assist
            </span>
          </div>
          <div className="p-3.5 bg-surface-container-low rounded-xl flex items-center justify-between">
            <div>
              <span className="font-label-md text-label-md font-bold text-error">
                Security / Legal / Pricing
              </span>
              <p className="text-xs text-on-surface-variant">Outreach halted instantly • Ramya notified</p>
            </div>
            <span className="font-label-sm text-label-sm font-semibold bg-error-container text-on-error-container px-2.5 py-1 rounded-md">
              Hard Escalation
            </span>
          </div>
        </div>
      ),
    },
    6: {
      badge: 'Voice AI Latency',
      title: 'Agent 6: Voice AI & Whisper Barge Configuration',
      subtitle: 'Configure ultra-low latency voice models and supervisor coaching whisper channels.',
      icon: 'mic',
      content: (
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="p-3.5 bg-surface-container-low rounded-xl">
              <span className="font-label-sm text-label-sm text-outline uppercase block text-[10px]">
                Target Latency
              </span>
              <div className="font-headline-sm text-headline-sm text-tertiary font-serif mt-0.5">240 ms</div>
              <span className="text-xs text-on-surface-variant">Streaming WebRTC</span>
            </div>
            <div className="p-3.5 bg-surface-container-low rounded-xl">
              <span className="font-label-sm text-label-sm text-outline uppercase block text-[10px]">
                Whisper Mode
              </span>
              <div className="font-headline-sm text-headline-sm text-on-surface font-serif mt-0.5">
                Barge-in Armed
              </div>
              <span className="text-xs text-primary font-semibold">Supervisor audio priority</span>
            </div>
          </div>
          <div className="p-3.5 bg-surface-container-low rounded-xl flex items-center justify-between">
            <span className="font-label-md text-label-md font-semibold text-on-surface">
              Maximum Call Duration (Auto-escalate)
            </span>
            <span className="font-label-md text-label-md font-bold text-on-surface">3m 30s</span>
          </div>
        </div>
      ),
    },
  };

  const current = configs[agentId];
  if (!current) return null;

  const handleSave = () => {
    onSave?.(agentId, { icpCutoff, cloudWeight, hiresWeight, selectedTone });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-inverse-surface/40 backdrop-blur-sm">
      <div className="bg-surface-container-lowest rounded-2xl max-w-xl w-full p-space-lg shadow-2xl border border-outline-variant/40 flex flex-col gap-space-md animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex flex-col">
            <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-surface-container text-on-surface-variant font-label-sm text-label-sm font-semibold w-max mb-1">
              <span className="material-symbols-outlined text-[14px] select-none">{current.icon}</span>
              <span>{current.badge}</span>
            </div>
            <h3 className="font-headline-md text-headline-md text-on-surface font-serif mt-1">
              {current.title}
            </h3>
            <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">{current.subtitle}</p>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full flex items-center justify-center text-outline hover:text-on-surface hover:bg-surface-container transition-colors flex-shrink-0"
          >
            <span className="material-symbols-outlined text-[20px] select-none">close</span>
          </button>
        </div>

        {/* Dynamic Content */}
        <div className="py-2">{current.content}</div>

        {/* Footer actions */}
        <div className="pt-3 border-t border-outline-variant/30 flex items-center justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-full text-on-surface-variant hover:bg-surface-container font-label-md text-label-md transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-5 py-2 rounded-full bg-primary-container text-on-primary-container hover:opacity-95 font-label-md text-label-md font-semibold shadow-sm transition-all"
          >
            Save Calibration
          </button>
        </div>
      </div>
    </div>
  );
};
