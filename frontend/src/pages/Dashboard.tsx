import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Zap, Search, MessageSquare, Calendar, Users } from 'lucide-react';
import { Campaign, ActivityEvent } from '@/types';
import { getCampaigns } from '@/api/campaigns';
import { StatCard } from '@/components/shared/StatCard';
import { CampaignTable } from '@/components/campaign/CampaignTable';
import { CreateCampaignModal } from '@/components/campaign/CreateCampaignModal';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { CardSkeleton, TableSkeleton } from '@/components/shared/LoadingSkeleton';
import { demoActivity } from '@/data/demo/activity';

const agentFeed: ActivityEvent[] = demoActivity.slice(0, 6);

const agentIcons: Record<string, React.ReactNode> = {
  'ICP Fitment Agent': <Zap size={12} />,
  'Lead Research Agent': <Search size={12} />,
  'Outreach Strategy Agent': <MessageSquare size={12} />,
  'Personalisation Agent': <Zap size={12} />,
  'Conversation Agent': <MessageSquare size={12} />,
  'Follow-up Agent': <Calendar size={12} />,
};

export function Dashboard() {
  const navigate = useNavigate();
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);

  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening';

  useEffect(() => {
    getCampaigns().then(setCampaigns).finally(() => setLoading(false));
  }, []);

  const handleStatusChange = (id: string, status: Campaign['status']) => {
    setCampaigns((prev) => prev.map((c) => (c.id === id ? { ...c, status } : c)));
  };

  const totals = campaigns.reduce(
    (acc, c) => ({
      prospects: acc.prospects + (c.prospects ?? 0),
      messages: acc.messages + (c.messages ?? 0),
      replies: acc.replies + (c.replies ?? 0),
      meetings: acc.meetings + (c.meetings ?? 0),
    }),
    { prospects: 0, messages: 0, replies: 0, meetings: 0 }
  );

  const activeCampaigns = campaigns.filter((c) => c.status === 'LIVE').length;

  return (
    <div className="p-6 max-w-[1400px] mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between page-header">
        <div>
          <h1 className="text-xl font-bold text-slate-900">{greeting}</h1>
          <p className="text-sm text-slate-500 mt-1">Monitor your autonomous sales campaigns and agent activity.</p>
        </div>
        <button className="btn-primary" onClick={() => setShowCreate(true)}>
          <Plus size={15} />
          New Campaign
        </button>
      </div>

      {/* Stats */}
      {loading ? (
        <CardSkeleton count={5} />
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
          <StatCard label="Active Campaigns" value={activeCampaigns} />
          <StatCard label="Prospects" value={totals.prospects.toLocaleString()} />
          <StatCard label="Messages Sent" value={totals.messages.toLocaleString()} />
          <StatCard label="Replies" value={totals.replies} delta="+8 today" positive />
          <StatCard label="Meetings" value={totals.meetings} delta="+2 this week" positive />
        </div>
      )}

      <div className="grid grid-cols-[1fr_280px] gap-6">
        {/* Campaign Overview */}
        <div>
          <div className="section-header">
            <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wide">Campaign Overview</h2>
            <button className="text-xs text-brand hover:underline" onClick={() => navigate('/campaigns')}>
              View all
            </button>
          </div>
          {loading ? (
            <div className="card"><TableSkeleton rows={3} cols={7} /></div>
          ) : (
            <CampaignTable campaigns={campaigns} onStatusChange={handleStatusChange} />
          )}
        </div>

        {/* Agent Activity */}
        <div>
          <div className="section-header">
            <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wide">Agent Activity</h2>
            <button className="text-xs text-brand hover:underline" onClick={() => navigate('/activity')}>
              View all
            </button>
          </div>
          <div className="card divide-y divide-border-light">
            {agentFeed.map((event) => (
              <div key={event.id} className="px-4 py-3">
                <div className="flex items-start gap-2.5">
                  <div className="w-6 h-6 rounded-lg bg-brand/10 flex items-center justify-center text-brand flex-shrink-0 mt-0.5">
                    {agentIcons[event.agentName] ?? <Zap size={12} />}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-medium text-slate-700 truncate">{event.agentName}</p>
                    <p className="text-xs text-slate-400 leading-relaxed mt-0.5">{event.action}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-2xs text-slate-300">{event.timestamp}</span>
                      {event.prospect && (
                        <span className="text-2xs text-brand truncate">{event.prospect}</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {showCreate && (
        <CreateCampaignModal
          onClose={() => setShowCreate(false)}
          onCreated={(c) => setCampaigns((prev) => [c, ...prev])}
        />
      )}
    </div>
  );
}
