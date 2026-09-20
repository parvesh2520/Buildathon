import { useState } from 'react';
import { CheckCircle, AlertCircle, XCircle, Save, Mail, Send, ExternalLink } from 'lucide-react';
import toast from 'react-hot-toast';
import { sendTestEmail } from '@/api/email';
import { KnowledgeBaseModal } from '@/components/knowledge/KnowledgeBaseModal';

type SystemStatusKey = 'fastapi' | 'dronahq' | 'webhooks' | 'email';

const initialStatus: Record<SystemStatusKey, 'ok' | 'warn' | 'error'> = {
  fastapi: 'ok',
  dronahq: 'warn',
  webhooks: 'ok',
  email: 'warn',
};

const statusConfig = {
  ok: { icon: <CheckCircle size={14} />, color: 'text-emerald-600', label: 'Operational', dot: 'bg-emerald-400' },
  warn: { icon: <AlertCircle size={14} />, color: 'text-amber-600', label: 'Not configured', dot: 'bg-amber-400' },
  error: { icon: <XCircle size={14} />, color: 'text-red-500', label: 'Error', dot: 'bg-red-400' },
};

const systemItems: { key: SystemStatusKey; label: string }[] = [
  { key: 'fastapi', label: 'FastAPI Backend' },
  { key: 'dronahq', label: 'DronaHQ Automation' },
  { key: 'webhooks', label: 'Agent Webhooks' },
  { key: 'email', label: 'Gmail Provider' },
];

