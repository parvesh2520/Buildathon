import { apiClient } from './client';

export interface VoiceCallTestRequest {
  phone: string;
  prospect_id?: string;
  campaign_id?: string;
}

export interface VoiceCallResponse {
  status: string;
  execution_id: string;
  twilio_call_sid: string;
  phone: string;
  error?: string | null;
}

export interface VoiceTranscriptResponse {
  identifier: string;
  execution_id?: string;
  call_sid?: string;
  status: string;
  turns_count: number;
  full_transcript: string;
  recording_url?: string | null;
  turns: Array<{
    turn: number;
    user_speech: string;
    agent_response: string;
    timestamp: string;
  }>;
}

export const voiceApi = {
  testCall: (data: VoiceCallTestRequest) =>
    apiClient.post<VoiceCallResponse>('/api/voice/test', data),

  getTranscript: (identifier: string) =>
    apiClient.get<VoiceTranscriptResponse>(`/api/voice/transcript/${identifier}`),
};
