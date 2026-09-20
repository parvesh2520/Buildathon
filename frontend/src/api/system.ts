import { apiClient } from './client';
import {
  OperationalControls,
  CampaignConflict,
  TokenEconomics,
} from '@/types';

export async function getOperationalControls(): Promise<OperationalControls> {
  return apiClient.get<OperationalControls>('/api/system/controls');
}

export async function toggleKillSwitch(
  enabled: boolean,
  reason?: string
): Promise<OperationalControls> {
  await apiClient.post('/api/system/kill-switch', { enabled, reason });
  return getOperationalControls();
}

export async function toggleChannelPause(
  channel: string,
  paused: boolean
): Promise<OperationalControls> {
  await apiClient.post('/api/system/channel-pause', { channel, paused });
  return getOperationalControls();
}

export async function toggleAgentPause(
  agent_id: string,
  paused: boolean
): Promise<OperationalControls> {
  await apiClient.post('/api/system/agent-pause', { agent_id, paused });
  return getOperationalControls();
}

export async function getCampaignConflicts(): Promise<{
  conflict_count: number;
  conflicts: CampaignConflict[];
  cooldown_policy_days: number;
}> {
  return apiClient.get('/api/system/conflicts');
}

export async function resolveConflict(
  conflict_id: string,
  prospect_id: string,
  action: string
): Promise<{ status: string; message: string }> {
  return apiClient.post('/api/system/conflicts/resolve', {
    conflict_id,
    prospect_id,
    action,
  });
}

export async function getTokenEconomics(): Promise<TokenEconomics> {
  return apiClient.get<TokenEconomics>('/api/system/token-economics');
}

export async function queryRAGKnowledge(query: string, top_k = 3): Promise<any> {
  return apiClient.post('/api/system/rag/query', { query, top_k });
}

export async function getRAGDocuments(): Promise<any> {
  return apiClient.get('/api/system/rag/knowledge');
}
