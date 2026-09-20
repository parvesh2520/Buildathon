// ─── Campaign ────────────────────────────────────────────────────────────────

export type CampaignStatus = 'LIVE' | 'PAUSED' | 'COMPLETED';

export interface Campaign {
  id: string;
  name: string;
  description?: string;
  icp: string;
  status: CampaignStatus;
  prospects?: number;
  messages?: number;
  replies?: number;
  meetings?: number;
  replyRate?: number;
  created?: string;
  lastActivity?: string;
  goal?: string;
  targetGeo?: string;
  targetRoles?: string;
  companySize?: string;
  industry?: string;
  product?: string;
}

export interface CampaignCreate {
  name: string;
  description?: string;
  icp: string;
  status: CampaignStatus;
  goal?: string;
  targetGeo?: string;
  targetRoles?: string;
  companySize?: string;
  industry?: string;
  product?: string;
}

export interface CampaignStatusUpdate {
  status: CampaignStatus;
}

// ─── Prospect ────────────────────────────────────────────────────────────────

export type ProspectStatus =
  | 'FIT'
  | 'REVIEW'
  | 'NO_FIT'
  | 'CONTACTED'
  | 'REPLIED'
  | 'MEETING';

export type OutreachChannel = 'EMAIL' | 'LINKEDIN' | 'SMS' | 'PHONE';

export interface Prospect {
  id: string;
  name: string;
  email: string;
  phone?: string;
  linkedin_url?: string;
  title: string;
  company: string;
  domain?: string;
  location?: string;
  companySize?: string;
  notes?: string;
  campaignId?: string;
  campaignName?: string;
  icpScore?: number;
  status?: ProspectStatus;
  channel?: OutreachChannel;
  lastActivity?: string;
}

export interface ProspectCreate {
  name: string;
  email: string;
  phone?: string;
  linkedin_url?: string;
  title: string;
  company: string;
  domain?: string;
  location?: string;
  companySize?: string;
  notes?: string;
  campaignId?: string;
}

// ─── Agent ───────────────────────────────────────────────────────────────────

export type AgentStatus = 'ACTIVE' | 'IDLE' | 'ERROR';
export type ExecutionStatus = 'RUNNING' | 'COMPLETED' | 'FAILED' | 'WAITING';

export interface AgentExecution {
  id: string;
  agentId: string;
  prospect?: string;
  campaign?: string;
  status: ExecutionStatus;
  startedAt: string;
  completedAt?: string;
  duration?: number;
  output?: string;
}

export interface Agent {
  id: string;
  name: string;
  description: string;
  responsibilities: string[];
  status: AgentStatus;
  executions: number;
  successRate: number;
  lastRun?: string;
  avgDuration?: number;
  recentExecutions?: AgentExecution[];
}

// ─── Activity ─────────────────────────────────────────────────────────────────

export type ActivityCategory =
  | 'research'
  | 'qualification'
  | 'strategy'
  | 'personalisation'
  | 'conversation'
  | 'follow-up'
  | 'voice'
  | 'campaign';

export interface ActivityEvent {
  id: string;
  agentName: string;
  action: string;
  prospect?: string;
  campaign?: string;
  status: ExecutionStatus;
  category: ActivityCategory;
  timestamp: string;
}

// ─── Outreach ─────────────────────────────────────────────────────────────────

export type OutreachStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'SENT';

export interface OutreachMessage {
  id: string;
  prospectId: string;
  prospectName: string;
  channel: OutreachChannel;
  subject?: string;
  body: string;
  generatedBy: string;
  timestamp: string;
  status: OutreachStatus;
  requiresApproval?: boolean;
}

// ─── SDR Run ─────────────────────────────────────────────────────────────────

export interface SDRRunRequest {
  campaign_id: string;
  prospect_id: string;
}

export interface SDRRunResponse {
  run_id: string;
  campaign_id: string;
  prospect_id: string;
  status: 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  fitment?: string;
  reasoning?: string;
  email_status?: string;
  email_details?: {
    to: string;
    subject: string;
    preview: string;
    sent_via: string;
    delivery_message?: string;
  };
}

