import { apiClient } from './client';

export interface InboxMessage {
  id: string;
  direction: 'inbound' | 'outbound';
  content: string;
  subject?: string;
  channel: string;
  status: string;
  sender: string;
  sentiment?: string;
  created_at: string;
}

export interface ConversationThread {
  prospect_id: string;
  prospect_name: string;
  prospect_email?: string;
  prospect_phone?: string;
  prospect_title?: string;
  prospect_company?: string;
  prospect_status?: string;
  prospect_channel: string;
  campaign_id?: string;
  messages: InboxMessage[];
  message_count: number;
  last_message_at?: string;
}

export interface ManualReplyRequest {
  prospect_id: string;
  message: string;
  subject?: string;
  channel?: string;
}

export interface ManualReplyResponse {
  status: string;
  channel: string;
  recipient: string;
  prospect_id: string;
  prospect_name: string;
  message_preview: string;
  execution_id: string;
  sent_at: string;
}

export async function getConversationThreads(): Promise<ConversationThread[]> {
  return apiClient.get<ConversationThread[]>('/api/inbound/threads');
}

export async function sendManualReply(data: ManualReplyRequest): Promise<ManualReplyResponse> {
  return apiClient.post<ManualReplyResponse>('/api/inbound/manual-reply', data);
}

export async function triggerGmailPoll(): Promise<{ processed: number; message: string }> {
  return apiClient.post<{ processed: number; message: string }>('/api/inbound/gmail/poll', {});
}
