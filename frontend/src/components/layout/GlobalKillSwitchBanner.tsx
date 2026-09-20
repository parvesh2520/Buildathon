import { useState, useEffect } from 'react';
import { AlertOctagon, ShieldAlert, CheckCircle2, Shield } from 'lucide-react';
import { getOperationalControls, toggleKillSwitch } from '@/api/system';
import { OperationalControls } from '@/types';
import toast from 'react-hot-toast';
import { cn } from '@/lib/utils';

export function GlobalKillSwitchBanner() {
  const [controls, setControls] = useState<OperationalControls | null>(null);
  const [toggling, setToggling] = useState(false);

  const fetchControls = () => {
    getOperationalControls()
      .then(setControls)
      .catch(() => {});
  };

  useEffect(() => {
    fetchControls();
    const interval = setInterval(fetchControls, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleToggle = async () => {
    if (!controls) return;
    const willEnable = !controls.global_kill_switch;
    if (willEnable) {
      if (!window.confirm('⚠️ EMERGENCY KILL SWITCH: Are you sure you want to halt ALL autonomous outreach across all campaigns and channels immediately?')) {
        return;
      }
    }
    setToggling(true);
    try {
      const updated = await toggleKillSwitch(willEnable, willEnable ? 'Manual operator intervention' : undefined);
      setControls(updated);
      if (willEnable) {
        toast.error('GLOBAL KILL SWITCH ENGAGED: All agent execution frozen', { duration: 5000 });
      } else {
        toast.success('Global operations resumed successfully');
      }
    } catch {
      toast.error('Failed to toggle kill switch');
    } finally {
      setToggling(false);
    }
  };

  const isStopped = controls?.global_kill_switch;

  return (
    <>
      {/* Red Alert Banner when Emergency Stopped */}
      {isStopped && (
        <div className="bg-rose-600 text-white px-4 py-2.5 flex items-center justify-between text-xs font-semibold shadow-md sticky top-0 z-50">
          <div className="flex items-center gap-2">
            <AlertOctagon size={16} className="animate-bounce" />
            <span>
              EMERGENCY STOP ACTIVE: All autonomous prospecting and dispatch have been globally halted.
            </span>
          </div>
          <button
            onClick={handleToggle}
            disabled={toggling}
            className="bg-white text-rose-700 px-3 py-1 rounded-md text-xs font-bold hover:bg-rose-50 transition-colors shadow-xs"
          >
            {toggling ? 'Resuming...' : 'Resume All Operations'}
          </button>
        </div>
      )}

      {/* Persistent Status Control Strip in App Layout */}
      <div className="bg-surface-secondary border-b border-border px-6 py-1.5 flex items-center justify-between text-2xs">
        <div className="flex items-center gap-3">
          <span className="font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-1">
            <Shield size={12} className="text-slate-400" /> Platform Control Plane
          </span>
          <div className="flex items-center gap-1.5">
            <span
              className={cn(
                'w-2 h-2 rounded-full',
                isStopped ? 'bg-rose-500 animate-pulse' : 'bg-emerald-500'
              )}
            />
            <span className="text-slate-600 font-medium">
              {isStopped ? 'System Halted (Kill Switch)' : 'Autonomy Active'}
            </span>
          </div>
          {controls?.paused_channels && controls.paused_channels.length > 0 && (
            <span className="bg-amber-100 text-amber-800 border border-amber-200 px-1.5 py-0.5 rounded font-mono">
              Channels Paused: {controls.paused_channels.join(', ')}
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleToggle}
            disabled={toggling}
            className={cn(
              'flex items-center gap-1 px-2 py-0.5 rounded text-2xs font-semibold border transition-all cursor-pointer',
              isStopped
                ? 'bg-emerald-600 text-white border-emerald-600 hover:bg-emerald-700'
                : 'bg-white text-rose-600 border-rose-200 hover:bg-rose-50 hover:border-rose-300'
            )}
            title={isStopped ? 'Resume autonomous SDR executions' : 'Immediately freeze all outbound outreach'}
          >
            {isStopped ? (
              <>
                <CheckCircle2 size={11} /> Resume Operations
              </>
            ) : (
              <>
                <ShieldAlert size={11} /> Global Kill Switch
              </>
            )}
          </button>
        </div>
      </div>
    </>
  );
}
