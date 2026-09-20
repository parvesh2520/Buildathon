import { SDRRunRequest, ExecutionRecord, Agent, ActivityEvent, OutreachMessage } from '@/types';
import { apiClient } from './client';
import { formatAgentText } from '@/lib/utils';

export async function runSDR(data: SDRRunRequest): Promise<ExecutionRecord> {
  return apiClient.post<ExecutionRecord>('/api/sdr/run', data);
}

export async function getProspectExecution(prospectId: string): Promise<ExecutionRecord | null> {
  try {
    return await apiClient.get<ExecutionRecord>(`/api/sdr/prospects/${prospectId}/execution`);
  } catch {
    return null;
  }
}

export async function getExecutions(): Promise<ExecutionRecord[]> {
  return apiClient.get<ExecutionRecord[]>('/api/sdr/executions');
}

export async function getAgents(): Promise<Agent[]> {
  return apiClient.get<Agent[]>('/api/agents');
}

const categoryForAgent = (agent: string): ActivityEvent['category'] => {
  const normalized = agent.toLowerCase();
  if (normalized.includes('research')) return 'research';
  if (normalized.includes('icp') || normalized.includes('fit')) return 'qualification';
  if (normalized.includes('strategy')) return 'strategy';
  if (normalized.includes('personal')) return 'personalisation';
  if (normalized.includes('conversation')) return 'conversation';
  if (normalized.includes('follow')) return 'follow-up';
  if (normalized.includes('voice')) return 'voice';
  return 'campaign';
};

const formatTimestamp = (iso?: string) => {
  if (!iso) return 'No timestamp';
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? iso : date.toLocaleString();
};

export async function getActivityEvents(campaignId?: string): Promise<ActivityEvent[]> {
  const executions = campaignId
    ? await apiClient.get<ExecutionRecord[]>(`/api/campaigns/${campaignId}/executions`)
    : await getExecutions();

  return executions.map((execution) => ({
    id: execution.execution_id,
    agentName: execution.current_agent || 'SDR Pipeline',
    action: execution.error
      ? execution.error
      : `Processed ${execution.actual_channel || execution.recommended_channel || execution.channel || 'outreach'}`,
    prospect: execution.prospect_id,
    campaign: execution.campaign_id,
    status: execution.status === 'FAILED' || execution.status === 'BLOCKED' ? 'FAILED' : 'COMPLETED',
    category: categoryForAgent(execution.current_agent || ''),
    timestamp: formatTimestamp(execution.completed_at || execution.started_at),
  }));
}

export async function getCampaignOutreach(campaignId: string): Promise<OutreachMessage[]> {
  const executions = await apiClient.get<ExecutionRecord[]>(`/api/campaigns/${campaignId}/executions`);

  return executions
    .filter((execution) => execution.personalisation_result?.content || execution.email_details?.preview || execution.channel_result)
    .map((execution) => ({
      id: execution.execution_id,
      prospectId: execution.prospect_id,
      prospectName: execution.prospect_id,
      channel: (execution.actual_channel || execution.recommended_channel || execution.channel || execution.channel_result?.channel || 'EMAIL') as OutreachMessage['channel'],
      subject: formatAgentText(execution.personalisation_result?.subject_line || execution.email_details?.subject),
      body: formatAgentText(execution.personalisation_result?.content) || execution.email_details?.preview || execution.channel_result?.error || '',
      generatedBy: execution.current_agent || 'SDR Pipeline',
      timestamp: formatTimestamp(execution.completed_at || execution.started_at),
      status: execution.status === 'SENT' || execution.status === 'COMPLETED' ? 'SENT' : 'PENDING',
      requiresApproval: execution.status === 'PENDING_MANUAL',
    }));
}
