import { ActivityEvent } from '@/types';

export const demoActivity: ActivityEvent[] = [
  { id: 'a1', agentName: 'ICP Fitment Agent', action: 'Prospect qualified with score 91', prospect: 'James Carter', campaign: 'US SaaS CTOs', status: 'COMPLETED', category: 'qualification', timestamp: '12:42' },
  { id: 'a2', agentName: 'Personalisation Agent', action: 'Generated personalised email', prospect: 'James Carter', campaign: 'US SaaS CTOs', status: 'COMPLETED', category: 'personalisation', timestamp: '12:40' },
  { id: 'a3', agentName: 'Lead Research Agent', action: 'Completed prospect intelligence report', prospect: 'James Carter', campaign: 'US SaaS CTOs', status: 'COMPLETED', category: 'research', timestamp: '12:37' },
  { id: 'a4', agentName: 'Outreach Strategy Agent', action: 'Selected EMAIL channel for outreach', prospect: 'Sarah Kim', campaign: 'US SaaS CTOs', status: 'COMPLETED', category: 'strategy', timestamp: '12:34' },
  { id: 'a5', agentName: 'ICP Fitment Agent', action: 'Prospect reviewed — score 74, needs human review', prospect: 'Rajesh Patel', campaign: 'India BFSI CIOs', status: 'COMPLETED', category: 'qualification', timestamp: '12:31' },
  { id: 'a6', agentName: 'Conversation Agent', action: 'Reply detected — drafted response', prospect: 'Priya Nair', campaign: 'India BFSI CIOs', status: 'COMPLETED', category: 'conversation', timestamp: '12:28' },
  { id: 'a7', agentName: 'Follow-up Agent', action: 'Sent follow-up #2', prospect: 'Alex Reid', campaign: 'Voice AI Founders', status: 'COMPLETED', category: 'follow-up', timestamp: '12:20' },
  { id: 'a8', agentName: 'Campaign', action: 'Campaign started', campaign: 'US SaaS CTOs', status: 'COMPLETED', category: 'campaign', timestamp: '12:00' },
  { id: 'a9', agentName: 'Voice SDR Agent', action: 'Call placed — voicemail left', prospect: 'James Carter', campaign: 'US SaaS CTOs', status: 'COMPLETED', category: 'voice', timestamp: '11:50' },
  { id: 'a10', agentName: 'Personalisation Agent', action: 'LinkedIn message drafted', prospect: 'Priya Nair', campaign: 'India BFSI CIOs', status: 'COMPLETED', category: 'personalisation', timestamp: '11:42' },
  { id: 'a11', agentName: 'Lead Research Agent', action: 'Research complete — 3 pain points identified', prospect: 'Ananya Singh', campaign: 'Voice AI Founders', status: 'COMPLETED', category: 'research', timestamp: '11:35' },
  { id: 'a12', agentName: 'ICP Fitment Agent', action: 'Prospect scored 95 — STRONG FIT', prospect: 'Alex Reid', campaign: 'Voice AI Founders', status: 'COMPLETED', category: 'qualification', timestamp: '11:30' },
  { id: 'a13', agentName: 'Conversation Agent', action: 'Meeting requested — escalating to human', prospect: 'James Carter', campaign: 'US SaaS CTOs', status: 'COMPLETED', category: 'conversation', timestamp: '11:20' },
  { id: 'a14', agentName: 'Follow-up Agent', action: 'Follow-up sequence exhausted — marking COLD', prospect: 'Michael Torres', campaign: 'US SaaS CTOs', status: 'COMPLETED', category: 'follow-up', timestamp: '11:10' },
  { id: 'a15', agentName: 'Lead Research Agent', action: 'Research failed — insufficient public data', prospect: 'David Nguyen', campaign: 'US SaaS CTOs', status: 'FAILED', category: 'research', timestamp: '11:05' },
];
