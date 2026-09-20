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

export async function duplicateCampaign(
  id: string,
  variant_name?: string
): Promise<Campaign> {
  if (IS_DEMO) {
    await fakeDelay(400);
    const source = _demoCampaigns.find((c) => c.id === id);
    if (!source) throw new Error('Campaign not found');
    const newCamp: Campaign = {
      ...source,
      id: `${source.id}_var_${Math.random().toString(36).slice(2, 6)}`,
      name: variant_name || `${source.name} (Variant B)`,
      status: 'PAUSED',
      prospects: 0,
      messages: 0,
      replies: 0,
      meetings: 0,
      created: new Date().toISOString().split('T')[0],
      lastActivity: 'just now',
    };
    _demoCampaigns = [newCamp, ..._demoCampaigns];
    return newCamp;
  }
  return apiClient.post<Campaign>(`/api/campaigns/${id}/duplicate`, { variant_name });
}

export async function getCampaignPrompts(campaignId: string): Promise<any> {
  if (IS_DEMO) {
    await fakeDelay(200);
    return {
      campaign_id: campaignId,
      current: {
        system_prompt: 'You are an autonomous AI SDR orchestrating enterprise outreach. Observe strict professional tonality.',
        agent_prompts: {
          icp_fitment: 'Score prospect 0-100 against target ICP criteria.',
          lead_research: 'Detect developer infrastructure, tech stack, and pain points.',
          outreach_strategy: 'Select optimal channel (Email, LinkedIn, SMS, Voice).',
          personalisation: 'Draft compelling contextual outreach referencing prospect signals.',
          conversation: 'Analyze prospect reply and select next objection handling action.',
          follow_up: 'Decide follow-up cadence (3-day or 7-day spacing).',
          voice_sdr: 'Generate voice phone call script with gatekeeper handling.',
        },
        version: 'v1.0',
        author: 'System Admin',
        updated_at: '2026-09-18T12:00:00Z',
      },
      history: [
        {
          version: 'v1.0',
          author: 'System Admin',
          updated_at: '2026-09-18T12:00:00Z',
        },
      ],
      version_count: 1,
    };
  }
  return apiClient.get(`/api/campaigns/${campaignId}/prompts`);
}

export async function saveCampaignPrompts(
  campaignId: string,
  system_prompt: string,
  agent_prompts: Record<string, string>,
  author = 'Campaign Manager'
): Promise<any> {
  if (IS_DEMO) {
    await fakeDelay(300);
    return {
      campaign_id: campaignId,
      current: {
        system_prompt,
        agent_prompts,
        version: 'v2.0',
        author,
        updated_at: new Date().toISOString(),
      },
    };
  }
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
  if (IS_DEMO) {
    await fakeDelay(300);
    return { status: 'ROLLED_BACK', target_version };
  }
  return apiClient.post(`/api/campaigns/${campaignId}/prompts/rollback`, {
    target_version,
  });
}

export async function getCampaignReps(campaignId: string): Promise<any[]> {
  if (IS_DEMO) {
    await fakeDelay(200);
    return [
      {
        id: 'rep-1',
        name: 'Sarah Jenkins',
        email: 'sarah.jenkins@autonomous-sdr.ai',
        role: 'Senior Enterprise SDR',
        channels: ['EMAIL', 'LINKEDIN'],
        daily_quota: 50,
        working_hours: '09:00 - 18:00 EST',
        status: 'ACTIVE',
      },
      {
        id: 'rep-2',
        name: 'Alex Rivera',
        email: 'alex.rivera@autonomous-sdr.ai',
        role: 'Outbound Specialist',
        channels: ['PHONE', 'SMS'],
        daily_quota: 40,
        working_hours: '08:00 - 17:00 PST',
        status: 'ACTIVE',
      },
    ];
  }
  return apiClient.get(`/api/campaigns/${campaignId}/reps`);
}

export async function assignCampaignRep(
  campaignId: string,
  repData: any
): Promise<any> {
  if (IS_DEMO) {
    await fakeDelay(250);
    return { ...repData, id: `rep-${Math.random().toString(36).slice(2, 6)}`, status: 'ACTIVE' };
  }
  return apiClient.post(`/api/campaigns/${campaignId}/reps`, repData);
}

export async function offboardCampaignRep(
  campaignId: string,
  rep_id: string,
  reassign_to_id?: string
): Promise<any> {
  if (IS_DEMO) {
    await fakeDelay(300);
    return { message: 'Rep successfully offboarded and prospects reassigned.' };
  }
  return apiClient.post(`/api/campaigns/${campaignId}/reps/offboard`, {
    rep_id,
    reassign_to_id,
  });
}

