import { apiClient, IS_DEMO, fakeDelay } from './client';
import {
  OperationalControls,
  CampaignConflict,
  TokenEconomics,
} from '@/types';

let _mockControls: OperationalControls = {
  global_kill_switch: false,
  kill_switch_triggered_at: null,
  kill_switch_reason: null,
  paused_channels: [],
  paused_agents: [],
  campaign_summary: { total: 3, live: 2, paused: 1 },
  system_status: 'HEALTHY',
};

export async function getOperationalControls(): Promise<OperationalControls> {
  if (IS_DEMO) {
    await fakeDelay(150);
    return { ..._mockControls };
  }
  return apiClient.get<OperationalControls>('/api/system/controls');
}

export async function toggleKillSwitch(
  enabled: boolean,
  reason?: string
): Promise<OperationalControls> {
  if (IS_DEMO) {
    await fakeDelay(200);
    _mockControls.global_kill_switch = enabled;
    _mockControls.kill_switch_triggered_at = enabled ? new Date().toISOString() : null;
    _mockControls.kill_switch_reason = enabled ? (reason || 'Emergency Operator Action') : null;
    _mockControls.system_status = enabled ? 'EMERGENCY_STOPPED' : 'HEALTHY';
    return { ..._mockControls };
  }
  await apiClient.post('/api/system/kill-switch', { enabled, reason });
  return getOperationalControls();
}

export async function toggleChannelPause(
  channel: string,
  paused: boolean
): Promise<OperationalControls> {
  if (IS_DEMO) {
    await fakeDelay(150);
    const ch = channel.toUpperCase();
    if (paused && !_mockControls.paused_channels.includes(ch)) {
      _mockControls.paused_channels.push(ch);
    } else if (!paused) {
      _mockControls.paused_channels = _mockControls.paused_channels.filter((c) => c !== ch);
    }
    return { ..._mockControls };
  }
  await apiClient.post('/api/system/channel-pause', { channel, paused });
  return getOperationalControls();
}

export async function toggleAgentPause(
  agent_id: string,
  paused: boolean
): Promise<OperationalControls> {
  if (IS_DEMO) {
    await fakeDelay(150);
    if (paused && !_mockControls.paused_agents.includes(agent_id)) {
      _mockControls.paused_agents.push(agent_id);
    } else if (!paused) {
      _mockControls.paused_agents = _mockControls.paused_agents.filter((a) => a !== agent_id);
    }
    return { ..._mockControls };
  }
  await apiClient.post('/api/system/agent-pause', { agent_id, paused });
  return getOperationalControls();
}

export async function getCampaignConflicts(): Promise<{
  conflict_count: number;
  conflicts: CampaignConflict[];
  cooldown_policy_days: number;
}> {
  if (IS_DEMO) {
    await fakeDelay(200);
    return {
      conflict_count: 1,
      conflicts: [
        {
          id: 'conf_1',
          type: 'MULTI_CAMPAIGN_COLLISION',
          severity: 'HIGH',
          title: 'Duplicate Prospect in Multiple Campaigns (James Carter)',
          email: 'james.carter@cloudpeak.io',
          company: 'CloudPeak',
          prospect_id: 'p1',
          involved_campaigns: ['US SaaS CTOs', 'Enterprise Expansion'],
          description:
            "Lead 'James Carter' is enrolled across 2 campaigns. Risk of conflicting messaging and brand fatigue.",
          suggested_action: 'ENFORCE_COOLDOWN',
        },
      ],
      cooldown_policy_days: 14,
    };
  }
  return apiClient.get('/api/system/conflicts');
}

export async function resolveConflict(
  conflict_id: string,
  prospect_id: string,
  action: string
): Promise<{ status: string; message: string }> {
  if (IS_DEMO) {
    await fakeDelay(200);
    return { status: 'RESOLVED', message: `Conflict resolved via ${action}` };
  }
  return apiClient.post('/api/system/conflicts/resolve', {
    conflict_id,
    prospect_id,
    action,
  });
}

export async function getTokenEconomics(): Promise<TokenEconomics> {
  if (IS_DEMO) {
    await fakeDelay(200);
    return {
      summary: {
        total_tokens_consumed: 421850,
        prompt_tokens: 312400,
        completion_tokens: 109450,
        total_cost_usd: 4.82,
        cost_per_prospect_usd: 0.014,
        cost_per_qualified_lead_usd: 0.048,
        average_latency_ms: 780,
      },
      agent_breakdown: [
        { agent: 'Lead Research Agent', model: 'Gemini 1.5 Flash', tokens: 142000, cost: 1.42, avg_latency_ms: 820 },
        { agent: 'ICP Fitment Agent', model: 'Gemini 1.5 Flash', tokens: 68500, cost: 0.68, avg_latency_ms: 340 },
        { agent: 'Outreach Strategy Agent', model: 'Gemini 1.5 Pro', tokens: 85200, cost: 1.70, avg_latency_ms: 910 },
        { agent: 'Personalisation Agent', model: 'Gemini 1.5 Flash', tokens: 92150, cost: 0.92, avg_latency_ms: 610 },
        { agent: 'SDR Voice Script Agent', model: 'Gemini 1.5 Flash', tokens: 34000, cost: 0.10, avg_latency_ms: 450 },
      ],
      optimization_notes: [
        'Routing: Simpler classification tasks (ICP & Research) routed to Flash for 80% cost reduction.',
        'RAG Caching: Static company knowledge cached to prevent redundant embedding calls.',
      ],
    };
  }
  return apiClient.get<TokenEconomics>('/api/system/token-economics');
}

export async function queryRAGKnowledge(query: string, top_k = 3): Promise<any> {
  if (IS_DEMO) {
    await fakeDelay(300);
    return {
      query,
      retrieved_chunks: [
        {
          id: 'kb-2',
          title: 'US SaaS CTO Outreach Playbook',
          category: 'playbook',
          content: 'Angle: Developer productivity and automated pipeline velocity. Emphasize saving 40% engineering cycles without adding headcount.',
          similarity_score: 0.892,
        },
      ],
      top_similarity: 0.892,
    };
  }
  return apiClient.post('/api/system/rag/query', { query, top_k });
}

export async function getRAGDocuments(): Promise<any> {
  if (IS_DEMO) {
    await fakeDelay(200);
    return {
      documents: [
        { id: 'kb-1', category: 'product', title: 'Product Overview', content: 'Autonomous SDR platform...' },
        { id: 'kb-2', category: 'playbook', title: 'US SaaS CTO Playbook', content: 'Angle: Developer productivity...' },
        { id: 'kb-3', category: 'objection', title: 'Objection Handling', content: 'Position as a multiplier...' },
      ],
    };
  }
  return apiClient.get('/api/system/rag/knowledge');
}
