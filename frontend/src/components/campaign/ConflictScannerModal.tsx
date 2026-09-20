import { useState, useEffect } from 'react';
import { AlertTriangle, CheckCircle2, ShieldAlert, X, ArrowRight, RefreshCw } from 'lucide-react';
import { getCampaignConflicts, resolveConflict } from '@/api/system';
import { CampaignConflict } from '@/types';
import toast from 'react-hot-toast';
import { cn } from '@/lib/utils';

interface ConflictScannerModalProps {
  onClose: () => void;
}

export function ConflictScannerModal({ onClose }: ConflictScannerModalProps) {
  const [loading, setLoading] = useState(true);
  const [conflicts, setConflicts] = useState<CampaignConflict[]>([]);
  const [cooldownDays, setCooldownDays] = useState(14);
  const [resolvingId, setResolvingId] = useState<string | null>(null);

  const fetchConflicts = async () => {
    setLoading(true);
    try {
      const data = await getCampaignConflicts();
      setConflicts(data.conflicts || []);
      setCooldownDays(data.cooldown_policy_days || 14);
    } catch {
      toast.error('Failed to run conflict scan');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConflicts();
  }, []);

  const handleResolve = async (conflict: CampaignConflict, action: string) => {
    setResolvingId(conflict.id);
    try {
      await resolveConflict(conflict.id, conflict.prospect_id || '', action);
      setConflicts((prev) => prev.filter((c) => c.id !== conflict.id));
      toast.success(`Conflict resolved: ${action}`);
    } catch {
      toast.error('Failed to resolve conflict');
    } finally {
      setResolvingId(null);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[85vh] flex flex-col overflow-hidden border border-border">
        {/* Header */}
        <div className="px-6 py-4 border-b border-border flex items-center justify-between bg-slate-50">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-amber-500/10 text-amber-600 flex items-center justify-center">
              <ShieldAlert size={16} />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">Campaign Isolation & Conflict Radar</h3>
              <p className="text-2xs text-slate-500">
                Detect duplicate outreach, multi-campaign collisions, and excessive contact frequency.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={fetchConflicts}
              disabled={loading}
              className="text-slate-400 hover:text-slate-600 p-1.5 rounded hover:bg-slate-200/50"
              title="Re-scan"
            >
              <RefreshCw size={14} className={cn(loading && 'animate-spin')} />
            </button>
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-slate-600 p-1.5 rounded hover:bg-slate-200/50"
            >
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-4 flex-1">
          {/* Policy Banner */}
          <div className="p-3 bg-blue-50/70 border border-blue-200 rounded-xl text-xs text-blue-900 flex items-center justify-between">
            <span className="font-medium">
              Enforced Policy: Minimum <strong>{cooldownDays}-day cooldown</strong> between cross-campaign touches.
            </span>
            <span className="text-2xs font-mono bg-white px-2 py-0.5 rounded border border-blue-200 text-blue-700">
              Active Protection
            </span>
          </div>

          {loading ? (
            <div className="p-8 text-center text-xs text-slate-400">Scanning cross-campaign database...</div>
          ) : conflicts.length === 0 ? (
            <div className="py-12 text-center space-y-2">
              <CheckCircle2 size={32} className="text-emerald-500 mx-auto" />
              <h4 className="text-sm font-bold text-slate-800">Zero Campaign Collisions Detected</h4>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                All active campaigns are strictly isolated. No prospects are enrolled across conflicting sequences.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {conflicts.map((conf) => (
                <div
                  key={conf.id}
                  className="p-4 rounded-xl border border-amber-200 bg-amber-50/30 space-y-3"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-1.5">
                        <span className="text-3xs font-bold uppercase px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 border border-amber-200">
                          {conf.severity} PRIORITY
                        </span>
                        <h4 className="text-xs font-bold text-slate-900">{conf.title}</h4>
                      </div>
                      <p className="text-xs text-slate-600 mt-1 leading-relaxed">{conf.description}</p>
                    </div>
                  </div>

                  {/* Campaigns Involved */}
                  <div className="flex items-center gap-2 text-2xs text-slate-500">
                    <span className="font-medium">Colliding Campaigns:</span>
                    {conf.involved_campaigns.map((camp, i) => (
                      <span key={i} className="bg-white border border-slate-200 px-2 py-0.5 rounded font-medium text-slate-700">
                        {camp}
                      </span>
                    ))}
                  </div>

                  {/* 1-Click Resolution Buttons */}
                  <div className="flex items-center justify-end gap-2 pt-2 border-t border-amber-100">
                    <button
                      onClick={() => handleResolve(conf, 'SUPPRESS_SECONDARY')}
                      disabled={resolvingId === conf.id}
                      className="px-2.5 py-1.5 rounded-lg text-2xs font-semibold bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 cursor-pointer"
                    >
                      Suppress Secondary
                    </button>
                    <button
                      onClick={() => handleResolve(conf, 'ENFORCE_COOLDOWN')}
                      disabled={resolvingId === conf.id}
                      className="btn-primary text-2xs px-3 py-1.5 cursor-pointer shadow-xs"
                    >
                      Enforce 14-Day Cooldown
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-border bg-slate-50 flex items-center justify-between text-2xs text-slate-500">
          <span>Campaign Isolation Engine powered by DronaHQ cross-campaign telemetry</span>
          <button onClick={onClose} className="btn-secondary text-xs px-3 py-1">
            Close Radar
          </button>
        </div>
      </div>
    </div>
  );
}
