import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';
import { Dashboard } from './pages/Dashboard';
import { Campaigns } from './pages/Campaigns';
import { CampaignDetail } from './pages/CampaignDetail';
import { ProspectDiscovery } from './pages/ProspectDiscovery';
import { Prospects } from './pages/Prospects';
import { Agents } from './pages/Agents';
import { ControlCentre } from './pages/ControlCentre';
import { Activity } from './pages/Activity';
import { Analytics } from './pages/Analytics';
import { Settings } from './pages/Settings';
import { Agent0SourcingScout } from './pages/Agent0SourcingScout';
import { Agent1DeepResearch } from './pages/Agent1DeepResearch';
import { Agent2ICPGate } from './pages/Agent2ICPGate';
import { Agent3OutreachTiming } from './pages/Agent3OutreachTiming';
import { Agent5ConversationBasket } from './pages/Agent5ConversationBasket';
import { Agent6VoiceAI } from './pages/Agent6VoiceAI';
import { AgentFleetSignalCalibration } from './pages/AgentFleetSignalCalibration';
import { Inbox } from './pages/Inbox';
import { NectarIntelligenceDesk } from './pages/NectarIntelligenceDesk';
import { Login } from './pages/Login';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route element={<AppLayout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/agents" element={<Agents />} />
          <Route path="/agents/signal-calibration" element={<AgentFleetSignalCalibration />} />
          <Route path="/agents/0" element={<Agent0SourcingScout />} />
          <Route path="/agents/1" element={<Agent1DeepResearch />} />
          <Route path="/agents/2" element={<Agent2ICPGate />} />
          <Route path="/agents/3" element={<Agent3OutreachTiming />} />
          <Route path="/agents/4" element={<AgentFleetSignalCalibration />} />
          <Route path="/agents/5" element={<Agent5ConversationBasket />} />
          <Route path="/agents/6" element={<Agent6VoiceAI />} />
          <Route path="/control-centre" element={<ControlCentre />} />
          <Route path="/campaigns" element={<Campaigns />} />
          <Route path="/campaigns/:id" element={<CampaignDetail />} />
          <Route path="/discovery" element={<ProspectDiscovery />} />
          <Route path="/prospects" element={<Prospects />} />
          <Route path="/inbox" element={<Inbox />} />
          <Route path="/activity" element={<Activity />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/settings" element={<Settings />} />
        </Route>
        {/* Standalone full-page — no AppLayout header/sidebar */}
        <Route path="/chatbot" element={<NectarIntelligenceDesk />} />
      </Routes>
    </BrowserRouter>
  );
}
