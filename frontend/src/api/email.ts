import { apiClient, IS_DEMO, fakeDelay } from './client';

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
  if (IS_DEMO) {
    await fakeDelay(200);
    return {
      configured: false,
      provider: 'Gmail SMTP (Demo)',
      sender_account: null,
      smtp_server: 'smtp.gmail.com',
    };
  }
  return apiClient.get<EmailStatusResponse>('/api/email/status');
}

export async function sendTestEmail(toEmail: string): Promise<SendTestEmailResponse> {
  if (IS_DEMO) {
    await fakeDelay(500);
    return {
      status: 'mocked',
      message: `Demo Mode: Test email sent to ${toEmail} (Simulated). Connect backend to send real emails!`,
      to: toEmail,
    };
  }
  return apiClient.post<SendTestEmailResponse>('/api/email/send-test', {
    to_email: toEmail,
    subject: 'Autonomous SDR - Gmail Connection Test',
    body: 'Your Gmail connection is working properly! The Autonomous SDR platform is ready to send sales outreach emails.',
  });
}
