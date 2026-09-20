import { useState } from 'react';
import toast from 'react-hot-toast';
import { voiceApi, VoiceTranscriptResponse } from '@/api/voice';

export function Agent6VoiceAI() {
  const waveBars = [3, 6, 10, 14, 8, 12, 16, 10, 5, 9, 14, 12, 7, 11, 15, 8, 4, 13, 10, 6, 12, 16, 9, 5, 8, 3];
  const waveColors = [
    'bg-surface-container-highest', 'bg-surface-container-highest', 'bg-primary-container', 'bg-primary-container',
    'bg-primary', 'bg-primary', 'bg-primary-container', 'bg-primary-container', 'bg-surface-container-highest',
    'bg-primary', 'bg-primary-container', 'bg-primary', 'bg-surface-container-highest', 'bg-primary-container',
    'bg-primary-container', 'bg-primary', 'bg-surface-container-highest', 'bg-primary-container',
    'bg-surface-container-highest', 'bg-surface-container-highest', 'bg-primary-container', 'bg-primary',
    'bg-primary-container', 'bg-surface-container-highest', 'bg-surface-container-highest', 'bg-surface-container-highest',
  ];

  // Test Call state
  const [phoneNumber, setPhoneNumber] = useState('+917419045750');
  const [calling, setCalling] = useState(false);
  const [callSid, setCallSid] = useState<string | null>(null);
  const [executionId, setExecutionId] = useState<string | null>(null);
  const [callStatus, setCallStatus] = useState<string | null>(null);
  const [transcriptData, setTranscriptData] = useState<VoiceTranscriptResponse | null>(null);
  const [loadingTranscript, setLoadingTranscript] = useState(false);

  // Trigger outbound call
  const handleInitiateCall = async () => {
    if (!phoneNumber.trim()) {
      toast.error('Please enter a valid phone number');
      return;
    }
    setCalling(true);
    setCallStatus('Initiating Call...');
    setTranscriptData(null);
    try {
      const res = await voiceApi.testCall({
        phone: phoneNumber.trim(),
        prospect_id: 'parvesh_user',
      });
      setCallSid(res.twilio_call_sid);
      setExecutionId(res.execution_id);
      setCallStatus(res.status || 'RINGING');
      toast.success(`Call placed! SID: ${res.twilio_call_sid.substring(0, 10)}...`);
    } catch (err: any) {
      toast.error(err.message || 'Failed to place call. Ensure backend is running.');
      setCallStatus('Failed');
    } finally {
      setCalling(false);
    }
  };

  // Fetch live transcript
  const handleFetchTranscript = async () => {
    const id = executionId || callSid;
    if (!id) {
      toast.error('No active or recent call found. Place a call first.');
      return;
    }
    setLoadingTranscript(true);
    try {
      const data = await voiceApi.getTranscript(id);
      setTranscriptData(data);
      toast.success(`Loaded ${data.turns_count || 0} conversation turns!`);
    } catch (err: any) {
      toast.error('Transcript not ready yet. Please wait for the call to finish.');
    } finally {
      setLoadingTranscript(false);
    }
  };

  return (
    <div className="w-full bg-surface min-h-screen px-space-lg py-space-lg">
      <div className="flex flex-col w-full relative">
        <div className="relative mx-auto w-full max-w-5xl my-4 rounded-xl bg-surface-container-lowest shadow-2xl overflow-hidden flex flex-col border border-surface-container-high">
          {/* Header */}
          <div className="px-space-xl pt-space-xl pb-space-lg bg-surface-container-low flex flex-col gap-space-md border-b border-surface-container-high">
            <div className="flex flex-wrap items-center justify-between gap-space-sm">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-inverse-surface text-surface text-label-sm font-label-sm tracking-wider uppercase">
                  <span className="w-1.5 h-1.5 rounded-full bg-primary-container animate-pulse"></span>
                  Node 06
                </span>
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-surface text-on-surface text-label-sm font-label-sm shadow-sm">
                  <span className="material-symbols-outlined text-[14px] text-tertiary">graphic_eq</span>
                  Ultra-Low Latency Voice Synthesizer
                </span>
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-tertiary-fixed text-on-tertiary-fixed text-label-sm font-label-sm shadow-sm">
                  <span className="material-symbols-outlined text-[14px]">hearing</span>
                  Whisper &amp; Barge-in Enabled
                </span>
              </div>
            </div>
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-space-md pt-space-xs">
              <div>
                <span className="font-label-sm text-label-sm text-outline uppercase tracking-widest text-[11px] font-semibold">
                  Autonomous Audio Pipeline
                </span>
                <h2 className="font-headline-lg text-headline-lg text-on-surface tracking-tight mt-0.5 font-bold text-2xl">
                  Agent 6: Voice AI &amp; Live Escalation
                </h2>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <div className="px-3 py-1.5 rounded-lg bg-surface-container flex items-center gap-2 text-label-sm font-label-sm text-on-surface">
                  <span className="material-symbols-outlined text-[16px] text-outline">call_log</span>
                  <span>48 calls today</span>
                </div>
                <div className="px-3 py-1.5 rounded-lg bg-surface-container flex items-center gap-2 text-label-sm font-label-sm text-on-surface">
                  <span className="material-symbols-outlined text-[16px] text-tertiary">speed</span>
                  <span>Avg Latency: <strong className="font-semibold text-tertiary">240ms</strong></span>
                </div>
                <div className="px-3 py-1.5 rounded-lg bg-primary-fixed text-on-primary-fixed flex items-center gap-2 text-label-sm font-label-sm font-semibold">
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
                  </span>
                  <span>Live: Alex (AI SDR)</span>
                </div>
              </div>
            </div>
          </div>

          {/* Body */}
          <div className="p-space-xl flex flex-col gap-space-xl bg-surface-container-lowest overflow-y-auto">
            {/* LIVE OUTBOUND CALL DISPATCH TEST SECTION */}
            <div className="bg-[#1c1c17] text-white rounded-2xl p-space-lg shadow-md border border-neutral-800 flex flex-col gap-space-md">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-white/10 pb-3">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-full bg-primary-container text-on-primary-container flex items-center justify-center font-bold">
                    <span className="material-symbols-outlined text-[18px]">phone_in_talk</span>
                  </div>
                  <div>
                    <h3 className="font-bold text-lg text-white">Live Outbound Twilio + Groq AI Call Dispatch</h3>
                    <p className="text-xs text-white/60">
                      Dispatches a real phone call to your verified number with Groq conversational AI voice agent (Alex).
                    </p>
                  </div>
                </div>
                {callStatus && (
                  <span className="px-3 py-1 rounded-full bg-primary-container/20 text-primary-fixed text-xs font-bold border border-primary-container/40">
                    Status: {callStatus}
                  </span>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
                <div className="md:col-span-7 flex flex-col gap-1.5">
                  <label className="text-xs font-semibold text-white/70">Verified Prospect Phone Number (E.164 format):</label>
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      value={phoneNumber}
                      onChange={(e) => setPhoneNumber(e.target.value)}
                      placeholder="+917419045750"
                      className="flex-1 bg-white/5 border border-white/15 rounded-xl px-4 py-2.5 text-white placeholder:text-white/30 focus:outline-none focus:border-primary-container text-sm font-mono"
                    />
                    <button
                      onClick={handleInitiateCall}
                      disabled={calling}
                      className="px-5 py-2.5 rounded-xl bg-primary-container text-on-primary-container hover:brightness-110 font-bold text-sm transition-all shadow-sm flex items-center gap-2 shrink-0 active:scale-95"
                    >
                      <span className="material-symbols-outlined text-[18px]">call</span>
                      <span>{calling ? 'Dialing...' : 'Place Call Now'}</span>
                    </button>
                  </div>
                </div>

                <div className="md:col-span-5 flex flex-col gap-1.5 bg-white/5 p-3 rounded-xl border border-white/10">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-white/50">Call SID:</span>
                    <span className="font-mono text-primary-fixed">{callSid ? callSid.substring(0, 16) + '...' : 'Not dialed yet'}</span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-white/50">Engine:</span>
                    <span className="text-white/90">Groq qwen/qwen3.8-27b (~240ms)</span>
                  </div>
                  <button
                    onClick={handleFetchTranscript}
                    disabled={loadingTranscript || !callSid}
                    className="mt-1 w-full py-1.5 rounded-lg bg-white/10 hover:bg-white/15 text-white text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors"
                  >
                    <span className="material-symbols-outlined text-[14px]">receipt_long</span>
                    <span>{loadingTranscript ? 'Fetching...' : 'View Call Transcript'}</span>
                  </button>
                </div>
              </div>

              {/* Transcript Display Box */}
              {transcriptData && (
                <div className="mt-2 p-3.5 rounded-xl bg-black/40 border border-white/10 flex flex-col gap-2">
                  <div className="flex items-center justify-between text-xs border-b border-white/10 pb-2">
                    <span className="font-bold text-white flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-[16px] text-tertiary">record_voice_over</span>
                      Call Transcript ({transcriptData.turns_count} turns recorded)
                    </span>
                    <span className="text-white/40 font-mono text-[11px]">{transcriptData.identifier}</span>
                  </div>
                  <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                    {transcriptData.turns && transcriptData.turns.length > 0 ? (
                      transcriptData.turns.map((t, idx) => (
                        <div key={idx} className="space-y-1 text-xs">
                          <div className="flex items-start gap-2 text-white/90">
                            <span className="font-bold text-primary-container shrink-0">Prospect:</span>
                            <span className="italic">"{t.user_speech}"</span>
                          </div>
                          <div className="flex items-start gap-2 text-white/80 pl-3">
                            <span className="font-bold text-tertiary-fixed shrink-0">Alex (AI SDR):</span>
                            <span>"{t.agent_response}"</span>
                          </div>
                        </div>
                      ))
                    ) : (
                      <p className="text-xs text-white/60 italic">
                        {transcriptData.full_transcript || 'Call completed. No speech recorded yet.'}
                      </p>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Section 1: Voice Persona */}
            <div className="flex flex-col gap-space-md">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-space-sm">
                  <span className="w-6 h-6 rounded-full bg-surface-container-high text-on-surface font-label-sm text-label-sm flex items-center justify-center font-semibold">01</span>
                  <h3 className="font-headline-sm text-headline-sm text-on-surface font-bold text-base">Voice Persona &amp; Acoustic Cadence</h3>
                </div>
                <span className="text-label-sm font-label-sm text-tertiary bg-tertiary-fixed/60 px-2.5 py-0.5 rounded-full font-medium">Neural Engine V3.4 active</span>
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-space-md">
                {/* Waveform Card */}
                <div className="lg:col-span-7 bg-surface-container-low rounded-xl p-space-lg flex flex-col justify-between shadow-sm relative overflow-hidden border border-surface-container-high">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <span className="font-label-sm text-label-sm uppercase tracking-wider text-outline text-[11px] font-semibold">Active Timbre</span>
                      <p className="font-headline-sm text-headline-sm text-on-surface mt-0.5 font-bold">Warm Executive Neutral</p>
                      <p className="font-body-sm text-body-sm text-on-surface-variant text-xs">Low nasal resonance, articulate micro-inflections, confident pitch floor.</p>
                    </div>
                    <div className="bg-surface-container p-1 rounded-full flex items-center shadow-inner">
                      <button className="px-3 py-1 rounded-full bg-surface-container-lowest text-on-surface text-label-sm font-label-sm shadow-sm transition-all font-semibold">Female</button>
                      <button className="px-3 py-1 rounded-full text-on-surface-variant hover:text-on-surface text-label-sm font-label-sm transition-all">Male</button>
                    </div>
                  </div>
                  <div className="my-space-md bg-surface-container-lowest rounded-xl p-space-md flex flex-col gap-2 shadow-sm border border-surface-container-high/60">
                    <div className="flex items-center justify-between text-label-sm font-label-sm text-outline text-xs">
                      <span className="flex items-center gap-1.5">
                        <span className="material-symbols-outlined text-[16px] text-primary-container">mic</span>
                        Synthesized Sample (Acme Pitch Deck QA)
                      </span>
                      <span className="text-on-surface font-mono">00:03.4 / 00:06.0</span>
                    </div>
                    <div className="h-16 flex items-center justify-between gap-1 px-1">
                      {waveBars.map((h, i) => (
                        <div key={i} className={`w-1.5 rounded-full ${waveColors[i]}`} style={{ height: `${h * 4}px` }}></div>
                      ))}
                    </div>
                    <div className="flex items-center justify-between pt-1">
                      <button
                        onClick={() => toast.success('Playing synthesis sample audio...')}
                        className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary text-on-primary font-label-md text-label-md hover:bg-primary-container hover:text-on-primary-container transition-colors shadow-sm text-xs font-semibold"
                      >
                        <span className="material-symbols-outlined text-[16px]">play_arrow</span>
                        <span>Play Synthesis Preview</span>
                      </button>
                      <span className="text-label-sm font-label-sm text-outline text-[11px]">Trained on 420 hrs executive sales audio</span>
                    </div>
                  </div>
                </div>

                {/* Persona Attributes Card */}
                <div className="lg:col-span-5 bg-surface-container-low rounded-xl p-space-lg flex flex-col justify-between shadow-sm border border-surface-container-high">
                  <div>
                    <span className="font-label-sm text-label-sm uppercase tracking-wider text-outline text-[11px] font-semibold">Prosody Parameters</span>
                    <h4 className="font-headline-sm text-headline-sm text-on-surface mt-0.5 font-bold">Delivery Nuance Controls</h4>
                  </div>
                  <div className="flex flex-col gap-3 my-space-sm">
                    <div>
                      <div className="flex justify-between text-label-sm font-label-sm mb-1 text-xs">
                        <span className="text-on-surface font-semibold">Speaking Rate</span>
                        <span className="font-mono text-primary font-bold">142 WPM</span>
                      </div>
                      <div className="w-full h-1.5 rounded-full bg-surface-container-highest overflow-hidden">
                        <div className="w-[62%] h-full bg-primary rounded-full"></div>
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between text-label-sm font-label-sm mb-1 text-xs">
                        <span className="text-on-surface font-semibold">Interruption Sensitivity</span>
                        <span className="font-mono text-tertiary font-bold">High (350ms)</span>
                      </div>
                      <div className="w-full h-1.5 rounded-full bg-surface-container-highest overflow-hidden">
                        <div className="w-[85%] h-full bg-tertiary rounded-full"></div>
                      </div>
                    </div>
                  </div>
                  <div className="p-3 bg-surface-container-lowest rounded-xl flex items-center justify-between border border-surface-container-high/60">
                    <span className="text-xs text-on-surface font-semibold">Barge-in Threshold</span>
                    <span className="text-xs font-mono bg-surface-container px-2 py-0.5 rounded font-bold text-tertiary">Adaptive</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Section 2: Real-time Supervision & Barge-in */}
            <div className="flex flex-col gap-space-md">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-space-sm">
                  <span className="w-6 h-6 rounded-full bg-surface-container-high text-on-surface font-label-sm text-label-sm flex items-center justify-center font-semibold">02</span>
                  <h3 className="font-headline-sm text-headline-sm text-on-surface font-bold text-base">Real-time Supervision &amp; Whisper Protocol</h3>
                </div>
                <span className="text-label-sm font-label-sm text-outline text-xs">Low latency WebSocket bridge</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-space-md">
                {[
                  { icon: 'smart_toy', badge: 'Active Mode', title: '1. Fully Autonomous', desc: 'Agent conducts qualification call end-to-end using the dynamic objection handling framework.' },
                  { icon: 'record_voice_over', badge: 'Standby', title: '2. Whisper Mode', desc: 'Supervisor speaks directly to coach answers live without prospect hearing.' },
                  { icon: 'phone_in_talk', badge: 'Instant', title: '3. One-Click Barge-in', desc: 'Take over audio immediately with smooth crossfade, notifying the prospect politely.' },
                ].map((mode) => (
                  <div key={mode.title} className="p-4 rounded-xl bg-surface-container-low border border-surface-container-high flex flex-col justify-between gap-3">
                    <div className="flex items-center justify-between">
                      <div className="w-8 h-8 rounded-lg bg-surface-container flex items-center justify-center">
                        <span className="material-symbols-outlined text-[18px] text-primary">{mode.icon}</span>
                      </div>
                      <span className="px-2 py-0.5 rounded-full bg-surface-container text-xs font-semibold">{mode.badge}</span>
                    </div>
                    <div>
                      <h4 className="font-bold text-sm text-on-surface">{mode.title}</h4>
                      <p className="text-xs text-on-surface-variant mt-1">{mode.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="px-space-xl py-space-md bg-surface-container-low flex flex-col sm:flex-row items-center justify-between gap-space-md border-t border-surface-container-high">
            <div className="flex items-center gap-2 text-outline font-label-sm text-label-sm text-xs">
              <span className="material-symbols-outlined text-[16px] text-tertiary">lock</span>
              <span>End-to-end encrypted voice session (TLS 1.3 + SRTP)</span>
            </div>
            <div className="flex items-center gap-space-sm w-full sm:w-auto justify-end">
              <button
                onClick={() => toast.success('Microphone calibrated! Noise floor: -48dB')}
                className="px-4 py-2 rounded-full bg-surface-container-lowest text-on-surface hover:bg-surface-container font-label-md text-label-md shadow-sm transition-colors flex items-center gap-1.5 text-xs font-semibold"
              >
                <span className="material-symbols-outlined text-[16px]">mic_none</span>
                <span>Test Microphone Sample</span>
              </button>
              <button
                onClick={() => toast.success('Voice AI rules deployed across fleet!')}
                className="px-5 py-2 rounded-full bg-primary-container text-on-primary-container hover:brightness-105 font-label-lg text-label-lg shadow-sm transition-all flex items-center gap-2 font-bold text-xs"
              >
                <span className="material-symbols-outlined text-[16px]">check</span>
                <span>Deploy Voice AI Rules</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
