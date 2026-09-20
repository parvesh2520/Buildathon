import { apiClient } from './client';
import {
  Prospect,
  DiscoveredProspectsResponse,
  RunDiscoveryResponse,
  StartPipelineResponse,
} from '@/types';

export async function getDiscoveredProspects(
  campaignId: string,
  status?: string
): Promise<Prospect[]> {
  const query = status ? `?status=${encodeURIComponent(status)}` : '';
  return apiClient.get<Prospect[]>(`/api/campaigns/${campaignId}/discovered-prospects${query}`);
}

export async function ingestDiscoveredProspects(
  campaignId: string,
  prospects: any[],
  source?: string
): Promise<DiscoveredProspectsResponse> {
  return apiClient.post<DiscoveredProspectsResponse>(
    `/api/campaigns/${campaignId}/discovered-prospects`,
    {
      discovery_source: source || 'Prospect Discovery Agent',
      prospects,
    }
  );
}

export async function runDiscoveryAgent(
  campaignId: string,
  count: number,
  criteria?: string,
  domain?: string
): Promise<RunDiscoveryResponse> {
  return apiClient.post<RunDiscoveryResponse>(
    `/api/campaigns/${campaignId}/run-discovery`,
    {
      count,
      criteria,
      domain,
    }
  );
}

export async function updateDiscoveredProspect(
  prospectId: string,
  status: string,
  notes?: string
): Promise<Prospect> {
  return apiClient.patch<Prospect>(`/api/discovered-prospects/${prospectId}`, {
    status,
    notes,
  });
}

export async function startSdrPipeline(
  campaignId: string,
  prospectIds: string[]
): Promise<StartPipelineResponse> {
  return apiClient.post<StartPipelineResponse>(
    `/api/campaigns/${campaignId}/start-pipeline`,
    {
      prospect_ids: prospectIds,
    }
  );
}

const DISCOVERY_STORAGE_KEY = 'agent0_active_discoveries';

export function setCampaignDiscovering(campaignId: string, isDiscovering: boolean, count?: number): void {
  try {
    const raw = localStorage.getItem(DISCOVERY_STORAGE_KEY);
    const map = raw ? JSON.parse(raw) : {};
    if (isDiscovering) {
      map[campaignId] = { count: count || 5, timestamp: Date.now() };
    } else {
      delete map[campaignId];
    }
    localStorage.setItem(DISCOVERY_STORAGE_KEY, JSON.stringify(map));
  } catch (e) {
    console.error('Error updating discovery storage:', e);
  }
}

export function isCampaignDiscovering(campaignId: string): { discovering: boolean; count?: number } {
  try {
    const raw = localStorage.getItem(DISCOVERY_STORAGE_KEY);
    if (!raw) return { discovering: false };
    const map = JSON.parse(raw);
    const info = map[campaignId];
    if (!info) return { discovering: false };
    // Auto-expire after 3 minutes in case a task halted
    if (Date.now() - info.timestamp > 180000) {
      delete map[campaignId];
      localStorage.setItem(DISCOVERY_STORAGE_KEY, JSON.stringify(map));
      return { discovering: false };
    }
    return { discovering: true, count: info.count };
  } catch {
    return { discovering: false };
  }
}

export function getActiveDiscoveries(): Record<string, { count: number; timestamp: number }> {
  try {
    const raw = localStorage.getItem(DISCOVERY_STORAGE_KEY);
    if (!raw) return {};
    const map = JSON.parse(raw);
    const now = Date.now();
    let changed = false;
    for (const cid in map) {
      if (now - map[cid].timestamp > 180000) {
        delete map[cid];
        changed = true;
      }
    }
    if (changed) localStorage.setItem(DISCOVERY_STORAGE_KEY, JSON.stringify(map));
    return map;
  } catch {
    return {};
  }
}

