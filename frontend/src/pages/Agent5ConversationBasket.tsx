export function Agent5ConversationBasket() {
  return (
    <div className="w-full bg-surface min-h-screen px-space-lg py-space-lg">
      <div className="flex flex-col w-full relative">
        <div className="w-full max-w-5xl mx-auto bg-surface-container-lowest rounded-xl shadow-2xl overflow-hidden flex flex-col">
          {/* Header */}
          <div className="bg-surface-container-low px-space-lg pt-space-lg pb-space-md flex flex-col gap-space-sm">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-space-xs flex-wrap">
                <span className="px-2.5 py-0.5 rounded-full bg-inverse-surface text-surface font-label-sm text-label-sm tracking-wider uppercase">NODE 05</span>
                <span className="px-2.5 py-0.5 rounded-full bg-surface-container-highest text-on-surface-variant font-label-sm text-label-sm">Autonomous Intent Classifier &amp; Safety Guardrail</span>
                <span className="px-2.5 py-0.5 rounded-full bg-tertiary-fixed text-on-tertiary-fixed font-label-sm text-label-sm flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-tertiary inline-block"></span>
                  Human-in-the-Loop Active
                </span>
              </div>
            </div>
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-space-sm mt-1">
              <div>
                <h1 className="font-headline-lg text-headline-lg text-on-surface tracking-tight">Agent 5: Conversation Basket &amp; Safety</h1>
                <p className="font-body-sm text-body-sm text-on-surface-variant mt-0.5">Defines intent classification, semantic triage routing, and fail-safe human handover gates.</p>
              </div>
              <div className="flex items-center gap-2 flex-wrap">
                {[
                  { label: 'Auto-handled', value: '82%', valueColor: 'text-tertiary' },
                  { label: 'Escalated', value: '18%', valueColor: 'text-primary' },
                  { label: 'Freeze Latency', value: '<120ms', valueColor: 'text-on-surface' },
                  { label: 'Violations', value: '0', valueColor: 'text-tertiary' },
                ].map(stat => (
                  <div key={stat.label} className="px-3 py-1 rounded-full bg-surface-container flex items-center gap-1.5 shadow-sm">
                    <span className="font-label-sm text-label-sm text-on-surface-variant uppercase">{stat.label}</span>
                    <span className={`font-label-md text-label-md font-bold ${stat.valueColor}`}>{stat.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Body */}
          <div className="p-space-lg flex flex-col gap-space-lg bg-surface-container-lowest">
            {/* Intent Baskets */}
            <div className="flex flex-col gap-space-sm">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-primary-container"></span>
                  <span className="font-label-sm text-label-sm uppercase tracking-wider text-outline">Section 01 // Intent Routing Architecture</span>
                </div>
                <span className="font-body-sm text-body-sm text-on-surface-variant">Real-time inference via vector semantic match</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-gutter">
                {[
                  {
                    num: 'Basket 1', badge: 'Autonomous', badgeColor: 'bg-tertiary-fixed text-on-tertiary-fixed',
                    title: 'Questions & Product Info',
                    desc: 'Direct technical and capability inquiries with authoritative knowledge bases.',
                    examples: ['"How does it integrate with GitHub?"', '"Do you have SOC-2 Type II?"'],
                    exIcon: 'chat_bubble', exIconColor: 'text-tertiary',
                    footerBg: 'bg-surface-container-lowest/60',
                    footerIcon: 'verified', footerIconColor: 'text-tertiary',
                    footerTitle: 'Agent 4 Claim Library',
                    footerDesc: 'Autonomous reply generated with citing verified documentation.',
                  },
                  {
                    num: 'Basket 2', badge: 'Smart Reframe', badgeColor: 'bg-primary-fixed text-on-primary-fixed',
                    title: 'Objections & Timing',
                    desc: 'Bandwidth limitations, contract cycles, or existing vendor commitments.',
                    examples: ['"Not now, busy until Q4."', '"Already using competitor."'],
                    exIcon: 'chat_bubble', exIconColor: 'text-primary',
                    footerBg: 'bg-surface-container-lowest/60',
                    footerIcon: 'schedule_send', footerIconColor: 'text-primary',
                    footerTitle: 'Cool-off & Nudge',
                    footerDesc: 'Acknowledge gracefully, set follow-up trigger, avoid pushiness.',
                  },
                  {
                    num: 'Basket 3', badge: 'Strict Handover', badgeColor: 'bg-error-container text-on-error-container',
                    title: 'Pricing & Contracts',
                    desc: 'Commercial negotiations, seat volumes, enterprise licensing tiers.',
                    examples: ['"What\'s pricing for 50 seats?"', '"Can we get an annual discount?"'],
                    exIcon: 'chat_bubble', exIconColor: 'text-error',
                    footerBg: 'bg-error-container/25',
                    footerIcon: 'pause_circle', footerIconColor: 'text-error',
                    footerTitle: 'Instant Freeze -> Ramya',
                    footerDesc: 'Bot freezes under 120ms; human notified with synthesized draft.',
                  },
                  {
                    num: 'Basket 4', badge: 'Zero-Bot Zone', badgeColor: 'bg-inverse-surface text-surface',
                    title: 'Legal & Complaints',
                    desc: 'Compliance mandates, regulatory opt-outs, and legal threats.',
                    examples: ['"GDPR formal unsubscribe."', '"Talk to our legal counsel."'],
                    exIcon: 'warning', exIconColor: 'text-error',
                    footerBg: 'bg-surface-container-highest',
                    footerIcon: 'lock', footerIconColor: 'text-error',
                    footerTitle: 'Hard Domain Lockout',
                    footerDesc: 'Prospect blacklisted across all campaigns; incident logged.',
                  },
                ].map(basket => (
                  <div key={basket.num} className="group bg-surface-container-low hover:bg-surface-container rounded-xl p-space-md flex flex-col justify-between transition-all shadow-sm">
                    <div className="space-y-space-sm">
                      <div className="flex items-center justify-between">
                        <span className="font-headline-sm text-headline-sm text-on-surface">{basket.num}</span>
                        <span className={`px-2 py-0.5 rounded-full font-label-sm text-label-sm font-semibold ${basket.badgeColor}`}>{basket.badge}</span>
                      </div>
                      <div>
                        <h3 className="font-label-lg text-label-lg text-on-surface">{basket.title}</h3>
                        <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">{basket.desc}</p>
                      </div>
                      <div className="bg-surface-container-lowest p-2.5 rounded-lg space-y-1.5 shadow-inner">
                        {basket.examples.map(ex => (
                          <div key={ex} className="flex items-start gap-1.5 text-on-surface">
                            <span className={`material-symbols-outlined text-[14px] ${basket.exIconColor} mt-0.5`}>{basket.exIcon}</span>
                            <span className="font-body-sm text-body-sm italic">{ex}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                    <div className={`mt-space-md pt-2 ${basket.footerBg} -mx-space-md -mb-space-md p-space-md rounded-b-xl`}>
                      <div className={`flex items-center gap-1.5 font-label-sm text-label-sm font-bold ${basket.footerIconColor}`}>
                        <span className="material-symbols-outlined text-[16px]">{basket.footerIcon}</span>
                        <span>{basket.footerTitle}</span>
                      </div>
                      <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">{basket.footerDesc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Sensitivity Sliders & Stop-Words */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-gutter pt-2">
              {/* Confidence Sliders */}
              <div className="lg:col-span-7 bg-surface-container-low p-space-md rounded-xl space-y-space-md shadow-sm">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="font-label-sm text-label-sm uppercase tracking-wider text-outline">Tuning &amp; Safety Thresholds</span>
                    <h4 className="font-headline-sm text-headline-sm text-on-surface">Confidence Trigger Calibration</h4>
                  </div>
                  <span className="px-2 py-0.5 rounded-full bg-surface-container-highest text-on-surface-variant font-label-sm text-label-sm">Bayesian Triage</span>
                </div>
                <div className="space-y-2 bg-surface-container-lowest p-space-sm rounded-xl">
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-2">
                      <span className="material-symbols-outlined text-tertiary text-[18px]">verified</span>
                      <span className="font-label-md text-label-md text-on-surface">Auto-send Threshold</span>
                    </div>
                    <span className="font-label-md text-label-md text-tertiary bg-surface-container px-2 py-0.5 rounded font-bold">88%</span>
                  </div>
                  <input className="w-full accent-primary h-1.5 bg-surface-container-high rounded-full cursor-pointer" max="98" min="60" type="range" defaultValue="88" />
                  <div className="flex justify-between text-on-surface-variant font-body-sm text-body-sm">
                    <span>Aggressive (75%)</span>
                    <span className="text-tertiary font-medium">Safe Boundary (88%)</span>
                    <span>Ultra-Conservative (95%)</span>
                  </div>
                </div>
                <div className="space-y-2 bg-surface-container-lowest p-space-sm rounded-xl">
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-2">
                      <span className="material-symbols-outlined text-primary text-[18px]">emergency_home</span>
                      <span className="font-label-md text-label-md text-on-surface">Mandatory Escalation Trigger</span>
                    </div>
                    <span className="font-label-md text-label-md text-primary bg-surface-container px-2 py-0.5 rounded font-bold">72%</span>
                  </div>
                  <input className="w-full accent-primary h-1.5 bg-surface-container-high rounded-full cursor-pointer" max="85" min="50" type="range" defaultValue="72" />
                  <div className="flex justify-between text-on-surface-variant font-body-sm text-body-sm">
                    <span>Low Alert (55%)</span>
                    <span className="text-primary font-medium">Auto-Flag Under 72%</span>
                    <span>Hyper Vigilant (80%)</span>
                  </div>
                </div>
                <div className="pt-1">
                  <div className="h-3 w-full bg-surface-container rounded-full overflow-hidden flex shadow-inner">
                    <div className="bg-inverse-surface h-full" style={{ width: '14%' }}></div>
                    <div className="bg-error-container h-full" style={{ width: '20%' }}></div>
                    <div className="bg-primary-container h-full" style={{ width: '26%' }}></div>
                    <div className="bg-tertiary h-full" style={{ width: '40%' }}></div>
                  </div>
                  <div className="flex justify-between items-center text-on-surface-variant font-label-sm text-label-sm mt-1.5 px-0.5">
                    <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-inverse-surface"></span> Lockout</span>
                    <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-error-container"></span> Escalate</span>
                    <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-primary-container"></span> Smart Reframe</span>
                    <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-tertiary"></span> Auto-Verified</span>
                  </div>
                </div>
              </div>

              {/* Stop-Words */}
              <div className="lg:col-span-5 bg-surface-container-low p-space-md rounded-xl space-y-space-sm flex flex-col justify-between shadow-sm">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="font-label-sm text-label-sm uppercase tracking-wider text-outline">Deterministic Intercept</span>
                    <span className="material-symbols-outlined text-outline text-[18px]">security</span>
                  </div>
                  <h4 className="font-headline-sm text-headline-sm text-on-surface">Stop-Words Registry</h4>
                  <p className="font-body-sm text-body-sm text-on-surface-variant mt-0.5">Presence of any single token forces immediate agent freeze regardless of semantic score.</p>
                  <div className="flex flex-wrap gap-1.5 mt-space-sm">
                    {[
                      { word: 'lawyer', color: 'bg-error' },
                      { word: 'pricing', color: 'bg-primary' },
                      { word: 'quote', color: 'bg-primary' },
                      { word: 'refund', color: 'bg-error' },
                      { word: 'gdpr', color: 'bg-error' },
                      { word: 'unsubscribe', color: 'bg-error' },
                      { word: 'sue', color: 'bg-error' },
                      { word: 'discount', color: 'bg-primary' },
                    ].map(tag => (
                      <span key={tag.word} className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-surface-container-lowest text-on-surface font-label-md text-label-md shadow-sm">
                        <span className={`w-1.5 h-1.5 rounded-full ${tag.color}`}></span> {tag.word}
                        <button className="hover:text-error ml-1 text-[12px] leading-none">×</button>
                      </span>
                    ))}
                  </div>
                </div>
                <div className="relative w-full mt-space-sm">
                  <span className="material-symbols-outlined absolute left-3 top-2 text-[16px] text-outline">add_circle</span>
                  <input className="w-full bg-surface-container-lowest rounded-xl pl-8 pr-3 py-1.5 font-body-sm text-body-sm text-on-surface placeholder:text-outline focus:outline-none focus:bg-surface-container shadow-inner" placeholder="Type new keyword and press enter..." type="text" />
                </div>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="bg-surface-container-low px-space-lg py-space-md flex flex-col sm:flex-row items-center justify-between gap-space-sm shadow-md">
            <div className="flex items-center gap-space-xs text-on-surface-variant font-body-sm text-body-sm">
              <span className="w-2 h-2 rounded-full bg-tertiary"></span>
              <span>Last synchronized with SDR preferences: 8 mins ago</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
