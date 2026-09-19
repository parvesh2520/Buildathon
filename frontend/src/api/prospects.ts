import { Prospect, ProspectCreate } from '@/types';
import { apiClient, IS_DEMO, fakeDelay } from './client';
import { demoProspects } from '@/data/demo/prospects';

let _demoProspects = [...demoProspects];

export async function getProspects(): Promise<Prospect[]> {
  if (IS_DEMO) {
    await fakeDelay();
    return [..._demoProspects];
  }
  return apiClient.get<Prospect[]>('/api/prospects');
}

export async function getProspect(id: string): Promise<Prospect> {
  if (IS_DEMO) {
    await fakeDelay(300);
    const p = _demoProspects.find((p) => p.id === id);
    if (!p) throw new Error('Prospect not found');
    return { ...p };
  }
  return apiClient.get<Prospect>(`/api/prospects/${id}`);
}

export async function createProspect(data: ProspectCreate): Promise<Prospect> {
  if (IS_DEMO) {
    await fakeDelay(600);
    const newProspect: Prospect = {
      ...data,
      id: crypto.randomUUID(),
      icpScore: undefined,
      status: 'REVIEW',
      lastActivity: 'just now',
    };
    _demoProspects = [newProspect, ..._demoProspects];
    return newProspect;
  }
  return apiClient.post<Prospect>('/api/prospects', data);
}

export async function deleteProspect(id: string): Promise<void> {
  if (IS_DEMO) {
    await fakeDelay(300);
    _demoProspects = _demoProspects.filter((p) => p.id !== id);
    return;
  }
  return apiClient.delete<void>(`/api/prospects/${id}`);
}