export interface ExecutionRecord {
  execution_id: string;
  campaign_id: string;
  prospect_id: string;
  status: string;
  current_agent: string;
  channel?: string;
  recommended_channel?: string;
  actual_channel?: string;
  action_type?: string;
  provider_call_id?: string;
  started_at: string;
  answered_at?: string;
  ended_at?: string;
  duration?: number;
  call_outcome?: string;
  completed_at?: string;
  error?: string;
  voice_agent_result?: {
    conversation_summary?: string;
    call_outcome?: string;
    interested?: boolean;
    objections?: string[];
    follow_up_required?: boolean;
    next_action?: string;
    [key: string]: any;
  };
  research_result?: {
    prospect_id?: string;
    prospect_summary?: string;
    verified_domain?: string;
    detected_tech_stack?: string[];
    personalisation_hooks?: string[];
    [key: string]: any;
  };
  icp_result?: {
    status?: string;
    score?: number;
    reasoning?: string;
    matched_criteria?: string[];
    unmatched_criteria?: string[];
    [key: string]: any;
  };
  strategy_result?: {
    recommended_channel?: string;
    action_type?: string;
    angle?: string;
    tone?: string;
    instructions_for_copywriter?: string;
    suggested_wait_days?: number;
    reasoning?: string;
    [key: string]: any;
  };
  personalisation_result?: {
    channel?: string;
    subject_line?: string;
    content?: string;
    rag_sources_cited?: string[];
    confidence_score?: number;
    [key: string]: any;
  };
  channel_result?: {
    channel?: string;
    status?: string;
    provider_message_id?: string;
    recipient?: string;
    error?: string;
    trial_template_used?: string;
    timestamp?: string;
    [key: string]: any;
  };
  fitment?: string;
  email_status?: string;
  email_details?: {
    to?: string;
    subject?: string;
    preview?: string;
    sent_via?: string;
    delivery_message?: string;
  };
}

// ─── Analytics ────────────────────────────────────────────────────────────────

export interface AnalyticsSummary {
  totalProspects: number;
  qualified: number;
  qualificationRate: number;
  messagesSent: number;
  replies: number;
  replyRate: number;
  meetings: number;
  meetingRate: number;
}

export interface ChartDataPoint {
  name: string;
  value: number;
  [key: string]: string | number;
}

// ─── Operational Controls & Problem Statement Additions ─────────────────────

export interface OperationalControls {
  global_kill_switch: boolean;
  kill_switch_triggered_at?: string | null;
  kill_switch_reason?: string | null;
  paused_channels: string[];
  paused_agents: string[];
  campaign_summary?: {
    total: number;
    live: number;
    paused: number;
  };
  system_status: 'HEALTHY' | 'EMERGENCY_STOPPED';
}

export interface PromptHarness {
  system_prompt: string;
  agent_prompts: {
    icp_fitment?: string;
    lead_research?: string;
    outreach_strategy?: string;
    personalisation?: string;
    conversation?: string;
    follow_up?: string;
    voice_sdr?: string;
    [key: string]: string | undefined;
  };
  version: string;
  author: string;
  updated_at: string;
}

export interface PromptHistoryResponse {
  campaign_id: string;
  current: PromptHarness;
  history: PromptHarness[];
  version_count: number;
}

export interface SalesRep {
  id: string;
  name: string;
  email: string;
  role: string;
  channels: string[];
  daily_quota: number;
  working_hours: string;
  status: 'ACTIVE' | 'OFFBOARDED';
}

export interface CampaignConflict {
  id: string;
  type: string;
  severity: 'HIGH' | 'MEDIUM' | 'LOW';
  title: string;
  email?: string;
  company?: string;
  prospect_id?: string;
  involved_campaigns: string[];
  description: string;
  suggested_action: string;
}

export interface TokenEconomics {
  summary: {
    total_tokens_consumed: number;
    prompt_tokens: number;
    completion_tokens: number;
    total_cost_usd: number;
    cost_per_prospect_usd: number;
    cost_per_qualified_lead_usd: number;
    average_latency_ms: number;
  };
  agent_breakdown: Array<{
    agent: string;
    model: string;
    tokens: number;
    cost: number;
    avg_latency_ms: number;
  }>;
  optimization_notes: string[];
}

