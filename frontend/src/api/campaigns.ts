import { Campaign, CampaignCreate, CampaignStatus } from '@/types';
import { apiClient } from './client';

export async function getCampaigns(): Promise<Campaign[]> {
  return apiClient.get<Campaign[]>('/api/campaigns');
}

export async function getCampaign(id: string): Promise<Campaign> {
  return apiClient.get<Campaign>(`/api/campaigns/${id}`);
}

export async function createCampaign(data: CampaignCreate): Promise<Campaign> {
  return apiClient.post<Campaign>('/api/campaigns', data);
}

export async function deleteCampaign(id: string): Promise<void> {
  return apiClient.delete<void>(`/api/campaigns/${id}`);
}

export async function updateCampaignStatus(
  id: string,
  status: CampaignStatus
): Promise<Campaign> {
  return apiClient.patch<Campaign>(`/api/campaigns/${id}/status`, { status });
}

export async function duplicateCampaign(
  id: string,
  variant_name?: string
): Promise<Campaign> {
  return apiClient.post<Campaign>(`/api/campaigns/${id}/duplicate`, { variant_name });
}

export async function getCampaignPrompts(campaignId: string): Promise<any> {
  return apiClient.get(`/api/campaigns/${campaignId}/prompts`);
}

export async function saveCampaignPrompts(
  campaignId: string,
  system_prompt: string,
  agent_prompts: Record<string, string>,
  author = 'Campaign Manager'
): Promise<any> {
  return apiClient.post(`/api/campaigns/${campaignId}/prompts`, {
    system_prompt,
    agent_prompts,
    author,
  });
}

export async function rollbackCampaignPrompts(
  campaignId: string,
  target_version: string
): Promise<any> {
  return apiClient.post(`/api/campaigns/${campaignId}/prompts/rollback`, {
    target_version,
  });
}

export async function getCampaignReps(campaignId: string): Promise<any[]> {
  return apiClient.get(`/api/campaigns/${campaignId}/reps`);
}

export async function assignCampaignRep(
  campaignId: string,
  repData: any
): Promise<any> {
  return apiClient.post(`/api/campaigns/${campaignId}/reps`, repData);
}

export async function offboardCampaignRep(
  campaignId: string,
  rep_id: string,
  reassign_to_id?: string
): Promise<any> {
  return apiClient.post(`/api/campaigns/${campaignId}/reps/offboard`, {
    rep_id,
    reassign_to_id,
  });
}

export async function enrollLeadsInCampaign(
  campaignId: string,
  prospectIds?: string[]
): Promise<{ enrolled_count: number; prospects: any[] }> {
  return apiClient.post(`/api/campaigns/${campaignId}/enroll-leads`, {
    prospect_ids: prospectIds,
  });
}

