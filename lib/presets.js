export const PROJECT_PRESETS = [
  {
    id: "devops-incident-autopilot",
    title: "IncidentPulse AI",
    tagline: "Autonomous SRE Copilot for Post-Mortems, Root-Cause Triaging & Auto-Remediation",
    track: "Developer Tools & Infra",
    theme: "Autonomous DevOps & Reliability",
    summary: "Ingests raw telemetry, log spikes, and PagerDuty alerts, correlates distributed traces across microservices, uses LLM synthesis to identify the root cause within seconds, and proposes verified safe rollback or hotfix PRs.",
    targetUsers: ["Site Reliability Engineers", "DevOps Leads", "On-Call Engineers"],
    keyMetrics: ["Mean Time to Resolution (MTTR) cut by 68%", "Zero false-positive automated rollbacks"],
    icon: "zap"
  },
  {
    id: "medscribe-clinical-copilot",
    title: "AetherMed Copilot",
    tagline: "Ambient Clinical Audio Scribe & Multimodal Differential Diagnosis Assistant",
    track: "Healthcare & Life Sciences",
    theme: "Ambient AI & Clinical Workflow",
    summary: "Listens to patient-physician consultations with real-time transcription, synthesizes structured SOAP notes mapped to ICD-10/SNOMED CT codes, and highlights contraindications with an explainable evidence trail.",
    targetUsers: ["General Practitioners", "Specialists", "Hospital Clinical Teams"],
    keyMetrics: ["Saves 2.5 hours per doctor/day on clinical EHR documentation", "100% citation traceability"],
    icon: "heart"
  },
  {
    id: "defi-risk-sentinel",
    title: "ChainGuard Sentinel",
    tagline: "Real-Time Smart Contract Exploit Early-Warning & Liquidity Anomaly Detector",
    track: "FinTech & Web3",
    theme: "Automated Financial Risk & Security",
    summary: "Monitors mempool transactions, pending flash loan simulations, and unverified contract deployments to predict DeFi drain exploits before block finality, alerting protocol treasuries and executing automated liquidity shelters.",
    targetUsers: ["DeFi Protocols", "Crypto Security Auditors", "DAO Treasuries"],
    keyMetrics: ["< 400ms mempool exploit detection latency", "Estimated $120M+ prevented in simulated flash loan exploits"],
    icon: "shield"
  },
  {
    id: "adaptive-learning-tutor",
    title: "NeuroTutor AI",
    tagline: "Socratic Cognitive Learning Companion that Adapts to Student Mental Models",
    track: "EdTech & Learning",
    theme: "Personalized Socratic Education",
    summary: "Instead of simply giving direct answers, NeuroTutor assesses the student's cognitive misconceptions through interactive dialog, builds a dynamic knowledge graph of mastery, and creates custom interactive micro-quizzes in real time.",
    targetUsers: ["STEM Undergraduates", "Bootcamp Students", "Self-Taught Developers"],
    keyMetrics: ["3.4x faster concept retention", "92% student engagement through Socratic probing"],
    icon: "book"
  },
  {
    id: "green-supply-oracle",
    title: "EcoLedger Oracle",
    tagline: "Automated Scope 3 Carbon Accounting & Supply Chain ESG Verification Engine",
    track: "Climate & Sustainability",
    theme: "Autonomous ESG & Supply Chain Intelligence",
    summary: "Parses complex supplier freight invoices, bills of lading, and manufacturing bills of materials to autonomously calculate verified Scope 1-3 carbon footprints compliant with CSRD and SEC disclosure mandates.",
    targetUsers: ["Chief Sustainability Officers", "Supply Chain Directors", "ESG Compliance Auditors"],
    keyMetrics: ["Reduces annual ESG audit prep from 4 months to 2 days", "Full audit-trail verification"],
    icon: "globe"
  }
];

export function getPresetById(id) {
  return PROJECT_PRESETS.find(p => p.id === id) || null;
}
