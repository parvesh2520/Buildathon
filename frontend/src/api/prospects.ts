import { Prospect, ProspectCreate } from '@/types';
import { apiClient } from './client';

export async function getProspects(): Promise<Prospect[]> {
  return apiClient.get<Prospect[]>('/api/prospects');
}

export async function getProspect(id: string): Promise<Prospect> {
  return apiClient.get<Prospect>(`/api/prospects/${id}`);
}

export async function createProspect(data: ProspectCreate): Promise<Prospect> {
  return apiClient.post<Prospect>('/api/prospects', data);
}

export async function deleteProspect(id: string): Promise<void> {
  return apiClient.delete<void>(`/api/prospects/${id}`);
}

export async function updateProspectStatus(
  id: string,
  status: string,
  channel?: string,
  icp_score?: number
): Promise<Prospect> {
  return apiClient.patch<Prospect>(`/api/prospects/${id}/status`, {
    status,
    channel,
    icp_score,
  });
}
