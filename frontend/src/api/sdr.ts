import { SDRRunRequest, SDRRunResponse, ExecutionRecord, Agent } from '@/types';
import { apiClient, IS_DEMO, fakeDelay } from './client';
import { demoAgents } from '@/data/demo/agents';

export async function runSDR(data: SDRRunRequest): Promise<ExecutionRecord> {
  if (IS_DEMO) {
    await fakeDelay(800);
    return {
      execution_id: crypto.randomUUID(),
      campaign_id: data.campaign_id,
      prospect_id: data.prospect_id,
      status: 'SENT',
      current_agent: 'COMPLETED',
      started_at: new Date().toISOString(),
    };
  }
  return apiClient.post<ExecutionRecord>('/api/sdr/run', data);
}

export async function getProspectExecution(prospectId: string): Promise<ExecutionRecord | null> {
  if (IS_DEMO) return null;
  try {
    return await apiClient.get<ExecutionRecord>(`/api/sdr/prospects/${prospectId}/execution`);
  } catch {
    return null;
  }
}

export async function getExecutions(): Promise<ExecutionRecord[]> {
  if (IS_DEMO) return [];
  try {
    return await apiClient.get<ExecutionRecord[]>('/api/sdr/executions');
  } catch {
    return [];
  }
}

export async function getAgents(): Promise<Agent[]> {
  if (IS_DEMO) return demoAgents;
  try {
    const agents = await apiClient.get<Agent[]>('/api/agents');
    return agents && agents.length > 0 ? agents : demoAgents;
  } catch {
    return demoAgents;
  }
}
