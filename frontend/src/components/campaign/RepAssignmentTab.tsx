import { useState, useEffect } from 'react';
import { UserCheck, UserX, Plus, Shield, Clock, Mail, Phone, ExternalLink } from 'lucide-react';
import { SalesRep } from '@/types';
import { getCampaignReps, assignCampaignRep, offboardCampaignRep } from '@/api/campaigns';
import toast from 'react-hot-toast';
import { cn } from '@/lib/utils';

interface RepAssignmentTabProps {
  campaignId: string;
}

export function RepAssignmentTab({ campaignId }: RepAssignmentTabProps) {
  const [reps, setReps] = useState<SalesRep[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [offboardTarget, setOffboardTarget] = useState<SalesRep | null>(null);

  // New rep form state
  const [newName, setNewName] = useState('');
  const [newEmail, setNewEmail] = useState('');
  const [newRole, setNewRole] = useState('Enterprise SDR');
  const [newQuota, setNewQuota] = useState(50);
  const [newHours, setNewHours] = useState('09:00 - 18:00 EST');

  useEffect(() => {
    loadReps();
  }, [campaignId]);

  const loadReps = async () => {
    setLoading(true);
    try {
      const data = await getCampaignReps(campaignId);
      setReps(data || []);
    } catch {
      toast.error('Failed to load sales reps');
    } finally {
      setLoading(false);
    }
  };

  const handleAddRep = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName || !newEmail) {
      toast.error('Please fill in name and email');
      return;
    }
    try {
      const created = await assignCampaignRep(campaignId, {
        name: newName,
        email: newEmail,
        role: newRole,
        daily_quota: Number(newQuota),
        working_hours: newHours,
        channels: ['EMAIL', 'LINKEDIN'],
      });
      setReps((prev) => [...prev, created]);
      setShowAddModal(false);
      setNewName('');
      setNewEmail('');
      toast.success(`Assigned ${newName} to campaign`);
    } catch {
      toast.error('Failed to assign rep');
    }
  };

  const handleOffboard = async () => {
    if (!offboardTarget) return;
    try {
      await offboardCampaignRep(campaignId, offboardTarget.id);
      setReps((prev) =>
        prev.map((r) => (r.id === offboardTarget.id ? { ...r, status: 'OFFBOARDED' } : r))
      );
      toast.success(`${offboardTarget.name} offboarded and leads safely reassigned`);
      setOffboardTarget(null);
    } catch {
      toast.error('Failed to offboard rep');
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-xs text-slate-400">Loading assigned representatives...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="card p-5 bg-white border-border flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <UserCheck size={16} className="text-brand" />
            <h3 className="text-sm font-bold text-slate-800">Representative Assignment & Work Quotas</h3>
          </div>
          <p className="text-xs text-slate-500">
            Control which human sales reps execute this campaign, sender identities, daily send quotas, and working hours.
          </p>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          className="btn-primary text-xs flex items-center gap-1.5 cursor-pointer shadow-xs"
        >
          <Plus size={13} />
          Assign Sales Rep
        </button>
      </div>

      {/* Reps Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {reps.map((rep) => {
          const isOffboarded = rep.status === 'OFFBOARDED';
          return (
            <div
              key={rep.id}
              className={cn(
                'card p-5 space-y-4 border transition-all',
                isOffboarded ? 'bg-slate-50 opacity-60 border-dashed border-slate-300' : 'bg-white border-border'
              )}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-full bg-brand/10 text-brand font-bold text-sm flex items-center justify-center">
                    {rep.name.charAt(0)}
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-slate-900">{rep.name}</h4>
                    <p className="text-xs text-slate-500">{rep.role}</p>
                    <p className="text-2xs text-slate-400 font-mono mt-0.5">{rep.email}</p>
                  </div>
                </div>

                <span
                  className={cn(
                    'text-3xs font-semibold px-2 py-0.5 rounded-full uppercase',
                    isOffboarded
                      ? 'bg-slate-200 text-slate-600'
                      : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                  )}
                >
                  {rep.status}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs pt-2 border-t border-border-light">
                <div className="flex items-center gap-2 text-slate-600">
                  <Shield size={13} className="text-slate-400 flex-shrink-0" />
                  <span>Daily Quota: <strong className="text-slate-800">{rep.daily_quota || 50}/day</strong></span>
                </div>
                <div className="flex items-center gap-2 text-slate-600">
                  <Clock size={13} className="text-slate-400 flex-shrink-0" />
                  <span>Hours: <strong className="text-slate-800">{rep.working_hours || '09:00 - 18:00'}</strong></span>
                </div>
              </div>

              {/* Channels Assigned */}
              <div className="flex items-center justify-between pt-2 border-t border-border-light text-xs">
                <div className="flex items-center gap-1.5">
                  <span className="text-2xs text-slate-400 font-medium">Channels:</span>
                  {(rep.channels || ['EMAIL', 'LINKEDIN']).map((ch) => (
                    <span key={ch} className="text-3xs font-mono bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded">
                      {ch}
                    </span>
                  ))}
                </div>

                {!isOffboarded && (
                  <button
                    onClick={() => setOffboardTarget(rep)}
                    className="text-2xs text-rose-600 hover:text-rose-800 font-semibold hover:underline flex items-center gap-1 cursor-pointer"
                  >
                    <UserX size={12} /> Offboard Rep
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Add Rep Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-xs">
          <div className="bg-white rounded-2xl p-6 shadow-2xl w-full max-w-md space-y-4">
            <h3 className="text-sm font-bold text-slate-900">Assign Sales Representative</h3>
            <form onSubmit={handleAddRep} className="space-y-3">
              <div>
                <label className="label">Full Name</label>
                <input
                  className="input"
                  placeholder="e.g. Maya Lin"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  required
                />
              </div>
              <div>
                <label className="label">Work Email</label>
                <input
                  className="input"
                  type="email"
                  placeholder="maya.lin@autonomous-sdr.ai"
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="label">Role</label>
                  <input
                    className="input"
                    value={newRole}
                    onChange={(e) => setNewRole(e.target.value)}
                  />
                </div>
                <div>
                  <label className="label">Daily Quota</label>
                  <input
                    className="input"
                    type="number"
                    value={newQuota}
                    onChange={(e) => setNewQuota(Number(e.target.value))}
                  />
                </div>
              </div>
              <div>
                <label className="label">Working Hours & Timezone</label>
                <input
                  className="input"
                  value={newHours}
                  onChange={(e) => setNewHours(e.target.value)}
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-border">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="btn-secondary text-xs"
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary text-xs">
                  Assign Representative
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Offboard Confirmation Modal */}
      {offboardTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-xs">
          <div className="bg-white rounded-2xl p-6 shadow-2xl w-full max-w-md space-y-4 border border-rose-100">
            <div className="flex items-center gap-2 text-rose-600 font-bold text-sm">
              <UserX size={18} />
              <h4>Offboard {offboardTarget.name}</h4>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              Offboarding this rep will immediately pause their personal sender identity and reassign all active prospect conversations to the campaign default rep pool.
            </p>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setOffboardTarget(null)}
                className="btn-secondary text-xs"
              >
                Cancel
              </button>
              <button
                onClick={handleOffboard}
                className="bg-rose-600 text-white px-3 py-1.5 rounded-lg text-xs font-semibold hover:bg-rose-700 transition-colors"
              >
                Confirm Offboarding & Reassign
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