export function Settings() {
  const [apiUrl, setApiUrl] = useState(import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000');
  const [webhookUrl, setWebhookUrl] = useState('');
  const [systemStatus] = useState(initialStatus);
  const [testEmailAddr, setTestEmailAddr] = useState('');
  const [sendingTest, setSendingTest] = useState(false);
  const [showKbModal, setShowKbModal] = useState(false);
  const isDemoMode = import.meta.env.VITE_DEMO_MODE === 'true';

  const save = (label: string) => {
    toast.success(`${label} saved`);
  };

  const handleTestEmail = async () => {
    if (!testEmailAddr || !testEmailAddr.includes('@')) {
      toast.error('Please enter a valid recipient email address');
      return;
    }
    setSendingTest(true);
    try {
      const res = await sendTestEmail(testEmailAddr);
      if (res.status === 'success') {
        toast.success(`Success! Email delivered to ${testEmailAddr}`);
      } else if (res.status === 'mocked') {
        toast.success(res.message);
      } else {
        toast.error(res.message);
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to send test email';
      toast.error(message);
    } finally {
      setSendingTest(false);
    }
  };

  return (
    <div className="p-6 max-w-[800px] mx-auto">
      <div className="page-header">
        <h1 className="text-xl font-bold text-slate-900">Settings</h1>
        <p className="text-sm text-slate-500 mt-1">Configure backend connections, integrations, and Gmail SMTP.</p>
      </div>

      {isDemoMode && (
        <div className="mb-6 px-4 py-3 rounded-xl border border-amber-200 bg-amber-50 text-xs text-amber-700 font-medium">
          ⚡ Demo mode is active. Set <code className="font-mono bg-amber-100 px-1 rounded">VITE_DEMO_MODE=false</code> in your <code className="font-mono bg-amber-100 px-1 rounded">.env</code> to connect to the real FastAPI backend.
        </div>
      )}

      <div className="space-y-5">
        {/* Backend Connection */}
        <div className="card p-5">
          <h2 className="text-sm font-semibold text-slate-800 mb-4">Backend Connection</h2>
          <div>
            <label className="label">API Base URL</label>
            <div className="flex gap-2">
              <input className="input flex-1" value={apiUrl} onChange={(e) => setApiUrl(e.target.value)} placeholder="http://localhost:8000" />
              <button className="btn-primary" onClick={() => save('API URL')}>
                <Save size={13} /> Save
              </button>
            </div>
            <p className="text-xs text-slate-400 mt-1.5">Set via <code className="font-mono bg-surface-tertiary px-1 rounded">VITE_API_BASE_URL</code> environment variable.</p>
          </div>
        </div>

        {/* Gmail Provider & Email Settings */}
        <div className="card p-5">
          <div className="flex items-center gap-2 mb-3">
            <Mail className="text-brand" size={18} />
            <h2 className="text-sm font-semibold text-slate-800">Gmail Outreach Integration</h2>
          </div>
          <p className="text-xs text-slate-500 mb-4">
            Connect your Gmail account to allow Autonomous SDR agents to send personalized outreach emails.
          </p>

          <div className="p-3.5 rounded-xl border border-border bg-surface-secondary text-xs text-slate-600 mb-4 space-y-2">
            <div className="font-semibold text-slate-800 flex items-center gap-1.5">
              💡 How to set up Gmail App Password (2 minutes):
            </div>
            <ol className="list-decimal list-inside space-y-1 text-slate-600 pl-1">
              <li>Enable 2-Step Verification on your Google Account.</li>
              <li>Go to <a href="https://myaccount.google.com/apppasswords" target="_blank" rel="noreferrer" className="text-brand underline inline-flex items-center gap-0.5 font-medium">Google App Passwords <ExternalLink size={10} /></a>.</li>
              <li>Generate a new 16-character App Password for "Autonomous SDR".</li>
              <li>Add <code className="font-mono bg-slate-200 px-1 rounded">SMTP_USERNAME</code> and <code className="font-mono bg-slate-200 px-1 rounded">SMTP_PASSWORD</code> into your backend <code className="font-mono bg-slate-200 px-1 rounded">.env</code>.</li>
            </ol>
          </div>

          <div>
            <label className="label">Send Test Email</label>
            <div className="flex gap-2">
              <input
                className="input flex-1"
                placeholder="recipient@example.com"
                value={testEmailAddr}
                onChange={(e) => setTestEmailAddr(e.target.value)}
              />
              <button className="btn-primary" onClick={handleTestEmail} disabled={sendingTest}>
                <Send size={13} /> {sendingTest ? 'Sending...' : 'Test Send'}
              </button>
            </div>
            <p className="text-xs text-slate-400 mt-1.5">
              Tests the FastAPI email service via <code className="font-mono bg-surface-tertiary px-1 rounded">POST /api/email/send-test</code>.
            </p>
          </div>
        </div>

        {/* DronaHQ */}
        <div className="card p-5">
          <h2 className="text-sm font-semibold text-slate-800 mb-4">DronaHQ Automation</h2>
          <div>
            <label className="label">Automation Webhook URL</label>
            <div className="flex gap-2">
              <input className="input flex-1" value={webhookUrl} onChange={(e) => setWebhookUrl(e.target.value)} placeholder="https://automations.dronahq.com/webhooks/..." />
              <button className="btn-primary" onClick={() => save('Webhook URL')}>
                <Save size={13} /> Save
              </button>
            </div>
            <p className="text-xs text-slate-400 mt-1.5">The FastAPI backend will call this URL when a new SDR run is triggered.</p>
          </div>
        </div>

        {/* Agent Configuration */}
        <div className="card p-5">
          <h2 className="text-sm font-semibold text-slate-800 mb-4">Agent Configuration</h2>
          <div className="space-y-2">
            {['ICP Fitment Agent', 'Lead Research Agent', 'Outreach Strategy Agent', 'Personalisation Agent', 'Conversation Agent', 'Voice SDR Agent', 'Follow-up Agent'].map((name) => (
              <div key={name} className="flex items-center justify-between px-3 py-2 rounded-lg bg-surface-secondary text-xs">
                <span className="text-slate-700 font-medium">{name}</span>
                <span className="text-emerald-600 font-medium flex items-center gap-1">
                  <CheckCircle size={11} /> Configured via DronaHQ
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Knowledge Base & Vector RAG */}
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-slate-800">Knowledge Base & Vector RAG Grounding</h2>
            <button
              onClick={() => setShowKbModal(true)}
              className="text-xs text-brand hover:underline font-medium cursor-pointer"
            >
              Open Vector RAG Explorer →
            </button>
          </div>
          <div className="grid grid-cols-3 gap-2">
            {['Product Information', 'Case Studies', 'Sales Playbook', 'ICP Definition', 'Objection Handling', 'Voice Scripts'].map((item) => (
              <div
                key={item}
                onClick={() => setShowKbModal(true)}
                className="flex items-center gap-2 p-3 rounded-lg border border-border text-xs text-slate-600 hover:border-brand hover:text-brand cursor-pointer transition-colors"
              >
                📄 {item}
              </div>
            ))}
          </div>
        </div>

        {showKbModal && <KnowledgeBaseModal onClose={() => setShowKbModal(false)} />}

        {/* System Status */}
        <div className="card p-5">
          <h2 className="text-sm font-semibold text-slate-800 mb-4">System Status</h2>
          <div className="space-y-2">
            {systemItems.map(({ key, label }) => {
              const s = systemStatus[key];
              const cfg = statusConfig[s];
              return (
                <div key={key} className="flex items-center justify-between px-3 py-2.5 rounded-lg bg-surface-secondary">
                  <div className="flex items-center gap-2.5">
                    <span className={`w-2 h-2 rounded-full ${cfg.dot}`} />
                    <span className="text-sm text-slate-700">{label}</span>
                  </div>
                  <div className={`flex items-center gap-1.5 text-xs font-medium ${cfg.color}`}>
                    {cfg.icon}
                    {cfg.label}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
