import { Campaign, CampaignCreate, CampaignStatus } from '@/types';
import { apiClient, IS_DEMO, fakeDelay } from './client';
import { demoCampaigns } from '@/data/demo/campaigns';

// In-memory store for demo campaigns (allows create/status toggle to persist in session)
let _demoCampaigns = [...demoCampaigns];

export async function getCampaigns(): Promise<Campaign[]> {
  if (IS_DEMO) {
    await fakeDelay();
    return [..._demoCampaigns];
  }
  return apiClient.get<Campaign[]>('/api/campaigns');
}

export async function getCampaign(id: string): Promise<Campaign> {
  if (IS_DEMO) {
    await fakeDelay(300);
    const c = _demoCampaigns.find((c) => c.id === id);
    if (!c) throw new Error('Campaign not found');
    return { ...c };
  }
  return apiClient.get<Campaign>(`/api/campaigns/${id}`);
}

export async function createCampaign(data: CampaignCreate): Promise<Campaign> {
  if (IS_DEMO) {
    await fakeDelay(600);
    const newCampaign: Campaign = {
      ...data,
      id: crypto.randomUUID(),
      prospects: 0,
      messages: 0,
      replies: 0,
      meetings: 0,
      replyRate: 0,
      created: new Date().toISOString().split('T')[0],
      lastActivity: 'just now',
    };
    _demoCampaigns = [newCampaign, ..._demoCampaigns];
    return newCampaign;
  }
  return apiClient.post<Campaign>('/api/campaigns', data);
}

export async function updateCampaignStatus(
  id: string,
  status: CampaignStatus
): Promise<Campaign> {
  if (IS_DEMO) {
    await fakeDelay(300);
    _demoCampaigns = _demoCampaigns.map((c) =>
      c.id === id ? { ...c, status } : c
    );
    const updated = _demoCampaigns.find((c) => c.id === id);
    if (!updated) throw new Error('Campaign not found');
    return { ...updated };
  }
  return apiClient.patch<Campaign>(`/api/campaigns/${id}/status`, { status });
}
