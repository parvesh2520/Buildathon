import { apiClient } from './client';

export interface EmailStatusResponse {
  configured: boolean;
  provider: string;
  sender_account: string | null;
  smtp_server: string;
}

export interface SendTestEmailResponse {
  status: 'success' | 'mocked' | 'error';
  message: string;
  to?: string;
}

export async function fetchEmailStatus(): Promise<EmailStatusResponse> {
  return apiClient.get<EmailStatusResponse>('/api/email/status');
}

export async function sendTestEmail(toEmail: string): Promise<SendTestEmailResponse> {
  return apiClient.post<SendTestEmailResponse>('/api/email/send-test', {
    to_email: toEmail,
    subject: 'Autonomous SDR - Gmail Connection Test',
    body: 'Your Gmail connection is working properly! The Autonomous SDR platform is ready to send sales outreach emails.',
  });
}
