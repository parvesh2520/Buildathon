import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, FunnelChart, Funnel, LabelList,
} from 'recharts';
import { StatCard } from '@/components/shared/StatCard';

const campaignData = [
  { name: 'US SaaS CTOs', prospects: 842, messages: 614, replies: 73, meetings: 18 },
  { name: 'India BFSI CIOs', prospects: 312, messages: 198, replies: 28, meetings: 7 },
  { name: 'Voice AI Founders', prospects: 127, messages: 96, replies: 21, meetings: 6 },
];

const channelData = [
  { name: 'Email', value: 68 },
  { name: 'LinkedIn', value: 22 },
  { name: 'SMS', value: 7 },
  { name: 'Phone', value: 3 },
];

const replyTrend = [
  { date: 'Mon', rate: 9.2 },
  { date: 'Tue', rate: 11.4 },
  { date: 'Wed', rate: 10.8 },
  { date: 'Thu', rate: 13.2 },
  { date: 'Fri', rate: 12.7 },
  { date: 'Sat', rate: 8.1 },
  { date: 'Sun', rate: 7.4 },
];

const funnelData = [
  { name: 'Prospects', value: 1281 },
  { name: 'ICP Qualified', value: 908 },
  { name: 'Outreach Generated', value: 908 },
  { name: 'Messages Sent', value: 871 },
  { name: 'Replies', value: 122 },
  { name: 'Meetings', value: 31 },
];

const COLORS = ['#6366f1', '#8b5cf6', '#06b6d4', '#10b981'];
const PIE_COLORS = ['#6366f1', '#06b6d4', '#f59e0b', '#10b981'];

const chartTooltipStyle = {
  fontSize: '12px',
  border: '1px solid #e4e7ef',
  borderRadius: '10px',
  boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
};

export function Analytics() {
  return (
    <div className="p-6 max-w-[1200px] mx-auto">
      <div className="page-header">
        <h1 className="text-xl font-bold text-slate-900">Analytics</h1>
        <p className="text-sm text-slate-500 mt-1">Campaign performance and pipeline metrics.</p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-4 md:grid-cols-7 gap-3 mb-6">
        <StatCard label="Prospects" value="1,281" />
        <StatCard label="Qualified" value="908" />
        <StatCard label="Qual. Rate" value="70.9%" />
        <StatCard label="Msgs Sent" value="871" />
        <StatCard label="Reply Rate" value="14.0%" delta="+2.1% vs last week" positive />
        <StatCard label="Meetings" value="31" />
        <StatCard label="Meeting Rate" value="3.6%" />
      </div>

      <div className="grid grid-cols-2 gap-5 mb-5">
        {/* Campaign comparison */}
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">Prospects by Campaign</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={campaignData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f2f7" />
              <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#94a3b8' }} />
              <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} />
              <Tooltip contentStyle={chartTooltipStyle} />
              <Legend wrapperStyle={{ fontSize: '11px' }} />
              <Bar dataKey="prospects" fill="#6366f1" radius={[4, 4, 0, 0]} name="Prospects" />
              <Bar dataKey="messages" fill="#06b6d4" radius={[4, 4, 0, 0]} name="Messages" />
              <Bar dataKey="replies" fill="#10b981" radius={[4, 4, 0, 0]} name="Replies" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Reply rate trend */}
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">Reply Rate Trend (7 days)</h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={replyTrend} margin={{ top: 0, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f2f7" />
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#94a3b8' }} />
              <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} unit="%" />
              <Tooltip contentStyle={chartTooltipStyle} formatter={(v) => [`${v}%`, 'Reply Rate']} />
              <Line type="monotone" dataKey="rate" stroke="#6366f1" strokeWidth={2} dot={{ r: 3, fill: '#6366f1' }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid grid-cols-[1fr_280px] gap-5">
        {/* Funnel */}
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">ICP Qualification Funnel</h3>
          <div className="space-y-3">
            {funnelData.map((stage, i) => (
              <div key={stage.name}>
                <div className="flex items-center justify-between mb-1.5 text-xs">
                  <span className="text-slate-600">{stage.name}</span>
                  <span className="font-semibold tabular-nums text-slate-800">{stage.value.toLocaleString()}</span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-2">
                  <div
                    className="h-2 rounded-full"
                    style={{
                      width: `${(stage.value / funnelData[0].value) * 100}%`,
                      background: `hsl(${245 - i * 15}, 75%, ${55 + i * 4}%)`,
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Channel breakdown */}
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">Outreach by Channel</h3>
          <ResponsiveContainer width="100%" height={140}>
            <PieChart>
              <Pie data={channelData} cx="50%" cy="50%" innerRadius={40} outerRadius={65} paddingAngle={3} dataKey="value">
                {channelData.map((_, index) => (
                  <Cell key={index} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={chartTooltipStyle} formatter={(v) => [`${v}%`, 'Share']} />
            </PieChart>
          </ResponsiveContainer>
          <div className="space-y-1.5 mt-2">
            {channelData.map((d, i) => (
              <div key={d.name} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full" style={{ background: PIE_COLORS[i] }} />
                  <span className="text-slate-600">{d.name}</span>
                </div>
                <span className="font-semibold text-slate-700 tabular-nums">{d.value}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
