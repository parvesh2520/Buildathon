import React, { useEffect, useState, useCallback, useRef } from 'react';
import { getConversationThreads, sendManualReply, triggerGmailPoll, ConversationThread, InboxMessage } from '@/api/inbox';

// ─── helpers ─────────────────────────────────────────────────────────────────

function timeAgo(iso?: string): string {
  if (!iso) return '—';
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

function channelIcon(channel: string) {
  switch (channel?.toUpperCase()) {
    case 'EMAIL': return 'mail';
    case 'SMS': return 'sms';
    case 'PHONE': return 'call';
    case 'LINKEDIN': return 'person_pin';
    default: return 'chat';
  }
}

function initials(name: string) {
  return name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase();
}

function sentimentColor(s?: string) {
  if (!s) return '';
  if (s === 'POSITIVE') return 'text-tertiary';
  if (s === 'NEGATIVE') return 'text-error';
  return 'text-outline';
}

// ─── sub-components ──────────────────────────────────────────────────────────

function MessageBubble({ msg }: { msg: InboxMessage }) {
  const isOut = msg.direction === 'outbound';
  return (
    <div className={`flex gap-2 ${isOut ? 'flex-row-reverse' : 'flex-row'}`}>
      <div className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 font-label-sm text-label-sm font-bold shadow-sm ${isOut ? 'bg-inverse-surface text-primary-fixed-dim' : 'bg-surface-container-high text-on-surface'}`}>
        {isOut
          ? <span className="material-symbols-outlined text-[15px]">spark</span>
          : msg.sender.charAt(0)}
      </div>
      <div className={`max-w-[75%] flex flex-col gap-0.5 ${isOut ? 'items-end' : 'items-start'}`}>
        {msg.subject && (
          <span className="font-label-sm text-label-sm text-outline px-1">{msg.subject}</span>
        )}
        <div className={`px-4 py-2.5 rounded-2xl font-body-md text-body-md shadow-sm ${
          isOut
            ? 'bg-inverse-surface text-surface rounded-tr-sm'
            : 'bg-surface-container-lowest text-on-surface rounded-tl-sm border border-outline-variant/40'
        }`}>
          {msg.content || <span className="italic text-outline">(empty message)</span>}
        </div>
        <div className="flex items-center gap-1.5 px-1">
          <span className="font-label-sm text-label-sm text-outline">{timeAgo(msg.created_at)}</span>
          {msg.sentiment && (
            <span className={`font-label-sm text-label-sm ${sentimentColor(msg.sentiment)} flex items-center gap-0.5`}>
              <span className="material-symbols-outlined text-[13px]">
                {msg.sentiment === 'POSITIVE' ? 'thumb_up' : msg.sentiment === 'NEGATIVE' ? 'thumb_down' : 'remove'}
              </span>
            </span>
          )}
          {isOut && (
            <span className={`material-symbols-outlined text-[13px] ${msg.status === 'SENT' ? 'text-tertiary' : 'text-outline'}`}>
              {msg.status === 'SENT' ? 'done_all' : 'schedule'}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── main component ───────────────────────────────────────────────────────────

export function Inbox() {
  const [threads, setThreads] = useState<ConversationThread[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [filter, setFilter] = useState<'ALL' | 'EMAIL' | 'SMS'>('ALL');
  const [search, setSearch] = useState('');

  // Reply state
  const [replyText, setReplyText] = useState('');
  const [replySubject, setReplySubject] = useState('');
  const [sending, setSending] = useState(false);
  const [sendResult, setSendResult] = useState<'ok' | 'err' | null>(null);

  // Polling
  const [polling, setPolling] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const loadThreads = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getConversationThreads();
      setThreads(data);
      setError(null);
      // Auto-select first thread on initial load
      if (data.length > 0 && !selectedId) {
        setSelectedId(data[0].prospect_id);
      }
    } catch (e: any) {
      setError(e.message ?? 'Failed to load inbox');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadThreads();
  }, [loadThreads]);

  // Scroll to bottom when thread changes or new message arrives
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [selectedId, threads]);

  const selectedThread = threads.find(t => t.prospect_id === selectedId) ?? null;

  const filteredThreads = threads.filter(t => {
    const matchesFilter = filter === 'ALL' || t.prospect_channel === filter;
    const matchesSearch = !search || [t.prospect_name, t.prospect_company, t.prospect_email].some(
      v => v?.toLowerCase().includes(search.toLowerCase())
    );
    return matchesFilter && matchesSearch;
  });

  const handleSend = async () => {
    if (!selectedThread || !replyText.trim() || sending) return;
    setSending(true);
    setSendResult(null);
    try {
      const res = await sendManualReply({
        prospect_id: selectedThread.prospect_id,
        message: replyText.trim(),
        subject: replySubject.trim() || undefined,
        channel: selectedThread.prospect_channel,
      });

      // Optimistically append message to thread
      const newMsg: InboxMessage = {
        id: res.execution_id,
        direction: 'outbound',
        content: replyText.trim(),
        subject: replySubject.trim() || undefined,
        channel: selectedThread.prospect_channel,
        status: res.status,
        sender: 'You (Operator)',
        created_at: res.sent_at,
      };
      setThreads(prev => prev.map(t =>
        t.prospect_id === selectedThread.prospect_id
          ? { ...t, messages: [...t.messages, newMsg], last_message_at: res.sent_at }
          : t
      ));
      setReplyText('');
      setReplySubject('');
      setSendResult('ok');
      setTimeout(() => setSendResult(null), 3000);
    } catch {
      setSendResult('err');
      setTimeout(() => setSendResult(null), 4000);
    } finally {
      setSending(false);
    }
  };

  const handlePollGmail = async () => {
    setPolling(true);
    try {
      await triggerGmailPoll();
      await loadThreads();
    } finally {
      setPolling(false);
    }
  };

  const unreadCount = threads.filter(t =>
    (t.prospect_status === 'REPLIED' || t.prospect_status === 'REVIEW') &&
    t.messages.some(m => m.direction === 'inbound')
  ).length;

  return (
    <div className="w-full bg-surface min-h-screen flex flex-col" style={{ height: 'calc(100vh - 0px)' }}>
      {/* Top bar */}
      <div className="flex items-center justify-between px-space-lg py-space-md border-b border-outline-variant bg-surface-container-lowest flex-shrink-0">
        <div className="flex items-center gap-space-sm">
          <h1 className="font-headline-md text-headline-md text-on-surface">Inbox</h1>
          {unreadCount > 0 && (
            <span className="px-2.5 py-0.5 rounded-full bg-primary-container text-on-primary-container font-label-sm text-label-sm animate-pulse">
              {unreadCount} need action
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handlePollGmail}
            disabled={polling}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-surface-container text-on-surface font-label-md text-label-md hover:bg-surface-container-high transition-all disabled:opacity-60"
            title="Trigger Gmail poll for new replies"
          >
            <span className={`material-symbols-outlined text-[17px] text-outline ${polling ? 'animate-spin' : ''}`}>refresh</span>
            <span>{polling ? 'Polling…' : 'Poll Gmail'}</span>
          </button>
          <button onClick={loadThreads}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-surface-container-lowest border border-outline-variant text-on-surface font-label-md text-label-md hover:bg-surface-container transition-all shadow-sm">
            <span className="material-symbols-outlined text-[17px] text-outline">sync</span>
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex flex-col items-center justify-center flex-1 gap-4">
          <div className="w-10 h-10 rounded-full border-2 border-primary-container border-t-primary animate-spin"></div>
          <span className="font-body-md text-body-md text-on-surface-variant">Loading conversations…</span>
        </div>
      ) : error ? (
        <div className="flex flex-col items-center justify-center flex-1 gap-4">
          <span className="material-symbols-outlined text-[48px] text-error">error_outline</span>
          <p className="font-body-md text-body-md text-on-surface-variant">{error}</p>
          <button onClick={loadThreads}
            className="px-4 py-2 rounded-full bg-primary-container text-on-primary-container font-label-md text-label-md">
            Retry
          </button>
        </div>
      ) : (
        <div className="flex flex-1 overflow-hidden">

          {/* ── Left panel: thread list ── */}
          <div className="w-80 flex-shrink-0 flex flex-col border-r border-outline-variant bg-surface-container-low overflow-hidden">
            {/* Search + filter */}
            <div className="p-space-sm flex flex-col gap-2 border-b border-outline-variant">
              <div className="relative">
                <span className="material-symbols-outlined absolute left-3 top-2.5 text-[16px] text-outline">search</span>
                <input
                  className="w-full bg-surface-container-lowest border border-outline-variant rounded-xl pl-9 pr-3 py-2 font-body-sm text-body-sm text-on-surface placeholder:text-outline focus:outline-none focus:ring-2 focus:ring-primary/20"
                  placeholder="Search conversations…"
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                />
              </div>
              <div className="flex gap-1">
                {(['ALL', 'EMAIL', 'SMS'] as const).map(f => (
                  <button key={f} onClick={() => setFilter(f)}
                    className={`px-3 py-1 rounded-full font-label-sm text-label-sm transition-colors ${filter === f ? 'bg-on-surface text-surface' : 'bg-surface-container text-on-surface-variant hover:bg-surface-container-high'}`}>
                    {f}
                  </button>
                ))}
              </div>
            </div>

            {/* Thread list */}
            <div className="flex-1 overflow-y-auto">
              {filteredThreads.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full gap-3 px-4 text-center">
                  <span className="material-symbols-outlined text-[36px] text-outline">inbox</span>
                  <p className="font-body-sm text-body-sm text-on-surface-variant">No conversations yet</p>
                </div>
              ) : (
                filteredThreads.map(thread => {
                  const lastMsg = thread.messages[thread.messages.length - 1];
                  const hasInbound = thread.messages.some(m => m.direction === 'inbound');
                  const needsAction = thread.prospect_status === 'REPLIED' || thread.prospect_status === 'REVIEW';
                  const isActive = selectedId === thread.prospect_id;
                  return (
                    <button
                      key={thread.prospect_id}
                      onClick={() => setSelectedId(thread.prospect_id)}
                      className={`w-full text-left px-space-sm py-3 border-b border-outline-variant/40 transition-colors flex flex-col gap-1 ${isActive ? 'bg-primary-fixed/20' : 'hover:bg-surface-container'}`}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <div className="flex items-center gap-2 min-w-0">
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center font-label-md text-label-md font-bold flex-shrink-0 shadow-sm ${needsAction ? 'bg-primary-container text-on-primary-container' : 'bg-surface-container-high text-on-surface'}`}>
                            {initials(thread.prospect_name)}
                          </div>
                          <div className="min-w-0">
                            <div className="font-label-md text-label-md text-on-surface truncate flex items-center gap-1">
                              {thread.prospect_name}
                              {needsAction && <span className="w-1.5 h-1.5 rounded-full bg-primary flex-shrink-0"></span>}
                            </div>
                            <div className="font-body-sm text-body-sm text-outline truncate">{thread.prospect_company}</div>
                          </div>
                        </div>
                        <div className="flex flex-col items-end gap-1 flex-shrink-0">
                          <span className="font-label-sm text-label-sm text-outline">{timeAgo(thread.last_message_at)}</span>
                          <div className="flex items-center gap-1">
                            <span className="material-symbols-outlined text-[13px] text-outline">{channelIcon(thread.prospect_channel)}</span>
                            {hasInbound && <span className="w-1.5 h-1.5 rounded-full bg-tertiary"></span>}
                          </div>
                        </div>
                      </div>
                      {lastMsg && (
                        <p className="font-body-sm text-body-sm text-on-surface-variant truncate pl-10">
                          {lastMsg.direction === 'outbound' ? '→ ' : '← '}
                          {lastMsg.content.slice(0, 60)}{lastMsg.content.length > 60 ? '…' : ''}
                        </p>
                      )}
                    </button>
                  );
                })
              )}
            </div>
          </div>

          {/* ── Right panel: conversation ── */}
          {selectedThread ? (
            <div className="flex-1 flex flex-col overflow-hidden">
              {/* Thread header */}
              <div className="flex items-center justify-between px-space-lg py-space-md border-b border-outline-variant bg-surface-container-lowest flex-shrink-0">
                <div className="flex items-center gap-space-sm">
                  <div className="w-10 h-10 rounded-full bg-surface-container-high text-on-surface flex items-center justify-center font-label-md text-label-md font-bold shadow-sm">
                    {initials(selectedThread.prospect_name)}
                  </div>
                  <div>
                    <div className="font-label-lg text-label-lg text-on-surface">{selectedThread.prospect_name}</div>
                    <div className="font-body-sm text-body-sm text-outline flex items-center gap-1.5">
                      <span>{selectedThread.prospect_title}</span>
                      <span>·</span>
                      <span>{selectedThread.prospect_company}</span>
                      <span>·</span>
                      <span className="material-symbols-outlined text-[13px]">{channelIcon(selectedThread.prospect_channel)}</span>
                      <span>{selectedThread.prospect_channel}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {selectedThread.prospect_email && (
                    <span className="font-label-sm text-label-sm text-on-surface-variant bg-surface-container px-2.5 py-1 rounded-full flex items-center gap-1">
                      <span className="material-symbols-outlined text-[14px] text-outline">mail</span>
                      {selectedThread.prospect_email}
                    </span>
                  )}
                  {selectedThread.prospect_phone && (
                    <span className="font-label-sm text-label-sm text-on-surface-variant bg-surface-container px-2.5 py-1 rounded-full flex items-center gap-1">
                      <span className="material-symbols-outlined text-[14px] text-outline">phone</span>
                      {selectedThread.prospect_phone}
                    </span>
                  )}
                  <span className={`px-2.5 py-0.5 rounded-full font-label-sm text-label-sm ${selectedThread.prospect_status === 'REPLIED' ? 'bg-primary-fixed text-on-primary-fixed-variant' : 'bg-surface-container text-on-surface-variant'}`}>
                    {selectedThread.prospect_status}
                  </span>
                </div>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto px-space-lg py-space-md flex flex-col gap-space-md bg-surface">
                {selectedThread.messages.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-full gap-3">
                    <span className="material-symbols-outlined text-[40px] text-outline">chat_bubble_outline</span>
                    <p className="font-body-md text-body-md text-on-surface-variant">No messages yet in this thread.</p>
                  </div>
                ) : (
                  selectedThread.messages.map(msg => (
                    <MessageBubble key={msg.id} msg={msg} />
                  ))
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Reply composer */}
              <div className="border-t border-outline-variant bg-surface-container-lowest px-space-lg py-space-md flex-shrink-0">
                {selectedThread.prospect_channel === 'EMAIL' && (
                  <input
                    className="w-full bg-surface-container-low border border-outline-variant rounded-xl px-3 py-1.5 font-body-sm text-body-sm text-on-surface placeholder:text-outline focus:outline-none focus:ring-2 focus:ring-primary/20 mb-2"
                    placeholder="Subject (optional)"
                    value={replySubject}
                    onChange={e => setReplySubject(e.target.value)}
                  />
                )}
                <div className="flex items-end gap-2">
                  <textarea
                    rows={3}
                    className="flex-1 bg-surface-container-low border border-outline-variant rounded-xl px-3 py-2.5 font-body-md text-body-md text-on-surface placeholder:text-outline focus:outline-none focus:ring-2 focus:ring-primary/20 resize-none"
                    placeholder={`Reply via ${selectedThread.prospect_channel}…`}
                    value={replyText}
                    onChange={e => setReplyText(e.target.value)}
                    onKeyDown={e => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) handleSend(); }}
                  />
                  <div className="flex flex-col gap-2">
                    <button
                      onClick={handleSend}
                      disabled={!replyText.trim() || sending}
                      className="w-11 h-11 rounded-xl bg-primary-container text-on-primary-container hover:bg-inverse-primary flex items-center justify-center shadow-sm transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
                      title="Send (Ctrl+Enter)"
                    >
                      {sending
                        ? <span className="material-symbols-outlined text-[20px] animate-spin">progress_activity</span>
                        : <span className="material-symbols-outlined text-[20px]">send</span>
                      }
                    </button>
                  </div>
                </div>
                <div className="flex items-center justify-between mt-2">
                  <span className="font-label-sm text-label-sm text-outline flex items-center gap-1">
                    <span className="material-symbols-outlined text-[14px]">{channelIcon(selectedThread.prospect_channel)}</span>
                    Sending via {selectedThread.prospect_channel}
                    {selectedThread.prospect_email && selectedThread.prospect_channel === 'EMAIL' && ` → ${selectedThread.prospect_email}`}
                    {selectedThread.prospect_phone && selectedThread.prospect_channel === 'SMS' && ` → ${selectedThread.prospect_phone}`}
                  </span>
                  {sendResult === 'ok' && (
                    <span className="font-label-sm text-label-sm text-tertiary flex items-center gap-1">
                      <span className="material-symbols-outlined text-[14px]">check_circle</span>
                      Sent successfully
                    </span>
                  )}
                  {sendResult === 'err' && (
                    <span className="font-label-sm text-label-sm text-error flex items-center gap-1">
                      <span className="material-symbols-outlined text-[14px]">error</span>
                      Failed to send — check backend
                    </span>
                  )}
                  <span className="font-label-sm text-label-sm text-outline">Ctrl+Enter to send</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center gap-4 bg-surface">
              <div className="w-20 h-20 rounded-2xl bg-surface-container-lowest shadow-sm flex items-center justify-center">
                <span className="material-symbols-outlined text-[40px] text-outline">inbox</span>
              </div>
              <div className="text-center">
                <h3 className="font-headline-md text-headline-md text-on-surface">Select a conversation</h3>
                <p className="font-body-md text-body-md text-on-surface-variant mt-1 max-w-xs">
                  Pick a thread from the left panel to view messages and reply.
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
